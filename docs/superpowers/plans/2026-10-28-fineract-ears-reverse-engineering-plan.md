# Apache Fineract 1.15.0 Reverse Engineering to EARS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reverse-engineer Apache Fineract 1.15.0 into standardized EARS requirements, establishing 6 file-parsing skills, a recursive documentation crawler, global architecture models, and bilingual modular requirements documents verified by 3-tier quality gates.

**Architecture:** Decoupled knowledge pipeline with isolated subagents for foundation tooling, documentation crawling, architecture discovery, and prioritized modular reverse-engineering governed by strict quality gates.

**Tech Stack:** Python 3.10+ (requests, beautifulsoup4, markdownify), Java 17, Gradle, Spring Boot, JAX-RS, JPA, EARS Specification Standard.

**Spec:** `docs/superpowers/specs/2026-10-28-fineract-ears-reverse-engineering-design.md`

## Global Constraints
- All EARS requirements must strictly use the 6 canonical EARS patterns (Ubiquitous, State-Driven, Event-Driven, Optional Feature, Unwanted Behavior, Complex).
- The modal verb in the English EARS clause must strictly be `shall` (never `should`, `will`, `can`, or `must`).
- Output requirements must follow the bilingual format (English EARS + Persian scenario/business description + Traceability matrix).
- Every requirement must cite explicit source code grounding (relative file path, class, method/endpoint, DB table/error code).
- All file-parsing skills must be placed under `.skills/<skill-name>/SKILL.md` with standard YAML frontmatter.
- Crawled documentation must reside in `docs/crawled/` with `sitemap.json` and `SUMMARY.md`.
- Progress must be persistently recorded in `docs/sdd/progress.md`.

---

### Task 1: Create the 6 Dedicated File-Parsing Skills

**Files:**
- Create: `.skills/fineract-java-parser/SKILL.md`
- Create: `.skills/fineract-gradle-parser/SKILL.md`
- Create: `.skills/fineract-config-parser/SKILL.md`
- Create: `.skills/fineract-xml-parser/SKILL.md`
- Create: `.skills/fineract-doc-parser/SKILL.md`
- Create: `.skills/fineract-db-schema-parser/SKILL.md`

**Interfaces:**
- Consumes: Design specification rules in `docs/superpowers/specs/2026-10-28-fineract-ears-reverse-engineering-design.md`
- Produces: 6 self-contained skill packages in `.skills/` loaded by subsequent analysis agents.

- [ ] **Step 1: Write `.skills/fineract-java-parser/SKILL.md`**
Define instructions for parsing Java Spring Boot / JAX-RS controllers, service implementations, command handlers, domain entities, validators, and mapping them to EARS patterns (`When`, `While`, `If...Then`, `shall`).

- [ ] **Step 2: Write `.skills/fineract-gradle-parser/SKILL.md`**
Define instructions for parsing `build.gradle`, `settings.gradle`, and `gradle.properties` to extract module dependencies, third-party libraries, and system capability boundaries.

- [ ] **Step 3: Write `.skills/fineract-config-parser/SKILL.md`**
Define instructions for parsing `application.properties`, `.yml`, Docker, and multi-tenant configs into Optional Feature (`Where`) and Ubiquitous EARS requirements.

- [ ] **Step 4: Write `.skills/fineract-xml-parser/SKILL.md`**
Define instructions for parsing Spring XML configs, `logback.xml`, and `ehcache.xml` into audit, logging, and caching requirements.

- [ ] **Step 5: Write `.skills/fineract-doc-parser/SKILL.md`**
Define instructions for parsing Markdown, AsciiDoc, and crawled HTML docs to extract declared business workflows and user-facing requirements.

- [ ] **Step 6: Write `.skills/fineract-db-schema-parser/SKILL.md`**
Define instructions for parsing Flyway migration SQL scripts (`V...__*.sql`) to extract domain data structures, unique constraints, and audit invariants.

- [ ] **Step 7: Verify skills structure and commit**
Run verification command:
```powershell
Get-ChildItem -Path .skills -Recurse -Filter "SKILL.md" | Select-Object FullName
git add .skills/
git commit -m "feat(skills): add 6 dedicated file-parsing skills for Fineract reverse engineering"
```

---

### Task 2: Implement and Execute Documentation Crawler Subagent

**Files:**
- Create: `scripts/crawl_docs.py`
- Create: `docs/crawled/sitemap.json`
- Create: `docs/crawled/SUMMARY.md`
- Create: `docs/crawled/pages/**/*.md`

**Interfaces:**
- Consumes: Target URL `https://fineract.apache.org/docs/stable`
- Produces: Crawled markdown documentation tree in `docs/crawled/` and `docs/crawled/sitemap.json`.

- [ ] **Step 1: Implement `scripts/crawl_docs.py`**
Write a Python script that recursively crawls `https://fineract.apache.org/docs/stable` up to depth 3, sanitizes HTML (strips navbars, headers, footers), converts to Markdown, and records metadata in `docs/crawled/sitemap.json` and `docs/crawled/SUMMARY.md`.

- [ ] **Step 2: Execute crawler script**
Run:
```powershell
python scripts/crawl_docs.py
```
Verify that pages are downloaded and `docs/crawled/sitemap.json` is populated with depth tracking (0, 1, 2, 3).

- [ ] **Step 3: Commit crawled corpus**
```powershell
git add scripts/crawl_docs.py docs/crawled/
git commit -m "feat(crawler): crawl Fineract stable documentation up to depth 3"
```

---

### Task 3: Extract Global System Architecture & Module Graph (Arch Subagent A)

**Files:**
- Create: `docs/architecture/01-system-modules-and-stack.md`

**Interfaces:**
- Consumes: `apache-fineract-src-1.15.0/settings.gradle`, `build.gradle`, subproject `build.gradle` files.
- Produces: Full module dependency graph (Mermaid), technology stack breakdown, and multi-tenancy database routing architecture.

- [ ] **Step 1: Analyze Gradle submodules and dependencies**
Execute dependency analysis across all 40+ subprojects in `apache-fineract-src-1.15.0`.

- [ ] **Step 2: Document module dependency graph and multi-tenancy**
Write `docs/architecture/01-system-modules-and-stack.md` including:
- Mermaid diagram of inter-module dependencies.
- Technology stack matrix (Java 17, Spring Boot, OpenJPA, Flyway, Ehcache, Quartz, ActiveMQ/Kafka).
- Multi-tenancy architecture (TenantDataSourceProvider, schema switching).

- [ ] **Step 3: Commit architecture document**
```powershell
git add docs/architecture/01-system-modules-and-stack.md
git commit -m "docs(architecture): add system modules dependency graph and tech stack"
```

---

### Task 4: Extract API Catalog, CQRS Pipeline & RBAC Permissions (Arch Subagent B)

**Files:**
- Create: `docs/architecture/02-api-cqrs-and-security.md`

**Interfaces:**
- Consumes: REST Controllers, JAX-RS annotations, `CommandWrapper`, `PortfolioCommandSourceWritePlatformService`, `CommandHandler` implementations.
- Produces: Categorized REST API directory, CQRS execution pipeline, and RBAC permissions dictionary.

- [ ] **Step 1: Extract all REST API endpoints and command mappings**
Scan `apache-fineract-src-1.15.0` for `@Path`, `@POST`, `@GET`, `@PUT`, `@DELETE` and corresponding command handlers.

- [ ] **Step 2: Document API catalog, CQRS flow, and security permissions**
Write `docs/architecture/02-api-cqrs-and-security.md` detailing:
- REST API inventory grouped by functional domain.
- Command execution sequence diagram (Request $\to$ Filter $\to$ CommandWrapper $\to$ Handler $\to$ Event $\to$ Audit).
- RBAC permissions taxonomy.

- [ ] **Step 3: Commit API & CQRS document**
```powershell
git add docs/architecture/02-api-cqrs-and-security.md
git commit -m "docs(architecture): add REST API catalog, CQRS pipeline and RBAC permissions"
```

---

### Task 5: Extract Domain Data Model, State Machines & COB Batch Lifecycle (Arch Subagent C)

**Files:**
- Create: `docs/architecture/03-domain-data-events-and-cob.md`

**Interfaces:**
- Consumes: JPA `@Entity` classes, Flyway SQL scripts in `fineract-provider/src/main/resources/db/migration/`, `fineract-cob`.
- Produces: Core banking ERD, account state machines, and Close of Business (COB) execution architecture.

- [ ] **Step 1: Analyze database schema and JPA entities**
Extract core tables (`m_loan`, `m_savings_account`, `m_client`, `acc_gl_journal_entry`, `m_charge`) and relationships.

- [ ] **Step 2: Document ERD, state machines, and COB lifecycle**
Write `docs/architecture/03-domain-data-events-and-cob.md` detailing:
- Mermaid ERD of banking portfolio.
- Loan and Savings account state machine diagrams.
- Close-of-Business (COB) batch execution flow and day-end accrual jobs.

- [ ] **Step 3: Commit data model & COB document**
```powershell
git add docs/architecture/03-domain-data-events-and-cob.md
git commit -m "docs(architecture): add domain data model, state machines and COB batch lifecycle"
```

---

### Task 6: Consolidate Canonical Banking Domain Glossary

**Files:**
- Create: `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`

**Interfaces:**
- Consumes: Architecture documents (`01`, `02`, `03`) and crawled documentation in `docs/crawled/`.
- Produces: Authoritative banking dictionary with English terms, Persian translations, definitions, and entity mappings.

- [ ] **Step 1: Compile unified banking glossary**
Gather financial terms (Principal, Interest, Amortization, Accrual, Moratorium, Grace Period, Delinquency, NPA, Tranche, Disbursal, Write-Off, General Ledger, COB).

- [ ] **Step 2: Write `docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md`**
Document terms in a standardized table with English term, Persian translation, precise domain definition, and Fineract entity/class reference.

- [ ] **Step 3: Commit glossary**
```powershell
git add docs/architecture/GLOBAL_DOMAIN_GLOSSARY.md
git commit -m "docs(architecture): add global banking domain glossary"
```

---

### Task 7: Reverse-Engineer Tier 1: Core Lending & Progressive Loans Portfolio

**Files:**
- Create: `docs/requirements/01-loan-portfolio.md`

**Interfaces:**
- Consumes: `fineract-loan`, `fineract-progressive-loan`, `fineract-loan-origination`, `.skills/fineract-java-parser/`, `GLOBAL_DOMAIN_GLOSSARY.md`.
- Produces: Comprehensive bilingual EARS requirements document for loan products, lifecycle, interest schedules, disbursements, repayments, write-offs, and restructuring.

- [ ] **Step 1: Analyze loan products and creation rules**
Extract requirements for product definition, interest calculation methods (Flat, Declining Balance), repayment frequencies, and amortization schedules.

- [ ] **Step 2: Analyze loan account lifecycle and transaction commands**
Extract requirements for submission, approval, disbursal, repayment, prepayment, foreclosure, waiver, and write-off.

- [ ] **Step 3: Write bilingual EARS requirements in `docs/requirements/01-loan-portfolio.md`**
Structure every requirement with EARS pattern name, English statement with `shall`, Persian explanation, unwanted behavior clauses (`If...Then`), and code traceability matrix.

- [ ] **Step 4: Commit loan requirements**
```powershell
git add docs/requirements/01-loan-portfolio.md
git commit -m "feat(requirements): add comprehensive EARS requirements for loan portfolio"
```

---

### Task 8: Reverse-Engineer Tier 2: Savings & Deposit Accounts

**Files:**
- Create: `docs/requirements/02-savings-and-deposits.md`

**Interfaces:**
- Consumes: `fineract-savings`, `fineract-provider/.../savings/`, `.skills/fineract-java-parser/`, `GLOBAL_DOMAIN_GLOSSARY.md`.
- Produces: Bilingual EARS requirements document for savings accounts, recurring deposits, fixed deposits, interest postings, and withdrawal limits.

- [ ] **Step 1: Analyze savings products and account rules**
Extract requirements for regular savings, fixed deposit terms, recurring deposits, interest compounding, and posting periods.

- [ ] **Step 2: Analyze savings transactions and state transitions**
Extract requirements for deposit, withdrawal, amount holds, interest calculation, dormancy, and account closure.

- [ ] **Step 3: Write bilingual EARS requirements in `docs/requirements/02-savings-and-deposits.md`**
Format all requirements in standard EARS with Persian explanations and code traceability.

- [ ] **Step 4: Commit savings requirements**
```powershell
git add docs/requirements/02-savings-and-deposits.md
git commit -m "feat(requirements): add comprehensive EARS requirements for savings and deposits"
```

---

### Task 9: Reverse-Engineer Tier 3: Core Accounting, Financial GL & Charges/Tax

**Files:**
- Create: `docs/requirements/03-accounting-and-financial-ledger.md`
- Create: `docs/requirements/04-charges-taxes-and-rates.md`

**Interfaces:**
- Consumes: `fineract-accounting`, `fineract-charge`, `fineract-tax`, `fineract-rates`.
- Produces: Bilingual EARS requirements for General Ledger (GL) journal entries, cash vs accrual accounting, fee schedules, penalty calculations, and tax withholdings.

- [ ] **Step 1: Analyze Chart of Accounts and GL entry rules**
Extract double-entry accounting rules, manual journal vouchers, automated accruals, and financial activity mappings.

- [ ] **Step 2: Analyze charges, fees, taxes, and interest rates**
Extract fee calculation modes (flat, percentage of principal/disbursement), overdue penalties, and withholding tax rules.

- [ ] **Step 3: Write bilingual EARS requirements in `docs/requirements/03-...` and `04-...`**
Generate both requirement documents conforming strictly to the EARS template.

- [ ] **Step 4: Commit accounting and charges requirements**
```powershell
git add docs/requirements/03-accounting-and-financial-ledger.md docs/requirements/04-charges-taxes-and-rates.md
git commit -m "feat(requirements): add EARS requirements for accounting, GL, charges and taxes"
```

---

### Task 10: Reverse-Engineer Tier 4: Close of Business (COB) & Batch Operations

**Files:**
- Create: `docs/requirements/05-cob-and-batch-operations.md`

**Interfaces:**
- Consumes: `fineract-cob`, scheduled jobs in `fineract-provider/.../infrastructure/jobs/`.
- Produces: Bilingual EARS requirements for day-end loan processing, day-end accruals, holiday rules, account locking, and batch retry mechanisms.

- [ ] **Step 1: Analyze COB batch pipeline and job workflows**
Extract requirements for business day advancement, loan delinquency aging, automated interest accrual posting, and business lockouts.

- [ ] **Step 2: Write bilingual EARS requirements in `docs/requirements/05-cob-and-batch-operations.md`**
Generate EARS specifications with preconditions (`While`), triggers (`When`), and exception flows (`If...Then`).

- [ ] **Step 3: Commit COB requirements**
```powershell
git add docs/requirements/05-cob-and-batch-operations.md
git commit -m "feat(requirements): add EARS requirements for COB and batch operations"
```

---

### Task 11: Reverse-Engineer Tier 5: Organization, CRM & Infrastructure

**Files:**
- Create: `docs/requirements/06-crm-organization-and-security.md`
- Create: `docs/requirements/07-infrastructure-and-integrations.md`

**Interfaces:**
- Consumes: `client`, `group`, `organisation`, `useradministration`, `notification`, messaging modules.
- Produces: Bilingual EARS requirements for customer onboarding (KYC), branch hierarchies, teller/cashier management, two-factor authentication, and asynchronous Kafka/ActiveMQ messaging.

- [ ] **Step 1: Analyze client KYC, offices, tellers, and user administration**
Extract requirements for client states, document attachments, branch hierarchy, cashier floating limits, and user permissions.

- [ ] **Step 2: Analyze infrastructure, event streaming, and integrations**
Extract requirements for event streaming (Kafka/ActiveMQ), webhooks, SMS/email notifications, and document storage.

- [ ] **Step 3: Write bilingual EARS requirements in `docs/requirements/06-...` and `07-...`**
Generate requirement specifications following standard EARS format.

- [ ] **Step 4: Commit CRM and infrastructure requirements**
```powershell
git add docs/requirements/06-crm-organization-and-security.md docs/requirements/07-infrastructure-and-integrations.md
git commit -m "feat(requirements): add EARS requirements for CRM, organization and infrastructure"
```

---

### Task 12: Run 3-Tier Quality Gate Auditing & Assemble Unified Master Catalog

**Files:**
- Create: `scripts/audit_ears_requirements.py`
- Create: `docs/requirements/MASTER_REQUIREMENTS_INDEX.md`
- Create: `docs/sdd/progress.md`

**Interfaces:**
- Consumes: All requirement files in `docs/requirements/*.md` and source code in `apache-fineract-src-1.15.0/`.
- Produces: Verification audit report, comprehensive traceability matrix, and the master requirements index.

- [ ] **Step 1: Implement automated EARS linter and traceability checker**
Write `scripts/audit_ears_requirements.py` to verify:
- Gate 1: Strict EARS keywords (`shall`, valid pattern format).
- Gate 2: Cited file paths and class/method references actually exist.
- Gate 3: Invariants (accounting balanced entries, valid status transitions).

- [ ] **Step 2: Execute auditor script across all requirements**
Run:
```powershell
python scripts/audit_ears_requirements.py
```
Ensure 100% pass rate; fix any flagged issues.

- [ ] **Step 3: Compile `docs/requirements/MASTER_REQUIREMENTS_INDEX.md`**
Generate the master catalog indexing every single requirement ID, title, pattern, module, and file link.

- [ ] **Step 4: Commit final audit and master requirements index**
```powershell
git add scripts/audit_ears_requirements.py docs/requirements/MASTER_REQUIREMENTS_INDEX.md docs/sdd/progress.md
git commit -m "feat(catalog): audit all requirements and generate master requirements index"
```
