import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

with open('docs/sdd/task-8-brief.md', 'r', encoding='utf-8') as f:
    brief = f.read()

with open('docs/sdd/task-8-report.md', 'r', encoding='utf-8') as f:
    report = f.read()

package_content = f"""# Task 8 Review Package: Tier 2 Savings & Deposits Reverse Engineering

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 8: Tier 2 Savings Accounts, Fixed Deposits, Recurring Deposits, Interest Compounding, Holds, and Dormancy reverse engineering.

---

## 2. Implementer Report
{report}

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
"""

with open('docs/sdd/task-8-review-package.md', 'w', encoding='utf-8') as f:
    f.write(package_content)

print('Successfully written docs/sdd/task-8-review-package.md')
