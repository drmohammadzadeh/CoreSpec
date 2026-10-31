# Task 5 Brief: Extract Domain Data Model, ERD, State Machines & COB Lifecycle (Arch Subagent C)

## Role in Project
Analyze the core domain data model, database entities, account state machines, domain event bus, and Close of Business (COB) batch lifecycle in Apache Fineract 1.15.0 to produce `docs/architecture/03-domain-data-events-and-cob.md`.

## Files to Touch
- Create: `docs/architecture/03-domain-data-events-and-cob.md`
- Report: `docs/sdd/task-5-report.md`

## Input Resources
- Skills: `.skills/fineract-java-parser/SKILL.md` and `.skills/fineract-db-schema-parser/SKILL.md`
- Codebase:
  - Entities across `fineract-provider`, `fineract-loan`, `fineract-savings`, `fineract-accounting`, `fineract-core`
  - Liquibase changelogs / Flyway SQL scripts (`fineract-provider/src/main/resources/db/` or `fineract-db/`)
  - Domain Events: `BusinessEvent`, `BusinessEventNotifierService`, external event publishing (Kafka, ActiveMQ)
  - Close of Business (COB): `fineract-cob` module, `LoanCOBConstant`, Spring Batch partitioners, loan locks (`LoanAccountLock`), catch-up mode, day-end accruals
- Crawled Docs: `docs/crawled/pages/stable/sections/05-architecture.md` and `docs/crawled/pages/stable/sections/07-features.md`

## Deliverables & Detailed Requirements
1. **Core Banking Domain Data Model & ERD:**
   - Exhaustively model core entities and relationships:
     - Customer/Party: `m_client`, `m_group`, `m_office`, `m_staff`
     - Loan Subsystem: `m_product_loan`, `m_loan`, `m_loan_transaction`, `m_loan_repayment_schedule`, `m_loan_charge`, `m_loan_collateral`
     - Savings Subsystem: `m_savings_product`, `m_savings_account`, `m_savings_account_transaction`, `m_savings_account_charge`
     - Accounting Subsystem: `acc_gl_account`, `acc_gl_journal_entry`, `acc_rule`
     - COB Subsystem: `m_loan_lock`, `cob_business_step`, `batch_job_execution`
   - Include a valid Mermaid `erDiagram` visualizing key entities, foreign keys, cardinality, and audit columns.
2. **Account State Machines & Lifecycles:**
   - Formal state machine for Loan Accounts (`SubmittedAndPendingApproval` -> `Approved` -> `Disbursed/Active` -> `Closed/Overpaid/Written-Off/WithdrawnByClient`).
   - Formal state machine for Savings Accounts (`SubmittedAndPendingApproval` -> `Approved` -> `Active` -> `Matured/Closed/PrematureClosed/Dormant`).
   - Detail state transitions, triggers, preconditions, and transition rules.
   - Include valid Mermaid `stateDiagram-v2` diagrams for both lifecycles.
3. **Domain Event Bus & Messaging Architecture:**
   - Analyze `BusinessEventNotifierService` and `BusinessEvent` hierarchy (e.g. `LoanDisbursalBusinessEvent`, `LoanRepaymentBusinessEvent`, `SavingsDepositBusinessEvent`).
   - Integration with external event publishers (`ExternalEvent`, Avro serialization in `fineract-avro-schemas`, Kafka partition keys, ActiveMQ).
4. **Close of Business (COB) Batch Engine Lifecycle:**
   - In-depth architectural analysis of the COB engine:
     - Business day progression and holiday/non-working day rules.
     - COB partitioner and step execution pipeline (Accrual step, Loan Delinquency classification step, Locking step).
     - Concurrency and lock management: Inline locks (`LoanAccountLock`), optimistic locking, loan lock recovery, and COB bypass for non-COB branches.
     - Catch-up execution and error handling.
   - Include a Mermaid sequence or flowchart for the COB execution lifecycle.
5. **Architectural EARS Requirements:**
   - Standard bilingual EARS requirement cards (State-Driven, Event-Driven, Complex, Unwanted Behavior, Ubiquitous) strictly enforcing the normative modal verb `shall`, Persian explanations, failure conditions (`If-Then`), and source-code traceability.

## Report Contract
- Author `docs/architecture/03-domain-data-events-and-cob.md`.
- Commit with `git add docs/architecture/03-domain-data-events-and-cob.md` and message `docs(architecture): add domain data model, state machines and COB batch lifecycle`.
- Write your full report to `docs/sdd/task-5-report.md`.
- Return status (DONE), commit hash, and summary.
