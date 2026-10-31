# Task 4 Brief: Extract API Catalog, CQRS Pipeline & RBAC Permissions (Arch Subagent B)

## Role in Project
Analyze the REST API presentation layer, CQRS command processing pipeline, and Role-Based Access Control (RBAC) security model of Apache Fineract 1.15.0 to author the reference architecture document `docs/architecture/02-api-cqrs-and-security.md`.

## Files to Touch
- Create: `docs/architecture/02-api-cqrs-and-security.md`
- Report: `docs/sdd/task-4-report.md`

## Input Resources
- Skills: `.skills/fineract-java-parser/SKILL.md` and `.skills/fineract-doc-parser/SKILL.md`
- Codebase:
  - Controllers/API resources across `fineract-provider`, `fineract-loan`, `fineract-savings`, `fineract-accounting`, `fineract-client`, etc.
  - CQRS command pipeline: `PortfolioCommandSourceWritePlatformService`, `CommandWrapper`, `CommandProcessingResult`, command handlers in `fineract-command*` and `fineract-provider`
  - Security & Permissions: `useradministration`, `m_permission`, `BasicAuthFilter`, OAuth2/Two-factor configurations
- Crawled Docs: `docs/crawled/pages/stable/sections/06-command-processing.md` and `docs/crawled/pages/stable/sections/13-security.md`

## Deliverables & Detailed Requirements
1. **REST API Catalog:**
   - Catalog all major REST API endpoints grouped by domain:
     - Authentication & User Administration (`/v1/authentication`, `/v1/users`, `/v1/roles`, `/v1/permissions`)
     - Clients & Groups (`/v1/clients`, `/v1/groups`, `/v1/centers`)
     - Loan Portfolio (`/v1/loans`, `/v1/loanproducts`, `/v1/loans/{loanId}/transactions`, `/v1/loans/{loanId}/charges`)
     - Savings & Deposits (`/v1/savingsaccounts`, `/v1/savingsproducts`, `/v1/recurringdepositaccounts`, `/v1/fixeddepositaccounts`)
     - Accounting & General Ledger (`/v1/glaccounts`, `/v1/journalentries`, `/v1/financialactivitymappings`)
     - Batch, COB & Infrastructure (`/v1/jobs`, `/v1/cob`, `/v1/reports`, `/v1/hooks`)
   - Document HTTP methods, query commands (e.g. `?command=approve`, `?command=disburse`), and sample JSON request payloads.
2. **CQRS & Command Pipeline Architecture:**
   - Provide an in-depth analysis of command execution:
     - The Command Pattern in Fineract (`CommandWrapperBuilder`, `CommandWrapper`).
     - Synchronous vs. Asynchronous execution (Disruptor ring-buffer in `fineract-command-disruptor`, JMS/ActiveMQ, direct JDBC in `fineract-command-jdbc`).
     - Command lifecycle hooks (`CommandHook`, `HookService`, Webhooks).
     - Audit logging (`m_portfolio_command_source` table, `CommandProcessingResult`, transaction rollback guarantees).
   - Include a comprehensive Mermaid sequence diagram for the CQRS Command Pipeline.
3. **RBAC & Security Taxonomy:**
   - Document authentication mechanisms (HTTP Basic Auth with Tenant header, OAuth2, 2FA/TOTP).
   - Taxonomy of permissions: Maker-Checker approval workflow, Read/Create/Update/Delete permissions per entity.
4. **Architectural EARS Requirements:**
   - Authored bilingual EARS requirements (Event-Driven, State-Driven, Complex, Unwanted Behavior) strictly using the modal verb `shall`, Persian explanations, failure conditions (`If-Then`), and source-code traceability.

## Report Contract
- Author `docs/architecture/02-api-cqrs-and-security.md`.
- Commit with `git add docs/architecture/02-api-cqrs-and-security.md` and message `docs(architecture): add REST API catalog, CQRS pipeline and RBAC permissions`.
- Write your full report to `docs/sdd/task-4-report.md`.
- Return status (DONE), commit hash, and summary.
