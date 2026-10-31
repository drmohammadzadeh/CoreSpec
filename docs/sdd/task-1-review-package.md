commit 6c7de4061d9c21147638e0650846fcce8ccd8744
Author: Rahman Alimohammadzadeh <alimohammadzadeh.r@tiddev.com>
Date:   Wed Oct 28 17:11:01 2026 +0330

    feat(skills): add 6 dedicated file-parsing skills for Fineract reverse engineering

 .skills/fineract-config-parser/SKILL.md    | 166 ++++++++++++++++++++++++++
 .skills/fineract-db-schema-parser/SKILL.md | 169 ++++++++++++++++++++++++++
 .skills/fineract-doc-parser/SKILL.md       | 135 +++++++++++++++++++++
 .skills/fineract-gradle-parser/SKILL.md    | 180 ++++++++++++++++++++++++++++
 .skills/fineract-java-parser/SKILL.md      | 185 +++++++++++++++++++++++++++++
 .skills/fineract-xml-parser/SKILL.md       | 174 +++++++++++++++++++++++++++
 6 files changed, 1009 insertions(+)
diff --git a/.skills/fineract-config-parser/SKILL.md b/.skills/fineract-config-parser/SKILL.md
new file mode 100644
index 0000000..22975a7
--- /dev/null
+++ b/.skills/fineract-config-parser/SKILL.md
@@ -0,0 +1,166 @@
+---
+name: fineract-config-parser
+description: Extracts system configuration constraints, multi-tenancy rules, security toggles, and operational parameters from properties and YAML configuration files across Apache Fineract into standardized EARS requirements. Activate when inspecting application.properties, application.yml, or Docker configuration files in apache-fineract-src-1.15.0.
+---
+
+# Fineract Configuration Parser to EARS Requirements
+
+## Overview
+This skill guides agents in parsing configuration files (`application.properties`, `application.yml`, Docker environment files) within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to extract operational defaults, feature toggles, multi-tenancy routing rules, connection pool bounds, and environmental constraints into standardized EARS requirements.
+
+## Target File Scope & Locations
+This skill applies to all configuration files across the codebase:
+* **Spring Application Configuration:**
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.properties`
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.yml`
+  * `apache-fineract-src-1.15.0/**/src/main/resources/application-*.properties` (e.g. `application-test.properties`, `application-oauth.properties`)
+* **Docker & Container Runtime Settings:**
+  * `apache-fineract-src-1.15.0/docker/docker-compose*.yml`
+  * `apache-fineract-src-1.15.0/config/docker/**/*.env`
+  * `apache-fineract-src-1.15.0/docker/Dockerfile`
+* **Java Configuration Beans:**
+  * Classes annotated with `@ConfigurationProperties(prefix = "fineract...")`
+
+---
+
+## Configuration Property Semantics
+
+1. **Multi-Tenancy Configuration (`fineract.tenant.*`):**
+   * Configures shared tenant store vs isolated tenant databases, schema resolution strategies, and tenant header names.
+2. **Feature Toggles (`fineract.mode.*`, `fineract.events.*`):**
+   * Controls whether asynchronous command processing, external Kafka/ActiveMQ messaging, or OAuth2 authentication are active.
+3. **Operational Thresholds & Defaults:**
+   * Pagination limits (`fineract.pagination.default-limit`), Hikari connection pool sizes, session timeouts, and COB batch thread counts.
+4. **Environment Variables Overrides:**
+   * Standard convention: property `fineract.tenant.username` is overridden by environment variable `FINERACT_DEFAULT_TENANTDB_USER`.
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **Config Construct:** Hardcoded or default operational parameters and thresholds applied universally.
+* **Extraction Pattern:**
+  ```properties
+  server.port=8080
+  fineract.pagination.default-limit=200
+  ```
+  * Map to: `The Fineract Platform shall limit default API search query pagination to a maximum of 200 records per response.`
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **Config Construct:** Resource pool states, thread saturation, read-only replica status.
+* **Extraction Pattern:**
+  ```properties
+  spring.datasource.hikari.connection-timeout=30000
+  spring.datasource.hikari.maximum-pool-size=20
+  ```
+  * Map to: `While the tenant connection pool is at maximum capacity (20 active connections), the Fineract DataSource Manager shall hold pending database requests up to 30,000 milliseconds before timing out.`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **Config Construct:** Application bootstrapping, context refresh, dynamic configuration update events.
+* **Extraction Pattern:**
+  ```properties
+  fineract.tenant.reload.enabled=true
+  ```
+  * Map to: `When a tenant registration or update event occurs, the Fineract Tenant Manager shall dynamically refresh the tenant connection pool without restarting the application server.`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **Config Construct:** Feature flags enabled via boolean configuration properties (`fineract.mode.async-enabled=true`, `fineract.events.external.enabled=true`).
+* **Extraction Pattern:**
+  ```properties
+  fineract.events.external.enabled=true
+  fineract.events.external.producer.jms.enabled=true
+  ```
+  * Map to: `Where external event publishing is enabled, the Fineract Event Engine shall publish domain events to the configured JMS broker topic.`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **Config Construct:** Missing required configuration, invalid tenant identifier header, database connection failure.
+* **Extraction Pattern:**
+  ```properties
+  fineract.tenant.identifier-header=Fineract-Platform-TenantId
+  ```
+  * Map to: `If an incoming HTTP request lacks a valid tenant identifier in the "Fineract-Platform-TenantId" header, then the Fineract Gateway shall reject the request and return HTTP status 400 Bad Request with error code "error.msg.invalid.tenant.identifier".`
+
+### 6. Complex Requirements
+* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
+* **Config Construct:** Multi-tenancy combined with batch processing or external authentication servers.
+* **Extraction Pattern:**
+  ```properties
+  fineract.tenant.mode=multi-tenant
+  fineract.security.oauth.enabled=true
+  ```
+  * Map to: `Where multi-tenancy is active, while OAuth2 authentication is enabled, when a secure REST endpoint is invoked, the Fineract Security Gateway shall validate the bearer token against the specific tenant authorization server.`
+
+---
+
+## Code Extraction Heuristics & Regex Patterns
+
+| Target Element | Regex / Search Pattern | Semantics Extracted |
+| :--- | :--- | :--- |
+| **Property Key-Value** | `^([a-zA-Z0-9.\-_]+)\s*=\s*(.*)$` | Configuration key and default value |
+| **YAML Key-Value** | `^\s*([a-zA-Z0-9\-_]+):\s*(.*)$` | Hierarchical configuration property |
+| **Env Var Mapping** | `\$\{([A-Z0-9_]+):([^}]+)\}` | Environment variable fallback and default |
+| **Hikari Pool Bounds** | `spring\.datasource\.hikari\.(maximum-pool-size\|minimum-idle)` | Connection pooling constraints |
+| **Tenant Routing Key** | `fineract\.tenant\.(identifier-header\|datasource\..*)` | Multi-tenancy routing invariants |
+| **External Event Toggle** | `fineract\.events\.external\.(enabled\|producer\..*)` | Event streaming integrations |
+
+---
+
+## Step-by-Step Configuration Parsing Workflow
+
+1. **Inspect `application.properties` and `application.yml`:**
+   * Catalog core operational variables (server port, context path, SSL, datasource parameters).
+2. **Scan Multi-Tenant Configuration:**
+   * Extract tenant master DB credentials, connection pools, and header definitions (`Fineract-Platform-TenantId`).
+3. **Scan Feature Toggles:**
+   * Identify all `fineract.*` feature flags and their default boolean states.
+4. **Cross-Reference with `@ConfigurationProperties`:**
+   * Locate the Java configuration class (e.g., `FineractProperties.java`) to verify types, validation constraints, and defaults.
+5. **Formulate Bilingual EARS Card:**
+   * Construct the requirement card according to the standard template.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ┘à┘ü┘ç┘ê┘à ┘╛█î┌⌐╪▒╪¿┘å╪»█î╪î ┘à┘é╪º╪»█î╪▒ ┘╛█î╪┤ΓÇî┘ü╪▒╪╢ ┘ê ╪¬╪ú╪½█î╪▒ ╪ó┘å ╪¿╪▒ ╪¿█î╪▓┘å╪│ ╪│╪º┘à╪º┘å┘ç ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä█î╪» ┘╛█î┌⌐╪▒╪¿┘å╪»█î:** `apache-fineract-src-1.15.0/.../application.properties`
+  * **┘å╪º┘à ┌⌐┘ä█î╪»:** `fineract....`
+  * **┘à╪¬╪║█î╪▒ ┘à╪¡█î╪╖█î ┘à╪╣╪º╪»┘ä:** `FINERACT_...`
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-CFG-TENANT-ROUTING-001: ┘à╪│█î╪▒█î╪º╪¿█î ╪»╪▒╪«┘ê╪º╪│╪¬ΓÇî┘ç╪º ╪¿╪▒ ╪º╪│╪º╪│ ╪┤┘å╪º╪│┘ç ┘à╪│╪¬╪ú╪¼╪▒ (Multi-Tenancy)
+* **╪º┘ä┌»┘ê█î EARS:** Optional Feature
+* **EARS Statement:**
+  > Where multi-tenancy is enabled, the Fineract Platform shall inspect the "Fineract-Platform-TenantId" HTTP header of each incoming request and route all database queries and transactions to the corresponding tenant schema.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ╪│╪º┘à╪º┘å┘ç ┘ü╪º█î┘å╪▒╪º┌⌐╪¬ ╪¿┘ç ╪╡┘ê╪▒╪¬ ┘╛█î╪┤ΓÇî┘ü╪▒╪╢ ╪º╪▓ ┘à╪╣┘à╪º╪▒█î ┌å┘å╪»┘à╪│╪¬╪ú╪¼╪▒█î (Multi-Tenancy) ╪¿╪º ╪¬┘ü┌⌐█î┌⌐ ┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç █î╪º ╪º╪│┌⌐█î┘à╪º█î ┘à╪│╪¬┘é┘ä ┘╛╪┤╪¬█î╪¿╪º┘å█î ┘à█îΓÇî┌⌐┘å╪». ╪»╪▒ ╪º█î┘å ╪│╪º╪«╪¬╪º╪▒╪î ┘ç╪▒ ╪»╪▒╪«┘ê╪º╪│╪¬ ┘ê╪¿ ╪¡╪º┘ê█î ┘ç╪»╪▒ ╪┤┘å╪º╪│┘ç ┘à╪│╪¬╪ú╪¼╪▒ ╪¿┘ê╪»┘ç ┘ê ┘ç╪│╪¬┘ç ┘╛┘ä╪¬┘ü╪▒┘à ╪¿┘ç ╪╡┘ê╪▒╪¬ ╪«┘ê╪»┌⌐╪º╪▒ ┌⌐╪º┘å┌⌐╪┤┘å ╪»█î╪¬╪º╪¿█î╪│ ╪▒╪º ╪¿┘ç ┘à╪«╪▓┘å ╪»╪º╪»┘ç ┘ç┘à╪º┘å ┘à╪│╪¬╪ú╪¼╪▒ ┘ç╪»╪º█î╪¬ ┘à█îΓÇî┘å┘à╪º█î╪» ╪¬╪º ╪º█î╪▓┘ê┘ä╪º╪│█î┘ê┘å ┌⌐╪º┘à┘ä ╪»╪º╪»┘çΓÇî┘ç╪º█î ┘à╪º┘ä█î ╪¬╪╢┘à█î┘å ┌»╪▒╪»╪».
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If an incoming API request does not contain the "Fineract-Platform-TenantId" header or contains a non-existent tenant identifier, then the Fineract Platform shall reject the request and return HTTP status 400 Bad Request with error code "error.msg.invalid.tenant.identifier".`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä█î╪» ┘╛█î┌⌐╪▒╪¿┘å╪»█î:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.properties`
+  * **┘å╪º┘à ┌⌐┘ä█î╪»:** `fineract.tenant.identifier-header=Fineract-Platform-TenantId`
+  * **┘à╪¬╪║█î╪▒ ┘à╪¡█î╪╖█î ┘à╪╣╪º╪»┘ä:** `FINERACT_DEFAULT_TENANTDB_IDENTIFIER`
+  * **┌⌐┘ä╪º╪│ ┘à╪¬┘å╪º╪╕╪▒ ╪»╪▒ ┌⌐╪»:** `org.apache.fineract.infrastructure.core.boot.FineractProperties`
+```
diff --git a/.skills/fineract-db-schema-parser/SKILL.md b/.skills/fineract-db-schema-parser/SKILL.md
new file mode 100644
index 0000000..dd88203
--- /dev/null
+++ b/.skills/fineract-db-schema-parser/SKILL.md
@@ -0,0 +1,169 @@
+---
+name: fineract-db-schema-parser
+description: Extracts core domain entities, relational integrity constraints, uniqueness invariants, and audit requirements from Flyway SQL and Liquibase changelogs across Apache Fineract into standardized EARS requirements. Activate when inspecting database migration files (.sql, .xml) in fineract-provider or fineract-db in apache-fineract-src-1.15.0.
+---
+
+# Fineract Database Schema & Migration Parser to EARS Requirements
+
+## Overview
+This skill guides agents in parsing database migration artifactsΓÇöincluding Liquibase XML/SQL changelogs and Flyway/raw DDL scripts within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`)ΓÇöto systematically reverse-engineer domain entity models, relational integrity constraints, uniqueness invariants, and audit requirements into standardized EARS requirements.
+
+## Target File Scope & Locations
+This skill applies to all database changelog and migration files across the codebase:
+* **Liquibase Master & Tenant Changelogs:**
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/db.changelog-tenant.xml`
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/*.xml` (e.g. `0001_initial_schema.xml`, `0002_initial_data.xml`, feature-specific XML changelogs)
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant-store/**/*.xml` (tenant registry and connection catalog)
+* **Modular JPA & Subsystem Changelogs:**
+  * `apache-fineract-src-1.15.0/**/src/main/resources/**/db/changelog/**/*.xml` (e.g. in `fineract-accounting`, `fineract-branch`)
+* **Raw DDL & SQL Migration Scripts:**
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/sql/migrations/**/*.sql`
+  * `apache-fineract-src-1.15.0/fineract-db/**/*.sql` (e.g. `mifospltaform-tenants-first-time-install.sql`, demo schema dumps)
+
+---
+
+## Architectural Semantics of Schema Definitions
+
+1. **Table Definitions (`<createTable>` / `CREATE TABLE`):**
+   * Establishes domain aggregate roots and child entity definitions (e.g., `m_loan`, `m_loan_transaction`, `m_savings_account`, `acc_gl_journal_entry`).
+2. **Column Constraints (`nullable="false"`, `defaultValue`):**
+   * Enforces mandatory domain attributes and financial non-null invariants.
+3. **Primary & Foreign Keys (`<addForeignKeyConstraint>` / `FOREIGN KEY`):**
+   * Enforces referential integrity between financial records (e.g. transactions referencing valid accounts, journal entries referencing chart of accounts).
+4. **Unique Constraints (`<addUniqueConstraint>` / `UNIQUE KEY`):**
+   * Enforces uniqueness invariants per tenant (e.g. account numbers, external IDs).
+5. **Auditing & Concurrency Columns:**
+   * Universal presence of `createdby_id`, `created_date`, `lastmodifiedby_id`, `lastmodified_date`, and `version` columns.
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **DB Schema Construct:** System-wide audit columns and optimistic locking version fields.
+* **Extraction Pattern:**
+  ```xml
+  <column name="created_date" type="datetime"/>
+  <column name="createdby_id" type="bigint"/>
+  <column name="version" type="bigint" defaultValue="1"/>
+  ```
+  * Map to: `The Fineract Database Layer shall track the creation timestamp, creating user ID, and optimistic locking version on every record inserted into table "m_loan".`
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **DB Schema Construct:** State-dependent column population (e.g. disbursement date required when loan status is active).
+* **Extraction Pattern:**
+  * Map to: `While a loan record in "m_loan" has "loan_status_id" set to 300 (ACTIVE), the Fineract Database Layer shall maintain a non-null "disbursedon_date".`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **DB Schema Construct:** Foreign key cascading rules or trigger behaviors.
+* **Extraction Pattern:**
+  ```xml
+  <addForeignKeyConstraint constraintName="fk_m_loan_m_client"
+                           baseTableName="m_loan" baseColumnNames="client_id"
+                           referencedTableName="m_client" referencedColumnNames="id"
+                           onDelete="RESTRICT"/>
+  ```
+  * Map to: `When a deletion is requested for a record in "m_client", the Fineract Database Layer shall reject the deletion if referencing child records exist in "m_loan".`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **DB Schema Construct:** Optional auxiliary tables and feature-dependent columns (e.g. multi-disbursement, collateral, guarantor).
+* **Extraction Pattern:**
+  ```xml
+  <createTable tableName="m_loan_disbursement_detail">
+      <column name="loan_id" type="bigint"/>
+      <column name="principal" type="decimal(19,6)"/>
+      <column name="expected_disbursement_date" type="date"/>
+  </createTable>
+  ```
+  * Map to: `Where multi-disbursement is configured for a loan, the Fineract Database Layer shall store individual disbursement tranches in table "m_loan_disbursement_detail".`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **DB Schema Construct:** Unique constraint violations and check constraint rejections.
+* **Extraction Pattern:**
+  ```xml
+  <addUniqueConstraint tableName="m_loan"
+                       columnNames="account_no"
+                       constraintName="loan_account_no_unique"/>
+  ```
+  * Map to: `If a loan record insertion contains an "account_no" that already exists within the tenant schema, then the Fineract Database Layer shall abort the transaction and raise a unique constraint violation on "loan_account_no_unique".`
+
+### 6. Complex Requirements
+* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
+* **DB Schema Construct:** Conditional foreign key associations depending on account type.
+* **Extraction Pattern:**
+  * Map to: `Where a loan is associated with a lending group, while the "group_id" column in "m_loan" is populated, the Fineract Database Layer shall enforce foreign key integrity against table "m_group".`
+
+---
+
+## Code Extraction Heuristics & Regex Patterns
+
+| Target Element | Regex / Search Pattern | Semantics Extracted |
+| :--- | :--- | :--- |
+| **Liquibase Table** | `<createTable\s+tableName=["']([^"']+)["']` | Core domain entity table |
+| **Liquibase Column** | `<column\s+name=["']([^"']+)["']\s+type=["']([^"']+)["']` | Entity attribute and data type |
+| **Unique Constraint** | `<addUniqueConstraint\s+tableName=["']([^"']+)["']\s+columnNames=["']([^"']+)["']` | Domain uniqueness invariant |
+| **Foreign Key** | `<addForeignKeyConstraint\s+baseTableName=["']([^"']+)["'].*referencedTableName=["']([^"']+)["']` | Relational integrity link |
+| **Raw SQL Table** | `CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\`?([a-zA-Z0-9_]+)\`?` | Domain table definition |
+| **Raw SQL Unique** | `UNIQUE\s+KEY\s+\`?([a-zA-Z0-9_]+)\`?\s*\(([^)]+)\)` | SQL unique index invariant |
+| **Audit Columns** | `(created_date\|createdby_id\|lastmodified_date)` | Regulatory audit invariant |
+
+---
+
+## Step-by-Step DB Schema Parsing Workflow
+
+1. **Locate Schema Changelogs:**
+   * Review `fineract-provider/src/main/resources/db/changelog/tenant/parts/*.xml` for core tables (`m_loan`, `m_savings_account`, `acc_gl_journal_entry`).
+2. **Extract Entity Constraints:**
+   * Identify primary keys, foreign keys, and unique indexes for each table.
+3. **Map State and Invariant Columns:**
+   * Locate status columns (e.g. `loan_status_id`) and foreign keys to look up code values (`m_code_value`).
+4. **Inspect Audit & Concurrency Columns:**
+   * Verify standard audit columns (`createdby_id`, `created_date`, `lastmodifiedby_id`, `lastmodified_date`) and `version`.
+5. **Formulate Bilingual EARS Card:**
+   * Create the requirement card according to the standard template.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ╪│╪º╪«╪¬╪º╪▒ ╪»╪º╪»┘ç╪î ┘é█î┘ê╪» █î┌⌐╪¬╪º█î█î ┘ê ╪▒┘ê╪º╪¿╪╖ ┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┌å┘å╪¼ΓÇî┘ä╪º┌»:** `apache-fineract-src-1.15.0/.../<changelog>.xml`
+  * **┘å╪º┘à ╪¼╪»┘ê┘ä ┘ê ╪│╪¬┘ê┘åΓÇî┘ç╪º:** `m_...`, `column_name`
+  * **┘å╪º┘à ┘é█î╪» ┘ê ┌⌐┘ä█î╪» ╪«╪º╪▒╪¼█î:** `fk_...`, `..._unique`
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-DB-LOAN-UNIQUE-ACCOUNT-001: █î┌⌐╪¬╪º█î█î ╪┤┘à╪º╪▒┘ç ╪¡╪│╪º╪¿ ╪¬╪│┘ç█î┘ä╪º╪¬ ╪»╪▒ ╪│╪╖╪¡ ╪º╪│┌⌐█î┘à╪º█î ┘à╪│╪¬╪ú╪¼╪▒
+* **╪º┘ä┌»┘ê█î EARS:** Unwanted Behavior
+* **EARS Statement:**
+  > If a loan creation or modification transaction attempts to assign an "account_no" value that already exists in table "m_loan" for the current tenant schema, then the Fineract Database Layer shall reject the operation and raise a unique constraint violation on "loan_account_no_unique".
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ╪¿┘ç ┘à┘å╪╕┘ê╪▒ ╪¡┘ü╪╕ █î┌⌐┘╛╪º╪▒┌å┌»█î ╪»╪º╪»┘çΓÇî┘ç╪º█î ┘à╪º┘ä█î ┘ê ╪¼┘ä┘ê┌»█î╪▒█î ╪º╪▓ ╪º╪«╪¬┘ä╪º╪╖ ╪¡╪│╪º╪¿ΓÇî┘ç╪º█î ┘à╪┤╪¬╪▒█î╪º┘å╪î ╪┤┘à╪º╪▒┘ç ╪¡╪│╪º╪¿ ╪¬╪│┘ç█î┘ä╪º╪¬ ╪»╪▒ ╪¼╪»┘ê┘ä `m_loan` ╪»╪º╪▒╪º█î ┘é█î╪» █î┌⌐╪¬╪º█î█î (Unique Constraint) ╪º╪│╪¬. ╪│╪º┘à╪º┘å┘ç ┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ┘ü╪º█î┘å╪▒╪º┌⌐╪¬ ┘à┘ê╪╕┘ü ╪º╪│╪¬ ┘à╪º┘å╪╣ ╪º╪▓ ╪»╪▒╪¼ ┘ç╪▒┌»┘ê┘å┘ç ╪┤┘à╪º╪▒┘ç ╪¡╪│╪º╪¿ ╪¬┌⌐╪▒╪º╪▒█î ╪»╪▒ ╪│╪╖╪¡ ┘ç╪▒ ┘à╪│╪¬╪ú╪¼╪▒ ╪┤╪»┘ç ┘ê ╪»╪▒ ╪╡┘ê╪▒╪¬ ╪¿╪▒┘ê╪▓ ╪«╪╖╪º╪î ╪¬╪▒╪º┌⌐┘å╪┤ ┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ╪▒╪º ┘ä╪║┘ê ┘å┘à╪º█î╪».
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If a duplicate "account_no" is inserted into table "m_loan", then the Fineract Database Layer shall fail the SQL transaction with constraint violation "loan_account_no_unique".`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┌å┘å╪¼ΓÇî┘ä╪º┌»:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/tenant/parts/0001_initial_schema.xml`
+  * **┘å╪º┘à ╪¼╪»┘ê┘ä ┘ê ╪│╪¬┘ê┘åΓÇî┘ç╪º:** ╪¼╪»┘ê┘ä `m_loan`╪î ╪│╪¬┘ê┘å `account_no` (┘å┘ê╪╣ ╪»╪º╪»┘ç `VARCHAR(20)`)
+  * **┘å╪º┘à ┘é█î╪» ┘ê ┌⌐┘ä█î╪» ╪«╪º╪▒╪¼█î:** ┘é█î╪» █î┌⌐╪¬╪º█î█î `loan_account_no_unique`
+  * **╪º┘å╪¬█î╪¬█î ┘à╪¬┘å╪º╪╕╪▒ ╪»╪▒ ╪¼╪º┘ê╪º:** `org.apache.fineract.portfolio.loanaccount.domain.Loan`
+```
diff --git a/.skills/fineract-doc-parser/SKILL.md b/.skills/fineract-doc-parser/SKILL.md
new file mode 100644
index 0000000..9fc294f
--- /dev/null
+++ b/.skills/fineract-doc-parser/SKILL.md
@@ -0,0 +1,135 @@
+---
+name: fineract-doc-parser
+description: Extracts declared business rules, financial workflows, and user-facing functional requirements from AsciiDoc, Markdown, and crawled HTML documentation across Apache Fineract into standardized EARS requirements. Activate when inspecting documentation files in fineract-doc, READMEs, or docs/crawled/.
+---
+
+# Fineract Documentation Parser to EARS Requirements
+
+## Overview
+This skill guides agents in parsing textual documentationΓÇöincluding AsciiDoc files (`*.adoc`), Markdown specifications (`*.md`), and crawled HTML documents (`docs/crawled/`)ΓÇöto extract declared business rules, banking calculation specifications, user workflows, and regulatory constraints into standardized EARS requirements.
+
+Crucially, this skill enforces **Doc-to-Code Reconciliation**: every declared business rule found in documentation must be cross-verified against the actual Java implementation to prevent documentation drift or hallucination.
+
+## Target File Scope & Locations
+This skill applies to all documentation assets within the workspace:
+* **In-Repository AsciiDoc Files:**
+  * `apache-fineract-src-1.15.0/fineract-doc/src/docs/asciidoc/**/*.adoc`
+  * Subproject user manuals and developer guides
+* **Repository Markdown Files:**
+  * `apache-fineract-src-1.15.0/README.md`
+  * `apache-fineract-src-1.15.0/**/README.md`
+  * `apache-fineract-src-1.15.0/CHANGELOG.md`
+* **Crawled Online Documentation:**
+  * `docs/crawled/sitemap.json`
+  * `docs/crawled/SUMMARY.md`
+  * `docs/crawled/pages/**/*.md` (Crawled technical and operational documentation from `https://fineract.apache.org/docs/stable`)
+
+---
+
+## Architectural Semantics of Documentation
+
+1. **Declared Functional Capabilities:**
+   * High-level feature definitions, supported financial conventions (e.g. Day count conventions: 30/360, Actual/365, Actual/Actual).
+2. **Business Workflows & State Progression:**
+   * Declared lifecycle workflows (e.g., Loan lifecycle: `Submitted` $\to$ `Approved` $\to$ `Disbursed` $\to$ `Active` $\to$ `Closed`).
+3. **Financial Formulas & Calculations:**
+   * Amortization algorithms (Equal Installments, Equal Principal, Declining Balance), compound interest frequencies, penalty calculations.
+4. **Declared Constraints & Validation Boundaries:**
+   * Documented limitations (e.g., maximum term, minimum disbursement amount, grace period limits).
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **Doc Construct:** Universally declared business rules or regulatory capabilities.
+* **Extraction Pattern:**
+  * Documented statement: "Fineract supports both Cash-based and Accrual-based accounting principles across all loan products."
+  * Map to: `The Fineract Accounting Engine shall support both Cash-based and Accrual-based accounting methodologies for all financial transaction postings.`
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **Doc Construct:** Workflow step prerequisites and lifecycle constraints.
+* **Extraction Pattern:**
+  * Documented statement: "A loan account cannot be closed while there is any outstanding principal balance remaining."
+  * Map to: `While a loan account retains a non-zero outstanding balance, the Fineract Loan Engine shall prohibit loan account closure.`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **Doc Construct:** Documented operational events, end-of-day operations, batch scheduling.
+* **Extraction Pattern:**
+  * Documented statement: "At the end of each business day, Close-of-Business batch job calculates and posts daily interest accruals."
+  * Map to: `When the Close-of-Business (COB) daily job executes, the Fineract Batch Subsystem shall calculate and post accrued interest for all eligible active accounts.`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **Doc Construct:** Documented optional capabilities (e.g. Moratorium, Floating interest rates, Tranche disbursement).
+* **Extraction Pattern:**
+  * Documented statement: "Where a repayment moratorium is defined on principal, installments within the moratorium period only require interest repayment."
+  * Map to: `Where a principal repayment moratorium is configured on a loan account, the Fineract Loan Engine shall exclude principal amortization from installments falling within the moratorium window.`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **Doc Construct:** Documented warning callouts, validation rules, operational prohibitions.
+* **Extraction Pattern:**
+  * Documented statement: "NOTE: Disbursing a loan on a date before the approval date is strictly forbidden."
+  * Map to: `If a user attempts to record a loan disbursement with a transaction date prior to the approval date, then the Fineract Loan Engine shall reject the transaction with error code "error.msg.loan.disbursement.date.cannot.be.before.approved.date".`
+
+### 6. Complex Requirements
+* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
+* **Doc Construct:** Documented conditional features during specific operational states.
+* **Extraction Pattern:**
+  * Map to: `Where floating interest rates are enabled, while the loan account is in "ACTIVE" state, when a base interest rate change occurs, the Fineract Loan Engine shall dynamically recalculate future installment schedules.`
+
+---
+
+## Heuristics for Doc-to-Code Reconciliation
+
+To prevent hallucinated or outdated requirements, follow this mandatory 3-step check:
+1. **Extract Candidate:** Identify the declared rule and parameters (e.g. grace period, interest method).
+2. **Locate Implementation:** Search Java source code in `apache-fineract-src-1.15.0/` (using methods, enums, or validator error codes) to verify the rule exists.
+3. **Reconcile Parameters:** If documentation claims behavior $X$ but the code implements $Y$, prioritize the code as the ground truth, document the discrepancy in the Persian rationale, and link the exact source code location in the Traceability Matrix.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ╪│┘å╪º╪▒█î┘ê█î ╪¿╪º┘å┌⌐█î ╪¿╪▒ ╪º╪│╪º╪│ ┘à╪│╪¬┘å╪»╪º╪¬ ╪▒╪│┘à█î╪î ┘à┘å╪╖┘é ┘à╪º┘ä█î ┘ê ╪º┘å╪╖╪¿╪º┘é ╪¿╪º ╪▒┘ü╪¬╪º╪▒ ╪│█î╪│╪¬┘à ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à┘å╪¿╪╣ ┘à╪│╪¬┘å╪»╪º╪¬:** `fineract-doc/.../*.adoc` █î╪º `docs/crawled/pages/...`
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│ ┘à╪¬┘å╪º╪╕╪▒:** `apache-fineract-src-1.15.0/.../ClassName.java`
+  * **┘à╪¬╪» ╪º╪¼╪▒╪º█î█î:** `#methodName()`
+  * **┌⌐╪»┘ç╪º█î ╪«╪╖╪º ┘ê ╪º┘å┘ê╪¬█î╪┤┘åΓÇî┘ç╪º:** `error.msg....`
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-DOC-LOAN-MORATORIUM-001: ╪º╪╣┘à╪º┘ä ╪»┘ê╪▒┘ç ╪¬┘å┘ü╪│ ╪»╪▒ ╪¿╪º╪▓┘╛╪▒╪»╪º╪«╪¬ ╪º╪╡┘ä ┘ê╪º┘à (Grace Period / Moratorium)
+* **╪º┘ä┌»┘ê█î EARS:** Optional Feature
+* **EARS Statement:**
+  > Where a principal repayment moratorium is configured for a loan product, the Fineract Loan Engine shall exclude principal amounts from repayment installments during the designated moratorium period while continuing to accrue and demand interest payments.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ╪¿╪▒ ╪º╪│╪º╪│ ┘à╪│╪¬┘å╪»╪º╪¬ ╪▒╪│┘à█î ╪│╪º┘à╪º┘å┘ç╪î ╪»╪▒ ╪╡┘ê╪▒╪¬█î ┌⌐┘ç ╪»┘ê╪▒┘ç ╪¬┘å┘ü╪│ ╪º╪╡┘ä ┘ê╪º┘à (Principal Moratorium) ╪¿╪▒╪º█î ┘à╪┤╪¬╪▒█î ┘ü╪╣╪º┘ä ╪┤╪»┘ç ╪¿╪º╪┤╪»╪î ╪»╪▒ ╪╖┘ê┘ä ╪»┘ê╪▒┘ç ╪¬┘å┘ü╪│ ╪º┘é╪│╪º╪╖ ┘ü┘é╪╖ ╪┤╪º┘à┘ä ╪¿┘ç╪▒┘ç ╪¬╪│┘ç█î┘ä╪º╪¬ ╪¿┘ê╪»┘ç ┘ê ╪¿╪º╪▓┘╛╪▒╪»╪º╪«╪¬ ╪º╪╡┘ä ┘ê╪º┘à ╪¿┘ç ╪¬╪╣┘ê█î┘é ┘à█îΓÇî╪º┘ü╪¬╪». ╪¿╪º ┘╛╪º█î╪º┘å ╪»┘ê╪▒┘ç ╪¬┘å┘ü╪│╪î ╪º╪╡┘ä ┘à╪¿┘ä╪║ ╪¿╪º┘é█îΓÇî┘à╪º┘å╪»┘ç ╪¿╪▒ ╪▒┘ê█î ╪º┘é╪│╪º╪╖ ╪ó╪¬█î ╪│╪▒╪┤┌⌐┘å ┘à█îΓÇî┌»╪▒╪»╪». ╪╡╪¡╪¬ ╪º█î┘å ┘à┘å╪╖┘é ╪¿╪º ┘à╪¬╪»┘ç╪º█î ┘à╪¡╪º╪│╪¿┘ç ╪¼╪»┘ê┘ä ╪¿╪º╪▓┘╛╪▒╪»╪º╪«╪¬ ╪»╪▒ ┌⌐╪» ╪¼╪º┘ê╪º ╪¬╪╖╪¿█î┘é ╪»╪º╪»┘ç ╪┤╪»┘ç ╪º╪│╪¬.
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If the configured principal moratorium period equals or exceeds the total number of repayment installments, then the Fineract Loan Engine shall reject the loan creation with error code "error.msg.loan.moratorium.period.cannot.exceed.or.equal.number.of.installments".`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à┘å╪¿╪╣ ┘à╪│╪¬┘å╪»╪º╪¬:** `docs/crawled/pages/user-manual/loan-products.md` (╪¿╪«╪┤ Grace on Principal Payment)
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│ ┘à╪¬┘å╪º╪╕╪▒:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/LoanRepaymentScheduleInstallment.java`
+  * **┘à╪¬╪» ╪º╪¼╪▒╪º█î█î:** `#isAdditional()`, `#updatePrincipalAndInterestAmount()`
+  * **┌⌐╪»┘ç╪º█î ╪«╪╖╪º ┘ê ╪º┘å┘ê╪¬█î╪┤┘åΓÇî┘ç╪º:** `error.msg.loan.moratorium.period.cannot.exceed.or.equal.number.of.installments`
+  * **┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ┘ê ╪º┘å╪¬█î╪¬█îΓÇî┘ç╪º:** ╪¼╪»┘ê┘ä `m_loan`, ╪¼╪»┘ê┘ä `m_loan_repayment_schedule`
+```
diff --git a/.skills/fineract-gradle-parser/SKILL.md b/.skills/fineract-gradle-parser/SKILL.md
new file mode 100644
index 0000000..ccf4465
--- /dev/null
+++ b/.skills/fineract-gradle-parser/SKILL.md
@@ -0,0 +1,180 @@
+---
+name: fineract-gradle-parser
+description: Extracts architectural capability boundaries, modular dependencies, and third-party subsystem integration requirements from Gradle build files across Apache Fineract into standardized EARS requirements. Activate when inspecting build.gradle, settings.gradle, or gradle.properties files in apache-fineract-src-1.15.0.
+---
+
+# Fineract Gradle Build Parser to EARS Requirements
+
+## Overview
+This skill instructs agents on parsing root and multi-project Gradle build files within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to reverse-engineer system architecture boundaries, modular dependencies, technology stack constraints, and integration capabilities into standardized EARS requirements.
+
+## Target File Scope & Locations
+This skill applies to all Gradle build and property files:
+* **Root Build Settings:**
+  * `apache-fineract-src-1.15.0/settings.gradle` (all subproject module declarations)
+  * `apache-fineract-src-1.15.0/build.gradle` (root build script, plugins, subprojects configuration)
+  * `apache-fineract-src-1.15.0/dependencies.gradle` (dependency management versions, shared libraries)
+  * `apache-fineract-src-1.15.0/gradle.properties` (JVM configuration, flag toggles)
+* **Submodule Build Files:**
+  * `apache-fineract-src-1.15.0/**/build.gradle` (e.g. `fineract-provider/build.gradle`, `fineract-core/build.gradle`, `fineract-loan/build.gradle`, `fineract-accounting/build.gradle`, `fineract-cob/build.gradle`)
+* **Build Tools & Conventions:**
+  * `apache-fineract-src-1.15.0/buildSrc/src/main/groovy/**`
+
+---
+
+## Architectural Semantics of Gradle Declarations
+
+1. **Subproject Declarations (`settings.gradle`):**
+   * Every `include 'module-name'` statement establishes an isolated architectural domain or infrastructural subsystem boundary.
+2. **Inter-Module Dependencies (`project(':module-name')`):**
+   * Defines coupling, domain flow, and modular hierarchy (e.g., `fineract-loan` depends on `fineract-core`, but `fineract-core` never depends on `fineract-loan`).
+3. **Third-Party Integrations (`implementation 'group:artifact:version'`):**
+   * Pinpoints third-party enterprise services:
+     * `spring-boot-starter-data-jpa` $\to$ Relational database persistence.
+     * `org.apache.activemq` / `spring-kafka` $\to$ Event streaming and messaging broker.
+     * `org.ehcache` $\to$ In-memory distributed and local caching.
+     * `org.quartz-scheduler` $\to$ Background job orchestration and COB scheduling.
+     * `com.lmax:disruptor` $\to$ High-throughput ring-buffer asynchronous command processing.
+     * `org.liquibase:liquibase-core` $\to$ Database schema change management.
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **Gradle Construct:** Universal runtime platform requirements, baseline compiler targets, UTF-8 source encodings.
+* **Extraction Pattern:**
+  ```groovy
+  java {
+      toolchain {
+          languageVersion = JavaLanguageVersion.of(17)
+      }
+  }
+  ```
+  * Map to: `The Fineract Platform shall execute on a Java 17 runtime environment.`
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **Gradle Construct:** Profile-based execution (e.g., test execution vs production build), daemon execution flags.
+* **Extraction Pattern:**
+  ```groovy
+  tasks.withType(Test) {
+      systemProperty 'spring.profiles.active', 'test'
+  }
+  ```
+  * Map to: `While executing under the automated test profile, the Fineract Platform shall utilize the isolated in-memory or ephemeral tenant test database.`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **Gradle Construct:** Lifecycle tasks, compilation events, container image packaging.
+* **Extraction Pattern:**
+  ```groovy
+  tasks.named('bootJar') {
+      archiveClassifier = 'boot'
+  }
+  ```
+  * Map to: `When the executable packaging task is invoked, the Fineract Build Subsystem shall produce a self-contained Spring Boot executable JAR including all embedded web server components.`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **Gradle Construct:** Optional subprojects, conditional plugins, or modular feature packs (e.g., `fineract-investor`, `oauth2-tests`, `fineract-mix`).
+* **Extraction Pattern:**
+  ```groovy
+  if (project.hasProperty('enableKafka')) {
+      implementation 'org.springframework.kafka:spring-kafka'
+  }
+  ```
+  * Map to: `Where Apache Kafka messaging is included, the Fineract Event Engine shall publish domain events to designated Kafka topic brokers.`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **Gradle Construct:** Dependency resolution conflicts, missing JDK requirements, checkstyle/lint violations.
+* **Extraction Pattern:**
+  ```groovy
+  configurations.all {
+      resolutionStrategy.failOnVersionConflict()
+  }
+  ```
+  * Map to: `If a transitively resolved library exhibits a version conflict, then the Fineract Build Engine shall terminate the build immediately with an explicit version resolution failure.`
+
+### 6. Complex Requirements
+* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
+* **Gradle Construct:** Asynchronous command processing combined with external broker libraries and queue states.
+* **Extraction Pattern:**
+  ```groovy
+  project(':fineract-command-disruptor') {
+      dependencies {
+          implementation project(':fineract-command')
+          implementation 'com.lmax:disruptor'
+      }
+  }
+  ```
+  * Map to: `Where the disruptor-based command subsystem is enabled, when a write command is dispatched, the Fineract Command Engine shall process the command payload asynchronously using an in-memory ring buffer.`
+
+---
+
+## Code Extraction Heuristics & Regex Patterns
+
+| Target Element | Regex / Search Pattern | Semantics Extracted |
+| :--- | :--- | :--- |
+| **Subproject List** | `include\s+['"]([^'"]+)['"]` | System module inventory and isolation boundaries |
+| **Subproject Coupling** | `project\s*\(\s*['"](:[^'"]+)['"]\s*\)` | Inter-module capability dependency |
+| **External Dependency** | `(implementation\|api)\s+['"]([^:]+):([^:]+):?([^'"]*)['"]` | Third-party framework capability integration |
+| **Java Toolchain** | `JavaLanguageVersion\.of\s*\(\s*([0-9]+)\s*\)` | Core platform runtime specification |
+| **Plugin Declaration** | `id\s+['"]([^'"]+)['"]` | Platform build extensions (Docker, Spring Boot, Spotless) |
+| **Compiler Args** | `options\.compilerArgs\s*\+=\s*\[([^\]]+)\]` | JVM memory parameters, bytecode constraints |
+
+---
+
+## Step-by-Step Gradle Parsing Workflow
+
+1. **Scan `settings.gradle`:**
+   * Extract all declared submodules. Map them into high-level domains (Core, Loan, Savings, Accounting, COB, Messaging, Security).
+2. **Analyze Root `build.gradle` and `dependencies.gradle`:**
+   * Identify core frameworks (Spring Boot, OpenJPA, Liquibase/Flyway, Jackson, Apache Camel, etc.).
+   * Document baseline ubiquitous platform constraints (Java 17, UTF-8, strict checkstyle).
+3. **Inspect Submodule `build.gradle` Files:**
+   * Trace incoming and outgoing dependencies for each module to identify architectural layers (e.g. `fineract-progressive-loan` $\to$ `fineract-loan` $\to$ `fineract-core`).
+4. **Formulate Bilingual EARS Card:**
+   * Document architectural boundaries and non-functional requirements conforming to the standard template.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ┘à┘ü┘ç┘ê┘à ┘à╪╣┘à╪º╪▒█î╪î ┘à╪▒╪▓┘ç╪º█î ┘à╪º┌ÿ┘ê┘ä╪º╪▒ ┘ê ┘å┘é╪┤ ┌⌐╪¬╪º╪¿╪«╪º┘å┘çΓÇî┘ç╪º ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│:** `apache-fineract-src-1.15.0/.../build.gradle`
+  * **┘╛█î┌⌐╪▒╪¿┘å╪»█î ┘ê ┌⌐╪¬╪º╪¿╪«╪º┘å┘ç ┘ê╪º╪¿╪│╪¬┘ç:** `implementation project(':...')`, `group:artifact:version`
+  * **╪º┘ç╪»╪º┘ü ┘à╪╣┘à╪º╪▒█î:** ╪¼╪»╪º╪│╪º╪▓█î ┘à╪º┌ÿ┘ê┘ä╪º╪▒ ┘ê ┌⌐┘å╪¬╪▒┘ä ┘ê╪º╪¿╪│╪¬┌»█îΓÇî┘ç╪º
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-ARCH-ASYNC-CMD-001: ┘╛╪▒╪»╪º╪▓╪┤ ┘å╪º┘ç┘à┌»╪º┘à ╪»╪│╪¬┘ê╪▒╪º╪¬ ┘à╪º┘ä█î ╪º╪▓ ╪╖╪▒█î┘é ╪¿╪º┘ü╪▒ ╪¡┘ä┘é┘ê█î ╪»█î╪│╪▒╪º┘╛╪¬┘ê╪▒
+* **╪º┘ä┌»┘ê█î EARS:** Complex
+* **EARS Statement:**
+  > Where the disruptor command processing module ("fineract-command-disruptor") is included, when a high-throughput write command is submitted, the Fineract Command Subsystem shall enqueue and execute the command payload asynchronously using an in-memory ring buffer without blocking the calling HTTP servlet thread.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ┘à╪º┌ÿ┘ê┘ä ┘╛╪▒╪»╪º╪▓╪┤ ╪»╪│╪¬┘ê╪▒╪º╪¬ ╪¿┘ç ╪╡┘ê╪▒╪¬ ┘å╪º┘ç┘à┌»╪º┘à (`fineract-command-disruptor`) ╪º┘à┌⌐╪º┘å ┘╛╪▒╪»╪º╪▓╪┤ ╪¿╪º ╪¬┘ê╪º┘å ╪╣┘à┘ä█î╪º╪¬█î ╪¿╪│█î╪º╪▒ ╪¿╪º┘ä╪º ╪▒╪º ┘ü╪▒╪º┘ç┘à ┘à█îΓÇî╪│╪º╪▓╪». ╪»╪▒ ╪º█î┘å ┘à╪º┌ÿ┘ê┘ä ╪¿╪º ╪º╪│╪¬┘ü╪º╪»┘ç ╪º╪▓ ┌⌐╪¬╪º╪¿╪«╪º┘å┘ç LMAX Disruptor╪î ╪▒┘ê█î╪»╪º╪»┘ç╪º ┘ê ╪»╪│╪¬┘ê╪▒╪º╪¬ ╪½╪¿╪¬ ╪¬╪▒╪º┌⌐┘å╪┤ΓÇî┘ç╪º█î ╪¿╪º┘å┌⌐█î ╪»╪▒ █î┌⌐ ╪¿╪º┘ü╪▒ ╪¡┘ä┘é┘ê█î ╪¡╪º┘ü╪╕┘çΓÇî┘à╪¡┘ê╪▒ ╪╡┘üΓÇî╪¿┘å╪»█î ╪┤╪»┘ç ┘ê ╪¬╪▒╪»┘ç╪º█î ╪º╪«╪¬╪╡╪º╪╡█î ╪│█î╪│╪¬┘à ╪¿╪»┘ê┘å ┘à╪╣╪╖┘ä ┘å┌»╪º┘ç ╪»╪º╪┤╪¬┘å ╪»╪▒╪«┘ê╪º╪│╪¬ ┘ê╪¿ ┌⌐┘ä╪º█î┘å╪¬╪î ╪»╪│╪¬┘ê╪▒ ╪▒╪º ╪º╪¼╪▒╪º ┘ê ╪░╪«█î╪▒┘ç ┘à█îΓÇî┌⌐┘å┘å╪».
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If the disruptor ring buffer reaches maximum capacity and backpressure timeout expires, then the Fineract Command Subsystem shall reject incoming write commands and return an HTTP 503 Service Unavailable response.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│:** `apache-fineract-src-1.15.0/fineract-command-disruptor/build.gradle`
+  * **┘╛█î┌⌐╪▒╪¿┘å╪»█î ┘ê ┌⌐╪¬╪º╪¿╪«╪º┘å┘ç ┘ê╪º╪¿╪│╪¬┘ç:** `implementation project(':fineract-command')`, `implementation 'com.lmax:disruptor:3.4.4'`
+  * **╪º┘ç╪»╪º┘ü ┘à╪╣┘à╪º╪▒█î:** ╪¬┘ü┌⌐█î┌⌐ ╪»╪│╪¬┘ê╪▒╪º╪¬ CQRS ┘ê ┘à┘é█î╪º╪│ΓÇî┘╛╪░█î╪▒█î ╪╣┘à┘ä█î╪º╪¬ ╪¿╪º ╪¬┘ê╪º┘å ┘╛╪▒╪»╪º╪▓╪┤█î ╪¿╪º┘ä╪º
+```
diff --git a/.skills/fineract-java-parser/SKILL.md b/.skills/fineract-java-parser/SKILL.md
new file mode 100644
index 0000000..89b1850
--- /dev/null
+++ b/.skills/fineract-java-parser/SKILL.md
@@ -0,0 +1,185 @@
+---
+name: fineract-java-parser
+description: Extracts standardized EARS requirements from Java source files across Apache Fineract, analyzing JAX-RS/Spring MVC controllers, CQRS command handlers, domain entities, state machines, and data validation rules into bilingual requirements. Activate when inspecting .java files in apache-fineract-src-1.15.0.
+---
+
+# Fineract Java Source Code Parser to EARS Requirements
+
+## Overview
+This skill guides agents in parsing Java source files in the Apache Fineract 1.15.0 codebase (`apache-fineract-src-1.15.0/`) to systematically extract, structure, and document business logic, financial algorithms, access control, and state transitions as standardized EARS (Easy Approach to Requirements Syntax) requirements.
+
+## Target File Scope & Locations
+This skill applies to all Java files (`*.java`) located under:
+* `apache-fineract-src-1.15.0/**/src/main/java/**/*.java`
+* Key submodules:
+  * `fineract-provider/src/main/java/org/apache/fineract/**`
+  * `fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/**`
+  * `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/**`
+  * `fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/**`
+  * `fineract-accounting/src/main/java/org/apache/fineract/accounting/**`
+  * `fineract-charge/src/main/java/org/apache/fineract/portfolio/charge/**`
+  * `fineract-cob/src/main/java/org/apache/fineract/cob/**`
+
+### Key Java Architectural Roles
+1. **API Resources (Controllers):** `*ApiResource.java` (JAX-RS annotations: `@Path`, `@POST`, `@GET`, `@PUT`, `@DELETE`, `@PreAuthorize`)
+2. **Command Handlers:** `*CommandHandler.java` (CQRS command processing: `CommandHandler`, `CommandWrapper`, `NewCommandSourceHandler`)
+3. **Write Platform Services:** `*WritePlatformServiceImpl.java` (Transactional business logic, calculations, state mutations)
+4. **Read Platform Services:** `*ReadPlatformServiceImpl.java` (Reporting, search, query projection)
+5. **Domain Entities:** `@Entity` classes (JPA state models, invariants, lifecycle hooks, e.g. `Loan.java`, `SavingsAccount.java`)
+6. **State Enums:** Status enums with transitions (e.g. `LoanStatus.java`, `SavingsAccountStatus.java`)
+7. **Validators:** `*DataValidator.java`, `DataValidatorBuilder` (Parameter constraints, type checks, business rule preconditions)
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **Java Source Construct:** Universal invariants, auditing timestamps (`@CreatedDate`, `@LastModifiedDate`), global tenant isolation, immutable transaction IDs.
+* **Extraction Pattern:**
+  * Base entity auditing: `AbstractAuditableCustom` / `created_date`, `createdby_id`.
+  * OpenJPA optimistic locking: `@Version Long version`.
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **Java Source Construct:** Guard clauses checking domain entity status enum or boolean flags before proceeding.
+* **Extraction Pattern:**
+  ```java
+  if (!this.loanStatus.isActive()) {
+      throw new LoanNotFoundException(this.getId());
+  }
+  ```
+  * Map `this.loanStatus.isApproved()` $\to$ `While the loan account is in "APPROVED" state...`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **Java Source Construct:** JAX-RS REST endpoints, incoming HTTP requests, API commands, message events.
+* **Extraction Pattern:**
+  ```java
+  @POST
+  @Path("{loanId}")
+  @Consumes({MediaType.APPLICATION_JSON})
+  @Produces({MediaType.APPLICATION_JSON})
+  public String stateTransitions(@PathParam("loanId") final Long loanId, @QueryParam("command") final String commandParam, ...)
+  ```
+  * Map `POST /v1/loans/{loanId}?command=disburse` $\to$ `When a disburse command is received for a specified loan...`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **Java Source Construct:** Feature toggle flags in Product settings, conditional strategy injections, optional configurations (e.g., `isMultiDisburseAllowed`, `isInterestRecalculationEnabled`, `isTopup`).
+* **Extraction Pattern:**
+  ```java
+  if (loanProduct.isMultiDisburseLoan()) {
+      // multi disbursement logic
+  }
+  ```
+  * Map to `Where multi-disbursement is enabled on the loan product, the Fineract Loan Engine shall...`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **Java Source Construct:** Validation failure checks, `DataValidatorBuilder`, exception throwing (`PlatformApiDataValidationException`, `LoanException`).
+* **Extraction Pattern:**
+  ```java
+  baseDataValidator.reset().parameter("principal").value(principal).notNull().positiveAmount();
+  if (disbursementAmount.compareTo(approvedPrincipal) > 0) {
+      throw new LoanException("error.msg.loan.amount.exceeds.approved", ...);
+  }
+  ```
+  * Map to `If the requested disbursement amount exceeds the approved principal, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.amount.exceeds.approved".`
+
+### 6. Complex Requirements
+* **Template:** `While <state>, when <trigger>, the <system name> shall <system response>` OR `Where <feature>, if <unwanted condition>, then the <system name> shall <system response>`
+* **Java Source Construct:** Method with status guard, event trigger, and optional feature check combined.
+* **Extraction Pattern:**
+  ```java
+  if (loan.getStatus().isApproved()) {
+      if (command.isDisburse()) {
+          loan.disburse(disbursementDate, amount, ...);
+      }
+  }
+  ```
+
+---
+
+## Code Extraction Heuristics & Regex Patterns
+
+When analyzing Java files, use the following regex patterns to locate requirement candidates:
+
+| Target Element | Regex / Search Pattern | Semantics Extracted |
+| :--- | :--- | :--- |
+| **REST Endpoint** | `@Path\s*\(\s*["']([^"']+)["']\s*\)` | API URL trigger path |
+| **HTTP Verb** | `@(POST\|GET\|PUT\|DELETE)` | Event action trigger |
+| **Security Role** | `@PreAuthorize\s*\(\s*["']hasAuthority\('([^']+)'\)["']\s*\)` | Precondition authorization clause |
+| **Command Router** | `commands\.contains\s*\(\s*["']([^"']+)["']\s*\)` | Action command trigger parameter |
+| **Validation Error** | `baseDataValidator\.reset\(\)\.parameter\(["']([^"']+)["']\)` | Input parameter validation invariants |
+| **Business Exception** | `throw\s+new\s+([A-Za-z0-9_]+Exception)\s*\(\s*["']([^"']+)["']` | Unwanted behavior error codes |
+| **State Inspection** | `if\s*\(!?this\.[a-zA-Z0-9_]+\.is([A-Za-z]+)\(\)\)` | State-driven precondition |
+| **Domain State Enum** | `public\s+enum\s+([A-Za-z0-9_]+Status)\s*\{` | Account lifecycle state space |
+| **GL Accounting Hook** | `journalEntryWritePlatformService\.createJournalEntriesForLoan` | Financial transaction ledger invariant |
+
+---
+
+## Step-by-Step Java Parsing Workflow
+
+1. **Locate Resource & Command Handler:**
+   * Find `@Path` in `*ApiResource.java` to define the API endpoint and HTTP method.
+   * Identify the corresponding `@PreAuthorize` role to formulate the authorization precondition: `While the user possesses the "<PERMISSION>" authority...`.
+2. **Inspect WritePlatformServiceImpl:**
+   * Trace execution from API resource into the service implementation.
+   * Identify status check preconditions (`loan.isSubmittedAndPendingApproval()`).
+   * Identify calculation methods (e.g. `calculateRepaymentSchedule`, `calculateInterest`).
+3. **Inspect Validator:**
+   * Open the associated `*DataValidator.java`.
+   * Extract all `.failWithCode("...")` and `DataValidatorBuilder` checks into **If-Then** Unwanted Behavior clauses.
+4. **Inspect Domain Entity:**
+   * Open `@Entity` class to locate state transitions (e.g. `loan.status = LoanStatus.ACTIVE.getValue()`).
+   * Verify table name (`@Table(name = "m_loan")`) and database columns.
+5. **Formulate Bilingual EARS Card:**
+   * Assemble the requirement card conforming to the standard template.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+Every extracted requirement must follow this structure:
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ╪│┘å╪º╪▒█î┘ê█î ╪¿╪º┘å┌⌐█î╪î ┘à┘å╪╖┘é ╪¿█î╪▓┘å╪│ ┘ê ╪º┘ç╪»╪º┘ü ┘à╪º┘ä█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall reject the request and return error code "<CODE_1>".`
+  * `If <error condition 2>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│:** `apache-fineract-src-1.15.0/.../ClassName.java`
+  * **┘à╪¬╪» ╪º╪¼╪▒╪º█î█î:** `#methodName()`
+  * **┌⌐╪»┘ç╪º█î ╪«╪╖╪º ┘ê ╪º┘å┘ê╪¬█î╪┤┘åΓÇî┘ç╪º:** `@PreAuthorize(...)`, `error.msg....`
+  * **┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ┘ê ╪º┘å╪¬█î╪¬█îΓÇî┘ç╪º:** ╪¼╪»╪º┘ê┘ä `m_...`, ╪º┘å╪¬█î╪¬█î `@Entity ...`
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-LOAN-DISBURSE-001: ┘╛╪▒╪»╪º╪«╪¬ ┘ê ╪º┘å╪¬┘é╪º┘ä ┘ê╪¼┘ç ┘ê╪º┘à ╪¿┘ç ╪¡╪│╪º╪¿ ┘à╪┤╪¬╪▒█î
+* **╪º┘ä┌»┘ê█î EARS:** Complex
+* **EARS Statement:**
+  > While the loan account is in "APPROVED" state, when a disbursement request is submitted with a valid disbursement date, the Fineract Loan Engine shall disburse the approved principal amount, transition the loan status to "ACTIVE", and generate the initial repayment schedule.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ┘ç┘å┌»╪º┘à█î ┌⌐┘ç █î┌⌐ ┘╛╪▒┘ê┘å╪»┘ç ╪¬╪│┘ç█î┘ä╪º╪¬ ╪¿┘ç ┘ê╪╢╪╣█î╪¬ ┘à╪╡┘ê╪¿ (APPROVED) ┘à█îΓÇî╪▒╪│╪»╪î ┌⌐╪º╪▒╪¿╪▒ ┘à╪¼╪º╪▓ ╪┤╪╣╪¿┘ç ┘à█îΓÇî╪¬┘ê╪º┘å╪» ┘à╪¿┘ä╪║ ╪¬╪│┘ç█î┘ä╪º╪¬ ╪▒╪º ╪¿┘ç ┘à╪┤╪¬╪▒█î ┘╛╪▒╪»╪º╪«╪¬ ┌⌐┘å╪». ╪│█î╪│╪¬┘à ┘ü╪º█î┘å╪▒╪º┌⌐╪¬ ┘à┘ê╪╕┘ü ╪º╪│╪¬ ┘╛╪│ ╪º╪▓ ╪¿╪▒╪▒╪│█î ┘ê╪╢╪╣█î╪¬ ╪¡╪│╪º╪¿╪î ╪¬╪º╪▒█î╪« ┘╛╪▒╪»╪º╪«╪¬ ┘ê ┘à╪¿┘ä╪║╪î ┘ê╪╢╪╣█î╪¬ ┘╛╪▒┘ê┘å╪»┘ç ╪▒╪º ╪¿┘ç ┘ü╪╣╪º┘ä (ACTIVE) ╪¬╪║█î█î╪▒ ╪»┘ç╪»╪î ╪º┘é╪│╪º╪╖ ╪¿╪º╪▓┘╛╪▒╪»╪º╪«╪¬ ╪▒╪º ┘å┘ç╪º█î█î ┘å┘à┘ê╪»┘ç ┘ê ╪│┘å╪» ╪¡╪│╪º╪¿╪»╪º╪▒█î ┘à╪▒╪¬╪¿╪╖ ╪¿╪º ┘╛╪▒╪»╪º╪«╪¬ ┘ê╪¼┘ç ╪º╪▓ ╪╡┘å╪»┘ê┘é/╪¿╪º┘å┌⌐ ╪¿┘ç ╪¡╪│╪º╪¿ ╪¬╪│┘ç█î┘ä╪º╪¬ ╪▒╪º ╪¿┘ç ╪╡┘ê╪▒╪¬ ╪«┘ê╪»┌⌐╪º╪▒ ╪»╪▒ ╪»┘ü╪¬╪▒ ┌⌐┘ä ╪╡╪º╪»╪▒ ┘å┘à╪º█î╪».
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If the loan account is not in "APPROVED" state at the time of disbursement, then the Fineract Loan Engine shall reject the disbursement command and return error code "error.msg.loan.not.approved".`
+  * `If the disbursement date is prior to the loan approval date, then the Fineract Loan Engine shall reject the command and return error code "error.msg.loan.disbursement.date.cannot.be.before.approved.date".`
+  * `If the disbursement amount exceeds the approved principal balance, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.amount.exceeds.approved".`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ┌⌐┘ä╪º╪│ ╪│┘ê╪▒╪│:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
+  * **┘à╪¬╪» ╪º╪¼╪▒╪º█î█î:** `#disburseLoan(Long loanId, JsonCommand command)`
+  * **┌⌐╪»┘ç╪º█î ╪«╪╖╪º ┘ê ╪º┘å┘ê╪¬█î╪┤┘åΓÇî┘ç╪º:** `@PreAuthorize("hasAuthority('DISBURSE_LOAN')")`, `error.msg.loan.not.approved`, `error.msg.loan.disbursement.date.cannot.be.before.approved.date`
+  * **┘╛╪º█î┌»╪º┘ç ╪»╪º╪»┘ç ┘ê ╪º┘å╪¬█î╪¬█îΓÇî┘ç╪º:** ╪¼╪»┘ê┘ä `m_loan`, ╪¼╪»┘ê┘ä `m_loan_transaction`, ╪º┘å╪¬█î╪¬█î `org.apache.fineract.portfolio.loanaccount.domain.Loan`
+```
diff --git a/.skills/fineract-xml-parser/SKILL.md b/.skills/fineract-xml-parser/SKILL.md
new file mode 100644
index 0000000..50de736
--- /dev/null
+++ b/.skills/fineract-xml-parser/SKILL.md
@@ -0,0 +1,174 @@
+---
+name: fineract-xml-parser
+description: Extracts non-functional requirements, audit policies, caching strategies, and Spring bean definitions from XML configuration files across Apache Fineract into standardized EARS requirements. Activate when inspecting .xml configuration files like logback.xml, ehcache.xml, or persistence.xml in apache-fineract-src-1.15.0.
+---
+
+# Fineract XML Configuration Parser to EARS Requirements
+
+## Overview
+This skill guides agents in parsing XML configuration files within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to extract non-functional requirements (NFRs), logging and regulatory audit policies, distributed and local caching boundaries, and JPA persistence declarations into standardized EARS requirements.
+
+## Target File Scope & Locations
+This skill applies to all XML configuration files across the codebase:
+* **Logging & Audit Specifications:**
+  * `apache-fineract-src-1.15.0/**/src/main/resources/logback.xml`
+  * `apache-fineract-src-1.15.0/**/src/main/resources/logback-spring.xml`
+* **In-Memory & Distributed Caching:**
+  * `apache-fineract-src-1.15.0/**/src/main/resources/ehcache.xml`
+* **JPA Persistence Unit Definitions:**
+  * `apache-fineract-src-1.15.0/**/src/main/resources/META-INF/persistence.xml`
+* **Spring Application Context Bean Configurations:**
+  * `apache-fineract-src-1.15.0/**/src/main/resources/**/*.xml`
+* **Liquibase Schema Changeset XML Files:**
+  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/**/*.xml`
+
+---
+
+## Architectural Semantics of XML Files
+
+1. **`logback.xml` / `logback-spring.xml`:**
+   * Defines MDC (Mapped Diagnostic Context) capturing `tenantId`, `userId`, `correlationId`.
+   * Enforces log retention, rolling file policies (time/size triggers), and log sanitization (masking sensitive financial data like passwords and account balances).
+2. **`ehcache.xml`:**
+   * Declares cache regions for frequently accessed, infrequently mutated entities (e.g. `loanProducts`, `savingsProducts`, `offices`, `users`).
+   * Configures `maxEntriesLocalHeap`, `timeToLiveSeconds`, `timeToIdleSeconds`, and memory eviction policies (`LRU`, `LFU`, `FIFO`).
+3. **`persistence.xml`:**
+   * Declares OpenJPA / Hibernate persistence units, caching L2 provider settings, and transaction types.
+
+---
+
+## EARS Mapping Rules & Syntactic Constraints
+
+All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.
+
+### 1. Ubiquitous Requirements
+* **Template:** `The <system name> shall <system response>`
+* **XML Construct:** Universal logging formats, mandatory MDC fields in appender pattern.
+* **Extraction Pattern:**
+  ```xml
+  <encoder>
+      <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level [tenant:%X{tenantId}] [user:%X{userId}] %logger{36} - %msg%n</pattern>
+  </encoder>
+  ```
+  * Map to: `The Fineract Logging Subsystem shall inject the active tenant identifier, authenticated user ID, and timestamp into the Mapped Diagnostic Context (MDC) for every emitted log entry.`
+
+### 2. State-Driven Requirements
+* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
+* **XML Construct:** Cache saturation and eviction under heap constraints.
+* **Extraction Pattern:**
+  ```xml
+  <cache name="loanProducts"
+         maxEntriesLocalHeap="1000"
+         memoryStoreEvictionPolicy="LRU"
+         timeToLiveSeconds="3600"/>
+  ```
+  * Map to: `While the in-memory cache for "loanProducts" reaches the threshold of 1,000 entries, the Fineract Caching Layer shall evict the Least Recently Used (LRU) records to maintain memory bounds.`
+
+### 3. Event-Driven Requirements
+* **Template:** `When <trigger>, the <system name> shall <system response>`
+* **XML Construct:** Log file rolling events based on time or file size limits.
+* **Extraction Pattern:**
+  ```xml
+  <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
+      <fileNamePattern>fineract-%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
+      <maxFileSize>100MB</maxFileSize>
+      <maxHistory>30</maxHistory>
+  </rollingPolicy>
+  ```
+  * Map to: `When an active log file reaches 100 megabytes in size, the Fineract Logging Subsystem shall compress the log into a gzip archive and initialize a new active log file.`
+
+### 4. Optional Feature Requirements
+* **Template:** `Where <feature is included>, the <system name> shall <system response>`
+* **XML Construct:** Asynchronous appender or secondary cache clustering.
+* **Extraction Pattern:**
+  ```xml
+  <appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
+      <queueSize>512</queueSize>
+      <appender-ref ref="FILE" />
+  </appender>
+  ```
+  * Map to: `Where asynchronous logging is configured, the Fineract Logging Subsystem shall buffer log records in a non-blocking queue of capacity 512 entries.`
+
+### 5. Unwanted Behavior Requirements
+* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
+* **XML Construct:** Disk full or queue saturation behavior in logging appenders.
+* **Extraction Pattern:**
+  ```xml
+  <neverBlock>true</neverBlock>
+  <discardingThreshold>20</discardingThreshold>
+  ```
+  * Map to: `If the asynchronous log queue reaches 80% capacity (discardingThreshold 20%), then the Fineract Logging Subsystem shall discard TRACE and DEBUG level events to preserve system responsiveness.`
+
+### 6. Complex Requirements
+* **Template:** `While <state>, when <trigger>, the <system name> shall <system response>`
+* **XML Construct:** Caching eviction combined with entity mutation events.
+* **Extraction Pattern:**
+  * Map to: `While an entity is cached in the "offices" cache region, when an update or delete operation completes on that office record, the Fineract Caching Layer shall invalidate the corresponding cache key across all application nodes.`
+
+---
+
+## Code Extraction Heuristics & XPath Patterns
+
+| Target Element | XPath / Regex Pattern | Semantics Extracted |
+| :--- | :--- | :--- |
+| **Appender Pattern** | `//appender/encoder/pattern` | MDC fields, audit logging format |
+| **Rolling Policy** | `//rollingPolicy/maxFileSize` | Log file size trigger and archive policy |
+| **Retention Policy** | `//rollingPolicy/maxHistory` | Regulatory compliance audit log retention days |
+| **Cache Region** | `//cache[@name]` | Entity caching domains and scopes |
+| **Cache Bounds** | `//cache/@maxEntriesLocalHeap` | Memory saturation and resource guard |
+| **Cache Expiry** | `//cache/@timeToLiveSeconds` | Data freshness and stale read prevention |
+| **Eviction Policy** | `//cache/@memoryStoreEvictionPolicy`| Cache eviction algorithm (LRU, LFU, FIFO) |
+
+---
+
+## Step-by-Step XML Parsing Workflow
+
+1. **Parse `logback.xml`:**
+   * Extract logging appenders (Console, RollingFile, Async).
+   * Note regex pattern for MDC variables (`tenantId`, `userId`).
+   * Record archival limits (`maxFileSize`, `maxHistory`).
+2. **Parse `ehcache.xml`:**
+   * Catalog all cache regions (`users`, `offices`, `loanProducts`).
+   * Extract expiration and eviction policies for each region.
+3. **Parse `persistence.xml`:**
+   * Identify JPA provider properties and caching configuration.
+4. **Formulate Bilingual EARS Card:**
+   * Create the requirement card according to the standard template.
+
+---
+
+## Bilingual Output Requirement Card Template
+
+```markdown
+### REQ-[MODULE]-[ACTION]-[NUM]: [╪╣┘å┘ê╪º┘å ┌⌐┘ê╪¬╪º┘ç ╪¬┘ê╪╡█î┘ü█î ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î]
+* **╪º┘ä┌»┘ê█î EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
+* **EARS Statement:**
+  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  [╪¬┘ê╪╢█î╪¡ ┌⌐╪º┘à┘ä ┘à┘ü┘ç┘ê┘à ╪╣┘à┘ä┌⌐╪▒╪»█î╪î ┘ä╪º┌»█î┘å┌»╪î ┘à╪º┘å█î╪¬┘ê╪▒█î┘å┌» █î╪º ┘à╪»█î╪▒█î╪¬ ╪¡╪º┘ü╪╕┘ç ┌⌐╪┤ ╪¿┘ç ╪▓╪¿╪º┘å ┘ü╪º╪▒╪│█î ╪▒┘ê╪º┘å]
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If <error condition 1>, then the <system name> shall <error response>.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ╪¬┌» XML:** `apache-fineract-src-1.15.0/.../<filename>.xml`
+  * **╪¬┌» ┘ê ╪«╪╡█î╪╡┘ç ┘à┘ê╪▒╪» ╪¬╪¡┘ä█î┘ä:** `<cache name="...">`, `<rollingPolicy>`
+  * **╪┤╪º╪«╪╡ΓÇî┘ç╪º█î ┌⌐┘ä█î╪»█î:** ╪╕╪▒┘ü█î╪¬╪î ╪│█î╪º╪│╪¬ ╪¡╪░┘ü╪î ╪»┘ê╪▒┘ç ┘à╪º┘å╪»┌»╪º╪▒█î
+```
+
+---
+
+## Concrete Example
+
+```markdown
+### REQ-NFR-CACHE-LOAN-PROD-001: ┘à╪»█î╪▒█î╪¬ ┌⌐╪┤ ╪¡╪º┘ü╪╕┘çΓÇî┘à╪¡┘ê╪▒ ╪º╪╖┘ä╪º╪╣╪º╪¬ ┘à╪¡╪╡┘ê┘ä╪º╪¬ ╪¬╪│┘ç█î┘ä╪º╪¬
+* **╪º┘ä┌»┘ê█î EARS:** State-Driven
+* **EARS Statement:**
+  > While the in-memory cache for "loanProducts" reaches the maximum limit of 1,000 entries, the Fineract Caching Layer shall evict the Least Recently Used (LRU) records to maintain JVM heap bounds.
+* **╪┤╪▒╪¡ ┘å█î╪º╪▓┘à┘å╪»█î ┘ê ╪│┘å╪º╪▒█î┘ê█î ╪¿█î╪▓┘å╪│ (┘ü╪º╪▒╪│█î):**
+  ╪º╪╖┘ä╪º╪╣╪º╪¬ ┘à╪¡╪╡┘ê┘ä╪º╪¬ ╪¬╪│┘ç█î┘ä╪º╪¬ ╪¿╪º┘å┌⌐█î ╪¿┘ç ╪»┘ä█î┘ä ┘å╪▒╪« ╪«┘ê╪º┘å╪»┘å ╪¿╪º┘ä╪º ┘ê ╪¬╪║█î█î╪▒╪º╪¬ ╪º┘å╪»┌⌐╪î ╪»╪▒ ╪¡╪º┘ü╪╕┘ç ╪│╪▒█î╪╣ Ehcache ┘å┌»┘ç╪»╪º╪▒█î ┘à█îΓÇî╪┤┘ê┘å╪». ╪│█î╪│╪¬┘à ┘à┘ê╪╕┘ü ╪º╪│╪¬ ╪│┘é┘ü ╪¡╪º┘ü╪╕┘ç ╪▒╪º ╪¡╪»╪º┌⌐╪½╪▒ ╪¬╪º █▒█░█░█░ ┘é┘ä┘à ╪¬╪╣╪▒█î┘ü ┘å┘à┘ê╪»┘ç ┘ê ╪»╪▒ ╪╡┘ê╪▒╪¬ ┘╛╪▒ ╪┤╪»┘å ╪╕╪▒┘ü█î╪¬╪î ╪╖╪¿┘é ╪º┘ä┌»┘ê╪▒█î╪¬┘à ┌⌐┘à╪¬╪▒█î┘å ╪º╪│╪¬┘ü╪º╪»┘ç ╪º╪«█î╪▒ (LRU)╪î ╪»╪º╪»┘çΓÇî┘ç╪º█î ┘é╪»█î┘à█î ╪▒╪º ╪º╪▓ ╪¡╪º┘ü╪╕┘ç ┘╛╪º┌⌐ ┘å┘à╪º█î╪» ╪¬╪º ╪º╪▓ ╪«╪╖╪º█î ┌⌐┘à╪¿┘ê╪» ╪¡╪º┘ü╪╕┘ç (OutOfMemory) ╪¼┘ä┘ê┌»█î╪▒█î ╪¿┘ç ╪╣┘à┘ä ╪ó█î╪».
+* **╪▒┘ü╪¬╪º╪▒┘ç╪º█î ┘å╪º╪«┘ê╪º╪│╪¬┘ç ┘ê ╪┤╪▒┘ê╪╖ ╪«╪╖╪º (EARS If-Then):**
+  * `If an uncached product is requested and the primary database is unreachable, then the Fineract Caching Layer shall throw a ServiceUnavailableException without storing null values in the cache.`
+* **┘à╪º╪¬╪▒█î╪│ ╪▒╪»█î╪º╪¿█î ╪¿┘ç ╪│┘ê╪▒╪│ΓÇî┌⌐╪» (Traceability Matrix):**
+  * **┘à╪│█î╪▒ ┘ü╪º█î┘ä ┘ê ╪¬┌» XML:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/ehcache.xml`
+  * **╪¬┌» ┘ê ╪«╪╡█î╪╡┘ç ┘à┘ê╪▒╪» ╪¬╪¡┘ä█î┘ä:** `<cache name="loanProducts" maxEntriesLocalHeap="1000" memoryStoreEvictionPolicy="LRU" timeToLiveSeconds="3600"/>`
+  * **╪┤╪º╪«╪╡ΓÇî┘ç╪º█î ┌⌐┘ä█î╪»█î:** ╪│┘é┘ü █▒█░█░█░ ╪▒┌⌐┘ê╪▒╪»╪î ╪¬╪«┘ä█î┘ç LRU╪î ╪╖┘ê┘ä ╪╣┘à╪▒ ╪»╪º╪»┘ç █│█╢█░█░ ╪½╪º┘å█î┘ç
+```
