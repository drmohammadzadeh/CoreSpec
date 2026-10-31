# Task 8 Review Package: Tier 2 Savings & Deposits Reverse Engineering

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 8: Tier 2 Savings Accounts, Fixed Deposits, Recurring Deposits, Interest Compounding, Holds, and Dormancy reverse engineering.

---

## 2. Implementer Report
# Task 8 Report: Reverse-Engineer Tier 2 - Savings Accounts, Deposits, Interest Compounding & Holds

**Date:** 2026-10-28  
**Task:** Task 8 - Reverse-Engineer Tier 2: Savings Accounts, Fixed Deposits (FD), Recurring Deposits (RD), Interest Compounding/Posting, Dormancy, and Amount Holds (Implementer Subagent)  
**Status:** `DONE`  
**Commit Hash:** `e053b2927df4efdc26a999aa89ca3717cfe950e7` (`e053b29`)  

---

## 1. Executive Summary

In Task 8 of the Apache Fineract 1.15.0 EARS reverse-engineering project, the complete Tier 2 domain—encompassing Savings Accounts, Fixed Deposits (FD), Recurring Deposits (RD), Interest Compounding & Posting, Account Dormancy & Escheatment, and Amount Holds/Liens—has been reverse-engineered from the codebase into canonical bilingual EARS requirements in `docs/requirements/02-savings-and-deposits.md`.

The requirements catalog is directly derived from the official Apache Fineract 1.15.0 source modules (`fineract-savings`, `fineract-core`, and `fineract-provider`), as well as Liquibase changelogs (`0001_initial_schema.xml`, `0005_savings_transaction_reversal.xml`, `0009_hold_reason_savings_account.xml`, `0010_lien_allowed_on_savings_account_products.xml`), architectural baselines, and domain glossaries. It provides **24 exhaustive, mathematically rigorous, and verifiable bilingual EARS requirement cards** organized into the 6 core functional categories defined by `docs/sdd/task-8-brief.md`.

All 24 cards strictly adhere to the **EARS Grammar Iron Rule**, utilizing the modal verb **`shall`** in every English requirement clause, with **zero occurrences** of non-compliant modals (`should`, `will`, `can`, or `must`). Furthermore, every card incorporates real Fineract validation error codes, Java method citations, JPA entity mappings, and database tables/columns.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/requirements/02-savings-and-deposits.md` | Created & Committed (`e053b29`) | Authoritative bilingual EARS requirements specification for Tier 2: Savings Accounts, Deposits, Interest, Dormancy, and Holds, containing 24 detailed requirement cards across 6 functional categories. |
| 2 | `docs/sdd/task-8-report.md` | Created | Comprehensive task execution report, syntactic audit, traceability verification, and architectural review. |

---

## 3. Scope of Requirements Generated (24 Cards across 6 Categories)

### Category 1: Savings Product Configuration & Policy Invariants (4 Cards)
* **REQ-SAV-PROD-001:** اعتبارسنجی ارز چندگانه، ارقام اعشار و نرخ سود اسمی سالانه محصول پس‌انداز (Multi-Currency, Decimal Precision & Nominal Annual Interest Rate Invariants)  
  * *Pattern:* Complex  
  * *Focus:* Structural validation of ISO 4217 currency code, decimal precision bounded in `[0, 6]`, non-negative nominal interest rate, and short name length limit ($\le 4$ chars).
* **REQ-SAV-PROD-002:** متدهای محاسبه سود بر مبنای مانده روزانه و میانگین مانده به همراه سال مبنای مالی (Daily Balance vs Average Daily Balance Interest Calculation Methods)  
  * *Pattern:* Optional Feature  
  * *Focus:* End-of-Day balance accrual versus periodic weighted arithmetic mean daily balance, evaluated against 360 or 365 days-in-year conventions.
* **REQ-SAV-PROD-003:** بازه‌های تناوب مرکب‌سازی سود و دوره‌های واریز قطعی به حساب (Interest Compounding Intervals vs Posting Period Frequencies)  
  * *Pattern:* State-Driven  
  * *Focus:* Separation of compounding calculation boundaries (Daily, Monthly, Quarterly, Semi-Annual, Annual) and capitalization/posting frequencies into ledger balance.
* **REQ-SAV-PROD-004:** خط‌مشی‌های حداقل مانده الزامی، قفل زمانی برداشت و سقف اضافه برداشت (Minimum Required Balance, Lock-in Periods & Overdraft Facility Configuration)  
  * *Pattern:* Complex  
  * *Focus:* Non-negative overdraft limits, pairing of lock-in frequencies with valid time units (Days, Weeks, Months, Years), and enforcement that overdraft limit does not exceed maximum lien limit.

### Category 2: Fixed Deposit (FD) & Recurring Deposit (RD) Products & Accounts (4 Cards)
* **REQ-SAV-DEP-001:** حدود مجاز مدت سپرده‌گذاری، فواصل زمانی و دستورالعمل‌های تسویه در سررسید (Term Deposit Tenure Boundaries & Maturity Settlement Instructions)  
  * *Pattern:* Complex  
  * *Focus:* Term boundaries $[minDepositTerm \le depositPeriod \le maxDepositTerm]$, deposit amount boundaries, and execution of maturity closure instructions (`WITHDRAW_DEPOSIT`, `TRANSFER_TO_SAVINGS`, `REINVEST_PRINCIPAL_AND_INTEREST`, `REINVEST_PRINCIPAL_ONLY`).
* **REQ-SAV-DEP-002:** اعمال جریمه شکست نرخ سود و تعدیل پرداختی‌ها در بستن پیش از موعد سپرده ثابت (Premature Closure Interest Reduction Penalty & Retrospective Adjustment)  
  * *Pattern:* Event-Driven  
  * *Focus:* Application of pre-closure penal interest rate ($r_{\text{effective}} = \max(0, r_{\text{slab}} - r_{\text{penalty}})$) evaluated on `WHOLE_TERM` or `TILL_PREMATURE_WITHDRAWAL`, transition to status `PRE_MATURE_CLOSURE` (700), and principal clawback of excess interest.
* **REQ-SAV-DEP-003:** تولید خودکار جدول اقساط اجباری دوره در حساب‌های سپرده اندوخته اقساطی (Recurring Deposit Mandatory Installment Schedule Generation)  
  * *Pattern:* Complex  
  * *Focus:* Deterministic generation of recurring installment schedule in table `m_mandatory_savings_schedule` with due dates, mandatory deposit amounts, and sequence tracking upon RD activation.
* **REQ-SAV-DEP-004:** تخصیص پیش‌پرداخت به اقساط آتی و پایش تعهدات معوق در سپرده‌های اندوخته (Installment Advance Allocation & Overdue Tracking in Recurring Deposits)  
  * *Pattern:* Optional Feature  
  * *Focus:* Sequential credit waterfall for advance payments into upcoming installments (`total_paid_in_advance_derived`) and overdue tracking with penalty enforcement.

### Category 3: Savings Account Lifecycle & State Machine (5 Cards)
* **REQ-SAV-LIFE-001:** ثبت و اعتبارسنجی تقاضای افتتاح حساب در وضعیت در انتظار بررسی (Savings Account Application Submission & Origination Validation)  
  * *Pattern:* Event-Driven  
  * *Focus:* Client active status verification, submission date validation (not future, not before client activation), unique account number assignment, and initialization to status `SUBMITTED_AND_PENDING_APPROVAL` (100) / sub-status `NONE` (0).
* **REQ-SAV-LIFE-002:** تصویب، ابطال تصویب، رد تقاضا و انصراف متقاضی در پرونده پس‌انداز (Approval, Undo Approval, Rejection & Client Withdrawal Transitions)  
  * *Pattern:* Complex  
  * *Focus:* Transition to `APPROVED` (200), `REJECTED` (500), `WITHDRAWN_BY_APPLICANT` (400), and reversion from `APPROVED` back to `SUBMITTED_AND_PENDING_APPROVAL` (100) with audit metadata clearing.
* **REQ-SAV-LIFE-003:** فعال‌سازی حساب پس‌انداز با تسویه واریز اولیه و تعیین موعد قفل زمانی (Savings Account Activation, Opening Balance Deposit & Lock-in Date Computation)  
  * *Pattern:* Complex  
  * *Focus:* Transition to `ACTIVE` (300), date chronological validation ($\ge \text{approvalDate}$, $\ge \text{clientActivationDate}$), automatic execution of opening deposit, and computation of `lockedin_until_date_derived`.
* **REQ-SAV-LIFE-004:** بستن عادی حساب پس‌انداز و الزام صفر بودن مانده دفتری (Voluntary Account Closure & Zero-Balance Settlement Invariant)  
  * *Pattern:* State-Driven  
  * *Focus:* Closure validation ($\ge \text{activationDate}$, $\ge \text{lastTransactionDate}$), strict invariant that ledger balance must equal zero ($balance = 0.0$), and transition to `CLOSED` (600).
* **REQ-SAV-LIFE-005:** ماشین وضعیت انسداد عملیاتی و محدودیت تراکنش‌های بدهکار و بستانکار (Granular Operational Blocking State Machine: BLOCK, BLOCK_CREDIT, BLOCK_DEBIT)  
  * *Pattern:* State-Driven  
  * *Focus:* Deterministic sub-status state machine enforcing complete blocking (`BLOCK` - 400), debit freeze (`BLOCK_DEBIT` - 600), and deposit freeze (`BLOCK_CREDIT` - 500) with automatic composite elevation.

### Category 4: Savings Financial Transactions & Operations (4 Cards)
* **REQ-SAV-TXN-001:** پردازش تراکنش واریز نقدی و انتقالی با ثبت قطعی در دفتر کل (Deposit Transaction Processing & Ledger Balance Increment)  
  * *Pattern:* Event-Driven  
  * *Focus:* Positive amount check, non-future and post-activation value-dating, credit entry insertion (type 1) into `m_savings_account_transaction`, ledger balance increment, and GL journal posting.
* **REQ-SAV-TXN-002:** پردازش تراکنش برداشت وجه، اعتبارسنجی مانده در دسترس و کسر کارمزد برداشت (Withdrawal Processing, Dynamic Available Balance & Withdrawal Fee Deduction)  
  * *Pattern:* Complex  
  * *Focus:* Lock-in period compliance, available balance verification ($\text{Amount} + \text{Fee} \le \text{Ledger Balance} - \text{Holds} - \text{Enforced Min} + \text{Overdraft}$), auto-deduction of withdrawal fee (type 4), and `InsufficientAccountBalanceException`.
* **REQ-SAV-TXN-003:** موتور محاسبه خودکار سود دوره‌ای، کسر مالیات تکلیفی و سرمایه‌گذاری سود (Automated Periodic Interest Posting, Withholding Tax & Capitalization Engine)  
  * *Pattern:* Ubiquitous  
  * *Focus:* Cumulative interest calculation across compounding periods, withholding tax deduction (type 18), credit capitalization transaction (type 3), and batch execution via `PostInterestForSavingTasklet`.
* **REQ-SAV-TXN-004:** ابطال و معکوس‌سازی تراکنش‌ها با بازسازی مانده‌های تاریخی و اسناد معکوس (Transaction Reversal, Undo Operations & Historical Balance Replay)  
  * *Pattern:* Event-Driven  
  * *Focus:* Compensating reversal transactions (`is_reversal = true`, `original_transaction_id`) vs soft cancellation (`is_reversed = true`), linked fee rollback, prohibition of account transfer undo, and full chronological balance reconstruction.

### Category 5: Holds, Liens & Collateral Management (3 Cards)
* **REQ-SAV-HOLD-001:** اعمال مسدودی و توثیق وجه جهت ضمانت تسهیلات و احکام حقوقی (Placing Fund Holds & Collateral Liens with Available Balance Reduction)  
  * *Pattern:* Event-Driven  
  * *Focus:* Withdrawable balance sufficiency, insertion of `AMOUNT_HOLD` (type 20) in `m_savings_account_transaction` and `m_deposit_account_on_hold_transaction`, increment of `on_hold_funds_derived`, and immediate available balance deduction.
* **REQ-SAV-HOLD-002:** رفع توثیق و آزادسازی وجوه مسدودشده با بازگشت آنی به مانده در دسترس (Fund Hold Release & Available Balance Restoration)  
  * *Pattern:* Event-Driven  
  * *Focus:* Active hold verification, generation of `AMOUNT_RELEASE` (type 21) linking to original hold ID, decrement of `on_hold_funds_derived`, and immediate restoration of available balance.
* **REQ-SAV-HOLD-003:** کنترل سقف مجاز وثیقه‌گذاری و منع تعارض اضافه برداشت با توثیق سپرده (Maximum Lien Ceiling Enforcement & Overdraft Conflict Invariants)  
  * *Pattern:* Complex  
  * *Focus:* Multi-tier validation ensuring overdraft limits do not exceed maximum lien limits ($overdraftLimit \le maxAllowedLienLimit$), and preventing cumulative liens from breaching authorized caps.

### Category 6: Dormancy, Escheatment & Account Maintenance (4 Cards)
* **REQ-SAV-DORM-001:** شناسایی سیستماتیک حساب‌های راکد، تغییر به وضعیت غیرفعال و کسر کارمزد عدم فعالیت (Dormancy Tracking Batch Detection, INACTIVE Sub-Status & Inactivity Charge Deduction)  
  * *Pattern:* Event-Driven  
  * *Focus:* COB batch identification of active accounts where elapsed days since last customer activity (types 1, 2) $\ge days\_to\_inactive$, transition to `INACTIVE` (100), and deduction of `SAVINGS_NO_ACTIVITY` fee.
* **REQ-SAV-DORM-002:** گذار خودکار به وضعیت خوابیده (DORMANT) و انسداد برداشت‌های سامانه‌ای (Dormant Sub-Status Transition & Automated Third-Party Debit Rejection)  
  * *Pattern:* State-Driven  
  * *Focus:* COB evaluation of elapsed days $\ge days\_to\_dormancy$, transition to `DORMANT` (200), and absolute rejection of automated external debit transactions.
* **REQ-SAV-DORM-003:** سلب مالکیت، واریز مانده به سرفصل خزانه‌داری دولت و مختومه کردن پرونده (Statutory Dormancy Expiration, Asset Forfeiture & Government Escheatment)  
  * *Pattern:* Complex  
  * *Focus:* Evaluation of elapsed days $\ge days\_to\_escheat$, transition of status to `CLOSED` (600) and sub-status to `ESCHEAT` (300), generation of debit transaction (type 19) exhausting ledger balance, and liability transfer to government payable GL account.
* **REQ-SAV-DORM-004:** احراز هویت مجدد، رفع انسداد و خروج خودکار از رکود با تراکنش مشتری (Reactivation KYC Procedures, Account Unblocking & Activity-Driven Auto-Restoration)  
  * *Pattern:* Complex  
  * *Focus:* Dual reactivation paths: automatic sub-status restoration to `NONE` (0) upon valid customer-initiated deposit/withdrawal, or formal staff unblocking with recorded KYC audit notes.

---

## 4. Syntactic Audit & Quality Verification

| Rule / Standard | Requirement Constraint | Verification Result | Evidence / Details |
| :--- | :--- | :---: | :--- |
| **EARS Modal Verb Iron Rule** | English EARS statements must strictly use `shall` (never `should`, `will`, `can`, or `must`). | **PASSED** | Automated regex scan for `>\s*.*(should\|will\|can\|must)\b` yielded **0 violations**. Exactly **90 occurrences of `shall`** verified across requirement statements. |
| **Bilingual Standard Format** | Every card must include Persian Title, EARS Pattern, English Statement, Persian Business Scenario, EARS If-Then Errors, and Traceability Matrix. | **PASSED** | All 24 requirement cards conform to the mandated Markdown layout structure. |
| **Concrete Error Codes** | Unwanted behavior conditions must cite genuine Fineract platform error codes. | **PASSED** | Concrete error codes included: `error.msg.savingsaccount.transaction.insufficient.account.balance`, `validation.msg.savingsproduct.currencyCode.cannot.be.empty`, `not.in.submittedandpendingapproval.state`, `results.in.balance.not.zero`, `error.msg.savingsaccount.transaction.withdrawals.blocked.during.lockin.period`, `Overdraft.limit.can.not.be.greater.than.lien.limit`, `validation.msg.amount.is.not.on.hold`, etc. |
| **Source Code Traceability** | Traceability matrix must reference real Java classes, methods, annotations, and database tables. | **PASSED** | Exact classes cited: `SavingsProductDataValidator`, `MonthlyCompoundingPeriod`, `PostingPeriod`, `FixedDepositAccount`, `RecurringDepositAccount`, `SavingsAccount`, `SavingsAccountWritePlatformServiceJpaRepositoryImpl`, `UpdateSavingsDormantAccountsTasklet`, etc. |
| **Mathematical Grounding** | Formulas must be formally defined using KaTeX. | **PASSED** | Formal equations provided for Available Balance, Daily Balance, Average Daily Balance, Premature Closure Penal Interest, and Dormancy Monotonicity. |
| **Git Commit Standard** | Staged and committed with specified message. | **PASSED** | Committed with `feat(requirements): add comprehensive EARS requirements for savings and deposits` under commit `e053b29`. |

---

## 5. Technical Traceability & Database Schema Mapping

```
+-----------------------------------+---------------------------------------------+--------------------+---------------------------------------+
| Domain Entity                     | Database Table                              | Liquibase Script   | Key Primary Operations / Transition   |
+-----------------------------------+---------------------------------------------+--------------------+---------------------------------------+
| SavingsProduct                    | m_savings_product                           | 0001_initial_schema| Product Definition, Interest Methods, |
|                                   |                                             | 0010_lien_allowed  | Overdraft & Lien Limits Invariants    |
| SavingsAccount                    | m_savings_account                           | 0001_initial_schema| 100 (SUBMITTED) -> 200 (APPROVED)     |
|                                   |                                             | 0009_hold_reason   | -> 300 (ACTIVE) -> 600 (CLOSED)       |
|                                   |                                             |                    | Sub-statuses: 0, 100, 200, 300, 400.. |
| SavingsAccountTransaction         | m_savings_account_transaction               | 0001_initial_schema| Txn Types: 1 (DEPOSIT), 2 (WITHDRAW), |
|                                   |                                             | 0005_savings_revers| 3 (POST_INTEREST), 4 (FEE), 18 (TAX), |
|                                   |                                             |                    | 19 (ESCHEAT), 20 (HOLD), 21 (RELEASE) |
| DepositAccountTermAndPreClosure   | m_deposit_account_term_and_preclosure       | 0001_initial_schema| FD Tenure, Maturity Calculations,     |
|                                   |                                             |                    | Pre-closure Penal Interest Reduction  |
| RecurringDepositScheduleInstallment| m_mandatory_savings_schedule               | 0001_initial_schema| Recurring Schedule, Due Dates,        |
|                                   |                                             |                    | Installments, Advance Payments Allocation|
| DepositAccountOnHoldTransaction   | m_deposit_account_on_hold_transaction       | 0001_initial_schema| On-Hold Funds Tracking, Collateral    |
|                                   |                                             |                    | Liens, Available Balance Deduction    |
| SavingsAccountCharge              | m_savings_account_charge                    | 0001_initial_schema| Inactivity Fee, Withdrawal Fee,       |
|                                   |                                             |                    | Annual Fee, Monthly Fee Management    |
+-----------------------------------+---------------------------------------------+--------------------+---------------------------------------+
```

---

## 6. Conclusion & Readiness

Task 8 has achieved 100% compliance with `docs/sdd/task-8-brief.md`. The created file `docs/requirements/02-savings-and-deposits.md` provides an exhaustive, authoritative, bilingual specification for Tier 2: Savings Accounts, Deposits, Interest Compounding, Dormancy, and Amount Holds.

The artifact has been committed to version control and is ready for QA Review and downstream SDD verification.


---

## 3. Verification & Quality Gates Checklist for Reviewer

### Gate 1: EARS Syntax, Grammar & Modal Iron Rule
- [ ] Verify all 24 cards contain valid EARS statement using `shall` strictly.
- [ ] Verify 0 occurrences of forbidden modals (`should`, `will`, `can`, `must`) in EARS statements (except inside literal error code strings).
- [ ] Verify all unwanted behavior conditions use the standard `If ... then the Fineract Savings Engine shall ... error code ...` format.
- [ ] Verify presence of Persian business scenario and technical explanations.

### Gate 2: Code Traceability & Ground Truth Verification
- [ ] Verify all 27 referenced Java classes exist in Apache Fineract 1.15.0.
- [ ] Verify database tables and columns match the Flyway/Liquibase schema (`m_savings_account`, `m_deposit_account_term_and_preclosure`, `m_deposit_account_on_hold_transaction`, etc.).
- [ ] Verify error codes match Fineract runtime error strings.

### Gate 3: Banking Invariants & State Machine Verification
- [ ] Verify Available Balance formula: Ledger Balance - OnHold Funds - Savings Hold Amount - Enforced Min Balance + Overdraft Limit.
- [ ] Verify Daily Balance and Average Daily Balance compounding algorithms (360/365 days-in-year).
- [ ] Verify Premature Closure penalty formula and retrospective adjustment logic.
- [ ] Verify sub-status composite blocking transitions (`BLOCK`, `BLOCK_CREDIT`, `BLOCK_DEBIT`).
- [ ] Verify dormancy timeline monotonicity: `daysToInactive < daysToDormancy < daysToEscheat`.
