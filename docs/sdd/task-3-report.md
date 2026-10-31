# Task 3 Report: Global System Architecture, Module Graph & Technology Stack

**Date:** 2026-10-28  
**Task:** Task 3 - Extract Global System Architecture & Module Graph (Arch Subagent A)  
**Status:** `DONE`  
**Commit Hash:** `be17a1a61feb3e63371b80759194cf7db8c1f015` (Short: `be17a1a`)  

---

## 1. Executive Summary

Task 3 of the Apache Fineract 1.15.0 reverse-engineering project has been successfully completed. An exhaustive architectural analysis was performed across all 46 Gradle subprojects, root build configurations (`settings.gradle`, `build.gradle`, `dependencies.gradle`), and operational application configurations.

The primary deliverable, `docs/architecture/01-system-modules-and-stack.md`, has been authored and committed to the repository. It includes:
1. **Exhaustive Module Inventory:** 46 Gradle submodules categorized into 7 distinct architectural tiers with dependency paths and roles.
2. **Comprehensive Module Dependency Graph:** Complete, valid Mermaid flowchart illustrating inter-module coupling and tier boundaries.
3. **Technology Stack Matrix:** Detailed matrix covering runtime (JDK 21 LTS), frameworks (Spring Boot 3.5.15), persistence (EclipseLink 4.0.9 with static weaving), databases (PostgreSQL, MariaDB, MySQL), connection pooling (HikariCP), messaging (Kafka, ActiveMQ), high-throughput ring buffer (LMAX Disruptor 4.0.0), and observability (Micrometer, OpenTelemetry).
4. **Multi-Tenancy Deep Dive:** Full analysis of the separate-schema/database-per-tenant architecture, HTTP resolution (`Fineract-Platform-TenantId`), context isolation (`ThreadLocalContextUtil`, `FineractContext`), routing data source (`RoutingDataSource`, `DataSourcePerTenantServiceFactory`, `TomcatJdbcDataSourcePerTenantService`), and read-only replica routing, complete with a Mermaid sequence diagram.
5. **Architectural EARS Requirements:** Standard bilingual EARS requirement cards (Ubiquitous, Event-Driven, State-Driven, Optional Feature, Complex) adhering to the strict `shall` normative constraint and grounded traceability matrix.

---

## 2. Deliverables & Files Touched

| # | File Path | Status | Description |
| :- | :--- | :--- | :--- |
| 1 | `docs/architecture/01-system-modules-and-stack.md` | Created & Committed (`be17a1a`) | Comprehensive system architecture, module topology, tech stack matrix, multi-tenancy mechanics, and architectural EARS requirements. |
| 2 | `docs/sdd/task-3-report.md` | Created | Full task completion report and audit trail. |

---

## 3. Key Findings & Architectural Highlights

1. **Java 21 LTS Runtime & Toolchain:**
   * Apache Fineract 1.15.0 enforces `JavaLanguageVersion.of(21)` in `build.gradle`.
   * Compilation applies ErrorProne 2.49.0, Checkstyle 13.4.2, SpotBugs 6.5.4, and Spotless 6.25.0.
2. **Spring Boot 3.5.15 & Jakarta EE 10:**
   * Full modernization to Jakarta EE packages (`jakarta.persistence`, `jakarta.ws.rs`, `jakarta.servlet`).
   * Dual REST layer support using Jersey 3.1.11 and Spring MVC with SpringDoc OpenAPI 2.8.17.
3. **EclipseLink 4.0.9 with Static Weaving:**
   * Replaces legacy Hibernate/OpenJPA implementations as the primary JPA provider.
   * Leverages static bytecode weaving (`static-weaving.gradle`) for enhanced lazy loading, change tracking, and relationship fetch performance without runtime overhead.
4. **Database-Per-Tenant Architecture:**
   * Root catalog `fineract_tenants` maintains tenant connection metadata.
   * `TenantAwareBasicAuthenticationFilter` strictly requires the `Fineract-Platform-TenantId` HTTP header.
   * `RoutingDataSource` acts as the primary data source, dynamically delegating to a per-tenant `HikariDataSource` maintained in `ConcurrentHashMap`.
   * Read-only replicas are natively supported for high-volume read transactions (`fineract.mode.read-enabled=true`).
   * Full context propagation across asynchronous threads and COB batch workers is handled by `ThreadLocalContextUtil` and immutable snapshots via `FineractContext`.
5. **Ultra-High Throughput CQRS & COB Batching:**
   * LMAX Disruptor 4.0.0 provides lock-free ring-buffer processing for write commands in `fineract-command-disruptor`.
   * Spring Batch 5.x and Spring Integration power the Close-of-Business (COB) partitioned loan processing engine in `fineract-cob`.

---

## 4. Verification & Quality Gates

* **Exhaustive Module Coverage:** All 46 Gradle modules declared in `settings.gradle` and dynamic `custom` subdirectories were indexed and traced.
* **Mermaid Syntax Validation:** All subgraphs, node quotes, and dependency flow lines in both the architectural flowchart and the multi-tenancy sequence diagram adhere strictly to supported Mermaid standards.
* **EARS Normative Compliance:** All 8 architectural EARS requirements strictly use the modal verb **`shall`** in their English requirement clauses, with complete Persian technical narratives, failure modes (`If-Then`), and source-code traceability matrices.
* **Git Commit Audit:**
  * Added `docs/architecture/01-system-modules-and-stack.md`.
  * Committed with message `docs(architecture): add system modules dependency graph and tech stack`.
  * Commit verified: `be17a1a61feb3e63371b80759194cf7db8c1f015`.
