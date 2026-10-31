# Task 5 Report: Domain Data Model, ERD, State Machines & COB Lifecycle

**Date:** 2026-10-28  
**Task:** Task 5 - Extract Domain Data Model, ERD, State Machines & COB Lifecycle (Arch Subagent C)  
**Status:** `DONE`  
**Commit Hash:** `003d253b39eeb20277cef6735be2a8ad75e270e2` (Short: `003d253`)  

---

## 1. Executive Summary

Task 5 of the Apache Fineract 1.15.0 reverse-engineering project has been successfully executed. An exhaustive architectural investigation was conducted across the core domain entities, Liquibase schema changelogs, JPA domain model classes, account lifecycle state machines, domain event bus, and the Close of Business (COB) batch engine across `fineract-core`, `fineract-loan`, `fineract-savings`, `fineract-accounting`, `fineract-cob`, and `fineract-provider`.

The primary architectural deliverable, `docs/architecture/03-domain-data-events-and-cob.md`, has been authored and committed to the repository (`003d253`). It provides:
1. **Core Banking Domain Data Model & Relational ERD:**
   - Detailed modeling of five core domain aggregates: Customer/Party (`m_client`, `m_group`, `m_office`, `m_staff`), Loan Subsystem (`m_product_loan`, `m_loan`, `m_loan_transaction`, `m_loan_repayment_schedule`, `m_loan_charge`, `m_loan_collateral`), Savings Subsystem (`m_savings_product`, `m_savings_account`, `m_savings_account_transaction`, `m_savings_account_charge`), General Ledger Accounting (`acc_gl_account`, `acc_gl_journal_entry`, `acc_accounting_rule`), and COB/Batch Metadata (`m_loan_account_locks`, `m_batch_business_steps`, `BATCH_JOB_INSTANCE`, `BATCH_JOB_EXECUTION`, `m_external_event`).
   - A complete, valid Mermaid `erDiagram` detailing entity attributes, primary keys, foreign keys, cardinality, and audit columns.
2. **Account State Machines & Financial Lifecycles:**
   - Formal state machine analysis for Loan Accounts (`DefaultLoanLifecycleStateMachine.java`), encompassing all 11 statuses (`SUBMITTED_AND_PENDING_APPROVAL`, `APPROVED`, `ACTIVE`, `TRANSFER_IN_PROGRESS`, `TRANSFER_ON_HOLD`, `WITHDRAWN_BY_CLIENT`, `REJECTED`, `CLOSED_OBLIGATIONS_MET`, `CLOSED_WRITTEN_OFF`, `CLOSED_RESCHEDULE_OUTSTANDING_AMOUNT`, `OVERPAID`), over 30 events (`LOAN_APPROVED`, `LOAN_DISBURSED`, `REPAID_IN_FULL`, `LOAN_OVERPAYMENT`, `LOAN_CREDIT_BALANCE_REFUND`, `LOAN_ADJUST_TRANSACTION`, etc.), and guard conditions.
   - Formal state machine analysis for Savings & Deposit Accounts (`SavingsAccountStatusType`), covering 10 account statuses and the 7-state active sub-status hierarchy (`SavingsAccountSubStatusEnum`: `NONE`, `INACTIVE`, `DORMANT`, `ESCHEAT`, `BLOCK`, `BLOCK_CREDIT`, `BLOCK_DEBIT`).
   - Valid Mermaid `stateDiagram-v2` diagrams for both lifecycles.
3. **Domain Event Bus & Messaging Architecture:**
   - Analysis of `BusinessEventNotifierService` and `BusinessEvent` class hierarchy.
   - Transactional Outbox pattern implemented via `m_external_event`.
   - Apache Avro schema serialization (`fineract-avro-schemas`).
   - Distributed message streaming via Apache Kafka (`KafkaExternalEventProducer` with `aggregateRootId` partition key) and JMS/ActiveMQ (`JMSMultiExternalEventProducer`).
4. **Close of Business (COB) Batch Engine Lifecycle:**
   - Deep architectural analysis of Spring Batch remote partitioning (`LoanCOBManagerConfiguration` and `LoanCOBWorkerConfiguration`).
   - Calendar progression (`BusinessDateType.BUSINESS_DATE` vs `COB_DATE`) and holiday/working-day rescheduling rules (`m_working_days`, `m_holiday`).
   - Configurable business step pipeline (`m_batch_business_steps`) executing 8+ specialized loan steps (accruals, aging buckets, delinquency tagging, overdue charges).
   - Concurrency control and dual-owner locks (`LoanAccountLock` with `LOAN_COB_CHUNK_PROCESSING` and `LOAN_INLINE_COB_PROCESSING`).
   - Zero-downtime on-the-fly Inline COB execution via `LoanCOBApiFilter` and multi-day Catch-Up execution mode (`LoanCOBCatchUpService`).
   - Complete Mermaid sequence and flowchart diagrams detailing the batch pipeline.
5. **Architectural EARS Requirements:**
   - 10 standardized bilingual requirement cards (Ubiquitous, Unwanted Behavior, State-Driven, Event-Driven, Optional Feature, and Complex) strictly enforcing the normative modal verb `shall`, Persian business rationales, failure conditions (`If-Then`), and source-code traceability matrices.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/architecture/03-domain-data-events-and-cob.md` | Created & Committed (`003d253`) | Comprehensive architectural reference covering Domain Data Model, ERD, Loan/Savings State Machines, Domain Events Bus, COB Batch Engine, and bilingual EARS requirements. |
| 2 | `docs/sdd/task-5-report.md` | Created | Full task completion report and architectural audit trail. |

---

## 3. Key Findings & Architectural Highlights

1. **Relational Integrity & Optimistic Concurrency:**
   * All aggregate roots (`m_loan`, `m_savings_account`, `m_client`) inherit from `AbstractAuditableCustom`, guaranteeing strict regulatory auditability (`createdby_id`, `created_date`, `lastmodifiedby_id`, `lastmodified_date`).
   * Optimistic concurrency control is universally enforced via `@Version Long version` columns. Concurrent mutations fail fast with `OptimisticLockException`.
2. **Deterministic State Machine Mechanics:**
   * `DefaultLoanLifecycleStateMachine` is strictly deterministic. Status changes trigger side-effects (e.g. transitioning to `ACTIVE` clears `closedon_date` and `overpaidon_date`; transitioning to `CLOSED_OBLIGATIONS_MET` sets `closedon_date`).
   * Financial transitions dynamically re-evaluate derived balances via `LoanBalanceService#updateLoanSummaryDerivedFields`. An active loan that receives an overpayment transitions directly to `OVERPAID`, and if later adjusted or refunded, returns to `CLOSED_OBLIGATIONS_MET` or `ACTIVE`.
   * Every status transition automatically triggers a `LoanStatusChangedBusinessEvent`.
3. **Transactional Outbox & Strict Partition Ordering:**
   * Business mutations and external event creation occur within the exact same database transaction. Events are staged into `m_external_event` with `status = 'TO_BE_SENT'` and binary payload serialized via compiled Apache Avro schemas.
   * `KafkaExternalEventProducer` groups events by `aggregateRootId`, sending each aggregate's events to Kafka using the account ID as the message key. This guarantees strict chronological FIFO processing across Kafka partitions for every financial account.
4. **Spring Batch Remote Partitioning & Manager-Worker Topology:**
   * `loanCOBJob` runs on the manager node, querying all loan IDs needing COB execution via `RetrieveLoanIdService`.
   * `LoanCOBPartitioner` chunks IDs according to tenant properties (`fineract.cob.partition-size`) and publishes partitions onto Spring Integration channels (Kafka or ActiveMQ queues).
   * Worker nodes process chunks independently. Before processing a chunk, `ApplyLoanLockTasklet` locks accounts in `m_loan_account_locks` with owner `LOAN_COB_CHUNK_PROCESSING`.
   * Inside the chunk, `LoanItemProcessor` dynamically queries `m_batch_business_steps` to execute each enabled business step in exact sequential order (`step_order`).
5. **Zero-Downtime Concurrency via Inline COB:**
   * If an API command targets a loan currently being processed by the COB batch, `LoanCOBApiFilter` detects the lock and immediately returns HTTP 409 Conflict (`LoanIdsHardLockedException`).
   * If a transaction targets a loan that lagged behind the active business date (e.g., missed by a previous batch), `LoanCOBApiFilter` intercepts the request and triggers `InlineLoanCOBExecutorServiceImpl`. This runs the full COB business step pipeline on-the-fly under lock `LOAN_INLINE_COB_PROCESSING`, bringing the account up to date before releasing the lock and allowing the user transaction to proceed.

---

## 4. Verification & Quality Gates

* **Domain Data Model Completeness:** Exhaustively covered Customer/Party (`m_client`, `m_group`, `m_office`, `m_staff`), Loan Subsystem (`m_product_loan`, `m_loan`, `m_loan_transaction`, `m_loan_repayment_schedule`, `m_loan_charge`, `m_loan_collateral`), Savings Subsystem (`m_savings_product`, `m_savings_account`, `m_savings_account_transaction`, `m_savings_account_charge`), General Ledger (`acc_gl_account`, `acc_gl_journal_entry`, `acc_accounting_rule`), and COB/Batch metadata (`m_loan_account_locks`, `m_batch_business_steps`, `BATCH_JOB_EXECUTION`, `m_external_event`).
* **Mermaid Syntax Validation:** Verified valid syntax across:
  - Mermaid `erDiagram` detailing entities, cardinality, attributes, and relationships.
  - Mermaid `stateDiagram-v2` for Loan Lifecycle (11 states, 30+ events).
  - Mermaid `stateDiagram-v2` for Savings Lifecycle & Sub-status hierarchy (10 states, 7 sub-states).
  - Mermaid `flowchart TD` and `sequenceDiagram` for the COB Manager-Worker batch execution and Transactional Outbox pattern.
* **EARS Normative Compliance:** All 10 architectural EARS requirements strictly use the normative modal verb **`shall`** in their English requirement clauses, accompanied by comprehensive Persian technical explanations, failure conditions (`If-Then`), and source-code traceability matrices.
* **Git Commit Audit:**
  - Added `docs/architecture/03-domain-data-events-and-cob.md`.
  - Committed with message `docs(architecture): add domain data model, state machines and COB batch lifecycle`.
  - Verified commit hash: `003d253b39eeb20277cef6735be2a8ad75e270e2` (Short: `003d253`).
