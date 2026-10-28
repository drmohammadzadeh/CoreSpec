---
name: fineract-config-parser
description: Extracts system configuration constraints, multi-tenancy rules, security toggles, and operational parameters from properties and YAML configuration files across Apache Fineract into standardized EARS requirements. Activate when inspecting application.properties, application.yml, or Docker configuration files in apache-fineract-src-1.15.0.
---

# Fineract Configuration Parser to EARS Requirements

## Overview
This skill guides agents in parsing configuration files (`application.properties`, `application.yml`, Docker environment files) within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to extract operational defaults, feature toggles, multi-tenancy routing rules, connection pool bounds, and environmental constraints into standardized EARS requirements.

## Target File Scope & Locations
This skill applies to all configuration files across the codebase:
* **Spring Application Configuration:**
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.properties`
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.yml`
  * `apache-fineract-src-1.15.0/**/src/main/resources/application-*.properties` (e.g. `application-test.properties`, `application-oauth.properties`)
* **Docker & Container Runtime Settings:**
  * `apache-fineract-src-1.15.0/docker/docker-compose*.yml`
  * `apache-fineract-src-1.15.0/config/docker/**/*.env`
  * `apache-fineract-src-1.15.0/docker/Dockerfile`
* **Java Configuration Beans:**
  * Classes annotated with `@ConfigurationProperties(prefix = "fineract...")`

---

## Configuration Property Semantics

1. **Multi-Tenancy Configuration (`fineract.tenant.*`):**
   * Configures shared tenant store vs isolated tenant databases, schema resolution strategies, and tenant header names.
2. **Feature Toggles (`fineract.mode.*`, `fineract.events.*`):**
   * Controls whether asynchronous command processing, external Kafka/ActiveMQ messaging, or OAuth2 authentication are active.
3. **Operational Thresholds & Defaults:**
   * Pagination limits (`fineract.pagination.default-limit`), Hikari connection pool sizes, session timeouts, and COB batch thread counts.
4. **Environment Variables Overrides:**
   * Standard convention: property `fineract.tenant.username` is overridden by environment variable `FINERACT_DEFAULT_TENANTDB_USER`.

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **Config Construct:** Hardcoded or default operational parameters and thresholds applied universally.
* **Extraction Pattern:**
  ```properties
  server.port=8080
  fineract.pagination.default-limit=200
  ```
  * Map to: `The Fineract Platform shall limit default API search query pagination to a maximum of 200 records per response.`

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **Config Construct:** Resource pool states, thread saturation, read-only replica status.
* **Extraction Pattern:**
  ```properties
  spring.datasource.hikari.connection-timeout=30000
  spring.datasource.hikari.maximum-pool-size=20
  ```
  * Map to: `While the tenant connection pool is at maximum capacity (20 active connections), the Fineract DataSource Manager shall hold pending database requests up to 30,000 milliseconds before timing out.`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **Config Construct:** Application bootstrapping, context refresh, dynamic configuration update events.
* **Extraction Pattern:**
  ```properties
  fineract.tenant.reload.enabled=true
  ```
  * Map to: `When a tenant registration or update event occurs, the Fineract Tenant Manager shall dynamically refresh the tenant connection pool without restarting the application server.`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **Config Construct:** Feature flags enabled via boolean configuration properties (`fineract.mode.async-enabled=true`, `fineract.events.external.enabled=true`).
* **Extraction Pattern:**
  ```properties
  fineract.events.external.enabled=true
  fineract.events.external.producer.jms.enabled=true
  ```
  * Map to: `Where external event publishing is enabled, the Fineract Event Engine shall publish domain events to the configured JMS broker topic.`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **Config Construct:** Missing required configuration, invalid tenant identifier header, database connection failure.
* **Extraction Pattern:**
  ```properties
  fineract.tenant.identifier-header=Fineract-Platform-TenantId
  ```
  * Map to: `If an incoming HTTP request lacks a valid tenant identifier in the "Fineract-Platform-TenantId" header, then the Fineract Gateway shall reject the request and return HTTP status 400 Bad Request with error code "error.msg.invalid.tenant.identifier".`

### 6. Complex Requirements
* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
* **Config Construct:** Multi-tenancy combined with batch processing or external authentication servers.
* **Extraction Pattern:**
  ```properties
  fineract.tenant.mode=multi-tenant
  fineract.security.oauth.enabled=true
  ```
  * Map to: `Where multi-tenancy is active, while OAuth2 authentication is enabled, when a secure REST endpoint is invoked, the Fineract Security Gateway shall validate the bearer token against the specific tenant authorization server.`

---

## Code Extraction Heuristics & Regex Patterns

| Target Element | Regex / Search Pattern | Semantics Extracted |
| :--- | :--- | :--- |
| **Property Key-Value** | `^([a-zA-Z0-9.\-_]+)\s*=\s*(.*)$` | Configuration key and default value |
| **YAML Key-Value** | `^\s*([a-zA-Z0-9\-_]+):\s*(.*)$` | Hierarchical configuration property |
| **Env Var Mapping** | `\$\{([A-Z0-9_]+):([^}]+)\}` | Environment variable fallback and default |
| **Hikari Pool Bounds** | `spring\.datasource\.hikari\.(maximum-pool-size\|minimum-idle)` | Connection pooling constraints |
| **Tenant Routing Key** | `fineract\.tenant\.(identifier-header\|datasource\..*)` | Multi-tenancy routing invariants |
| **External Event Toggle** | `fineract\.events\.external\.(enabled\|producer\..*)` | Event streaming integrations |

---

## Step-by-Step Configuration Parsing Workflow

1. **Inspect `application.properties` and `application.yml`:**
   * Catalog core operational variables (server port, context path, SSL, datasource parameters).
2. **Scan Multi-Tenant Configuration:**
   * Extract tenant master DB credentials, connection pools, and header definitions (`Fineract-Platform-TenantId`).
3. **Scan Feature Toggles:**
   * Identify all `fineract.*` feature flags and their default boolean states.
4. **Cross-Reference with `@ConfigurationProperties`:**
   * Locate the Java configuration class (e.g., `FineractProperties.java`) to verify types, validation constraints, and defaults.
5. **Formulate Bilingual EARS Card:**
   * Construct the requirement card according to the standard template.

---

## Bilingual Output Requirement Card Template

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل مفهوم پیکربندی، مقادیر پیش‌فرض و تأثیر آن بر بیزنس سامانه به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلید پیکربندی:** `apache-fineract-src-1.15.0/.../application.properties`
  * **نام کلید:** `fineract....`
  * **متغیر محیطی معادل:** `FINERACT_...`
```

---

## Concrete Example

```markdown
### REQ-CFG-TENANT-ROUTING-001: مسیریابی درخواست‌ها بر اساس شناسه مستأجر (Multi-Tenancy)
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where multi-tenancy is enabled, the Fineract Platform shall inspect the "Fineract-Platform-TenantId" HTTP header of each incoming request and route all database queries and transactions to the corresponding tenant schema.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  سامانه فاینراکت به صورت پیش‌فرض از معماری چندمستأجری (Multi-Tenancy) با تفکیک پایگاه داده یا اسکیمای مستقل پشتیبانی می‌کند. در این ساختار، هر درخواست وب حاوی هدر شناسه مستأجر بوده و هسته پلتفرم به صورت خودکار کانکشن دیتابیس را به مخزن داده همان مستأجر هدایت می‌نماید تا ایزولاسیون کامل داده‌های مالی تضمین گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an incoming API request does not contain the "Fineract-Platform-TenantId" header or contains a non-existent tenant identifier, then the Fineract Platform shall reject the request and return HTTP status 400 Bad Request with error code "error.msg.invalid.tenant.identifier".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلید پیکربندی:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/application.properties`
  * **نام کلید:** `fineract.tenant.identifier-header=Fineract-Platform-TenantId`
  * **متغیر محیطی معادل:** `FINERACT_DEFAULT_TENANTDB_IDENTIFIER`
  * **کلاس متناظر در کد:** `org.apache.fineract.infrastructure.core.boot.FineractProperties`
```
