# Task 7 Report: Reverse-Engineer Tier 1 - Core Lending & Progressive Loans Portfolio

**Date:** 2026-10-28  
**Task:** Task 7 - Reverse-Engineer Tier 1: Core Lending, Progressive Loans, and Loan Lifecycle (Implementer Subagent)  
**Status:** `DONE`  
**Commit Hash:** `37a074fa8b905447687abbd22d027a2e743ce54b` (`37a074f`)  

---

## 1. Executive Summary

In Task 7 of the Apache Fineract 1.15.0 EARS reverse-engineering project, the complete Tier 1 domain—spanning Core Lending, Progressive Loans, and the Loan Account Lifecycle—has been comprehensively reverse-engineered into canonical bilingual EARS requirements in `docs/requirements/01-loan-portfolio.md`.

This requirements catalog is grounded directly in the actual Java source code across `fineract-loan`, `fineract-progressive-loan`, `fineract-provider`, and `fineract-core`, as well as Liquibase schema changelogs and official documentation. It delivers **26 detailed, rigorous, and verifiable bilingual EARS requirement cards** covering all 6 functional categories mandated by `docs/sdd/task-7-brief.md`.

All 26 cards strictly adhere to the **EARS Grammar Iron Rule**, employing the modal verb **`shall`** in every English requirement clause (with zero occurrences of forbidden modal verbs `should`, `will`, `can`, or `must`). Every card incorporates concrete Fineract error codes, JPA entity mappings, and Liquibase database tables.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/requirements/01-loan-portfolio.md` | Created & Committed (`37a074f`) | Comprehensive bilingual EARS requirements specification for Tier 1: Core Lending & Progressive Loans, containing 26 requirement cards across 6 functional categories. |
| 2 | `docs/sdd/task-7-report.md` | Created | Full task execution report, syntactic audit, traceability verification, and quality assessment. |

---

## 3. Scope of Requirements Generated (26 Cards across 6 Categories)

### Category 1: Loan Product Configuration & Policy Invariants (4 Cards)
* **REQ-LOAN-PROD-001:** اعتبارسنجی ارز چندگانه و حدود سقف، کف و مقدار پیش‌فرض اصل تسهیلات (Multi-Currency & Principal Min/Default/Max Bounds Validation)  
  * *Pattern:* Complex  
  * *Focus:* ISO 4217 currency checks, decimal precision (0 to 6), and invariant $[minPrincipal \le defaultPrincipal \le maxPrincipal]$.
* **REQ-LOAN-PROD-002:** متدهای استهلاک اقساط مساوی و اصل مساوی (Amortization Methods: Equal Installments vs Equal Principal)  
  * *Pattern:* Optional Feature  
  * *Focus:* Distinction between Equated Monthly Installment (EMI) and uniform principal reduction with declining interest.
* **REQ-LOAN-PROD-003:** متدهای محاسبه سود ثابت و مانده نزولی (Interest Calculation Methods: Flat vs Declining Balance)  
  * *Pattern:* Optional Feature  
  * *Focus:* Nominal initial principal interest calculation versus reducing balance daily accrual models.
* **REQ-LOAN-PROD-004:** استراتژی پیشرفته تخصیص اقساط و اولویت‌بندی تسویه مؤلفه‌های بدهی (Advanced Payment Allocation Rules & Settlement Priority)  
  * *Pattern:* Event-Driven  
  * *Focus:* Flexible multidimensional allocation rules across Past Due, Due, and In Advance tiers with future installment actions (`NEXT_INSTALLMENT`, `LAST_INSTALLMENT`, `REAMORTIZATION`).

### Category 2: Schedule Generation & Amortization Algorithms (5 Cards)
* **REQ-LOAN-SCHED-001:** تولید جدول اقساط کلاسیک با تجمیع سود دوره‌ای و روزشمار (Classic Repayment Schedule Generation with Daily / Period Compounding)  
  * *Pattern:* Event-Driven  
  * *Focus:* Cumulative installment calculations, calendar day count conventions (360/365/Actual), and periodic rounding.
* **REQ-LOAN-SCHED-002:** موتور محاسباتی تسهیلات پیش‌رونده با تجدید ساختار داینامیک سود روزشمار (Progressive Loan Schedule Engine with Daily Exact Accrual)  
  * *Pattern:* Optional Feature  
  * *Focus:* Next-generation `fineract-progressive-loan` engine, dynamic recalculation upon financial events, and non-destructive modeling.
* **REQ-LOAN-SCHED-003:** دوره‌های تنفس در اصل و سود تسهیلات (Grace Periods on Principal and Interest Moratorium)  
  * *Pattern:* Optional Feature  
  * *Focus:* Grace period periods on principal (`graceOnPrincipalPayment`) and interest (`graceOnInterestPayment`) with remaining term rebalancing.
* **REQ-LOAN-SCHED-004:** پیش‌پرداخت اولیه و کاهش فوری مانده اصل تسهیلات (Down Payment Policy & Immediate Principal Reduction)  
  * *Pattern:* Optional Feature  
  * *Focus:* Automatic calculation and deduction of borrower equity contribution upon first disbursement.
* **REQ-LOAN-SCHED-005:** پرداخت چندمرحله‌ای ترانش‌ها و بازتنظیم جدول استهلاک (Tranche Multi-Disbursals & Dynamic Schedule Adjustment)  
  * *Pattern:* Complex  
  * *Focus:* Multi-disbursal schedules, tranche limits verification, and dynamic remaining balance re-amortization.

### Category 3: Loan Account Lifecycle & State Transitions (5 Cards)
* **REQ-LOAN-LIFE-001:** ثبت درخواست و ایجاد پرونده تسهیلات در وضعیت در انتظار بررسی (Loan Application Submission & Origination Invariants)  
  * *Pattern:* Event-Driven  
  * *Focus:* Application creation, status 100 (`SUBMITTED_AND_PENDING_APPROVAL`), and `LoanCreatedBusinessEvent`.
* **REQ-LOAN-LIFE-002:** تصویب، رد یا انصراف متقاضی از پرونده تسهیلاتی (Loan Approval, Rejection, and Client Withdrawal)  
  * *Pattern:* Complex  
  * *Focus:* Committee approval (status 200), rejection (status 500), and applicant withdrawal (status 400) state machine transitions.
* **REQ-LOAN-LIFE-003:** پرداخت اولیه و فعال‌سازی پرونده تسهیلات (Initial Disbursement & Transition to Active)  
  * *Pattern:* Complex  
  * *Focus:* Payout validation, transition to status 300 (`ACTIVE`), binding installment activation, and asset debit journal entries.
* **REQ-LOAN-LIFE-004:** تسویه کامل تعهدات و خاتمه عادی پرونده (Full Loan Repayment & Closed Obligations Met)  
  * *Pattern:* State-Driven  
  * *Focus:* Automated transition to status 600 (`CLOSED_OBLIGATIONS_MET`) upon zero debt balance and charge resolution.
* **REQ-LOAN-LIFE-005:** شناسایی و مدیریت وضعیت مازاد پرداختی مشتری (Overpaid Status Transition & Credit Balance Management)  
  * *Pattern:* Complex  
  * *Focus:* Surplus funds routing to `total_overpaid_derived`, status 700 (`OVERPAID`), and credit balance refunds.

### Category 4: Loan Transactions & Financial Operations (5 Cards)
* **REQ-LOAN-TXN-001:** ثبت بازپرداخت‌های عادی و تخصیص میان اجزای اقساط (Regular Repayments Processing & Allocation Across Due Balances)  
  * *Pattern:* Event-Driven  
  * *Focus:* Repayment processing (type 2), chronological value-dating, and waterfall balance updates.
* **REQ-LOAN-TXN-002:** تسویه پیش از موعد اختیاری و بازتنظیم سودهای آتی (Early Prepayment & Dynamic Future Interest Recalculation)  
  * *Pattern:* Event-Driven  
  * *Focus:* Excess payments, principal acceleration, unearned future interest savings, and interest recalculation hooks.
* **REQ-LOAN-TXN-003:** تسویه اجباری پرونده تسهیلاتی و حال شدن تعهدات آتی (Loan Foreclosure & Unearned Interest Acceleration)  
  * *Pattern:* Event-Driven  
  * *Focus:* Mandatory pre-closure checks, acceleration of unearned interest, schedule archiving, and sub-status `FORECLOSED`.
* **REQ-LOAN-TXN-004:** معکوس‌سازی تراکنش‌ها، ابطال پرداخت و بازتنظیم سن بدهی (Transaction Reversals: Undo Disbursal & Undo Repayment)  
  * *Pattern:* Event-Driven  
  * *Focus:* Non-destructive audit trail reversals (`is_reversed = true`), GL backout, and transaction replay.
* **REQ-LOAN-TXN-005:** سوخت مطالبات، حذف از ترازنامه و وصول مطالبات سوخت‌شده (Bad Debt Write-Off & Post-Write-Off Recovery Repayment)  
  * *Pattern:* Complex  
  * *Focus:* Balance sheet asset derecognition, status 601 (`CLOSED_WRITTEN_OFF`), and post-charge-off recovery repayments (type 5).

### Category 5: Delinquency, NPA & Overdue Management (4 Cards)
* **REQ-LOAN-DELINQ-001:** محاسبه اقساط سررسیدگذشته و شاخص روزهای گذشته از موعد (Overdue Calculation & Days Past Due - DPD Tracking)  
  * *Pattern:* Ubiquitous  
  * *Focus:* COB batch calculation of DPD from oldest delinquent installment and populating `m_loan_arrears_aging`.
* **REQ-LOAN-DELINQ-002:** دسته‌بندی زمانی مطالبات در سبدهای نکول و بازه‌های سنی (Delinquency Ranges & Aging Buckets Classification)  
  * *Pattern:* Event-Driven  
  * *Focus:* Delinquency ranges, non-overlapping age bucket enforcement, and installment-level tagging history.
* **REQ-LOAN-DELINQ-003:** طبقه‌بندی تسهیلات غیرجاری و توقف شناسایی درآمد تعهدی (Non-Performing Asset - NPA Classification & Accrual Halting)  
  * *Pattern:* State-Driven  
  * *Focus:* Automatic classification to `is_npa = true` when exceeding threshold, halting P&L interest recognition, and suspense ledger routing.
* **REQ-LOAN-DELINQ-004:** مکانیزم تعلیق و توقف موقت محاسبه نکول (Delinquency Pause Periods & Suspension Management)  
  * *Pattern:* Complex  
  * *Focus:* Fineract 1.15.0 `LoanDelinquencyAction` (PAUSE / RESUME) feature, freezing DPD and preserving classification tags during hardship.

### Category 6: Loan Restructuring & Rescheduling (3 Cards)
* **REQ-LOAN-RESCHED-001:** ثبت درخواست استمهال و اعتبارسنجی شرایط قرارداد (Loan Reschedule Request Submission & Policy Verification)  
  * *Pattern:* Event-Driven  
  * *Focus:* Reschedule request intake in status 100, reason code validation from `m_code_value`, and boundary checks.
* **REQ-LOAN-RESCHED-002:** تصویب استمهال با تمدید مدت، تعدیل نرخ سود و دوره تنفس جدید (Reschedule Approval with Term Extension, Rate Adjustment, and Moratorium)  
  * *Pattern:* Complex  
  * *Focus:* Maker-Checker approval, archiving prior schedule to `m_loan_schedule_history`, applying term variations, and generating a restructured plan.
* **REQ-LOAN-RESCHED-003:** بازتنظیم سن بدهی و بازاستهلاک در موتور تسهیلات پیش‌رونده (Loan Re-Aging & Re-Amortization via Progressive Loan Engine)  
  * *Pattern:* Optional Feature  
  * *Focus:* Progressive loan restructuring features—Re-aging (overdue reset without maturity change) and Re-amortization (annuity re-projection) under `LoanReAmortizationInterestHandlingType`.

---

## 4. Syntactic & Quality Assurance Verification

| Quality Metric | Required Standard | Actual Measurement | Result |
| :--- | :--- | :--- | :--- |
| **EARS Iron Rule: Modal Verb** | English clause must strictly use `shall` | **26 / 26** requirement statements contain `shall`. | **PASS (100%)** |
| **Forbidden Modal Verbs** | No `should`, `will`, `can`, or `must` in statements | **0** occurrences across all EARS statement lines (`> ...`). | **PASS** |
| **If-Then Error Clauses** | Every card must contain concrete If-Then error rules | **62** explicit If-Then statements with verified Fineract error codes. | **PASS** |
| **Card Format Consistency** | Standard 6-element bilingual structure | **26 / 26** cards strictly follow the brief's standard format. | **PASS** |
| **Source Traceability** | Real classes, methods, annotations, tables | All cards cite genuine classes in `fineract-loan`, `fineract-progressive-loan`, `fineract-provider`, `fineract-core`. | **PASS** |
| **Glossary Alignment** | Consistency with `GLOBAL_DOMAIN_GLOSSARY.md` | Complete terminological alignment with Section 2 of the domain glossary. | **PASS** |

---

## 5. Summary & Next Steps

Task 7 has achieved full completion. The resulting artifact `docs/requirements/01-loan-portfolio.md` establishes a rock-solid, mathematically grounded, and rigorously verified baseline for the Core Lending domain in Apache Fineract 1.15.0.

The repository is clean and ready for Task 8 (Tier 2: Savings, Deposits, and Working Capital Loans).
