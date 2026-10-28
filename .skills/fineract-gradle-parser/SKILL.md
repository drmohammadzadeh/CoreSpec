---
name: fineract-gradle-parser
description: Extracts architectural capability boundaries, modular dependencies, and third-party subsystem integration requirements from Gradle build files across Apache Fineract into standardized EARS requirements. Activate when inspecting build.gradle, settings.gradle, or gradle.properties files in apache-fineract-src-1.15.0.
---

# Fineract Gradle Build Parser to EARS Requirements

## Overview
This skill instructs agents on parsing root and multi-project Gradle build files within Apache Fineract 1.15.0 (`apache-fineract-src-1.15.0/`) to reverse-engineer system architecture boundaries, modular dependencies, technology stack constraints, and integration capabilities into standardized EARS requirements.

## Target File Scope & Locations
This skill applies to all Gradle build and property files:
* **Root Build Settings:**
  * `apache-fineract-src-1.15.0/settings.gradle` (all subproject module declarations)
  * `apache-fineract-src-1.15.0/build.gradle` (root build script, plugins, subprojects configuration)
  * `apache-fineract-src-1.15.0/dependencies.gradle` (dependency management versions, shared libraries)
  * `apache-fineract-src-1.15.0/gradle.properties` (JVM configuration, flag toggles)
* **Submodule Build Files:**
  * `apache-fineract-src-1.15.0/**/build.gradle` (e.g. `fineract-provider/build.gradle`, `fineract-core/build.gradle`, `fineract-loan/build.gradle`, `fineract-accounting/build.gradle`, `fineract-cob/build.gradle`)
* **Build Tools & Conventions:**
  * `apache-fineract-src-1.15.0/buildSrc/src/main/groovy/**`

---

## Architectural Semantics of Gradle Declarations

1. **Subproject Declarations (`settings.gradle`):**
   * Every `include 'module-name'` statement establishes an isolated architectural domain or infrastructural subsystem boundary.
2. **Inter-Module Dependencies (`project(':module-name')`):**
   * Defines coupling, domain flow, and modular hierarchy (e.g., `fineract-loan` depends on `fineract-core`, but `fineract-core` never depends on `fineract-loan`).
3. **Third-Party Integrations (`implementation 'group:artifact:version'`):**
   * Pinpoints third-party enterprise services:
     * `spring-boot-starter-data-jpa` $\to$ Relational database persistence.
     * `org.apache.activemq` / `spring-kafka` $\to$ Event streaming and messaging broker.
     * `org.ehcache` $\to$ In-memory distributed and local caching.
     * `org.quartz-scheduler` $\to$ Background job orchestration and COB scheduling.
     * `com.lmax:disruptor` $\to$ High-throughput ring-buffer asynchronous command processing.
     * `org.liquibase:liquibase-core` $\to$ Database schema change management.

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **Gradle Construct:** Universal runtime platform requirements, baseline compiler targets, UTF-8 source encodings.
* **Extraction Pattern:**
  ```groovy
  java {
      toolchain {
          languageVersion = JavaLanguageVersion.of(17)
      }
  }
  ```
  * Map to: `The Fineract Platform shall execute on a Java 17 runtime environment.`

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **Gradle Construct:** Profile-based execution (e.g., test execution vs production build), daemon execution flags.
* **Extraction Pattern:**
  ```groovy
  tasks.withType(Test) {
      systemProperty 'spring.profiles.active', 'test'
  }
  ```
  * Map to: `While executing under the automated test profile, the Fineract Platform shall utilize the isolated in-memory or ephemeral tenant test database.`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **Gradle Construct:** Lifecycle tasks, compilation events, container image packaging.
* **Extraction Pattern:**
  ```groovy
  tasks.named('bootJar') {
      archiveClassifier = 'boot'
  }
  ```
  * Map to: `When the executable packaging task is invoked, the Fineract Build Subsystem shall produce a self-contained Spring Boot executable JAR including all embedded web server components.`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **Gradle Construct:** Optional subprojects, conditional plugins, or modular feature packs (e.g., `fineract-investor`, `oauth2-tests`, `fineract-mix`).
* **Extraction Pattern:**
  ```groovy
  if (project.hasProperty('enableKafka')) {
      implementation 'org.springframework.kafka:spring-kafka'
  }
  ```
  * Map to: `Where Apache Kafka messaging is included, the Fineract Event Engine shall publish domain events to designated Kafka topic brokers.`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **Gradle Construct:** Dependency resolution conflicts, missing JDK requirements, checkstyle/lint violations.
* **Extraction Pattern:**
  ```groovy
  configurations.all {
      resolutionStrategy.failOnVersionConflict()
  }
  ```
  * Map to: `If a transitively resolved library exhibits a version conflict, then the Fineract Build Engine shall terminate the build immediately with an explicit version resolution failure.`

### 6. Complex Requirements
* **Template:** `Where <feature>, while <state>, when <trigger>, the <system name> shall <system response>`
* **Gradle Construct:** Asynchronous command processing combined with external broker libraries and queue states.
* **Extraction Pattern:**
  ```groovy
  project(':fineract-command-disruptor') {
      dependencies {
          implementation project(':fineract-command')
          implementation 'com.lmax:disruptor'
      }
  }
  ```
  * Map to: `Where the disruptor-based command subsystem is enabled, when a write command is dispatched, the Fineract Command Engine shall process the command payload asynchronously using an in-memory ring buffer.`

---

## Code Extraction Heuristics & Regex Patterns

| Target Element | Regex / Search Pattern | Semantics Extracted |
| :--- | :--- | :--- |
| **Subproject List** | `include\s+['"]([^'"]+)['"]` | System module inventory and isolation boundaries |
| **Subproject Coupling** | `project\s*\(\s*['"](:[^'"]+)['"]\s*\)` | Inter-module capability dependency |
| **External Dependency** | `(implementation\|api)\s+['"]([^:]+):([^:]+):?([^'"]*)['"]` | Third-party framework capability integration |
| **Java Toolchain** | `JavaLanguageVersion\.of\s*\(\s*([0-9]+)\s*\)` | Core platform runtime specification |
| **Plugin Declaration** | `id\s+['"]([^'"]+)['"]` | Platform build extensions (Docker, Spring Boot, Spotless) |
| **Compiler Args** | `options\.compilerArgs\s*\+=\s*\[([^\]]+)\]` | JVM memory parameters, bytecode constraints |

---

## Step-by-Step Gradle Parsing Workflow

1. **Scan `settings.gradle`:**
   * Extract all declared submodules. Map them into high-level domains (Core, Loan, Savings, Accounting, COB, Messaging, Security).
2. **Analyze Root `build.gradle` and `dependencies.gradle`:**
   * Identify core frameworks (Spring Boot, OpenJPA, Liquibase/Flyway, Jackson, Apache Camel, etc.).
   * Document baseline ubiquitous platform constraints (Java 17, UTF-8, strict checkstyle).
3. **Inspect Submodule `build.gradle` Files:**
   * Trace incoming and outgoing dependencies for each module to identify architectural layers (e.g. `fineract-progressive-loan` $\to$ `fineract-loan` $\to$ `fineract-core`).
4. **Formulate Bilingual EARS Card:**
   * Document architectural boundaries and non-functional requirements conforming to the standard template.

---

## Bilingual Output Requirement Card Template

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل مفهوم معماری، مرزهای ماژولار و نقش کتابخانه‌ها به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/.../build.gradle`
  * **پیکربندی و کتابخانه وابسته:** `implementation project(':...')`, `group:artifact:version`
  * **اهداف معماری:** جداسازی ماژولار و کنترل وابستگی‌ها
```

---

## Concrete Example

```markdown
### REQ-ARCH-ASYNC-CMD-001: پردازش ناهمگام دستورات مالی از طریق بافر حلقوی دیسراپتور
* **الگوی EARS:** Complex
* **EARS Statement:**
  > Where the disruptor command processing module ("fineract-command-disruptor") is included, when a high-throughput write command is submitted, the Fineract Command Subsystem shall enqueue and execute the command payload asynchronously using an in-memory ring buffer without blocking the calling HTTP servlet thread.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  ماژول پردازش دستورات به صورت ناهمگام (`fineract-command-disruptor`) امکان پردازش با توان عملیاتی بسیار بالا را فراهم می‌سازد. در این ماژول با استفاده از کتابخانه LMAX Disruptor، رویدادها و دستورات ثبت تراکنش‌های بانکی در یک بافر حلقوی حافظه‌محور صف‌بندی شده و تردهای اختصاصی سیستم بدون معطل نگاه داشتن درخواست وب کلاینت، دستور را اجرا و ذخیره می‌کنند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the disruptor ring buffer reaches maximum capacity and backpressure timeout expires, then the Fineract Command Subsystem shall reject incoming write commands and return an HTTP 503 Service Unavailable response.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-command-disruptor/build.gradle`
  * **پیکربندی و کتابخانه وابسته:** `implementation project(':fineract-command')`, `implementation 'com.lmax:disruptor:3.4.4'`
  * **اهداف معماری:** تفکیک دستورات CQRS و مقیاس‌پذیری عملیات با توان پردازشی بالا
```
