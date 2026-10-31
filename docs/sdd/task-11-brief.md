# Task 11 Brief: Reverse-Engineering Tier 5 (Organization, CRM, Security & Infrastructure Integrations)

**Task ID:** Task 11  
**Parent Plan:** `docs/superpowers/plans/2026-10-28-fineract-ears-reverse-engineering-plan.md`  
**Deliverables Required:**
1. `docs/requirements/06-crm-organization-and-security.md`
2. `docs/requirements/07-infrastructure-and-integrations.md`
3. `docs/sdd/task-11-report.md`

---

## 1. Domain Scope & Mission

Reverse-engineer Apache Fineract 1.15.0's CRM, organizational hierarchy, role-based access control (RBAC), and technical integration infrastructure into two authoritative bilingual EARS specifications:

### File 1: `docs/requirements/06-crm-organization-and-security.md`
1. **Client KYC, Identifiers & Legal Forms:**
   - Person vs. Non-Person (Corporate/Entity) clients (`Client.java`, `ClientNonPerson.java`).
   - National identification cards, passports, tax IDs with uniqueness enforcement (`ClientIdentifier.java`).
   - Client lifecycle state machine (Pending -> Active -> Transfer In Progress -> Closed / Rejected / Withdrawn).
2. **Groups & Centers (Microfinance Group Lending):**
   - Joint Liability Groups (JLG) and Self-Help Groups (SHG) (`Group.java`, `Center.java`).
   - Group meeting calendars, group roles (Leader, Treasurer, Secretary), and group member association.
3. **Office Hierarchy & Inter-Branch Operations:**
   - Tree hierarchy (Head Office, Regional, Branch) with acyclic validation (`Office.java`, `OfficeDataValidator.java`).
   - Office opening date constraint: $\text{OpeningDate}(\text{child}) \ge \text{OpeningDate}(\text{parent})$.
   - Inter-branch office fund transfers (`m_office_transaction`).
4. **Staff Management & Portfolio Officer Assignment:**
   - Staff creation, office binding, loan officer vs. non-loan officer flags (`Staff.java`).
   - Bulk reassignment of client, loan, and savings portfolios between officers (`LoanOfficerAssignmentHistory`).
5. **Tellers, Cashiers & Cash Vault Management:**
   - Teller station setup, cashier assignment with operational date ranges and time windows (`Teller.java`, `Cashier.java`).
   - Cash allocation from vault, cash settlement back to vault, and cashier cash limits (`CashierTransaction.java`).
6. **User Administration, Password Policies & RBAC:**
   - User account lifecycle, multi-tenant credential storage, office hierarchy scoping (`AppUser.java`).
   - Role and granular permission assignment (`Role.java`, `Permission.java`, `m_role_permission`).
   - Password policy enforcement (length, history reuse prohibition `m_appuser_previous_password`, expiry).

### File 2: `docs/requirements/07-infrastructure-and-integrations.md`
1. **Transactional Outbox & Event Streaming Engine:**
   - Transactional Outbox pattern guaranteeing exactly-once / at-least-once message publishing (`m_external_event`, `ExternalEventConfiguration`).
   - Multi-broker messaging support: Apache Kafka and Apache ActiveMQ integration (`ActiveMQNotificationEventPublisher`, Kafka producers).
   - Domain business events serialization (`BusinessEventSerializer.java`, `BusinessEventNotifierService.java`).
2. **Webhooks & Outbound HTTP Integrations:**
   - Webhook registration, event triggers, HTTP basic auth / header tokens (`m_hook`, `m_hook_configuration`).
   - Webhook retry policies, asynchronous execution, and payload template formatting (`WebHookService`).
3. **Document Management & Storage Subsystems:**
   - File attachment metadata, multi-part file upload, MIME type whitelist validation (`m_document`, `Document.java`).
   - Multi-tenant storage backend abstraction: local filesystem storage vs. Amazon S3 / cloud blob storage.
4. **Dynamic Datatables & Entity Workflow Checks:**
   - User-defined extensible relational datatables (`x_registered_table`, `ReadWriteNonCoreDataService`).
   - Entity-datatable validation checks (`m_entity_datatable_check`): enforcing mandatory datatable entry prior to entity state transition (e.g., loan approval, client activation).
5. **In-App Notification Engine & Subscriptions:**
   - Notification topic configuration, subscriber assignment, and user notification inbox (`Notification.java`, `TopicSubscriber.java`).
6. **Two-Factor Authentication (2FA) & Communication Gateways:**
   - Time-based One-Time Password (TOTP) / SMS two-factor authentication setup (`TwoFactorConfiguration`).
   - SMS and email campaign integration gateways.

---

## 2. Document Architecture & Standards

Both requirement files must adhere strictly to the established bilingual standard:

### Section 1: Executive Summary, Architecture & Invariants
- Mathematical and architectural formulations:
  - Office Tree Acyclic Invariant: $\forall o \in \text{Offices}, o \notin \text{Ancestors}(o)$.
  - Office Opening Date Invariant: $t_{\text{open}}(o) \ge t_{\text{open}}(\text{parent}(o))$.
  - Cashier Cash Conservation Law: $\text{CashierBalance} = \sum \text{Allocations} + \sum \text{Inflows} - \sum \text{Outflows} - \sum \text{Settlements}$.
  - Transactional Outbox Atomicity: $E \in \text{Outbox} \iff \text{TxnCommit} = \text{true}$.
  - Datatable workflow check invariant.

### Section 2: Catalog Summary Table
- Markdown table mapping Requirement ID, Title (Persian), EARS Pattern, and Primary Source Class.

### Section 3+: Categorized Bilingual EARS Requirement Cards (18-20 per file)
Each card MUST contain:
1. **Title (Persian):** `#### REQ-[MODULE]-[CAT]-[NUM]: [عنوان دقیق فارسی]`
2. **EARS Pattern:** (Ubiquitous, Event-Driven, State-Driven, Unwanted Behavior, Optional Feature, Complex)
3. **EARS Statement (English):** Strict adherence to the **`shall`** modal verb iron rule. Forbidden modals (`should`, `will`, `can`, `must`) are strictly prohibited in normative prose.
4. **شرح نیازمندی و سناریوی بیزنس (فارسی):** Comprehensive Persian explanation.
5. **رفتارهای ناخواسته و شروط خطا (EARS If-Then):** Explicit `If...then the Fineract Engine shall...` clauses with authentic error codes/exceptions.
6. **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
   - Exact Java source file path and class name.
   - Method name(s).
   - Runtime error codes and Spring security annotations.
   - Database tables and columns.

---

## 3. Mandatory Quality Gates
- **Gate 1 (EARS Grammar):** 100% `shall`, 0 forbidden modals, standard If-Then clauses with error codes.
- **Gate 2 (Traceability):** Grounded in real Java files and Liquibase changelogs in `apache-fineract-src-1.15.0`.
- **Gate 3 (Banking & System Invariants):** Tree hierarchy acyclicity, cashier balance conservation, RBAC office scoping, transactional outbox atomicity, and datatable check enforcement.
