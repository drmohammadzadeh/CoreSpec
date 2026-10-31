# Task 10 Brief: Reverse-Engineering Tier 4 (Close of Business - COB & Batch Operations)

**Task ID:** Task 10  
**Parent Plan:** `docs/superpowers/plans/2026-10-28-fineract-ears-reverse-engineering-plan.md`  
**Deliverable Required:**
1. `docs/requirements/05-cob-and-batch-operations.md`
2. `docs/sdd/task-10-report.md`

---

## 1. Domain Scope & Mission

Reverse-engineer Apache Fineract 1.15.0's batch processing and Close of Business (COB) architecture into a comprehensive, authoritative bilingual EARS specification covering:

1. **COB Orchestration & Remote Partitioning Engine:**
   - Spring Batch multi-threaded chunk processing and remote partitioning (`LoanCOBPartitioner`, `LoanCOBWorkerConfig`, `COBManagerImpl`).
   - Configurable business steps pipeline (`m_batch_business_steps`, `BatchBusinessStepRepository`, `COBBusinessStepService`).
   - Business step execution ordering, dependency enforcement, and error isolation.

2. **Account Locking & Concurrency Control (Inline COB Catch-Up):**
   - Soft/hard pessimistic account locking during COB (`m_loan_account_locks`, `LoanLockingService`, `AccountLockService`).
   - Prevention of concurrent user transactions during batch execution (`AccountLockCannotBeOverruledException`).
   - Inline Loan COB execution (`InlineLoanCOBExecutorService`) for accounts lagging behind system business date when accessed by user or API.

3. **Delinquency Classification & Arrears Aging on COB:**
   - Daily aging calculation: $\text{OverdueDays} = \text{CurrentBusinessDate} - \text{OldestUnpaidDueDate}$.
   - Delinquency bucket classification (`DelinquencyRangeScheduleBusinessStep`, `SetLoanDelinquencyTagsBusinessStep`).
   - Automated assessment of overdue charges and penalties (`ApplyChargeToOverdueLoansBusinessStep`).

4. **Accruals, Interest Recalculation & Fee Amortization on COB:**
   - Automated daily and periodic interest accrual posting (`AddPeriodicAccrualEntriesBusinessStep`).
   - Interest recalculation for progressive and declining balance loans (`LoanInterestRecalculationCOBBusinessStep`).
   - Fee amortization on COB (`BuyDownFeeAmortizationBusinessStep`, `CapitalizedIncomeAmortizationBusinessStep`, `DiscountFeeAmortizationBusinessStep`).

5. **Business Date Advancement, Working Days & Holiday Calendar:**
   - System business date increment invariant: $\text{BusinessDate}_{t+1} = \text{BusinessDate}_t + 1 \text{ day}$.
   - Calendar holidays and office hierarchy bindings (`m_holiday`, `m_holiday_office`).
   - Working days configuration (`m_working_days`) and repayment schedule adjustment strategies (Next Working Day, Same Day, Next Meeting Day).

6. **Batch Job Infrastructure, Monitoring & Failure Recovery:**
   - Spring Batch job registry and cron-triggered execution (`job`, `job_run_history`, `BATCH_JOB_EXECUTION`).
   - Job parameters, idempotency, retry mechanisms, and catch-up runs for missed scheduled windows.

---

## 2. Document Architecture & Standards

`docs/requirements/05-cob-and-batch-operations.md` must follow the established multi-layer standard:

### Section 1: Executive Summary, Architecture & Invariants
- Mathematical and architectural formulations:
  - $\text{COB Completion Condition}: \forall a \in \mathcal{A}_{\text{active}}, \text{COBDate}(a) = \text{TargetBusinessDate}$.
  - Locking invariant: $\text{LockState}(a) \in \{\text{LOCKED\_COB}, \text{LOCKED\_INLINE}, \text{UNLOCKED}\}$.
  - Arrears aging equation: $\text{DPD} = \max\left(0, \text{COBDate} - \min_{i \in \text{Unpaid}} \text{DueDate}(i)\right)$.
  - Working day adjustment function: $\text{AdjustDueDate}(d) = \min \{d' \ge d \mid \text{IsWorkingDay}(d') \land \neg \text{IsHoliday}(d')\}$.
- Spring Batch Chunking & Partitioning sequence diagram.

### Section 2: Catalog Summary Table
- Markdown table mapping Requirement ID, Title (Persian), EARS Pattern, and Primary Source Class.

### Section 3+: Categorized Bilingual EARS Requirement Cards (20 to 24 Cards)
Each card MUST contain:
1. **Title (Persian):** `#### REQ-COB-[CAT]-[NUM]: [عنوان دقیق فارسی]`
2. **EARS Pattern:** (Ubiquitous, Event-Driven, State-Driven, Unwanted Behavior, Optional Feature, Complex)
3. **EARS Statement (English):** Strict adherence to the **`shall`** modal verb iron rule. Forbidden modals (`should`, `will`, `can`, `must`) are strictly prohibited in normative prose.
4. **شرح نیازمندی و سناریوی بیزنس (فارسی):** Comprehensive Persian explanation of the batch/COB operation.
5. **رفتارهای ناخواسته و شروط خطا (EARS If-Then):** Explicit `If...then the Fineract Batch Engine shall...` clauses with authentic error codes/exceptions.
6. **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
   - Exact Java source file path and class name.
   - Method name(s).
   - Runtime error codes and Spring Batch annotations.
   - Database tables and columns.

---

## 3. Mandatory Quality Gates
- **Gate 1 (EARS Grammar):** 100% `shall`, 0 forbidden modals, standard If-Then clauses with error codes.
- **Gate 2 (Traceability):** Grounded in real Java files in `fineract-provider/.../cob/`, `infrastructure/jobs/`, and `fineract-provider/.../holiday/`.
- **Gate 3 (Batch Invariants):** Balanced partitions, monotonic business dates, accurate lock acquisition/release, DPD aging, and holiday rescheduling.
