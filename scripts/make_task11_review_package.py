import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

with open('docs/sdd/task-11-brief.md', 'r', encoding='utf-8') as f:
    brief = f.read()

with open('docs/sdd/task-11-report.md', 'r', encoding='utf-8') as f:
    report = f.read()

package_content = f"""# Task 11 Review Package: Tier 5 Organization, CRM, Security & Infrastructure Integrations

## 1. Task Brief Summary
This package consolidates the implementer deliverables for Task 11: Client KYC, Identifiers, Legal Forms, Groups, Centers, Office Tree Hierarchy, Staff Management, Tellers, Cashiers, RBAC Security, Transactional Outbox, Event Streaming, Webhooks, Document Management, Dynamic Datatables, Notifications, and 2FA reverse engineering.

---

## 2. Implementer Report
{report}

---

## 3. Verification & Quality Gates Checklist for Reviewer

### Gate 1: EARS Syntax, Grammar & Modal Iron Rule
- [ ] Verify all 40 requirement cards across both files (21 in Doc 06, 19 in Doc 07) contain valid EARS statements using `shall` strictly.
- [ ] Verify 0 occurrences of forbidden modals (`should`, `will`, `can`, `must`) in EARS statements (except inside literal error code strings/class identifiers).
- [ ] Verify all unwanted behavior conditions use the standard `If ... then the Fineract Engine shall ... error code ...` format.
- [ ] Verify presence of comprehensive Persian business scenarios and technical explanations.

### Gate 2: Code Traceability & Ground Truth Verification
- [ ] Verify referenced Java classes exist in Apache Fineract 1.15.0 across client, group, organisation, useradministration, notification, and infrastructure modules.
- [ ] Verify database tables and columns match the Flyway/Liquibase schema (`m_client`, `m_group`, `m_office`, `m_staff`, `m_tellers`, `m_cashiers`, `m_appuser`, `m_role`, `m_permission`, `m_external_event`, `m_hook`, `m_document`, `x_registered_table`, `m_entity_datatable_check`, etc.).
- [ ] Verify error codes match Fineract runtime error strings and exception classes.

### Gate 3: Banking & Technical Domain Invariants
- [ ] Office Tree Acyclic Invariant and opening date monotonicity: $t_{{open}}(\\text{{child}}) \\ge t_{{open}}(\\text{{parent}})$.
- [ ] Cashier Cash Conservation Law and vault allocation/settlement.
- [ ] RBAC Office Scoping Security Invariant: user cannot access entities outside their office subtree.
- [ ] Transactional Outbox Atomicity: event published iff database transaction commits.
- [ ] Datatable Workflow Check Invariant: mandatory datatable entry prior to state transition.
"""

with open('docs/sdd/task-11-review-package.md', 'w', encoding='utf-8') as f:
    f.write(package_content)

print('Successfully written docs/sdd/task-11-review-package.md')
