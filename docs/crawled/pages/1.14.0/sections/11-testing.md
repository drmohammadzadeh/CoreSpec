---
source_url: https://fineract.apache.org/docs/1.14.0#_testing
title: "Testing"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/1.14.0
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

* **Java 21**: Apache Fineract requires Java 21 (Azul Zulu JDK recommended)
* **Database**: MariaDB 11.5.2, PostgreSQL 17.4, or MySQL 9.1
* **Git**: For source code management
* **Gradle 8.14.3**: Included via wrapper

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
curl -X PUT https://localhost:8443/fineract-provider/api/v1/configurations/name/enable-business-date \
  -H "Authorization: Basic bWlmb3M6cGFzc3dvcmQ=" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

**Verification**:

```bash
mysql -u root -pmysql fineract_default -e \
  "SELECT * FROM c_configuration WHERE name LIKE '%business%';"
```

#### Running E2E Tests

##### Complete Workflow

###### Step 1: Start Fineract

```bash
# Start Fineract in background
./gradlew bootRun
```

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
import java.io.IOException;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.apache.commons.io.IOUtils;
import org.apache.fineract.template.domain.Template;
import org.apache.fineract.template.domain.TemplateMapper;
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

    private String compile(String templateText, Map<String, Object> scope) throws IOException {
        List<TemplateMapper> mappers = new ArrayList<>();
        Template template = new Template("TemplateName", templateText, null, null, mappers);
        return tms.compile(template, scope);
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
* **Framework**: JUnit 5 with REST Assured for HTTP communication
* **Base Class**: Most tests extend `BaseLoanIntegrationTest` or `IntegrationTest`
* **Client Library**: Uses Fineract client library for type-safe API interactions
* **Prerequisites**: Running Apache Fineract instance (default: [localhost:8443](https://localhost:8443))

##### Key Characteristics

* Tests run against a live Fineract instance
* Validates end-to-end API functionality
* Tests business logic, validation rules, and workflows
* Includes accounting verification and data integrity checks
* Uses real database transactions
* Tests can be run individually or as a suite

#### Prerequisites

##### Required Software

* **Java 21**: Apache Fineract requires Java 21 (Azul Zulu JDK recommended)
* **Database**: MariaDB 11.5.2, PostgreSQL 17.4, or MySQL 9.1
* **Git**: For source code management
* **Gradle 8.14.3**: Included via wrapper
* **12GB RAM**: Recommended for test execution

##### Database Setup

Before running integration tests, ensure the databases are created:

```bash
# Create required databases
./gradlew createDB -PdbName=fineract_tenants
./gradlew createDB -PdbName=fineract_default
```

##### Fineract Instance

Integration tests run fineract instance from cargo plugin by default.

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

```bash
# Start Fineract in background
./gradlew bootRun &

# Wait for startup (manual check)
curl -k https://localhost:8443/actuator/health
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

```bash
# Run tests excluding specific packages
./gradlew :integration-tests:test --tests "*" \
  --exclude "*Deprecated*"

# Run only fast tests (custom tag)
./gradlew :integration-tests:test --tests "*Fast*"
```

###### Parallel Execution

```bash
# Run tests in parallel
./gradlew :integration-tests:test --parallel --max-workers=4

# Set custom thread count
./gradlew :integration-tests:test --parallel --max-workers=8
```

> [!WARNING]
> Some integration tests may have dependencies on shared state. Use parallel execution carefully and ensure tests are properly isolated.

###### Run with Custom JVM Arguments

```bash
# Increase heap size for large test suites
./gradlew :integration-tests:test -Xmx4g

# Enable debugging
./gradlew :integration-tests:test --debug-jvm
```

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

##### BaseLoanIntegrationTest Overview

`BaseLoanIntegrationTest` is the comprehensive base test class for loan-related integration tests. It provides:

###### Pre-configured Loan Product Creation

```java
// Create standard loan products
createOnePeriod30DaysLongNoInterestPeriodicAccrualProduct()
create4IProgressive() // Progressive loan products
create4IProgressiveWithCapitalizedIncome() // With capitalized income
createOnePeriod30DaysPeriodicAccrualProductWithAdvancedPaymentAllocation()
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

```java
// Create progressive loan product
Long productId = create4IProgressive();

// Apply and approve
Long loanId = applyAndApproveProgressiveLoan(clientId, productId,
    amount, numberOfRepayments, interestRate);

// Test advanced features
testCapitalizedIncome(loanId);
testDownPayment(loanId);
testAdvancedPaymentAllocation(loanId);
```

#### Writing Integration Tests

##### Test Development Guidelines

###### 1. Create Test Class

Create a new test class in `integration-tests/src/test/java/org/apache/fineract/integrationtests/`:

```java
package org.apache.fineract.integrationtests;

import org.apache.fineract.integrationtests.common.Utils;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;

public class MyNewFeatureIntegrationTest extends BaseLoanIntegrationTest {

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

    @Test
    public void testMyNewFeature() {
        // Test implementation
    }
}
```

###### 2. Use Helper Classes

Leverage existing helper classes:

```java
// Client operations
ClientHelper clientHelper = new ClientHelper(requestSpec, responseSpec);
Long clientId = clientHelper.createClient(...);

// Loan operations
LoanTransactionHelper loanHelper = new LoanTransactionHelper(requestSpec, responseSpec);
Long loanId = loanHelper.applyLoan(...);

// Account operations
AccountHelper accountHelper = new AccountHelper(requestSpec, responseSpec);

// Business date operations
BusinessDateHelper businessDateHelper = new BusinessDateHelper();
businessDateHelper.updateBusinessDate(...);

// COB operations
InlineLoanCOBHelper cobHelper = new InlineLoanCOBHelper(requestSpec, responseSpec);
cobHelper.executeInlineCOB(loanId);
```

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

# Restart Fineract if needed
pkill -f bootRun
./gradlew bootRun &
```

###### Authentication Failures

**Symptom**: Tests fail with 401 or 403 errors

**Solutions**:

```bash
# Check default credentials
mysql -u root -pmysql fineract_default -e \
  "SELECT username, password FROM m_appuser WHERE username = 'mifos';"

# Reset credentials if needed
mysql -u root -pmysql fineract_default -e \
  "UPDATE m_appuser SET password = '5jdQ3dNQXHPzCuBbZVdQZ2XnVlPc3l2l' \
   WHERE username = 'mifos';"

# Verify connection settings
echo "Protocol: ${BACKEND_PROTOCOL:-https}"
echo "Host: ${BACKEND_HOST:-localhost}"
echo "Port: ${BACKEND_PORT:-8443}"
```

###### Data Inconsistency

**Symptom**: Tests fail due to unexpected data state

**Solutions**:

```bash
# Reset database
mysql -u root -pmysql -e "DROP DATABASE fineract_default;"
mysql -u root -pmysql -e "DROP DATABASE fineract_tenants;"

# Recreate databases
./gradlew createDB -PdbName=fineract_tenants
./gradlew createDB -PdbName=fineract_default

# Restart Fineract
pkill -f bootRun
./gradlew bootRun &
```

###### Test Timeout

**Symptom**: Tests hang or timeout

**Solutions**:

```bash
# Increase test timeout
./gradlew :integration-tests:test -Dtest.timeout=600

# Check for database locks
mysql -u root -pmysql fineract_default -e "SHOW PROCESSLIST;"

# Kill long-running queries
mysql -u root -pmysql fineract_default -e "KILL <process_id>;"
```

###### Memory Issues

**Symptom**: OutOfMemoryError during test execution

**Solutions**:

```bash
# Increase heap size
./gradlew :integration-tests:test -Xmx4g -Xms2g

# Run fewer tests in parallel
./gradlew :integration-tests:test --max-workers=2

# Clean build directory
./gradlew clean
```

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
mysql -u root -pmysql fineract_default -e \
  "SELECT id, account_no, loan_status_id, principal_amount \
   FROM m_loan ORDER BY id DESC LIMIT 10;"

# Check transactions
mysql -u root -pmysql fineract_default -e \
  "SELECT loan_id, transaction_type_enum, amount, transaction_date \
   FROM m_loan_transaction WHERE loan_id = <loan_id>;"

# Check journal entries
mysql -u root -pmysql fineract_default -e \
  "SELECT entry_date, account_id, type_enum, amount \
   FROM acc_gl_journal_entry WHERE loan_id = <loan_id>;"

# Check configurations
mysql -u root -pmysql fineract_default -e \
  "SELECT name, enabled FROM c_configuration \
   WHERE name LIKE '%business%' OR name LIKE '%enable%';"
```

###### API Response Debugging

Add logging to test methods:

```java
Response response = loanHelper.applyLoan(...);
System.out.println("Response: " + response.asString());
System.out.println("Status Code: " + response.getStatusCode());

// Or use logger
log.info("Response: {}", response.asString());
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

* Extend appropriate base classes (`BaseLoanIntegrationTest`, `IntegrationTest`)
* Use descriptive test method names that explain what is being tested
* Group related tests in the same test class
* Use `@BeforeEach` for setup and `@AfterEach` for cleanup
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