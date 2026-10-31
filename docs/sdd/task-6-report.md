# Task 6 Report: Consolidate Canonical Banking Domain Glossary

**Date:** 2026-10-28  
**Task:** Task 6 - Consolidate Canonical Banking Domain Glossary (Implementer Subagent)  
**Status:** `DONE` (Reviewed & Revised)  
**Commit Hash:** Initial: `c0c1e279c72d9056205caff956f0884ceb31f13d` (`c0c1e27`), Revised: `86858eca97b6a95fbe874a742880c98f98d414a6` (`86858ec`)  

---

## 1. Executive Summary

Task 6 of the Apache Fineract 1.15.0 reverse-engineering project has been successfully completed. By synthesizing the three foundational architectural deliverables (`01-system-modules-and-stack.md`, `02-api-cqrs-and-security.md`, `03-domain-data-events-and-cob.md`), the crawled official documentation (`docs/crawled/pages/stable/sections/07-features.md`, `08-working-capital-loan-projected-amortization-schedule.md`), and the actual Java source code across `apache-fineract-src-1.15.0`, an authoritative, canonical banking domain glossary has been authored and committed to the repository: `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`.

This deliverable functions as the **Binding Semantic Compass (قطب‌نمای معنایی الزام‌آور)** for all downstream reverse-engineering workers (Tasks 7 through 11). It resolves the historical documentation gap where the official Fineract documentation glossary was marked as "TBD" (`docs/crawled/pages/stable/sections/19-glossary.md`).

The document spans **1,577 lines** (176 KB) and systematically articulates **84 canonical domain concepts** organized into the 6 mandated core banking domains, supplemented by **9 cross-module disambiguation rules** and an **84-term master traceability matrix**.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md` | Created & Committed (`c0c1e27`) | Comprehensive, authoritative bilingual banking domain glossary containing 84 term records, 9 cross-module disambiguation rules, and an exhaustive traceability matrix. |
| 2 | `docs/sdd/task-6-report.md` | Created | Comprehensive task execution report, audit trail, and quality assurance record. |

---

## 3. Structural Breakdown & Domain Coverage

The glossary enforces a strict 5-part record format for every concept:
1. **English Term (اصطلاح انگلیسی)**: Standard technical term in codebase, REST APIs, and documentation.
2. **Canonical Persian Equivalent (معادل استاندارد فارسی)**: Accurate banking equivalent according to Iranian and international banking standards.
3. **Domain Definition & Banking Rationale (تعریف جامع و منطق بانکی)**: Financial rationale, economic role, and accounting implications.
4. **Fineract Technical Grounding (تطبیق فنی در فاینراکت)**: Concrete JPA entity classes (`@Entity`), database tables (`m_*`, `acc_*`), enum types, fields, and transaction type constants.
5. **Standard EARS Usage Rule (نحوه استفاده استاندارد در گزاره‌های EARS)**: Prescribed EARS pattern (Ubiquitous, State-Driven, Event-Driven, Optional Feature, Unwanted Behavior, Complex) and a normative bilingual requirement clause strictly employing the modal verb **`shall`** (never `should`, `will`, `can`, or `must`).

### Domain Breakdown:
1. **Lending & Credit Portfolio Domain (۲۶ اصطلاح):**
   * *Core Capital & Return:* Principal (`m_loan.principal_amount`), Interest (`m_loan.nominal_interest_rate_per_period`), Repayment Schedule (`m_loan_repayment_schedule`).
   * *Amortization & Calculation Methods:* Equal Installments (`AmortizationMethod.EQUAL_INSTALLMENTS`), Equal Principal (`AmortizationMethod.EQUAL_PRINCIPAL`), Flat Interest (`InterestMethod.FLAT`), Declining Balance (`InterestMethod.DECLINING_BALANCE`), Daily Calculation Period (`InterestCalculationPeriodMethod.DAILY`), Same as Repayment Period (`SAME_AS_REPAYMENT_PERIOD`).
   * *Grace, Moratorium & Multi-Disbursal:* Grace Period on Principal (`grace_on_principal_periods`), Grace Period on Interest (`grace_on_interest_periods`), Moratorium (`grace_on_arreas_ageing`), Tranche / Multi-disbursal (`LoanDisbursementDetails`, `m_loan_disbursement_detail`).
   * *Restructuring & Risk Recovery:* Restructure / Reschedule (`LoanRescheduleRequest`, `m_loan_reschedule_request`), Foreclosure (`forecloseLoan`), Delinquency (`DelinquencyBucket`, `m_delinquency_bucket`), Non-Performing Asset (`m_loan.is_npa`), Overdue (`completed_derived = false`), Days Past Due (`m_loan_arrears_aging`), Arrears (`total_overdue_derived`), Aging Buckets (`DelinquencyRange`), Write-Off (`CLOSED_WRITTEN_OFF`, status 601), Recovery (`LoanTransactionType.RECOVERY_REPAYMENT`, type 5).
   * *Modern / Progressive Lending:* Capitalized Income / Origination Fee (`m_loan_charge.is_capitalized`), Advanced Payment Allocation Strategy (`m_loan_product_payment_allocation_rule`), Progressive Loan Schedule (`ProgressiveLoanScheduleGenerator`).
2. **Savings & Deposit Accounts Domain (۱۴ اصطلاح):**
   * *Balances & Constraints:* Available Balance (`getAvailableBalance()`), Ledger Balance (`account_balance_derived`), Daily Balance (`DailyBalanceSavingsAccountInterestCalculationStrategy`), Minimum Balance (`min_required_balance`), Hold Amount / Lien (`on_hold_funds_derived`, `m_savings_account_on_hold_funds`).
   * *Deposit Products & Lifecycle:* Fixed Deposit (`FixedDepositAccount`, `m_deposit_account_term_and_pre_closure`), Recurring Deposit (`RecurringDepositAccount`, `m_deposit_account_recurring_detail`), Interest Posting (`POST_INTEREST`, transaction type 3), Compounding Period (`SavingsCompoundingInterestPeriodType`), Premature Closure (`PRE_MATURE_CLOSURE`, status 700), Dormancy (`DORMANT`, sub-status 200), Escheatment (`ESCHEAT`, sub-status 300), Overdraft (`allow_overdraft`), Savings Sub-Status Hierarchy (`SavingsAccountSubStatusEnum`: `NONE`, `INACTIVE`, `DORMANT`, `ESCHEAT`, `BLOCK`, `BLOCK_CREDIT`, `BLOCK_DEBIT`).
3. **General Ledger & Financial Accounting Domain (۱۶ اصطلاح):**
   * *Double-Entry Core & Hierarchy:* Double-Entry Bookkeeping (`validateJournalEntriesAreBalanced`), Chart of Accounts (`GLAccount`, `acc_gl_account`), Asset (`GLAccountType.ASSET`, type 1), Liability (`GLAccountType.LIABILITY`, type 2), Equity (`GLAccountType.EQUITY`, type 3), Income (`GLAccountType.INCOME`, type 4), Expense (`GLAccountType.EXPENSE`, type 5).
   * *Accounting Rules & Postings:* Cash-based Accounting (`AccountingRuleType.CASH_BASED`, rule 2), Accrual-based Accounting - Periodic (`AccountingRuleType.ACCRUAL_PERIODIC`, rule 3), Accrual-based Accounting - Upfront (`AccountingRuleType.ACCRUAL_UPFRONT`, rule 4), Journal Entry (`acc_gl_journal_entry`), Debit (`type_enum = 1`), Credit (`type_enum = 2`), Financial Activity Mapping (`FinancialActivityAccount`, `acc_financial_activity_account`), Suspense Account (`suspense_account = true`), Currency Revaluation (Unrealized FX Gain/Loss).
4. **Charges, Fees & Taxes Domain (۱۰ اصطلاح):**
   * *Charge Types & Timing:* Disbursal Fee (`ChargeTimeType.DISBURSEMENT`, time 1), Specified Due Date Charge (`SPECIFIED_DUE_DATE`, time 2), Installment Fee (`INSTALLMENT_FEE`, time 8), Overdue Penalty (`OVERDUE_INSTALLMENT`, time 9, `is_penalty = true`), Flat Fee (`ChargeCalculationType.FLAT`, calc 1), Pro-rata Fee (`PERCENT_OF_AMOUNT`, calc 2), Capitalized Fee (`is_capitalized = true`).
   * *Taxation:* Withholding Tax (`withhold_tax = true`), Tax Group (`TaxGroup`, `m_tax_group`), Tax Component (`TaxComponent`, `m_tax_component`).
5. **Close of Business (COB) & Core Operations Domain (۹ اصطلاح):**
   * *Batch Orchestration & Progression:* Business Date (`BusinessDateType.BUSINESS_DATE` vs `COB_DATE`), Day-End Accrual (`AddPeriodicAccrualEntriesBusinessStep`), COB Catch-Up (`LoanCOBCatchUpService`), Inline COB (`LoanCOBApiFilter`, `InlineLoanCOBExecution`), Account Lock (`m_loan_account_locks`, `LOAN_COB_CHUNK_PROCESSING` vs `LOAN_INLINE_COB_PROCESSING`), Holiday Calendar (`Holiday`, `WorkingDays`), Reschedule on Holiday (`RescheduleType.NEXT_WORKING_DAY`), Batch Business Steps (`BatchBusinessStep`, `m_batch_business_steps`), Remote Partitioning (`LoanCOBPartitioner`, Spring Batch / Spring Integration).
6. **Platform, Identity & Governance Domain (۹ اصطلاح):**
   * *Security & Tenancy:* Tenant (`FineractPlatformTenant`, `tenants`), Maker (`m_portfolio_command_source.maker_id`), Checker (`m_portfolio_command_source.checker_id`), Segregation of Duties / 4-Eyes (`maker_id != checker_id`), Idempotency Key (`IdempotencyKeyResolver`, `Idempotent-Key` header), Command Wrapper (`CommandWrapper`), Audit Trail (`Audit`, `GET /v1/audits`), Event Sourcing (`_derived` fields replayed from transaction logs), Transactional Outbox (`ExternalEvent`, `m_external_event`, Avro serialization).

---

## 4. Cross-Module Disambiguation Rules

Section 8 of the glossary establishes 9 binding semantic conventions to prevent contradictions during requirement extraction:
1. **Loan Disbursal vs. Repayment**: Strict separation of cash outflow (disbursement) from cash inflow (repayment).
2. **Accrued Interest vs. Capitalized Interest**: Accrued interest remains in `Interest Receivable` without affecting the principal; capitalized interest is appended directly to `principal_amount`.
3. **Fee vs. Penalty vs. Charge**: Fees represent legitimate service charges (`is_penalty = false`); penalties represent punitive overdue charges (`is_penalty = true`); charge is the abstract parent concept.
4. **Write-Off vs. Foreclosure vs. Pre-closure**: Distinguishes accounting bad-debt derecognition (Write-off) from legal loan enforcement (Foreclosure) and voluntary early repayment (Pre-closure).
5. **Available Balance vs. Ledger Balance vs. Daily Balance**: Ledger balance is the raw accounting sum; available balance subtracts liens/holds; daily balance is the end-of-day basis for interest calculations.
6. **Cash vs. Periodic Accrual vs. Upfront Accrual**: Details the journal entry divergence across the three product accounting methodologies.
7. **COB Account Lock vs. Account Lien/Hold**: Separates transient technical batch-exclusion locks (`m_loan_account_locks`) from persistent legal/collateral deposit holds (`m_savings_account_on_hold_funds`).
8. **Segregation of Duties vs. Self-Approval Prohibition**: Clarifies role segregation from the strict domain invariant prohibiting a superuser from approving their own command.
9. **Progressive Loan vs. Classic Schedule Engine**: Defines the architectural boundary between modern daily-amortization progressive loans and legacy schedule generation.

---

## 5. Verification & Quality Assurance

* **Completeness:** All 84 terms requested in the brief are fully articulated across the 6 target domains.
* **Normative EARS Compliance:** Every term contains a formal EARS statement strictly employing the modal verb **`shall`** in its English clause and precise Persian equivalents.
* **Technical Fidelity:** Every term is grounded in concrete Java source classes (`org.apache.fineract.*`) and relational database tables (`m_*`, `acc_*`) verified against Apache Fineract 1.15.0 source code.
* **Git Audit:**
  * Added and committed `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`.
  * Initial commit message: `docs(architecture): add global banking domain glossary` (`c0c1e27`).
  * Revised commit message: `docs(architecture): add document title, section 1 preamble and fix table grounding` (`86858ec`).
* **Subagent Dispatch Constraint:** No other subagents were dispatched, complying with contract requirement 6.

---

## 6. Review & Revision Log (Fix Round 1)

Following the independent review by the Task 6 Reviewer subagent (`d34ab61f-1517-47f7-a948-bdc09b3bd76c`):
1. **Finding 1 (Missing Document Header & Section 1 Preamble):** Resolved. Added top-level H1 title (`# سند واژه‌نامه جامع اصطلاحات بانکی...`) and Section 1 (`## ۱. مقدمه، متدولوژی ۵ لایه‌ای و چارچوب معنایی EARS`) establishing the glossary as the binding semantic compass and defining the 5-layer methodology.
2. **Finding 2 (JPA Table Name for FinancialActivityAccount):** Resolved. Corrected database table name from `acc_financial_activity_account` to `acc_gl_financial_activity_account` in Section 4.14 and in row 54 of the Master Traceability Matrix.
3. **Commit:** `86858ec` successfully verified with clean line diff (`20 insertions(+), 2 deletions(-)`). All checks now **APPROVED**.
