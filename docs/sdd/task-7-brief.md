# Task 7 Brief: Reverse-Engineer Tier 1 - Core Lending & Progressive Loans Portfolio

## Role in Project
Execute the comprehensive reverse-engineering of Apache Fineract 1.15.0 Tier 1: Core Lending, Progressive Loans, and Loan Lifecycle into the canonical Easy Approach to Requirements Syntax (EARS) format in `docs/requirements/01-loan-portfolio.md`.

## Files to Touch
- Create: `docs/requirements/01-loan-portfolio.md`
- Report: `docs/sdd/task-7-report.md`

## Input Resources
- Source Modules:
  - `apache-fineract-src-1.15.0/fineract-loan/`
  - `apache-fineract-src-1.15.0/fineract-progressive-loan/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanproduct/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/delinquency/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/` (loan tables: `m_loan`, `m_product_loan`, `m_loan_transaction`, `m_loan_repayment_schedule`, `m_loan_charge`, `m_delinquency_bucket`, etc.)
- Crawled Docs:
  - `docs/crawled/pages/stable/sections/07-features.md`
  - `docs/crawled/pages/stable/sections/08-working-capital-loan-projected-amortization-schedule.md`
  - `docs/crawled/pages/stable/sections/13-portfolio.md`
- Architecture & Glossary Deliverables:
  - `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`
  - `docs/architecture/02-api-cqrs-and-security.md`
  - `docs/architecture/03-domain-data-events-and-cob.md`
- Skills:
  - `.skills/fineract-java-parser/SKILL.md`
  - `.skills/fineract-db-schema-parser/SKILL.md`

## Scope of Loan Portfolio Reverse-Engineering
Author a comprehensive, authoritative requirements catalog containing **at least 20 to 25 detailed bilingual EARS requirement cards** covering:
1. **Loan Product Configuration & Policy Invariants:**
   - Multi-currency, principal min/default/max bounds.
   - Amortization methods (`EQUAL_INSTALLMENTS`, `EQUAL_PRINCIPAL`).
   - Interest calculation methods (`FLAT`, `DECLINING_BALANCE`).
   - Repayment strategy / Payment allocation rules (`m_loan_product_payment_allocation_rule`, Advanced payment allocation).
2. **Schedule Generation & Amortization Algorithms:**
   - Classic schedule generator (`LoanScheduleCalculationPlatformServiceImpl`).
   - Progressive loan engine with daily compounding / interest recalculation (`ProgressiveLoanScheduleGenerator`, `fineract-progressive-loan`).
   - Grace periods on principal and interest (`graceOnPrincipalPayment`, `graceOnInterestPayment`).
   - Down-payment enablement and tranche / multi-disbursal schedule updates.
3. **Loan Account Lifecycle & State Transitions:**
   - Submission & Origination (`m_loan` state `SUBMITTED_AND_PENDING_APPROVAL`, status 100).
   - Approval & Rejection (`APPROVED`, status 200).
   - Disbursal & Multi-Tranche Payout (`ACTIVE`, status 300).
   - Full Repayment & Closure (`OBLIGATIONS_MET`, status 600; `OVERPAID`, status 700).
4. **Loan Transactions & Financial Operations:**
   - Repayments, Prepayments, and Foreclosure.
   - Payment allocation hierarchy (Penalties -> Fees -> Interest -> Principal).
   - Transaction reversals (`UNDODISBURSEMENT`, undo repayment, chargeback).
   - Interest waivers and write-offs (`LoanTransactionType.WAIVE_INTEREST`, `LoanTransactionType.WRITEOFF`).
5. **Delinquency, NPA & Overdue Management:**
   - Overdue calculation, Days Past Due (DPD), and Arrears.
   - Delinquency ranges and aging buckets (`m_delinquency_bucket`, `m_delinquency_range`).
   - Non-Performing Asset (NPA) classification and pause delinquency periods.
6. **Loan Restructuring & Rescheduling:**
   - Reschedule requests (`m_loan_reschedule_request`), term extensions, interest rate adjustments, moratorium.

## Deliverable Standard & Format
Every requirement card must strictly follow the standard format:
```markdown
### REQ-LOAN-[CATEGORY]-[NUM]: [عنوان دقیق و توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > [While <preconditions>,] [When <trigger>,] [Where <feature>,] the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل سناریوی بانکی، منطق بیزنس و اهداف مالی به زبان فارسی روان و تحلیلی]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the Fineract Loan Engine shall reject the request and return error code "<CODE_1>".`
  * `If <error condition 2>, then the Fineract Loan Engine shall ...`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/.../ClassName.java`
  * **متد اجرایی:** `#methodName()`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize(...)`, `error.msg....`
  * **پایگاه داده و انتیتی‌ها:** جداول `m_...`, انتیتی `@Entity ...`
```

## Quality Constraints
- **EARS Grammar Iron Rule:** The modal verb in the English EARS clause must strictly be **`shall`** (never `should`, `will`, `can`, or `must`).
- **Verifiability:** All conditions and responses must be precise, testable, and mathematically grounded.
- **Traceability:** Genuine Apache Fineract 1.15.0 classes, methods, tables, and error codes must be cited.
- **Glossary Alignment:** All terminology must match `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`.

## Report Contract
- Author `docs/requirements/01-loan-portfolio.md`.
- Commit with `git add docs/requirements/01-loan-portfolio.md` and message `feat(requirements): add comprehensive EARS requirements for loan portfolio`.
- Write your full report to `docs/sdd/task-7-report.md`.
- Return status (DONE), commit hash, and summary of requirements generated.
