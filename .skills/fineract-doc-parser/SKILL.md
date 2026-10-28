---
name: fineract-doc-parser
description: Extracts declared business rules, financial workflows, and user-facing functional requirements from AsciiDoc, Markdown, and crawled HTML documentation across Apache Fineract into standardized EARS requirements. Activate when inspecting documentation files in fineract-doc, READMEs, or docs/crawled/.
---

# Fineract Documentation Parser to EARS Requirements

## Overview
This skill guides agents in parsing textual documentation—including AsciiDoc files (`*.adoc`), Markdown specifications (`*.md`), and crawled HTML documents (`docs/crawled/`)—to extract declared business rules, banking calculation specifications, user workflows, and regulatory constraints into standardized EARS requirements.

Crucially, this skill enforces **Doc-to-Code Reconciliation**: every declared business rule found in documentation must be cross-verified against the actual Java implementation to prevent documentation drift or hallucination.

## Target File Scope & Locations
This skill applies to all documentation assets within the workspace:
* **In-Repository AsciiDoc Files:**
  * `apache-fineract-src-1.15.0/fineract-doc/src/docs/asciidoc/**/*.adoc`
  * Subproject user manuals and developer guides
* **Repository Markdown Files:**
  * `apache-fineract-src-1.15.0/README.md`
  * `apache-fineract-src-1.15.0/**/README.md`
  * `apache-fineract-src-1.15.0/CHANGELOG.md`
* **Crawled Online Documentation:**
  * `docs/crawled/sitemap.json`
  * `docs/crawled/SUMMARY.md`
  * `docs/crawled/pages/**/*.md` (Crawled technical and operational documentation from `https://fineract.apache.org/docs/stable`)

---

## Architectural Semantics of Documentation

1. **Declared Functional Capabilities:**
   * High-level feature definitions, supported financial conventions (e.g. Day count conventions: 30/360, Actual/365, Actual/Actual).
2. **Business Workflows & State Progression:**
   * Declared lifecycle workflows (e.g., Loan lifecycle: `Submitted` $\to$ `Approved` $\to$ `Disbursed` $\to$ `Active` $\to$ `Closed`).
3. **Financial Formulas & Calculations:**
   * Amortization algorithms (Equal Installments, Equal Principal, Declining Balance), compound interest frequencies, penalty calculations.
4. **Declared Constraints & Validation Boundaries:**
   * Documented limitations (e.g., maximum term, minimum disbursement amount, grace period limits).

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **Doc Construct:** Universally declared business rules or regulatory capabilities.
* **Extraction Pattern:**
  * Documented statement: "Fineract supports both Cash-based and Accrual-based accounting principles across all loan products."
  * Map to: `The Fineract Accounting Engine shall support both Cash-based and Accrual-based accounting methodologies for all financial transaction postings.`

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **Doc Construct:** Workflow step prerequisites and lifecycle constraints.
* **Extraction Pattern:**
  * Documented statement: "A loan account cannot be closed while there is any outstanding principal balance remaining."
  * Map to: `While a loan account retains a non-zero outstanding balance, the Fineract Loan Engine shall prohibit loan account closure.`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **Doc Construct:** Documented operational events, end-of-day operations, batch scheduling.
* **Extraction Pattern:**
  * Documented statement: "At the end of each business day, Close-of-Business batch job calculates and posts daily interest accruals."
  * Map to: `When the Close-of-Business (COB) daily job executes, the Fineract Batch Subsystem shall calculate and post accrued interest for all eligible active accounts.`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **Doc Construct:** Documented optional capabilities (e.g. Moratorium, Floating interest rates, Tranche disbursement).
* **Extraction Pattern:**
  * Documented statement: "Where a repayment moratorium is defined on principal, installments within the moratorium period only require interest repayment."
  * Map to: `Where a principal repayment moratorium is configured on a loan account, the Fineract Loan Engine shall exclude principal amortization from installments falling within the moratorium window.`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **Doc Construct:** Documented warning callouts, validation rules, operational prohibitions.
* **Extraction Pattern:**
  * Documented statement: "NOTE: Disbursing a loan on a date before the approval date is strictly forbidden."
  * Map to: `If a user attempts to record a loan disbursement with a transaction date prior to the approval date, then the Fineract Loan Engine shall reject the transaction with error code "error.msg.loan.disbursement.date.cannot.be.before.approved.date".`

### 6. Complex Requirements
* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
* **Doc Construct:** Documented conditional features during specific operational states.
* **Extraction Pattern:**
  * Map to: `Where floating interest rates are enabled, while the loan account is in "ACTIVE" state, when a base interest rate change occurs, the Fineract Loan Engine shall dynamically recalculate future installment schedules.`

---

## Heuristics for Doc-to-Code Reconciliation

To prevent hallucinated or outdated requirements, follow this mandatory 3-step check:
1. **Extract Candidate:** Identify the declared rule and parameters (e.g. grace period, interest method).
2. **Locate Implementation:** Search Java source code in `apache-fineract-src-1.15.0/` (using methods, enums, or validator error codes) to verify the rule exists.
3. **Reconcile Parameters:** If documentation claims behavior $X$ but the code implements $Y$, prioritize the code as the ground truth, document the discrepancy in the Persian rationale, and link the exact source code location in the Traceability Matrix.

---

## Bilingual Output Requirement Card Template

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل سناریوی بانکی بر اساس مستندات رسمی، منطق مالی و انطباق با رفتار سیستم به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **منبع مستندات:** `fineract-doc/.../*.adoc` یا `docs/crawled/pages/...`
  * **مسیر فایل و کلاس سورس متناظر:** `apache-fineract-src-1.15.0/.../ClassName.java`
  * **متد اجرایی:** `#methodName()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg....`
```

---

## Concrete Example

```markdown
### REQ-DOC-LOAN-MORATORIUM-001: اعمال دوره تنفس در بازپرداخت اصل وام (Grace Period / Moratorium)
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a principal repayment moratorium is configured for a loan product, the Fineract Loan Engine shall exclude principal amounts from repayment installments during the designated moratorium period while continuing to accrue and demand interest payments.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  بر اساس مستندات رسمی سامانه، در صورتی که دوره تنفس اصل وام (Principal Moratorium) برای مشتری فعال شده باشد، در طول دوره تنفس اقساط فقط شامل بهره تسهیلات بوده و بازپرداخت اصل وام به تعویق می‌افتد. با پایان دوره تنفس، اصل مبلغ باقی‌مانده بر روی اقساط آتی سرشکن می‌گردد. صحت این منطق با متدهای محاسبه جدول بازپرداخت در کد جاوا تطبیق داده شده است.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the configured principal moratorium period equals or exceeds the total number of repayment installments, then the Fineract Loan Engine shall reject the loan creation with error code "error.msg.loan.moratorium.period.cannot.exceed.or.equal.number.of.installments".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **منبع مستندات:** `docs/crawled/pages/user-manual/loan-products.md` (بخش Grace on Principal Payment)
  * **مسیر فایل و کلاس سورس متناظر:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/LoanRepaymentScheduleInstallment.java`
  * **متد اجرایی:** `#isAdditional()`, `#updatePrincipalAndInterestAmount()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.moratorium.period.cannot.exceed.or.equal.number.of.installments`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan`, جدول `m_loan_repayment_schedule`
```
