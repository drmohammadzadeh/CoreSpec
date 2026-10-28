---
source_url: https://fineract.apache.org/docs/1.17.0-SNAPSHOT#_fsip_fineract_significant_improvement_proposals
title: "FSIP: Fineract Significant Improvement Proposals"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/develop
---

## FSIP: Fineract Significant Improvement Proposals

Fineract Significant Improvement Proposals (FSIPs) are the mechanism the community uses to propose, discuss, and track significant changes to Apache Fineract. Each FSIP follows the pattern **DISCUSS, VOTE, TRACK, CLOSE**.

> [!NOTE]
> See [the Apache Fineract wiki](https://cwiki.apache.org/confluence/display/FINERACT/Fineract+Significant+Improvement+Proposals) for the authoritative, up-to-date list of FSIPs. The proposals below were imported from that wiki.

### FSIP-001: Modular Security Architecture

Adopted by the Community over many months beginning April 2023 and continuing until May 2024 See listserv discussions.

[lists.apache.org/thread/m46dnqwn8lcy9ohhgd5j03yjjsjpq3ny](https://lists.apache.org/thread/m46dnqwn8lcy9ohhgd5j03yjjsjpq3ny)

Clarifications but no objections raised to the need, and progress was undertaken incrementally.

This led to the recognition of the need for a more formal SIP acceptance process.

This SIP is the reason we adopted a more formal process of DISCUSS, VOTE, and TRACK.

#### GOALS

* separate the current security infrastructure as much as possible from Fineractâs core; i. e. make it a custom module
* create the OAuth Client aka Keycloak module as a drop-in replacement for the current security mechanics
* delegate everything authentication/authorization related to 3rd party libs/frameworks/products/services
* re-use 3rd party libs/frameworks/products/services user interfaces and remove corresponding views (e. g. user management) from Fineract web app
* as minimal refactoring as possible in the short/mid term
* keep backwards compatibility for a couple of major releases
* provide good documentation and/or automated tools for migration

#### Non-Goals

* Fineract as a standalone identity server

More details here in Jira ticket 1908.

[FINERACT-1908](https://issues.apache.org/jira/browse/FINERACT-1908)

### FSIP-002: Scarf Data Tracking

Adopted with three binding votes: Jdailey, Javier, Alexandar on May 16, 2024.

Apache Fineract® will use Scarf to gain insights into downloads and users to more effectively understand the population of users and their needs. This will complement our existing data from Apache infra.

Scarf[1] is on a list of approved vendors at Apache [2].
Apache recommends against using Google and approves of Scarf[3]

> "Yes: Scarf has signed a DPA with us, fully supports the GDPR and was added to our privacy terms. It is possible to use their service."

There is a case study covering how Apache Superset uses Scarf.

> "Usage metrics gathered through Scarf provides Apache Superset with valuable insights they can use to drive decision-making. From making more educated decisions about long-term support for older releases to better understanding which installation paths are most common in practice. Apache Superset is able to allocate resources more effectively and ensure their software meets the needs of their users and community."[4]

There is a forever free tier at Scarf that is available as soon as we start, and there are minimal ways to get started. The first way will be to put a pixel in the documentation, on the dockerhub landing page, and on the website. The second approach is to put a forwarding gateway on downloads, e.g. for the binaries downloads. Eventually we may want to consider some level of telemetry data, see this Commit at Sedona [5], but that is more involved and for now, my proposal is to do this in an incremental manner.

We would start with the pixel approach and see what kind of data we get from the free tier. If that looks promising, companies (vendors) or individuals will be asked to split the cost of paying for a base level of Scarf and that data would be accessible to the PMC for the benefit of the project. Benefits to the project would mainly be the ability to know who is using the software (for best understanding needs) and for encouraging contributions by users. (James Dailey )

[2] [privacy.apache.org/policies/privacy-policy-public.html](https://privacy.apache.org/policies/privacy-policy-public.html)
[3] [privacy.apache.org/faq/committers.html](https://privacy.apache.org/faq/committers.html)
[4] [about.scarf.sh/post/scarf-case-study-apache-superset](https://about.scarf.sh/post/scarf-case-study-apache-superset)
[5] [github.com/apache/sedona/pull/1373/commits/19e76e994f53aaa2978d0a98a3aaf9d2427f6f7f](https://github.com/apache/sedona/pull/1373/commits/19e76e994f53aaa2978d0a98a3aaf9d2427f6f7f)

**COMPLETED and RUNNING**

### FSIP-003: Continue Enhancing New Progressive Loan Module to Support Interest-Bearing Loans

Adopted June 17th.

[lists.apache.org/thread/v009fbf3m0s40y613byz2s3b1gppjwz6](https://lists.apache.org/thread/v009fbf3m0s40y613byz2s3b1gppjwz6)

#### Summary

We are proposing to add support for interest-bearing loan products for progressive loan schedule by continuing to develop on the recently merged progressive loan handling changes and moving it into a new externalized *fineract-progressive-loan* module.

These changes are in support of an enterprise customer that has been sponsoring upstream contributions into Fineract to support the migration of its BNPL and installment lending products onto a new loan management system of record.

This new module will aim to re-use existing logic from the legacy loan module by extracting it into separate methods or classes to reduce the complexity and improve the reusability.

The legacy loan module is far too complicated to build these new loan capabilities onto but we also have decided not to build a completely separate and independent loan module that would lead to forked implementations.

Our proposed approach will allow us to deliver a solution that meets the customer requirements while not breaking any existing functionality for the community. We will make substantial progress on the much-needed redesign and refactoring of the loan module and gradually and iteratively over time build out this enhanced loan module to ideally deprecate the legacy loan module.

#### Status

**Under Discussion, Proposed**

#### Who is Involved

Proposal Owner: Edward Cable

Lead Developer(s) & Architects: Adam Saghy and Marta Jankovics

Business Analyst: Bharath Gowda

#### Background/Motivation

The Mifos Initiative has been working with a global enterprise-scale consumer of Fineract to migrate their loan management system of record from a legacy core banking system to one based on Fineract for their BNPL lending portfolio. This customer has sponsored the development of significant functional and non-functional contributions that have been merged upstream into Fineract over the past two years (PostgreSQL/Eclipselink support, Business Date, new Spring Batch module, new reliable event framework, transaction idempotency, downpayment support for multiple disbursals, configurable payment application logic, new transaction types, delinquency bucket tracking, etc).

These upstream contributions have been designed, developed and tested by developers and architects from BaaSFlow along with business analysts and developers from Mifos.

In support of these requirements, the Fineract community has already accepted and merged in enhancements to the current loan module to support the introduction of a progressive loan schedule for multi-disbursal loans enabling fully configurable payment application logic. This new capability was only added to loans without interest. In short, the difference between cumulative and progressive loan schedules (for multiple disbursals) is under the progressive calculation, a second disbursement donât cause previous disbursements and transactions to be recalculated. Legacy cumulative loan calculation was designed for single disbursement installment loans. Multiple disbursement loans are now better supported with progressive loan calculation whereby additional disbursements will only be spread across future installment and not affect previous ones.

* **Cumulative** (by default, legacy): all of the installments are used to split the newly disbursed amount (recalculating already executed disbursements and transactions)
* **Progressive** Only the future installments to be used to split the newly disbursed amount.

More detailed explanation below.

The customer would now like to support interest-bearing loans using Fineract so that is why we are submitting this proposal to outline the proposed approach to continue enhancing the loan module to support interest-bearing loans on top of the progressive loan calculation.

The proposal will not only support the requirements of the customer but make substantial progress on addressing the technical debt and overwhelming size and complexity of the current loan module which presents a highly steep learning curve for new and existing developers and is difficult to test, and doesnât support all the standard calculations the financial services sector expects.

#### Goals and Exclusions

* Extend the newly enhanced progressive loan module to support interest-bearing loan products
* Improve the performance, maintainability and ease of developing around loan module by developing an externalized loan module that has new capabilities but aims to re-use existing business logic and optimized code - this in turn would reduce technical debt.
* Continue externalization of Fineract services/packages into modules as done previously by moving away from all-in-one fineract-provider to fineract-core, fineract-loan, fineract-investor and now fineract-progressive-loan
* Gradually deprecate the legacy loan module as the progressive loan module gets more capabilities introduced to it.
* Proposed changes in progressive loan module will fix the errors that have been identified with EMI calculations where supposed configurable fields in EMI calculation formula are actually hard-coded and due to the PMT formula not giving precise EMI, resulting in slight differences in the last installment.
* Initial phases of development wonât create a new loan module that is at 100% parity with the legacy loan module including no support for these enhancements to existing cumulative loan schedule handling.
* New approach wonât support the entire wide range of configurations available for loans currently - initially implementing a narrow set of features and step by step adding more over time.

#### Change Proposed

The changes proposed are the following:

* Extract the already created and already merged progressive loan-related changes into a new module (fineract-progressive-loan).
* No planned new APIs but additional configurations might be added (i.e. additional advanced payment adjustment type for configuration of interest recalculation, etc.
* New capabilities introduced into this module will include:
* Initial configuration will be for the progressive loan to support Declining balance interest strategy, with daily interest calculation and interest recalculation which modifies the last installment of the loan based on whether there were early or late repayments.

We will adopt an approach that builds the progressive loan as a separate module but in a step-by-step manner either: have a new, redesigned better implementation for existing or new features or examine using existing logic when appropriate.

If functionality should behave or work differently, we will attempt to refactor existing logic without breaking it so it could become common logic for the legacy and progressive loan modules. Whenever reusing something, it will first be simplified to avoid multi-conditional behavior and complexity.

Through this approach, we will analyze and touch already working features as well such as disbursements, repayments, etc. Based on our analysis, some features will be reworked partially or fully in the new loan module or existing logic from the legacy module might be extracted into separate methods or classes to reduce the complexity and improve the reusability

This will allow us to ensure the new loan can focus on meeting the actual requirements of the customer without being burdened by the near impossible task to support everything. However we will still be able to improve the common logic without breaking how it works as we do this gradually rework, refactor and redesign.

We fully understand the current loan module is too complex and too fragmented making it hard to work with and hard to understand how it works and that it does need to be refactored and redesigned. By doing this incrementally and right-sizing the refactoring, we can do it in the right way by first introducing these changes for the progressive loan to see how well it works and performs and then we can either continue adding capability to the new loan module or introduce changes to the legacy loan module. Ideally over time we could deprecate the legacy module once the newly built progressive loan module is closer to functional parity.

#### Alternatives Considered

We considered the following alternative approaches:

* Build the additional interest-bearing capabilities directly onto the existing loan module
* Create a completely separate brand new loan module without utilizing any logic/design/code of the existing loan module.

Because of the overwhelming size and complexity of the current loan module (7000+ lines of code) and the high amount of technical debt, we chose not to build this directly onto the legacy module.

We chose not to go with a completely independent new loan module that doesnât utilize any of the existing business logic/calculations because we recognize that we canât have a forked loan module and the legacy loan is still used widely so we didnât want to break anything for current users at the moment and also have the ability to gradually add existing capabilities on the newly enhanced module

Phases of work

* May 2024 - Design of Proposed Changes and creation of tickets for proposed development
* June 2024 - October 2024 - Development & Testing or Proposed Changes with iterative points to check on performance and progress of re-using existing logic
* Nov 2024 - roadmap and backlog for community to pick up and address capabilities to be added to new progressive loan module.

We will later share a wiki page which outlines the loan products that are supported and documents the gaps between the new progressive loan module and the existing legacy loan module.

#### Additional Information

**Cumulative vs Progressive Loan Handling**

*Previously Fineract (as designed primarily for fixed term installment lending) only supported a cumulative loan schedule and disbursement strategy where it didnât matter when something was disbursed, and the total amount disbursed was split across all installments. So in a loan with multiple disbursements, when new amounts were disbursed, Fineract would recalculate and regenerate the schedule for the whole disbursement amount, affecting previously created disbursements and transactions.*

*This behavior wasnât appropriate for line of credit type lending with multiple disbursements to support wallets, digital lending, BNPL, etc.. Support is now in place for a progressive loan strategy where the new disbursement amount is only distributed to future installments and the repayment schedule or installments that happened before the disbursement date are not recalculated.*

Features enabled by Progressive Loan Calculation

* **Progressive Loan Calculation** - Legacy cumulative loan calculation was designed for single disbursement installment loans. Multiple disbursement loans are now better supported with progressive loan calculation whereby additional disbursements will only be spread across future installment and not affect previous ones.
* **Configurable Payment Application Logic** - Previously in order to adjust the sequence against which a repayment is applied against the portions of a loan, penalty, fees, interest, principal one had to modify the source code. Now this is fully configurable from the UI with a drag and drop menu to modify the payment application logic for any transaction type.
* **Vertical Loan Processing** - Underpinning this powerful new feature was the introduction of horizontal vs vertical loan processing. Legacy behavior was horizontal processing whereby a transaction is applied âhorizontallyâ across the entire scope of an installment, against each portion one by one, only supporting payment application logic to be grouped by due type. With the new vertical loan processing, payments are now allocated âverticallyâ through the entire repayment schedule so the payment can be applied to all penalty portions of any due type across all installments.

### FSIP-004: Cucumber Testing Framework

[lists.apache.org/thread/52082h1ps1hyo59lwogk5otn0ccyxv1f](https://lists.apache.org/thread/52082h1ps1hyo59lwogk5otn0ccyxv1f)

Supported by: Adam, Aleksandar , Arnold +1s

**Summary: A new Testing Framework that complements and is expected to replace the existing integration testing framework was adopted by the community.**

NOTE on June 14, 2024

Devs - I believe that the cucumber test framework and approach are now accepted by the Community as per this discussion, and while this didn’t go through a formal vote, I think that the discussion was sufficient and more formality on this is not needed. So, now there needs to be a wiki page or a set of instructions in the documentation for using and writing additional cucumber tests. That is needed at the same time as the acceptance of the tests. There will be people confused by our overall testing strategy. We have a collection of integration tests, that don’t cover all of the APIs, are probably inadequate, and which take a long time to run, and now, we also have Cucumber tests. Are we keeping the existing integration tests? Or are we going to sunset them at some point? Should people count on the integration tests? How should a dev set up the cucumber tests to run? Is there a gradle task? Are all dependencies included in the code? James Dailey

### FSIP-005: New Command Processing Infrastructure

#### Summary

We are proposing to develop a modular and performant command processing component in parallel to the currently available one in Fineract and gradually migrate REST API controllers/resource classes, command handlers and where necessary business logic services. These changes will improve the developer experience (speed) significantly by (re-)introducing proper Class types where we currently use Strings as a common denominator to process various command payloads. Having proper type information is a requirement to delegate all JSON related de-/serialization to the Jackson framework and ultimately get rid of all handcrafted JSON parsing boilerplate code (ca. 20% of the overall code base). With that we’ll regain error checking at compile time (vs. tedious bug hunting at runtime, because of e.g. a simple refactoring of a command attribute). We are expecting visible performance gains by using Jackson and having a simpler command processing pipeline that has configurable performance levels (sync, async, non-blocking).

#### Status

Under Development

#### Who is Involved

* Aleksandar Vidakovic (proposal owner, lead developer)
* Victor Romero (reviewer)
* Adam Saghy (reviewer)

#### Background/Motivation

Fineract accumulated some technical debt over the years. One area that is implicated is type-safety of internal and external facing APIs, the most prominent of which is Fineract’s REST API. In general the package layout of the project reflects a more or less classic layered architecture (REST API, data transfer/value objects, business logic services, storage/repositories). The project predates some of the more modern frameworks and best practices that are available today and on occasions the data structures that are exchanged offer some challenges (e.g. generic types). Fineract’s code base reflects that, especially where JSON de-/serialization is involved. Nowadays, this task would be simply delegated to the Jackson framework, but when Fineract (Mifos) started the decision was made to use Google’s GSON library and create handcrafted helper classes to deal with JSON parsing. While this provided a lot of flexibility this approach had some downsides:

* the lowest common denominator is the string type (aka JSON blob); this is where we lose the type information
* the strings are transformed into JSON Objects; a little bit better than raw strings, but barely more than a hash map
* a ton of "magic" strings are needed to get/set values
* this approach makes refactoring unnecessarily more difficult
* to be able to serve an OpenAPI descriptor (as JSON and YAML) we had to re-introduce the type information at the REST API level with dummy classes that contain only the specified attributes; those classes are only used with the Swagger annotations and no were else
* some developers skipped the layered architecture and found it too tedious to maintain DTOs and JSON helper classes, and as a result just passed JSONObjects right to the business logic layer
* now the business logic is unnecessarily aware of how Fineract communicates to the outside world and makes replacing/enhancing the communication protocol (e.g. with GRPC) pretty much impossible

The list doesn’t end here, but in the end things boil down to two main points:

* poor developer experience: boilerplate code and missing type safety cost more time
* bugs: the more code the more likely errors get introduced, especially when type safety is missing and we have to rely on runtime errors (vs. compile time).

There has been already some preparatory work done concerning type safety, but until now we avoided dealing with the real source of this issue. Fineract’s architectures devises read from write requests ("CQRS", [martinfowler.com/bliki/CQRS.html](https://martinfowler.com/bliki/CQRS.html)) for improved scalability.

The read requests are not that problematic, but all write requests pass through a component/service that is called "SynchronousCommandProcessingService. As the name suggests the execution of business logic is synchronous (mostly) due to this part of the architecture. This is not necessarily a problem (not immediately at least), but it’s nevertheless a central bottleneck in the system. Even more important: this service is responsible to route incoming commands to their respective handler classes which in turn execute functions on one or more business logic services. The payload of these commands are obviously not always the same…​ which is the main reason why we decided to use the lowest common denominator to be able to handle these various types and rendered all payloads as strings. This compromise bubbles now up in the REST API and the business logic layers (and actually everything in between).

Over the years we’ve also added additional features (e.g. idempotency guarantees for incoming write requests) that make it now very hard to reason about the execution flow. Testing the performance impact of such additions to the critical execution path even can’t be properly measured. Note: the current implementation of idempotency relies on database lookups (quite often, for each incoming request) and none of those queries are cached. If we wanted to store already processed requests (IDs) in a faster system (let’s Redis) then this can’t be done without major refactoring.

In conclusion, if we really want to fix those issues that are not only cosmetic and affect the performance and the developer experience equally then we urgently need to fix the way how we process write requests aka commands.

#### Goals

* new command processing will run independently next to the legacy mechanics
* self contained
* fully tested
* ensure that the REST API is 100% backward compatible
* try to contain the migration and make it as easy as possible for the community to integrate those changes
* introduce types where needed and migrate the (old) JAX-RS REST resource classes to Spring Web MVC (better performance and better test-ability)
* introduce DTOs if not already available and make sure if they exist that they are not outdated
* assemble one DTO as command payload from all incoming REST API parameters (headers, query/path parameters, request bodies)
* annotate attributes in the DTOs with Jakarta Validation annotations to enforce constraints on their values
* wired REST API to the new command processing, one service at a time/pull request
* take a non-critical service (like document management) and migrate it to the new command processing mechanics from top (REST API) to bottom (business logic service)
* refactor command handlers to new internal API
* make sure that the business service logic classes/functions take only one DTO request input parameter (aka don’t let a function have 12 input parameters of type string…​)
* when all integration tests run successfully then remove all legacy boilerplate code that is not used anymore
* make an ordered list of modules/features (easiest, lowest hanging fruit first)
* maintain at least the same performance as the current implementation
* optional: improve performance if it can be done in a reasonable time frame
* optional: improve resilience if it can be done in a reasonable time frame

#### Exclusions

* current command processing will stay untouched, will run independently of new infrastructure
* don’t try cleaning up the storage layer; that’s a separate effort for later (type safe queries, query performance, clean entity classes)
* doesn’t need to be optimized for speed immediately
* no changes in the integration tests

#### Change Proposed

##### Command Wrapper

Class contains some generic attributes like:

* tenant ID
* username(s)
* timestamp(s)
* idempotency key
* error message (if available)
* state of execution (when stored to the database)

The actual payload (aka command input parameters) are defined as a generic parameter. It is expected that the modules implement classes that introduce the payload types and inherit from the abstract command class.

##### Command Processing Service

* synchronously (required): this is pretty much as we do right now (use virtual threads optionally)
* asynchronously (optional): with executor service and futures (use virtual threads optionally)
* non-blocking (optional): high performance LMAX Disruptor non-blocking implementation

These different performance level implementations need to be absolute drop-in replacements (for each other). It is expected that more performant implementations need more testing due to increased complexity and possible unforseen side effects. In case any problems show up we can always roll back to the required default implementation (synchronous).

> [!NOTE]
> we should consider providing a command processing implementation based on Apache Camel once this concept is approved and we migrated already a couple of services. They are specialized for exactly this kind of use cases and have more dedicated people working on it’s implementation. Could give more flexibility without us needing to maintain code.

##### References to users

Keep things lightweight and only reference users by their user names.

##### Critical patch of execution

Again, keep things as lightweight as possible and avoid any database operations during the command processing.

#### Alternatives Considered

We could just opt to use an existing framework like Apache Camel which provides all necessary building parts to implement and efficient command processing infrastructure. We still recommend starting with a standalone solution that is properly abstracted with interfaces. Once the basic mechanics and the performance are tested we can still opt to provide an alternative implementation (aka command processing plugin) that is based on Apache Camel. That way we avoid any vendor (framework) lock-in.

#### Phases of work

* Jan 12-15 2025: First prototype and pull request available
* Jan 2025: community vote
* Jan 2025: pick an example Fineract service/feature (e.g. document management) that is less used than others and onboard devs
* Feb 2025: review the results, lessons learned, performance improvement (or degradation)
* Feb 2025: community vote if this is a viable approach; if yes, prioritize the migration of Fineract’s services/features starting with the least important (Fineract has approximately 50 features/services/"modules" that would need to be migrated)
* Feb 2026: added audit capabilities
* Mar 2026: tentative date for completion of migration of 20 modules (currently ca. 10 modules are migrated or close to)

> [!NOTE]
> the actual refactoring of a feature/service for type-safety will be done with the following steps

* move from JAX-RS REST resources to Spring Web MVC REST controllers; this is a low hanging fruit and involves mostly changing some annotations and occasionally input parameters; this will give us better (unit) testability of the REST API layer; also: Spring Web MVC is a first class citizen in the Spring ecosystem, adds more developer convenience and probably performance
* go through all function that are presented in the REST controller, pick those that have a request body (i.e. those handling PUT, POST requests), replace the JSON string parameter with a proper Java Class and typed attributes. NOTE: the Swagger API annotations and the associated dummy classes can help here if no (or outdated) DTOs (package "data") exist; use this information and create or update the DTOs and replace the JSON string body parameter with those DTO classes
* wire the incoming typed request body values to the new command processing engine (detailed instructions will be given in a proof of concept PR)
* migrate any existing command handlers related to the service/feature to the new command processing engine
* make sure that the business logic services accept only the DTOs that were previously defined in the REST API layer; no references to JSON string blobs or JSON objects should be left on business logic services and their functions; functions have ideally one input parameter that is a DTO class with one or more attributes; do not use (multiple) primitive types as input for those functions (very hard to refactor, very hard to interpret when you have multiple primitive type parameters of the same type in sequence)
* do not change any of the logic (feature creep)
* do not try fix any of the technical debt in the storage layer (feature creep)

### FSIP-006: Type Safe Native SQL Queries

#### Summary

**NOTE: THIS IS WORK IN PROGRESS!**

We are proposing to introduce type safe SQL query generation by using the QueryDSL library. Moving away from string-based SQL native queries, this change aims to leverage QueryDSL’s generated query types to eliminate runtime errors from malformed queries, improve maintainability through a fluent Java API, and enable the safe use of advanced database features while maintaining compile-time validation. The integration will focus on new query development and iterative refactoring of high-change-frequency existing queries.

#### Status

Under Discussion, Proposed

#### Who is Involved

* Aleksandar Vidakovic (proposal owner, lead developer)
* TBD (reviewer)

#### Background/Motivation

Apache Fineract has started out to use JPA/Jakarta Persistence to abstract database specific details. Over the years developers started to use native SQL queries mostly for performance reasons. While this was and is a valid strategy for critical path and performance sensitive components this approach has a major drawback. The queries are usually written by using string variables and/or related classes (StringBuffer, StringBuilder, custom utility classes like SqlQueryBuilder). The problem here is that developers tried various strategies to format the queries in a way to be easily readable. That effort is pretty much in vain, because we have automated code formatting and linting in place which affects the "layout" of these SQL query variables in a major way. The code formatter usually splits up the string into multiple pieces and distributes the parts over multiple lines to follow the line length constraints we defined in the formatting rules. Obviously that doesn’t result in particularly readable code/queries. A far worse problem than the readability of this kind of code is that any changes/refactorings to the underlying data structures (database tables, mapping entity classes) is not caught by any of the refactoring tools or by the Java compiler. In case we are referencing tables, columns in the query that are not there anymore or renamed we only find out during runtime. Additionally developers started to use database specific non-SQL standard functions (e.g. variations of "current date") that prevented us for a long time to upgrade even the same database product (MySQL) from an old version (5.7) to a more modern one (8.x) let alone introduce another database system like PostgreSQL. We kind of solved these issues, but introduced custom code to abstract away e.g. the use of database specific functions. Introducing JPA/Jakarta Persistence is not a solution here, because of the overhead for translating OQL to SQL and the whole entity mapping "magic". QueryDSL as a solution hits a sweet spot, because it contains an annotation based code generator for all database related metadata (column types to Java types etc.) and provides a Java DSL (aka fluent API) that resemble SQL statements close enough. QueryDSL gives us syntactic and type safety and because everything under the hood is a prepared statement the danger of SQL injection attacks is greatly reused by design (and not retro-actively by trying to "escape" dangerous query values).

#### Goals

* **Enhance type safety:** Shift query validation from runtime to compile-time by generating query types that reflect the database schema, eliminating a class of runtime errors.
* **Improve maintainability and readability:** Replace concatenated SQL strings with a fluent, Java-based API that is easier to understand, refactor, and version control.
* **Maintain performance:** Ensure the generated SQL queries are efficient and performant, comparable to hand-tuned native SQL.
* **Standardize Query Construction:** Provide a consistent, modern approach for building both simple and complex SQL queries across the community.

#### Exclusions

* **Abandoning JPA/Jakarta Persistence:** TBD
* **Mandatory for all SQL:** sometimes it’s easy enough to just use the "magic" function name translations of Spring Data’s repository interfaces.

#### Change Proposed

We will integrate QueryDSL SQL into the project through the following steps:

1. Add required dependencies (Spring Data JDBC, QueryDSL/Openfeign QueryDSL, Infobip QueryDSL starter)
2. Configure code generation in Gradle build scripts
3. Prioritize packages/modules for refactoring
4. Do a first migration on a low impact package/module

#### Alternatives Considered

* **JOOQ:** TBD
* **Multi-Line Strings:** TBD

#### Phases of work

* Mar 2026: First prototype and pull request available
* ??? 2026: community vote
* …​

### FSIP-007: Traditional Merge Strategy

#### Summary

When merging a PR into `develop` (our main integration branch), use a **traditional merge** **commit** instead of squashing, rebasing, and fast-forwarding.

[Discussion thread](https://lists.apache.org/thread/3569vo83c75yvm8q9xtord2n70gf5oz1)

#### Status

Accepted. [Vote thread](https://lists.apache.org/thread/5qg1xpjpspfdpmy6n0h2kbkqon7twsxk). [Vote result](https://lists.apache.org/thread/gpf9clbz4l0cdmvo45sg9b986fvns9do).

#### Who is Involved

* Adam Monsen (original proposal)
* Krishna Mewara (reviewer)
* Adam Saghy (reviewer)
* james dailey (reviewer)

#### Background/Motivation

The original motivation was supporting verifiable signed git commits. This was [proposed in 2025](https://issues.apache.org/jira/browse/FINERACT-2177) and [adopted in 2026](https://github.com/apache/fineract/pull/5431). Upon investigation, it was determined the current merge strategy (squash, rebase, fast-forward) precludes signed commits except in special situations (done locally or when squash/rebase were unnecessary, e.g. one commit was created and PR was merged before any other commits on `develop` were added).

Additional motivations: preserve more history, preserve more developer intent.

*When I’m looking at commit history, I want to be able to know exactly what happened, when, by whom, and why. I want to see branch start & end points, when changes were made and unmade. Yes it means more commits. Thankfully Git is built to handle many, many commits. It has excellent filtering to, for example, examine simplified history.*

— [Adam Monsen](https://lists.apache.org/thread/3569vo83c75yvm8q9xtord2n70gf5oz1)

#### Goals and Exclusions

Continue to use GitHub for reviewing and merging PRs as well as local tooling (e.g. `git merge` on the command line).

Encourage developers to use as few or as many commits as they choose in their PRs, with the intent to most clearly communicate the reviewable progress of their work during PR review and for posterity. This means rebasing locally, adding/removing commits, and force-pushing are all still allowed, although these should be used only as necessary/helpful (e.g. when a new commit on `develop` assists the PR or to correct noise/mistakes). If force-push is used, communicate it thoughtfully.

Encourage developers to leave commits as-is/un-squashed when updating PRs with new changes. It’s helpful for posterity / intent forensics to see progress along the way, changes reversed, etc. Ideally with commit log detail about the "why" for the changes, summaries of our discussions leading to the changes, ideas/plans for future changes, etc.

#### Change Proposed

Standardize on and manually enforce traditional git merge commits for merging approved PRs to the `develop` branch. When merging a PR, do not enforce squash/rebase/fast-forward.

For examining history, document and practice use of git history simplification strategies such as

```java
git log --first-parent develop
git log --no-merges
git log --max-parents=1
```

or simply viewing [the commits list on github](https://github.com/apache/fineract/commits/develop/).

After a ~one week bake-in period, [enforce new strategy](https://github.com/apache/infrastructure-asfyaml#merge-buttons) with `.asf.yaml`:

```java
# must be added to existing github section
# (do not create a new one)
github:
  enabled_merge_buttons:
    merge: true
    squash: false
    rebase: false
  protected_branches:
Â  Â  develop:
Â  Â  Â  required_linear_history: false
Â  Â  Â  required_signatures: true
  Â  Â  required_conversation_resolution: true
```

#### Alternatives Considered

Continue to enforce squash/rebase/fast-forward, but do so locally only, so committer’s signature is valid. Abandoned as this would leave behind useless merge commit "triangles" in the history.

#### Phases of work

This is effectively a process change, hence, mostly follows the simple/default FSIP pattern.

1. DISCUSS
2. VOTE
3. TRACK (update community, update docs, remind ourselves via dev list, chat, PR comments)
4. CLOSE

### FSIP-008: Introducing SOLID Principles To Decouple Modules

#### Summary

> [!NOTE]
> this proposal was called "Event Driven Architecture - EDA" in previous discussions. **THIS IS WORK IN PROGRESS!**

We are proposing to introduce the use of SOLID principles in the current Fineract code base to avoid direct references between services (and sometimes low level storage related/repository classes).

Quick reminder and overview what the 5 acronyms mean:

| Principle |
| --- |
| Meaning |
| Benefit |
| **S*ingle *R*esponsibility (*SRP**) |
| A class should have only **one reason** to change, meaning it should have a **single responsibility** |
| Maintainability, limited "blast radius" of changes, code is easier to understand |
| **O*pen/*C*losed (*OCP**) |
| Classes should be **open** for **extension** but **closed** for **modification** |
| Reduces risk of bugs when adding new features, as existing, tested code isn’t altered |
| **L*iskov *S*ubstitution (*LSP**) |
| Objects of a **super-class** should be **replaceable** with objects of its **sub-classes** without breaking the application (see also current custom modules approach) |
| Ensures reliability and correctness in inheritance hierarchies, promoting code re-usability |
| **I*nterface *S*egregation (*ISP**) |
| Classes/services should not be forced to depend on interfaces they do not use; it’s better to have many specific interfaces than one general-purpose interface |
| Reduces coupling and prevents classes from being "fat" with methods they don’t need |
| **D*ependency *I*nversion (*DIP**) |
| **High-level modules** should not depend on **low-level modules**; both should depend on **abstractions**. |
| Decouples components, making the system more modular, testable, and resilient to change |

Apply these principles not blindly for the sake of the principles. Use some practical judgement to decide if these principles really help in a given case or if it’s maybe better to just leave the code as is (for now) and/or apply a different strategy.

#### Status

Under Discussion, Proposed, GSoC2026

#### Who is Involved

* Aleksandar Vidakovic (proposal owner, lead developer)
* TBD (reviewer)

#### Background/Motivation

The current code-base has evolved over several years/decades. As a result, the system accumulated some technical debt of. The biggest group of issues is probably the lack of and enforcement of domain boundaries and the resulting direct references of services across different domains, but also breaking the rules of the layered architecture (e.g. by using storage related repository classes of one domain in another domain’s business service implementation). Initially Fineract/MifosX started out as a classic layered architecture. The result of this is:

* **Impact Radius:** A change in one module requires changes in modules that are in a different domain/module/package/feature.
* **Re-usability:** It is difficult to reuse existing code in other contexts because the specific implementations drag in any transitive dependencies.
* **Isolated Tests:** Heavy reliance on global state and static calls makes unit testing difficult or impossible without extensive mocking frameworks.
* **Extensibility:** If we don’t proper demarcation lines between the modules then the replacement/adoption of these modules/functionalities for different/custom contexts is difficult if not impossible

#### Goals

* **Improve maintainability:** local changes (in a specific domain) won’t have a global blast radius.
* **Improve Testability:** Isolated tests, much simplified configuration/dependency injection.
* **Reduce cognitive load:** Specific classes should become smaller (aka no "kitchen sink" dependency injection scenarios) and easier to understand.
* **Enable extensibility:** avoid "open heart" surgery on existing code for customizations and instead make components easily replaceable.
* **Standardization:** Create a toolbox of common solutions instead of getting too "creative"; should make code reviews a lot easier.

#### Exclusions

* **Complete rewrite:** TBD
* **Legacy works:** TBD
* **New framework:** TBD
* **Dogmatism:** TBD

#### Change Proposed

* **Adapter pattern:** TBD
* **Application event publisher (EDA, optional):** TBD
* **Internal commands (CQRS, optional):** TBD

#### Alternatives Considered

##### Continues with current practice

TBD

##### Complete rewrite

TBD

#### Phases of work

* March 2026: Minimal documentation and examples available
* ??? 2026: community vote
* ??? 2026: pick worthwhile package/feature/module, should be standalone after refactoring
* ??? 2026: review the results, lessons learned

### FSIP-009: Standardize on PostgreSQL

#### Summary

Only support Postgres. Remove MariaDB and MySQL support.

This is a SIGNIFICANT improvement with huge potential gain and some risks to mitigate.

This proposal is *only* **our agreement on a single database**; to proceed and remove code and documentation related specifically to MariaDB and MySQL. With this proposal we will make an effort but **we are not committing** to migration guides, scripts, tests, tools, wizards, and case studies easing database migrations. The community is strongly encouraged to **gather real-world data**, to share and discuss this proposal with all users, encouraging them to create or sponsor creation of these critically important migration materials.

[Discussion thread](https://lists.apache.org/thread/5byvzd2v9czcoh6501r9870cb2hbz96w). [Further discussion](https://lists.apache.org/thread/25dg2t7oggvb2c31sow60mqcf1xj4qlz).

#### Status

Accepted. [Vote thread.](https://lists.apache.org/thread/f2kqjbw5rcopzcnfr0w461wxq8do727j) [Vote result](https://lists.apache.org/thread/2lzgy7pkxf2fr6vd3p6owd3xwn0zxfc2).

#### Who is Involved

* Adam Saghy ( [original proposal](https://lists.apache.org/thread/5byvzd2v9czcoh6501r9870cb2hbz96w) , risk assessment)
* Nidhi Bhawari (reviewer)
* Bharath Gowda (reviewer)
* Tito Mari Francis EscaÃ±o (reviewer)
* Ambika (reviewer)
* Awasum Yannick (reviewer, risk assessment)
* Vignesh E (reviewer)
* Paul Christison (reviewer)
* Adam Monsen (FSIP author, reviewer)
* Edward Kang (reviewer)
* Victor Manual Romero Rodriguez (reviewer, risk assessment)
* james dailey (reviewer)
* Attila Budai (reviewer)
* Aleksandar Vidakovic (reviewer)
* Aman Mittal (reviewer)
* Mohammed Saifulhuq (reviewer)
* Jose Alberto Hernandez (reviewer)

#### Background/Motivation

* Speed up development, simplify maintenance
  
  
  
  
  
  * support one SQL flavor only
  * less edge/corner cases to manage
  * more reliable testing
  * faster CI build
* Leverage Postgres-specific features
  
  
  
  
  
  * sequences / identity columns for primary keys
  * native table partitioning
  * safer and more efficient transaction integrity support
  * more advanced indexing options
* Improve security

#### Goals and Exclusions

* Consolidate all relational database storage logic to work with Postgres only.
* Inform community and provide hints and tips for deployments needing to migrate to Postgres.
* Encourage entire community (especially all users: banks, vendors, and paid support orgs) to write or sponsor MariaDB/MySQL to Postgres migration guides, scripts, tests, tools, wizards, case studies, etc.
* We recognize this is a major improvement *not without risk* . See [comments by Victor and others in the discussion thread](https://lists.apache.org/thread/5byvzd2v9czcoh6501r9870cb2hbz96w) about anticipated risk. We commit to mitigating the risk as much as possible while we commit ourselves to making difficult, informed, and courageous choices on how best to maintain Fineract.

#### Change Proposed

Remove code and documentation related specifically to MariaDB and MySQL.

Best effort migration support only. Volunteers, users, banks, vendors, and paid support orgs are expected to create or sponsor creation of anything useful for deployments needing to migrate.

#### Alternatives Considered

None.

#### Phases of work

1. DISCUSS
2. VOTE
3. TRACK
4. CLOSE

### FSIP-010: (Revenue-based) Working Capital Loan product

**Status:** Draft
**Author(s):** Adam Saghy, Bharath Gowda, Mihaly Dallos
**Created:** April 2026

#### Summary

This proposal introduces a new loan product type in Apache Fineract tailored for small and medium-sized merchants seeking working capital. Unlike traditional installment-based loan products, this product ties repayment dynamically to the borrower’s ongoing revenue stream, offering a transparent, flexible, and merchant-friendly financing model that diverges significantly from Fineract’s existing loan product capabilities.

#### Motivation / Business Case

Small and medium-sized merchants regularly face cash flow constraints driven by the seasonal or unpredictable nature of their sales cycles. Traditional loan products with fixed monthly installments create financial hardship during low-revenue periods while failing to capitalize on high-revenue periods.

A **Revenue-Based Working Capital Loan** closes this gap by:

* Basing loan eligibility and sizing on the merchant’s **proven transaction and sales history** , rather than traditional credit scoring
* Introducing a **single transparent fixed fee** agreed at origination, as an alternative to a periodic interest-based cost structure
* Adjusting repayment amounts **proportionally to incoming revenue** , so repayments naturally slow down or accelerate with business performance
* Removing the rigidity of fixed payment schedules and fixed maturity dates
* Supporting loan terms ranging from a few months up to **2â3 years**

#### Proposed Solution

##### New Loan Product Type: Working Capital Loan

A new dedicated loan product configuration is proposed, distinguished from existing Fineract loan products by the following pillars:

##### Pillar 1 â Fixed Fee (Non-Interest Cost of Borrowing)

* The cost of borrowing is expressed as a **single upfront flat fee** , determined at loan origination
* No periodic interest charges or APR-based amortization schedule
* The fee remains constant regardless of repayment speed

##### Pillar 2 â Revenue-Based Repayment

* Repayments are computed as a **configurable fixed percentage of the borrower’s periodic revenue**
* Repayment amounts are inherently variable, automatically rising with higher revenue and reducing during slower periods
* An API must be designed and implemented to support **modification of the repayment percentage** during the loan lifecycle

##### Pillar 3 â Open-Ended Loan Term

* No fixed maturity date is set at origination
* The loan concludes once the total outstanding balance (principal + fixed fee) is fully settled
* This requires a new approach to **Effective Interest Rate (EIR) calculation** , as the standard schedule-based EIR method is incompatible with a variable repayment timeline

##### Pillar 4 â Minimum Repayment Checkpoints

* A minimum repayment threshold must be satisfied within defined review windows (e.g., X% of outstanding balance every N days)
* Failure to meet the threshold triggers **delinquency and collections workflows**
* Requires enhancements to existing **collections programs** such as Breathing Space and Re-Age to support this product’s specific checkpoint-based delinquency model

##### Pillar 5 â Flexible Early Settlement

* Full early repayment is supported at any time without additional penalty
* Requires **credit balance refund** support and **chargeback handling**

#### Key Technical Components

##### Loan Product Configuration Parameters

| **Parameter** |
| --- |
| **Description** |
| repaymentPercentage |
| % of merchant revenue deducted per repayment event |
| fixedFee |
| Single flat charge applied at origination |
| minRepaymentThreshold |
| Minimum % of outstanding balance per checkpoint |
| maxLoanAmountFactor |
| Multiplier applied against historical revenue for sizing |

##### EIR Calculation Engine

* EIR is **estimated at origination** using projected repayment timelines based on historical revenue
* **Actual EIR is recalculated dynamically** as real repayments are received, compared against initial disclosure
* A dedicated **batch job foundation** supports this ongoing recalculation
* EIR breach management logic handles scenarios where actual EIR diverges materially from disclosed EIR

##### Collections & Delinquency

* Delinquency rules are checkpoint-based, not missed-installment-based
* Extensions of existing collections programs adapted for this product model

#### Impact on Existing Fineract Modules

| **Module** |
| --- |
| **Nature of Impact** |
| Loan Product |
| New product type flag and configuration schema |
| Repayment Schedule |
| Variable/event-driven schedule engine |
| EIR Calculation |
| New variable-term EIR method + batch recalculation |
| Accounting |
| New transaction types for revenue-based repayment events |
| Collections |
| Checkpoint-based delinquency triggers and program extensions |

#### Out of Scope

* Automated underwriting and eligibility scoring engine
* Direct integration with payment processors or transaction platforms
* Merchant-facing dashboards or portals

### FSIP-011: Implement the "Q" in CQRS

#### Summary

**NOTE: THIS IS WORK IN PROGRESS!**

TBD.

#### Status

Under Discussion, Proposed

#### Who is Involved

* Aleksandar Vidakovic (proposal owner, lead developer)
* TBD (reviewer)

#### Background/Motivation

TBD.

#### Goals

* **Standardize Query:** TBD.

#### Exclusions

#### Change Proposed

We will integrate QueryDSL SQL into the project through the following steps:

1. TBD
2. TBD
3. …​

#### Alternatives Considered

* TBD
* …​

#### Phases of work

* July 2026: First prototype and pull request available
* ??? 2026: community vote
* …​

### FSIP-012: Event-driven architecture for modular design

#### Summary

Fineract’s feature modules import each other’s internal classes directly: loan reads
savings entities, savings calls accounting services, accounting depends on organisation
repositories. Two shared modules already exist to prevent this — `fineract-core` (read-only
contracts) and `fineract-command` (write-side commands and events) — but nothing enforces
their use, so the boundary has eroded. We propose to make those two modules the only
permitted cross-feature dependency: reads cross a boundary as a `fineract-core` interface
returning a DTO, writes cross as a `fineract-command` command or domain event. Every direct
feature-to-feature import is migrated to one of those two mechanisms, in risk order, and an
ArchUnit rule is activated in CI to keep the boundary from eroding again. A Spring Modulith
boundary scanner already exists and reports the current violation set per module, giving a
before/after count for each phase. The REST API and integration tests stay unchanged
throughout.

#### Status

Under Development

#### Who is involved

* Mansi Maurya (proposal owner, lead developer)
* Aleksandar Vidakovic (reviewer)

#### Background / Motivation

The package layout reflects a layered architecture (REST, DTOs, services, repositories), but
the feature modules are not isolated from one another. Over the years, services and
repositories from one feature have been imported directly into others, with no rule to stop
it. `fineract-core` and `fineract-command` exist, but using them is optional; a developer can
import another feature’s repository and the build still passes.

The concrete cost:

* **Refactoring is unsafe.** Changing an internal class in one feature can silently break a
  consumer in an unrelated module, surfacing only at test or runtime.
* **Ownership is diffuse.** When several features import the same repository, adding a field,
  changing a query, or deprecating a method turns into a multi-team negotiation.
* **Isolated testing is impractical.** Unit-testing one service pulls in the transitive
  dependency graph of everything it imports.
* **Event-driven execution is blocked.** Direct synchronous calls between features leave no
  seam at which to introduce events, asynchronous handling, or an outbox.

The boundary scanner quantifies the problem today: accounting, savings, loan, group, teller,
batch and the deposit modules each reference types from other features. The numbers per
module are tracked so each phase shows measurable reduction.

#### Goals

* `fineract-core` becomes the single home for shared, read-only contracts: read-service
  interfaces, the DTOs/projections they return (`ClientSummaryDTO`, `OfficeDTO`, `ChargeDTO`,
  `LoanAccountSummaryDTO`, …​), and shared value objects and enums. No business logic, no
  feature-owned entities.
* `fineract-command` becomes the single home for cross-feature write contracts: command and
  domain-event definitions, the command/event bus, transactional outbox/inbox, and saga
  support for long-running flows.
* Every direct feature-to-feature import is removed and re-expressed as a `fineract-core`
  read or a `fineract-command` write.
* An ArchUnit rule is wired into CI once the violation count reaches zero, failing any build
  that reintroduces a cross-feature import.
* The REST API stays 100% backward-compatible: no changes to endpoints, request shapes, or
  response shapes.
* Integration tests stay green at every phase boundary; no phase requires a big-bang cutover.

#### Exclusions

* The storage layer — JPA entities, schema, query performance — is out of scope; that is a
  separate effort.
* No changes to existing REST API contracts or response shapes.
* No external message brokers; outbox/inbox stays within the database transaction for now.
* Performance tuning and asynchronous execution are not in scope, though the event-driven
  boundaries introduced here make them straightforward to add later.

#### Change proposed

##### Reads:fineract-corecontracts

Instead of importing another feature’s repository to perform a read, a feature depends on an
interface declared in `fineract-core`, and the owning feature provides the implementation.
The interface returns a DTO — a plain, stable projection — so the data crossing a boundary
is never a live entity. This inverts the dependency: both the caller and the owner depend on
`fineract-core`, neither on the other.

```java
        accounting  --depends on-->  fineract-core (ChargeReadService)  <--implements--  charge
```

##### Writes:fineract-commandcommands and events

A feature that needs another feature to act stops calling its service directly. It dispatches
a command (point-to-point, expects a handler) or publishes a domain event (broadcast, zero or
more subscribers). The owning feature handles it. `fineract-command` owns the command and
event definitions, the dispatch bus, and a transactional outbox/inbox so a published event
and its originating database change commit atomically.

##### By-id references

Where a feature only stores a reference to another feature’s aggregate (e.g. a foreign-key
relationship), the JPA association to the foreign entity is replaced with the identifier
(`Long`), keeping the same database column. Details, when needed, are fetched through the
relevant `fineract-core` read contract. This removes the import without a schema change.

#### Migration approach

Each phase targets one package or feature and is a set of PRs. The scanner’s before/after
count per module is the unit of progress a reviewer can verify. Phases are ordered by
cross-feature surface area and traffic, smallest first, so the mechanics are proven on
low-risk modules before reaching savings and loan. The ArchUnit enforcement rule is activated
only after the violation count is zero.

#### Phases of work

1. **Inventory.** Run the boundary scanner, classify each violation, and assign ownership.
  Expand `fineract-core` (DTOs, read-service interfaces, shared value objects) and
  `fineract-command` (bus, outbox/inbox, sagas, initial command and event catalogs).
2. **Easy wins.** Decouple accounting, client, and user-administration from organisation and
  charge.
3. **Mid-tier.** group, account transfers, MIX, shareaccounts, batch.
4. **Savings.** Replace savings → accounting direct calls with domain events; move all other
  dependencies to core DTOs and interfaces.
5. **Loan.** Publish loan lifecycle events; replace every direct import with commands, events,
  and core contracts. Largest phase.
6. **Deposits.** Break fixed/recurring deposit inheritance from savings; use an
  `AccountLifecycle` and composition contracts instead.
7. **Orchestrators.** teller, reporting, notifications, and templates move to the command bus
  and read models.
8. **Enforcement.** Activate the ArchUnit boundary rule in CI; track violation counts per PR
  going forward.

#### Alternatives considered

* **Do nothing / rely on review.** The boundary has already eroded under code review alone; an
  automated rule is the only durable guarantee.
* **Split every feature into its own Gradle module up front.** Physically separating modules
  forces the boundary but is a large, high-risk change and reorders the work; the contract-
  first approach lets features stay in place and migrate incrementally, with module
  extraction following naturally once the imports are gone.
* **Introduce an external message broker now.** Deferred. The outbox/inbox pattern within the
  existing database transaction delivers reliable eventing without new infrastructure; a
  broker can replace the transport later without changing the command/event contracts.