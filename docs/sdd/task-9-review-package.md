# Task 9 Review Package: Tier 3 Core Accounting, Financial GL & Charges/Tax

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 9: Core Accounting, Financial GL, Double-Entry Balance Conservation, Charges, Fees, Taxes, and Interest Rates reverse engineering.

---

## 2. Implementer Report
# Task 9 Report: Reverse-Engineering Tier 3 - Core Accounting, Financial GL, Charges, Taxes & Rates

**Date:** 2026-10-28  
**Task:** Task 9 - Reverse-Engineer Tier 3: Core Accounting, Financial GL, Double-Entry Conservation, Charges, Taxes, and Interest Rates (Financial & Accounting Systems Reverse Engineer)  
**Status:** `DONE`  
**Commit Hash:** `0f704fc150bd71c18e74f3fdbc0f7ea5116b61d2` (`0f704fc`)  

---

## 1. Executive Summary

In Task 9 of the Apache Fineract 1.15.0 EARS reverse-engineering project, the complete Tier 3 financial engine—spanning two fundamental and interconnected domains: (1) Core Accounting, General Ledger, Subledger Bridges, and Accounting Closures, and (2) Universal Charges, Multi-Dimensional Tax Structures, Floating Rates, and Interest Rate Charts with Demographic Incentives—has been reverse-engineered into two authoritative bilingual EARS requirement specifications:
1. `docs/requirements/03-accounting-and-financial-ledger.md` (18 Requirement Cards)
2. `docs/requirements/04-charges-taxes-and-rates.md` (18 Requirement Cards)

Both documents have been reverse-engineered directly from official Apache Fineract 1.15.0 source modules (`fineract-accounting`, `fineract-charge`, `fineract-tax`, `fineract-rates`, `fineract-core`, `fineract-provider`, `fineract-loan`, and `fineract-savings`), with all 36 requirement cards grounded in verified Java classes, handler methods, domain exceptions, Spring security authorities, and underlying relational tables (`acc_gl_account`, `acc_gl_journal_entry`, `acc_gl_closure`, `acc_gl_financial_activity_account`, `acc_accounting_rule`, `acc_product_mapping`, `m_charge`, `m_loan_charge`, `m_savings_account_charge`, `m_tax_component`, `m_tax_group`, `m_floating_rates`, `m_interest_rate_chart`, `m_interest_incentives`).

Both documents strictly satisfy all **Mandatory Quality Gates**, featuring 100% adherence to the **`shall` modal verb iron rule** (0 forbidden modals outside backticks/quotes), complete bilingual standard layouts, explicit `If...then the Fineract Engine shall...` unwanted behavior clauses with concrete Fineract error codes, and mathematical domain invariant definitions.

---

## 2. Deliverables & Git Commit Details

| # | Deliverable | Git Status | Commit Hash | Description |
| :- | :--- | :--- | :--- | :--- |
| 1 | `docs/requirements/03-accounting-and-financial-ledger.md` | Created & Committed | `0f704fc` | Bilingual EARS requirements specification for Core Accounting, Chart of Accounts, Journal Entries, Double-Entry Balance Conservation, Cash vs Accrual subledger bridges, Financial Activities, GL Closures, and Accounting Rules (18 Cards). |
| 2 | `docs/requirements/04-charges-taxes-and-rates.md` | Created & Committed | `0f704fc` | Bilingual EARS requirements specification for Charges, Calculation Types, Time Frequencies, Min/Max Caps, Free Withdrawals, Loan/Savings/Share Charges, Tax Components, Tax Groups, Withholding Tax, Floating Rates, and Interest Rate Charts with Incentives (18 Cards). |
| 3 | `docs/sdd/task-9-report.md` | Created | Pending commit | Complete reverse-engineering audit report, automated quality gate verification, domain invariants, and traceability matrix. |

**Git Commit Message:**  
`feat(requirements): add EARS requirements for accounting, GL, charges and taxes`

---

## 3. Scope of Requirements Generated (36 Cards across 2 Specifications)

### 3.1. `03-accounting-and-financial-ledger.md` (18 Cards across 6 Sections)

#### Section 1: درخت حساب‌ها و کدینگ دفتر کل (Chart of Accounts & GL Hierarchy)
* **REQ-ACC-COA-001:** تعریف کدینگ، رده‌های حسابداری و طبقه‌بندی سرفصل‌های دفتر کل (Chart of Accounts Hierarchy & Classification)
  * *Pattern:* Complex
  * *Focus:* Validation of unique GL code, non-blank name, and classification strictly into one of the 5 primary types: `ASSET (1)`, `LIABILITY (2)`, `EQUITY (3)`, `INCOME (4)`, or `EXPENSE (5)`.
* **REQ-ACC-COA-002:** ساختار درختی، حساب‌های سرگروه و حساب‌های تفصیلی (GL Account Usage, Parent Hierarchy & Aggregation)
  * *Pattern:* Complex
  * *Focus:* Account usage designation as `HEADER (2)` or `DETAIL (1)`, parent account requirement to be `HEADER`, child-parent classification homogeneity, and hierarchical path generation.
* **REQ-ACC-COA-003:** قیود غیرفعال‌سازی، انتساب به محصولات و حذف سرفصل‌های دفتر کل (GL Account Deactivation & Deletion Constraints)
  * *Pattern:* State-Driven
  * *Focus:* Prevention of deactivation if mapped in `acc_product_mapping`, and prohibition of deletion if having sub-accounts, logged transactions in `acc_gl_journal_entry`, or product mappings.

#### Section 2: مدیریت اسناد حسابداری و دفتر روزنامه (Journal Entries & Balancing)
* **REQ-ACC-JRNL-001:** قانون ناوردای توازن دوطرفه در اسناد حسابداری (Double-Entry Balance Conservation Invariant)
  * *Pattern:* Ubiquitous
  * *Focus:* Strict arithmetic balance conservation: $\sum_{i=1}^n \text{Debit}_i = \sum_{j=1}^m \text{Credit}_j$ across all manual and automated vouchers in the transaction currency.
* **REQ-ACC-JRNL-002:** اعتبارسنجی ثبت دستی اسناد حسابداری و کنترل شعب (Manual Journal Entry Validation & Office Scope)
  * *Pattern:* Event-Driven
  * *Focus:* Enforcement of `manual_journal_entries_allowed == true`, active account status, non-future transaction dating, and valid active office verification.
* **REQ-ACC-JRNL-003:** تغییرناپذیری اسناد حسابداری و فرآیند برگشت سند (Journal Entry Immutability & Transaction Reversal)
  * *Pattern:* Event-Driven
  * *Focus:* Physical ledger immutability, reversal through contra-entries swapping debits and credits, setting `reversed = true`, and audit tracking via `reversal_id`.
* **REQ-ACC-JRNL-004:** محاسبه داینامیک مانده جاری حساب‌ها و تراز آزمایشی (Running Balance Computation & Trial Balance Updates)
  * *Pattern:* Event-Driven
  * *Focus:* Incremental calculation of `office_running_balance` and `organization_running_balance` respecting account classification debit/credit normal balance conventions.

#### Section 3: پل ارتباطی زیردفاتر پرتفوی اعتبارات (Loan Subledger Bridge)
* **REQ-ACC-LOAN-001:** حسابداری مبتنی بر نقدی تسهیلات اعطایی (Cash-Based Accounting for Loans)
  * *Pattern:* Event-Driven
  * *Focus:* Cash mode (`accountingRule == 2`): Debit `Loan Portfolio` and Credit `Fund Source` on disbursement; Credit `Loan Portfolio` for principal and directly credit fee/interest/penalty income on cash collection.
* **REQ-ACC-LOAN-002:** حسابداری تعهدی دوره‌ای و شناختی تسهیلات (Accrual-Based Accounting for Loans - Periodic & Upfront)
  * *Pattern:* Event-Driven
  * *Focus:* Accrual mode (`PERIODIC_ACCRUAL` / `UPFRONT_ACCRUAL`): Debit `Receivable` asset accounts and Credit `Income` accounts on accrual run; Credit `Receivable` accounts upon subsequent cash collection.
* **REQ-ACC-LOAN-003:** ثبت اسناد سوخت مطالبات، تعدیل تعهدات و بازیافت مطالبات سوخت‌شده (Loan Write-Off, Charge-Off & Recovery Postings)
  * *Pattern:* Event-Driven
  * *Focus:* Write-off debit to `Losses Written Off` expense and credit to `Loan Portfolio`; recovery repayments debiting `Fund Source` and crediting `Income from Recovery`.

#### Section 4: پل ارتباطی زیردفاتر سپرده‌ها و سهام (Savings & Shares Subledger Bridge)
* **REQ-ACC-SAV-001:** حسابداری نقدی حساب‌های پس‌انداز و سپرده (Cash-Based Accounting for Savings & Deposits)
  * *Pattern:* Event-Driven
  * *Focus:* Deposits credit `Savings Control` liability and debit `Savings Reference` cash asset; withdrawals debit `Savings Control` and credit cash; interest postings debit `Interest on Savings` expense and credit `Savings Control`.
* **REQ-ACC-SAV-002:** حسابداری تعهدی سپرده‌ها و شناسایی سود بدهکاران/بستانکاران (Accrual-Based Accounting for Savings & Overdrafts)
  * *Pattern:* Event-Driven
  * *Focus:* Periodic accrual debits `Interest on Savings` and credits `Interest Payable` liability; interest posting debits `Interest Payable` and credits `Savings Control`; negative balances tracked via `Overdraft Portfolio Control`.
* **REQ-ACC-SHR-001:** ثبت دفاتر کل حسابداری معاملات و سهامداری (Subledger Accounting for Share Accounts)
  * *Pattern:* Event-Driven
  * *Focus:* Share purchases debit `Shares Reference` asset and credit `Shares Equity` and `Income from Fees`; share redemptions debit `Shares Equity` and credit `Shares Reference`.

#### Section 5: فعالیت‌های ویژه مالی و بستن دوره‌ها (Financial Activities & Periodic Closures)
* **REQ-ACC-FINACT-001:** نگاشت سرفصل‌های دفتر کل به فعالیت‌های ویژه مالی (Financial Activity Account Mappings)
  * *Pattern:* Complex
  * *Focus:* Verification that GL account classifications strictly match activity requirements: Asset activities (`ASSET_TRANSFER`, `CASH_AT_MAINVAULT`, `CASH_AT_TELLER`, `ASSET_FUND_SOURCE`), Liability activities (`LIABILITY_TRANSFER`, `PAYABLE_DIVIDENDS`), and Equity activities (`OPENING_BALANCES_TRANSFER_CONTRA`).
* **REQ-ACC-CLOS-001:** بستن دوره‌های مالی و انسداد ثبت اسناد عطف به ماسبق (Accounting Periodic Closures & Backdated Freeze)
  * *Pattern:* Complex
  * *Focus:* Date boundary invariant $t_{\text{txn}} > t_{\text{closure}}$; hard rejection of any voucher or subledger posting on or prior to the office latest closure date.
* **REQ-ACC-CLOS-002:** مدیریت چرخه حیات و محدودیت‌های حذف بستن حساب‌ها (GL Closure Lifecycle & Deletion Constraints)
  * *Pattern:* State-Driven
  * *Focus:* Rejection of future dates or dates preceding existing closures; deletion permitted strictly for the most recent closure record of a branch.

#### Section 6: قواعد حسابداری و مانده‌های افتتاحیه (Accounting Rules & Opening Balances)
* **REQ-ACC-RULE-001:** حسابداری مبتنی بر قواعد و الگوهای سند دوبل (Rule-Based Accounting & Journal Templates)
  * *Pattern:* Complex
  * *Focus:* Office-scoped accounting rule templates configuring debit/credit GL accounts or account tags with configurable multi-entry allowances.
* **REQ-ACC-OPEN-001:** ثبت مانده‌های افتتاحیه دفاتر کل و حساب رابط سرمایه (Office Opening Balances Definition & Contra Equity Mapping)
  * *Pattern:* Event-Driven
  * *Focus:* Mandatory active `OPENING_BALANCES_TRANSFER_CONTRA` equity mapping, balanced opening debits and credits, and automated opening voucher persistence.

---

### 3.2. `04-charges-taxes-and-rates.md` (18 Cards across 6 Sections)

#### Section 1: تعاریف پایه کارمزد و انواع محاسبات (Charge Definitions & Calculations)
* **REQ-CHG-DEF-001:** تعریف جامع کارمزد و قلمرو انتساب به حساب‌های بانکی (Universal Charge Master Definition & Applicability)
  * *Pattern:* Complex
  * *Focus:* Mandatory unique charge name, positive amount, currency code, and strict applicability scope (`chargeAppliesTo` $\in$ {LOAN, SAVINGS, CLIENT, SHARES}).
* **REQ-CHG-CALC-001:** پیاده‌سازی متدهای پنج‌گانه محاسبه مبلغ کارمزد (Charge Calculation Types Implementation)
  * *Pattern:* Optional Feature
  * *Focus:* 5 calculation algorithms: `FLAT (1)`, `PERCENT_OF_AMOUNT (2)`, `PERCENT_OF_AMOUNT_AND_INTEREST (3)`, `PERCENT_OF_INTEREST (4)`, and `PERCENT_OF_DISBURSEMENT_AMOUNT (5)`.
* **REQ-CHG-TIME-001:** زمان‌بندی و رویدادهای محرک اعمال کارمزدها (Charge Time Frequencies & Event Triggers)
  * *Pattern:* Complex
  * *Focus:* Trigger events: `DISBURSEMENT`, `SPECIFIED_DUE_DATE`, `INSTALMENT_FEE`, `OVERDUE_INSTALLMENT`, `WITHDRAWAL_FEE`, `SAVINGS_ACTIVATION`, `ANNUAL_FEE`, `MONTHLY_FEE`.
* **REQ-CHG-DEF-002:** قواعد و الزامات تفکیک کارمزد عادی از جرایم تاخیر (Fee vs Penalty Invariants)
  * *Pattern:* State-Driven
  * *Focus:* Invariants: charges due at disbursement cannot be penalties (`ChargeDueAtDisbursementCannotBePenaltyException`), and overdue installment charges must be penalties (`ChargeMustBePenaltyException`).

#### Section 2: سقف و کف، برداشت رایگان و چرخه کارمزد تسهیلات (Caps & Loan Charges)
* **REQ-CHG-CAP-001:** اعمال حدود کف و سقف بر کارمزدهای درصدی (Minimum & Maximum Caps Clamping)
  * *Pattern:* Optional Feature
  * *Focus:* Dynamic clamping function $\text{EffectiveFee} = \min(\text{maxCap}, \max(\text{minCap}, \text{Fee}))$ on percentage charges.
* **REQ-CHG-FREE-001:** معافیت برداشت‌های رایگان و بازنشانی دوره‌ای شمارنده (Free Withdrawal Policy & Period Counter Resets)
  * *Pattern:* Event-Driven
  * *Focus:* Exemption of first $N$ withdrawals within a period (`freeWithdrawalFrequency`), charging subsequent withdrawals, and resetting counter on `restartCountFrequency` boundaries.
* **REQ-CHG-LOAN-001:** تخصیص، تسویه و پرداخت کارمزد در پرونده تسهیلات (Loan Charge Allocation & Payment Processing)
  * *Pattern:* Event-Driven
  * *Focus:* Balance decrement of `amountOutstanding`, fee breakdown persistence in `m_loan_charge_paid_by`, and transition to `paid = true`.
* **REQ-CHG-LOAN-002:** بخشش کارمزد تسهیلات و ابطال بخشش قبلی (Loan Charge Waiving & Undo Waive Reversal)
  * *Pattern:* Event-Driven
  * *Focus:* Setting `amountWaived = amountOutstanding` and `amountOutstanding = 0`; undo-waive restores `amountOutstanding` and clears waived flag.

#### Section 3: کارمزدهای سپرده، اعضا و سهام (Savings, Client & Share Charges)
* **REQ-CHG-SAV-001:** کسر کارمزد سپرده، وضعیت تعلیق و غیرفعال‌سازی (Savings Account Charge Deductions & Inactivation)
  * *Pattern:* Event-Driven
  * *Focus:* Available balance deduction, `Fee Deduction` transaction insertion, and support for waiving or inactivating recurring annual/monthly fees on dormant accounts.
* **REQ-CHG-MISC-001:** کارمزدهای سطح مشتری و کارمزد معاملات خرید سهام (Client & Share Account Transaction Charges)
  * *Pattern:* Event-Driven
  * *Focus:* Assessing client charges during customer onboarding, and deducting `ShareAccountCharge` during share purchase approvals with credit to fee income.

#### Section 4: سیستم مالیات و کسر مالیات‌های تکلیفی (Tax Components, Groups & Withholding)
* **REQ-TAX-COMP-001:** تعریف مؤلفه مالیاتی و اتصال به حساب‌های معین دفتر کل (Tax Component Definition & GL Account Mapping)
  * *Pattern:* Complex
  * *Focus:* Unique component name, percentage $[0, 100]$, effective start date, explicit debit and credit GL account linkage, and audit history in `m_tax_component_history`.
* **REQ-TAX-GRP-001:** گروه‌بندی مالیاتی و مدیریت بازه‌های زمانی ناهمپوشان (Tax Group Assembly & Non-Overlapping Slabs)
  * *Pattern:* Complex
  * *Focus:* Multi-component aggregation into a `TaxGroup`, start/end dates, and strict validation preventing overlapping date intervals for identical tax components.
* **REQ-TAX-CALC-001:** محاسبه و تسهیم مالیات بر کارمزدهای خدمات بانکی (Tax Calculation & Split on Banking Fees)
  * *Pattern:* Event-Driven
  * *Focus:* Execution of `TaxUtils.splitTax` across active tax components: $T_k = \text{Amount} \times \frac{r_k}{100}$ and $\text{NetIncome} = \text{Amount} - \sum T_k$.
* **REQ-TAX-WHT-001:** کسر اتوماتیک مالیات تکلیفی از سود سپرده‌های سرمایه‌گذاری (Withholding Tax on Savings Interest)
  * *Pattern:* Event-Driven
  * *Focus:* Automated deduction of withholding tax during savings interest posting (`withHoldTax == true`), crediting tax liability account, and creating `WITHHOLD_TAX` savings transaction.

#### Section 5: نرخ‌های شناور و نرخ مبنای وام‌دهی (Floating Interest Rates & Base Lending Rate)
* **REQ-FLT-DEF-001:** تعریف نرخ شناور و ناوردای انحصار نرخ مرجع وام‌دهی (Floating Rate Definition & Base Lending Rate Invariant)
  * *Pattern:* State-Driven
  * *Focus:* Unique name up to 200 characters, and tenant singleton invariant: at most one active `isBaseLendingRate == true` across the entire tenant (`baselendingrate.duplicate`).
* **REQ-FLT-PER-001:** دوره‌های زمانی اثرگذاری نرخ شناور و حاشیه سود تفاضلی (Floating Rate Periods & Margin Differentials)
  * *Pattern:* Complex
  * *Focus:* Effective period sequence (`fromDate`), unique dates per rate, and computation of effective lending rate via differential margin over the active Base Lending Rate.

#### Section 6: جداول نرخ سود سپرده‌ها و پاداش‌های تشویقی (Interest Rate Charts & Incentives)
* **REQ-CHRT-SLAB-001:** جدول ماتریسی پلکان‌های نرخ سود بر اساس مدت و مبلغ (Interest Rate Chart Matrix Slabs)
  * *Pattern:* Complex
  * *Focus:* Multi-dimensional slab matrix defined by period range (`fromPeriod` to `toPeriod`) and amount range (`amountRangeFrom` to `amountRangeTo`), with non-overlapping period boundaries.
* **REQ-CHRT-INC-001:** اعمال پاداش‌ها و مشوق‌های نرخ سود بر اساس صفات مشتری (Demographic & Attribute-Based Interest Incentives)
  * *Pattern:* Event-Driven
  * *Focus:* Dynamic interest rate margin adjustments ($\Delta r$) matching client demographic attributes (`GENDER`, `AGE`, `CLIENT_TYPE`, `CLIENT_CLASSIFICATION`) using comparison condition operators.

---

## 4. Automated Quality Gate Audit Results

An automated pre-audit verification script (`scripts/test_task9_audit.py`) was executed to validate the deliverables against all quality criteria:

```text
=======================================================
AUDITING: docs/requirements/03-accounting-and-financial-ledger.md
=======================================================
Gate 1 - Modal check outside backticks/quotes: 0 violations
Gate 2 - Requirement cards found: 18
Gate 3 - EARS grammar & shall check: 0 errors
Total shall count: 89
Total If-Then clauses: 52
Gate 4 - Java file references: 34
Missing Java files: 0
AUDIT RESULT for docs/requirements/03-accounting-and-financial-ledger.md: PASS (100%)

=======================================================
AUDITING: docs/requirements/04-charges-taxes-and-rates.md
=======================================================
Gate 1 - Modal check outside backticks/quotes: 0 violations
Gate 2 - Requirement cards found: 18
Gate 3 - EARS grammar & shall check: 0 errors
Total shall count: 85
Total If-Then clauses: 46
Gate 4 - Java file references: 41
Missing Java files: 0
AUDIT RESULT for docs/requirements/04-charges-taxes-and-rates.md: PASS (100%)
```

### Detailed Quality Gate Metrics Summary:

| Metric | Target | `03-accounting-and-financial-ledger.md` | `04-charges-taxes-and-rates.md` | Compliance |
| :--- | :--- | :--- | :--- | :--- |
| **Total Cards** | 16 - 20 cards | 18 cards | 18 cards | **100% PASS** |
| **EARS Modal Verb** | strictly `shall` | 89 occurrences | 85 occurrences | **100% PASS** |
| **Forbidden Modals** | 0 violations (`should`, `will`, `can`, `must`) | 0 violations | 0 violations | **100% PASS** |
| **Unwanted Behaviors** | `If...then the Fineract Engine shall...` | 52 clauses | 46 clauses | **100% PASS** |
| **Java File Citations** | Real files in Fineract 1.15.0 | 34 unique classes | 41 unique classes | **100% PASS** |
| **Missing Java Files** | 0 missing | 0 missing | 0 missing | **100% PASS** |
| **Bilingual Structure** | Persian Title + English Statement + Persian Explanation + Traceability | Fully Implemented | Fully Implemented | **100% PASS** |

---

## 5. Primary Grounded Source Code References

### 5.1. Core Accounting & Ledger (`03-accounting-and-financial-ledger.md`)
* `fineract-core/.../glaccount/domain/GLAccount.java`
* `fineract-accounting/.../glaccount/service/GLAccountWritePlatformServiceJpaRepositoryImpl.java`
* `fineract-accounting/.../glaccount/command/GLAccountCommand.java`
* `fineract-accounting/.../journalentry/domain/JournalEntry.java`
* `fineract-provider/.../journalentry/service/JournalEntryWritePlatformServiceJpaRepositoryImpl.java`
* `fineract-accounting/.../journalentry/serialization/JournalEntryCommandFromApiJsonDeserializer.java`
* `fineract-provider/.../journalentry/service/JournalEntryRunningBalanceUpdateServiceImpl.java`
* `fineract-provider/.../journalentry/service/CashBasedAccountingProcessorForLoan.java`
* `fineract-provider/.../journalentry/service/AccrualBasedAccountingProcessorForLoan.java`
* `fineract-provider/.../journalentry/service/CashBasedAccountingProcessorForSavings.java`
* `fineract-provider/.../journalentry/service/AccrualBasedAccountingProcessorForSavings.java`
* `fineract-provider/.../journalentry/service/CashBasedAccountingProcessorForShares.java`
* `fineract-accounting/.../financialactivityaccount/service/FinancialActivityAccountWritePlatformServiceImpl.java`
* `fineract-accounting/.../closure/service/GLClosureWritePlatformServiceJpaRepositoryImpl.java`
* `fineract-accounting/.../closure/domain/GLClosure.java`
* `fineract-accounting/.../rule/service/AccountingRuleWritePlatformServiceJpaRepositoryImpl.java`
* `fineract-accounting/.../rule/serialization/AccountingRuleCommandFromApiJsonDeserializer.java`

### 5.2. Charges, Taxes & Rates (`04-charges-taxes-and-rates.md`)
* `fineract-charge/.../charge/domain/Charge.java`
* `fineract-charge/.../charge/domain/ChargeCalculationType.java`
* `fineract-charge/.../charge/domain/ChargeAppliesTo.java`
* `fineract-core/.../charge/domain/ChargeTimeType.java`
* `fineract-charge/.../charge/serialization/ChargeDefinitionCommandFromApiJsonDeserializer.java`
* `fineract-charge/.../charge/exception/ChargeDueAtDisbursementCannotBePenaltyException.java`
* `fineract-charge/.../charge/exception/ChargeMustBePenaltyException.java`
* `fineract-loan/.../loanaccount/domain/LoanCharge.java`
* `fineract-loan/.../loanaccount/handler/PayLoanChargeCommandHandler.java`
* `fineract-loan/.../loanaccount/handler/WaiveLoanChargeCommandHandler.java`
* `fineract-savings/.../savings/domain/SavingsAccountCharge.java`
* `fineract-provider/.../shareaccounts/domain/ShareAccountCharge.java`
* `fineract-tax/.../tax/domain/TaxComponent.java`
* `fineract-tax/.../tax/domain/TaxGroup.java`
* `fineract-tax/.../tax/domain/TaxGroupMappings.java`
* `fineract-tax/.../tax/serialization/TaxValidator.java`
* `fineract-tax/.../tax/service/ChargeTaxApplicationServiceImpl.java`
* `fineract-tax/.../tax/service/TaxUtils.java`
* `fineract-rates/.../floatingrates/domain/FloatingRate.java`
* `fineract-rates/.../floatingrates/domain/FloatingRatePeriod.java`
* `fineract-rates/.../floatingrates/serialization/FloatingRateDataValidator.java`
* `fineract-savings/.../interestratechart/domain/InterestRateChart.java`
* `fineract-savings/.../interestratechart/domain/InterestRateChartSlab.java`
* `fineract-savings/.../interestratechart/domain/InterestIncentives.java`
* `fineract-savings/.../interestratechart/incentive/ClientAttributeIncentiveCalculation.java`

---

## 6. Conclusion & Completion Status

Task 9 is fully accomplished. Both required bilingual EARS requirement specifications (`03-accounting-and-financial-ledger.md` and `04-charges-taxes-and-rates.md`) have been authored, validated against all quality gates, committed to Git (`0f704fc`), and thoroughly documented in this report.


---

## 3. Verification & Quality Gates Checklist for Reviewer

### Gate 1: EARS Syntax, Grammar & Modal Iron Rule
- [ ] Verify all 36 requirement cards across both files contain valid EARS statements using `shall` strictly.
- [ ] Verify 0 occurrences of forbidden modals (`should`, `will`, `can`, `must`) in EARS statements (except inside literal error code strings/class identifiers).
- [ ] Verify all unwanted behavior conditions use the standard `If ... then the Fineract Engine shall ... error code ...` format.
- [ ] Verify presence of comprehensive Persian business scenarios and technical explanations.

### Gate 2: Code Traceability & Ground Truth Verification
- [ ] Verify referenced Java classes exist in Apache Fineract 1.15.0 across `fineract-accounting`, `fineract-charge`, `fineract-tax`, `fineract-rates`, and `fineract-provider`.
- [ ] Verify database tables and columns match the Flyway/Liquibase schema (`acc_gl_account`, `acc_gl_journal_entry`, `acc_gl_closure`, `acc_gl_financial_activity_account`, `acc_accounting_rule`, `m_charge`, `m_tax_component`, `m_tax_group`, `m_interest_rate_chart`, `m_floating_rates`, etc.).
- [ ] Verify error codes match Fineract runtime error strings and exception classes.

### Gate 3: Banking & Financial Domain Invariants
- [ ] Double-Entry Balance Conservation Law: $\sum \text{Debits} = \sum \text{Credits}$ across all journal entries.
- [ ] Cash vs Accrual accounting models: Cash, Periodic Accrual, Upfront Accrual.
- [ ] Accounting Closures (GLClosure): $t_{\text{txn}} > t_{\text{closure}}$ invariant preventing backdated entries before closure.
- [ ] Charge calculation modes: Flat, % of Amount, % of Loan + Interest, % of Interest, % of Disbursement with min/max caps clamping.
- [ ] Tax component & group split calculation on banking fees and interest withholding.
- [ ] Floating rate singleton Base Lending Rate invariant and interest rate slab evaluation.
