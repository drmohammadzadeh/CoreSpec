---
source_url: https://fineract.apache.org/docs/1.16.0#_testing
title: "Testing"
depth: 1
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/stable
---

## Testing

TBD

### Cucumber E2E Tests

Apache Fineract’s E2E test suite provides comprehensive coverage of business functionality using Cucumber BDD (Behavior-Driven Development) framework. These tests serve as both functional validation and living documentation of the system’s capabilities.

#### Overview

##### Architecture

* **fineract-e2e-tests-runner**: Contains all Cucumber feature files and test scenarios
* **fineract-e2e-tests-core**: Contains step definitions, test utilities, and supporting code
* **Framework**: Cucumber with Java, using Gherkin syntax for readable test specifications
* **Prerequisites**: Running Apache Fineract instance (typically on port 8443 with HTTPS)

##### Test Organization

* Feature files located in: `fineract-e2e-tests-runner/src/test/resources/features/`
* Step definitions in: `fineract-e2e-tests-core/src/test/java/org/apache/fineract/test/stepdef/`
* Tests are tagged with TestRail IDs for traceability (e.g., `@TestRailId:C16`)
* Special tags include `@Smoke` for quick validation tests

#### Prerequisites

##### Required Software

See *Fineract Development Environment*.

##### Database Setup

Before running E2E tests, ensure the databases are created:

```bash
# Create required databases
./gradlew createDB -PdbName=fineract_tenants
./gradlew createDB -PdbName=fineract_default
```

#### Configuration

##### Connection Configuration

E2E tests connect to the running Fineract instance. Default configuration in `fineract-e2e-tests-core/src/test/resources/fineract-test-application.properties`:

```properties
# Connection details to running backend
fineract-test.api.base-url=${BASE_URL:https://localhost:8443}
fineract-test.api.username=${TEST_USERNAME:mifos}
fineract-test.api.password=${TEST_PASSWORD:password}
fineract-test.api.tenant-id=${TEST_TENANT_ID:default}
```

To override defaults, use environment variables:

```bash
export BASE_URL=http://localhost:8080
export TEST_USERNAME=mifos
export TEST_PASSWORD=password
export TEST_TENANT_ID=default
```

##### Test Data Initialization

> [!IMPORTANT]
> Many E2E tests require pre-configured test data (loan products, charges, configurations). This initialization is controlled by the `fineract-test.initialization.enabled` property.

**Default Behavior**:

* By default, initialization is **DISABLED** (`fineract-test.initialization.enabled=false`)
* Without initialization, tests will fail with errors like:

```java
java.lang.IllegalArgumentException: Loan product [LP2_ADV_CUSTOM_PMT_ALLOC_PROGRESSIVE_LOAN_SCHEDULE_HORIZONTAL] not found
```

**How to Enable Initialization**:

Method 1 - Environment Variable (Recommended):

```bash
cd fineract-e2e-tests-runner
INITIALIZATION_ENABLED=true ../gradlew cucumber
```

Method 2 - System Property:

```bash
cd fineract-e2e-tests-runner
../gradlew cucumber -DINITIALIZATION_ENABLED=true
```

Method 3 - Modify Properties File:
Edit `fineract-e2e-tests-core/src/test/resources/fineract-test-application.properties`:

```properties
fineract-test.initialization.enabled=true
```

**What Initialization Creates**:

* 100+ loan products with specific configurations
* Various charge types (NSF fees, processing fees, etc.)
* Payment allocation rules
* Interest calculation configurations
* Advanced payment allocation strategies
* Progressive loan schedule configurations

**When to Use Initialization**:

* First-time test execution on a fresh database
* After database reset/recreation
* When running tests that require specific loan products
* Testing new features that depend on pre-configured products

> [!NOTE]
> Initialization takes additional time (2-5 minutes) as it creates extensive test data. Consider running it once and reusing the database for multiple test runs.

##### Business Date Configuration

CRITICAL: The Business Date feature must be enabled in the database for many E2E tests to function correctly.

**Default Behavior**:

* Business Date is **DISABLED** by default in fresh Fineract installations
* Without Business Date enabled, tests fail with:

```json
{"errors":[{
  "defaultUserMessage":"Business date functionality is not enabled",
  "developerMessage":"Business date functionality is not enabled",
  "userMessageGlobalisationCode":"business.date.is.not.enabled"
}]}
```

**How to Enable Business Date**:

Method 1 - Via SQL (Direct Database):

```bash
mysql -u root -pmysql fineract_default -e \
  "UPDATE c_configuration SET enabled = 1 WHERE name = 'enable-business-date';"
```

Method 2 - Via API (After Fineract is Running):

```bash
curl -k -X PUT https://localhost:8443/fineract-provider/api/v1/configurations/name/enable-business-date \
  -H "Authorization: Basic bWlmb3M6cGFzc3dvcmQ=" \
  -H "Fineract-Platform-TenantId: default" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

> [!NOTE]
> The `Fineract-Platform-TenantId` header is required. Without it, the request can fail with HTTP 400 because tenant context is missing.

**Verification**:

```bash
mysql -u root -pmysql fineract_default -e \
  "SELECT * FROM c_configuration WHERE name LIKE '%business%';"
```

#### Running E2E Tests

##### Complete Workflow

###### Step 1: Start Fineract

```bash
# Start Fineract with test profile enabled for E2E
./gradlew bootRun -Dspring.profiles.active=test
```

> [!IMPORTANT]
> When running E2E tests that hit endpoints/APIs backed by beans annotated with `@Profile(FineractProfiles.TEST)`, the provider startup must include `-Dspring.profiles.active=test`. Without this, test-profile-only components are not loaded.

Wait for Fineract to be fully started. You can verify by checking:

```bash
curl -k https://localhost:8443/actuator/health
```

###### Step 2: Enable Business Date (if needed)

```bash
mysql -u root -pmysql fineract_default -e \
  "UPDATE c_configuration SET enabled = 1 WHERE name = 'enable-business-date';"
```

###### Step 3: Run E2E Tests

Navigate to the E2E tests module:

```bash
cd fineract-e2e-tests-runner
```

**Run All E2E Tests**:

```bash
# First run with initialization
INITIALIZATION_ENABLED=true ../gradlew cucumber

# Subsequent runs without initialization (faster)
../gradlew cucumber
```

**Run Specific Feature File**:

```bash
../gradlew cucumber -Pcucumber.features="src/test/resources/features/Loan.feature"
```

**Run Tests by Tag**:

```bash
# Run only smoke tests
../gradlew cucumber -Pcucumber.tags="@Smoke"

# Run specific TestRail test
../gradlew cucumber -Pcucumber.tags="@TestRailId:C16"

# Run multiple tags
../gradlew cucumber -Pcucumber.tags="@Smoke and @TestRailId:C16"
```

**Run Tests with Custom Configuration**:

```bash
BASE_URL=http://localhost:8080 \
TEST_USERNAME=admin \
TEST_PASSWORD=admin123 \
INITIALIZATION_ENABLED=true \
../gradlew cucumber
```

##### Gradle Command Options

###### Basic Cucumber Task

```bash
../gradlew cucumber
```

###### Feature File Selection

```bash
# Single feature
../gradlew cucumber -Pcucumber.features="src/test/resources/features/Client.feature"

# Multiple features
../gradlew cucumber -Pcucumber.features="src/test/resources/features/Client.feature:src/test/resources/features/Loan.feature"

# Specific scenario by line number
../gradlew cucumber -Pcucumber.features="src/test/resources/features/Loan.feature:45"
```

###### Tag-Based Execution

```bash
# Single tag
../gradlew cucumber -Pcucumber.tags="@Smoke"

# Multiple tags (AND)
../gradlew cucumber -Pcucumber.tags="@Smoke and @TestRailId:C16"

# Multiple tags (OR)
../gradlew cucumber -Pcucumber.tags="@Smoke or @TestRailId:C16"

# Exclude tags
../gradlew cucumber -Pcucumber.tags="not @ignore"

# Complex tag expression
../gradlew cucumber -Pcucumber.tags="@Smoke and not @ignore"
```

###### Report Generation

```bash
# Generate HTML report
../gradlew cucumber -Dcucumber.plugin="pretty,html:build/cucumber-reports/cucumber.html"

# Generate JSON report
../gradlew cucumber -Dcucumber.plugin="json:build/cucumber-reports/cucumber.json"

# Multiple report formats
../gradlew cucumber -Dcucumber.plugin="pretty,html:build/cucumber-reports/cucumber.html,json:build/cucumber-reports/cucumber.json"

# Generate Allure report (comprehensive visual reporting)
../gradlew cucumber allureReport
```

After running tests with Allure, the report is available at:

```java
fineract-e2e-tests-runner/build/reports/allure-report/index.html
```

> [!NOTE]
> Allure provides rich visual reports with test history, statistics, and detailed execution information. Open the `index.html` file in a browser to view the interactive report.

###### Clean and Run

```bash
# Clean previous test results and run
../gradlew clean cucumber
```

##### Advanced Execution Scenarios

###### Running Against Different Environment

```bash
# Against staging environment
BASE_URL=https://staging.example.com:8443 \
TEST_USERNAME=staging_user \
TEST_PASSWORD=staging_pass \
../gradlew cucumber
```

###### Running with External Event Verification

```bash
# Enable external event verification (requires ActiveMQ)
ACTIVEMQ_BROKER_URL=tcp://localhost:61616 \
ACTIVEMQ_BROKER_USERNAME=admin \
ACTIVEMQ_BROKER_PASSWORD=admin \
ACTIVEMQ_TOPIC_NAME=fineract-events \
EVENT_VERIFICATION_ENABLED=true \
../gradlew cucumber
```

###### Running with TestRail Integration

```bash
TESTRAIL_ENABLED=true \
TESTRAIL_BASEURL=https://testrail.example.com \
TESTRAIL_USERNAME=test@example.com \
TESTRAIL_PASSWORD=testrail_password \
TESTRAIL_RUN_ID=123 \
../gradlew cucumber
```

#### Test Development

##### Feature Coverage

The E2E tests cover the following functional domains:

###### Client Management

* Client creation and management
* Address management
* Document management
* Family member tracking

###### Loan Management

* Loan application and approval
* Disbursement
* Repayment processing
* Charges and fees
* Advanced features: chargeback, charge-off, re-aging, re-amortization
* Specialized loans: down payment, merchant-issued refund

###### Savings Account Management

* Account opening and activation
* Deposits and withdrawals
* Interest calculation
* Account closure

###### Accounting

* Journal entry validation
* Asset externalization
* GL account mapping

###### Operational Processes

* Close of Business (COB)
* Inline COB
* Business date management
* Batch API operations

##### Writing New E2E Tests

When writing new Cucumber tests:

1. **Create Feature File**: Add new `.feature` file in `fineract-e2e-tests-runner/src/test/resources/features/`
2. **Use Gherkin Syntax**:
  
  
  
  
  ```gherkin
  Feature: Loan Disbursement
  
    Scenario: Successful loan disbursement
      Given A client named "John Doe"
      When Admin creates a loan for client with amount "1000"
      And Admin approves the loan
      And Admin disburses the loan on business date
      Then Loan status is "Active"
      And Loan outstanding balance is "1000"
  ```
3. **Implement Step Definitions**: Add corresponding step definitions in `fineract-e2e-tests-core/src/test/java/org/apache/fineract/test/stepdef/`
4. **Add Tags**: Tag scenarios appropriately:
  
  
  
  
  ```gherkin
  @TestRailId:C1234 @Smoke
  Scenario: Critical loan test
  ```
5. **Verify with Gradle**:
  
  
  
  
  ```bash
  cd fineract-e2e-tests-runner
  ../gradlew cucumber -Pcucumber.features="src/test/resources/features/YourNewFeature.feature"
  ```

#### Troubleshooting

##### Common Test Failures

###### Connection Issues

**Symptom**: Tests fail with connection refused errors

**Solutions**:

```bash
# Verify Fineract is running
curl -k https://localhost:8443/actuator/health

# Check if port is in use
netstat -tulpn | grep 8443

# Check logs (logs go to console/stdout)
# If running in background, redirect output:
# ./gradlew bootRun > build/bootRun.log 2>&1 &
# tail -f build/bootRun.log
```

###### Business Date Issues

**Symptom**: Tests fail with "Business date functionality is not enabled"

**Solutions**:

```bash
# Enable Business Date
mysql -u root -pmysql fineract_default -e \
  "UPDATE c_configuration SET enabled = 1 WHERE name = 'enable-business-date';"

# Verify
mysql -u root -pmysql fineract_default -e \
  "SELECT * FROM c_configuration WHERE name = 'enable-business-date';"
```

###### Data Dependencies

**Symptom**: Tests fail due to missing products or charges

**Solutions**:

```bash
# Run with initialization enabled
cd fineract-e2e-tests-runner
INITIALIZATION_ENABLED=true ../gradlew cucumber
```

###### Authentication Failures

**Symptom**: 401 or 403 errors

**Solutions**:

```bash
# Verify credentials
TEST_USERNAME=mifos TEST_PASSWORD=password ../gradlew cucumber

# Check user permissions in database
mysql -u root -pmysql fineract_default -e \
  "SELECT * FROM m_appuser WHERE username = 'mifos';"
```

##### Debugging Tips

###### Enable Detailed Logging

```bash
# Run with verbose output
../gradlew cucumber -Dcucumber.plugin="pretty" --info

# Save output to file
../gradlew cucumber > test-output.log 2>&1
```

###### Check Database State

```bash
# Check loan products after initialization
mysql -u root -pmysql fineract_default -e \
  "SELECT id, product_name FROM m_product_loan LIMIT 20;"

# Check configurations
mysql -u root -pmysql fineract_default -e \
  "SELECT name, enabled FROM c_configuration WHERE name LIKE '%enable%';"
```

###### View Test Reports

After test execution, reports are available in:

```java
fineract-e2e-tests-runner/build/cucumber-reports/
fineract-e2e-tests-runner/build/reports/tests/
```

#### Best Practices

##### Test Organization

* Keep feature files focused on specific business domains
* Use descriptive scenario names
* Include business context in scenario descriptions
* Tag tests appropriately for organization and execution

##### Test Isolation

* Each test should be independent
* Don’t rely on state from other tests
* Clean up test data in `@After` hooks
* Use unique identifiers for test entities

##### Test Data Management

* Use initialization for complex test data setup
* Create minimal required data in test scenarios
* Document test data dependencies
* Reuse database for multiple test runs when possible

##### Performance Optimization

* Run initialization once per database
* Use tags to run subset of tests during development
* Run full suite in CI/CD pipelines
* Consider parallel execution for large test suites

#### Cucumber Cheatsheet

Cucumber is a test framework based on Behavior-Driven Development (BDD). Tests are written in plain text with very basic syntax rules. These rules form a mini language that is called Gherkin.

A specification resembles spoken language. This makes it ideal for use with non-technical people that have domain specific knowledge. The emphasis of Cucumber lies on finding examples to describe your test cases. The few keywords and language rules are easy to explain to anyone (compared JUnit for example).

##### Keywords

The Gherkin language has the following keywords:

* `Feature`
* `Rule`
* `Scenario Outline` or `Scenario Template`
* `Example` or `Scenario`
* `Examples` or `Scenarios`
* `Background`
* `Given`
* `And`
* `But`
* `When`
* `Then`

There are a couple of additional signs used in Gherkin:

* `|` is as column delimiters in `Examples` tables
* with `@` you can assign any kind of tags to categorize the specs (or e.g. relate them to certain Jira tickets)
* `#` is used to indicate line comments

> [!IMPORTANT]
> The tag `@ignore` is used to skip tests. This is a somewhat arbitrary choice (we could use any other tag to indicate temporarily disabled tests).

Each non-empty line of a test specification needs to start with one of these keywords. The text blocks that follows the keywords are mapped to so called step definitions that contain the actual test code.

A typical Cucumber test specification written in Gherkin looks like this:

```gherkin
Feature: Template Service

  @template
  Scenario Outline: Verify that mustache templates have expected results
    Given A mustache template file <template>
    Given A JSON data file <json>
    When The user merges the template with data
    Then The result should match the content of file <result>

    Examples:
      | template             | json       | result          |
      | hello.mustache       | hello.json | hello.txt       |
      | loan.mustache        | loan.json  | loan.html       |
      | array.loop.mustache  | array.json | array.loop.txt  |
      | array.index.mustache | array.json | array.index.txt |
```

The corresponding step definitions would look like this:

```java
package org.apache.fineract.template.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.google.common.reflect.TypeToken;
import com.google.gson.Gson;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import io.cucumber.java8.En;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import org.apache.commons.io.IOUtils;
import org.apache.fineract.template.data.TemplateData;
import org.springframework.beans.factory.annotation.Autowired;

public class TemplateServiceStepDefinitions implements En {

    @Autowired
    private TemplateMergeService tms;

    private String template;

    private Map<String, Object> data;

    private String result;

    public TemplateServiceStepDefinitions() {
        Given("/^A mustache template file (.*)$/", (String file) -> {
            template = IOUtils.resourceToString("templates/" + file, StandardCharsets.UTF_8,
                    TemplateServiceStepDefinitions.class.getClassLoader());
        });

        Given("/^A JSON data file (.*)$/", (String file) -> {
            data = parse(IOUtils.resourceToString("templates/" + file, StandardCharsets.UTF_8,
                    TemplateServiceStepDefinitions.class.getClassLoader()));
        });

        When("The user merges the template with data", () -> {
            result = compile(template, data);
        });

        Then("/^The result should match the content of file (.*)$/", (String file) -> {
            String expected = IOUtils.resourceToString("results/" + file, StandardCharsets.UTF_8,
                    TemplateServiceStepDefinitions.class.getClassLoader());
            assertEquals(expected, result);
        });
    }

    private String compile(String templateText, Map<String, Object> scope) {
        return tms.compile(TemplateData.builder().name("TemplateName").text(templateText).mappers(List.of()).build(), scope);
    }

    private Map<String, Object> parse(String data) {
        Gson gson = new Gson();
        Type ssMap = new TypeToken<Map<String, Object>>() {}.getType();
        JsonElement json = JsonParser.parseString(data);
        return gson.fromJson(json, ssMap);
    }
}
```

> [!NOTE]
> This example is an actual test specification that you can find in the `fineract-provider` module.

###### Feature

This keyword is used to group scenarios and to group related scenarios. All Gherkin specifications must start with the word `Feature`.

###### Descriptions

A description is any non-empty line that doesn’t start with a keyword. Descriptions can be placed under the keywords:

* `Feature`
* `Rule`
* `Background`
* `Example`/`Scenario`
* `Scenario Outline`

###### Rule

Rule is used to group multiple related scenarios together.

###### Example/Scenario

This is the important part of the specification as it should describe the business logic in more detail with the usage of steps (usually `Given`, `When`, `Then`)

###### Steps

TBD

###### Given

TBD

###### When

TBD

###### Then

TBD

###### And, But

TBD

###### Background

TBD

###### Scenario Outline

TBD

###### Examples/Tables

TBD

##### Outlook

As a proof of concept we’ve converted all unit tests in `fineract-provider` into Cucumber tests. The more interesting part starts when we’ll attack the integration tests with over 400 mostly business logic related tests. These tests fit very well in Cucumber’s test specification structure (a lot of *if-then-else* or in Gherkin: *Given-When-Then*). Migrating all tests will take a while, but we would already recommend trying to implement tests as Cucumber specifications. It should be relatively easy to convert these tests into the new syntax.

Hopefully this will motivate even more people from the broader Fineract community to participate in the project by sharing their domain specific knowledge as Cucumber specifications. Specifications are written in English (although not a technical requirement).

> [!NOTE]
> Have a look at the specifications in `fineract-provider` for an initial inspiration. For more information please see [cucumber.io/docs](https://cucumber.io/docs)

### Unit Testing

TBD

### Integration Testing

Integration tests in Apache Fineract validate the complete API layer and business logic by making HTTP calls to a running Fineract instance. These tests ensure that different components work together correctly and that the API behaves as expected.

#### Overview

##### Architecture

* **Location**: `integration-tests/src/test/java/org/apache/fineract/integrationtests`
* **Framework**: JUnit 5. Tests under `client/feign` drive the server through the generated Feign client; the remainder still use REST Assured for HTTP communication
* **Base Class**: Most tests extend `BaseLoanIntegrationTest` or `IntegrationTest`; Feign tests extend `FeignLoanTestBase` or `FeignSavingsTestBase`
* **Prerequisites**: Running Apache Fineract instance (default: [localhost:8443](https://localhost:8443))

New tests should be written against the generated Feign client, which is covered in Feign Integration Tests. The rest of this chapter describes the setup shared by both, and the REST Assured pattern used by the tests that have not yet been migrated.

##### Key Characteristics

* Tests run against a live Fineract instance
* Validates end-to-end API functionality
* Tests business logic, validation rules, and workflows
* Includes accounting verification and data integrity checks
* Uses real database transactions
* Tests can be run individually or as a suite

#### Prerequisites

##### Required Software

See *Fineract Development Environment*.

##### Database Setup

Before running integration tests, ensure the databases are created:

There is a separate task per database engine: `createPGDB` for PostgreSQL, `createDB` for MariaDB, and `createMySQLDB` for MySQL.

```bash
# Create required databases (PostgreSQL)
./gradlew createPGDB -PdbName=fineract_tenants
./gradlew createPGDB -PdbName=fineract_default
```

##### Fineract Instance

The build never starts a server. `:integration-tests:test`, `:twofactor-tests:test` and `:oauth2-tests:test` all
run against whatever is already answering at the address in Default Connection Settings, so you have to bring
an instance up yourself first. Start it any of these three ways.

###### Docker Compose (recommended)

This is what CI does, so it is the configuration the suites are actually verified against. Build the image once,
then bring up the stack:

```bash
./gradlew :fineract-provider:jibDockerBuild -Djib.to.image=fineract -x test -x cucumber

# PostgreSQL; docker-compose-mariadb-test.yml and docker-compose-mysql-test.yml also exist
docker compose -f docker-compose-postgresql-test.yml up -d

./gradlew :integration-tests:waitForFineract
```

The compose files bring up the database, LocalStack and the mock OAuth2 server alongside Fineract, and they create
the `fineract_tenants` and `fineract_default` databases for you â the `createPGDB` step above is only needed when
you run the server outside Docker.

###### Gradle

```bash
./gradlew :fineract-provider:bootRun
```

`bootRun` needs a database reachable on `localhost` and the `createPGDB`/`createDB`/`createMySQLDB` step above.
Use `:fineract-provider:devRun` for the same thing with the quality checks switched off.

###### IDE

Run `org.apache.fineract.ServerApplication`. The defaults in `application.properties` already put the server on
`localhost:8443/fineract-provider`, which is exactly where the tests look, so no run configuration is
needed beyond the database settings.

###### Waiting for it to come up

`:integration-tests:waitForFineract` polls `/actuator/health` until the instance answers, using the same
`BACKEND_PROTOCOL`/`BACKEND_HOST`/`BACKEND_PORT` variables as the tests. It is handy in scripts:

```bash
./gradlew :integration-tests:waitForFineract -PwaitForFineractTimeoutSeconds=300
```

###### The WAR deployment

`fineract-war` still ships `fineract-provider.war` in the binary distribution, and one CI job keeps that deployment
path honest: `.github/workflows/build-war-smoke.yml` deploys the WAR into a stock Tomcat and drives a single E2E
scenario against it. `docker-compose-war-test.yml` is the same stack, so you can reproduce it locally:

```bash
./gradlew :fineract-war:war
docker compose -f docker-compose-war-test.yml up -d

BASE_URL=http://localhost:8080 ./gradlew :fineract-e2e-tests-runner:cucumber \
  -Pcucumber.features="src/test/resources/features/Client.feature" \
  -Pcucumber.tags="@Smoke"
```

`-Pcucumber.features` takes a path relative to `fineract-e2e-tests-runner`, and `-Pcucumber.tags` takes a
cucumber tag expression. A filter that matches nothing is not an error: cucumber reports `0 scenarios` and
exits 0, so a scripted run should check the summary line rather than trust the exit code.

Tomcat serves the WAR over plain HTTP on 8080 rather than HTTPS on 8443, which is why `BASE_URL` is set explicitly;
the integration suites take `BACKEND_PROTOCOL` and `BACKEND_PORT` instead. Every other job in CI runs the Spring
Boot jar through the jib image, so this is the only place a WAR-specific regression shows up.

###### Authentication modes

`twofactor-tests` and `oauth2-tests` need the server started with a different authentication mode than the default,
so they cannot run against the same instance as `integration-tests`. Layer the matching compose override on top and
recreate the `fineract` service:

```bash
# two-factor authentication
docker compose -f docker-compose-postgresql-test.yml -f docker-compose-twofactor-test.yml \
  up -d --force-recreate fineract
./gradlew :twofactor-tests:test

# OAuth2
docker compose -f docker-compose-postgresql-test.yml -f docker-compose-oauth2-test.yml \
  up -d --force-recreate fineract
./gradlew :oauth2-tests:test
```

#### Configuration

##### Default Connection Settings

Integration tests use the following default connection settings:

```properties
BACKEND_PROTOCOL=https
BACKEND_HOST=localhost
BACKEND_PORT=8443
BACKEND_USERNAME=mifos
BACKEND_PASSWORD=password
BACKEND_TENANT=default
```

##### Override Configuration

To override default values, set environment variables:

```bash
# Set custom connection details
export BACKEND_PROTOCOL=http
export BACKEND_HOST=localhost
export BACKEND_PORT=8080
export BACKEND_USERNAME=admin
export BACKEND_PASSWORD=admin123
export BACKEND_TENANT=default
```

#### Running Integration Tests

##### Complete Workflow

###### Step 1: Start Fineract

Bring up an instance as described in Fineract Instance, for example:

```bash
# Start Fineract in background
./gradlew :fineract-provider:bootRun &

# Wait for startup
curl -k https://localhost:8443/fineract-provider/actuator/health
```

Expected response:

```json
{"status":"UP"}
```

###### Step 2: Run Integration Tests

Navigate to the project root and execute tests:

```bash
# Run all integration tests
./gradlew :integration-tests:test

# Run with clean build
./gradlew clean :integration-tests:test
```

##### Running Specific Tests

###### Run Single Test Class

```bash
# Run entire test class
./gradlew :integration-tests:test --tests ClientLoanIntegrationTest

# Run with verbose output
./gradlew :integration-tests:test --tests ClientLoanIntegrationTest --info
```

###### Run Specific Test Method

```bash
# Run single test method
./gradlew :integration-tests:test --tests ClientLoanIntegrationTest.testLoanSchedule

# Run multiple specific tests
./gradlew :integration-tests:test --tests ClientLoanIntegrationTest.testLoanSchedule \
  --tests ClientLoanIntegrationTest.testLoanRepayment
```

###### Run Tests by Pattern

```bash
# Run all loan-related tests
./gradlew :integration-tests:test --tests "*Loan*"

# Run all client-related tests
./gradlew :integration-tests:test --tests "*Client*"

# Run all accounting tests
./gradlew :integration-tests:test --tests "*Accounting*"

# Run all COB tests
./gradlew :integration-tests:test --tests "*COB*"
```

##### Advanced Test Execution

###### Run with Test Filtering

`--tests` is the only filter the `test` task accepts. Repeat it to select several patterns; there is no corresponding exclude option.

```bash
# Select several patterns
./gradlew :integration-tests:test \
  --tests "*Loan*" \
  --tests "*Savings*"
```

To skip a test permanently, annotate it with `@Disabled` rather than filtering it on the command line.

###### Parallel Execution

`--max-workers` limits Gradle’s own worker count; it does not fork the test JVM. Within-task parallelism is controlled by `maxParallelForks` on the `test` task, which `integration-tests` does not set â the suite runs in a single JVM.

> [!WARNING]
> Integration tests share the database of the instance under test. Raising `maxParallelForks` requires the tests to be isolated from one another first.

###### Run with Custom JVM Arguments

```bash
# Attach a debugger to the test JVM (suspends until the debugger connects)
./gradlew :integration-tests:test --debug-jvm
```

To debug the **server** rather than the tests, attach to the instance you started. The compose test stacks already
run it with a JDWP agent â `JAVA_TOOL_OPTIONS` in `config/docker/env/fineract-common.env` â and publish it on
port 5000, so a remote JVM debugger pointed at `localhost:5000` connects without any further setup.

The Gradle daemon’s own heap is set by `org.gradle.jvmargs` in `gradle.properties`.

> [!CAUTION]
> Overriding it on the command line with `-Dorg.gradle.jvmargs` replaces the whole value, including the `--add-exports` and `--add-opens` flags the build needs. Repeat those flags if you override it.

###### Generate Test Reports

```bash
# Run tests and generate HTML reports
./gradlew :integration-tests:test

# Reports are generated at:
# integration-tests/build/reports/tests/test/index.html
```

###### Continuous Execution

```bash
# Watch for changes and re-run tests
./gradlew :integration-tests:test --continuous

# Run specific test continuously
./gradlew :integration-tests:test --continuous --tests ClientLoanIntegrationTest
```

##### Test Execution Examples

###### Basic Loan Workflow Test

```bash
# Test complete loan lifecycle
./gradlew :integration-tests:test --tests LoanApplicationTest
```

###### Progressive Loan Tests

```bash
# Run all progressive loan tests
./gradlew :integration-tests:test --tests "*Progressive*"
```

###### Accounting Integration Tests

```bash
# Run accounting-related tests
./gradlew :integration-tests:test --tests AccountingScenarioIntegrationTest
```

###### Business Date Tests

```bash
# Run business date functionality tests
./gradlew :integration-tests:test --tests BusinessDateTest
```

###### Charge-Off Tests

```bash
# Run charge-off related tests
./gradlew :integration-tests:test --tests "*ChargeOff*"
```

#### Test Structure

##### Loan Test Base Class Overview

`FeignLoanTestBase` is the base class for loan-related integration tests, and provides the helpers described below. `BaseLoanIntegrationTest` offers the same surface for the REST Assured tests that have not yet been migrated.

###### Pre-configured Loan Product Creation

These methods return a `PostLoanProductsRequest` describing the product. Pass it to `createLoanProduct` to create the product and obtain its identifier.

```java
createOnePeriod30DaysLongNoInterestPeriodicAccrualProduct()
create4IProgressive()
create4IProgressiveWithCapitalizedIncome()
createOnePeriod30DaysLongNoInterestPeriodicAccrualProductWithAdvancedPaymentAllocation()
```

###### Transaction Management

```java
// Validate loan transactions
verifyTransactions(loanId,
    transaction(100.0, "Disbursement", "01 January 2024"),
    transaction(50.0, "Repayment", "15 January 2024")
);

// Verify accounting journal entries
verifyJournalEntries(loanId, expectedEntries);

// Create transaction test data
Transaction txn = transaction(amount, type, date);
```

###### Loan Lifecycle Operations

```java
// Disburse loan
disburseLoan(loanId, BigDecimal.valueOf(100), "01 January 2024");

// Undo disbursement
undoDisbursement(loanId);

// Re-age loan
reAgeLoan(loanId, reAgeRequest);

// Re-amortize loan
reAmortizeLoan(loanId, reAmortizeRequest);

// Execute Close of Business
executeInlineCOB(loanId);
```

###### Business Date Management

```java
// Execute code at specific business date
runAt("01 January 2024", () -> {
    Long loanId = applyAndApproveProgressiveLoan(...);
    disburseLoan(loanId, BigDecimal.valueOf(100), "01 January 2024");
});

// Execute over date range
runFromToInclusive("01 January 2024", "31 January 2024", () -> {
    // Operations for each date in the range
});

// Execute without bypass privileges
runAsNonByPass(() -> {
    // Test operations with regular user permissions
});
```

###### Verification Methods

```java
// Validate repayment schedule
verifyRepaymentSchedule(loanId, expectedSchedule);

// Check loan status
verifyLoanStatus(loanId, "ACTIVE");

// Verify outstanding amounts
verifyOutstanding(loanId, expectedOutstanding);

// Check arrears status
verifyArrears(loanId, expectedArrears);
```

##### Common Test Patterns

###### Test Setup Pattern

A test extending `FeignLoanTestBase` needs no setup block; the base class builds the client and its helpers.

The REST Assured tests that have not yet been migrated build a request specification per test:

```java
@BeforeEach
public void setup() {
    Utils.initializeRESTAssured();
    this.requestSpec = new RequestSpecBuilder()
        .setContentType(ContentType.JSON)
        .build();
    this.requestSpec.header("Authorization", "Basic " +
        Utils.loginIntoServerAndGetBase64EncodedAuthenticationKey());
    this.responseSpec = new ResponseSpecBuilder()
        .expectStatusCode(200)
        .build();
}
```

Do not copy this into a new test. `loginIntoServerAndGetBase64EncodedAuthenticationKey` authenticates against the server on every test method.

###### Date-Specific Operations

```java
runAt("01 January 2024", () -> {
    // Create client
    Long clientId = clientHelper.createClient(...);

    // Apply for loan
    Long loanId = applyLoan(clientId, productId, amount);

    // Approve loan
    approveLoan(loanId, "01 January 2024");

    // Disburse loan
    disburseLoan(loanId, amount, "01 January 2024");
});
```

###### Structured Verification

```java
// Verify transactions
verifyTransactions(loanId,
    transaction(100.0, "Disbursement", "01 January 2024"),
    transaction(50.0, "Capitalized Income", "01 January 2024"),
    transaction(0.55, "Capitalized Income Amortization", "01 January 2024")
);

// Verify journal entries using convenience methods
verifyJournalEntries(loanId,
    debit(account.getLoansReceivable(), 100.0),
    credit(account.getSuspenseClearingAccount(), 100.0)
);

// Or using full journalEntry method with Account objects
verifyJournalEntries(loanId,
    journalEntry(100.0, account.getLoansReceivable(), "DEBIT"),
    journalEntry(100.0, account.getSuspenseClearingAccount(), "CREDIT")
);
```

###### Progressive Loan Testing

The `create*` methods return a `PostLoanProductsRequest` describing the product, not a product identifier. Pass the request to `createLoanProduct` to obtain the identifier, customising it first if the test needs to.

```java
Long productId = createLoanProduct(create4IProgressive());

Long loanId = applyAndApproveProgressiveLoan(clientId, productId, "01 January 2024",
    1000.0, 10.0, 12, request -> request.setLoanTermFrequency(12));
```

#### Writing Integration Tests

##### Test Development Guidelines

###### 1. Create Test Class

Create a new test class in `integration-tests/src/test/java/org/apache/fineract/integrationtests/` and extend `FeignLoanTestBase`:

```java
package org.apache.fineract.integrationtests;

import org.apache.fineract.integrationtests.client.feign.FeignLoanTestBase;
import org.junit.jupiter.api.Test;

public class MyNewFeatureIntegrationTest extends FeignLoanTestBase {

    @Test
    public void testMyNewFeature() {
        // Test implementation
    }
}
```

The conventions that apply to the body of such a test â how to call the API, how to assert failures, and what to do when a generated model is missing a field â are covered in Feign Integration Tests.

###### 2. Use Helper Classes

`FeignLoanTestBase` exposes the helpers as fields, already constructed against the shared client. There is no request specification to pass around:

```java
Long clientId = clientHelper.createClient(...);
PostLoansResponse loan = loanHelper.applyForLoan(request);
businessDateHelper.updateBusinessDate(...);
```

Helpers that the base class does not expose are constructed with the client:

```java
FeignOfficeHelper officeHelper = new FeignOfficeHelper(FineractFeignClientHelper.getFineractFeignClient());
```

The full set lives in `integration-tests/src/test/java/org/apache/fineract/integrationtests/client/feign/helpers`.

###### 3. Follow Best Practices

* **Self-Contained Tests**: Each test should be independent
* **Clear Setup**: Use `@BeforeEach` for test initialization
* **Date Management**: Use `runAt()` for consistent date-based testing
* **Comprehensive Verification**: Verify transactions, schedules, and accounting
* **Helper Methods**: Use provided helper classes rather than direct API calls
* **Error Testing**: Test both positive and negative scenarios
* **Cleanup**: Clean up test data when necessary

###### 4. Test Complex Scenarios

```java
@Test
public void testLoanWithMultipleDisbursements() {
    runAt("01 January 2024", () -> {
        // Create client
        Long clientId = clientHelper.createClient(ClientHelper.defaultClientCreationRequest());

        // Create multi-disbursement loan product
        Long productId = createMultiDisbursementProduct();

        // Apply for loan
        Long loanId = applyAndApproveProgressiveLoan(clientId, productId,
            BigDecimal.valueOf(1000), 12, BigDecimal.valueOf(10));

        // First disbursement
        disburseLoan(loanId, BigDecimal.valueOf(500), "01 January 2024");

        // Verify first disbursement
        verifyTransactions(loanId,
            transaction(500.0, "Disbursement", "01 January 2024")
        );
    });

    runAt("15 January 2024", () -> {
        // Second disbursement
        disburseLoan(loanId, BigDecimal.valueOf(500), "15 January 2024");

        // Verify both disbursements
        verifyTransactions(loanId,
            transaction(500.0, "Disbursement", "01 January 2024"),
            transaction(500.0, "Disbursement", "15 January 2024")
        );

        // Verify outstanding balance
        verifyOutstanding(loanId, BigDecimal.valueOf(1000));
    });
}
```

###### 5. Run and Verify

```bash
# Run your new test
./gradlew :integration-tests:test --tests MyNewFeatureIntegrationTest

# Run with verbose output for debugging
./gradlew :integration-tests:test --tests MyNewFeatureIntegrationTest --info

# Run specific test method
./gradlew :integration-tests:test --tests MyNewFeatureIntegrationTest.testMyNewFeature
```

#### Troubleshooting

##### Common Test Failures

###### Connection Issues

**Symptom**: Tests fail with connection refused errors

**Solutions**:

```bash
# Verify Fineract is running
curl -k https://localhost:8443/actuator/health

# Check if port is available
netstat -tulpn | grep 8443

# Check Fineract logs (logs go to console/stdout)
# If running in background with output redirection:
# tail -f build/bootRun.log
```

> [!CAUTION]
> Do not stop the instance with `pkill -f bootRun` or by pattern-matching Gradle daemons. The server is a child of the daemon that launched it, so those patterns take the daemon down with it. Stop it from the terminal running it.

Rebuilding while an instance is running replaces the classes it loaded from `build/`. Reads may continue to work while writes start failing. Build first, then start the server.

###### Authentication Failures

**Symptom**: Tests fail with 401 or 403 errors

**Solutions**:

```bash
# Check the user exists and is not locked
psql -U root -d fineract_default \
  -c "SELECT username, nonlocked FROM m_appuser WHERE username = 'mifos';"

# Verify connection settings
echo "Protocol: ${BACKEND_PROTOCOL:-https}"
echo "Host: ${BACKEND_HOST:-localhost}"
echo "Port: ${BACKEND_PORT:-8443}"
echo "Tenant: ${BACKEND_TENANT:-default}"
```

Check `BACKEND_TENANT` as well as the credentials. The tenant identifier is resolved before the user is authenticated, so an unknown tenant fails every test in the same way a bad password does.

###### Data Inconsistency

**Symptom**: Tests fail due to unexpected data state

**Solutions**:

```bash
# 1. Stop the running instance first: PostgreSQL refuses to drop a database
#    while the server still holds connections to it. Stop it from the
#    terminal it is running in.

# 2. Reset the databases
psql -U root -d postgres -c "DROP DATABASE fineract_default;"
psql -U root -d postgres -c "DROP DATABASE fineract_tenants;"

./gradlew createPGDB -PdbName=fineract_tenants
./gradlew createPGDB -PdbName=fineract_default

# 3. Start Fineract again
./gradlew bootRun
```

`createPGDB` is the PostgreSQL task. `createDB` targets MariaDB and `createMySQLDB` targets MySQL; using the wrong one leaves the instance without the databases it expects.

A long-lived development database is itself a source of failures. Tests that generate short random names begin to collide once the table holds enough rows, and tests that page through a listing stop finding what they created. A collision clears on a re-run; a paging miss does not. Reset the databases rather than re-running repeatedly.

###### Test Timeout

**Symptom**: Tests hang or timeout

Timeouts are declared per test with JUnit’s `@Timeout`, or by the awaiting helper a test uses; there is no global timeout property.

**Solutions**:

```bash
# Check for blocked queries
psql -U root -d fineract_default \
  -c "SELECT pid, state, wait_event, query FROM pg_stat_activity WHERE state <> 'idle';"

# Cancel a long-running query
psql -U root -d fineract_default -c "SELECT pg_cancel_backend(<pid>);"
```

A test that waits on a scheduled job can exceed its budget simply because the job is slow on a database with accumulated data, rather than because of a regression. Re-run the class on its own before treating it as a failure.

###### Memory Issues

**Symptom**: OutOfMemoryError during test execution

**Solutions**:

The `test` task always forks its own JVM, and its heap comes from `maxHeapSize` on that task rather than from `org.gradle.jvmargs`. `integration-tests` does not set it, so the fork runs at Gradle’s default. Raise it in `integration-tests/build.gradle`:

```groovy
tasks.named('test') {
    maxHeapSize = '2g'
}
```

`org.gradle.jvmargs` in `gradle.properties` sizes the Gradle daemon, which is a separate process. Raise that only for an out-of-memory failure in the build itself, such as during client generation.

> [!NOTE]
> "Gradle build daemon disappeared unexpectedly" is not the same failure. It is usually the operating system’s out-of-memory killer, meaning `org.gradle.jvmargs` asks for more heap than the machine has; lower it.

##### Debugging Tips

###### Enable Detailed Logging

```bash
# Run with debug output
./gradlew :integration-tests:test --debug

# Run with info level
./gradlew :integration-tests:test --info

# Save output to file
./gradlew :integration-tests:test --info > test-output.log 2>&1
```

###### Check Test Reports

After test execution, detailed reports are available:

```java
# HTML report
integration-tests/build/reports/tests/test/index.html

# XML reports (for CI/CD)
integration-tests/build/test-results/test/

# Gradle scan (upload for detailed analysis)
```

Generate Gradle build scan:

```bash
./gradlew :integration-tests:test --scan
```

###### Database State Verification

```bash
# Check loan status
psql -U root -d fineract_default -c \
  "SELECT id, account_no, loan_status_id, principal_amount \
   FROM m_loan ORDER BY id DESC LIMIT 10;"

# Check transactions
psql -U root -d fineract_default -c \
  "SELECT loan_id, transaction_type_enum, amount, transaction_date \
   FROM m_loan_transaction WHERE loan_id = <loan_id>;"

# Check journal entries
psql -U root -d fineract_default -c \
  "SELECT entry_date, account_id, type_enum, amount \
   FROM acc_gl_journal_entry WHERE loan_id = <loan_id>;"

# Check configurations
psql -U root -d fineract_default -c \
  "SELECT name, enabled FROM c_configuration \
   WHERE name LIKE '%business%' OR name LIKE '%enable%';"
```

###### API Response Debugging

A failed Feign call raises `CallFailedRuntimeException`, which carries the status, the developer message and the raw response body:

```java
CallFailedRuntimeException exception = fail(() -> loanHelper.applyForLoan(request));
log.info("status={} body={}", exception.getStatus(), exception.getResponseBody());
```

To see the requests and responses themselves, build a client with debug logging enabled:

```java
FineractFeignClient debugClient = FineractFeignClientHelper
        .createNewFineractFeignClient(username, password, true);
```

###### Isolate Failing Tests

```bash
# Run only the failing test
./gradlew :integration-tests:test --tests FailingTest --info

# Run with rerun-tasks option
./gradlew :integration-tests:test --tests FailingTest --rerun-tasks

# Run with fail-fast to stop on first failure
./gradlew :integration-tests:test --fail-fast
```

#### Best Practices

##### Test Organization

* Extend `FeignLoanTestBase` for loan tests, or `FeignSavingsTestBase` for savings tests
* Use descriptive test method names that explain what is being tested
* Group related tests in the same test class
* Rely on the base class for setup; a Feign test needs no `@BeforeEach` block to build a client
* Follow existing naming conventions

##### Test Isolation

* Each test should be independent and not rely on other tests
* Create fresh test data for each test
* Clean up test data after test execution
* Use unique identifiers to avoid conflicts
* Don’t share mutable state between tests

##### Performance Optimization

* Reuse Fineract instance across test runs
* Use `runAt()` for efficient date management
* Minimize unnecessary API calls
* Use bulk operations when appropriate
* Consider parallel execution for independent tests
* Run subset of tests during development

##### Code Quality

* Follow existing code patterns and conventions
* Use helper methods instead of duplicating code
* Add comments for complex business logic
* Verify both positive and negative scenarios
* Include edge cases in test coverage
* Document test assumptions and prerequisites

##### Comprehensive Verification

* Always verify transaction creation
* Check accounting journal entries
* Validate repayment schedules
* Verify loan status transitions
* Test charge applications
* Validate business date handling
* Check error messages for validation failures

##### Maintenance

* Update tests when API changes
* Remove deprecated test methods
* Keep test data realistic
* Document complex test scenarios
* Review and refactor tests regularly
* Keep tests aligned with current best practices

### Feign Integration Tests

#### Overview

Apache Fineract is migrating its integration tests from REST Assured to the generated Feign client (`fineract-client-feign`), so that tests drive the server through the same strongly typed, OpenAPI-derived models that API consumers use. A test written against the generated client stops compiling when the API contract changes, rather than failing at runtime â or, worse, continuing to pass against a payload the server no longer produces.

The shared machinery is the `client/feign` package tree â the `FeignLoanTestBase` and `FeignSavingsTestBase` base classes and the helpers under `client/feign/helpers` â together with the `FeignIntegrationTest` root base class one directory above it and the `FineractFeignClientHelper` client factory in `common`. Most migrated tests sit alongside the unmigrated ones in the `org.apache.fineract.integrationtests` package and reach the client by extending one of those base classes.

A Checkstyle rule rejects REST Assured imports in every file except those listed in a baseline of files that still use it. The baseline only shrinks: each migration removes entries from it, so neither a new test nor a migrated one can bring REST Assured back.

This chapter covers the guardrail and the conventions that apply to tests written against the Feign client. For prerequisites, database setup, and how to run a suite, see the Integration Testing chapter.

#### The Guardrail

##### How It Works

An `IllegalImport` check in `config/checkstyle/checkstyle.xml` rejects any `io.restassured` import, and a `SuppressionFilter` exempts the files listed in `config/checkstyle/restassured-baseline.xml`:

```xml
<module name="SuppressionFilter">
    <property name="file" value="${config_loc}/restassured-baseline.xml"/>
</module>
```

```xml
<module name="IllegalImport">
    <property name="id" value="FeignNoRestAssured" />
    <property name="regexp" value="true" />
    <property name="illegalPkgs" value="^io\.restassured" />
    <message key="import.illegal"
             value="Integration tests must call the server through the generated Feign client, not REST Assured: ''{0}''. Do not add this file to restassured-baseline.xml." />
</module>
```

Each baseline entry names one file by its full path and carries the check’s `id`, so it exempts that file from this check alone and leaves every other check untouched:

```xml
<suppress id="FeignNoRestAssured" files="[/\\]integration-tests[/\\]src[/\\]test[/\\]java[/\\]org[/\\]apache[/\\]fineract[/\\]integrationtests[/\\]StaffTest\.java$"/>
```

The check runs as part of `checkstyleTest`, which the `build-quality-checks.yml` workflow executes on every pull request. A violation fails the build.

##### The Baseline

The baseline lists every file that imported REST Assured when the check was widened to the whole tree. Checkstyle selects files by path, not by supertype, so a plain ban would have failed on those files at once; the baseline lets the ban apply everywhere else from the start.

* A new file that imports REST Assured fails the build.
* A migrated file that imports REST Assured again fails the build, because it is no longer listed.
* A listed file builds as before, so work on unmigrated tests is not blocked.

The list only shrinks. A PR that removes the last REST Assured import from a file deletes that file’s entry in the same change. Never add an entry: a file that needs REST Assured to pass the check needs migrating instead. Once the list is empty, the baseline, the check and the `io.rest-assured` dependency are removed together, after which a REST Assured import no longer compiles.

The check works per file. New REST Assured code inside a file that is still listed is not caught, so reviewers still watch for it until that file is migrated.

##### What the Check Does and Does Not Catch

The `Utils.performServerGet`, `performServerPost`, `performServerPut` and `performServerDelete` helpers in `org.apache.fineract.integrationtests.common` are the other common route back to REST Assured. Every one of those overloads takes an `io.restassured.specification.RequestSpecification` as its first parameter, so reaching them normally requires the forbidden import.

The check reads import statements only, so it is a deterrent rather than a proof. Two routes get past it: a fully qualified reference such as `io.restassured.RestAssured.baseURI`, and a `var` that infers a REST Assured type from another method’s return value without ever naming it. Neither appears in the tree today, and neither is something a contributor writes by accident, but a reviewer should not treat a green build as evidence that no REST Assured call exists.

Utility methods on `Utils` that do not touch the transport â `uniqueRandomStringGenerator`, `getLocalDateOfTenant`, `getDoubleValue`, `dateFormatter` â are unaffected and are used widely by migrated tests.

##### Running Locally

```bash
./gradlew :integration-tests:checkstyleTest :oauth2-tests:checkstyleTest :twofactor-tests:checkstyleTest
```

The report is written to each module’s `build/reports/checkstyle/` directory.

The task compiles the test sources first, which for this module means generating both clients. No server is involved: nothing in the build starts one, so a static check never needs a running instance.

##### When the Check Fires

A violation means a call is being made outside the generated client. Resolve it in this order:

1. **The endpoint is in the generated client.** Use it. This is the common case â the generated client covers the public API surface, including the `/v1/internal` endpoints used by tests.
2. **The endpoint is in the client, but the generated model is missing a field you need.** Fix the schema at source. See Fixing a Generated Model at Source.
3. **The generated client cannot express the call.** Where an endpoint declares no response schema the generator types the result as a bare `String` â `retrieveOneSavingsAccountTransaction` is one example â and some multi-step commands are not modelled at all. Give the endpoint an `@ApiResponse` schema where you can (IT-06); otherwise call it over plain HTTP and add a Javadoc comment stating why the typed client cannot express it.

Suppressing the rule, adding the file to the baseline, dropping the assertion, or substituting a different field are not resolutions. See rules IT-05 and IT-09.

#### Writing a Feign Integration Test

##### Test Class Layout

Loan tests extend `FeignLoanTestBase`, which supplies the client, the shared helpers, and the accounting and schedule verification methods. Savings tests extend `FeignSavingsTestBase`.

```java
package org.apache.fineract.integrationtests.client.feign.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.apache.fineract.client.models.GetLoansLoanIdResponse;
import org.apache.fineract.client.models.GetLoansLoanIdStatus;
import org.apache.fineract.client.models.PostLoanProductsRequest;
import org.apache.fineract.integrationtests.client.feign.FeignLoanTestBase;
import org.apache.fineract.integrationtests.common.Utils;
import org.junit.jupiter.api.Test;

public class FeignLoanCreationTest extends FeignLoanTestBase {

    @Test
    void testLoanRepayment_FullRepayment() {
        Long clientId = createClient();
        PostLoanProductsRequest productRequest = onePeriod30DaysNoInterest();
        Long productId = createLoanProduct(productRequest);
        String todayDate = Utils.dateFormatter.format(Utils.getLocalDateOfTenant());
        Long loanId = createApproveAndDisburseLoan(clientId, productId, todayDate, 1000.0, 1);

        Long repaymentId = addRepayment(loanId, repayment(1000.0, todayDate));
        assertNotNull(repaymentId);

        GetLoansLoanIdResponse loan = getLoanDetails(loanId);
        verifyLoanStatus(loan, GetLoansLoanIdStatus::getClosedObligationsMet);
        assertEquals(0.0, Utils.getDoubleValue(loan.getSummary().getTotalOutstanding()));
    }
}
```

`FeignLoanTestBase` assigns its helper fields in a `@BeforeAll` named `setupHelpers`. A subclass that declares its own `@BeforeAll` must give it a different name â a static method with the same signature hides the inherited one, and the helpers are then never assigned.

##### Obtaining the Client Directly

Inside a test, `fineractClient()` returns the client the base class is using. `FineractFeignClientHelper.getFineractFeignClient()` returns the same shared instance, authenticated with the default backend credentials, and is what helpers outside the base class use. Call `createNewFineractFeignClient(username, password)` when a test needs a different user.

##### Calling the API

Wrap calls in the `FeignCalls` helpers from `org.apache.fineract.client.feign.util` rather than invoking the API interface directly:

| Method | Use |
| --- | --- |
| `ok(…​)` | A call expected to succeed, returning a typed body. |
| `executeVoid(…​)` | A call expected to succeed with no response body. |
| `fail(…​)` | A call expected to fail; returns the `CallFailedRuntimeException` for assertion. |
| `failVoid(…​)` | As `fail(…​)`, for a call with no response body. |
| `execute(…​)` | A call whose raw `FeignException` the test handles itself. |

A direct invocation throws a raw `FeignException`, which carries the HTTP status but not the wrapped error detail the assertion helpers expect. `ok(…​)` and `fail(…​)` translate it into `CallFailedRuntimeException`.

##### Asserting Failures

`FeignLoanTestBase.assertErrorGlobalisationCode(exception, expectedCode)` asserts the specific error code. The top-level `userMessageGlobalisationCode` is often a generic wrapper â `validation.msg.validation.errors.exist` for a validation failure, `validation.msg.domain.rule.violation` for a domain rule â with the meaningful code in the first element of the `errors` array. The helper returns the top-level code unless it is one of those two wrappers, in which case it descends into `errors[0]`. Expect the specific code in both cases.

```java
CallFailedRuntimeException exception = fail(
        () -> fineractClient().loans().handleCommandsLoan(loanId, request, Map.of("command", "approve")));
assertEquals(403, exception.getStatus());
assertErrorGlobalisationCode(exception, "error.msg.loan.approval.cannot.be.a.future.date");
```

#### Conventions

The following rules are drawn from review feedback on the migration pull requests. They are referenced by identifier in code review.

##### Transport

| Rule | Description |
| --- | --- |
| IT-01 | Call the server through the generated Feign client. REST Assured is not permitted in the `…​client.feign` package tree; the Checkstyle rule above enforces this. |
| IT-02 | Use the `FeignCalls` helpers rather than invoking the generated API interface directly, so failures arrive as `CallFailedRuntimeException`. |
| IT-03 | Use the Feign client, not the legacy Retrofit client’s `Calls` or `.legacy` accessors. |
| IT-04 | Plain HTTP is acceptable only where the generated client cannot express the call, and only with a Javadoc comment recording why. |

> [!CAUTION]
> The Retrofit and Feign SDKs both publish models under `org.apache.fineract.client.models`. In `integration-tests` both are on the test classpath, and the one declared first in `dependencies.gradle` wins. When a model change appears to have no effect at runtime, check which SDK supplied the class.

##### Schema and SDK

| Rule | Description |
| --- | --- |
| IT-05 | When a generated model lacks a field the test needs, add it to the corresponding `*ApiResourceSwagger` DTO and regenerate. Do not work around the gap in the test. |
| IT-06 | Where an endpoint declares no response schema, give it one via `@ApiResponse` rather than introducing a hand-written client interface. |
| IT-07 | Schema changes must respect the API compatibility rules. See API Backward Compatibility, including its guidance on intentional breaking changes. |
| IT-08 | To send an explicit JSON `null`, mark the property `nullable` in the schema; the generator emits `JsonNullable<T>`. Do not hand-roll a request model. |

After changing a Swagger DTO, regenerate the client and compile every module that consumes it, not only the one under test:

```bash
# Regenerate both clients
./gradlew :fineract-client:cleanupGeneratedJavaFiles \
          :fineract-client-feign:cleanupGeneratedJavaFiles

# Then compile the consumers
./gradlew :fineract-provider:compileTestJava \
          :integration-tests:compileTestJava
```

`cleanupGeneratedJavaFiles` depends on `buildJavaSdk`, so it regenerates and then copies the result into `build/generated/java`. Running `buildJavaSdk` on its own stops before that copy and leaves the sources the compiler actually uses unchanged. Neither task compiles anything downstream, which is why the second command is needed â a schema change that breaks a consumer is otherwise found only in CI.

Regenerate both clients together. `integration-tests` compiles against both, and changing one alone leaves the two disagreeing about the same model class.

##### Assertions

| Rule | Description |
| --- | --- |
| IT-09 | Never weaken or delete a verification because the generated model does not expose the field. Fix the model (IT-05) or keep the check by another route. |
| IT-10 | Assert the specific status code and error code, not merely that the call threw. |
| IT-11 | Verify an unordered collection by removing each expected element from a mutable copy of the actual collection, then asserting the copy is empty. A size check combined with `anyMatch` passes on duplicates. |
| IT-12 | A `null` expected value means "assert this is null". Do not redefine it to mean "skip this check". |
| IT-13 | A migration must not change an expected value. If a migrated test needs a different number to pass, establish which value the server actually produces before changing it. |

```java
List<JournalEntry> remaining = new ArrayList<>(actualEntries);
for (JournalEntry expected : expectedEntries) {
    Optional<JournalEntry> match = remaining.stream().filter(a -> matches(a, expected)).findFirst();
    assertTrue(match.isPresent(), "Missing entry: " + expected);
    remaining.remove(match.get());
}
assertTrue(remaining.isEmpty(), "Unexpected entries: " + remaining);
```

##### Test Structure

| Rule | Description |
| --- | --- |
| IT-14 | A helper used by one test class belongs in that class. Only behaviour shared across classes belongs on the base class or in a helper under `client/feign/helpers`. |
| IT-15 | Return the response model from a helper, not just the identifier, so callers can assert on the rest of the response without a second request. |
| IT-16 | Use the generated enums and the shared constants in `client/feign/modules/FeignTestConstants`. Do not repeat literal codes and identifiers. |
| IT-17 | Name variables and helper methods for what they hold or do in domain terms, not for their type. |

#### Fixing a Generated Model at Source

When a field the server accepts or returns is absent from the generated model, the fix belongs in the Swagger DTO on the server, not in the test.

1. Locate the `*ApiResourceSwagger` class for the resource â for example `LoanProductsApiResourceSwagger` for `/loanproducts`.
2. Add the field to the request or response DTO, matching the name and type the server already reads or writes.
3. Regenerate both SDKs and compile every consuming module, using the command under Schema and SDK.
4. Confirm the API compatibility check still passes, or document the breaking change as described in API Backward Compatibility.
5. Replace the workaround in the test with the generated accessor.

Adding a field to a response schema and widening a request type are both additive from the perspective of an existing consumer, but the compatibility checker reports some widening changes as violations. API Backward Compatibility describes how to handle a violation that is deliberate.

#### Verifying a Change

| Rule | Description |
| --- | --- |
| IT-18 | Compilation and `spotlessCheck` are not verification. Run the tests you touched against a running instance. |
| IT-19 | The build does not start a server. Bring an instance up first â see Fineract Instance â or every test in the suite fails on connection refused. |
| IT-20 | Before attributing a failure to your change, run the test at the base commit on the same instance. Some tests fail independently of the change under review. |

Against a locally running instance:

```bash
./gradlew :integration-tests:test \
  --tests FeignLoanCreationTest
```

The suite talks to whatever is listening at `BACKEND_PROTOCOL`://`BACKEND_HOST`:`BACKEND_PORT`, defaulting to
`localhost:8443`. Fineract Instance covers the ways to bring that instance up.

#### Tool Reference

* **Checkstyle**: [checkstyle](https://checkstyle.org/) 13.4.2, configured in `config/checkstyle/checkstyle.xml`
* **IllegalImport**: [check reference](https://checkstyle.org/checks/imports/illegalimport.html)
* **SuppressionFilter**: [filter reference](https://checkstyle.org/filters/suppressionfilter.html)
* **Baseline**: `config/checkstyle/restassured-baseline.xml`
* **Workflow**: `.github/workflows/build-quality-checks.yml`
* **Generated client**: `fineract-client-feign`
* **Migrated tests**: `integration-tests/src/test/java/org/apache/fineract/integrationtests/client/feign`