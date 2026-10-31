# Task 6 Brief: Consolidate Canonical Banking Domain Glossary

## Role in Project
Synthesize all domain terminology, business concepts, accounting rules, and entity models from the three architectural deliverables (`01`, `02`, `03`) and the crawled documentation into an authoritative, canonical banking domain glossary: `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`. This document serves as the binding semantic compass for all downstream module reverse-engineering workers (Tasks 7 through 11).

## Files to Touch
- Create: `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`
- Report: `docs/sdd/task-6-report.md`

## Input Resources
- Architecture Documents:
  - `docs/architecture/01-system-modules-and-stack.md`
  - `docs/architecture/02-api-cqrs-and-security.md`
  - `docs/architecture/03-domain-data-events-and-cob.md`
- Crawled Docs: `docs/crawled/pages/stable/sections/07-features.md`, `08-working-capital-loan.md`
- Skills: `.skills/fineract-java-parser/SKILL.md` and `.skills/fineract-doc-parser/SKILL.md`

## Deliverables & Detailed Requirements
1. **Canonical Banking Domain Glossary Structure:**
   - Organize terms into distinct domain categories:
     1. **Lending & Credit Portfolio:** Principal, Interest, Repayment Schedule, Amortization (Equal Installments, Equal Principal), Interest Method (Flat, Declining Balance), Interest Calculation Period (Daily, Same as Repayment), Grace Period (on principal, on interest), Moratorium, Tranche / Multi-disbursal, Restructure / Reschedule, Foreclosure, Delinquency, Non-Performing Asset (NPA), Overdue, Days Past Due (DPD), Arrears, Aging Buckets, Write-Off, Recovery.
     2. **Savings & Deposit Accounts:** Available Balance, Ledger Balance, Daily Balance, Minimum Balance, Hold Amount / Lien, Fixed Deposit, Recurring Deposit, Interest Posting, Compounding Period, Premature Closure, Dormancy, Escheatment.
     3. **General Ledger & Financial Accounting:** Double-Entry Bookkeeping, Chart of Accounts, Asset, Liability, Equity, Income, Expense, Cash-based Accounting, Accrual-based Accounting (Periodic, Upfront), Journal Entry, Debit, Credit, Financial Activity Mapping, Suspense Account, Revaluation.
     4. **Charges, Fees & Taxes:** Disbursal Fee, Specified Due Date Charge, Installment Fee, Overdue Penalty, Flat Fee, Pro-rata Fee, Withholding Tax, Tax Group, Tax Component.
     5. **Close of Business (COB) & Core Operations:** Business Date, Day-End Accrual, COB Catch-Up, Inline COB, Account Lock, Holiday Calendar, Reschedule on Holiday.
     6. **Platform, Identity & Governance:** Tenant, Maker, Checker, Segregation of Duties (4-Eyes), Idempotency Key, Command Wrapper, Audit Trail, Event Sourcing, Transactional Outbox.
2. **Standard Terminology Record Format:**
   For each banking term, provide:
   - **English Term (اصطلاح انگلیسی)**
   - **Canonical Persian Equivalent (معادل استاندارد فارسی)**
   - **Domain Definition & Banking Rationale (تعریف جامع و منطق بانکی)**
   - **Fineract Technical Grounding (کلاس/انتیتی و جدول متناظر در فاینراکت)**
   - **Standard EARS Usage Rule (نحوه استفاده استاندارد در گزاره‌های EARS)**
3. **Cross-Module Disambiguation Rules:**
   - Explicitly define semantic conventions to prevent contradictions (e.g. distinguishing between "Loan Disbursal" vs "Payment", "Accrued Interest" vs "Capitalized Interest", "Fee" vs "Penalty").

## Report Contract
- Author `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`.
- Commit with `git add docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md` and message `docs(architecture): add global banking domain glossary`.
- Write your full report to `docs/sdd/task-6-report.md`.
- Return status (DONE), commit hash, and summary.
