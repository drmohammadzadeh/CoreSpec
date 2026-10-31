# Task 8 Brief: Reverse-Engineer Tier 2 - Savings & Deposit Accounts

## Role in Project
Execute the comprehensive reverse-engineering of Apache Fineract 1.15.0 Tier 2: Savings Accounts, Fixed Deposits (FD), Recurring Deposits (RD), Interest Compounding/Posting, Dormancy, and Amount Holds into the canonical Easy Approach to Requirements Syntax (EARS) format in `docs/requirements/02-savings-and-deposits.md`.

## Files to Touch
- Create: `docs/requirements/02-savings-and-deposits.md`
- Report: `docs/sdd/task-8-report.md`

## Input Resources
- Source Modules:
  - `apache-fineract-src-1.15.0/fineract-savings/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/`
  - `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/` (savings tables: `m_savings_product`, `m_savings_account`, `m_savings_account_transaction`, `m_savings_account_charge`, `m_deposit_account_term_and_pre_closure`, `m_deposit_account_recurring_installment`, `m_savings_account_on_hold_funds`, etc.)
- Crawled Docs:
  - `docs/crawled/pages/stable/sections/07-features.md`
  - `docs/crawled/pages/stable/sections/13-portfolio.md`
- Architecture & Glossary Deliverables:
  - `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`
  - `docs/architecture/02-api-cqrs-and-security.md`
  - `docs/architecture/03-domain-data-events-and-cob.md`
- Skills:
  - `.skills/fineract-java-parser/SKILL.md`
  - `.skills/fineract-db-schema-parser/SKILL.md`

## Scope of Savings & Deposits Reverse-Engineering
Author a comprehensive, authoritative requirements catalog containing **at least 20 to 24 detailed bilingual EARS requirement cards** covering:
1. **Savings Product Configuration & Policy Invariants:**
   - Multi-currency, nominal annual interest rate, interest calculation methods (Daily Balance vs Average Daily Balance).
   - Interest compounding period types (Daily, Monthly, Quarterly, Semi-Annual, Annual) and posting period types (Monthly, Quarterly, Biannual, Annual).
   - Minimum required opening balance, minimum balance for interest calculation, lock-in period (Days, Weeks, Months, Years), and overdraft configuration.
2. **Fixed Deposit (FD) & Recurring Deposit (RD) Products & Accounts:**
   - Term deposit parameters (min/max/default tenure, period frequency types).
   - Premature closure interest reduction and penalties (`pre_closure_penal_interest`, `pre_closure_penal_interest_on_enum`).
   - Recurring deposit mandatory periodic installments, schedules, and overdue penalties (`m_deposit_account_recurring_installment`).
3. **Savings Account Lifecycle & State Transitions:**
   - Account submission (`SUBMITTED_AND_PENDING_APPROVAL`, status 100).
   - Approval (`APPROVED`, 200), Rejection (`REJECTED`, 500), Withdrawal (`WITHDRAWN_BY_CLIENT`, 400).
   - Activation (`ACTIVE`, 300) with initial deposit validation.
   - Voluntary and mature Closure (`CLOSED`, 600).
   - Sub-statuses: `INACTIVE` (100), `DORMANT` (200), `ESCHEAT` (300), `BLOCK` (400), `BLOCK_CREDIT` (500), `BLOCK_DEBIT` (600).
4. **Savings Transactions & Financial Operations:**
   - Cash deposits, transfers, and minimum/maximum transaction amount limits.
   - Cash withdrawals, available balance verification ($\text{Available} = \text{Balance} - \text{Hold} - \text{MinBalance}$), and overdraft rules.
   - Automated interest calculation & posting engine (`SavingsAccount.postInterest`).
   - Transaction reversals (Undo Deposit, Undo Withdrawal) and chargebacks.
5. **Holds, Liens & Collateral Management:**
   - Placing funds on hold for loan collateral or legal attachment (`m_savings_account_on_hold_funds`).
   - Hold release, partial release, and impact on available balance.
6. **Dormancy, Escheatment & Account Maintenance:**
   - Inactivity detection, automated transition to Dormant, and asset forfeiture / Escheatment.
   - Account unblocking, reactivation KYC procedures, and dormancy fee deductions.

## Deliverable Standard & Format
Every requirement card must strictly follow the standard format:
```markdown
### REQ-SAVINGS-[CATEGORY]-[NUM]: [عنوان دقیق و توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > [While <preconditions>,] [When <trigger>,] [Where <feature>,] the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل سناریوی بانکی، منطق بیزنس و اهداف مالی به زبان فارسی روان و تحلیلی]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the Fineract Savings Engine shall reject the request and return error code "<CODE_1>".`
  * `If <error condition 2>, then the Fineract Savings Engine shall ...`
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
- Author `docs/requirements/02-savings-and-deposits.md`.
- Commit with `git add docs/requirements/02-savings-and-deposits.md` and message `feat(requirements): add comprehensive EARS requirements for savings and deposits`.
- Write your full report to `docs/sdd/task-8-report.md`.
- Return status (DONE), commit hash, and summary of requirements generated.
