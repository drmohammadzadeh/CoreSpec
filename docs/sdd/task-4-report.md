# Task 4 Report: REST API Catalog, CQRS Pipeline & RBAC Security Model

**Date:** 2026-10-28  
**Task:** Task 4 - Extract API Catalog, CQRS Pipeline & RBAC Permissions (Arch Subagent B)  
**Status:** `DONE`  
**Commit Hash:** `f9bd1f37db1ef99b9829460e0677781ab3bc36f7` (Short: `f9bd1f3`)  

---

## 1. Executive Summary

Task 4 of the Apache Fineract 1.15.0 reverse-engineering project has been successfully completed. An exhaustive architectural analysis was performed across the REST API controllers (`*ApiResource.java`), CQRS command processing pipeline (`fineract-command*` and `fineract-provider`), and the Role-Based Access Control (RBAC) security engine (`fineract-security` and `fineract-core`).

The primary deliverable, `docs/architecture/02-api-cqrs-and-security.md`, has been authored and committed to the repository. It includes:
1. **Exhaustive REST API Catalog:** Over 100 endpoints organized into 6 core business domains:
   - Authentication & User Administration (`/v1/authentication`, `/v1/users`, `/v1/roles`, `/v1/permissions`, `/v1/twofactor`)
   - Clients & Groups (`/v1/clients`, `/v1/groups`, `/v1/centers`)
   - Loan Portfolio & Servicing (`/v1/loans`, `/v1/loanproducts`, `/v1/loans/{loanId}/transactions`, `/v1/loans/{loanId}/charges`, `/v1/rescheduleloans`)
   - Savings & Deposits (`/v1/savingsaccounts`, `/v1/savingsproducts`, `/v1/recurringdepositaccounts`, `/v1/fixeddepositaccounts`)
   - General Ledger Accounting (`/v1/glaccounts`, `/v1/journalentries`, `/v1/financialactivitymappings`, `/v1/accountingrules`)
   - Batch, COB & Infrastructure (`/v1/jobs`, `/v1/batches`, `/v1/cob`, `/v1/hooks`, `/v1/makercheckers`, `/v1/audits`)
   - Documented with HTTP methods, query commands (`?command=approve`, `disburse`, `repayment`, etc.), and sample JSON payloads.
2. **CQRS & Command Pipeline Architecture:**
   - Command encapsulation pattern (`CommandWrapperBuilder` and `CommandWrapper`).
   - Production execution flow (`PortfolioCommandSourceWritePlatformServiceImpl` and `SynchronousCommandProcessingService`).
   - Idempotency guarantees (`IdempotencyStoreFilter`, `IdempotencyKeyResolver`, and `m_portfolio_command_source` status codes: `UNDER_PROCESSING [100]`, `AWAITING_APPROVAL [200]`, `PROCESSED [300]`, `REJECTED [400]`, `ERROR [500]`).
   - Modern type-safe CQRS sub-system (`fineract-command` via FINERACT-2169): `CommandDispatcher`, `CommandHandlerManager`, `CommandHookManager` (`Before`, `After`, `Error`), `JdbcCommandStore`, `AsyncCommandDispatcher`, and lock-free `DisruptorCommandDispatcher` (LMAX Disruptor 4.0.0).
   - Complete, valid Mermaid sequence diagram depicting the full lifecycle of write commands, Maker-Checker rollbacks, and webhook propagation.
3. **RBAC & Security Taxonomy:**
   - Authentication schemes: HTTP Basic Auth with `Fineract-Platform-TenantId`, OAuth2 Resource Server with JWT validation, OIDC Federation (Keycloak, Okta, Google), and Two-Factor Authentication (2FA/TOTP) with `Fineract-Platform-TFA-Token`.
   - RBAC data model: `m_appuser`, `m_role`, `m_permission`, `m_appuser_role`, `m_role_permission`.
   - Permission naming grammar: `<ACTION>_<ENTITY>` (e.g. `DISBURSE_LOAN`, `APPROVE_LOAN`).
   - Maker-Checker / 4-Eyes workflow: Permission flagging (`can_maker_checker`), staged rollback (`RollbackTransactionNotApprovedException`), `<TASK>_CHECKER` authorities, and strict prohibition of self-checking (`!isSameMakerCheckerEnabled`).
   - Superuser roles: `ALL_FUNCTIONS`, `ALL_FUNCTIONS_READ`, `CHECKER_SUPER_USER`, `REPORTING_SUPER_USER`.
4. **Architectural EARS Requirements:** 9 standardized bilingual requirement cards (Event-Driven, State-Driven, Complex, Optional Feature, Unwanted Behavior, Ubiquitous) strictly enforcing the normative modal verb `shall`, Persian explanations, failure conditions (`If-Then`), and source code traceability.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/architecture/02-api-cqrs-and-security.md` | Created & Committed (`f9bd1f3`) | Comprehensive reference architecture covering the REST API catalog, CQRS pipeline, Maker-Checker workflow, RBAC permissions, and bilingual EARS requirements. |
| 2 | `docs/sdd/task-4-report.md` | Created | Full task completion report and audit trail. |

---

## 3. Key Findings & Architectural Highlights

1. **Dual-Stack CQRS Evolution:**
   * **Production Pipeline:** Handled by `PortfolioCommandSourceWritePlatformService` and `SynchronousCommandProcessingService`. Wraps requests in `CommandWrapper`, verifies permissions (`actionName + "_" + entityName`), stages initial command in `m_portfolio_command_source`, executes domain service via `NewCommandSourceHandler`, and evaluates Maker-Checker rules.
   * **Modern CQRS Pipeline:** Introduced in `fineract-command` subproject, providing type-safe `Command<REQ>` and `CommandHandler<REQ, RES>`, dispatched through `CommandDispatcher`. Supports synchronous, asynchronous queueing (`fineract-command-async`), and ultra-fast LMAX Disruptor ring buffer (`fineract-command-disruptor`). Pioneered in production by `HookApiResource`.
2. **Idempotency Architecture:**
   * Incoming requests are intercepted by `IdempotencyStoreFilter`, resolving the `Idempotency-Key` HTTP header.
   * Concurrent duplicate invocations trigger `IdempotentCommandProcessUnderProcessingException` (HTTP 409).
   * Completed commands return cached `CommandProcessingResult` without re-executing domain calculations.
3. **Four-Eyes / Maker-Checker Mechanics:**
   * A maker's write action executes business validation, but if `can_maker_checker` is enabled, `CommandSourceService` marks the command as `AWAITING_APPROVAL` (status `200`) and throws `RollbackTransactionNotApprovedException`.
   * The business transaction is completely rolled back in the tenant DB, but the command source record remains persisted.
   * A separate checker user invokes `POST /v1/makercheckers/{auditId}?command=approve`. The system verifies `appUser.getId() != maker.getId()`, validates `<TASK>_CHECKER` permission, re-executes the command with `isApprovedByChecker = true`, and commits the transaction to the database.
4. **Enclosing Batch Transactions:**
   * `POST /v1/batches?enclosingTransaction=true` executes all child requests inside a single atomic database transaction.
   * Webhook notifications (`publishHookEvent`) are deferred using Spring's `TransactionSynchronizationManager.afterCommit()` to prevent ghost webhooks from firing for commands that roll back if a subsequent command in the batch fails.

---

## 4. Verification & Quality Gates

* **Domain API Coverage:** Covered all 6 specified domains (Authentication, Clients/Groups, Loans, Savings, Accounting, Batch/COB/Infrastructure) with exact endpoints, HTTP verbs, command query parameters, and JSON payloads.
* **Mermaid Syntax Validation:** Verified valid Mermaid sequence diagram depicting the complete CQRS lifecycle, including idempotency checks, database transactions, Maker-Checker rollback exceptions, and webhook synchronization.
* **EARS Normative Compliance:** All 9 architectural EARS requirements strictly use the modal verb **`shall`** in their English requirement clauses, accompanied by Persian technical explanations, failure modes (`If-Then`), and source-code traceability matrices.
* **Git Commit Audit:**
  * Added `docs/architecture/02-api-cqrs-and-security.md`.
  * Committed with message `docs(architecture): add REST API catalog, CQRS pipeline and RBAC permissions`.
  * Commit verified: `f9bd1f37db1ef99b9829460e0677781ab3bc36f7`.
