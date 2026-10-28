---
name: fineract-xml-parser
description: Extracts non-functional requirements, audit policies, caching strategies, and Spring bean definitions from XML configuration files across Apache Fineract into standardized EARS requirements. Activate when inspecting .xml configuration files like logback.xml, ehcache.xml, or persistence.xml in apache-fineract-src-1.15.0.
---

# Fineract XML Configuration Parser to EARS Requirements

## Overview
This skill guides agents in parsing XML configuration files within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to extract non-functional requirements (NFRs), logging and regulatory audit policies, distributed and local caching boundaries, and JPA persistence declarations into standardized EARS requirements.

## Target File Scope & Locations
This skill applies to all XML configuration files across the codebase:
* **Logging & Audit Specifications:**
  * `apache-fineract-src-1.15.0/**/src/main/resources/logback.xml`
  * `apache-fineract-src-1.15.0/**/src/main/resources/logback-spring.xml`
* **In-Memory & Distributed Caching:**
  * `apache-fineract-src-1.15.0/**/src/main/resources/ehcache.xml`
* **JPA Persistence Unit Definitions:**
  * `apache-fineract-src-1.15.0/**/src/main/resources/META-INF/persistence.xml`
* **Spring Application Context Bean Configurations:**
  * `apache-fineract-src-1.15.0/**/src/main/resources/**/*.xml`
* **Liquibase Schema Changeset XML Files:**
  * `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/db/changelog/**/*.xml`

---

## Architectural Semantics of XML Files

1. **`logback.xml` / `logback-spring.xml`:**
   * Defines MDC (Mapped Diagnostic Context) capturing `tenantId`, `userId`, `correlationId`.
   * Enforces log retention, rolling file policies (time/size triggers), and log sanitization (masking sensitive financial data like passwords and account balances).
2. **`ehcache.xml`:**
   * Declares cache regions for frequently accessed, infrequently mutated entities (e.g. `loanProducts`, `savingsProducts`, `offices`, `users`).
   * Configures `maxEntriesLocalHeap`, `timeToLiveSeconds`, `timeToIdleSeconds`, and memory eviction policies (`LRU`, `LFU`, `FIFO`).
3. **`persistence.xml`:**
   * Declares OpenJPA / Hibernate persistence units, caching L2 provider settings, and transaction types.

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **XML Construct:** Universal logging formats, mandatory MDC fields in appender pattern.
* **Extraction Pattern:**
  ```xml
  <encoder>
      <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level [tenant:%X{tenantId}] [user:%X{userId}] %logger{36} - %msg%n</pattern>
  </encoder>
  ```
  * Map to: `The Fineract Logging Subsystem shall inject the active tenant identifier, authenticated user ID, and timestamp into the Mapped Diagnostic Context (MDC) for every emitted log entry.`

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **XML Construct:** Cache saturation and eviction under heap constraints.
* **Extraction Pattern:**
  ```xml
  <cache name="loanProducts"
         maxEntriesLocalHeap="1000"
         memoryStoreEvictionPolicy="LRU"
         timeToLiveSeconds="3600"/>
  ```
  * Map to: `While the in-memory cache for "loanProducts" reaches the threshold of 1,000 entries, the Fineract Caching Layer shall evict the Least Recently Used (LRU) records to maintain memory bounds.`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **XML Construct:** Log file rolling events based on time or file size limits.
* **Extraction Pattern:**
  ```xml
  <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
      <fileNamePattern>fineract-%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
      <maxFileSize>100MB</maxFileSize>
      <maxHistory>30</maxHistory>
  </rollingPolicy>
  ```
  * Map to: `When an active log file reaches 100 megabytes in size, the Fineract Logging Subsystem shall compress the log into a gzip archive and initialize a new active log file.`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **XML Construct:** Asynchronous appender or secondary cache clustering.
* **Extraction Pattern:**
  ```xml
  <appender name="ASYNC" class="ch.qos.logback.classic.AsyncAppender">
      <queueSize>512</queueSize>
      <appender-ref ref="FILE" />
  </appender>
  ```
  * Map to: `Where asynchronous logging is configured, the Fineract Logging Subsystem shall buffer log records in a non-blocking queue of capacity 512 entries.`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **XML Construct:** Disk full or queue saturation behavior in logging appenders.
* **Extraction Pattern:**
  ```xml
  <neverBlock>true</neverBlock>
  <discardingThreshold>20</discardingThreshold>
  ```
  * Map to: `If the asynchronous log queue reaches 80% capacity (discardingThreshold 20%), then the Fineract Logging Subsystem shall discard TRACE and DEBUG level events to preserve system responsiveness.`

### 6. Complex Requirements
* **Template:** `While <state>, when <trigger>, the <system name> shall <system response>`
* **XML Construct:** Caching eviction combined with entity mutation events.
* **Extraction Pattern:**
  * Map to: `While an entity is cached in the "offices" cache region, when an update or delete operation completes on that office record, the Fineract Caching Layer shall invalidate the corresponding cache key across all application nodes.`

---

## Code Extraction Heuristics & XPath Patterns

| Target Element | XPath / Regex Pattern | Semantics Extracted |
| :--- | :--- | :--- |
| **Appender Pattern** | `//appender/encoder/pattern` | MDC fields, audit logging format |
| **Rolling Policy** | `//rollingPolicy/maxFileSize` | Log file size trigger and archive policy |
| **Retention Policy** | `//rollingPolicy/maxHistory` | Regulatory compliance audit log retention days |
| **Cache Region** | `//cache[@name]` | Entity caching domains and scopes |
| **Cache Bounds** | `//cache/@maxEntriesLocalHeap` | Memory saturation and resource guard |
| **Cache Expiry** | `//cache/@timeToLiveSeconds` | Data freshness and stale read prevention |
| **Eviction Policy** | `//cache/@memoryStoreEvictionPolicy`| Cache eviction algorithm (LRU, LFU, FIFO) |

---

## Step-by-Step XML Parsing Workflow

1. **Parse `logback.xml`:**
   * Extract logging appenders (Console, RollingFile, Async).
   * Note regex pattern for MDC variables (`tenantId`, `userId`).
   * Record archival limits (`maxFileSize`, `maxHistory`).
2. **Parse `ehcache.xml`:**
   * Catalog all cache regions (`users`, `offices`, `loanProducts`).
   * Extract expiration and eviction policies for each region.
3. **Parse `persistence.xml`:**
   * Identify JPA provider properties and caching configuration.
4. **Formulate Bilingual EARS Card:**
   * Create the requirement card according to the standard template.

---

## Bilingual Output Requirement Card Template

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل مفهوم عملکردی، لاگینگ، مانیتورینگ یا مدیریت حافظه کش به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و تگ XML:** `apache-fineract-src-1.15.0/.../<filename>.xml`
  * **تگ و خصیصه مورد تحلیل:** `<cache name="...">`, `<rollingPolicy>`
  * **شاخص‌های کلیدی:** ظرفیت، سیاست حذف، دوره ماندگاری
```

---

## Concrete Example

```markdown
### REQ-NFR-CACHE-LOAN-PROD-001: مدیریت کش حافظه‌محور اطلاعات محصولات تسهیلات
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While the in-memory cache for "loanProducts" reaches the maximum limit of 1,000 entries, the Fineract Caching Layer shall evict the Least Recently Used (LRU) records to maintain JVM heap bounds.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  اطلاعات محصولات تسهیلات بانکی به دلیل نرخ خواندن بالا و تغییرات اندک، در حافظه سریع Ehcache نگهداری می‌شوند. سیستم موظف است سقف حافظه را حداکثر تا ۱۰۰۰ قلم تعریف نموده و در صورت پر شدن ظرفیت، طبق الگوریتم کمترین استفاده اخیر (LRU)، داده‌های قدیمی را از حافظه پاک نماید تا از خطای کمبود حافظه (OutOfMemory) جلوگیری به عمل آید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an uncached product is requested and the primary database is unreachable, then the Fineract Caching Layer shall throw a ServiceUnavailableException without storing null values in the cache.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و تگ XML:** `apache-fineract-src-1.15.0/fineract-provider/src/main/resources/ehcache.xml`
  * **تگ و خصیصه مورد تحلیل:** `<cache name="loanProducts" maxEntriesLocalHeap="1000" memoryStoreEvictionPolicy="LRU" timeToLiveSeconds="3600"/>`
  * **شاخص‌های کلیدی:** سقف ۱۰۰۰ رکورد، تخلیه LRU، طول عمر داده ۳۶۰۰ ثانیه
```
