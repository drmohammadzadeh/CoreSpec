# Task 9 Brief: Reverse-Engineering Tier 3 (Core Accounting, Financial GL, Charges, Taxes & Rates)

**Task ID:** Task 9  
**Parent Plan:** `docs/superpowers/plans/2026-10-28-fineract-ears-reverse-engineering-plan.md`  
**Deliverables Required:**
1. `docs/requirements/03-accounting-and-financial-ledger.md`
2. `docs/requirements/04-charges-taxes-and-rates.md`
3. `docs/sdd/task-9-report.md`

---

## 1. Domain Scope & Mission

Reverse-engineer Apache Fineract 1.15.0's financial engine covering two interconnected yet distinct domains:
1. **Financial Ledger & Accounting (`03-accounting-and-financial-ledger.md`):**
   - Chart of Accounts (COA) hierarchy (Asset, Liability, Equity, Income, Expense) with manual entry disabled flags and usage restrictions.
   - Double-entry balance conservation ($\sum \text{Debits} = \sum \text{Credits}$) for manual journal vouchers and automated portfolio postings.
   - Cash vs. Accrual accounting modes (Cash-based, Periodic Accrual, Upfront Accrual).
   - Portfolio subledger bridge (`AccountingProcessorForLoan`, `AccountingProcessorForSavings`, `AccountingProcessorForShares`).
   - Financial Activity Account Mappings (`acc_gl_financial_activity_account`) for suspense, asset transfer, opening balance equity, etc.
   - Accounting Closures & Periodic Freezes (`GLClosure`) preventing backdated transactions before the closure date.
   - Rule-based accounting vouchers (`AccountingRule`).

2. **Charges, Taxes & Interest Rates (`04-charges-taxes-and-rates.md`):**
   - Charge definitions across products and accounts (Loan, Savings, Client, Share).
   - Charge calculation types (Flat, % of Amount, % of Amount + Interest, % of Interest, % of Disbursement).
   - Charge time frequencies (Disbursement, Specified Due Date, Installment Fee, Overdue Installment Penalty, Withdrawal Fee, Annual Fee, Monthly Fee).
   - Tax components and tax groups (Withholding tax on savings interest, tax on loan charges).
   - Floating interest rate charts, rate slabs, and incentive calculation rules.

---

## 2. Document Architecture & Standards

Both requirement files must adhere to the high standard established in `01-loan-portfolio.md` and `02-savings-and-deposits.md`:

### Section 1: Executive Summary, Architecture & Domain Invariants
- Mathematical and accounting formulas:
  - $\sum_{i=1}^n \text{Debit}_i = \sum_{j=1}^m \text{Credit}_j$
  - Effective charge computation equations across calculation types.
  - Tax withholding formula: $T = I_{\text{gross}} \times \frac{r_{\text{tax}}}{100}$.
  - Accounting closure boundary condition: $t_{\text{txn}} > t_{\text{closure}}$.
- Subproject architecture and component diagram.

### Section 2: Catalog Summary Table
- Markdown table mapping Requirement ID, Title (Persian), EARS Pattern, and Primary Source Class.

### Section 3+: Categorized Bilingual EARS Requirement Cards
Each card MUST contain:
1. **Title (Persian):** `#### REQ-[MODULE]-[SUB]-[NUM]: [عنوان دقیق فارسی]`
2. **EARS Pattern:** (Ubiquitous, Event-Driven, State-Driven, Unwanted Behavior, Optional Feature, Complex)
3. **EARS Statement (English):** Strict adherence to the **`shall`** modal verb iron rule. Forbidden modals (`should`, `will`, `can`, `must`) are strictly prohibited in normative prose.
4. **شرح نیازمندی و سناریوی بیزنس (فارسی):** Thorough Persian explanation of the banking mechanism.
5. **رفتارهای ناخواسته و شروط خطا (EARS If-Then):** Explicit `If...then the Fineract Engine shall...` clauses with real Fineract validation error codes.
6. **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
   - Exact Java source file path and class name.
   - Method name(s).
   - Runtime error codes and Spring security annotations.
   - Database tables and columns.

---

## 3. Mandatory Quality Gates
- **Gate 1 (EARS Grammar):** 100% `shall`, 0 forbidden modals, complete bilingual structure, standard If-Then clauses.
- **Gate 2 (Traceability):** Grounded in real Java files in `fineract-accounting`, `fineract-charge`, `fineract-tax`, `fineract-rates`, and `fineract-provider`.
- **Gate 3 (Financial Invariants):** Balanced double entries, accurate accrual vs cash behaviors, tax deductions, and rate slab evaluations.
