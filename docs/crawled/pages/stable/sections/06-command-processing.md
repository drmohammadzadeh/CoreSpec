---
source_url: https://fineract.apache.org/docs/1.16.0#_command_processing
title: "Command Processing"
depth: 1
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/stable
---

## Command Processing

> [!NOTE]
> This is an ongoing effort to migrate to an improved [CQRS](https://martinfowler.com/bliki/CQRS.html[CQRS]) sub-system. Please read Jira ticket [FINERACT-2169](https://issues.apache.org/jira/browse/FINERACT-2169) to see the current progress.

### Introduction

Fineract accumulated some technical debt over the years. One area that is implicated is type-safety of internal and external facing APIs, the most prominent of which is Fineract’s REST API. In general the package layout of the project reflects a more or less classic layered architecture (REST API, data transfer/value objects, business logic services, storage/repositories). The project predates some of the more modern frameworks and best practices that are available today and on occasions the data structures that are exchanged offer some challenges (e.g. generic types). Fineract’s code base reflects that, especially where JSON de-/serialization is involved. Nowadays, this task would be simply delegated to the Jackson framework, but when Fineract (MifosX) started, the decision was made to use Google’s GSON library and create handcrafted helper classes to deal with JSON parsing. While this provided a lot of flexibility the approach had some downsides:

* the lowest common denominator is the string type (aka JSON blob); this is where we lose the type information
* the strings are transformed into JSONObjects; a little bit better than raw strings, but barely more than a hash map
* "magic" strings are needed to get/set values
* this approach makes refactoring more difficult
* to be able to serve an OpenAPI descriptor (as JSON and YAML) we had to re-introduce the type information at the REST API level with dummy classes that contain only the specified attributes; those classes are only used with the Swagger annotations and no were else
* some developers skipped the layered architecture and found it too tedious to maintain DTOs and JSON helper classes, and as a result just passed JSONObjects right to the business logic layer
* now the business logic is unnecessarily aware of how Fineract communicates to the outside world and makes replacing/enhancing the communication protocol (e.g. with GRPC) pretty much impossible

The list doesn’t end here, but in the end things boil down to two main points:

* developer experience: boilerplate code and missing type safety cost more time
* bugs: the more code the more likely errors get introduced, especially when type safety is missing and we have to rely on runtime errors (vs. compile time).

There has been already some preparatory work done concerning type safety, but until now we avoided dealing with the real source of this issue. Fineract’s architectures devises read from write requests ([CQRS](https://martinfowler.com/bliki/CQRS.html)) for improved scalability.

The read requests are not that problematic and not (yet) covered, but all write requests pass through a component/service that is called `SynchronousCommandProcessingService`.

```java
public class SynchronousCommandProcessingService implements CommandProcessingService {

    public static final String IDEMPOTENCY_KEY_STORE_FLAG = "idempotencyKeyStoreFlag";

    public static final String IDEMPOTENCY_KEY_ATTRIBUTE = "IdempotencyKeyAttribute";
    public static final String COMMAND_SOURCE_ID = "commandSourceId";
    private final PlatformSecurityContext context;
    private final ApplicationContext applicationContext;
    private final TransactionBoundApplicationEventPublisher eventPublisher;
    private final ToApiJsonSerializer<Map<String, Object>> toApiJsonSerializer;
    private final ToApiJsonSerializer<CommandProcessingResult> toApiResultJsonSerializer;
    private final ConfigurationDomainService configurationDomainService;
    private final CommandHandlerProvider commandHandlerProvider;
    private final IdempotencyKeyResolver idempotencyKeyResolver;
    private final CommandSourceService commandSourceService;
    private final RetryConfigurationAssembler retryConfigurationAssembler;

    private final FineractRequestContextHolder fineractRequestContextHolder;
    private final Gson gson = GoogleGsonSerializerHelper.createSimpleGson();

    private CommandProcessingResult executeWithRetry(CommandExecutionContext executionContext) {
        try {
            if (!BatchRequestContextHolder.isEnclosingTransaction()) {
                return retryConfigurationAssembler.getRetryConfigurationForExecuteCommand()
                        .executeSupplier(() -> executeCommandAttempt(executionContext));
            }
            return executeCommandAttempt(executionContext);
        } catch (RollbackTransactionNotApprovedException e) {
            throw e;
        } catch (RuntimeException e) {
            RuntimeException mappable = ErrorHandler.getMappable(e);
            persistFinalErrorResult(executionContext, mappable);
            throw mappable;
        }
    }

    @Override
    public CommandProcessingResult executeCommand(final CommandWrapper wrapper, final JsonCommand command,
            final boolean isApprovedByChecker) {
        return executeWithRetry(new CommandExecutionContext(wrapper, command, isApprovedByChecker));
    }

    private CommandProcessingResult executeCommandAttempt(CommandExecutionContext executionContext) {
        // Do not store the idempotency key because of the exception handling
        setIdempotencyKeyStoreFlag(false);

        CommandWrapper wrapper = executionContext.wrapper();
        JsonCommand command = executionContext.command();
        Long commandId = (Long) fineractRequestContextHolder.getAttribute(COMMAND_SOURCE_ID, null);
        boolean isRetry = commandId != null;
        boolean isEnclosingTransaction = BatchRequestContextHolder.isEnclosingTransaction();
        executionContext.setEnclosingTransaction(isEnclosingTransaction);

        CommandSource commandSource = null;
        String idempotencyKey;
        if (isRetry) {
            commandSource = commandSourceService.getCommandSource(commandId);
            idempotencyKey = commandSource.getIdempotencyKey();
        } else if ((commandId = command.commandId()) != null) { // action on the command itself
            commandSource = commandSourceService.getCommandSource(commandId);
            idempotencyKey = commandSource.getIdempotencyKey();
        } else {
            idempotencyKey = idempotencyKeyResolver.resolve(wrapper);
        }
        exceptionWhenTheRequestAlreadyProcessed(wrapper, idempotencyKey, isRetry);

        AppUser user = context.authenticatedUser(wrapper);
        if (commandSource == null) {
            if (isEnclosingTransaction) {
                commandSource = commandSourceService.getInitialCommandSource(wrapper, command, user, idempotencyKey);
            } else {
                commandSource = commandSourceService.saveInitial(wrapper, command, user, idempotencyKey);
                commandId = commandSource.getId();
            }
        }
        executionContext.setCommandSource(commandSource);
        if (commandId != null) {
            storeCommandIdInContext(commandSource); // Store command id as a request attribute
        }

        setIdempotencyKeyStoreFlag(true);

        return executeCommandInTransaction(executionContext, commandSource, user, isEnclosingTransaction);
    }

    private CommandProcessingResult executeCommandInTransaction(CommandExecutionContext executionContext, CommandSource commandSource,
            AppUser user, boolean isEnclosingTransaction) {

        final CommandSourceService.CommandExecutionResult commandExecutionResult;
        try {
            commandExecutionResult = commandSourceService.processCommandAndSaveResult(findCommandHandler(executionContext.wrapper()),
                    executionContext.command(), commandSource, user, executionContext.approvedByChecker(), this::updateSuccessfulResult);
        } catch (RollbackTransactionNotApprovedException e) {
            ErrorInfo errorInfo = commandSourceService.generateErrorInfo(e);
            commandSource.setResultStatusCode(errorInfo.getStatusCode());
            commandSource.setResult(errorInfo.getMessage());
            if (!isEnclosingTransaction) { // TODO: temporary solution
                commandSourceService.saveResult(commandSource);
            }
            publishHookErrorEvent(executionContext.wrapper(), executionContext.command(), errorInfo);
            throw e;
        }

        CommandProcessingResult result = commandExecutionResult.result();
        storeCommandIdInContext(commandExecutionResult.commandSource());

        result.setRollbackTransaction(null);

        // When running inside an enclosing batch transaction, defer hook publication
        // until after the transaction commits. This prevents webhooks from firing for
        // commands that are subsequently rolled back when a later command in the batch
        // fails (e.g. a withdrawal succeeds but its fee charge fails, rolling back both).
        if (isEnclosingTransaction && TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {

                @Override
                public void afterCommit() {
                    publishHookEvent(executionContext.wrapper().entityName(), executionContext.wrapper().actionName(),
                            executionContext.command(), result);
                }
            });
        } else {
            publishHookEvent(executionContext.wrapper().entityName(), executionContext.wrapper().actionName(), executionContext.command(),
                    result);
        }

        return result;
    }

    private void updateSuccessfulResult(CommandSource commandSource, CommandProcessingResult result) {
        commandSource.setResultStatusCode(SC_OK);
        commandSource.updateForAudit(result);
        commandSource.setResult(toApiResultJsonSerializer.serializeResult(result));
        commandSource.setStatus(PROCESSED);
    }

    private void persistFinalErrorResult(CommandExecutionContext executionContext, RuntimeException mappable) {
        CommandSource commandSource = executionContext.commandSource();
        if (commandSource == null) {
            return;
        }
        ErrorInfo errorInfo = commandSourceService.generateErrorInfo(mappable);
        publishHookErrorEvent(executionContext.wrapper(), executionContext.command(), errorInfo);
        if (executionContext.enclosingTransaction()) {
            return;
        }

        Integer statusCode = errorInfo.getStatusCode();
        commandSource.setResultStatusCode(statusCode);
        commandSource.setResult(errorInfo.getMessage());
        if (statusCode != SC_OK) {
            commandSource.setStatus(ERROR);
        }
        commandSourceService.saveResult(commandSource);
    }

    private void storeCommandIdInContext(CommandSource savedCommandSource) {
        if (savedCommandSource.getId() == null) {
            throw new IllegalStateException("Command source not saved");
        }
        // Idempotency filters and retry need this
        fineractRequestContextHolder.setAttribute(COMMAND_SOURCE_ID, savedCommandSource.getId());
    }

    private void publishHookErrorEvent(CommandWrapper wrapper, JsonCommand command, ErrorInfo errorInfo) {
        try {
            publishHookEvent(wrapper.entityName(), wrapper.actionName(), command, gson.toJson(errorInfo));
        } catch (Exception e) {
            log.error("Failed to publish hook error event for entity: {}, action: {}", wrapper.entityName(), wrapper.actionName(), e);
        }
    }

    private void exceptionWhenTheRequestAlreadyProcessed(CommandWrapper wrapper, String idempotencyKey, boolean retry) {
        CommandSource command = commandSourceService.findCommandSource(wrapper, idempotencyKey);
        if (command == null) {
            return;
        }
        CommandProcessingResultType status = CommandProcessingResultType.fromInt(command.getStatus());
        switch (status) {
            case UNDER_PROCESSING -> {
                Class<?> lastExecutionExceptionClass = retryConfigurationAssembler.getLastException();
                if (lastExecutionExceptionClass == null
                        || IdempotentCommandProcessUnderProcessingException.class.isAssignableFrom(lastExecutionExceptionClass)) {
                    throw new IdempotentCommandProcessUnderProcessingException(wrapper, idempotencyKey);
                }
            }
            case PROCESSED -> throw new IdempotentCommandProcessSucceedException(wrapper, idempotencyKey, command);
            case ERROR -> {
                if (!retry) {
                    throw new IdempotentCommandProcessFailedException(wrapper, idempotencyKey, command);
                }
            }
            default -> {
            }
        }
    }

    private void setIdempotencyKeyStoreFlag(boolean flag) {
        fineractRequestContextHolder.setAttribute(IDEMPOTENCY_KEY_STORE_FLAG, flag);
    }

    private static final class CommandExecutionContext {

        private final CommandWrapper wrapper;
        private final JsonCommand command;
        private final boolean approvedByChecker;
        private CommandSource commandSource;
        private boolean enclosingTransaction;

        private CommandExecutionContext(CommandWrapper wrapper, JsonCommand command, boolean approvedByChecker) {
            this.wrapper = wrapper;
            this.command = command;
            this.approvedByChecker = approvedByChecker;
        }

        CommandWrapper wrapper() {
            return wrapper;
        }

        JsonCommand command() {
            return command;
        }

        boolean approvedByChecker() {
            return approvedByChecker;
        }

        CommandSource commandSource() {
            return commandSource;
        }

        void setCommandSource(CommandSource commandSource) {
            this.commandSource = commandSource;
        }

        boolean enclosingTransaction() {
            return enclosingTransaction;
        }

        void setEnclosingTransaction(boolean enclosingTransaction) {
            this.enclosingTransaction = enclosingTransaction;
        }
    }

    private NewCommandSourceHandler findCommandHandler(final CommandWrapper wrapper) {
        NewCommandSourceHandler handler;

        if (wrapper.isDatatableResource()) {
            if (wrapper.isCreateDatatable()) {
                handler = applicationContext.getBean("createDatatableCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isDeleteDatatable()) {
                handler = applicationContext.getBean("deleteDatatableCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isUpdateDatatable()) {
                handler = applicationContext.getBean("updateDatatableCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isCreate()) {
                handler = applicationContext.getBean("createDatatableEntryCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isUpdateMultiple()) {
                handler = applicationContext.getBean("updateOneToManyDatatableEntryCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isUpdateOneToOne()) {
                handler = applicationContext.getBean("updateOneToOneDatatableEntryCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isDeleteMultiple()) {
                handler = applicationContext.getBean("deleteOneToManyDatatableEntryCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isDeleteOneToOne()) {
                handler = applicationContext.getBean("deleteOneToOneDatatableEntryCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isRegisterDatatable()) {
                handler = applicationContext.getBean("registerDatatableCommandHandler", NewCommandSourceHandler.class);
            } else {
                throw new UnsupportedCommandException(wrapper.commandName());
            }
        } else if (wrapper.isNoteResource()) {
            if (wrapper.isCreate()) {
                handler = applicationContext.getBean("createNoteCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isUpdate()) {
                handler = applicationContext.getBean("updateNoteCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isDelete()) {
                handler = applicationContext.getBean("deleteNoteCommandHandler", NewCommandSourceHandler.class);
            } else {
                throw new UnsupportedCommandException(wrapper.commandName());
            }
        } else if (wrapper.isSurveyResource()) {
            if (wrapper.isRegisterSurvey()) {
                handler = applicationContext.getBean("registerSurveyCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isFullFilSurvey()) {
                handler = applicationContext.getBean("fullFilSurveyCommandHandler", NewCommandSourceHandler.class);
            } else {
                throw new UnsupportedCommandException(wrapper.commandName());
            }
        } else if (wrapper.isLoanDisburseDetailResource()) {
            if (wrapper.isUpdateDisbursementDate()) {
                handler = applicationContext.getBean("updateLoanDisburseDateCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.addAndDeleteDisbursementDetails()) {
                handler = applicationContext.getBean("addAndDeleteLoanDisburseDetailsCommandHandler", NewCommandSourceHandler.class);
            } else {
                throw new UnsupportedCommandException(wrapper.commandName());
            }
        } else if (wrapper.isInterestPauseResource()) {
            if (wrapper.isInterestPauseCreateResource()) {
                handler = applicationContext.getBean("createInterestPauseCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isInterestPauseUpdateResource()) {
                handler = applicationContext.getBean("updateInterestPauseCommandHandler", NewCommandSourceHandler.class);
            } else if (wrapper.isInterestPauseDeleteResource()) {
                handler = applicationContext.getBean("deleteInterestPauseCommandHandler", NewCommandSourceHandler.class);
            } else {
                throw new UnsupportedCommandException(wrapper.commandName());
            }
        } else {
            handler = commandHandlerProvider.getHandler(wrapper.entityName(), wrapper.actionName());
        }

        return handler;
    }

    @Override
    public boolean validateRollbackCommand(final CommandWrapper commandWrapper, final AppUser user) {
        user.validateHasPermissionTo(commandWrapper.getTaskPermissionName());
        boolean isMakerChecker = configurationDomainService.isMakerCheckerEnabledForTask(commandWrapper.taskPermissionName());
        return isMakerChecker && !user.isCheckerSuperUser();
    }

    protected void publishHookEvent(final String entityName, final String actionName, JsonCommand command, final Object result) {
        try {
            final AppUser appUser = context.authenticatedUser(CommandWrapper.wrap(actionName, entityName, null, null));

            final HookEventSource hookEventSource = new HookEventSource(entityName, actionName);

            // TODO: Add support for publishing array events
            if (command.json() != null) {
                Type type = new TypeToken<Map<String, Object>>() {

                }.getType();

                Map<String, Object> myMap;

                try {
                    myMap = gson.fromJson(command.json(), type);
                } catch (Exception e) {
                    throw new PlatformApiDataValidationException("error.msg.invalid.json", "The provided JSON is invalid.",
                            new ArrayList<>(), e);
                }

                Map<String, Object> reqmap = new HashMap<>();
                reqmap.put("entityName", entityName);
                reqmap.put("actionName", actionName);
                reqmap.put("createdBy", context.authenticatedUser().getId());
                reqmap.put("createdByName", context.authenticatedUser().getUsername());
                reqmap.put("createdByFullName", context.authenticatedUser().getDisplayName());

                reqmap.put("request", myMap);
                if (result instanceof CommandProcessingResult) {
                    CommandProcessingResult resultCopy = CommandProcessingResult
                            .fromCommandProcessingResult((CommandProcessingResult) result);

                    reqmap.put("officeId", resultCopy.getOfficeId());
                    reqmap.put("clientId", resultCopy.getClientId());
                    resultCopy.setOfficeId(null);
                    reqmap.put("response", resultCopy);
                } else if (result instanceof ErrorInfo ex) {
                    reqmap.put("status", "Exception");

                    Map<String, Object> errorMap = new HashMap<>();

                    try {
                        errorMap = gson.fromJson(ex.getMessage(), type);
                    } catch (Exception e) {
                        errorMap.put("errorMessage", ex.getMessage());
                    }

                    errorMap.put("errorCode", ex.getErrorCode());
                    errorMap.put("statusCode", ex.getStatusCode());

                    reqmap.put("response", errorMap);
                }

                reqmap.put("timestamp", Instant.now().toString());

                final String serializedResult = toApiJsonSerializer.serialize(reqmap);

                final HookEvent applicationEvent = new HookEvent(hookEventSource, serializedResult, appUser,
                        ThreadLocalContextUtil.getContext());

                eventPublisher.publishEvent(applicationEvent);
            }
        } catch (Exception e) {
            log.error("Failed to publish hook event for entity: {}, action: {}", entityName, actionName, e);
        }
    }
}
```

As the name suggests the execution of business logic is synchronous (mostly) due to this part of the architecture. This is not necessarily a problem (not immediately at least), but it’s nevertheless a central bottleneck in the system. Even more important: this service is responsible to route incoming commands to their respective handler classes which in turn execute functions on one or more business logic services. The payload of these commands are obviously not always the same…​ which is the main reason why we decided to use the lowest common denominator to be able to handle these various types and rendered all payloads as strings. This compromise bubbles now up in the REST API and the business logic layers (and actually everything in between).

Over the years we’ve also added additional features (e.g. idempotency guarantees for incoming write requests) that make it now very hard to reason about the execution flow. Testing the performance impact of such additions to the critical execution path even can’t be properly measured. Note: the current implementation of idempotency relies on database lookups (quite often, for each incoming request) and none of those queries are cached. If we wanted to store already processed requests (IDs) in a faster system (let’s Redis) then this can’t be done without major refactoring.

### Architecture

This chapter outlines the new Command Query Responsibility Segregation (CQRS) implementation introduced in Apache Fineract. This architecture aims to improve the separation of concerns, testability, and maintainability of the write-side (command) operations.

> [!NOTE]
> A proposal to cover the read-side (query) is in preparation.

By shifting from our legacy type-less, synchronous command processing to an improved and extensible command-driven flow, we establish a robust pipeline for handling business operations, cross-cutting concerns (via hooks), and error handling (retries, fallbacks).

#### Core Components

* command dispatcher: the entry point for all command operations
* command hanlder: acts as the bridge between the incoming command and the specific business logic required to handle it
* command hooks: interception points to execute cross-cutting logic without polluting the dispatcher or the handler; there are three types of hooks
  
  
  
  
  
  * before command hook
  * after command hook
  * error command hook

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc1NzdweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjEzOTFweDtoZWlnaHQ6NTc3cHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTM5MSA1NzcnIHdpZHRoPScxMzkxcHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5LjA2NzknIHN0eWxlPSdzdHJva2U6IzAwMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycgd2lkdGg9JzQ1MScgeD0nNDYzJyB5PSc1Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQ0MScgeD0nNDY4JyB5PScyNC45NjU5Jz5Db21tYW5kIFByb2Nlc3NpbmcgQXJjaGl0ZWN0dXJlIChMZXZlbCAxKSAtIENvcmUgQ29tcG9uZW50czwvdGV4dD48ZyBpZD0nY2x1c3Rlcl9maW5lcmFjdFN5c3RlbSc+PHJlY3QgaGVpZ2h0PSc1MjQnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzQ0NDQ0NDtzdHJva2Utd2lkdGg6MS4wO2ZpbGw6bm9uZTtzdHJva2UtZGFzaGFycmF5OjcuMCw3LjA7JyB3aWR0aD0nMTA1NicgeD0nMzI5JyB5PSc0Ny4wNjc5Jy8+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nNicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5JyB4PSc4NDIuNScgeT0nNTUuNDgyJz7Cq2JvdW5kYXJ5wrs8L3RleHQ+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY2JyB4PSc4MjQnIHk9Jzc2LjE3Mic+RmluZXJhY3Q8L3RleHQ+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzUyJyB4PSc4MzEnIHk9JzkzLjY4ODEnPltTeXN0ZW1dPC90ZXh0PjwvZz48ZyBpZD0nY2x1c3Rlcl9jb21tYW5kU3lzdGVtJz48cmVjdCBoZWlnaHQ9JzQyNScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojNDQ0NDQ0O3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6Ny4wLDcuMDsnIHdpZHRoPSc2MTcnIHg9Jzc0NCcgeT0nMTIyLjA2NzknLz48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPSc2JyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjknIHg9JzEwMzgnIHk9JzEzMC40ODInPsKrYm91bmRhcnnCuzwvdGV4dD48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTczJyB4PSc5NjYnIHk9JzE1MS4xNzInPkNvbW1hbmQgUHJvY2Vzc2luZzwvdGV4dD48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTInIHg9JzEwMjYuNScgeT0nMTY4LjY4ODEnPltTeXN0ZW1dPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9hcGknPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIxOScgeD0nMzQ1JyB5PSczMzEuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzQyMycgeT0nMzU0LjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTM5JyB4PSczODUnIHk9JzM3NS4wMTYxJz5GaW5lcmFjdCBSRVNUIEFQSTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzc0JyB4PSc0MTcuNScgeT0nMzkyLjUzMjInPltKQVgtUlMvSmVyc2V5XTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc0NTIuNScgeT0nNDExLjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE5NScgeD0nMzU5JyB5PSc0MzAuMDgyJz5FbnRyeSBwb2ludCBmb3IgYWxsIGNvbW1hbmRzPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9kaXNwYXRjaGVyJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzEzMS42ODQnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE5NCcgeD0nNzYwJyB5PSczMjIuMDY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzgyNS41JyB5PSczNDQuODk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNzQnIHg9Jzc3MCcgeT0nMzY1LjUxNjEnPkNvbW1hbmQgRGlzcGF0Y2hlcjwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzk4JyB4PSc4MDgnIHk9JzM4My4wMzIyJz5bTWVkaWF0b3IgUGF0dGVybl08L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nODU1JyB5PSc0MDEuNTE0MSc+wqA8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTUyJyB4PSc3ODEnIHk9JzQyMC41ODInPkNvb3JkaW5hdGVzIGNvbW1hbmQ8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjUnIHg9JzgyNC41JyB5PSc0MzkuNjUnPmV4ZWN1dGlvbjwvdGV4dD48L2c+PGcgaWQ9J2VsZW1faG9va01hbmFnZXInPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTUzLjQ3NjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIwNicgeD0nMTEzOScgeT0nMzc3LjU2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PScxMjEwLjUnIHk9JzQwMC4zOTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyOScgeD0nMTE3NS41JyB5PSc0MjEuMDE2MSc+Q29tbWFuZCBIb29rPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3MicgeD0nMTIwNicgeT0nNDQyLjgwODEnPk1hbmFnZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjEnIHg9JzExNjEuNScgeT0nNDYwLjMyNDInPltSZWdpc3RyeS9JbnRlcmNlcHRvciBQYXR0ZXJuc108L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nMTI0MCcgeT0nNDc4LjgwNjInPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1NCcgeD0nMTE2NScgeT0nNDk3Ljg3NDEnPk1hcHMgaG9va3MgdG8gaGFuZGxlcjwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODYnIHg9JzExNDknIHk9JzUxNi45NDInPmxpZmVjeWNsZSAoYmVmb3JlL2FmdGVyL2Vycm9yKTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1faGFuZGxlck1hbmFnZXInPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTUzLjQ3NjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE5MycgeD0nMTE0NS41JyB5PScxODkuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzEyMTAuNScgeT0nMjEyLjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTUxJyB4PScxMTY0LjUnIHk9JzIzMy4wMTYxJz5Db21tYW5kIEhhbmRsZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzcyJyB4PScxMjA2JyB5PScyNTQuODA4MSc+TWFuYWdlcjwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzkyJyB4PScxMTk2JyB5PScyNzIuMzI0Mic+W1JlZ2lzdHJ5IFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzEyNDAnIHk9JzI5MC44MDYyJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjUnIHg9JzExNTkuNScgeT0nMzA5Ljg3NDEnPk1hcHMgY29tbWFuZCB0eXBlcyB0bzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MCcgeD0nMTIxMicgeT0nMzI4Ljk0Mic+aGFuZGxlcnM8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2NsaWVudCc+PHJlY3QgZmlsbD0nIzA4NDI3QicgaGVpZ2h0PScxNDQuMjcyJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMwNzNCNkY7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxODMnIHg9JzcnIHk9JzMxNi4wNjc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0OScgeD0nNzQnIHk9JzMzOC44OTYnPsKrcGVyc29uwrs8L3RleHQ+PGltYWdlIGhlaWdodD0nNDgnIHhsaW5rOmhyZWY9J2RhdGE6aW1hZ2UvcG5nO2Jhc2U2NCxpVkJPUncwS0dnb0FBQUFOU1VoRVVnQUFBREFBQUFBd0NBSUFBQURZWUc3UUFBQUNEMGxFUVZSNFh1MllvVTRFTVJDR1QrNGo4QWk4QWhhSDRRSGdBVWpRdUZNRUNVZ01JVWd3SkFnTWhnUXNBWVVpSkNpUUlCQlkrRUlUc2pmVGRtZTZWMjR2NGM4dnlHYmIrWmpPdE4wYk5jdmpRWG1rSDgzV3ZZQld0bzZQTG02djdwN3VIMS93MmZYRCtQQnljWDFQdjJsM0lkRG0vdm43eCtkWFFpQXViUnpvVVJhN2dSWldkMGlHUklpSmJPbmhuZllCUVpOSmpOYnV5WTJlSkc4ZmtERTNiYkc0ZXA2TUhVQXNnWXhtRTNuVnM2VnNCV0pTR2Njc09sRlBtTElWaU16TE9CN3BDVk8yQXRISk1vaEg3Rmg2enFpdFFLN20wckp2QVZZZ0djRXBlLy9QTGREejY1c000cEY5TjdJQ2NYREtJQjVOdjZqN3REME5vU2RNMlFyVTlHZzBld0UxTHFCaEhSM0JCZHZqMnZhcG5pZGpIeEQvcTZ2ZDdQdmhyMzFBd2NZOGVYTVRYQUtFQ1paSkZYdUVxMjdhTGdRSzV1TE1vaENlbkdHdUdld094U2pCdllCcWVHNkIrTnFpYmxnZ2RqbmMrWlhEeStGTkZwRnp3NzZPM1VCQVJPdVhoNkZvaUFjZjVnOWVUdlVnenkwbldnNkk4Y1hIUlVwZzViT1ZCQ28rS0RwRmFqT2YyM0dnUG1lN1JTUStsYWNJRU5VZ0o2Z2cxazZIamdPbHFuTHFpcDR0RXVodjBoTkVNWFVEMGNseVhFM3A2cFpBMFMybm52VGxYd0xKRVpXbGI3Y1RRSDErVVNnVE40VmhBZW5tL3dlYTFPQ0FPbXFvNmZFMVdDYjlXU0tCYWgrcmJVV1BXQW1FMlJ2azBBcGlCNDVlT3lOQXpVOHhjVHZqOEt2a0tFb09hSVllSE5BM1p1eWdBdkZNVU8wQUFBQUFTVVZPUks1Q1lJST0nIHdpZHRoPSc0OCcgeD0nNzQuNScgeT0nMzQyLjQxMicvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0NycgeD0nNzUnIHk9JzQwNy41MTYxJz5DbGllbnQ8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nOTYuNScgeT0nNDI3LjE3Jz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTknIHg9JzIxJyB5PSc0NDYuMjM3OSc+VXNlciBvciBleHRlcm5hbCBzeXN0ZW08L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2NsaWVudF9hcGknPjxwYXRoIGQ9J00xOTAuMiwzODguMDY3OSBDMjM0Ljc0LDM4OC4wNjc5IDI4OC45NCwzODguMDY3OSAzMzYuNTUsMzg4LjA2NzkgJyBmaWxsPSdub25lJyBpZD0nY2xpZW50LXRvLWFwaScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPSczNDQuNzQsMzg4LjA2NzksMzM2Ljc0LDM4NS4wNjc5LDMzNi43NCwzOTEuMDY3OSwzNDQuNzQsMzg4LjA2NzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5MScgeD0nMjIxJyB5PSczNjcuODk2Jz5TZW5kcyByZXF1ZXN0czwvdGV4dD48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PScyMzUnIHk9JzM4NC4yNDAxJz5bSFRUUC9KU09OXTwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfYXBpX2Rpc3BhdGNoZXInPjxwYXRoIGQ9J001NjQuMTUsMzg4LjA2NzkgQzYyMi41NSwzODguMDY3OSA2OTQuMjEsMzg4LjA2NzkgNzUxLjkxLDM4OC4wNjc5ICcgZmlsbD0nbm9uZScgaWQ9J2FwaS10by1kaXNwYXRjaGVyJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9Jzc1OS45NSwzODguMDY3OSw3NTEuOTUsMzg1LjA2NzksNzUxLjk1LDM5MS4wNjc5LDc1OS45NSwzODguMDY3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyOScgeD0nNTk1JyB5PSczNjcuODk2Jz5Db252ZXJ0cyByZXF1ZXN0IGludG88L3RleHQ+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYwJyB4PSc2MzEnIHk9JzM4NC4yNDAxJz5jb21tYW5kPC90ZXh0PjwvZz48ZyBpZD0nbGlua19kaXNwYXRjaGVyX2hvb2tNYW5hZ2VyJz48cGF0aCBkPSdNOTM1LjI3LDQ1NC4yNTc5IEM5NTAuNTUsNDY0LjA0NzkgOTY3LjEsNDcyLjY1NzkgOTg0LDQ3OC4wNjc5IEMxMDMwLjgsNDkzLjA2NzkgMTA4NC42Niw0OTAuODA3OSAxMTMwLjk0LDQ4My4zMjc5ICcgZmlsbD0nbm9uZScgaWQ9J2Rpc3BhdGNoZXItdG8taG9va01hbmFnZXInIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMTEzOC45LDQ4MS45ODc5LDExMzAuNTA5OSw0ODAuMzczNSwxMTMxLjUxNzIsNDg2LjI4ODMsMTEzOC45LDQ4MS45ODc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTE1JyB4PSc5ODknIHk9JzQ3My44OTYnPkNhbGwgYmVmb3JlIGhhbmRsZXI8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2Rpc3BhdGNoZXJfaG9va01hbmFnZXInPjxwYXRoIGQ9J005NTQuMDUsNDEzLjY5NzkgQzk2NC4xMyw0MTYuMDE3OSA5NzQuMjUsNDE4LjE4NzkgOTg0LDQyMC4wNjc5IEMxMDMxLjg0LDQyOS4yNzc5IDEwODUuMTgsNDM2Ljc3NzkgMTEzMC44LDQ0Mi4zNjc5ICcgZmlsbD0nbm9uZScgaWQ9J2Rpc3BhdGNoZXItdG8taG9va01hbmFnZXItMScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPScxMTM4Ljk0LDQ0My4zNDc5LDExMzEuMzU2NCw0MzkuNDEyNCwxMTMwLjYzODUsNDQ1LjM2OTMsMTEzOC45NCw0NDMuMzQ3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwNScgeD0nOTk0JyB5PSc0MTUuODk2Jz5DYWxsIGFmdGVyIGhhbmRsZXI8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2Rpc3BhdGNoZXJfaG9va01hbmFnZXInPjxwYXRoIGQ9J005NTQuMSwzODMuODM3OSBDMTAwMS4yOSwzODMuNzk3OSAxMDU4LjY4LDM4Ni43ODc5IDExMDksMzk4LjA2NzkgQzExMTYuMjIsMzk5LjY4NzkgMTEyMy41NSw0MDEuNjg3OSAxMTMwLjg2LDQwMy45NTc5ICcgZmlsbD0nbm9uZScgaWQ9J2Rpc3BhdGNoZXItdG8taG9va01hbmFnZXItMicgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPScxMTM4Ljc4LDQwNi41MTc5LDExMzIuMDg3OSw0MDEuMjA2LDExMzAuMjQ1Myw0MDYuOTE2MSwxMTM4Ljc4LDQwNi41MTc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTIzJyB4PSc5ODUnIHk9JzM4MC44OTYnPkNhbGwgb24gaGFuZGxlciBlcnJvcjwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfZGlzcGF0Y2hlcl9oYW5kbGVyTWFuYWdlcic+PHBhdGggZD0nTTk1NC4xNSwzNTcuNDM3OSBDMTAxMC4wMiwzMzkuNjM3OSAxMDgwLjQzLDMxNy4yMTc5IDExMzcuNTEsMjk5LjAzNzkgJyBmaWxsPSdub25lJyBpZD0nZGlzcGF0Y2hlci10by1oYW5kbGVyTWFuYWdlcicgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPScxMTQ1LjQ3LDI5Ni40OTc5LDExMzYuOTM2OSwyOTYuMDY2MSwxMTM4Ljc1NywzMDEuNzgzNCwxMTQ1LjQ3LDI5Ni40OTc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTA2JyB4PSc5OTMuNScgeT0nMzA0Ljg5Nic+SGFuZGxlIGNvbW1hbmQ8L3RleHQ+PC9nPjwvZz48L3N2Zz4=)

Figure 7. Command Processing Architecture Level 1 - Core

### Commands

This is the write-side of the architecture…​

#### Dispatcher

The synchronous command dispatcher is the default implementation that is used to dispatch and execute commands. We have already prototypes for other dispatch modes (asynchronous and non-blocking), but they need extensive testing before they can be used in production. When ready they can be dropped in without any further code changes. The default synchronous dispatcher is automatically disabled if an alternative command dispatcher implementation is provided by Spring Framework’s dependency injection mechanism.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc1NDBweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjk5NHB4O2hlaWdodDo1NDBweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA5OTQgNTQwJyB3aWR0aD0nOTk0cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5LjA2NzknIHN0eWxlPSdzdHJva2U6IzAwMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycgd2lkdGg9JzQwMCcgeD0nMjkwJyB5PSc1Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzM5MCcgeD0nMjk1JyB5PScyNC45NjU5Jz5Db21tYW5kIFByb2Nlc3NpbmcgQXJjaGl0ZWN0dXJlIChMZXZlbCAyKSAtIERpc3BhdGNoZXI8L3RleHQ+PGcgaWQ9J2NsdXN0ZXJfZGlzcGF0Y2hlclN5c3RlbSc+PHJlY3QgaGVpZ2h0PSc0ODcnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzQ0NDQ0NDtzdHJva2Utd2lkdGg6MS4wO2ZpbGw6bm9uZTtzdHJva2UtZGFzaGFycmF5OjcuMCw3LjA7JyB3aWR0aD0nOTgxJyB4PSc3JyB5PSc0Ny4wNjc5Jy8+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nNicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5JyB4PSc0ODMnIHk9JzU1LjQ4Mic+wqtib3VuZGFyecK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyM0NDQ0NDQnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNzQnIHg9JzQxMC41JyB5PSc3Ni4xNzInPkNvbW1hbmQgRGlzcGF0Y2hlcjwvdGV4dD48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTInIHg9JzQ3MS41JyB5PSc5My42ODgxJz5bU3lzdGVtXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fZGlzcGF0Y2hlckludGVyZmFjZSc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxNTMuNDc2MScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTk4JyB4PSc0MDQnIHk9JzM2NS4wNjc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nNDcxLjUnIHk9JzM4Ny44OTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3NCcgeD0nNDE0JyB5PSc0MDguNTE2MSc+Q29tbWFuZCBEaXNwYXRjaGVyPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4MycgeD0nNDYxLjUnIHk9JzQzMC4zMDgxJz4oSW50ZXJmYWNlKTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzU0JyB4PSc0NzYnIHk9JzQ0Ny44MjQyJz5bSW50ZXJmYWNlXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc1MDEnIHk9JzQ2Ni4zMDYyJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTEnIHg9JzQyNy41JyB5PSc0ODUuMzc0MSc+Q29udHJhY3QgZm9yIGNvbW1hbmQ8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nODAnIHg9JzQ2MycgeT0nNTA0LjQ0Mic+ZGlzcGF0Y2hpbmc8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2Rpc3BhdGNoZXJTeW5jJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzEzMS42ODQnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIxNicgeD0nNzU2JyB5PScxMzQuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzgzMi41JyB5PScxNTcuMzk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxOTYnIHg9Jzc2NicgeT0nMTc4LjAxNjEnPlN5bmNocm9ub3VzIERpc3BhdGNoZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5OCcgeD0nODE1JyB5PScxOTUuNTMyMic+W01lZGlhdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9Jzg2MicgeT0nMjE0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1OCcgeD0nNzg1JyB5PScyMzMuMDgyJz5TeW5jaHJvbm91cyBjb21tYW5kPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY1JyB4PSc4MzEuNScgeT0nMjUyLjE1Jz5leGVjdXRpb248L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2Rpc3BhdGNoZXJBc3luYyc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxNTMuNDc2MScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTk0JyB4PSc1MjcnIHk9JzEyNC4wNjc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nNTkyLjUnIHk9JzE0Ni44OTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNScgeD0nNTY0LjUnIHk9JzE2Ny41MTYxJz5Bc3luY2hyb25vdXM8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg3JyB4PSc1ODAuNScgeT0nMTg5LjMwODEnPkRpc3BhdGNoZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5OCcgeD0nNTc1JyB5PScyMDYuODI0Mic+W01lZGlhdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzYyMicgeT0nMjI1LjMwNjInPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2NicgeD0nNTQxJyB5PScyNDQuMzc0MSc+QXN5bmNocm9ub3VzIGNvbW1hbmQ8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjUnIHg9JzU5MS41JyB5PScyNjMuNDQyJz5leGVjdXRpb248L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2Rpc3BhdGNoZXJOb25CbG9ja2luZyc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxMzEuNjg0JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScyMTknIHg9JzI3Mi41JyB5PScxMzQuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzM1MC41JyB5PScxNTcuMzk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxOTknIHg9JzI4Mi41JyB5PScxNzguMDE2MSc+Tm9uLWJsb2NraW5nIERpc3BhdGNoZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5OCcgeD0nMzMzJyB5PScxOTUuNTMyMic+W01lZGlhdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzM4MCcgeT0nMjE0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2MScgeD0nMzAxLjUnIHk9JzIzMy4wODInPk5vbi1ibG9ja2luZyBjb21tYW5kPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY1JyB4PSczNDkuNScgeT0nMjUyLjE1Jz5leGVjdXRpb248L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2Rpc3BhdGNoZXJDaHJvbmljbGUnPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTcyLjU0NCcgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMjE0JyB4PScyMycgeT0nMTE0LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSc5OC41JyB5PScxMzYuODk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzYxLjUnIHk9JzE1Ny41MTYxJz5DaHJvbmljbGUgUXVldWU8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg3JyB4PSc4Ni41JyB5PScxNzkuMzA4MSc+RGlzcGF0Y2hlcjwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzk4JyB4PSc4MScgeT0nMTk2LjgyNDInPltNZWRpYXRvciBQYXR0ZXJuXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PScxMjgnIHk9JzIxNS4zMDYyJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODAnIHg9JzQwJyB5PScyMzQuMzc0MSc+Q29tbWFuZCBleGVjdXRpb24gdXNpbmc8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTkwJyB4PSczMycgeT0nMjUzLjQ0Mic+aGlnaCBwZXJmb3JtYW5jZSBDaHJvbmljbGU8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNDUnIHg9JzEwNy41JyB5PScyNzIuNTA5OSc+UXVldWU8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2Rpc3BhdGNoZXJTeW5jX2Rpc3BhdGNoZXJJbnRlcmZhY2UnPjxwYXRoIGQ9J003NjkuMjksMjY2LjY4NzkgQzc1OS4wOSwyNzMuNTk3OSA3NDguODQsMjgwLjQ5NzkgNzM5LDI4Ny4wNjc5IEM2OTYuNjMsMzE1LjMyNzkgNjQ5LjY2LDM0Ni4wMTc5IDYwOC44NCwzNzIuNDY3OSAnIGZpbGw9J25vbmUnIGlkPSdkaXNwYXRjaGVyU3luYy10by1kaXNwYXRjaGVySW50ZXJmYWNlJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzYwMi4wOCwzNzYuODQ3OSw2MTAuNDI2NiwzNzUuMDIyMSw2MDcuMTY4LDM2OS45ODQxLDYwMi4wOCwzNzYuODQ3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzczJyB4PSc2ODgnIHk9JzMzMC44OTYnPmltcGxlbWVudHM8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2Rpc3BhdGNoZXJBc3luY19kaXNwYXRjaGVySW50ZXJmYWNlJz48cGF0aCBkPSdNNTg1LjcxLDI3Ny4xODc5IEM1NzIuNzQsMzAyLjgxNzkgNTU4LjE4LDMzMS41Njc5IDU0NC45NCwzNTcuNzI3OSAnIGZpbGw9J25vbmUnIGlkPSdkaXNwYXRjaGVyQXN5bmMtdG8tZGlzcGF0Y2hlckludGVyZmFjZScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPSc1NDEuMjQsMzY1LjAyNzksNTQ3LjUyODgsMzU5LjI0NDIsNTQyLjE3NTEsMzU2LjUzNTIsNTQxLjI0LDM2NS4wMjc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzMnIHg9JzU2NCcgeT0nMzMwLjg5Nic+aW1wbGVtZW50czwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfZGlzcGF0Y2hlck5vbkJsb2NraW5nX2Rpc3BhdGNoZXJJbnRlcmZhY2UnPjxwYXRoIGQ9J000MTUuMDYsMjY2Ljg3NzkgQzQyOS4xOSwyOTQuNzc3OSA0NDUuODUsMzI3LjY4NzkgNDYwLjg1LDM1Ny4zMDc5ICcgZmlsbD0nbm9uZScgaWQ9J2Rpc3BhdGNoZXJOb25CbG9ja2luZy10by1kaXNwYXRjaGVySW50ZXJmYWNlJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzQ2NC42MiwzNjQuNzU3OSw0NjMuNjg0OSwzNTYuMjY1Miw0NTguMzMxMiwzNTguOTc0Miw0NjQuNjIsMzY0Ljc1NzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3MycgeD0nNDQ3JyB5PSczMzAuODk2Jz5pbXBsZW1lbnRzPC90ZXh0PjwvZz48ZyBpZD0nbGlua19kaXNwYXRjaGVyQ2hyb25pY2xlX2Rpc3BhdGNoZXJJbnRlcmZhY2UnPjxwYXRoIGQ9J00yMzcuMTgsMjc1LjM0NzkgQzI0My4xOSwyNzkuMzM3OSAyNDkuMTYsMjgzLjI2NzkgMjU1LDI4Ny4wNjc5IEMzMDEuMTIsMzE3LjA4NzkgMzUyLjc4LDM0OS4yODc5IDM5Ni45NiwzNzYuNDA3OSAnIGZpbGw9J25vbmUnIGlkPSdkaXNwYXRjaGVyQ2hyb25pY2xlLXRvLWRpc3BhdGNoZXJJbnRlcmZhY2UnIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nNDAzLjk5LDM4MC43MDc5LDM5OC43MzMyLDM3My45NzI1LDM5NS42MDA2LDM3OS4wODk4LDQwMy45OSwzODAuNzA3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzczJyB4PSczMzAnIHk9JzMzMC44OTYnPmltcGxlbWVudHM8L3RleHQ+PC9nPjwvZz48L3N2Zz4=)

Figure 8. Command Processing Architecture Level 2 - Dispatcher

```java
package org.apache.fineract.command.core;

import java.util.function.Supplier;

public interface CommandDispatcher {

    <REQ, RES> Supplier<RES> dispatch(Command<REQ> command);
}
```

#### Synchronous

TBD

#### Asynchronous

> [!NOTE]
> Early phase of development. There is a prototype available in module `fineract-command-async`, but needs extensive testing before it can be used in production.

TBD

#### LMAX Disruptor

> [!NOTE]
> Early phase of development. There is a prototype available in module `fineract-command-disruptor`, but needs extensive testing before it can be used in production.

TBD

#### Chronicle Queue

> [!NOTE]
> Early phase of development. No prototype available yet, but most likely module `fineract-command-chronicle` will be used.

TBD

### Command Handler

TBD

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PScyOTBweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjEyMTVweDtoZWlnaHQ6MjkwcHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTIxNSAyOTAnIHdpZHRoPScxMjE1cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5LjA2NzknIHN0eWxlPSdzdHJva2U6IzAwMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycgd2lkdGg9JzM4OCcgeD0nNDA2LjUnIHk9JzUnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzc4JyB4PSc0MTEuNScgeT0nMjQuOTY1OSc+Q29tbWFuZCBQcm9jZXNzaW5nIEFyY2hpdGVjdHVyZSAoTGV2ZWwgMikgLSBIYW5kbGVyczwvdGV4dD48ZyBpZD0nY2x1c3Rlcl9jb21tYW5kU3lzdGVtJz48cmVjdCBoZWlnaHQ9JzIzNycgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojNDQ0NDQ0O3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6Ny4wLDcuMDsnIHdpZHRoPSc1ODMnIHg9JzcnIHk9JzQ3LjA2NzknLz48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPSc2JyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjknIHg9JzI4NCcgeT0nNTUuNDgyJz7Cq2JvdW5kYXJ5wrs8L3RleHQ+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3MycgeD0nMjEyJyB5PSc3Ni4xNzInPkNvbW1hbmQgUHJvY2Vzc2luZzwvdGV4dD48dGV4dCBmaWxsPScjNDQ0NDQ0JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTInIHg9JzI3Mi41JyB5PSc5My42ODgxJz5bU3lzdGVtXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1faGFuZGxlck1hbmFnZXInPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTUzLjQ3NjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE5MycgeD0nMjMnIHk9JzExNC41Njc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nODgnIHk9JzEzNy4zOTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1MScgeD0nNDInIHk9JzE1OC4wMTYxJz5Db21tYW5kIEhhbmRsZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY2JyB4PSc4Ni41JyB5PScxNzkuODA4MSc+UmVnaXN0cnk8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5MicgeD0nNzMuNScgeT0nMTk3LjMyNDInPltSZWdpc3RyeSBQYXR0ZXJuXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PScxMTcuNScgeT0nMjE1LjgwNjInPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2NScgeD0nMzcnIHk9JzIzNC44NzQxJz5NYXBzIGNvbW1hbmQgdHlwZXMgdG88L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjAnIHg9Jzg5LjUnIHk9JzI1My45NDInPmhhbmRsZXJzPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9oYW5kbGVycyc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxMzEuNjg0JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxOTknIHg9JzM3NScgeT0nMTI1LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSc0NDMnIHk9JzE0Ny44OTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1OScgeD0nMzk1JyB5PScxNjguNTE2MSc+Q29tbWFuZCBIYW5kbGVyczwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwMicgeD0nNDIzLjUnIHk9JzE4Ni4wMzIyJz5bTXVsdGlwbGUgSW5zdGFuY2VzXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc0NzIuNScgeT0nMjA0LjUxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3MScgeD0nMzg5JyB5PScyMjMuNTgyJz5FeGVjdXRlIHNwZWNpZmljIGJ1c2luZXNzPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzMyJyB4PSc0NTguNScgeT0nMjQyLjY1Jz5sb2dpYzwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fYnVzaW5lc3NTZXJ2aWNlJz48cmVjdCBmaWxsPScjQjNCM0IzJyBoZWlnaHQ9JzExMi42MTYxJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiNBNkE2QTY7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxOTInIHg9Jzc1MScgeT0nMTM0LjU2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExMicgeD0nNzkxJyB5PScxNTcuMzk2Jz7Cq2V4dGVybmFsX2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDAnIHg9Jzc5NycgeT0nMTc4LjAxNjEnPlNvbWVTZXJ2aWNlPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nOTEnIHg9JzgwMS41JyB5PScxOTUuNTMyMic+W0J1c2luZXNzIFNlcnZpY2VdPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9Jzg0NScgeT0nMjE0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2OCcgeD0nNzY1JyB5PScyMzMuMDgyJz5Tb21lIGRvbWFpbiBvcGVyYXRpb25zPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9kYic+PHBhdGggZD0nTTEwNjYsMTU5LjU2NzkgQzEwNjYsMTQ5LjU2NzkgMTEzMiwxNDkuNTY3OSAxMTMyLDE0OS41Njc5IEMxMTMyLDE0OS41Njc5IDExOTgsMTQ5LjU2NzkgMTE5OCwxNTkuNTY3OSBMMTE5OCwyMjMuMDQ4MiBDMTE5OCwyMzMuMDQ4MiAxMTMyLDIzMy4wNDgyIDExMzIsMjMzLjA0ODIgQzExMzIsMjMzLjA0ODIgMTA2NiwyMzMuMDQ4MiAxMDY2LDIyMy4wNDgyIEwxMDY2LDE1OS41Njc5ICcgZmlsbD0nI0IzQjNCMycgc3R5bGU9J3N0cm9rZTojQTZBNkE2O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTEwNjYsMTU5LjU2NzkgQzEwNjYsMTY5LjU2NzkgMTEzMiwxNjkuNTY3OSAxMTMyLDE2OS41Njc5IEMxMTMyLDE2OS41Njc5IDExOTgsMTY5LjU2NzkgMTE5OCwxNTkuNTY3OSAnIGZpbGw9J25vbmUnIHN0eWxlPSdzdHJva2U6I0E2QTZBNjtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTEyJyB4PScxMDc2JyB5PScxODYuMzk2Jz7Cq2V4dGVybmFsX2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3NicgeD0nMTA5NCcgeT0nMjA3LjAxNjEnPkRhdGFiYXNlPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzknIHg9JzEwOTIuNScgeT0nMjI0LjUzMjInPltCdXNpbmVzcyBkYXRhXTwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfaGFuZGxlck1hbmFnZXJfaGFuZGxlcnMnPjxwYXRoIGQ9J00yMTYuMDMsMTkxLjA2NzkgQzI2Mi41NCwxOTEuMDY3OSAzMTguNjQsMTkxLjA2NzkgMzY2LjU4LDE5MS4wNjc5ICcgZmlsbD0nbm9uZScgaWQ9J2hhbmRsZXJNYW5hZ2VyLXRvLWhhbmRsZXJzJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzM3NC44MiwxOTEuMDY3OSwzNjYuODIsMTg4LjA2NzksMzY2LjgyLDE5NC4wNjc5LDM3NC44MiwxOTEuMDY3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzk3JyB4PScyNDcnIHk9JzE4Ni44OTYnPlJldHVybnMgaGFuZGxlcjwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfaGFuZGxlcnNfYnVzaW5lc3NTZXJ2aWNlJz48cGF0aCBkPSdNNTc0LjMsMTkxLjA2NzkgQzYyNi40LDE5MS4wNjc5IDY5MC4yNSwxOTEuMDY3OSA3NDIuOTYsMTkxLjA2NzkgJyBmaWxsPSdub25lJyBpZD0naGFuZGxlcnMtdG8tYnVzaW5lc3NTZXJ2aWNlJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9Jzc1MC45OSwxOTEuMDY3OSw3NDIuOTksMTg4LjA2NzksNzQyLjk5LDE5NC4wNjc5LDc1MC45OSwxOTEuMDY3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExMCcgeD0nNjA3JyB5PScxNTMuODk2Jz5NYXAgY29tbWFuZHMgdG88L3RleHQ+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzk4JyB4PSc2MTMnIHk9JzE3MC4yNDAxJz5idXNpbmVzcyBzZXJ2aWNlPC90ZXh0Pjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc1NycgeD0nNjM1JyB5PScxODYuNTg0Mic+ZnVuY3Rpb25zPC90ZXh0PjwvZz48ZyBpZD0nbGlua19idXNpbmVzc1NlcnZpY2VfZGInPjxwYXRoIGQ9J005NDMuMDIsMTkxLjA2NzkgQzk4MC4zNCwxOTEuMDY3OSAxMDIyLjUsMTkxLjA2NzkgMTA1Ny40MiwxOTEuMDY3OSAnIGZpbGw9J25vbmUnIGlkPSdidXNpbmVzc1NlcnZpY2UtdG8tZGInIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMTA2NS42OCwxOTEuMDY3OSwxMDU3LjY4LDE4OC4wNjc5LDEwNTcuNjgsMTk0LjA2NzksMTA2NS42OCwxOTEuMDY3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYxJyB4PSc5NzQnIHk9JzE4Ni44OTYnPlN0b3JlIGRhdGE8L3RleHQ+PC9nPjwvZz48L3N2Zz4=)

Figure 9. Command Processing Architecture Level 2 - Handlers

#### Handler Manager

```java
package org.apache.fineract.command.core;

@FunctionalInterface
public interface CommandHandlerManager {

    <REQ, RES> RES handle(Command<REQ> command);
}
```

#### Handler

```java
package org.apache.fineract.command.core;

import com.google.common.reflect.TypeToken;
import lombok.SneakyThrows;

public interface CommandHandler<REQ, RES> {

    RES handle(Command<REQ> command);

    @SneakyThrows
    default RES fallback(Command<REQ> command, Throwable t) {
        // NOTE: any command handler can override this default to implement more specialized fallbacks.
        throw t;
    }

    default boolean matches(Command<REQ> command) {
        TypeToken<REQ> handlerType = new TypeToken<>(getClass()) {};

        return handlerType.getRawType().isAssignableFrom(command.getPayload().getClass());
    }
}
```

### Command Hooks

TBD

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc3MDlweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjEyODRweDtoZWlnaHQ6NzA5cHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTI4NCA3MDknIHdpZHRoPScxMjg0cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5LjA2NzknIHN0eWxlPSdzdHJva2U6IzAwMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycgd2lkdGg9JzM3MScgeD0nNDQ5LjUnIHk9JzUnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzYxJyB4PSc0NTQuNScgeT0nMjQuOTY1OSc+Q29tbWFuZCBQcm9jZXNzaW5nIEFyY2hpdGVjdHVyZSAoTGV2ZWwgMikgLSBIb29rczwvdGV4dD48ZyBpZD0nY2x1c3Rlcl9jb21tYW5kU3lzdGVtJz48cmVjdCBoZWlnaHQ9JzY1Nicgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojNDQ0NDQ0O3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6Ny4wLDcuMDsnIHdpZHRoPScxMjcxJyB4PSc3JyB5PSc0Ny4wNjc5Jy8+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nNicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5JyB4PSc2MjgnIHk9JzU1LjQ4Mic+wqtib3VuZGFyecK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyM0NDQ0NDQnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNzMnIHg9JzU1NicgeT0nNzYuMTcyJz5Db21tYW5kIFByb2Nlc3Npbmc8L3RleHQ+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzUyJyB4PSc2MTYuNScgeT0nOTMuNjg4MSc+W1N5c3RlbV08L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2hvb2tNYW5hZ2VyJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzE1My40NzYxJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScyMDYnIHg9JzgyMicgeT0nMTE0LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSc4OTMuNScgeT0nMTM2Ljg5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI5JyB4PSc4NTguNScgeT0nMTU3LjUxNjEnPkNvbW1hbmQgSG9vazwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzInIHg9Jzg4OScgeT0nMTc5LjMwODEnPk1hbmFnZXI8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5NycgeD0nODc2LjUnIHk9JzE5Ni44MjQyJz5bUmVnaXN0cnkgUGF0dGVybnNdPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzkyMycgeT0nMjE1LjMwNjInPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1NCcgeD0nODQ4JyB5PScyMzQuMzc0MSc+TWFwcyBob29rcyB0byBoYW5kbGVyPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE4NicgeD0nODMyJyB5PScyNTMuNDQyJz5saWZlY3ljbGUgKGJlZm9yZS9hZnRlci9lcnJvcik8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2JlZm9yZUhvb2tzJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzEzMS42ODQnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIxMycgeD0nNDc0LjUnIHk9JzM0NS4wNjc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nNTQ5LjUnIHk9JzM2Ny44OTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE5MycgeD0nNDg0LjUnIHk9JzM4OC41MTYxJz5Db21tYW5kIEJlZm9yZSBIb29rczwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwMicgeD0nNTMwJyB5PSc0MDYuMDMyMic+W011bHRpcGxlIEluc3RhbmNlc108L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nNTc5JyB5PSc0MjQuNTE0MSc+wqA8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTYyJyB4PSc1MDAnIHk9JzQ0My41ODInPkNhbGxlZCBiZWZvcmUgaGFuZGxlciBpczwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MScgeD0nNTUwLjUnIHk9JzQ2Mi42NSc+ZXhlY3V0ZWQ8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2FmdGVySG9va3MnPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTMxLjY4NCcgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMjAxJyB4PSc4MjQuNScgeT0nMzQ1LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSc4OTMuNScgeT0nMzY3Ljg5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTgxJyB4PSc4MzQuNScgeT0nMzg4LjUxNjEnPkNvbW1hbmQgQWZ0ZXIgSG9va3M8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDInIHg9Jzg3NCcgeT0nNDA2LjAzMjInPltNdWx0aXBsZSBJbnN0YW5jZXNdPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzkyMycgeT0nNDI0LjUxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1MCcgeD0nODUwJyB5PSc0NDMuNTgyJz5DYWxsZWQgYWZ0ZXIgaGFuZGxlciBpczwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MScgeD0nODk0LjUnIHk9JzQ2Mi42NSc+ZXhlY3V0ZWQ8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2Vycm9ySG9va3MnPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIwMScgeD0nMTA2MC41JyB5PSczNTQuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzExMjkuNScgeT0nMzc3LjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTgxJyB4PScxMDcwLjUnIHk9JzM5OC4wMTYxJz5Db21tYW5kIEVycm9yIEhvb2tzPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTAyJyB4PScxMTEwJyB5PSc0MTUuNTMyMic+W011bHRpcGxlIEluc3RhbmNlc108L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nMTE1OScgeT0nNDM0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1OCcgeD0nMTA4NCcgeT0nNDUzLjA4Mic+Q2FsbGVkIG9uIGhhbmRsZXIgZXJyb3I8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2hlYWRlckhvb2snPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE4MicgeD0nMjMnIHk9JzU2NC41Njc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nODIuNScgeT0nNTg3LjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTYyJyB4PSczMycgeT0nNjA4LjAxNjEnPlNlcnZsZXQgSGVhZGVyIEhvb2s8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDknIHg9JzU5LjUnIHk9JzYyNS41MzIyJz5bSW50ZXJjZXB0b3IgUGF0dGVybl08L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nMTEyJyB5PSc2NDQuMDE0MSc+wqA8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTUwJyB4PSc0MScgeT0nNjYzLjA4Mic+RXh0cmFjdHMgSFRUUCBoZWFkZXJzPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV90aW1lc3RhbXBIb29rJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzExMi42MTYxJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScyMDQnIHg9JzI0MCcgeT0nNTY0LjU2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSczMTAuNScgeT0nNTg3LjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTM2JyB4PScyNzQnIHk9JzYwOC4wMTYxJz5UaW1lc3RhbXAgSG9vazwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwOScgeD0nMjg3LjUnIHk9JzYyNS41MzIyJz5bSW50ZXJjZXB0b3IgUGF0dGVybl08L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nMzQwJyB5PSc2NDQuMDE0MSc+wqA8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTgwJyB4PScyNTQnIHk9JzY2My4wODInPkFwcGxpZXMgY3VycmVudCB0aW1lc3RhbXA8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX3VzZXJuYW1lSG9vayc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxMzEuNjg0JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScyMDQnIHg9JzQ3OScgeT0nNTU1LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSc1NDkuNScgeT0nNTc3Ljg5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTMyJyB4PSc1MTUnIHk9JzU5OC41MTYxJz5Vc2VyIG5hbWUgSG9vazwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwOScgeD0nNTI2LjUnIHk9JzYxNi4wMzIyJz5bSW50ZXJjZXB0b3IgUGF0dGVybl08L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNCcgeD0nNTc5JyB5PSc2MzQuNTE0MSc+wqA8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTc2JyB4PSc0OTMnIHk9JzY1My41ODInPkdldCBjdXJyZW50IHVzZXIgbmFtZSB2aWE8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTAzJyB4PSc1MjkuNScgeT0nNjcyLjY1Jz5TcHJpbmcgU2VjdXJpdHk8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2F1ZGl0QmVmb3JlSG9vayc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxMTIuNjE2MScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTY2JyB4PSc3MTgnIHk9JzU2NC41Njc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nNzY5LjUnIHk9JzU4Ny4zOTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE0NicgeD0nNzI4JyB5PSc2MDguMDE2MSc+QXVkaXQgQmVmb3JlIEhvb2s8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDknIHg9Jzc0Ni41JyB5PSc2MjUuNTMyMic+W0ludGVyY2VwdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9Jzc5OScgeT0nNjQ0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg0JyB4PSc3NjEnIHk9JzY2My4wODInPkF1ZGl0IGJlZm9yZTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fYXVkaXRBZnRlckhvb2snPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE1NCcgeD0nOTE5JyB5PSc1NjQuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9Jzk2NC41JyB5PSc1ODcuMzk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzQnIHg9JzkyOScgeT0nNjA4LjAxNjEnPkF1ZGl0IEFmdGVyIEhvb2s8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDknIHg9Jzk0MS41JyB5PSc2MjUuNTMyMic+W0ludGVyY2VwdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9Jzk5NCcgeT0nNjQ0LjAxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzcyJyB4PSc5NjInIHk9JzY2My4wODInPkF1ZGl0IGFmdGVyPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9hdWRpdEVycm9ySG9vayc+PHJlY3QgZmlsbD0nIzQzOERENScgaGVpZ2h0PScxMTIuNjE2MScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTU0JyB4PScxMTA4JyB5PSc1NjQuNTY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzExNTMuNScgeT0nNTg3LjM5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTM0JyB4PScxMTE4JyB5PSc2MDguMDE2MSc+QXVkaXQgRXJyb3IgSG9vazwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwOScgeD0nMTEzMC41JyB5PSc2MjUuNTMyMic+W0ludGVyY2VwdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzExODMnIHk9JzY0NC4wMTQxJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3NCcgeD0nMTE1MCcgeT0nNjYzLjA4Mic+QXVkaXQgZXJyb3I8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2hvb2tNYW5hZ2VyX2JlZm9yZUhvb2tzJz48cGF0aCBkPSdNODIxLjc5LDI1Ny4xMjc5IEM3ODAuMzYsMjgzLjQzNzkgNzMyLjU1LDMxMy44MDc5IDY5MC41MSwzNDAuNTA3OSAnIGZpbGw9J25vbmUnIGlkPSdob29rTWFuYWdlci10by1iZWZvcmVIb29rcycgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPSc2ODMuNTUsMzQ0LjkzNzksNjkxLjkxMjYsMzQzLjE4NjUsNjg4LjY5ODksMzM4LjExOTcsNjgzLjU1LDM0NC45Mzc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI3JyB4PSc3NTQnIHk9JzMxMC44OTYnPkl0ZXJhdGVzIGJlZm9yZSBob29rczwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfYmVmb3JlSG9va3NfaGVhZGVySG9vayc+PHBhdGggZD0nTTQ3NC4xNCw0NDkuNzA3OSBDNDAxLjk1LDQ3Ni4zNTc5IDMwNS4yMSw1MTQuNDU3OSAyMjMsNTU1LjA2NzkgQzIxOS4zMyw1NTYuODc3OSAyMTUuNjIsNTU4Ljc3NzkgMjExLjg5LDU2MC43Mjc5ICcgZmlsbD0nbm9uZScgaWQ9J2JlZm9yZUhvb2tzLXRvLWhlYWRlckhvb2snIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMjA0LjcsNTY0LjU0NzksMjEzLjE3MTQsNTYzLjQzNjUsMjEwLjM1MTgsNTU4LjE0MDMsMjA0LjcsNTY0LjU0NzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MScgeD0nMzIwJyB5PSc1MjAuODk2Jz5DYWxscyBob29rPC90ZXh0PjwvZz48ZyBpZD0nbGlua19iZWZvcmVIb29rc190aW1lc3RhbXBIb29rJz48cGF0aCBkPSdNNTA2LjAzLDQ3Ny4zMDc5IEM0NzYsNTAzLjQ0NzkgNDQxLjU5LDUzMy4zOTc5IDQxMi4wNiw1NTkuMDk3OSAnIGZpbGw9J25vbmUnIGlkPSdiZWZvcmVIb29rcy10by10aW1lc3RhbXBIb29rJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzQwNS44NCw1NjQuNTA3OSw0MTMuODQxMiw1NjEuNTExLDQwOS44OTc3LDU1Ni45ODksNDA1Ljg0LDU2NC41MDc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjEnIHg9JzQ2OScgeT0nNTIwLjg5Nic+Q2FsbHMgaG9vazwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfYmVmb3JlSG9va3NfdXNlcm5hbWVIb29rJz48cGF0aCBkPSdNNTgxLDQ3Ny4zMDc5IEM1ODEsNDk5LjM3NzkgNTgxLDUyNC4xNjc5IDU4MSw1NDYuODE3OSAnIGZpbGw9J25vbmUnIGlkPSdiZWZvcmVIb29rcy10by11c2VybmFtZUhvb2snIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nNTgxLDU1NS4wNTc5LDU4NCw1NDcuMDU3OSw1NzgsNTQ3LjA1NzksNTgxLDU1NS4wNTc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjEnIHg9JzU4MicgeT0nNTIwLjg5Nic+Q2FsbHMgaG9vazwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfYmVmb3JlSG9va3NfYXVkaXRCZWZvcmVIb29rJz48cGF0aCBkPSdNNjUwLjAxLDQ3Ny4zMDc5IEM2NzcuNTQsNTAzLjMzNzkgNzA5LjA3LDUzMy4xNDc5IDczNi4xNyw1NTguNzY3OSAnIGZpbGw9J25vbmUnIGlkPSdiZWZvcmVIb29rcy10by1hdWRpdEJlZm9yZUhvb2snIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nNzQyLjI0LDU2NC41MDc5LDczOC40ODk5LDU1Ni44MzA5LDczNC4zNjY3LDU2MS4xODk3LDc0Mi4yNCw1NjQuNTA3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYxJyB4PSc2OTgnIHk9JzUyMC44OTYnPkNhbGxzIGhvb2s8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2hvb2tNYW5hZ2VyX2FmdGVySG9va3MnPjxwYXRoIGQ9J005MjUsMjY3LjA2NzkgQzkyNSwyODkuNTg3OSA5MjUsMzE0LjIzNzkgOTI1LDMzNi42MTc5ICcgZmlsbD0nbm9uZScgaWQ9J2hvb2tNYW5hZ2VyLXRvLWFmdGVySG9va3MnIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nOTI1LDM0NC43NTc5LDkyOCwzMzYuNzU3OSw5MjIsMzM2Ljc1NzksOTI1LDM0NC43NTc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTE3JyB4PSc5MjYnIHk9JzMxMC44OTYnPkl0ZXJhdGVzIGFmdGVyIGhvb2tzPC90ZXh0PjwvZz48ZyBpZD0nbGlua19hZnRlckhvb2tzX2F1ZGl0QWZ0ZXJIb29rJz48cGF0aCBkPSdNOTQ3LjI3LDQ3Ny4zMDc5IEM5NTUuOTMsNTAyLjY3NzkgOTY1LjgyLDUzMS42NDc5IDk3NC40MSw1NTYuODI3OSAnIGZpbGw9J25vbmUnIGlkPSdhZnRlckhvb2tzLXRvLWF1ZGl0QWZ0ZXJIb29rJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9Jzk3Ny4wNCw1NjQuNTA3OSw5NzcuMjkzNSw1NTUuOTY3Nyw5NzEuNjE1NSw1NTcuOTA2OCw5NzcuMDQsNTY0LjUwNzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MScgeD0nOTYzJyB5PSc1MjAuODk2Jz5DYWxscyBob29rPC90ZXh0PjwvZz48ZyBpZD0nbGlua19ob29rTWFuYWdlcl9lcnJvckhvb2tzJz48cGF0aCBkPSdNMTAxOC42MiwyNjcuMzI3OSBDMTAzMC4wMywyNzcuMTQ3OSAxMDQxLjM5LDI4Ny4yMTc5IDEwNTIsMjk3LjA2NzkgQzEwNjkuMzUsMzEzLjE2NzkgMTA4Ny40NywzMzEuMzU3OSAxMTAzLjg0LDM0OC4zNDc5ICcgZmlsbD0nbm9uZScgaWQ9J2hvb2tNYW5hZ2VyLXRvLWVycm9ySG9va3MnIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMTEwOS43OSwzNTQuNTQ3OSwxMTA2LjQxMjMsMzQ2LjY5OTksMTEwMi4wODQ4LDM1MC44NTYsMTEwOS43OSwzNTQuNTQ3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNycgeD0nMTA3MScgeT0nMzEwLjg5Nic+SXRlcmF0ZXMgZXJyb3IgaG9va3M8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2Vycm9ySG9va3NfYXVkaXRFcnJvckhvb2snPjxwYXRoIGQ9J00xMTY3LjQzLDQ2Ny44MDc5IEMxMTcwLjU4LDQ5NS4wNzc5IDExNzQuMzgsNTI4LjAzNzkgMTE3Ny42NCw1NTYuMzA3OSAnIGZpbGw9J25vbmUnIGlkPSdlcnJvckhvb2tzLXRvLWF1ZGl0RXJyb3JIb29rJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzExNzguNTksNTY0LjUzNzksMTE4MC42NTcyLDU1Ni4yNDc4LDExNzQuNjk2NCw1NTYuOTMyNywxMTc4LjU5LDU2NC41Mzc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjEnIHg9JzExNzQnIHk9JzUyMC44OTYnPkNhbGxzIGhvb2s8L3RleHQ+PC9nPjwvZz48L3N2Zz4=)

Figure 10. Command Processing Architecture Level 2 - Hooks

#### Hook Manager

```java
package org.apache.fineract.command.core;

public interface CommandHookManager {

    void before(Command command);

    void after(Command command, Object response);

    void error(Command command, Throwable error);
}
```

#### Before Hooks

TBD

```java
package org.apache.fineract.command.core;

@FunctionalInterface
public interface CommandHookBefore<REQ> {

    void onBefore(Command<REQ> command);
}
```

#### After Hooks

TBD

```java
package org.apache.fineract.command.core;

@FunctionalInterface
public interface CommandHookAfter<REQ, RES> {

    void onAfter(Command<REQ> command, RES response);
}
```

#### Error Hooks

TBD

```java
package org.apache.fineract.command.core;

@FunctionalInterface
public interface CommandHookError<REQ> {

    void onError(Command<REQ> command, Throwable error);
}
```

### Command Store

TBD

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc2MzNweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjkxM3B4O2hlaWdodDo2MzNweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA5MTMgNjMzJyB3aWR0aD0nOTEzcHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5LjA2NzknIHN0eWxlPSdzdHJva2U6IzAwMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycgd2lkdGg9JzM2MycgeD0nMjY4LjI1JyB5PSc1Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzM1MycgeD0nMjczLjI1JyB5PScyNC45NjU5Jz5Db21tYW5kIFByb2Nlc3NpbmcgQXJjaGl0ZWN0dXJlIChMZXZlbCAyKSAtIFN0b3JlPC90ZXh0PjxnIGlkPSdjbHVzdGVyX2NvbW1hbmRTeXN0ZW0nPjxyZWN0IGhlaWdodD0nNDA2JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiM0NDQ0NDQ7c3Ryb2tlLXdpZHRoOjEuMDtmaWxsOm5vbmU7c3Ryb2tlLWRhc2hhcnJheTo3LjAsNy4wOycgd2lkdGg9JzU3NicgeD0nMTI0JyB5PSc0Ny4wNjc5Jy8+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nNicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5JyB4PSczOTcuNScgeT0nNTUuNDgyJz7Cq2JvdW5kYXJ5wrs8L3RleHQ+PHRleHQgZmlsbD0nIzQ0NDQ0NCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3MycgeD0nMzI1LjUnIHk9Jzc2LjE3Mic+Q29tbWFuZCBQcm9jZXNzaW5nPC90ZXh0Pjx0ZXh0IGZpbGw9JyM0NDQ0NDQnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc1MicgeD0nMzg2JyB5PSc5My42ODgxJz5bU3lzdGVtXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fc3RvcmUnPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTMxLjY4NCcgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojM0M3RkMwO3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMjE2JyB4PScyOTgnIHk9JzMwNS4wNjc5Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2MycgeD0nMzc0LjUnIHk9JzMyNy44OTYnPsKrY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyOScgeD0nMzQxLjUnIHk9JzM0OC41MTYxJz5Db21tYW5kIFN0b3JlPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTExJyB4PSczNTAuNScgeT0nMzY2LjAzMjInPltSZXBvc2l0b3J5IFBhdHRlcm5zXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc0MDQnIHk9JzM4NC41MTQxJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODgnIHg9JzMxMicgeT0nNDAzLjU4Mic+U3RvcmVzIGNvbW1hbmRzIGluY2x1ZGluZzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODInIHg9JzMxNScgeT0nNDIyLjY1Jz5yZXF1ZXN0IGFuZCByZXNwb25zZSBkYXRhPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9hdWRpdEJlZm9yZUhvb2snPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE2NicgeD0nNTE4JyB5PScxMTQuMDY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzU2OS41JyB5PScxMzYuODk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNDYnIHg9JzUyOCcgeT0nMTU3LjUxNjEnPkF1ZGl0IEJlZm9yZSBIb29rPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTA5JyB4PSc1NDYuNScgeT0nMTc1LjAzMjInPltJbnRlcmNlcHRvciBQYXR0ZXJuXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc1OTknIHk9JzE5My41MTQxJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4NCcgeD0nNTYxJyB5PScyMTIuNTgyJz5BdWRpdCBiZWZvcmU8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2F1ZGl0QWZ0ZXJIb29rJz48cmVjdCBmaWxsPScjNDM4REQ1JyBoZWlnaHQ9JzExMi42MTYxJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMzQzdGQzA7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxNTQnIHg9JzMyOScgeT0nMTE0LjA2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzYzJyB4PSczNzQuNScgeT0nMTM2Ljg5Nic+wqtjb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTM0JyB4PSczMzknIHk9JzE1Ny41MTYxJz5BdWRpdCBBZnRlciBIb29rPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTA5JyB4PSczNTEuNScgeT0nMTc1LjAzMjInPltJbnRlcmNlcHRvciBQYXR0ZXJuXTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0JyB4PSc0MDQnIHk9JzE5My41MTQxJz7CoDwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3MicgeD0nMzcyJyB5PScyMTIuNTgyJz5BdWRpdCBhZnRlcjwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fYXVkaXRFcnJvckhvb2snPjxyZWN0IGZpbGw9JyM0MzhERDUnIGhlaWdodD0nMTEyLjYxNjEnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzNDN0ZDMDtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE1NCcgeD0nMTQwJyB5PScxMTQuMDY3OScvPjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjMnIHg9JzE4NS41JyB5PScxMzYuODk2Jz7Cq2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzQnIHg9JzE1MCcgeT0nMTU3LjUxNjEnPkF1ZGl0IEVycm9yIEhvb2s8L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDknIHg9JzE2Mi41JyB5PScxNzUuMDMyMic+W0ludGVyY2VwdG9yIFBhdHRlcm5dPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQnIHg9JzIxNScgeT0nMTkzLjUxNDEnPsKgPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzc0JyB4PScxODInIHk9JzIxMi41ODInPkF1ZGl0IGVycm9yPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9wZ0RiJz48cGF0aCBkPSdNNiw1NDMuMDY3OSBDNiw1MzMuMDY3OSA3Miw1MzMuMDY3OSA3Miw1MzMuMDY3OSBDNzIsNTMzLjA2NzkgMTM4LDUzMy4wNjc5IDEzOCw1NDMuMDY3OSBMMTM4LDYwNi41NDgyIEMxMzgsNjE2LjU0ODIgNzIsNjE2LjU0ODIgNzIsNjE2LjU0ODIgQzcyLDYxNi41NDgyIDYsNjE2LjU0ODIgNiw2MDYuNTQ4MiBMNiw1NDMuMDY3OSAnIGZpbGw9JyNCM0IzQjMnIHN0eWxlPSdzdHJva2U6I0E2QTZBNjtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J002LDU0My4wNjc5IEM2LDU1My4wNjc5IDcyLDU1My4wNjc5IDcyLDU1My4wNjc5IEM3Miw1NTMuMDY3OSAxMzgsNTUzLjA2NzkgMTM4LDU0My4wNjc5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojQTZBNkE2O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTInIHg9JzE2JyB5PSc1NjkuODk2Jz7Cq2V4dGVybmFsX2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3NicgeD0nMzQnIHk9JzU5MC41MTYxJz5EYXRhYmFzZTwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY4JyB4PSczOCcgeT0nNjA4LjAzMjInPltQb3N0Z3JlU1FMXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fbXlzcWxEYic+PHBhdGggZD0nTTE3Myw1NDMuMDY3OSBDMTczLDUzMy4wNjc5IDIzOSw1MzMuMDY3OSAyMzksNTMzLjA2NzkgQzIzOSw1MzMuMDY3OSAzMDUsNTMzLjA2NzkgMzA1LDU0My4wNjc5IEwzMDUsNjA2LjU0ODIgQzMwNSw2MTYuNTQ4MiAyMzksNjE2LjU0ODIgMjM5LDYxNi41NDgyIEMyMzksNjE2LjU0ODIgMTczLDYxNi41NDgyIDE3Myw2MDYuNTQ4MiBMMTczLDU0My4wNjc5ICcgZmlsbD0nI0IzQjNCMycgc3R5bGU9J3N0cm9rZTojQTZBNkE2O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTE3Myw1NDMuMDY3OSBDMTczLDU1My4wNjc5IDIzOSw1NTMuMDY3OSAyMzksNTUzLjA2NzkgQzIzOSw1NTMuMDY3OSAzMDUsNTUzLjA2NzkgMzA1LDU0My4wNjc5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojQTZBNkE2O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTInIHg9JzE4MycgeT0nNTY5Ljg5Nic+wqtleHRlcm5hbF9jb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzYnIHg9JzIwMScgeT0nNTkwLjUxNjEnPkRhdGFiYXNlPC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNDMnIHg9JzIxNy41JyB5PSc2MDguMDMyMic+W015U1FMXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fZmlsZSc+PHJlY3QgZmlsbD0nI0IzQjNCMycgaGVpZ2h0PSc3NC40ODAzJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiNBNkE2QTY7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMzInIHg9JzM0MCcgeT0nNTM3LjU2NzknLz48dGV4dCBmaWxsPScjRkZGRkZGJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExMicgeD0nMzUwJyB5PSc1NjAuMzk2Jz7Cq2V4dGVybmFsX2NvbnRhaW5lcsK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyNGRkZGRkYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE2JyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5MCcgeD0nMzYxJyB5PSc1ODEuMDE2MSc+RmlsZSBTeXN0ZW08L3RleHQ+PHRleHQgZmlsbD0nI0ZGRkZGRicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2JyB4PSc0MDMnIHk9JzU5OC41MzIyJz5bXTwvdGV4dD48L2c+PGcgaWQ9J2VsZW1fZHluYW1vRGInPjxwYXRoIGQ9J001MDcuNSw1NDMuMDY3OSBDNTA3LjUsNTMzLjA2NzkgNTk2LDUzMy4wNjc5IDU5Niw1MzMuMDY3OSBDNTk2LDUzMy4wNjc5IDY4NC41LDUzMy4wNjc5IDY4NC41LDU0My4wNjc5IEw2ODQuNSw2MDYuNTQ4MiBDNjg0LjUsNjE2LjU0ODIgNTk2LDYxNi41NDgyIDU5Niw2MTYuNTQ4MiBDNTk2LDYxNi41NDgyIDUwNy41LDYxNi41NDgyIDUwNy41LDYwNi41NDgyIEw1MDcuNSw1NDMuMDY3OSAnIGZpbGw9JyNGRkZGRkYnIHN0eWxlPSdzdHJva2U6I0E2QTZBNjtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J001MDcuNSw1NDMuMDY3OSBDNTA3LjUsNTUzLjA2NzkgNTk2LDU1My4wNjc5IDU5Niw1NTMuMDY3OSBDNTk2LDU1My4wNjc5IDY4NC41LDU1My4wNjc5IDY4NC41LDU0My4wNjc5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojQTZBNkE2O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nIzgwODA4MCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtc3R5bGU9J2l0YWxpYycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTcnIHg9JzUxNy41JyB5PSc1NjkuODk2Jz7Cq2Z1dHVyZcK7wqtleHRlcm5hbF9jb250YWluZXLCuzwvdGV4dD48dGV4dCBmaWxsPScjODA4MDgwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzYnIHg9JzU1OCcgeT0nNTkwLjUxNjEnPkRhdGFiYXNlPC90ZXh0Pjx0ZXh0IGZpbGw9JyM4MDgwODAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzAnIHg9JzU2MScgeT0nNjA4LjAzMjInPltEeW5hbW8gREJdPC90ZXh0PjwvZz48ZyBpZD0nZWxlbV9vdGhlckRiJz48cGF0aCBkPSdNNzE5LjUsNTQzLjA2NzkgQzcxOS41LDUzMy4wNjc5IDgwOCw1MzMuMDY3OSA4MDgsNTMzLjA2NzkgQzgwOCw1MzMuMDY3OSA4OTYuNSw1MzMuMDY3OSA4OTYuNSw1NDMuMDY3OSBMODk2LjUsNjA2LjU0ODIgQzg5Ni41LDYxNi41NDgyIDgwOCw2MTYuNTQ4MiA4MDgsNjE2LjU0ODIgQzgwOCw2MTYuNTQ4MiA3MTkuNSw2MTYuNTQ4MiA3MTkuNSw2MDYuNTQ4MiBMNzE5LjUsNTQzLjA2NzkgJyBmaWxsPScjRkZGRkZGJyBzdHlsZT0nc3Ryb2tlOiNBNkE2QTY7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cGF0aCBkPSdNNzE5LjUsNTQzLjA2NzkgQzcxOS41LDU1My4wNjc5IDgwOCw1NTMuMDY3OSA4MDgsNTUzLjA2NzkgQzgwOCw1NTMuMDY3OSA4OTYuNSw1NTMuMDY3OSA4OTYuNSw1NDMuMDY3OSAnIGZpbGw9J25vbmUnIHN0eWxlPSdzdHJva2U6I0E2QTZBNjtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyM4MDgwODAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTU3JyB4PSc3MjkuNScgeT0nNTY5Ljg5Nic+wqtmdXR1cmXCu8KrZXh0ZXJuYWxfY29udGFpbmVywrs8L3RleHQ+PHRleHQgZmlsbD0nIzgwODA4MCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTYnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1JyB4PSc4MDAuNScgeT0nNTkwLjUxNjEnPi4uLjwvdGV4dD48dGV4dCBmaWxsPScjODA4MDgwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzgyJyB4PSc3NjcnIHk9JzYwOC4wMzIyJz5bT3RoZXIgU3RvcmFnZV08L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2F1ZGl0QmVmb3JlSG9va19zdG9yZSc+PHBhdGggZD0nTTU0Ni40MiwyMjcuMTI3OSBDNTI0LjUxLDI0OS40Mzc5IDQ5OC45NywyNzUuNDI3OSA0NzUuNzQsMjk5LjA3NzkgJyBmaWxsPSdub25lJyBpZD0nYXVkaXRCZWZvcmVIb29rLXRvLXN0b3JlJyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjNjY2NjY2JyBwb2ludHM9JzQ2OS44OCwzMDUuMDM3OSw0NzcuNjI2NywzMDEuNDMzOSw0NzMuMzQ2NywyOTcuMjI4OCw0NjkuODgsMzA1LjAzNzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOCcgeD0nNTE3JyB5PScyNzAuODk2Jz5Vc2VzPC90ZXh0PjwvZz48ZyBpZD0nbGlua19hdWRpdEFmdGVySG9va19zdG9yZSc+PHBhdGggZD0nTTQwNiwyMjcuMTI3OSBDNDA2LDI0OC43Nzc5IDQwNiwyNzMuODg3OSA0MDYsMjk2Ljk2NzkgJyBmaWxsPSdub25lJyBpZD0nYXVkaXRBZnRlckhvb2stdG8tc3RvcmUnIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nNDA2LDMwNS4wMzc5LDQwOSwyOTcuMDM3OSw0MDMsMjk3LjAzNzksNDA2LDMwNS4wMzc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjgnIHg9JzQwNycgeT0nMjcwLjg5Nic+VXNlczwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfYXVkaXRFcnJvckhvb2tfc3RvcmUnPjxwYXRoIGQ9J00yNjkuOSwyMjcuMTI3OSBDMjkxLjE0LDI0OS40Mzc5IDMxNS44OSwyNzUuNDI3OSAzMzguNDEsMjk5LjA3NzkgJyBmaWxsPSdub25lJyBpZD0nYXVkaXRFcnJvckhvb2stdG8tc3RvcmUnIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMzQ0LjA4LDMwNS4wMzc5LDM0MC43MzIzLDI5Ny4xNzcxLDMzNi4zODksMzAxLjMxNjYsMzQ0LjA4LDMwNS4wMzc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjgnIHg9JzMxMycgeT0nMjcwLjg5Nic+VXNlczwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfc3RvcmVfcGdEYic+PHBhdGggZD0nTTI5Ny43OCw0MjQuOTQ3OSBDMjcxLjYsNDM4LjYyNzkgMjQzLjk3LDQ1My44MTc5IDIxOSw0NjkuMDY3OSBDMTg5LjQ0LDQ4Ny4xMTc5IDE1Ny45Nyw1MDkuMDg3OSAxMzEuNzcsNTI4LjIwNzkgJyBmaWxsPSdub25lJyBpZD0nc3RvcmUtdG8tcGdEYicgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPScxMjUuMjMsNTMzLjAwNzksMTMzLjQ1NjksNTMwLjcwMTcsMTI5LjkxMiw1MjUuODYwOSwxMjUuMjMsNTMzLjAwNzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2OScgeD0nMjIwJyB5PSc0ODIuODk2Jz5yZWFkL3dyaXRlczwvdGV4dD48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC1zdHlsZT0naXRhbGljJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzMxJyB4PScyMzknIHk9JzQ5OS4yNDAxJz5bSkRCQ108L3RleHQ+PC9nPjxnIGlkPSdsaW5rX3N0b3JlX215c3FsRGInPjxwYXRoIGQ9J00zNTIuMDEsNDM3LjIwNzkgQzMyNy44NCw0NjYuMzc3OSAyOTkuODgsNTAwLjExNzkgMjc3LjgyLDUyNi43Mjc5ICcgZmlsbD0nbm9uZScgaWQ9J3N0b3JlLXRvLW15c3FsRGInIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nMjcyLjYzLDUzMi45ODc5LDI4MC4wNDM1LDUyOC43NDA2LDI3NS40MjI4LDUyNC45MTMzLDI3Mi42Myw1MzIuOTg3OScgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzY2NjY2NicgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY5JyB4PSczMjQnIHk9JzQ4Mi44OTYnPnJlYWQvd3JpdGVzPC90ZXh0Pjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzEnIHg9JzM0MycgeT0nNDk5LjI0MDEnPltKREJDXTwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfc3RvcmVfZmlsZSc+PHBhdGggZD0nTTQwNiw0MzcuMjA3OSBDNDA2LDQ2Ny4zMjc5IDQwNiw1MDIuMzA3OSA0MDYsNTI5LjMwNzkgJyBmaWxsPSdub25lJyBpZD0nc3RvcmUtdG8tZmlsZScgc3R5bGU9J3N0cm9rZTojRkYwMDAwO3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheTo3LjAsNy4wOycvPjxwb2x5Z29uIGZpbGw9JyNGRjAwMDAnIHBvaW50cz0nNDA2LDUzNy40MDc5LDQwOSw1MjkuNDA3OSw0MDMsNTI5LjQwNzksNDA2LDUzNy40MDc5JyBzdHlsZT0nc3Ryb2tlOiNGRjAwMDA7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzcnIHg9JzQxNScgeT0nNDgyLjg5Nic+d3JpdGVzPC90ZXh0Pjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXN0eWxlPSdpdGFsaWMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTMnIHg9JzQwNycgeT0nNDk5LjI0MDEnPltPbiBFcnJvcl08L3RleHQ+PC9nPjxnIGlkPSdsaW5rX3N0b3JlX2R5bmFtb0RiJz48cGF0aCBkPSdNNDY3LjQzLDQzNy4yMDc5IEM0OTUuMDQsNDY2LjQ5NzkgNTI3LjAxLDUwMC4zOTc5IDU1Mi4xNSw1MjcuMDY3OSAnIGZpbGw9J25vbmUnIGlkPSdzdG9yZS10by1keW5hbW9EYicgc3R5bGU9J3N0cm9rZTojNjY2NjY2O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nIzY2NjY2NicgcG9pbnRzPSc1NTcuNzQsNTMyLjk4NzksNTU0LjQ0MTcsNTI1LjEwNjIsNTUwLjA3MjUsNTI5LjIxODQsNTU3Ljc0LDUzMi45ODc5JyBzdHlsZT0nc3Ryb2tlOiM2NjY2NjY7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjNjY2NjY2JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjknIHg9JzUzMScgeT0nNDkwLjg5Nic+cmVhZC93cml0ZXM8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX3N0b3JlX290aGVyRGInPjxwYXRoIGQ9J001MTQuMDksNDIyLjc4NzkgQzU0NC44Nyw0MzcuNDc3OSA1NzguMzYsNDUzLjcwNzkgNjA5LDQ2OS4wNjc5IEM2NDcuMjcsNDg4LjI0NzkgNjg5LjI4LDUxMC4xNzc5IDcyNC44LDUyOC45Nzc5ICcgZmlsbD0nbm9uZScgaWQ9J3N0b3JlLXRvLW90aGVyRGInIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyM2NjY2NjYnIHBvaW50cz0nNzMyLjI4LDUzMi45NDc5LDcyNi42MTI4LDUyNi41NTQsNzIzLjgwNTksNTMxLjg1Nyw3MzIuMjgsNTMyLjk0NzknIHN0eWxlPSdzdHJva2U6IzY2NjY2NjtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyM2NjY2NjYnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2OScgeD0nNjc2JyB5PSc0OTAuODk2Jz5yZWFkL3dyaXRlczwvdGV4dD48L2c+PC9nPjwvc3ZnPg==)

Figure 11. Command Processing Architecture Level 2 - Store

### Command Audit

TBD

### Command Idempotency

TBD

### Command Observability

TBD

### Refactoring Instructions

> [!IMPORTANT]
> The content of this section will be probably distributed to the other parts of this chapter. Just to say: this is work in progress!

#### General

##### POJOs/DTOs

Please make sure that all POJOs (for request and response types) have a similar structure. They should:

* use Lombok to reduce boilerplate code
* make sure that all annotations are always in the same order as shown below
* avoid `records` for now (we might or might not migrate later from Lombok to `record`)
* each class should implement `java.io.Serializable`
* each class should contain a serialization version set to `1L`

Example:

```java
@Builder
@Data
@NoArgsConstructor
@AllArgsConstructor
@FieldNameConstants
public class DummyRequest implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @NotEmpty(message = "{org.apache.fineract.dummy.content.not-empty}")
    private String content;
}
```

##### Transformation between types

If you need to transform/convert two classes then then use [MapStruct](https://mapstruct.org/) whenever possible. Place the [MapStruct](https://mapstruct.org/[MapStruct]) interfaces under a sibling package `mapping` next to the `data` package (e.g. `org.apache.fineract.xxx.data` and `org.apache.fineract.xxx.mapping`).

##### Package structure (org.apache.fineract.xxx.*)

Please make sure to always follow this package structure pattern (aka layered architecture):

* `api`: contains all REST JAX-RS resource classes (later Spring Web MVC controllers)
* `command`: primarily used for command specific child class implementations of `org.apache.fineract.command.core.Command` (see section "Command Dispatcher preserving Type Information")
* `data`: contains all DTOs (request and response types)
* `domain`: contains all entity/table mapping classes
* `handler`: contains all command handlers
* `service`: contains business logic services
* `mapping`: contains MapStruct interfaces
* `security`: might contain later so called Spring Security "authorization managers" for more complex use cases
* `serialization`: technically we should not need this package anymore after we are done with the refactorings; in theory there could be very complex data structures that are not easily digestable by Jackson; for those case we could still use this package to add de-/serialization helpers (Jackson provides a proper API for this). We should avoid complex structures!
* `starter`: Spring Java configuration that allows us to make Fineract customizable (make parts of the system replaceable)
* `validation`: contains custom Jakarta Validation components/annotations

In general avoid too many nesting levels. Ideally we would only have one additional underneath the base package (`org.apache.fineract.*`) where in turn only the above package patterns are used.

#### REST API

##### Read Requests

The **read requests** (HTTP `GET`) usually only require to refactor (if at all) the business logic services in case they don’t return proper Java POJOs. More often than not service functions have a return type of `org.apache.fineract.infrastructure.core.data.CommandProcessingResult`. This type belongs to the legacy command processing mechanics and basically is just a thin wrapper around a JSON object that is stored in a string variable.

Please name all return types for these read requests consistently. We propose to add always a suffix `Response`; this makes it immediately clear that we are dealing with a data transfer object (vs database mapping entities) and that it’s something that we return to the clients (vs incoming requests). Historically we’ve used `Data` as a suffix, but this doesn’t make it clear if it’s used as input or output. Let’s see an example.

This is how the legacy code used to look like:

```java
public class BusinessDateApiResource {
    // ...
    @GET
    @Consumes({ MediaType.TEXT_HTML, MediaType.APPLICATION_JSON })
    @Produces(MediaType.APPLICATION_JSON)
    @Operation(summary = "List all business dates", description = "")
    public String getBusinessDates(@Context final UriInfo uriInfo) {
        securityContext.authenticatedUser().validateHasReadPermission("BUSINESS_DATE");
        final List<BusinessDateData> foundBusinessDates = this.readPlatformService.findAll();
        ApiRequestJsonSerializationSettings settings = parameterHelper.process(uriInfo.getQueryParameters());
        return this.jsonSerializer.serialize(settings, foundBusinessDates);
    }
    // ...
}
```

This is how the refactored code should look like; there is absolutely no need to manually serialize:

```java
public class BusinessDateApiResource {

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    @Operation(summary = "List all business dates", description = "")
    public List<BusinessDateResponse> getBusinessDates() {
        return businessDateMapper.mapFetchResponse(this.readPlatformService.findAll());
    }
```

On occasions it could be that there could be a service read function that returns a collection of some data structure. In those cases it is fine to use a DTO class with suffix `Data`. In the current code base we have all kinds of variations like `DTO`, `Dto`, `DATA` and so on. Make sure we are consistent with the naming and let’s use the `Data` suffix in these cases.

Very often you’ll see the use of `PlatformSecurityContext` (which is a wrapper around Spring Security’s `org.springframework.security.core.context.SecurityContextHolder`) to validate read permissions. Avoid this please! Fortunately, the fix is relatively easy. We just need to introduce an "Ant matcher" configuration in the Spring web security configuration (`org.apache.fineract.infrastructure.core.config.SecurityConfig`). The change should look something like this:

```java
@Configuration
@ConditionalOnProperty("fineract.security.basicauth.enabled")
                authorizationManagers.add(hasAuthority("TWOFACTOR_AUTHENTICATED"));
            }

            auth.requestMatchers(API_MATCHER.matcher(HttpMethod.OPTIONS, "/api/**")).permitAll()
                    .requestMatchers(API_MATCHER.matcher(HttpMethod.POST, "/api/*/authentication")).permitAll()
```

The nice side effect is that we’ll have all security rules that we are enforcing in one place. This will enable more flexibility with customizations around security (will be handled in the modular security proposal).

##### Write Requests

The **write requests** (HTTP `PUT` and `POST`) are the ones that affect the command processing infrastructure. The JSON body in pretty much all nthe legacy cases is probably represented as a simple string variable that gets passed to a command wrapper class (`org.apache.fineract.commands.domain.CommandWrapper`). All these variables need to be replaced by proper POJO classes that represent the request body. You can get hints how these classes should look like by checking the OpenAPI dummy classes we created to re-introduce the type information for the OpenAPI descriptor (see Swagger annotations).

Usually you’ll have 2 classes to take care of: **requests** (incoming input parameters) and **responses** (outgoing results). These classes are technically **DTOs** (data transfer objects) or **VOs** (value objects) and to make them more recognizable as such I would start standardizing the naming. E.g. if I have a use case aka REST endpoint that creates client data we would name that DTO class `CreateClientRequest`; and if any data needs to be sent back to the client then that class should be called `CreateClientResponse`. This is a very simple mechanic that helps identifying immediately what is what and doesn’t require the developers to come up with any naming stunts. Do not try to re-use these DTOs on multiple endpoints, it’s not worth it. Create a separate DTO for each endpoint. Nice side effect: all this becomes then nicer to read (both in Java code and in the OpenAPI descriptor and the resulting Asciidoc documentation) and this will make it less likely that names are clashing in the OpenAPI descriptor (and during code generation for the Fineract Java Client).

Only new thing that needs to be injected in those REST API resource classes (JAX-RS) or controllers (Spring Web MVC) is the `CommandDispatcher` component that allows you to send requests to the **command dispatcher** which in turn will be processed by **handlers** that eventually call one or more **business logic services**. Results are sent back to the dispatcher and are received in the REST API aka returned by `CommandDispatcher` as a `java.util.Supplier` **functional interface**, i.e. there is only one function to be implemented (`get()`). This small abstraction helps us to standardize how the results are delivered (**synchronous**, **asynchronous**, **non-blocking**) and maintain the same internal API.

##### Jakarta Validation

TBD

Example POJO:

```java
@Builder
@Data
@NoArgsConstructor
@AllArgsConstructor
@FieldNameConstants
public class DummyRequest implements Serializable {

    @Serial
    private static final long serialVersionUID = 1L;

    @NotEmpty(message = "{org.apache.fineract.dummy.content.not-empty}")
    private String content;
}
```

Add your translation keys to `fineract-validation/src/main/resources/ValidationMessages.properties`

##### Future: Spring Web MVC

We will not do this right now, but later we might move away from JAX-RS and introduce **Spring Web MVC** which is mostly just changing the annotations (e.g. `@POST` vs `@PostRequest`). This process should be pretty straight forward and could be even (semi-) automated by using **OpenRewrite** recipes. Once we have proper POJOs for requests and response we can also use **Jakarta Validation** annotations to validate the request content. You’ll see that currently we have an explicit service injected everywhere that does those checks manually (that includes some JSON parsing); very tedious and work intensive and hard to refactor. The first setup with Jakarta Validation take a little longer, but once that is working for one use case it should be pretty much rinse and repeat for the rest. Occasionally for very exotic validations there might be a need to implement **custom validations**. Another advantage of this approach: we can finally add the proper **internationalized error messages** on the server side, not only the translation keys. This removes a ton of code on the client side and ensures that the clients always have the correct messages. Read the Jakarta Validation documentation on how that works and use **Hibernate Validation** to implement this (pretty much the defacto standard library).

#### Command Dispatcher preserving Type Information

`CommandDispatcher` needs to be injected where needed (usually only REST API controllers). By default everything is configured for `sync`(-hronous) processing. Other modes (`async`, `disruptor`) can be easily configured via application.properties, but need more testing and are out of scope for now. As you can see the command object just contains some of metadata (`createdAt`, `username` etc.) and the payload aka request object. Obviously we have different use cases so that **payload** attribute is defined as a generic **type**. Please check the unit test code how to create a command object with payload/request properly.

```java
public class DummyApiResource {
    // ...
    @GET
    DummyResponse dummy(@HeaderParam("x-fineract-request-id") UUID requestId, @HeaderParam("Fineract-Platform-TenantId") String tenantId, DummyRequest request) {
        var command = new DummyCommand();
        command.setId(requestId);
        command.setPayload(request);

        tenantService.set(tenantId);

        Supplier<DummyResponse> result = pipeline.send(command);

        return result.get();
    }
    // ...
}
```

Make sure to create command specific child class of the generic (and abstract) `org.apache.fineract.command.core.Command` class. Example:

```java
@Data
@EqualsAndHashCode(callSuper = true)
public class DummyCommand extends Command<DummyRequest> {}
```

If everything is done correctly then no type information will be lost and everything can be parsed without further help by the Jackson parser. Eventually all handcrafted boilerplate JSON parsing code can be dumped. In rare cases we might need to add de-/serialization helper classes (a concept provided by Jackson) to help the parser identify the types properly.

When we use **Spring Web MVC unit testing** (actually integration testing) gets very easy. Just a couple of annotations and you can execute them pretty much like simple unit tests in your IDE (because Spring Web MVC is a first class citizen obviously in the Spring Framework). NONE of that handcrafted client code like in our current integration tests is required; the tests should be easier to refactor and easier to understand. Writing those tests is **optional** for now, because we have already over **1000 integration tests**. After all those refactorings the REST API should be 100% compatible to upstream even if it uses a different technology stack. If everything passes those ""old"" integration tests then we can be pretty confident that we didn’t mess something up. Migrating the integration tests to simpler Spring Web tests can be done later."

#### Command Handlers

In the current CQRS implementation we have already a concept called **command handlers**. Those handlers are responsible to receive the command objects with their (request) payloads and transform the requests as needed an pass them to one or more business logic services. The refactoring of those handlers should not be too complicated, they just need to implement the Java interface `CommandHandler`. Look at my test samples to see how the implementation details look like.

The old handlers look somewhat like this:

```java
@Service
@CommandType(entity = "PAYMENTTYPE", action = "CREATE")
public class CreatePaymentTypeCommandHandler implements NewCommandSourceHandler {

    private final PaymentTypeWriteService paymentTypeWriteService;

    @Autowired
    public CreatePaymentTypeCommandHandler(final PaymentTypeWriteService paymentTypeWriteService) {
        this.paymentTypeWriteService = paymentTypeWriteService;
    }

    @Override
    @Transactional
    public CommandProcessingResult processCommand(JsonCommand command) {
        return this.paymentTypeWriteService.createPaymentType(command);
    }
}
```

1. and this is how the refactored handler could look like:

```java
@Slf4j
@RequiredArgsConstructor
@Component
public class PaymentTypeCreateCommandHandler implements CommandHandler<PaymentTypeCreateRequest, PaymentTypeCreateResponse> {

    private final PaymentTypeWriteService paymentTypeWriteService;

    @Override
    public PaymentTypeCreateResponse handle(Command<PaymentTypeCreateRequest> command) {
        // TODO: refactor business logic service to accept properly typed request objects as input
        return paymentTypeWriteService.createPaymentType(command.getPayload());
    }
}
```

#### Dispatch Types

##### Sync Execution

This is the default execution mode. Performance is to be expected on par with the current legacy implementation all tests need to work with this mode.

##### Skip: Async Execution

Already included in the current implementation. Just needs a proper **configuration** in **application.properties** (see unit tests). One thing that might need some additional coding: the use of **thread local variables in multi threaded environments** needs some special care to properly work (we use this to identify the current tenant). Also: we should upgrade to JDK 25 and make use of virtual threads (very easy in Spring Boot, simple configuration property). This allows for massive parallel execution that is not bound by physical CPU cores without (take this with a pinch of salt) performance penalties (read: use millions of threads).

##### Skip: Non-blocking Execution

Already included in the current implementation and configurable. I’ve tried a couple of combinations with [LMAX disruptor](https://lmax-exchange.github.io/disruptor/user-guide), but this needs more testing to figure out optimal an configuration. Would be worth to create more realistic JMH benchmarks. I have added a simple one to get a first idea how the mechanics are working.

#### Maker-Checker

This will be part of a separate proposal. The only related feature I’ve added here was command persistence so that you can save commands for deferred execution. Other than that I want to keep this concept (command processing) clean and avoid mixing to many concepts/concerns in one place. This ensures better maintainability. Maker-checker is actually a security related concept and should probably be handled with the proper Spring Security APIs (`AuthorizationManager` interface comes to mind). But again, different proposal and can be ignored here for now.

When we encounter the first need to take care of Maker-Checker then let’s figure out a solution that has minimal impact and do a proper cleanup when the Maker-Checker proposal is available.

[!NOTE] The best guess is that Maker-Checker will probably implemented