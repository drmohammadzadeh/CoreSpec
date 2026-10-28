---
name: fineract-db-schema-parser
description: Extracts core domain entities, relational integrity constraints, uniqueness invariants, and audit requirements from Flyway SQL and Liquibase changelogs across Apache Fineract into standardized EARS requirements. Activate when inspecting database migration files (.sql, .xml) in fineract-provider or fineract-db in apache-fineract-src-1.15.0.
---

# Fineract Database Schema & Migration Parser to EARS Requirements

## Overview
This skill guides agents in parsing database migration artifacts—including Liquibase XML/SQL changelogs and Flyway/raw DDL scripts within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`)—to systematically reverse-engineer domain entity models, relational integrity constraints, uniqueness invariants, and audit requirements into standardized EARS requirements.

## Target File Scope & Locations
This skill applies to all database changelog and migration files across the codebase:
* **Liquibase Master & Tenant Changelogs:**
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/db.changelog-tenant.xml`
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/*.xml` (e.g. `0001_initial_schema.xml`, `0002_initial_data.xml`, feature-specific XML changelogs)
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant-store/**/*.xml` (tenant registry and connection catalog)
* **Modular JPA & Subsystem Changelogs:**
  * `apache-fineract-src-1.15.0/**/src/main/resources/**/db/changelog/**/*.xml` (e.g. in `fineract-accounting`, `fineract-branch`)
* **Raw DDL & SQL Migration Scripts:**
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/sql/migrations/**/*.sql`
  * `apache-fineract-src-1.15.0/fineract-db/**/*.sql` (e.g. `mifospltaform-tenants-first-time-install.sql`, demo schema dumps)

---

## Architectural Semantics of Schema Definitions

1. **Table Definitions (`<createTable>` / `CREATE TABLE`):**
   * Establishes domain aggregate roots and child entity definitions (e.g., `m_loan`, `m_loan_transaction`, `m_savings_account`, `acc_gl_journal_entry`).
2. **Column Constraints (`nullable="false"`, `defaultValue`):**
   * Enforces mandatory domain attributes and financial non-null invariants.
3. **Primary & Foreign Keys (`<addForeignKeyConstraint>` / `FOREIGN KEY`):**
   * Enforces referential integrity between financial records (e.g. transactions referencing valid accounts, journal entries referencing chart of accounts).
4. **Unique Constraints (`<addUniqueConstraint>` / `UNIQUE KEY`):**
   * Enforces uniqueness invariants per tenant (e.g. account numbers, external IDs).
5. **Auditing & Concurrency Columns:**
   * Universal presence of `createdby_id`, `created_date`, `lastmodifiedby_id`, `lastmodified_date`, and `version` columns.

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **DB Schema Construct:** System-wide audit columns and optimistic locking version fields.
* **Extraction Pattern:**
  ```xml
  <column name="created_date" type="datetime"/>
  <column name="createdby_id" type="bigint"/>
  <column name="version" type="bigint" defaultValue="1"/>
  ```
  * Map to: `The Fineract Database Layer shall track the creation timestamp, creating user ID, and optimistic locking version on every record inserted into table "m_loan".`

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **DB Schema Construct:** State-dependent column population (e.g. disbursement date required when loan status is active).
* **Extraction Pattern:**
  * Map to: `While a loan record in "m_loan" has "loan_status_id" set to 300 (ACTIVE), the Fineract Database Layer shall maintain a non-null "disbursedon_date".`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **DB Schema Construct:** Foreign key cascading rules or trigger behaviors.
* **Extraction Pattern:**
  ```xml
  <addForeignKeyConstraint constraintName="fk_m_loan_m_client"
                           baseTableName="m_loan" baseColumnNames="client_id"
                           referencedTableName="m_client" referencedColumnNames="id"
                           onDelete="RESTRICT"/>
  ```
  * Map to: `When a deletion is requested for a record in "m_client", the Fineract Database Layer shall reject the deletion if referencing child records exist in "m_loan".`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **DB Schema Construct:** Optional auxiliary tables and feature-dependent columns (e.g. multi-disbursement, collateral, guarantor).
* **Extraction Pattern:**
  ```xml
  <createTable tableName="m_loan_disbursement_detail">
      <column name="loan_id" type="bigint"/>
      <column name="principal" type="decimal(19,6)"/>
      <column name="expected_disbursement_date" type="date"/>
  </createTable>
  ```
  * Map to: `Where multi-disbursement is configured for a loan, the Fineract Database Layer shall store individual disbursement tranches in table "m_loan_disbursement_detail".`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **DB Schema Construct:** Unique constraint violations and check constraint rejections.
* **Extraction Pattern:**
  ```xml
  <addUniqueConstraint tableName="m_loan"
                       columnNames="account_no"
                       constraintName="loan_account_no_unique"/>
  ```
  * Map to: `If a loan record insertion contains an "account_no" that already exists within the tenant schema, then the Fineract Database Layer shall abort the transaction and raise a unique constraint violation on "loan_account_no_unique".`

### 6. Complex Requirements
* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
* **DB Schema Construct:** Conditional foreign key associations depending on account type.
* **Extraction Pattern:**
  * Map to: `Where a loan is associated with a lending group, while the "group_id" column in "m_loan" is populated, the Fineract Database Layer shall enforce foreign key integrity against table "m_group".`

---

## Code Extraction Heuristics & Regex Patterns

| Target Element | Regex / Search Pattern | Semantics Extracted |
| :--- | :--- | :--- |
| **Liquibase Table** | `<createTable\s+tableName=["']([^"']+)["']` | Core domain entity table |
| **Liquibase Column** | `<column\s+name=["']([^"']+)["']\s+type=["']([^"']+)["']` | Entity attribute and data type |
| **Unique Constraint** | `<addUniqueConstraint\s+tableName=["']([^"']+)["']\s+columnNames=["']([^"']+)["']` | Domain uniqueness invariant |
| **Foreign Key** | `<addForeignKeyConstraint\s+baseTableName=["']([^"']+)["'].*referencedTableName=["']([^"']+)["']` | Relational integrity link |
| **Raw SQL Table** | `CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\`?([a-zA-Z0-9_]+)\`?` | Domain table definition |
| **Raw SQL Unique** | `UNIQUE\s+KEY\s+\`?([a-zA-Z0-9_]+)\`?\s*\(([^)]+)\)` | SQL unique index invariant |
| **Audit Columns** | `(created_date\|createdby_id\|lastmodified_date)` | Regulatory audit invariant |

---

## Step-by-Step DB Schema Parsing Workflow

1. **Locate Schema Changelogs:**
   * Review `fineract-provider/src/main/resources/db/changelog/tenant/parts/*.xml` for core tables (`m_loan`, `m_savings_account`, `acc_gl_journal_entry`).
2. **Extract Entity Constraints:**
   * Identify primary keys, foreign keys, and unique indexes for each table.
3. **Map State and Invariant Columns:**
   * Locate status columns (e.g. `loan_status_id`) and foreign keys to look up code values (`m_code_value`).
4. **Inspect Audit & Concurrency Columns:**
   * Verify standard audit columns (`createdby_id`, `created_date`, `lastmodifiedby_id`, `lastmodified_date`) and `version`.
5. **Formulate Bilingual EARS Card:**
   * Create the requirement card according to the standard template.

---

## Bilingual Output Requirement Card Template

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل ساختار داده، قیود یکتایی و روابط پایگاه داده به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل چنج‌لاگ:** `apache-fineract-src-1.15.0/.../<changelog>.xml`
  * **نام جدول و ستون‌ها:** `m_...`, `column_name`
  * **نام قید و کلید خارجی:** `fk_...`, `..._unique`
```

---

## Concrete Example

```markdown
### REQ-DB-LOAN-UNIQUE-ACCOUNT-001: یکتایی شماره حساب تسهیلات در سطح اسکیمای مستأجر
* **الگوی EARS:** Unwanted Behavior
* **EARS Statement:**
  > If a loan creation or modification transaction attempts to assign an "account_no" value that already exists in table "m_loan" for the current tenant schema, then the Fineract Database Layer shall reject the operation and raise a unique constraint violation on "loan_account_no_unique".
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  به منظور حفظ یکپارچگی داده‌های مالی و جلوگیری از اختلاط حساب‌های مشتریان، شماره حساب تسهیلات در جدول `m_loan` دارای قید یکتایی (Unique Constraint) است. سامانه پایگاه داده فاینراکت موظف است مانع از درج هرگونه شماره حساب تکراری در سطح هر مستأجر شده و در صورت بروز خطا، تراکنش پایگاه داده را لغو نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a duplicate "account_no" is inserted into table "m_loan", then the Fineract Database Layer shall fail the SQL transaction with constraint violation "loan_account_no_unique".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل چنج‌لاگ:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml`
  * **نام جدول و ستون‌ها:** جدول `m_loan`، ستون `account_no` (نوع داده `VARCHAR(20)`)
  * **نام قید و کلید خارجی:** قید یکتایی `loan_account_no_unique`
  * **انتیتی متناظر در جاوا:** `org.apache.fineract.portfolio.loanaccount.domain.Loan`
```
