# Task 3 Brief: Extract Global System Architecture & Module Graph (Arch Subagent A)

## Role in Project
Analyze the full module topology, Gradle build configuration, and technology stack of Apache Fineract 1.15.0 to produce the foundational system architecture document `docs/architecture/01-system-modules-and-stack.md`.

## Files to Touch
- Create: `docs/architecture/01-system-modules-and-stack.md`
- Report: `docs/sdd/task-3-report.md`

## Input Resources
- Skills: `.skills/fineract-gradle-parser/SKILL.md` and `.skills/fineract-config-parser/SKILL.md`
- Codebase: `apache-fineract-src-1.15.0/settings.gradle`, `build.gradle`, subproject directories
- Crawled Docs: `docs/crawled/pages/stable/sections/05-architecture.md`

## Deliverables & Detailed Requirements
1. **Module Dependency Graph:**
   - Exhaustively analyze all 40+ Gradle submodules in `settings.gradle`.
   - Categorize modules into:
     - Core & Kernel (`fineract-core`, `fineract-provider`, `fineract-validation`)
     - Business Portfolio (`fineract-loan`, `fineract-progressive-loan`, `fineract-savings`, `fineract-accounting`, `fineract-charge`, `fineract-tax`, `fineract-rates`, `fineract-investor`)
     - Command & CQRS (`fineract-command`, `fineract-command-async`, `fineract-command-disruptor`, `fineract-command-jdbc`)
     - Batch & Operations (`fineract-cob`, `fineract-document`, `fineract-mix`)
     - Clients & Integration (`fineract-client`, `fineract-client-feign`, `fineract-avro-schemas`)
   - Generate a comprehensive, valid Mermaid flowchart showing module relationships and dependency hierarchy.
2. **Technology Stack Matrix:**
   - Table detailing runtime, language, frameworks, database abstraction, caching, queuing, and serialization with versions and rationale.
3. **Multi-Tenancy Architecture:**
   - Detail the multi-tenant architecture: Tenant database routing (`TenantDataSourceProvider`), schema isolation, tenant connection pooling (HikariCP), and HTTP tenant resolution (`Fineract-Platform-TenantId` header).
4. **EARS Invariant Requirements:**
   - Include core architectural EARS requirements for the platform (Ubiquitous, Optional Feature, Unwanted Behavior) strictly using the modal verb `shall` and bilingual formatting.

## Report Contract
- Author `docs/architecture/01-system-modules-and-stack.md`.
- Commit with `git add docs/architecture/01-system-modules-and-stack.md` and message `docs(architecture): add system modules dependency graph and tech stack`.
- Write your full report to `docs/sdd/task-3-report.md`.
- Return status (DONE), commit hash, and summary.
