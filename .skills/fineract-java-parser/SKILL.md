---
name: fineract-java-parser
description: Extracts standardized EARS requirements from Java source files across Apache Fineract, analyzing JAX-RS/Spring MVC controllers, CQRS command handlers, domain entities, state machines, and data validation rules into bilingual requirements. Activate when inspecting .java files in apache-fineract-src-1.15.0.
---

# Fineract Java Source Code Parser to EARS Requirements

## Overview
This skill guides agents in parsing Java source files in the Apache Fineract 1.15.0 codebase (`apache-fineract-src-1.15.0/`) to systematically extract, structure, and document business logic, financial algorithms, access control, and state transitions as standardized EARS (Easy Approach to Requirements Syntax) requirements.

## Target File Scope & Locations
This skill applies to all Java files (`*.java`) located under:
* `apache-fineract-src-1.15.0/**/src/main/java/**/*.java`
* Key submodules:
  * `fineract-provider/src/main/java/org/apache/fineract/**`
  * `fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/**`
  * `fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/**`
  * `fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/**`
  * `fineract-accounting/src/main/java/org/apache/fineract/accounting/**`
  * `fineract-charge/src/main/java/org/apache/fineract/portfolio/charge/**`
  * `fineract-cob/src/main/java/org/apache/fineract/cob/**`

### Key Java Architectural Roles
1. **API Resources (Controllers):** `*ApiResource.java` (JAX-RS annotations: `@Path`, `@POST`, `@GET`, `@PUT`, `@DELETE`, `@PreAuthorize`)
2. **Command Handlers:** `*CommandHandler.java` (CQRS command processing: `CommandHandler`, `CommandWrapper`, `NewCommandSourceHandler`)
3. **Write Platform Services:** `*WritePlatformServiceImpl.java` (Transactional business logic, calculations, state mutations)
4. **Read Platform Services:** `*ReadPlatformServiceImpl.java` (Reporting, search, query projection)
5. **Domain Entities:** `@Entity` classes (JPA state models, invariants, lifecycle hooks, e.g. `Loan.java`, `SavingsAccount.java`)
6. **State Enums:** Status enums with transitions (e.g. `LoanStatus.java`, `SavingsAccountStatus.java`)
7. **Validators:** `*DataValidator.java`, `DataValidatorBuilder` (Parameter constraints, type checks, business rule preconditions)

---

## EARS Mapping Rules & Syntactic Constraints

All generated requirements must conform to the 6 canonical EARS patterns and strictly utilize the modal verb **`shall`** in the English requirement clause. Never use `should`, `will`, `can`, or `must`.

### 1. Ubiquitous Requirements
* **Template:** `The <system name> shall <system response>`
* **Java Source Construct:** Universal invariants, auditing timestamps (`@CreatedDate`, `@LastModifiedDate`), global tenant isolation, immutable transaction IDs.
* **Extraction Pattern:**
  * Base entity auditing: `AbstractAuditableCustom` / `created_date`, `createdby_id`.
  * OpenJPA optimistic locking: `@Version Long version`.

### 2. State-Driven Requirements
* **Template:** `While <precondition(s)>, the <system name> shall <system response>`
* **Java Source Construct:** Guard clauses checking domain entity status enum or boolean flags before proceeding.
* **Extraction Pattern:**
  ```java
  if (!this.loanStatus.isActive()) {
      throw new LoanNotFoundException(this.getId());
  }
  ```
  * Map `this.loanStatus.isApproved()` $\to$ `While the loan account is in "APPROVED" state...`

### 3. Event-Driven Requirements
* **Template:** `When <trigger>, the <system name> shall <system response>`
* **Java Source Construct:** JAX-RS REST endpoints, incoming HTTP requests, API commands, message events.
* **Extraction Pattern:**
  ```java
  @POST
  @Path("{loanId}")
  @Consumes({MediaType.APPLICATION_JSON})
  @Produces({MediaType.APPLICATION_JSON})
  public String stateTransitions(@PathParam("loanId") final Long loanId, @QueryParam("command") final String commandParam, ...)
  ```
  * Map `POST /v1/loans/{loanId}?command=disburse` $\to$ `When a disburse command is received for a specified loan...`

### 4. Optional Feature Requirements
* **Template:** `Where <feature is included>, the <system name> shall <system response>`
* **Java Source Construct:** Feature toggle flags in Product settings, conditional strategy injections, optional configurations (e.g., `isMultiDisburseAllowed`, `isInterestRecalculationEnabled`, `isTopup`).
* **Extraction Pattern:**
  ```java
  if (loanProduct.isMultiDisburseLoan()) {
      // multi disbursement logic
  }
  ```
  * Map to `Where multi-disbursement is enabled on the loan product, the Fineract Loan Engine shall...`

### 5. Unwanted Behavior Requirements
* **Template:** `If <trigger/condition>, then the <system name> shall <system response>`
* **Java Source Construct:** Validation failure checks, `DataValidatorBuilder`, exception throwing (`PlatformApiDataValidationException`, `LoanException`).
* **Extraction Pattern:**
  ```java
  baseDataValidator.reset().parameter("principal").value(principal).notNull().positiveAmount();
  if (disbursementAmount.compareTo(approvedPrincipal) > 0) {
      throw new LoanException("error.msg.loan.amount.exceeds.approved", ...);
  }
  ```
  * Map to `If the requested disbursement amount exceeds the approved principal, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.amount.exceeds.approved".`

### 6. Complex Requirements
* **Template:** `While <state>, when <trigger>, the <system name> shall <system response>` OR `Where <feature>, if <unwanted condition>, then the <system name> shall <system response>`
* **Java Source Construct:** Method with status guard, event trigger, and optional feature check combined.
* **Extraction Pattern:**
  ```java
  if (loan.getStatus().isApproved()) {
      if (command.isDisburse()) {
          loan.disburse(disbursementDate, amount, ...);
      }
  }
  ```

---

## Code Extraction Heuristics & Regex Patterns

When analyzing Java files, use the following regex patterns to locate requirement candidates:

| Target Element | Regex / Search Pattern | Semantics Extracted |
| :--- | :--- | :--- |
| **REST Endpoint** | `@Path\s*\(\s*["']([^"']+)["']\s*\)` | API URL trigger path |
| **HTTP Verb** | `@(POST\|GET\|PUT\|DELETE)` | Event action trigger |
| **Security Role** | `@PreAuthorize\s*\(\s*["']hasAuthority\('([^']+)'\)["']\s*\)` | Precondition authorization clause |
| **Command Router** | `commands\.contains\s*\(\s*["']([^"']+)["']\s*\)` | Action command trigger parameter |
| **Validation Error** | `baseDataValidator\.reset\(\)\.parameter\(["']([^"']+)["']\)` | Input parameter validation invariants |
| **Business Exception** | `throw\s+new\s+([A-Za-z0-9_]+Exception)\s*\(\s*["']([^"']+)["']` | Unwanted behavior error codes |
| **State Inspection** | `if\s*\(!?this\.[a-zA-Z0-9_]+\.is([A-Za-z]+)\(\)\)` | State-driven precondition |
| **Domain State Enum** | `public\s+enum\s+([A-Za-z0-9_]+Status)\s*\{` | Account lifecycle state space |
| **GL Accounting Hook** | `journalEntryWritePlatformService\.createJournalEntriesForLoan` | Financial transaction ledger invariant |

---

## Step-by-Step Java Parsing Workflow

1. **Locate Resource & Command Handler:**
   * Find `@Path` in `*ApiResource.java` to define the API endpoint and HTTP method.
   * Identify the corresponding `@PreAuthorize` role to formulate the authorization precondition: `While the user possesses the "<PERMISSION>" authority...`.
2. **Inspect WritePlatformServiceImpl:**
   * Trace execution from API resource into the service implementation.
   * Identify status check preconditions (`loan.isSubmittedAndPendingApproval()`).
   * Identify calculation methods (e.g. `calculateRepaymentSchedule`, `calculateInterest`).
3. **Inspect Validator:**
   * Open the associated `*DataValidator.java`.
   * Extract all `.failWithCode("...")` and `DataValidatorBuilder` checks into **If-Then** Unwanted Behavior clauses.
4. **Inspect Domain Entity:**
   * Open `@Entity` class to locate state transitions (e.g. `loan.status = LoanStatus.ACTIVE.getValue()`).
   * Verify table name (`@Table(name = "m_loan")`) and database columns.
5. **Formulate Bilingual EARS Card:**
   * Assemble the requirement card conforming to the standard template.

---

## Bilingual Output Requirement Card Template

Every extracted requirement must follow this structure:

```markdown
### REQ-[MODULE]-[ACTION]-[NUM]: [عنوان کوتاه توصیفی به زبان فارسی]
* **الگوی EARS:** [Ubiquitous | State-Driven | Event-Driven | Optional Feature | Unwanted Behavior | Complex]
* **EARS Statement:**
  > While <preconditions>, when <trigger>, the <system name> shall <system response>.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  [توضیح کامل سناریوی بانکی، منطق بیزنس و اهداف مالی به زبان فارسی روان]
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If <error condition 1>, then the <system name> shall reject the request and return error code "<CODE_1>".`
  * `If <error condition 2>, then the <system name> shall <error response>.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/.../ClassName.java`
  * **متد اجرایی:** `#methodName()`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize(...)`, `error.msg....`
  * **پایگاه داده و انتیتی‌ها:** جداول `m_...`, انتیتی `@Entity ...`
```

---

## Concrete Example

```markdown
### REQ-LOAN-DISBURSE-001: پرداخت و انتقال وجه وام به حساب مشتری
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While the loan account is in "APPROVED" state, when a disbursement request is submitted with a valid disbursement date, the Fineract Loan Engine shall disburse the approved principal amount, transition the loan status to "ACTIVE", and generate the initial repayment schedule.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  هنگامی که یک پرونده تسهیلات به وضعیت مصوب (APPROVED) می‌رسد، کاربر مجاز شعبه می‌تواند مبلغ تسهیلات را به مشتری پرداخت کند. سیستم فاینراکت موظف است پس از بررسی وضعیت حساب، تاریخ پرداخت و مبلغ، وضعیت پرونده را به فعال (ACTIVE) تغییر دهد، اقساط بازپرداخت را نهایی نموده و سند حسابداری مرتبط با پرداخت وجه از صندوق/بانک به حساب تسهیلات را به صورت خودکار در دفتر کل صادر نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the loan account is not in "APPROVED" state at the time of disbursement, then the Fineract Loan Engine shall reject the disbursement command and return error code "error.msg.loan.not.approved".`
  * `If the disbursement date is prior to the loan approval date, then the Fineract Loan Engine shall reject the command and return error code "error.msg.loan.disbursement.date.cannot.be.before.approved.date".`
  * `If the disbursement amount exceeds the approved principal balance, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.amount.exceeds.approved".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#disburseLoan(Long loanId, JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('DISBURSE_LOAN')")`, `error.msg.loan.not.approved`, `error.msg.loan.disbursement.date.cannot.be.before.approved.date`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan`, جدول `m_loan_transaction`, انتیتی `org.apache.fineract.portfolio.loanaccount.domain.Loan`
```
