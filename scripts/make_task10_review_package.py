import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

with open('docs/sdd/task-10-brief.md', 'r', encoding='utf-8') as f:
    brief = f.read()

with open('docs/sdd/task-10-report.md', 'r', encoding='utf-8') as f:
    report = f.read()

package_content = f"""# Task 10 Review Package: Tier 4 Close of Business (COB) & Batch Operations

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 10: Close of Business (COB) Orchestration, Remote Partitioning, Business Steps Pipeline, Account Locking, Concurrency Control, Delinquency Aging, Accrual Business Steps, Business Date Progression, Holiday Calendars, and Spring Batch Infrastructure reverse engineering.

---

## 2. Implementer Report
{report}

---

## 3. Verification & Quality Gates Checklist for Reviewer

### Gate 1: EARS Syntax, Grammar & Modal Iron Rule
- [ ] Verify all 24 requirement cards contain valid EARS statements using `shall` strictly.
- [ ] Verify 0 occurrences of forbidden modals (`should`, `will`, `can`, `must`) in EARS statements (except inside literal error code strings/class identifiers).
- [ ] Verify all unwanted behavior conditions use the standard `If ... then the Fineract Engine shall ... error code ...` format.
- [ ] Verify presence of comprehensive Persian business scenarios and technical explanations.

### Gate 2: Code Traceability & Ground Truth Verification
- [ ] Verify referenced Java classes exist in Apache Fineract 1.15.0 across `fineract-cob`, `fineract-provider`, `fineract-loan`, and `fineract-core`.
- [ ] Verify database tables and columns match the Flyway/Liquibase schema (`m_batch_business_steps`, `m_loan_account_locks`, `m_holiday`, `m_working_days`, `job`, `job_run_history`, `BATCH_JOB_EXECUTION`, `m_loan_arrears_aging`, etc.).
- [ ] Verify error codes match Fineract runtime error strings and exception classes.

### Gate 3: Banking & Batch Invariants
- [ ] COB Completion Condition: For all active accounts, COB date equals target business date.
- [ ] Loan Account Locking & API Interception: Concurrency rejection (HTTP 409) when loan is locked by COB worker.
- [ ] Inline Loan COB Catch-Up: Day-by-day sequential execution for lagging loan accounts.
- [ ] Delinquency Aging (DPD) & Bucket Classification.
- [ ] Business Date Monotonicity: BusinessDate(t+1) = BusinessDate(t) + 1.
- [ ] Working Day Rescheduling & Holiday Adjustment Strategies.
"""

with open('docs/sdd/task-10-review-package.md', 'w', encoding='utf-8') as f:
    f.write(package_content)

print('Successfully written docs/sdd/task-10-review-package.md')
