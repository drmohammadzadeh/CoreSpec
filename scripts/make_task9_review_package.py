import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

with open('docs/sdd/task-9-brief.md', 'r', encoding='utf-8') as f:
    brief = f.read()

with open('docs/sdd/task-9-report.md', 'r', encoding='utf-8') as f:
    report = f.read()

package_content = f"""# Task 9 Review Package: Tier 3 Core Accounting, Financial GL & Charges/Tax

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 9: Core Accounting, Financial GL, Double-Entry Balance Conservation, Charges, Fees, Taxes, and Interest Rates reverse engineering.

---

## 2. Implementer Report
{report}

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
- [ ] Double-Entry Balance Conservation Law: $\\sum \\text{{Debits}} = \\sum \\text{{Credits}}$ across all journal entries.
- [ ] Cash vs Accrual accounting models: Cash, Periodic Accrual, Upfront Accrual.
- [ ] Accounting Closures (GLClosure): $t_{{\\text{{txn}}}} > t_{{\\text{{closure}}}}$ invariant preventing backdated entries before closure.
- [ ] Charge calculation modes: Flat, % of Amount, % of Loan + Interest, % of Interest, % of Disbursement with min/max caps clamping.
- [ ] Tax component & group split calculation on banking fees and interest withholding.
- [ ] Floating rate singleton Base Lending Rate invariant and interest rate slab evaluation.
"""

with open('docs/sdd/task-9-review-package.md', 'w', encoding='utf-8') as f:
    f.write(package_content)

print('Successfully written docs/sdd/task-9-review-package.md')
