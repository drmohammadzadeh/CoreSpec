---
source_url: https://fineract.apache.org/docs/1.14.0#_resilience
title: "Resilience"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/1.14.0
---

## Resilience

### Introduction Resilience

Fineract had handcrafted retry loops in place for the longest time. A typical retry code would have looked like this:

```java
    @Override
    @SuppressWarnings("AvoidHidingCauseException")
    @SuppressFBWarnings(value = {
            "DMI_RANDOM_USED_ONLY_ONCE" }, justification = "False positive for random object created and used only once")
    public CommandProcessingResult logCommandSource(final CommandWrapper wrapper) {

        boolean isApprovedByChecker = false;
        // check if is update of own account details
        if (wrapper.isUpdateOfOwnUserDetails(this.context.authenticatedUser(wrapper).getId())) {
            // then allow this operation to proceed.
            // maker checker doesn't mean anything here.
            isApprovedByChecker = true; // set to true in case permissions have
                                        // been maker-checker enabled by
                                        // accident.
        } else {
            // if not user changing their own details - check user has
            // permission to perform specific task.
            this.context.authenticatedUser(wrapper).validateHasPermissionTo(wrapper.getTaskPermissionName());
        }
        validateIsUpdateAllowed();

        final String json = wrapper.getJson();
        CommandProcessingResult result = null;
        JsonCommand command;
        int numberOfRetries = 0; (1)
        int maxNumberOfRetries = ThreadLocalContextUtil.getTenant().getConnection().getMaxRetriesOnDeadlock();
        int maxIntervalBetweenRetries = ThreadLocalContextUtil.getTenant().getConnection().getMaxIntervalBetweenRetries();
        final JsonElement parsedCommand = this.fromApiJsonHelper.parse(json);
        command = JsonCommand.from(json, parsedCommand, this.fromApiJsonHelper, wrapper.getEntityName(), wrapper.getEntityId(),
                wrapper.getSubentityId(), wrapper.getGroupId(), wrapper.getClientId(), wrapper.getLoanId(), wrapper.getSavingsId(),
                wrapper.getTransactionId(), wrapper.getHref(), wrapper.getProductId(), wrapper.getCreditBureauId(),
                wrapper.getOrganisationCreditBureauId(), wrapper.getJobName());
        while (numberOfRetries <= maxNumberOfRetries) { (2)
            try {
                result = this.processAndLogCommandService.executeCommand(wrapper, command, isApprovedByChecker);
                numberOfRetries = maxNumberOfRetries + 1; (3)
            } catch (CannotAcquireLockException | ObjectOptimisticLockingFailureException exception) {
                log.debug("The following command {} has been retried  {} time(s)", command.json(), numberOfRetries);
                /***
                 * Fail if the transaction has been retired for maxNumberOfRetries
                 **/
                if (numberOfRetries >= maxNumberOfRetries) {
                    log.warn("The following command {} has been retried for the max allowed attempts of {} and will be rolled back",
                            command.json(), numberOfRetries);
                    throw exception;
                }
                /***
                 * Else sleep for a random time (between 1 to 10 seconds) and continue
                 **/
                try {
                    int randomNum = RANDOM.nextInt(maxIntervalBetweenRetries + 1);
                    Thread.sleep(1000 + (randomNum * 1000));
                    numberOfRetries = numberOfRetries + 1; (4)
                } catch (InterruptedException e) {
                    throw exception;
                }
            } catch (final RollbackTransactionAsCommandIsNotApprovedByCheckerException e) {
                numberOfRetries = maxNumberOfRetries + 1; (3)
                result = this.processAndLogCommandService.logCommand(e.getCommandSourceResult());
            }
        }

        return result;
    }
```

| **1** | counter |
| --- | --- |
| **2** | `while` loop |
| **3** | increment to abort |
| **4** | increment |

For better code quality and readability we introduced [Resilience4j](https://resilience4j.readme.io/docs):

```java
    private final CommandProcessingService processAndLogCommandService;
    private final SchedulerJobRunnerReadService schedulerJobRunnerReadService;
    private final ConfigurationDomainService configurationService;

    @Override
    public CommandProcessingResult logCommandSource(final CommandWrapper wrapper) {
        boolean isApprovedByChecker = false;

        // check if is update of own account details
        if (wrapper.isChangeOfOwnUserDetails(this.context.authenticatedUser(wrapper).getId())) {
            // then allow this operation to proceed.
            // maker checker doesnt mean anything here.
            isApprovedByChecker = true; // set to true in case permissions have
                                        // been maker-checker enabled by
                                        // accident.
        } else {
            // if not user changing their own details - check user has
            // permission to perform specific task.
            this.context.authenticatedUser(wrapper).validateHasPermissionTo(wrapper.getTaskPermissionName());
        }
        validateIsUpdateAllowed();

        final String json = wrapper.getJson();
        final JsonElement parsedCommand = this.fromApiJsonHelper.parse(json);
        JsonCommand command = JsonCommand.from(json, parsedCommand, this.fromApiJsonHelper, wrapper.getEntityName(), wrapper.getEntityId(),
                wrapper.getSubentityId(), wrapper.getGroupId(), wrapper.getClientId(), wrapper.getLoanId(), wrapper.getSavingsId(),
                wrapper.getTransactionId(), wrapper.getHref(), wrapper.getProductId(), wrapper.getCreditBureauId(),
                wrapper.getOrganisationCreditBureauId(), wrapper.getJobName(), wrapper.getLoanExternalId());
```

### Command

#### CommandProcessingService

TBD

```
executeCommand
```

```
fallbackExecuteCommand
```

```
executeCommand
```

### Jobs

#### SchedularWritePlatformService

> [!WARNING]
> This service has a typo and should be called `SchedulerWritePlatformService`.

TBD

```
processJobDetailForExecution
```

```
fallbackProcessJobDetailForExecution
```

```
processJobDetailForExecution
```

### Loan

#### LoanWritePlatformService

TBD

```
recalculateInterest
```

```
fallbackRecalculateInterest
```

```
recalculateInterest
```

### Savings

#### SavingsAccountWritePlatformService

TBD

```
postInterest
```

```
fallbackPostInterest
```

```
postInterest
```