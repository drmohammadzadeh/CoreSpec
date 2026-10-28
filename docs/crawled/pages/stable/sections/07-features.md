---
source_url: https://fineract.apache.org/docs/1.16.0#_features
title: "Features"
depth: 1
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/stable
---

## Features

This section covers specific features and functionality available in Apache Fineract.

### Capitalized Income

#### Overview

Capitalized Income (formerly referred to as Origination Fee) in Apache Fineract is a fee-based or interest-based income item that is added to the principal of a loan and amortized over time. It is designed to be applied at disbursement and is treated as part of the loan’s principal for repayment and interest calculations.

#### Purpose

This functionality enables financial institutions to:

* Recognize deferred income (fees or interest) systematically over the loan term
* Align accounting practices with regulatory requirements
* Improve income recognition accuracy

#### Supported Loan Type

> [!IMPORTANT]
> Capitalized Income is only supported for:
> * Progressive Loan Schedules
> * Advanced Payment Allocation Strategy
> Other loan schedule types and transaction processing strategies are not supported.

#### Configuration at Loan Product Level

Capitalized income must be configured on the loan product.

The configuration options include:

* **Enable Capitalized Income**: Boolean toggle (default: disabled)
* **Calculation Mode**: Only "Flat" is currently supported
  
  
  
  
  
  * Later "Percentage based" can be introduced
* **Amortization Strategy**: Only "EQUAL_AMORTIZATION" is supported
  
  
  
  
  
  * Daily equal portions are recognized over the life of the loan
  * Later other strategies can be introduced
* **Income Type**: Specifies allocation rule. Defines which "balance category" to be used.

> [!NOTE]
> In Fineract, balance of a transaction is either: Principal, Fee, Penalty, Interest or overpayment

Options:
* FEE (default)
* INTEREST

##### GL Mapping

Required GL Account mappings when Capitalized Income is enabled:

* **Deferred Income (Liability)**: `deferredIncomeLiabilityAccountId` - mandatory when enabled
* **Income from Capitalization (Income)**: `incomeFromCapitalizationAccountId` - mandatory when enabled

> [!IMPORTANT]
> Both GL accounts become mandatory when `enableIncomeCapitalization` is set to `true`.

##### Configuration Dependencies

When `enableIncomeCapitalization` is set to `true`, all following parameters become mandatory:

* `capitalizedIncomeCalculationType` - must be "FLAT"
* `capitalizedIncomeStrategy` - must be "EQUAL_AMORTIZATION"
* `capitalizedIncomeType` - must be "FEE" or "INTEREST"
* `deferredIncomeLiabilityAccountId` - must reference a valid GL account
* `incomeFromCapitalizationAccountId` - must reference a valid GL account

#### Behavior and Calculations

* Capitalized income is added via API on or after the first disbursement date
* It is treated as a principal portion, recalculating the repayment schedule accordingly
* Interest and amortization schedules are updated to include the capitalized income amount
* Validated using formula: `(Total Disbursed + Current Capitalized Income + New Transaction Amount) â¤ Max Amount`, where Max Amount depends on loan product configuration: if `allowApprovedDisbursedAmountsOverApplied = true` uses `getOverAppliedMax(loan)`, otherwise uses `getApprovedPrincipal()`

##### Daily Amortization

* Recognized daily using the configured strategy
* Recognized portions move from Deferred Income to Income from Capitalization

###### Special Handling

* **Preclosure**: Remaining balance recognized in full on the preclosure date
* **Charge-off**: Amortization stops and remaining balance is charged off

#### Transaction Types Introduced

* Capitalized Income
* Capitalized Income Amortization
* Capitalized Income Adjustment
* Capitalized Income Amortization Adjustment

##### Capitalized Income Transaction

The Capitalized Income transaction in Apache Fineract performs the following actions:

* Adds a specified amount to the loan principal
  
  
  
  
  
  * Considered a deferred income item (such as a fee or interest)
  * Booked as part of the loan’s principal
  * Added post-disbursement and only if the loan type supports it (currently: Progressive Loans)
* Creates a distinct loan transaction
  
  
  
  
  
  * Separately tracked with its own transaction type ("Capitalized Income")
  * Not merged with disbursements or repayments
* Updates the loan schedule
  
  
  
  
  
  * Recalculates amortization and interest schedule to include the added amount in the outstanding principal
* Triggers accounting entries
  
  
  
  
  
  * Debits "Loan Portfolio" (Asset)
  * Credits "Deferred Income" (Liability)
  * Does not recognize income upfront
* Initiates daily amortization
  
  
  
  
  
  * Source for daily income recognition through "Capitalized Income Amortization" transactions
  * Progressively converts the deferred amount to recognized income

###### Accounting Entries

| Scenario | Debit |
| --- | --- |
| Credit | Capitalized Income |
| Loan Portfolio (Asset) | Deferred Income (Liability) |

##### Capitalized Income Amortization

A Capitalized Income Amortization transaction in Apache Fineract does the following:

* **Recognizes Deferred Income Over Time**: Transfers a portion of the capitalized income (originally posted as a liability) into recognized income (posted as interest or fee income), based on a configured daily amortization strategy.
* **Daily Posting**: The system automatically creates this transaction each day from the date of capitalized income until the loan maturity or until the full amount is amortized. This is handled by a background job during the COB (Close of Business) process.
* **Uses Equal Amortization**: The default and only supported strategy is Equal Amortization, which divides the total capitalized income evenly over the remaining number of days until the loan matures.

###### Accounting Entries

| Scenario | Debit |
| --- | --- |
| Credit | Daily amortization |
| Deferred Income (Liability) | Income from Capitalization (Income) |

###### Stops on Events

* **Preclosure**: Triggers final amortization for remaining unrecognized income
* **Charge-off**: Halts further amortization; the remaining deferred income is charged off

> [!NOTE]
> Reversal Handling: If the original Capitalized Income transaction is reversed, all associated amortization transactions are also reversed via "Capitalized Income Amortization Adjustment" transactions.

##### Capitalized Income Adjustment

A Capitalized Income Adjustment transaction in Apache Fineract serves to reduce the balance of an existing capitalized income transaction.

###### Purpose

* Correct overcharged or misposted capitalized income amounts
* Reflect fee waivers or negotiated reductions
* Support backdated corrections if needed

###### Transaction Behavior

* It is a credit-type transaction, reducing the capitalized income balance
* Treated similarly to other credit transactions and follows a defined allocation strategy
* Can be backdated, but not dated before the original capitalized income transaction

###### Validation Rules

* The adjustment amount must not exceed the remaining amount (original capitalized income amount minus total previous adjustments)
* Adjustment is linked to a specific Capitalized Income transaction (by ID)
* Multiple adjustments can be made against the same original transaction
* Adjustments can be reversed if needed

###### Accounting Entries

| Scenario | Debit | Credit |
| --- | --- | --- |
| Adjustment â¤ unrecognized balance | Deferred Income (Liability) | Loan Portfolio (Asset) |
| Adjustment > unrecognized balance | Deferred Income (Liability) | Loan Portfolio (Asset) |

###### Business Event Triggers

* Triggers "Capitalized Income Adjustment" event
* Updates loan balance and possibly loan status depending on impact

###### Impact

* Reduces amortization basis
* May modify future amortization amounts
* Repayment schedule is not affected directly unless recalculated manually

##### Capitalized Income Amortization Adjustment

A Capitalized Income Amortization Adjustment in Apache Fineract is a special transaction type used to reverse previously recognized income from capitalized income amortization.

###### Purpose

* Automatically generated when a Capitalized Income transaction is reversed or when backdated Capitalized Income Adjustment affects amortization balances
* Reverses all already recognized portions (amortized income) linked to the original Capitalized Income transaction

###### When It Occurs

* Created by daily amortization (COB) or final amortization (triggered on loan closure, charge-off, or by any backdated transaction that affects capitalized income balances)
* Reverses previously recognized income when amortization needs to be adjusted
* Restores Deferred Income balances and reverses income recognition

###### Accounting Entries

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Capitalized Income Amortization Adjustment | Income from Capitalization (Income) | Deferred Income (Liability) |

###### Key Characteristics

* **System-Generated Only**: Cannot be created manually by API or UI
* **Ensures Accounting Integrity**: Keeps amortized and unrecognized balances aligned after reversals
* **Non-monetary transaction - does not trigger balance changed or status update events**

###### Business Events

* Triggers a new business event: Capitalized Income Amortization Adjustment

#### API Endpoints

##### Configure Capitalized Income on Loan Product

* **Endpoint**: `/loanproducts`
* **Method**: `POST`

```json
{
    ...
    "enableIncomeCapitalization": true,     // Mandatory
    "capitalizedIncomeCalculationType": "FLAT",  // Mandatory when enabled
    "capitalizedIncomeStrategy": "EQUAL_AMORTIZATION",  // Mandatory when enabled
    "capitalizedIncomeType": "FEE",  // Mandatory when enabled
    "deferredIncomeLiabilityAccountId": 123,  // Mandatory when enabled
    "incomeFromCapitalizationAccountId": 456  // Mandatory when enabled
}
```

##### Add Capitalized Income

* **Endpoint**: `/loans/{loanId}/transactions?command=capitalizedIncome`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions?command=capitalizedIncome`
* **Method**: `POST`

```json
{
    "transactionDate": "2025-05-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en",                     // Mandatory
    "transactionAmount": 100.0,         // Mandatory
    "paymentTypeId": 1,                 // Optional
    "note": "Capitalized income fee",   // Optional
    "externalId": "CINCOME-001"         // Optional
}
```

##### Get Capitalized Income Amortization Info

* **Endpoint**: `/loans/{loanId}/deferredincome`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/deferredincome`
* **Method**: `GET`

###### Response Body

```json
{
    "capitalizedIncomeData": [
        {
            "amount": 50.0,                    // Total capitalized income amount
            "amortizedAmount": 1.1,            // Amount already amortized
            "unrecognizedAmount": 48.9,        // Amount not yet amortized
            "amountAdjustment": 0.0,           // Any adjustments made
            "chargedOffAmount": 0.0            // Amount charged off (if applicable)
        }
    ]
}
```

##### Add Capitalized Income Adjustment

* **Endpoint**: `/loans/{loanId}/transactions/{capitalizedIncomeTransactionId}?command=capitalizedIncomeAdjustment`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/{capitalizedIncomeTransactionId}?command=capitalizedIncomeAdjustment`
* **Method**: `POST`

```json
{
    "transactionDate": "2025-05-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en",                     // Mandatory
    "transactionAmount": 50.0,          // Mandatory
    "paymentTypeId": 1,                 // Optional
    "note": "Capitalized income fee",   // Optional
    "externalId": "CINCOMEADJ-001"      // Optional
}
```

###### Response Body

```json
{
    "resourceId": 1,
    "resourceExternalId": "CINCOMEADJ-001"
}
```

##### Capitalized Income Template API (to retrieve limits)

* **Endpoint**: `/loans/{loanId}/transactions/template?command=capitalizedIncome`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/template?command=capitalizedIncome`
* **Method**: `GET`

```json
{
    "paymentTypeOptions": [],  // List of available payment types
    "currency": {...},         // Currency configuration
    "date": [2025, 5, 29],     // Return the current date
    "amount": 0                // Return the maximum amount that can be capitalized (approved amount - disbursed amount - capitalized income)
}
```

##### Capitalized Income Adjustment Template API (to retrieve limits)

* **Endpoint**: `/loans/{loanId}/transactions/template?command=capitalizedIncomeAdjustment&transactionId={capitalizedIncomeTransactionId}`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/template?command=capitalizedIncomeAdjustment&transactionId={capitalizedIncomeTransactionId}`
* **Method**: `GET`

```json
{
    "paymentTypeOptions": [],  // List of available payment types
    "currency": {...},         // Currency configuration
    "date": [2025, 5, 29],     // Return the current date
    "amount": 0                // Return the maximum amount that can be adjusted (capitalized income - adjustment)
}
```

#### Accounting Entries

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Capitalized Income | Loan Portfolio (Asset) | Deferred Income (Liability) |
| Capitalized Income Amortization | Deferred Income (Liability) | Income from Capitalization (Income) |
| Capitalized Income Adjustment | Deferred Income (Liability) | Loan Portfolio (Asset) |
| Capitalized Income Amortization Adjustment | Income from Capitalization (Income) | Deferred Income (Liability) |

#### Business Events

##### Triggered for Capitalized Income

* `LoanCapitalizedIncomeTransactionCreatedBusinessEvent`
* `LoanBalanceChangedBusinessEvent`

##### Daily Amortization

* `LoanCapitalizedIncomeAmortizationTransactionCreatedBusinessEvent`
* `LoanCapitalizedIncomeAmortizationAdjustmentTransactionCreatedBusinessEvent`

##### Capitalized Income Adjustment

* `LoanCapitalizedIncomeAdjustmentTransactionCreatedBusinessEvent`
* `LoanBalanceChangedBusinessEvent`

##### Reversal

* `LoanAdjustTransactionBusinessEvent`

#### Database Structure

##### Configuration

###### Stored on Loan Product (m_product_loan)

| Field | Data Type | Description |
| --- | --- | --- |
| `enable_income_capitalization` | `BOOLEAN` | Enable capitalized income feature (default: `false`) |
| `capitalized_income_calculation_type` | `VARCHAR` | Calculation method (ENUM: `FLAT`) |
| `capitalized_income_strategy` | `VARCHAR` | Amortization strategy (ENUM: `EQUAL_AMORTIZATION`) |
| `capitalized_income_type` | `VARCHAR` | Income type (ENUM: `FEE`, `INTEREST`) |

###### Stored on Loan (m_loan)

| Field | Data Type | Description |
| --- | --- | --- |
| `enable_income_capitalization` | `BOOLEAN` | Enable capitalized income feature (default: `false`) |
| `capitalized_income_calculation_type` | `VARCHAR` | Calculation method (ENUM: `FLAT`) |
| `capitalized_income_strategy` | `VARCHAR` | Amortization strategy (ENUM: `EQUAL_AMORTIZATION`) |
| `capitalized_income_type` | `VARCHAR` | Income type (ENUM: `FEE`, `INTEREST`) |

##### Balances

###### On Loan

| Field | Data Type | Description |
| --- | --- | --- |
| `capitalized_income_derived` | `DECIMAL(19,6)` | Total capitalized income amount (nullable) |
| `capitalized_income_adjustment_derived` | `DECIMAL(19,6)` | Total adjustment amount (nullable) |

###### Capitalized Income Balance (m_loan_capitalized_income_balance)

Each capitalized income has its own balance (1 row for each transaction)

| Field | Data Type | Description |
| --- | --- | --- |
| `id` | `BIGINT` | Unique identifier (Primary Key) |
| `version` | `BIGINT` | Version for optimistic locking |
| `loan_id` | `BIGINT` | Associated loan ID (Foreign Key, NOT NULL) |
| `loan_transaction_id` | `BIGINT` | Associated loan transaction ID (Foreign Key, NOT NULL) |
| `amount` | `DECIMAL(19,6)` | Capitalized income transaction amount (NOT NULL) |
| `date` | `DATE` | Capitalized income transaction date (NOT NULL) |
| `unrecognized_amount` | `DECIMAL(19,6)` | Amortization - not yet recognized amount (NOT NULL) |
| `charged_off_amount` | `DECIMAL(19,6)` | Charged-off balance (nullable) |
| `amount_adjustment` | `DECIMAL(19,6)` | Total adjustment amount (nullable) |
| `created_by` | `BIGINT` | Audit field - user who created the record |
| `created_on_utc` | `DATETIME` | Creation timestamp (UTC) |
| `last_modified_by` | `BIGINT` | Last modifier user ID |
| `last_modified_on_utc` | `DATETIME` | Last modification timestamp (UTC) |

##### Constraints

* **Foreign Key Constraints:**
  
  
  
  
  
  * `loan_id` references `m_loan(id)`
  * `loan_transaction_id` references `m_loan_transaction(id)`
  * `created_by` references `m_appuser(id)`
  * `last_modified_by` references `m_appuser(id)`

#### Notes

> [!IMPORTANT]
> * Capitalized income transactions support backdating
> * Adjustment transactions must not predate the original capitalized income
> * No automatic reversal is supported; must be handled manually via dedicated transactions
> * Proper GL accounts must be set for Deferred Income and Income from Capitalization to enable this functionality

### Buy Down Fee

#### Overview

Buy Down Fee is a specialized fee mechanism in Apache Fineract that allows financial institutions to collect upfront fees from borrowers to reduce their effective interest rate over the loan term. This feature is particularly designed for 0% interest "buy down" loans where a merchant fee is collected and amortized into interest/fee income over the life of the loan.

The key characteristic of Buy Down Fee is that the amortized fee is **NOT visible to the customer** and **NOT affecting the repayment schedule** - it operates as a background process for proper revenue recognition while maintaining transparency in customer-facing loan terms.

#### Purpose

This functionality enables financial institutions to:

* **Interest Rate Reduction**: Borrowers can reduce their effective interest rate by paying an upfront fee
* **Merchant Fee Support**: Enables 0% interest loan products with merchant-paid fees
* **Revenue Recognition**: Provides controlled amortization of fee income over the loan term
* **Customer Transparency**: Fee amortization is invisible to customers, maintaining clean loan presentation
* **Accounting Integration**: Proper journal entries and accounting treatment for fee transactions

#### Supported Loan Type

> [!IMPORTANT]
> Buy Down Fee is only supported for loans that have **all** of the following:
> * **Advanced Payment Allocation Strategy** (transaction processing strategy)
> * **Progressive Loan Schedule** (loan schedule type)
> Other transaction processing strategies or loan schedule types are not supported.

#### Configuration at Loan Product Level

Buy Down Fee must be configured on the loan product.

The configuration options include:

* **Enable Buy Down Fee**: Boolean toggle (`enableBuyDownFee`) (default: disabled)
* **Calculation Mode**: Only "Flat" is currently supported (`buyDownFeeCalculationType`)
* **Amortization Strategy**: Only "EQUAL_AMORTIZATION" is supported (`buyDownFeeStrategy`)
  
  
  
  
  
  * Daily equal portions are recognized over the life of the loan
* **Income Type**: Specifies allocation rule (`buyDownFeeIncomeType`)

Options:
* FEE
* INTEREST

##### GL Mapping

Required GL Account mappings when Buy Down Fee is enabled:

* **Buy Down Expense Account**: `buyDownExpenseAccountId` - mandatory when enabled
* **Deferred Income Liability Account**: `deferredIncomeLiabilityAccountId` - mandatory when enabled
* **Income from Buy Down Account**: `incomeFromBuyDownAccountId` - mandatory when enabled

> [!IMPORTANT]
> All GL accounts become mandatory when `enableBuyDownFee` is set to `true`.

##### Configuration Dependencies

When `enableBuyDownFee` is set to `true`, all following parameters become mandatory:

* `buyDownFeeCalculationType` - must be "FLAT"
* `buyDownFeeStrategy` - must be "EQUAL_AMORTIZATION"
* `buyDownFeeIncomeType` - must be "FEE" or "INTEREST"
* `buyDownExpenseAccountId` - must reference a valid GL account
* `deferredIncomeLiabilityAccountId` - must reference a valid GL account
* `incomeFromBuyDownAccountId` - must reference a valid GL account

#### Validation Rules

##### Product Level Validations

* Buy Down Fee can only be enabled for Progressive Loan products
* When `enableBuyDownFee` is `true`, all related parameters become mandatory
* Calculation type must be `FLAT` (other types not yet supported)
* Strategy must be `EQUAL_AMORTIZATION` (other strategies not yet supported)
* Income type must be either `FEE` or `INTEREST`
* Both expense and income GL accounts must be provided and valid
* GL accounts must have correct account types (EXPENSE and INCOME respectively)
* `deferredIncomeLiabilityAccountId` mapping requirements:
  
  
  
  
  
  * Must be a valid LIABILITY type GL account
  * Represents temporary holding of not-yet-recognized income
  * Used to track unamortized Buy Down Fee portion
  * Cannot be zero or null when Buy Down Fee is enabled

##### Transaction Level Validations

* Buy Down Fee transactions can only be added to active loans
* Transaction amount must be positive (greater than zero)
* Transaction date cannot be before the first disbursement date
* Loan must have Buy Down Fee enabled in its product configuration
* Transaction date cannot be in the future
* Client/Group must be active
* Loan must be disbursed
* Multiple Buy Down Fee transactions per loan are supported

##### Adjustment Validations

* Original Buy Down Fee transaction must exist
* Adjustment amount cannot exceed remaining balance (amount - previous adjustments)
* Adjustment date cannot be before original transaction date
* Cannot reverse Buy Down Fee transaction if it has linked adjustments

Buy down fee adjustments are related to the buy down fee transaction (they have relation with type ADJUSTMENT between them), and there can be more than one adjustment to the same buy down fee transaction.

#### Error Responses

##### Common Error Codes

* `buy.down.fee.not.enabled`: Buy Down Fee not enabled for loan product
* `cannot.be.before.first.disbursement.date`: Invalid transaction date
* `cannot.be.more.than.remaining.amount`: Adjustment exceeds balance
* `loan.transaction.not.found`: Referenced transaction not found

##### Error Response Example

```json
{
  "developerMessage": "Buy down fee is not enabled for this loan product",
  "httpStatusCode": "400",
  "defaultUserMessage": "Buy down fee is not enabled for this loan product",
  "userMessageGlobalisationCode": "buy.down.fee.not.enabled",
  "errors": [
    {
      "developerMessage": "Buy down fee is not enabled for this loan product",
      "defaultUserMessage": "Buy down fee is not enabled for this loan product",
      "userMessageGlobalisationCode": "buy.down.fee.not.enabled",
      "parameterName": null
    }
  ]
}
```

##### Configuration Error Messages

* **"Buy Down Fee calculation type is required"**: Provide `buyDownFeeCalculationType` when enabling Buy Down Fee
* **"Buy Down Fee strategy is required"**: Provide `buyDownFeeStrategy` when enabling Buy Down Fee
* **"Buy Down Fee income type is required"**: Provide `buyDownFeeIncomeType` when enabling Buy Down Fee
* **"Buy Down expense account is required"**: Provide valid `buyDownExpenseAccountId`
* **"Deferred income liability account is required"**: Provide valid `deferredIncomeLiabilityAccountId`
* **"Income from Buy Down account is required"**: Provide valid `incomeFromBuyDownAccountId`
* **"Buy Down fees can only be added to active loans"**: Ensure loan status is ACTIVE before adding Buy Down Fee transactions

#### Behavior and Calculations

* Buy Down Fee transactions can only be added to active loans
* Transaction amount must be positive (greater than zero)
* Transaction date cannot be before the first disbursement date
* Loan must have Buy Down Fee enabled in its product configuration

##### Daily Amortization

* Recognized daily using the configured strategy
* Recognized portions move from Deferred Income to Income from Buy Down

###### Special Handling

* **Preclosure**: Remaining balance recognized in full on the preclosure date
* **Charge-off**: Amortization stops and remaining balance is charged off

#### Transaction Types Introduced

* Buy Down Fee
* Buy Down Fee Amortization
* Buy Down Fee Adjustment
* Buy Down Fee Amortization Adjustment

##### Buy Down Fee Transaction

The Buy Down Fee transaction in Apache Fineract performs the following actions:

* Creates a distinct loan transaction
  
  
  
  
  
  * Separately tracked with its own transaction type ("Buy Down Fee")
  * Not merged with disbursements or repayments
* Triggers accounting entries
  
  
  
  
  
  * Debits "Buy Down Expense Account" (Expense)
  * Credits "Deferred Income Liability Account" (Liability)
  * Does not recognize income upfront
* Initiates daily amortization
  
  
  
  
  
  * Source for daily income recognition through "Buy Down Fee Amortization" transactions
  * Progressively converts the deferred amount to recognized income

###### Accounting Entries

| Scenario | Debit |
| --- | --- |
| Credit | Buy Down Fee |
| Buy Down Expense Account | Deferred Income Liability Account |

##### Buy Down Fee Amortization

A Buy Down Fee Amortization transaction in Apache Fineract does the following:

* **Recognizes Deferred Income Over Time**: Transfers a portion of the buy down fee (originally posted as a liability) into recognized income, based on a configured daily amortization strategy.
* **Daily Posting**: The system automatically creates this transaction each day from the date of buy down fee until the loan maturity or until the full amount is amortized. This is handled by a background job during the COB (Close of Business) process.
* **Uses Equal Amortization**: The default and only supported strategy is Equal Amortization, which divides the total buy down fee evenly over the remaining number of days until the loan matures.

###### Accounting Entries

| Scenario | Debit |
| --- | --- |
| Credit | Daily amortization |
| Deferred Income Liability Account | Income from Buy Down Account |

###### Stops on Events

* **Preclosure**: Triggers final amortization for remaining unrecognized income
* **Charge-off**: Halts further amortization; the remaining deferred income is charged off using Charge-off Expense Account

##### Buy Down Fee Adjustment

A Buy Down Fee Adjustment transaction in Apache Fineract serves to reduce the balance of an existing buy down fee transaction.

###### Purpose

* Correct overcharged or misposted buy down fee amounts
* Reflect fee waivers or negotiated reductions
* Support backdated corrections if needed

###### Transaction Behavior

* It is a credit-type transaction, reducing the buy down fee balance
* Can be backdated, but not dated before the original buy down fee transaction

###### Validation Rules

* The adjustment amount cannot exceed remaining balance (amount - previous adjustments)
* Adjustment date cannot be before original transaction date
* Adjustment date cannot be before disbursement date
* Adjustment date cannot be in the future
* Cannot reverse Buy Down Fee transaction if it has linked adjustments
* Loan must be in Active, Closed, or Overpaid status
* Buy Down Fee must be enabled on the loan product
* Loan must use Progressive Schedule

###### Accounting Entries

| Scenario | Debit | Credit |
| --- | --- | --- |
| Buy Down Fee Adjustment | Deferred Income Liability Account | Buy Down Expense Account |

##### Buy Down Fee Amortization Adjustment

A Buy Down Fee Amortization Adjustment in Apache Fineract is a special transaction type used to reverse previously recognized income from buy down fee amortization.

###### Purpose

* Automatically generated when a Buy Down Fee transaction is reversed
* Reverses all already recognized portions (amortized income) linked to the original Buy Down Fee transaction

###### When It Occurs

* **Trigger**: Only initiated during the reversal of a Buy Down Fee transaction
* Reverses all amortization that has occurred up to that point
* Restores Deferred Income balances and reverses income recognition

###### Accounting Entries

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Buy Down Fee Amortization Adjustment | Income from Buy Down Account | Deferred Income Liability Account |

###### Key Characteristics

* **System-Generated Only**: Cannot be created manually by API or UI
* **Ensures Accounting Integrity**: Keeps amortized and unrecognized balances aligned after reversals
* **Links to Original Amortization**: Maintains traceability by referencing the reversed Buy Down Fee transaction

#### API Endpoints

##### Configure Buy Down Fee on Loan Product

* **Endpoint**: `/loanproducts`
* **Method**: `POST`

```json
{
    ...
    "enableBuyDownFee": true,                    // Mandatory
    "buyDownFeeCalculationType": "FLAT",         // Mandatory when enabled
    "buyDownFeeStrategy": "EQUAL_AMORTIZATION",  // Mandatory when enabled
    "buyDownFeeIncomeType": "FEE",              // Mandatory when enabled
    "buyDownExpenseAccountId": 123,             // Mandatory when enabled
    "deferredIncomeLiabilityAccountId": 456,    // Mandatory when enabled
    "incomeFromBuyDownAccountId": 789           // Mandatory when enabled
}
```

##### Add Buy Down Fee

* **Endpoint**: `/loans/{loanId}/transactions?command=buyDownFee`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions?command=buyDownFee`
* **Method**: `POST`

```json
{
    "transactionDate": "2025-05-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en",                     // Mandatory
    "transactionAmount": 100.0,         // Mandatory
    "paymentTypeId": 1,                 // Optional
    "note": "Buy down fee",             // Optional
    "externalId": "BUYDOWN-001"         // Optional
}
```

###### Response Body

```json
{
    "resourceId": 1,
    "resourceExternalId": "BUYDOWN-001"
}
```

##### Get Buy Down Fee Amortization Info

* **Endpoint**: `/loans/{loanId}/buydown-fees`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/buydown-fees`
* **Method**: `GET`

###### Response Body

```json
[
    {
        "id": 1,
        "loanId": 123,
        "transactionId": 456,
        "buyDownFeeDate": "2025-05-01",
        "buyDownFeeAmount": 100.0,
        "amortizedAmount": 5.0,
        "notYetAmortizedAmount": 95.0,
        "adjustedAmount": 0.0,
        "chargedOffAmount": 0.0
    }
]
```

##### Add Buy Down Fee Adjustment

* **Endpoint**: `/loans/{loanId}/transactions/{buyDownFeeTransactionId}?command=buyDownFeeAdjustment`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/{buyDownFeeTransactionId}?command=buyDownFeeAdjustment`
* **Method**: `POST`

```json
{
    "transactionDate": "2025-05-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en",                     // Mandatory
    "transactionAmount": 50.0,          // Mandatory
    "paymentTypeId": 1,                 // Optional
    "note": "Buy down fee adjustment",  // Optional
    "externalId": "BUYDOWNADJ-001"      // Optional
}
```

###### Response Body

```json
{
    "resourceId": 1,
    "resourceExternalId": "BUYDOWNADJ-001"
}
```

##### Buy Down Fee Template API (to retrieve limits)

* **Endpoint**: `/loans/{loanId}/transactions/template?command=buyDownFee`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/template?command=buyDownFee`
* **Method**: `GET`

```json
{
    "paymentTypeOptions": [],  // List of available payment types
    "currency": {...},         // Currency configuration
    "date": [2025, 5, 29],     // Return the current date
    "amount": 0                // Return the maximum amount that can be applied
}
```

##### Buy Down Fee Adjustment Template API (to retrieve limits)

* **Endpoint**: `/loans/{loanId}/transactions/template?command=buyDownFeeAdjustment`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}/transactions/template?command=buyDownFeeAdjustment`
* **Method**: `GET`

```json
{
    "paymentTypeOptions": [],  // List of available payment types
    "currency": {...},         // Currency configuration
    "date": [2025, 5, 29],     // Return the current date
    "amount": 0                // Return the maximum amount that can be adjusted
}
```

#### Database Structure

##### Configuration

###### Loan Product Table (m_product_loan)

| Field | Data Type | Description |
| --- | --- | --- |
| `enable_buy_down_fee` | `BOOLEAN` | Enable buy down fee feature (default: `false`) |
| `buy_down_fee_calculation_type` | `VARCHAR` | Calculation method (ENUM: `FLAT`) |
| `buy_down_fee_strategy` | `VARCHAR` | Amortization strategy (ENUM: `EQUAL_AMORTIZATION`) |
| `buy_down_fee_income_type` | `VARCHAR` | Income type (ENUM: `FEE`, `INTEREST`) |

##### Balances

###### Buy Down Fee Balance Table (m_loan_buy_down_fee_balance)

| Field | Data Type | Description |
| --- | --- | --- |
| `id` | `BIGINT` | Primary Key (auto-increment) |
| `version` | `BIGINT` | Version for optimistic locking (NOT NULL) |
| `loan_id` | `BIGINT` | Foreign Key to `m_loan.id` (NOT NULL) |
| `loan_transaction_id` | `BIGINT` | Foreign Key to `m_loan_transaction.id` (NOT NULL) |
| `amount` | `DECIMAL(19,6)` | Buy down fee transaction amount (NOT NULL) |
| `date` | `DATE` | Buy down fee transaction date (NOT NULL) |
| `unrecognized_amount` | `DECIMAL(19,6)` | Not yet amortized amount (NOT NULL) |
| `charged_off_amount` | `DECIMAL(19,6)` | Charged-off balance (nullable) |
| `amount_adjustment` | `DECIMAL(19,6)` | Total adjustment amount (nullable) |
| `created_by` | `BIGINT` | User who created the record (NOT NULL) |
| `created_on_utc` | `DATETIME` | Creation timestamp in UTC (NOT NULL) |
| `last_modified_by` | `BIGINT` | Last modifier user ID (NOT NULL) |
| `last_modified_on_utc` | `DATETIME` | Last modification timestamp in UTC (NOT NULL) |

##### Constraints and Indexes

* **Primary Key:** `id`
* **Foreign Keys:**
  
  
  
  
  
  * `loan_id` â `m_loan(id)`
  * `loan_transaction_id` â `m_loan_transaction(id)`
  * `created_by` â `m_appuser(id)`
  * `last_modified_by` â `m_appuser(id)`

##### Related Transaction Types

Buy Down Fee operations are stored in `m_loan_transaction` table with these transaction types:

* `BUY_DOWN_FEE` - Initial buy down fee creation
* `BUY_DOWN_FEE_ADJUSTMENT` - Adjustment to existing buy down fee
* `BUY_DOWN_FEE_AMORTIZATION` - Daily amortization transaction
* `BUY_DOWN_FEE_AMORTIZATION_ADJUSTMENT` - Adjustment to amortization

#### Accounting Entries

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Buy Down Fee | Buy Down Expense Account | Deferred Income Liability Account |
| Buy Down Fee Amortization | Deferred Income Liability Account | Income from Buy Down Account |
| Buy Down Fee Adjustment | Deferred Income Liability Account | Buy Down Expense Account |
| Buy Down Fee Amortization Adjustment | Income from Buy Down Account | Deferred Income Liability Account |

#### Business Events

##### Triggered for Buy Down Fee

* `LoanBuyDownFeeTransactionCreatedBusinessEvent`
* `LoanBalanceChangedBusinessEvent`

##### Daily Amortization

* `LoanBuyDownFeeAmortizationTransactionCreatedBusinessEvent`
* `LoanBuyDownFeeAmortizationAdjustmentTransactionCreatedBusinessEvent`

##### Buy Down Fee Adjustment

* `LoanBuyDownFeeAdjustmentTransactionCreatedBusinessEvent`
* `LoanBalanceChangedBusinessEvent`

##### Reversal

* `LoanAdjustTransactionBusinessEvent`

#### Available Disbursement Calculation

Buy Down Fee does not affect the available disbursement amount calculation:

```java
Available Disbursement = Approved Loan Amount
                       - Total Disbursed Amount
                       - Total Capitalized Income
```

Buy Down Fee transactions are separate from the loan disbursement logic and do not reduce the available disbursement amount.

#### Notes

> [!IMPORTANT]
> * Buy down fee transactions support backdating
> * Adjustment transactions must not predate the original buy down fee
> * No automatic reversal is supported; must be handled manually via dedicated transactions
> * Proper GL accounts must be set for Buy Down Expense, Deferred Income Liability, and Income from Buy Down to enable this functionality

### Approved amount modification on loans

#### Overview

In Apache Fineract, after a loan is disbursed, it is possible to alter the principal amount that the loan was approved with. This means that the amount to be disbursed can be fine-tuned throughout the loan lifecycle. The approved loan amount can either be modified directly or indirectly through different endpoints.

#### Supported Loan Type

Approved amount modifications are supported on all loan types.

#### Business Events

* Triggers a new business event: Loan Approved Amount Changed

#### API Endpoints

##### Modifying approved amount on loans

Fineract supports the direct modification of the approved amount on loans

* **Endpoint**: `/loans/<loan_id>/approved-amount`
* **Alternative Endpoint**: `/loans/external-id/<loan_external_id>/approved-amount`
* **Method**: `PUT`

```json
{
    "amount": 1000.0,
    "locale": "en"
}
```

###### Response Body

```json
{
    "changes": {
        "locale": "en",
        "newApprovedAmount": 1000.0,
        "oldApprovedAmount": 1500.0
    },
    "clientId": 6,
    "groupId": 10,
    "officeId": 2,
    "resourceExternalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7",
    "resourceId": 3
}
```

###### Validations

* The approved amount of the loan cannot be lower than the `total principal disbursed + total expected principal + total principal from capitalized income transactions`.
* The approved amount of the loan cannot be set higher, than the proposed amount of the loan or if `allow approved/disbursed over applied amount` configuration is enabled then the calculated threshold.

##### Modifying available disbursement amount on loans

Fineract supports the indirect modification of the approved amount on loans. This is called modifying the available disbursement amount.

> [!IMPORTANT]
> Available disbursement amount is only a calculated value used by this endpoint to indirectly update the approved amount of the loan. It is not stored anywhere.

The approved amount is calculated as: `total principal disbursed + total expected principal + total principal from capitalized income + "amount" from the request`.

* **Endpoint**: `/loans/<loan_id>/available-disbursement-amount`
* **Alternative Endpoint**: `/loans/external-id/<loan_external_id>/available-disbursement-amount`
* **Method**: `PUT`

```json
{
    "amount": 100.0,
    "locale": "en"
}
```

###### Response Body

```json
{
    "changes": {
        "locale": "en",
        "newApprovedAmount": 100.0,
        "oldApprovedAmount": 1000.0,
        "newAvailableDisbursementAmount": 100.0,
        "oldAvailableDisbursementAmount": 1000.0
    },
    "clientId": 6,
    "groupId": 10,
    "officeId": 2,
    "resourceExternalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7",
    "resourceId": 3
}
```

###### Validations

* The available disbursement amount cannot be lower than 0.
* The approved amount of the loan cannot be set higher, than the proposed amount of the loan or if `allow approved/disbursed over applied amount` configuration is enabled then the calculated threshold. This means that the new available disbursement amount cannot be higher than `maximumLoanPrincipalThreshold - total principal disbursed - total expected principal - total principal from capitalized income`

##### Approved amount history

Modifying the approved amount of the loan through either endpoint also creates a history entry that can be used to observe the changes overtime.

* **Endpoint**: `/loans/<loan_id>/approved-amount`
* **Alternative Endpoint**: `/loans/external-id/<loan_external_id>/approved-amount`
* **Method**: `GET`

###### Response Body

```json
[
  {
    "loanId": 152,
    "externalLoanId": "9e058913-3de8-4f6e-9e09-4b2067c4bb91",
    "newApprovedAmount": 800.000000,
    "oldApprovedAmount": 1000.000000,
    "dateOfChange": "2025-08-05T16:35:43.427229+02:00"
  },
  {
    "loanId": 152,
    "externalLoanId": "9e058913-3de8-4f6e-9e09-4b2067c4bb91",
    "newApprovedAmount": 600.000000,
    "oldApprovedAmount": 800.000000,
    "dateOfChange": "2025-08-05T16:35:43.543779+02:00"
  },
  {
    "loanId": 152,
    "externalLoanId": "9e058913-3de8-4f6e-9e09-4b2067c4bb91",
    "newApprovedAmount": 400.000000,
    "oldApprovedAmount": 600.000000,
    "dateOfChange": "2025-08-05T16:35:43.603855+02:00"
  }
]
```

### Backdated interest modification

In the previous implementation we were only allowing the interest rate modification from current date and from now on we will allow Interest modification backdated on progressive loans as well.

> [!IMPORTANT]
> Only available on progressive loans.

#### Functionality

Validations updated to allow backdated interest change, even on charged-off or otherwise closed loan. Making progressive loans more flexible.

1. Interest rate can be modified from backdate any date from first disbursement date
2. Interest will be affected from the applied date itself.
3. Backdate can be done on already paid Installments as well
4. Repayment schedule will be recalculated with New EMI and Interest from the Interest applied schedule date
  
  
  
  
  
  * Backdated PAID Installments and Unpaid/Partial Paid Installment EMI would be changed as per the new calculated EMI
5. Installments paid Interest amount will be reverse replayed as per the new Interest rate from the applied date
  
  
  
  
  
  * Transactions will be reversed replayed if there is any change is allocations
  * Accrual adjustments will be done during reverse replay (during the COB process)
6. No of Installments will remain the same, only EMI and Interest would get affected
7. Backdated Interest modification allowed on the loan that is charged off
  
  
  
  
  
  * If the repayment that was made before the charge-off is reversed and replayed due to backdated Interest modification,then the accounting entry of the reversed transaction and replayed transaction should follow standard accounting rules and not charge-off accounting rules
8. Backdated interest modification allowed on the loan that is overpaid, and CBR is complete.
  
  
  
  
  
  * Any action that triggers the recalculation (ex: reversal of backdated transaction) on the CBR loan will result in treating CBR as a credit transaction during reverse-replay. Same logic to be applied if the backdated interest modification is allowed on CBR loan accounts.
9. Asset transfer (externalization)
  
  
  
  
  
  * If the repayment that was made before the asset owner change got reversed and replayed due to backdated Interest modification,
    then, the accounting entry for the reversed transaction and replayed transaction include the tag of the current asset owner
10. Since backdated Interest modification is allowed on CBR/overpaid loans, we can keep the modification open on closed loans as well
  
  
  
  
  
  * system will do the chronological reverse-replay when the backdated Interest is changed on closed loans, schedule and transaction will be allocated accordingly

#### API endpoints

##### Create reschedule loans request (create reschedule)

* **Endpoint**: `/rescheduleloans`
* **Method**: `POST`

```json
{
    "loanId": 1,                        // Mandatory
    "newInterestRate": 1,               // Mandatory for interest rate change type reschedule
    "rescheduleFromDate": "2024-01-01", // Mandatory
    "rescheduleReasonId": 54,           // Mandatory
    "submittedOnDate": "2024-01-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en"                      // Mandatory
}
```

```json
{
    "resourceId": 1,
    "loanId": 1,
    "clientId": 1,
    "officeId": 1
}
```

##### Update reschedule loans request (approve reschedule)

* **Endpoint**: `/rescheduleloans/<reschedule_Id>`
* **Method**: `POST`

```json
{
    "approvedOnDate": "2024-01-01",     // Mandatory for approval
    "submittedOnDate": "2024-01-01",    // Mandatory
    "dateFormat": "yyyy-MM-dd",         // Mandatory
    "locale": "en"                      // Mandatory
}
```

```json
{
  "changes": {
    "approvedByUserId": 1,
    "approvedOnDate": "2024-01-01",
    "dateFormat": "yyyy-MM-dd",
    "locale": "en"
  },
  "clientId": 186,
  "loanId": 188,
  "officeId": 1,
  "resourceId": 35
}
```

### Interest Rate Modification For Progressive Loan

#### Overview

The Original Interest Rate Modification feature allows updating the interest rate for **active loans**. The updated interest rate can be applied only for active loans and effective date should be in the future.

This capability is introduced to support flexible interest rate management in loan lifecycles, reflecting changes due to inflation, risk reassessment, or customer-specific conditions.

New Progressive Loan Interest Change Modification feature can be applied for overpaid, charged off or even backdated cases, which makes it much more usable.

#### Scope and Limitations

* Only supported for **progressive** loan types.
* Loans must be **disbursed**
* Interest rate modifications apply from a specified **applied date**, which can be backdated from the **original disbursement date** onward.
* **Paid EMIs (Equal Monthly Installments) and interest amounts may be affected** by backdated interest rate changes.
* The modified interest rate affects **EMI amounts**
* Installment counts are not affected
* **Reversals/backdated repayments** are allowed after modification.

#### Feature Behavior

* When a new interest rate is applied, the system recalculates EMI values starting from the **applied date**.
* If the applied date is in the past, previously paid installments will be reprocessed under the new interest rate.
* The updated interest rate is effective **from the applied date itself**.
* Repayment schedule is updated using the current recalculation strategy.

#### Configuration

Interest calculation and interest recalculation strategies are **inherited from the loan product** configuration at the time of loan application.

This means:

* The interest calculation method (e.g., declining balance, flat) and
* The interest recalculation strategy

are **fixed per loan account** once the loan is created.

As a result, **no further changes** to these configurations are possible after loan creation. Any interest rate modifications must operate within the originally defined calculation and recalculation strategies.

#### API Specification

##### Endpoint

`POST DomainName/api/v1/rescheduleloans`

###### related API-s

Retrieve a Loan Reschedule Request

`GET DomainName/api/v1/rescheduleloans/{requestId}`

Retrieve a Preview of The New Loan Repayment Schedule

`GET DomainName/api/v1/rescheduleloans/{requestId}?command=previewLoanReschedule`

Reject a Loan Reschedule Request

`POST DomainName/api/v1/rescheduleloans/{requestId}?command=reject`

Approve a Loan Reschedule Request

`POST DomainName/api/v1/rescheduleloans/{requestId}?command=approve`

##### Request Payload

The following fields are accepted in the request body for interest rate modification. All date fields must follow the format specified by the `dateFormat` field, and parsing is performed using the specified `locale`.

| Field | Type | Description |
| --- | --- | --- |
| `loanId` | Long | Identifier of the loan to be modified. Must refer to a disbursed progressive loan. |
| `newInterestRate` | BigDecimal | Required. The new interest rate to be applied. Must be zero or positive, and comply with the loan productâs min/max rate constraints. |
| `dateFormat` | String | Required when any date fields are provided. Defines the expected format of date values (e.g., `yyyy-MM-dd`, `dd-MM-yyyy`, etc.). |
| `locale` | String | Required. Specifies the locale (e.g., `en`, `fr`, `in`) used for parsing numbers and dates. |
| `submittedOnDate` | String | Optional. The date the request is submitted. If provided, must match the specified `dateFormat`. |
| `rescheduleFromDate` | String | Required. The date from which the new interest rate becomes effective. Must be on or after the loan disbursement date. Format must match `dateFormat`. |
| `rescheduleReasonComment` | String | Optional. A free-text comment describing the reason for the interest rate change. |
| `rescheduleReasonId` | Long | Optional. ID referencing a predefined rescheduling reason (e.g., from a dropdown or lookup table). |

> [!NOTE]
> The following fields are **not applicable** in the context of an interest rate change request:
> * `adjustedDueDate`
> * `extraTerms`
> * `graceOnPrincipal`
> * `graceOnInterest`
> These parameters are reserved for other loan rescheduling operations.

###### newInterestRate

When processing an interest rate modification request, the system validates the `newInterestRate` parameter as follows:

* The value must be a valid `BigDecimal` parsed with the appropriate locale.
* The interest rate must be **zero or positive**.
* If defined on the loan product, the new interest rate must satisfy the following boundaries:
  
  
  
  
  
  * It must be **greater than or equal to** the product-level `minNominalInterestRatePerPeriod`.
  * It must be **less than or equal to** the product-level `maxNominalInterestRatePerPeriod`.

These boundaries are enforced using the product’s configured range at the time the loan was applied. If no minimum or maximum is set on the product, only the zero-or-positive constraint is enforced.

##### Example

###### Example Create Request

`POST DomainName/api/v1/rescheduleloans`

```java
POST rescheduleloans
Content-Type: application/json
```

```JSON
{
"loanId": 1,
"graceOnPrincipal": null,
"graceOnInterest": null,
"extraTerms": null,
"rescheduleFromDate": "04 December 2014",
"dateFormat": "dd MMMM yyyy",
"locale": "en",
"recalculateInterest": null,
"submittedOnDate": "04 September 2014",
"newInterestRate" : 28,
"rescheduleReasonId": 1
}
```

Response

```JSON
{
    "loanId": 1,
    "resourceId": 2
}
```

###### Example Approval

`POST DomainName/api/v1/rescheduleloans/{requestId}?command=approve`

```java
POST rescheduleloans/2?command=approve
Content-Type: application/json
```

```JSON
{
"locale": "en",
"dateFormat": "dd MMMM yyyy",
"approvedOnDate": "11 September 2014"
}
```

```JSON
{
"loanId": 1,
"resourceId": 2,
"changes": {
"locale": "en",
"dateFormat": "dd MMMM yyyy",
"approvedOnDate": "11 September 2014",
"approvedByUserId": 3
}
}
```

#### Developer Notes

The core concept is that the `AdvancedPaymentScheduleTransactionProcessor` processes transactions in order of their effective date, allowing it to handle backdated transaction cases.

The transaction processor uses the `EMICalculator` to manage interest rate changes over time, ensuring that changes only affect future transactions relative to the actual processing transaction. The `ProgressiveLoanInterestScheduleModel` is responsible for holding and calculating interest for future installments.

The underlying principle is to split repayment periods into smaller interest periods, enabling the calculation of interest for partial repayment periods. This approach makes it easier to adjust interest rates for specific interest periods as needed.

### Contract Termination

#### Overview

Contract Termination in Apache Fineract is a loan management feature that allows financial institutions to terminate loan contracts. When applied to loans with unpaid installments, this functionality accelerates the maturity date and makes the outstanding loan balance immediately due as of the termination date.

#### Purpose

This functionality enables financial institutions to:

* Terminate loan contracts when required by business rules
* Accelerate payment schedules by making outstanding balances immediately due
* Maintain proper loan status tracking and accounting
* Support charge-off and recovery operations on terminated loans

#### Supported Loan Type

> [!IMPORTANT]
> Contract Termination is only supported for:
> * Progressive Loan Schedules
> * Active loan accounts
> Other loan schedule types and inactive loan states are not supported.

#### Business Rules

##### Eligibility Requirements

Contract termination can only be applied when:

* **Loan Status**: The loan must be in `Active` status
* **Schedule Type**: Only `Progressive` loan schedule type is supported
* **Not Charged Off**: Loan must not be in charged-off state
* **Not Already Terminated**: Loan must not already have contract termination applied

##### Termination Date Rules

* Contract termination can only be done as of the current business date
* Backdated termination is not allowed
* No future-dated termination permitted

##### Schedule Impact

When contract termination is applied:

* **Maturity Acceleration**: If unpaid installments exist, the loan maturity date is accelerated to the termination date
* **Interest Calculation**: Interest is calculated only until the contract termination date
* **Maturity Date Updated**: The loan maturity date is updated to the contract termination date
* **Principal Outstanding**: The full outstanding principal balance becomes due
* **Delinquency Bucketing**: Continues as per the new accelerated schedule

##### Post-Termination Operations

After contract termination:

* **Charge-off Allowed**: Terminated loans can be charged off
* **Charge-backs Allowed**: Terminated loans support charge-back transactions
* **Future Installments**: All installments scheduled after termination date are removed from the schedule
* **Accrual Activities**: Accrual and accrual activity transactions stop after termination
* **Backdated Payments**: Backdated payments and reversals are allowed
* **Contract Termination Reversal**: The termination can be undone/reversed

##### Special Handling

###### Post-Maturity Termination

If contract termination is done after the original maturity date:

* No schedule acceleration occurs (installments and maturity date remain unchanged)
* Interest calculation follows normal rules up to the original maturity date
* The loan remains in its current state without forced acceleration

###### Contract Termination Reversal

* Contract termination can be undone/reversed
* Schedule will be recalculated and reapplied accordingly
* All associated transactions are properly reversed and replayed

#### Transaction Types

##### Contract Termination Transaction

The Contract Termination transaction in Apache Fineract performs the following actions:

* **Accelerates Payment Schedule**: Makes all outstanding amounts immediately due
* **Creates Distinct Transaction**: Tracked separately with transaction type "Contract Termination"
* **Updates Loan Sub-Status**: Changes loan sub-status to `CONTRACT_TERMINATION` (value: 900)
* **Triggers Schedule Recalculation**: Updates repayment schedule with accelerated terms
* **No Accounting Entries**: Contract termination itself does not generate accounting entries
* **Stops Accrual Activity**: Interest accrual and accrual activities cease after termination

###### Transaction Behavior

* Transaction date is set to current business date
* Amount represents total outstanding balance as calculated by loan summary
* Triggers loan reprocessing for interest-bearing loans with recalculation enabled
* Non-monetary transaction (excluded from monetary transaction queries)

###### Accrual Transactions

During contract termination, the system may generate:

* Final accrual transaction up to termination date
* Accrual adjustment transaction if needed
* Associated journal entries
* Relevant business events for accrual processing

##### Contract Termination Undo

The Contract Termination Undo transaction reverses a previous contract termination:

* **Reverses Termination Transaction**: Marks the original termination as reversed
* **Removes Sub-Status**: Restores loan to previous sub-status state
* **Recalculates Schedule**: Regenerates original repayment schedule
* **Reprocesses Transactions**: Re-runs transaction processing logic
* **Triggers Business Events**: Notifies system of balance and status changes

#### API Endpoints

##### Apply Contract Termination

* **Endpoint**: `/loans/{loanId}?command=contractTermination`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}?command=contractTermination`
* **Method**: `POST`

```json
{
    "note": "Contract terminated due to default",            // Optional
    "externalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7"     // Optional
}
```

###### Response Body

```json
{
    "entityId": 1,
    "entityExternalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7",
    "officeId": 1,
    "clientId": 1,
    "loanId": 1,
    "changes": {
        "subStatus": 900
    }
}
```

##### Undo Contract Termination

* **Endpoint**: `/loans/{loanId}?command=undoContractTermination`
* **Alternative Endpoint**: `/loans/external-id/{loanExternalId}?command=undoContractTermination`
* **Method**: `POST`

```json
{
    "note": "Reversing contract termination",                       // Optional
    "reversalExternalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7"    // Optional
}
```

###### Response Body

```json
{
    "entityId": 1,
    "entityExternalId": "95174ff9-1a75-4d72-a413-6f9b1cb988b7",
    "officeId": 1,
    "clientId": 1,
    "groupId": null,
    "loanId": 1,
    "changes": {
        "subStatus": null
    }
}
```

#### Business Events

##### Triggered for Contract Termination

* `LoanTransactionContractTerminationPostBusinessEvent` - After termination processing
* `LoanBalanceChangedBusinessEvent` - After termination processing
* `LoanAdjustTransactionBusinessEvent` - During termination transaction processing

##### Triggered for Contract Termination Undo

* `LoanUndoContractTerminationBusinessEvent` - Before and after undo operation
* `LoanBalanceChangedBusinessEvent` - After schedule recalculation
* `LoanAdjustTransactionBusinessEvent` - During reversal processing

#### Database Impact

##### Loan Sub-Status

###### Updated on Loan (m_loan)

| Field | Data Type | Description |
| --- | --- | --- |
| `sub_status_enum` | `SMALLINT` | Set to 900 (CONTRACT_TERMINATION) when terminated, reset to NULL when undone |

##### Transaction Records

###### Loan Transaction (m_loan_transaction)

| Field | Data Type | Description |
| --- | --- | --- |
| `transaction_type_enum` | `SMALLINT` | Set to 38 (CONTRACT_TERMINATION) |
| `transaction_date` | `DATE` | Current business date |
| `amount` | `DECIMAL(19,6)` | Total outstanding balance |
| `is_reversed` | `BOOLEAN` | Set to TRUE when undone |

#### Validation Rules

##### Contract Termination Validation

* Loan must be in active status (`loan.isOpen()`)
* Loan product must use Progressive schedule type
* Loan must not be charged off (`!loan.isChargedOff()`)
* Loan must not already be terminated (`!loan.isContractTermination()`)
* Client or group must be active

##### Contract Termination Undo Validation

* Original contract termination transaction must exist
* Transaction must not be already reversed
* Proper permissions required for reversal operations

#### Integration Points

##### Charge Operations

* Charge-off operations can be performed on terminated loans
* Charge-back transactions are supported on terminated loans
* Charge adjustments follow normal business rules

##### Delinquency Management

* Delinquency bucketing continues based on accelerated schedule
* Delinquency calculations use the new due dates from termination

##### Accounting Integration

* No direct accounting entries for contract termination transaction
* Potential accrual transactions generated up to termination date
* Journal entries created for final accrual transactions
* Interest accrual stops after termination
* Business events triggered for accrual processing

#### Notes

> [!IMPORTANT]
> * Contract termination is irreversible through normal business processes once additional transactions occur
> * Proper authorization and audit trails are maintained for all termination activities
> * Integration with external systems should account for accelerated payment schedules
> * Only Progressive loan schedule type supports this functionality due to schedule recalculation requirements

### Loan Charges

#### Overview

Loan charge products can be created with different charge time types and charge calculation types. The created charge product can be associated with loan products or individual loan accounts to automate fee and penalty application throughout the loan lifecycle.

##### Benefits

* Automates charge application at disbursement, specified dates, or installment schedules
* Supports multiple calculation methods including flat amounts and various percentage-based calculations
* Handles multi-disbursement loans with distinct first disbursement vs. tranche disbursement behavior
* Provides penalty automation for overdue installments
* Enables flexible fee structures for different loan products

#### Charge Time Types and Calculation Types

The following charge time types and corresponding calculation types are supported for loans:

| Charge Time Type | Description | Available Charge Calculation Types |
| --- | --- | --- |
| Disbursement | Charged at the time of first disbursement. For multi-disbursement loans, it applies only to the first disbursement. | * **Flat**: Fixed amount defined at charge creation * **% amount**: Percentage charged on approved loan amount * **% interest**: Percentage charged on total interest amount as per first disbursement * **% loan amount + interest**: Percentage charged on the disbursed amount plus total interest as per first disbursement * **% disbursement amount**: Percentage charged on actual disbursement amount |
| Specified Due Date | Charge applied on a specific date defined by the user within the loan lifecycle. | * **Flat**: Fixed amount defined at charge creation * **% amount**: Percentage charged on approved loan amount * **% interest**: Percentage charged on total interest amount as per first disbursement * **% loan amount + interest**: Percentage charged on the disbursed amount plus total interest as per first disbursement |
| Installment Fees | Charged with each repayment installment throughout the loan term. | * **Flat**: Fixed amount per installment * **% amount**: Percentage of approved amount divided across installments * **% loan amount + interest**: Percentage of principal plus interest for each installment |
| Overdue Fees | Penalties automatically applied when installments become overdue. | * **Flat**: Fixed penalty amount per overdue installment * **% amount**: Percentage penalty based on overdue amount |
| Tranche Disbursement | Charged for each disbursement tranche in multi-disbursement loans. | * **Flat**: Fixed amount per disbursement tranche * **% disbursement amount**: Percentage charged on each disbursement tranche amount |

#### API Endpoints

##### Charge Product Management

* **Endpoint**: `/v1/charges`
* **Methods**: `GET` (list all charges), `POST` (create charge)
* **Purpose**: Manage charge product definitions
* **Endpoint**: `/v1/charges/{chargeId}`
* **Methods**: `GET` (retrieve), `PUT` (update), `DELETE` (delete)
* **Purpose**: Individual charge product operations
* **Endpoint**: `/v1/charges/template`
* **Methods**: `GET`
* **Purpose**: Retrieve charge creation template with dropdown options

##### Loan Charge Management

* **Endpoint**: `/v1/loans/{loanId}/charges`
* **Alternative**: `/v1/loans/external-id/{loanExternalId}/charges`
* **Methods**: `GET` (list loan charges), `POST` (add charge to loan)
* **Purpose**: Manage charges on specific loans
* **Endpoint**: `/v1/loans/{loanId}/charges/{chargeId}`
* **Alternative**: `/v1/loans/external-id/{loanExternalId}/charges/external-id/{chargeExternalId}`
* **Methods**: `GET` (retrieve), `PUT` (update), `DELETE` (remove), `POST` (execute commands)
* **Purpose**: Individual loan charge operations
* **Endpoint**: `/v1/loans/{loanId}/charges/template`
* **Methods**: `GET`
* **Purpose**: Get template for adding charges to loans

##### Charge Commands

Loan charges support command-based operations via `POST` requests with `command` query parameter:

* `POST /v1/loans/{loanId}/charges/{chargeId}?command=waive` - Waive charge
* `POST /v1/loans/{loanId}/charges/{chargeId}?command=pay` - Pay charge directly

#### Configuration

##### Charge Product Setup

1. **Charge Time Type**: Select when the charge should be applied (disbursement, specified date, installments, overdue, or tranche)
2. **Charge Calculation Type**: Choose calculation method (flat amount or percentage-based)
3. **Amount/Percentage**: Define the charge amount or percentage value
4. **Currency**: Must match the loan product currency
5. **Penalty Flag**: Mark charges as penalties for reporting purposes
6. **Active Status**: Enable/disable charge availability

##### Loan Product Association

* Associate default charges to loan products during product configuration
* Default charges are automatically applied when loans are created from the product
* Individual charges can be added to specific loans regardless of product defaults

##### Validation Rules

* Charge currency must match loan currency
* Specified due dates must fall within the loan term
* Percentage values must be within valid ranges (0-100)
* Overdue charges require penalty flag to be enabled
* Disbursement charges can only be added before loan disbursement

### Loan Product Templates

Apache Fineract provides a loan-product API that can be used to create reusable product configurations.
The JSON files in `examples/loan-products` are directly importable baseline templates for common loan products.
They contain the required create-loan-product fields and explicit operational defaults that match the standard Fineract loan-product configuration.
They can be copied, reviewed for a tenant, and submitted to the create-loan-product endpoint.
After a product is created, it can also be modified in a Mifos user interface connected to the same Fineract tenant.

#### Available templates

| Template | Purpose | Key repayment configuration |
| --- | --- | --- |
| [`flat-interest-monthly.json`](https://fineract.apache.org/docs/examples/loan-products/flat-interest-monthly.json) | Monthly microloan-style starting point | Flat interest and equal installments |
| [`declining-balance-monthly.json`](https://fineract.apache.org/docs/examples/loan-products/declining-balance-monthly.json) | General-purpose monthly loan | Declining-balance interest and equal installments |
| [`weekly-small-business.json`](https://fineract.apache.org/docs/examples/loan-products/weekly-small-business.json) | Short-term business loan | Weekly declining-balance installments |
| [`interest-free-installments.json`](https://fineract.apache.org/docs/examples/loan-products/interest-free-installments.json) | Zero-interest lending program | Monthly installments with a zero interest rate |
| [`equal-principal-monthly.json`](https://fineract.apache.org/docs/examples/loan-products/equal-principal-monthly.json) | Loan where principal payments remain constant | Monthly declining-balance interest and equal principal payments |

#### Import a template

The templates are request bodies for `POST /fineract-provider/api/v1/loanproducts`.
They are API request templates, not database imports, and do not require tenant-specific database changes.
For example, the following command imports the flat-interest monthly template into a locally running Fineract instance:

```bash
curl --fail-with-body \
    --request POST \
    --url 'https://localhost:8443/fineract-provider/api/v1/loanproducts' \
    --header 'Authorization: Basic BASE64_ENCODED_USERNAME_AND_PASSWORD' \
    --header 'Fineract-Platform-TenantId: default' \
    --header 'Content-Type: application/json' \
    --data-binary '@fineract-doc/src/docs/en/examples/loan-products/flat-interest-monthly.json'
```

Replace the authorization value, tenant identifier, and server URL before running the command.
Each template uses a unique four-character `shortName`, but `name` and `shortName` must also be unique among the products that already exist in the target tenant.

#### Review a template before production use

The files are valid baseline API payloads, but no shared template can be production-approved for every financial institution.
The examples intentionally use `USD`, no-accounting mode (`accountingRule` value `1`), disabled optional features, and the standard transaction-processing strategy so that they do not depend on tenant-specific ledger-account identifiers.
Review at least the following fields and enable any institution-specific controls before using an imported product in production:

* `name`, `shortName`, and `description`
* `currencyCode`, `digitsAfterDecimal`, and `inMultiplesOf`
* `principal`, `minPrincipal`, and `maxPrincipal`
* `numberOfRepayments`, `repaymentEvery`, and `repaymentFrequencyType`
* `interestRatePerPeriod`, `interestRateFrequencyType`, `interestType`, and `amortizationType`
* `accountingRule` and any ledger-account mappings required when accounting is enabled
* arrears, non-performing asset, recalculation, down-payment, and optional feature settings

Use `GET /fineract-provider/api/v1/loanproducts/template` to retrieve the options available in the target tenant before adding tenant-dependent settings such as funds, charges, accounting mappings, or alternative transaction-processing strategies.

### Journal Entry Aggregation

#### Overview

The Journal Entry Aggregation Job is a Spring Batch-based solution designed to efficiently aggregate journal entries in the Fineract system. This job processes journal entries in configurable chunks, improving performance and resource utilization when dealing with large volumes of financial transactions.

#### Key Features

##### Chunk-based Processing

* Processes journal entries in configurable batch sizes
* Reduces memory footprint by working with manageable data subsets
* Improves performance through efficient batch processing

##### Tracking and Deduplication

* Tracks processed date ranges to prevent duplicate aggregations
* Uses `JournalEntryAggregationTracking` to maintain execution history
* Skips already processed date ranges in subsequent runs

##### Configurable Exclude Recent N Days

* Excludes the last N days (from business date) from processing
* Default `Exclude Recent N Days` can be customized via application properties

#### How It Works

##### Job Flow

###### Job Initialization

* Determines the date range to process based on last execution
* Sets up execution context with date boundaries

###### Data Reading

* Fetches unaggregated journal entries within the target date range
* Groups entries by GL account, product, office, and other dimensions

###### Processing

* Aggregates debit and credit amounts for each group
* Handles external asset owner mappings
* Processes data in configurable chunk sizes

###### Tracking

* Records successful aggregation runs
* Maintains execution history for future reference

#### Configuration

##### Job Parameters

* `aggregatedOnDate`: (Optional) Specific date to process (defaults to business date)
* `chunkSize`: (Optional) Number of records to process in each chunk

##### Application Properties

```properties
# Exclude Recent N days from aggregation
fineract.job.journal-entry-aggregation.exclude-recent-N-days=1

# Chunk size for batch processing
fineract.job.journal-entry-aggregation.chunk-size=1000
```

#### Usage

##### Manual Execution

Trigger the job manually through the Fineract API:

```http
POST /jobs/short-name/JRNL_AGG
Content-Type: application/json

{
}
```

##### Scheduled Execution

Configure the job to run on a schedule by adding to your scheduler configuration.

##### Monitoring

Monitor job execution through:

* Job execution logs
* `JOURNAL_ENTRY_AGGREGATION_TRACKING` table
* Spring Batch job execution tables

#### Best Practices

##### Chunk Size Tuning

* Larger chunks improve throughput but increase memory usage
* Monitor memory usage and adjust chunk size accordingly

##### Scheduling

* Schedule during off-peak hours for large datasets
* Consider running more frequently with smaller `Exclude Recent N Days` values

##### Error Handling

* Failed jobs can be restarted from the last successful chunk
* Review job execution logs for any processing issues

#### Performance Considerations

* **Indexing**: Ensure proper indexes exist on `aggregated_on_date`, `office_id`, and other filtering columns
* **Partitioning**: Consider partitioning large journal entry tables by date for better performance
* **Batch Window**: Allocate sufficient time for the job to complete during maintenance windows

#### Database Schema

##### m_journal_entry_aggregation_summary Table

This table stores the aggregated journal entry amounts, grouped by various dimensions for efficient reporting and analysis.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| id | BIGINT | No | Primary key |
| gl_account_id | BIGINT | No | Reference to `acc_gl_account` |
| product_id | BIGINT | Yes | Reference to the product (if applicable) |
| office_id | BIGINT | No | Reference to `m_office` |
| entity_type_enum | SMALLINT | No | Type of entity (e.g., loan, savings) |
| submitted_on_date | DATE | No | The date of the business date when entry was submitted |
| aggregated_on_date | DATE | No | The date when aggregation was performed |
| debit_amount | DECIMAL(19,6) | No | Sum of debit amounts |
| credit_amount | DECIMAL(19,6) | No | Sum of credit amounts |
| external_owner_id | BIGINT | Yes | Reference to external owner (if applicable) |
| job_execution_id | BIGINT | No | Reference to batch job execution |
| created_date | TIMESTAMP | No | Record creation timestamp |
| last_modified_date | TIMESTAMP | Yes | Last modification timestamp |

The table is designed to support efficient querying of aggregated financial data by:
* Date ranges (using `submitted_on_date` and `aggregated_on_date`)
* Organizational structure (using `office_id`)
* Financial dimensions (using `gl_account_id` and `product_id`)
* Entity types (using `entity_type_enum`)

##### m_journal_entry_aggregation_tracking Table

This table maintains a history of aggregation job executions, tracking which date ranges have been processed to prevent duplicate aggregations.

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| id | BIGINT | No | Primary key |
| job_execution_id | BIGINT | No | Reference to Spring Batch job execution |
| aggregated_on_date_from | DATE | No | Start date of the aggregation period |
| aggregated_on_date_to | DATE | No | End date of the aggregation period |
| submitted_on_date | DATE | No | The date of the business date when entry was submitted |
| status | VARCHAR(20) | No | Status of the aggregation (e.g., COMPLETED, FAILED) |
| error_message | TEXT | Yes | Error details if the job failed |
| start_time | TIMESTAMP | No | When the aggregation started |
| end_time | TIMESTAMP | Yes | When the aggregation completed |
| records_processed | INT | Yes | Number of records processed |
| created_date | TIMESTAMP | No | Record creation timestamp |
| last_modified_date | TIMESTAMP | Yes | Last modification timestamp |

Key aspects of the tracking table:
* Tracks the exact date ranges processed in each job execution
* Maintains job status and error information for debugging
* Records performance metrics (processing time, record counts)
* Used by the job to determine which date ranges need processing in subsequent runs

Indexes are created on frequently queried columns to ensure optimal performance for reporting and analysis.

This aggregation job provides a robust, scalable solution for processing journal entries while maintaining data integrity and providing clear audit trails of all aggregation activities.

### Asset Externalization

---

#### 1. Purpose & Scope

The Asset Externalization capability enables **loan ownership transfer** between a **Platform Owner** and external investors within **Fineract**, supporting:

* Loan sales and securitization for GPL products
* Real-time ownership awareness with **COB-based execution**
* Full accounting, reporting, and auditing for **Platform Ownerâowned and investor-owned loans**
* API-driven ownership lifecycle management
* Event-driven downstream integration (ETL, Credit domains)

Ownership is **exclusive**: once sold, the loan is **100% investor-owned** until buyback.

---

#### 2. In-Scope vs Out-of-Scope

##### In Scope (Fineract Responsibilities)

* Persist and manage **loan ownership throughout loan lifecycle**
* Accept ownership transfer requests (sale, buyback, cancel)
* Execute ownership changes **at Close of Business (COB)**
* Generate **accounting journal entries** per ownership
* Publish **ownership change events**
* Provide **GET/POST APIs** for ownership and transfers
* Support delayed settlement (pending â active)
* Produce investor accounting reports

##### Out of Scope

* General high-level mechanism for determining which loans/clients are eligible for sale or buyback (loan state requirements are scope and implemented)
* Smart Order Router which could prioritize internal logic or market logic
* Credit ETL (Extract, Transform, Load) schema decisions outside Fineract

---

#### 3. Ownership Model

##### Ownership Characteristics

* Single owner at any time (**Platform Owner** or Investor)
* Ownership stored with:
* Asset Owner ID
* Transfer (Sale / Buyback) ID
* Purchase Price Ratio
* Effective date range
* Status
* Ownership updates requested in real time, **executed during COB**

##### Ownership Statuses

| Status | Description |
| --- | --- |
| PENDING | Transfer requested, not yet executed |
| ACTIVE | Investor owns the loan |
| BUYBACK | Ownership reverted to Platform Owner |
| DECLINED | Transfer invalid due to balance/state |
| CANCELLED | Transfer cancelled before execution |

---

#### 4. Functional Flows

##### 4.1 Asset Sale (Ownership Transfer to Investor)

**Preconditions**

* Loan must be **ACTIVE**
* No active ownership
* Balance at COB **> 0.00**

**Process**

1. Sale request submitted via API
2. Ownership record created with status **PENDING**
3. At COB on settlement date:
  
  
  
  
  
  * If balance > 0.00 â status becomes **ACTIVE**
  * If balance â¤ 0.00 â status becomes **DECLINED**
4. Journal entries posted using **closing balance**
5. Ownership effective from next day

**Persisted Data**

* Asset Owner ID
* Sale Transaction ID
* Purchase Price Ratio
* Settlement date
* Effective date range
* Timestamps

---

##### 4.2 Buyback (Ownership Transfer to Platform Owner)

**Preconditions**

* Active ownership exists
* Loan must be **ACTIVE**
* Can be triggered for fraud, reversals, or business decision

**Process**

1. Buyback request submitted
2. Buyback transfer record created
3. At COB:
  
  
  
  
  
  * Ownership marked **INACTIVE**
  * Journal entries posted using closing balance
4. Ownership reverts to Platform Owner

**No buyback occurs if**

* Loan is CLOSED
* No active ownership
* Loan not found

---

##### 4.3 Delayed Settlement (Phase 2)

* Sale request can include **future settlement date**
* Ownership remains **PENDING** until settlement
* Pending accounting entries applied
* At settlement COB:
* Pending â ACTIVE if balance > 0
* Pending â DECLINED if balance â¤ 0

---

#### 5. Accounting Behavior

##### General Rules

* All accounting logic remains unchanged **except owner tagging**
* Fees, payments, delinquency, charge-off rules remain unchanged
* Fees after sale belong to **investor**
* No ownership transfer or GL entries if balance â¤ 0

---

##### 5.1 Sale & Buyback Journal Entries (COB)

**Sale**

* DR Loan/Fee Receivable â Investor
* CR Loan/Fee Receivable â Platform Owner

**Buyback**

* DR Loan/Fee Receivable â Platform Owner
* CR Loan/Fee Receivable â Investor

---

##### 5.2 Investor-Owned Loan Transactions

For investor-owned loans, journal entries are posted **against investor GLs** for:

* Disbursement
* Repayments (all payment types)
* Refunds
* Goodwill credits
* Snooze & NSF fees
* Fee waivers
* Credit balance refunds
* Repayment adjustments & reversals
* Charge-offs (non-payment, deceased, bankrupt)
* Recoveries (repayments, refunds)

---

#### 6. Events

##### Ownership Change Events

Events are published **in real time** when ownership changes occur.

**Published For**

* Sale
* Buyback
* Declined transfers

**Event Payload**

* Date/time
* Loan account ID
* Sale/Buyback Transaction ID
* Asset Owner ID
* Loan balance

**Consumption**

* Fineract SOR â Adaptor â Credit ETL
* Persisted in Credit databases

---

#### 7. APIs

##### Transfer Requests

Ownership transfer requests are supported for **sale**, **buyback**, and **cancel**, targeting loans by internal or external identifiers.

**Root endpoint**

* `/external-asset-owners`

**Sale / Buyback / Cancel**

* `POST /external-asset-owners/transfers?loanId=<loan_id>&command=<sale|buyback|cancel>`
* `POST /external-asset-owners/transfers?loanExternalId=<loan_external_id>&command=<sale|buyback|cancel>`
* `POST /external-asset-owners/transfers/loans/<loan_id>?command=<action>`
* `POST /external-asset-owners/transfers/loans/external-id/<loan_external_id>?command=<action>`

---

##### Retrieve Ownership

Ownership and transfer information can be retrieved using:

* `GET /external-asset-owners/transfers?transferExternalId=<transfer_external_id>`
* `GET /external-asset-owners/transfers?loanId=<loan_id>`
* `GET /external-asset-owners/transfers?loanExternalId=<loan_external_id>`

---

##### Retrieve Accounting Data

Accounting data related to ownership is available through:

* Transfer journal entries
* `GET /external-asset-owners/transfers/external-id/{ownerExternalId}/journal-entries`
* Owner journal entries
* `GET /external-asset-owners/owners/external-id/{ownerExternalId}/journal-entries`

---

#### 8. Data Model (Summary)

##### Core Tables

* `m_external_asset_owner`
* `m_external_asset_owner_transfer`
* `m_external_asset_owner_active_transfer_loan_mapping`
* `m_external_asset_owner_journal_entry_mapping`
* `m_external_asset_transfer_journal_entry_mapping`
* `m_external_asset_owner_transfer_details`

Supports:

* Ownership history
* Effective dating
* Auditing
* Investor-level accounting reconciliation

---

#### 9. Reporting

##### Daily Investor Reports

* GL Trial Balance Summary (by investor)
* Transaction Detail Report (by investor)

Used for reconciliation of:

* Investor cash
* GL balances
* Ownership-related postings

---

#### 10. Validation Rules (Consolidated)

* Only **ACTIVE loans** accepted for sale
* No transfer if:
* Loan CLOSED
* Balance â¤ 0 at COB
* Active ownership already exists
* Invalid loan ID
* Only one pending transfer allowed per loan
* Ownership changes occur **only during COB**

---

#### 11. Key Design Constraints

* Transfer initiation via API only
* Execution strictly at COB
* Ownership effective date always starts **day after settlement**
* Journal entries linked to owner via mapping tables
* Accounting and Investor modules are logically coupled

---

### Pause Delinquency

#### Overview

Pause Delinquency is a feature that allows users to temporarily pause the delinquency calculation for loan accounts. This functionality provides flexibility in managing loan delinquency status during specific periods, such as when customers are experiencing temporary financial difficulties or during special circumstances.

The system provides API support for establishing a "pause delinquency" on loan accounts and resuming paused delinquency when needed. When a loan is paused, no evaluation of delinquency is performed for that loan account during COB processing, and the delinquency bucket and tags remain unchanged.

#### Introduction

##### Purpose

This document specifies the functional and business requirements for the Pause Delinquency feature in Fineract. It defines the rules for pausing and resuming delinquency calculations, database design, API endpoints, event handling, and validation rules.

##### Scope

The scope of this document includes:

* Pause and Resume delinquency actions at the loan account level
* Database schema for storing delinquency actions
* API endpoints for managing delinquency actions
* Integration with existing delinquency calculation logic
* Event emission when pause flag changes
* Loan API extension with pause status information
* Validation rules for pause and resume actions

##### Applicability

The requirements described apply to:

* Active loan accounts only
* All loan products that support delinquency tracking

##### Definitions and Key Concepts

**Delinquency:** The state of a loan account when payments are overdue beyond the configured delinquency ranges.

**Pause:** An action that temporarily stops the delinquency calculation for a loan account. During the pause period, the delinquency status remains unchanged.

**Resume:** An action that ends an active pause period and re-enables delinquency calculation. The resume date becomes the effective end date for the pause period.

**Pause Period:** The time interval between the pause start date and the effective end date (either the pause end date or the resume date, whichever comes first).

**Delinquency Calculation Paused Status:** The current pause status is determined by checking if the business date falls within any active pause periods. The system maintains a list of pause periods, each with an `active` field indicating if that period is currently active.

**Effective Pause Period:** The actual pause period after considering resume actions. If a resume action occurs during a pause period, it effectively moves the pause end date earlier.

#### Design Decisions and Considerations

##### Loan-Level Feature

This is a feature that belongs to the loan and not a loan product. Each loan account can have its own pause/resume configuration independent of the loan product settings.

##### Scope of Pause

Pause applies to both:

* Loan-level delinquency calculation
* Installment-level delinquency calculation

The pause mechanism controls whether the delinquency recalculation runs during COB processing. When delinquency calculation runs after the pause period, it takes into account the duration of the pause.

##### Pause and Resume Actions

Once a loan is paused, it can be resumed using a resume action. It is not possible to undo a pause by updating or deleting the pause itself. The resume action must be used to end an active pause period.

#### Database Design

##### Overview

The delinquency pause functionality uses the `m_loan_delinquency_action` table to store delinquency actions (pause and resume) for loan accounts. The existing delinquency-related tables remain unchanged.

##### Existing Tables

The following existing tables are related to delinquency:

**m_delinquency_bucket**: A bucket is a set of preconfigured delinquency ranges which is referred by the loan product.

**m_delinquency_range**: The delinquency ranges (e.g.: 5-15 days, 15-30 days, etc.).

**m_delinquency_bucket_mappings**: Creates the association between the ranges and buckets. This table defines which ranges belong to a bucket.

**m_loan_delinquency_tag_history**: Stores the delinquency calculation result, with a history.

##### Table: m_loan_delinquency_action

The `m_loan_delinquency_action` table stores loan-level configuration for delinquency actions (pause and resume).

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | BIGINT | PK, not null | Primary Key of the delinquency action |
| loan_id | BIGINT | Index created, not null, FK to m_loan | Stores the association for the loan |
| action | VARCHAR(128) | not null | The enum type of the action (e.g.: PAUSE, RESUME) |
| start_date | Date | not null | The effective start of the given action, inclusive |
| end_date | Date | optional | The effective end date of the given action, inclusive |
| created_by | BIGINT | not null | Audit field |
| created_on_utc | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field - MySQL: DATETIME(6), PostgreSQL: TIMESTAMP WITH TIME ZONE |
| last_modified_by | BIGINT | not null | Audit field |
| last_modified_on_utc | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field - MySQL: DATETIME(6), PostgreSQL: TIMESTAMP WITH TIME ZONE |

##### Example Data

| id | loan_id | action | start_date | end_date | created_by | created_on_utc | last_modified_by | last_modified_on_utc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 100 | PAUSE | 2023-10-05 | 2023-10-10 | 1001 | 2023-10-05T10:49:54Z | 1001 | 2023-10-05T10:49:54Z |
| 2 | 100 | RESUME | 2023-10-08 |  | 1001 | 2023-10-07T10:49:54Z | 1001 | 2023-10-07T10:49:54Z |
| 3 | 100 | PAUSE | 2023-10-11 | 2023-10-15 | 1001 | 2023-10-07T11:49:54Z | 1001 | 2023-10-08T10:49:54Z |

##### Database Query Logic

###### Determining Current Pause Status

In order to decide if the delinquency calculation is currently paused or not, the system checks for the most recent delinquency action (ordered by creation date) that is effective on the current business date:

* For PAUSE actions: the business date must be between the pause start date and end date (inclusive)
* For RESUME actions: the business date must be on or after the resume start date, and the resume action has no end date

The logic for interpreting the result:

* **Nothing is returned** â delinquency calculation is enabled
* **PAUSE entry is returned** â currently paused
* **RESUME entry is returned** â delinquency calculation is enabled

###### Calculating Effective Pause Periods

For calculating delinquency ranges, the following algorithm is used:

1. All pause and resume entries are retrieved for a loan from the database
2. Effective pause periods are calculated as follows:
  
  
  
  
  
  * Groups entries by action type (PAUSE or RESUME)
  * For each PAUSE entry, finds a matching RESUME entry (if any) that overlaps with the pause period
  * When a matching RESUME is found, it sets the effective end date of the pause period to the resume start date
3. For each installment, the system filters out pause periods that are not relevant (e.g., not overlapping with the installment’s unpaid period)
4. The effective delinquency is calculated using the formula: `current date - unpaid installment date - sum(relevant pause days)`

#### API Design

##### Delinquency Actions Endpoints

Two endpoints are provided for managing delinquency actions:

* One endpoint retrieves all delinquency actions created for a loan
* Another endpoint submits a new delinquency action for an existing loan

There are **no endpoints for update and delete** of existing delinquency actions. Once created, actions cannot be modified or deleted directly.

###### Retrieve All Delinquency Actions

Retrieve all delinquency-actions for a given loan:

```java
GET /loans/{loanId}/delinquency-actions
GET /loans/external-id/{loanExternalId}/delinquency-actions
```

**Response:**

Returns an array of delinquency actions:

```json
[
  {
    "id": 123,
    "action": "PAUSE",
    "startDate": [2023, 10, 5],
    "endDate": [2023, 10, 8],
    "createdById": 1,
    "createdOn": "2023-10-05T10:49:54Z",
    "updatedById": 1,
    "lastModifiedOn": "2023-10-05T10:49:54Z"
  },
  {
    "id": 125,
    "action": "PAUSE",
    "startDate": [2023, 11, 5],
    "endDate": [2023, 11, 8],
    "createdById": 1,
    "createdOn": "2023-11-05T10:49:54Z",
    "updatedById": 1,
    "lastModifiedOn": "2023-11-05T10:49:54Z"
  }
]
```

###### Create New Delinquency Action

Create a new delinquency action for a loan:

```java
POST /loans/{loanId}/delinquency-actions
POST /loans/external-id/{loanExternalId}/delinquency-actions
```

**Request Body:**

```json
{
  "action": "pause",
  "startDate": "2023-10-05",
  "endDate": "2023-10-08",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

**Note:** The `dateFormat` and `locale` fields are optional. If not provided, default values will be used.

**Response:**

Returns a standard command processing result:

```json
{
  "officeId": 1,
  "clientId": 1,
  "resourceId": 123
}
```

The `resourceId` field contains the ID of the created delinquency action.

##### Loan Read Endpoint

The loan read endpoint includes delinquency information, including pause periods.

```java
GET /loans/{loanId}
GET /loans/external-id/{loanExternalId}
```

**Response Structure:**

The `GetLoansLoanIdResponse` contains the following fields related to delinquency:

* `GetLoansLoanIdDelinquencySummary delinquent` - comprehensive delinquency summary data
* `DelinquencyRangeData delinquencyRange` - current delinquency range classification

**Delinquency Summary Fields:**

The `GetLoansLoanIdDelinquencySummary` object contains:

* **Collection Data:**
* `availableDisbursementAmount` (BigDecimal) - available amount for disbursement
* `availableDisbursementAmountWithOverApplied` (BigDecimal) - available amount with over-applied consideration
* `pastDueDays` (Integer) - number of days past due
* `nextPaymentDueDate` (LocalDate) - next payment due date
* `nextPaymentAmount` (BigDecimal) - next payment amount
* `delinquentDays` (Integer) - number of delinquent days
* `delinquentDate` (LocalDate) - date when loan became delinquent
* `delinquentAmount` (BigDecimal) - total delinquent amount
* `delinquentPrincipal` (BigDecimal) - delinquent principal amount
* `delinquentInterest` (BigDecimal) - delinquent interest amount
* `delinquentFee` (BigDecimal) - delinquent fee amount
* `delinquentPenalty` (BigDecimal) - delinquent penalty amount
* `lastPaymentDate` (LocalDate) - date of last payment
* `lastPaymentAmount` (BigDecimal) - amount of last payment
* `lastRepaymentDate` (LocalDate) - date of last repayment
* `lastRepaymentAmount` (BigDecimal) - amount of last repayment
* **Pause Periods:**
* `delinquencyPausePeriods` (List<GetLoansLoanIdDelinquencyPausePeriod>) - list of pause periods for the loan
* **Installment Level Delinquency:**
* `installmentLevelDelinquency` (List<GetLoansLoanIdLoanInstallmentLevelDelinquency>) - installment-level delinquency data (if enabled)

**Pause Period Structure:**

Each `GetLoansLoanIdDelinquencyPausePeriod` object contains:

* `active` (Boolean) - indicates if this pause period is currently active based on the business date
* `pausePeriodStart` (LocalDate) - start date of the pause period
* `pausePeriodEnd` (LocalDate) - effective end date of the pause period

**Note:** The system supports multiple pause periods. The `active` field in each pause period indicates whether that specific period is currently active. A period is considered active if the current business date falls between `pausePeriodStart` (inclusive) and `pausePeriodEnd` (inclusive).

#### Validation Rules

##### General Rules

* Pause and resume delinquency actions can only be created for **active loan accounts**
* Currently only **PAUSE** and **RESUME** actions are supported

##### Validation Rules for Pause

* Pause start date must be **on or after the disbursement date** of the loan
* Pause must last at least a day (start date must be before end date)
* **Overlapping pause periods are not allowed**
* A loan account can have multiple pause periods, but the dates do not overlap with one another
* Both start date and end date are mandatory for pause actions

##### Validation Rules for Resume

* Resume can only be used when there is an **active pause**
* Resume start date must be **exactly equal to the current business date** (cannot be backdated or future-dated)
* In case of resume, end_date must **not** be specified
* Only one resume action can exist for a given date (duplicate resumes on the same date are not allowed)
* The resume date will become the effective pause end date for pause date calculations

#### Business Rules

##### Delinquency Calculation During Pause

* While a loan account is actively paused:
  
  
  
  
  
  * No evaluation of delinquency will be performed for that loan account during COB processing
  * The delinquency bucket and tags remain unchanged during the pause period

##### Pause Period Expiration

* When the business date moves beyond the pause period end date (or resume date, if applicable), the pause period is no longer active
* Delinquency calculation runs during COB processing when the business date is outside any active pause periods
* The system checks pause status during COB processing and calculates delinquency if the loan is not currently paused

##### Delinquency Recalculation After Pause Period

* When a pause period ends (either by reaching the end date or through a resume action), delinquency is recalculated during the next COB (Close of Business) run when the system processes the loan and detects that it is no longer paused
* The resume date (if used) becomes the effective pause end date for pause date calculations
* Delinquency calculation running after the pause period takes into account the duration of the pause by subtracting pause days from the overdue calculation

##### Effective Pause Period Calculation

* Effective pause periods are calculated by merging the pause and related resume entries
* When there is a resume entry, it technically moves the end_date of the pause period earlier
* For each installment, only relevant pause periods (overlapping with the installment’s unpaid period) are considered
* The effective delinquency is calculated using the formula: `current date - unpaid installment date - sum(relevant pause days)`

#### Event Definition

##### Overview

Events are emitted when delinquency actions are created and when the state of the delinquency calculation flag changes during COB processing.

##### New Business Event

**LoanAccountDelinquencyPauseChangedBusinessEvent** is emitted whenever a delinquency action (pause or resume) is created for a loan account. This event is triggered immediately after the action is saved to the database.

##### Existing Events

In the regular loan COB process, the system calculates and sets delinquency tags for loans with the current date.

**LoanDelinquencyRangeChangeBusinessEvent** is emitted when:
* The pause status changes during COB processing (e.g., when entering or exiting a pause period)
* A backdated pause action is created that affects the current delinquency status

##### Changes to CollectionDataV1

**CollectionDataV1** (Avro schema) has been extended with a new field:

* `delinquencyPausePeriods` (array of `DelinquencyPausePeriodV1`) - list of pause periods for the loan

Each `DelinquencyPausePeriodV1` contains:

* `active` (boolean) - indicates if this pause period is currently active
* `pausePeriodStart` (string) - start date of the pause period
* `pausePeriodEnd` (string) - effective end date of the pause period

This allows external systems to track pause periods through the existing event infrastructure without requiring a new event schema version.

##### Event Trigger

The following events are triggered:

* **LoanAccountDelinquencyPauseChangedBusinessEvent**: Emitted when any delinquency action (pause or resume) is created
* **LoanDelinquencyRangeChangeBusinessEvent**: Emitted when the pause status changes during COB processing or when a backdated pause affects current status

##### Backdated Pause Handling

When a backdated pause action is created (start date is before the current business date), the system will:

* Recalculate the loan’s delinquency data immediately
* If the pause end date is after the current business date, emit `LoanDelinquencyRangeChangeBusinessEvent` to reflect the current pause status
* Always emit `LoanAccountDelinquencyPauseChangedBusinessEvent` when any action is created

#### Example Scenarios

##### Scenario #1: Simple Pause Period

**Setup:**
* Loan disbursement: January 1st, 2022 (Amount: 1000)
* Installment #1: Due January 7th, 2022 (Amount: 250)
* Installment #2: Due January 28th, 2022 (Amount: 250)
* Installment #3: Due February 14th, 2022 (Amount: 250)
* Installment #4: Due March 7th, 2022 (Amount: 250)

**Pause Period:** January 2nd - January 20th, 2022

**Behavior:**

* **Pause Flag:** False on January 1st, True from January 2nd to January 20th, False from January 21st onwards
* **Installment #1:**
  
  
  
  
  
  * Pause days: 1-18 (January 2nd-20th)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from January 7th to January 20th, then increments from 2 (January 21st)
* **Installment #2:**
  
  
  
  
  
  * Pause days: 0-5 (January 2nd-20th, but only relevant days after installment due date)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from January 28th, then increments
* **Installment #3:**
  
  
  
  
  
  * Pause days: 0-13 (January 2nd-20th, but only relevant days before installment due date)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from February 14th, then increments

##### Scenario #2: Pause with Resume

**Setup:**
* Same loan schedule as Scenario #1

**Pause Period:** January 2nd - January 20th, 2022
**Resume Date:** January 15th, 2022

**Behavior:**

* **Effective Pause Period:** January 2nd - January 14th, 2022 (resume on 15th effectively ends the pause earlier)
* **Installment #1:**
  
  
  
  
  
  * Pause days: 0-13 (January 2nd-14th)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from January 7th to January 14th, then increments from 1 (January 15th)
* **Installment #2:**
  
  
  
  
  
  * Pause days: 0-13 (January 2nd-14th)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from January 28th, then increments
* **Installment #3:**
  
  
  
  
  
  * Pause days: 0-13 (January 2nd-14th)
  * Unpaid installment date: Increments daily from 0
  * Overdue days: Shows 1 from February 14th, then increments

The resume action effectively moves the pause end date from January 20th to January 14th, resulting in fewer pause days being counted for delinquency calculations.

#### Summary

The Pause Delinquency feature provides a flexible mechanism for temporarily suspending delinquency calculations on loan accounts. Key aspects include:

* Loan-level configuration (not product-level)
* Support for multiple non-overlapping pause periods
* Resume functionality to end pause periods early
* Automatic expiration of pause periods when business date moves beyond the end date
* Integration with existing delinquency calculation logic
* Event emission when pause status changes
* API endpoints for managing pause/resume actions
* Extension of loan read API with pause status information

### Loan Re-Amortization

#### Overview

Re-amortization recalculates EMI (Equal Monthly Installment) amounts for remaining installments based on the outstanding principal balance as of the current business date.

##### Example

A customer has a 1000 EUR loan with 4 monthly installments of 250 EUR each. After missing the first two payments (500 EUR overdue), re-amortization redistributes this amount across the remaining 2 installments, resulting in 500 EUR per installment instead of 250 EUR - without changing due dates or adding new installments.

##### Re-Amortization vs Re-Aging

| Aspect | Re-Amortization | Re-Aging |
| --- | --- | --- |
| Schedule structure | Preserves existing installment count and due dates | Creates new installments with user-defined count, start date, and frequency |
| User input | Only interest handling type | Start date, number of installments, period type, frequency, interest handling |
| Use case | Redistribute overdue principal across existing future installments | Restructure loan for customers in payment difficulty |

#### Supported Loan Type

Re-amortization is only available for:

* **Progressive** loan schedule type
* **Advanced Payment Allocation** strategy
* For interest-bearing loans: **interest recalculation must be enabled**

#### Eligibility Criteria

* Loan must be **active** (disbursed and not closed)
* Transaction date must be **before or on maturity date**
* Loan must **not** be charged-off
* Loan must **not** be contract terminated
* Only **one** re-amortization transaction is allowed per business day

#### Interest Handling Types

For **interest-bearing loans**, re-amortization supports three strategies:

| Type | Description |
| --- | --- |
| `DEFAULT` | Standard behavior - outstanding principal is redistributed across remaining installments |
| `EQUAL_AMORTIZATION_INTEREST_SPLIT` | Outstanding principal and interest are split equally across remaining installments |

#### Business Events

* `LoanReAmortizeBusinessEvent` - triggered after re-amortization
* `LoanReAmortizeTransactionBusinessEvent` - triggered for the transaction
* `LoanUndoReAmortizeBusinessEvent` - triggered after undo operation
* `LoanUndoReAmortizeTransactionBusinessEvent` - triggered for undo transaction

#### Permissions

* `REAMORTIZE_LOAN` - required to apply re-amortization
* `UNDO_REAMORTIZE_LOAN` - required to undo re-amortization

#### API Endpoints

##### Apply Re-Amortization

* **Endpoint**: `POST /loans/{loanId}/transactions?command=reAmortize`
* **Alternative**: `POST /loans/external-id/{loanExternalId}/transactions?command=reAmortize`

###### Request Body

```json
{
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
    "externalId": "ext-123",
    "reAmortizationInterestHandling": "DEFAULT",
    "reasonCodeValueId": 1
}
```

| Parameter | Required | Description |
| --- | --- | --- |
| `locale` | Yes | Locale for parsing |
| `dateFormat` | Yes | Date format pattern |
| `externalId` | No | External identifier for the transaction (max 100 chars) |
| `reAmortizationInterestHandling` | No | Interest handling type: `DEFAULT` or `EQUAL_AMORTIZATION_INTEREST_SPLIT`. Defaults to `DEFAULT` |
| `reasonCodeValueId` | No | Code value ID for re-amortization reason (from `ReamortizationReasons` code) |

###### Response Body

```json
{
    "officeId": 1,
    "clientId": 1,
    "loanId": 1,
    "resourceId": 15,
    "resourceExternalId": "ext-123",
    "changes": {
        "locale": "en",
        "dateFormat": "dd MMMM yyyy"
    }
}
```

##### Undo Re-Amortization

* **Endpoint**: `POST /loans/{loanId}/transactions?command=undoReAmortize`
* **Alternative**: `POST /loans/external-id/{loanExternalId}/transactions?command=undoReAmortize`

###### Request Body

```json
{
    "locale": "en",
    "dateFormat": "dd MMMM yyyy",
    "externalId": "reversal-ext-123"
}
```

###### Response Body

```json
{
    "officeId": 1,
    "clientId": 1,
    "loanId": 1,
    "resourceId": 15,
    "resourceExternalId": "ext-123",
    "changes": {
        "locale": "en",
        "dateFormat": "dd MMMM yyyy"
    }
}
```

##### Preview Re-Amortization

Generates a preview of the re-amortized schedule without modifying the loan.

* **Endpoint**: `GET /loans/{loanId}/transactions/reamortization-preview`
* **Alternative**: `GET /loans/external-id/{loanExternalId}/transactions/reamortization-preview`

###### Query Parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `reAmortizationInterestHandling` | Yes | Interest handling type: `DEFAULT` or `EQUAL_AMORTIZATION_INTEREST_SPLIT` |

###### Response Body

Returns the projected loan schedule with recalculated installments:

```json
{
    "currency": {
        "code": "USD",
        "decimalPlaces": 2
    },
    "loanTermInDays": 60,
    "totalPrincipalDisbursed": 1000.00,
    "totalPrincipalExpected": 1000.00,
    "totalInterestCharged": 50.00,
    "totalFeeChargesCharged": 0.00,
    "totalRepaymentExpected": 1050.00,
    "periods": [
        {
            "period": 1,
            "dueDate": "01 February 2023",
            "principalDue": 500.00,
            "interestDue": 25.00,
            "totalDueForPeriod": 525.00
        },
        {
            "period": 2,
            "dueDate": "01 March 2023",
            "principalDue": 500.00,
            "interestDue": 25.00,
            "totalDueForPeriod": 525.00
        }
    ]
}
```

##### Transaction Template

* **Endpoint**: `GET /loans/{loanId}/transactions/template?command=reAmortization`

#### Behavior

Installments excluded from redistribution:

* Down-payment installments
* Re-aged installments
* Additional (N+1) installments

Outstanding principal from installments with due date â¤ transaction date is redistributed equally across future installments.

#### Implementation Notes

Creates a `REAMORTIZE` transaction with:

* `transactionDate` = current business date
* `amount` = outstanding principal until transaction date
* `principalPortion` = outstanding principal
* `interestPortion` = 0
* `feeChargesPortion` = 0
* `penaltyChargesPortion` = 0

Non-monetary transaction - no GL entries created.

### Loan Re-Aging

#### Overview

Re-aging also known as Settlement Plan is to assist customers who are in duress around repaying their loans;

The goal is to create a new set of Installments for the same loan account from the principal outstanding pending on the loan account

For example, for a customer who is severely behind on payments, they could agree to a settlement plan where instead of having to pay now, it could be spread over the next 12 months, paying back the remaining 750 euro balance but over 10 equal payments.

#### Introduction

##### Purpose

This document specifies the functional and business requirements for the Re-Aging feature for Progressive loan products in Fineract.
It defines rules for interest handling, schedule regeneration, charge/fee mapping, special installments, and reversal logic to ensure consistent behavior across different interest handling methods.

##### Scope

The scope of this document includes:
* Re-Aging for Progressive, interest-bearing loans * Handling of Default, Equal Amortization scenarios * Support for backdated transactions * Schedule regeneration and installment remapping * Special collected installment creation * Reversal and replay of Re-Age transactions * User-driven configuration of re-aged schedule (start date, number of installments, period type/frequency)

This document does **not** cover:
* Non-Progressive loan strategies * Charge-off loan accounts * Interest-bearing loans outside the scope of Fineract Progressive product definition * External API documentation (covered separately)

##### Applicability

The requirements described apply to:
* Progressive loan products * Non-interest-nearing and Interest-bearing accounts with or without interest recalculation enabled * Loan accounts where re-aging may occur at any date â¥ last repayment date

##### Definitions and Key Concepts

**Re-Age:** The process of recalculating and adjusting the remaining loan schedule, including principal, interest, fees, and penalties, starting from a specified start date.
**Transaction Date:** The accounting/event date when re-aging is applied.
**Start Date:** The due date of the first re-aged installment (re-age start date).
**Special Collected Installment:** A single installment created to capture paid portions from installments with due-date after the transaction date.
**N+1 Installment:** Any additional installment added to the schedule before or after re-aging to balance principal, interest, and fees.
**Interest Handling:** The method applied during re-aging â Default, Equal Amortization.
**Chargeback:** A partial or full reversal of a previously posted repayment, adjusting principal, interest, and/or fees back to their prior state.

#### General Re-Aging Rules

##### Eligibility Criteria

* Re-Aging is allowed only for Progressive loan products.
* The re-age transaction date must be **greater than or equal to the last repayment date**.
* Re-Aging can be applied **anywhere in the loan lifecycle**, including before maturity.

##### Transaction Date vs Start Date

* **Transaction Date**: The accounting/event date when re-aging is applied.
* **Start Date**: The due date of the first re-aged installment.
* In backdated scenarios, **transaction date = start date**.
* In non-backdated scenarios, **transaction date â¤ start date**.
* The re-aged schedule begins from the start date, irrespective of past due installments.

##### Partial Payments Handling

* Any installment with a **partially paid amount** before the transaction date:
  
  
  
  
  
  * The **paid portion remains** allocated to the original installment.
  * The **unpaid portion** is included in the re-aged schedule.
* Installments fully paid before transaction date remain unchanged.

##### Down-Payment Handling

* Down-payments are **not affected** by re-aging.
* They remain linked to the original installment and are excluded from the re-age calculations.

##### Chargebacks

* Charge-back amounts (principal, interest, fees) are processed according to the selected interest handling scenario:
  
  
  
  
  
  * Equal Amortization: split across new installments.
  * Default: principal re-aged, interest moved to first new installment.
* Only **unpaid** are affected.

##### Special Collected Installments

* Any installment with **due-date > transaction date** that has payments posted before the transaction date:
  
  
  
  
  
  * Paid portions are **merged into a single special collected installment**.
  * Due date = transaction date.
  * GL postings must remain identical to original payments.
  * The special installment does not participate in interest/principal redistribution.
* Supports reverse and replay logic for backdated transactions.

##### Reversal and Replay Rules

* Re-Age transactions can be **reversed only if they are the latest transaction** on the loan account.
* Any backdated repayment or reversal triggers **reverse + replay**:
  
  
  
  
  
  * Reverts schedule to original state before re-age.
  * Removes special collected installment if it exists.
  * Restores charge/fee mapping.
* Backdated transaction posting or reversals triggers **reverse + replay**

##### User Input Parameters

Users must provide the following inputs when applying re-aging:
* **Start Date**: first due date of the re-aged schedule.
* **Number of Re-aged Installments**: total installments to generate.
* **Period Type**: Daily, Weekly, Monthly, or Yearly.
* **Period Frequency**: number of units per period type.
* **Interest Handling Method**: Default, Equal Amortization.
* These inputs drive the schedule generation, replacement of future installments, and calculation of N+1 installment.
* In case of non-interest-bearing loans interest handling strategy is omitted

##### Implementation details

Implementation core is located in AdvancedPaymentScheduleTransactionProcessor.
the entrypoint of the feature is handleReAge.
handleReAge function is the purpose of configure the different re-age strategies and handle both interest bearing and non interest bearing scenarios.
There is no real handling, and all the different specific handlers are described in the related interest handling scenarios dev notes chapters.

#### Non-Interest-Bearing Scenario

##### Background and Context

Re-aging functionality for **Non-Interest-Bearing Progressive loans** existed only **after maturity date**.
This means Fineract now supports re-aging before maturity date.

This enhancement introduces the ability to:
* Apply re-aging at **any point after the first disbursement**
* Apply re-aging **before or after maturity**
* Override installment schedule when necessary * Handle partially paid installments via **special installment creation**

Principal-only amortization â no future interest calculation involved.

##### General Re-Aging Rules

* Re-aging date **may be before last repayment date**
* Only **outstanding principal + outstanding fees/penalties** are redistributed
* Re-aging transaction remains **non-monetary**
* GL entries are not created

Fees/Penalties behavior:
* Fees/penalties **retain their due dates**
* Re-mapped to appropriate new installment when impacted by re-aging

##### Schedule Modification Requirements

When the re-aging transaction occurs before maturity date or overlaps future repayment periods:

* **Installments before the re-aging transaction date**
  
  
  
  
  
  * Only **paid portions** are retained
  * Any **unpaid portion** is included in re-aging redistribution
* **Installments on or after the re-aging transaction date**
  
  
  
  
  
  * Replaced with newly generated re-aged installments
  * New due dates and installment structure are based on re-aging configuration (period count, period type, frequency)

##### Handling of N+1 Installments (Post-Maturity Items)

N+1 installments exist to hold items that occur **after** the core repayment term â typically post-maturity fees and penalties (and in some contexts, post-maturity interest; interest is out of scope for this document but noted here for context).

Business rule:
* After re-aging, an existing N+1 installment is **kept only if its due date is strictly after the new maturity date** produced by the re-aged schedule.
* If an N+1 installment’s due date is **on or before** the new maturity date, it is **removed** and any underlying items are handled as part of the regenerated re-aged schedule.

##### Special Installment Handling

Special installments are created when **the re-aging transaction date** is before or on previous maturity date.
In this case:
* Any installment occurring after the re-aging date that has a paid portion is **collected and converted into special installments** to preserve historical repayment accuracy.
* Transactions already posted remain mapped to these special installments.
* All general ledger entries remain unchanged â no reversals are introduced because the payments were already consumed by the loan.

This ensures:
* Historical repayment activity is represented accurately.
* Only unpaid obligations are restructured in the new re-aged repayment plan.

##### Developer’s Note

Implementation is found in AdvancedPaymentScheduleTransactionProcessor Entry point for non-interest-bearing loans is `handleReAgeWithCommonStrategy`.

This implementation also contains solution for interest-bearing but not EMICalculator compatible loan schedules.
Implementation-wise it has the same logic, the only exception is the interest related calculations ends in zero amounts.

Core Logic steps:

* determine outstanding balances
* update transaction amounts to outstanding balances
* handle reversal if total amount is zero
* calculate EqualAmortizationValues for attributes recalculated by re-age
* handle charges if needed
* collect paidInAdvanceBalances - to move them into the special installment if required
* create special installment for early repaid balances.
* create first re-aged installment
  
  
  
  
  
  * try to merge or insert it depending on the existing schedule
  * add charge mapping
* create other re-aged installments if needed
  
  
  
  
  
  * try to merge or insert it depending on the existing schedule
  * add charge mapping

Note: merging the re-aged installments depends on the existing installment due-date and index.
Also, it keeps the charge mapping correct, in case charges (fees and penalties) should not be affected by re-age.

#### Interest Handling Scenarios

##### Scenario #1 â Equal Amortization

###### Core Logic

* Outstanding unpaid amounts (principal, interest, fees/penalties â¤ transaction date) are **split equally** across the newly generated installments.
* No new interest accrues after re-age â interest recalculation and declining balance logic are **turned off**.
* User-selected interest scope determines which interest is included:
  
  
  
  
  
  * **Outstanding Payable Interest**: only interest due to date.
  * **Outstanding Full Interest**: all accrued interest, including future installments if applicable.

###### Outstanding Principal, Interest, Fees/Penalties

* **Principal**: only unpaid portion included in equal split.
* **Interest**: split according to user-selected interest scope.
* **Fees/Penalties**: unpaid portions with due-date â¤ transaction date are included in the equal split; due-date > transaction date remain mapped to original installments.

###### Special Collected Installment

Same to non-interest-bearing scenario

###### Schedule Generation & N+1 Installment Adjustment

* Re-aged installments start from the **user-provided start date**.
* The number of installments, period type, and frequency are **user-defined**.
* N+1 installment may be adjusted to balance rounding differences in principal/interest/fees.
* Fully paid installments before start date remain unchanged; partially paid installments retain the paid portion, with unpaid portion included in re-age.

###### GL / Transaction Recording

* A **non-monetary re-age transaction** is posted with amount = total outstanding principal + interest + fees/penalties included in equal split.
* Special collected installment GL postings match original repayments.
* Reversal of re-age removes non-monetary transaction and restores original schedule and mappings.

###### Developer’s Note

Entrypoint: `AdvancedPaymentScheduleTransactionProcessor:handleReAgeEqualAmortizationEMICalculator`

Core Logic steps:

* determine outstanding balances
* update transaction amounts to outstanding balances
* handle reversal if total amount is zero
* calculate EqualAmortizationValues for non progressive model handled attributes
* handle charges
* collect paidInAdvanceBalances - to move them into the special installment if required
* update model with EMICalculator - see corresponding steps in next chapter
* remove installments after transaction date
  
  
  
  
  
  * keep N+1 installments and update it’s from date if it has a due date after the new maturity date, otherwise it is removed
* create special and re-aged installments according to model and update by EqualAmortizationValues calculated values
* update installments index

ProgressiveEMICalculator

Entry point: reAgeEqualAmortization

* **Determine original maturity and check if transaction is after it**
* **Calculate outstanding principal, interest for re-age**
* **Calculate already paid balances since transaction date**
  
  
  
  
  
  * Also sets moved credited principal & interest balances to handle not paid credited portions post re-age correctly which will be added back to fist re-age repayment period
* **Accelerate maturity date**
  
  
  
  
  
  * this step is actually modifies existing model by removing interest and repayment periods from re-age transaction date
* **Close existing repayment periods**
  
  
  
  
  
  * Marks **outstanding interest as moved due to re-aging**.
  * Sets EMI of each period to **total paid amount**.
  * Stops further unrecognised interest calculation.
* **Handle early repaid installments**
  
  
  
  
  
  * If any principal or interest has been paid beyond the transaction date:
  * Preserves paid amounts in a **special collected repayment period**.
* **Update model for re-aged periods**
  
  
  
  
  
  * Generates empty repayment periods according to the number of new installments.
* **Calculate EMI for new periods**
  
  
  
  
  
  * Splits principal, interest, and fees/penalties equally across new installments.
  * Ensures **rounding differences** are applied to the last installment.
* **Recalculate outstanding balance**
* **Add zero-interest period**
  
  
  
  
  
  * Ensures interest rate after re-age start is handled correctly.
  * If transaction is posted before original maturity date, we apply 0 interest from the transaction date
  * If transaction is posted after maturity date, we should add zero interest period from the original maturity date.
* **Calculate last unpaid repayment period EMI**
  
  
  
  
  
  * Ensures final installment balances the loan fully.

##### Scenario #2 â Default Behavior

###### Core Logic

* Overdue principal and charge-back principal are **re-aged** across new installments.
* Overdue interest and charge-back interest are moved **100% to the first new re-aged installment**.
* Future interest continues to accrue according to loan product rules (only past-due interest may be included in re-age calculation if applicable).
* Overdue fees and penalties are moved to the **first new re-aged installment**.
* Future fees and penalties remain on their original installments and are adjusted externally (not part of re-age logic).

###### Overdue vs Future Interest Handling

* Only **past-due interest** may be included in the re-age calculation.
* Overdue interest is **not split** â it goes entirely to the first re-aged installment.
* Future interest is calculated normally per the interest model.
* Charge-back interest follows the same rule: moved entirely to the first re-aged installment.

###### Overwriting Existing Future Installments

* Existing installments with due-date â¥ start date are replaced by **re-aged installments**.
* New installments are generated according to user-provided **start date, number of installments, period type, and frequency**.
* If re-age reduces total installments, any installments beyond new maturity date are removed.
* N+1 installments are recalculated to balance principal, interest, and fees.

###### Special Collected Installment

Same to non-interest-bearing scenario

###### Fees/Penalties Handling

* Overdue fees and penalties are moved to the **first re-aged installment**.
* Fees/penalties with due-date > start date remain on their original installments; mappings adjusted if installment numbering changes.
* Recalculation of future fees and penalties is handled outside re-age logic.

###### Schedule Generation & N+1 Installment Adjustment

* Schedule starts from **start date** provided by user.
* Number of installments, period type, and frequency are **user-defined**.
* Fully paid installments before start date remain unchanged.
* Partially paid installments: paid portion retained, unpaid portion included in re-aged principal.

###### Reversal / Backdated Transaction Handling

* Re-age can be reversed **only if it is the latest transaction**.
* Any backdated repayment or reversal triggers **reverse + replay**:
  
  
  
  
  
  * Removes special collected installment.
  * Restores original installment schedule.
  * Restores original charge/fee mappings and GL postings.
  * Re-applies re-age if necessary.

#### Schedule & Installment Mapping

##### Charge/Fee â Installment Mapping

* All fees and penalties are linked to specific installments in the schedule.
* After re-aging, the mapping must be updated to point fees/penalties to the correct new installment IDs.
* For fees/penalties with due-date > start date:
  
  
  
  
  
  * Preserve original due-date.
  * Adjust installment mapping only if installment IDs are shifted due to schedule regeneration.
* Overdue fees/penalties moved to first re-aged installment must have their mapping updated to the new installment ID.

##### Due Date Recalculation Rules

* Re-aged installments start from **user-provided start date**.
* Subsequent installment due-dates are calculated based on:
  
  
  
  
  
  * **Period Type**: Daily, Weekly, Monthly, Yearly
  * **Period Frequency**: number of periods between installments
* Fully paid installments before start date remain unchanged.
* Partial payments are preserved for principal and fees; only unpaid portions are re-aged.
* Any installment after the new maturity date is deleted if the re-age reduces total number of installments.

##### N+1 Installment Adjustment

* After generating re-aged installments, the **N+1 installment** is adjusted to balance rounding differences in principal, interest, and fees.
* Applies to all interest handling scenarios.
* Ensures total outstanding principal, interest, and fees are fully allocated across the new schedule.

##### Edge Cases

* Special collected installment:
  
  
  
  
  
  * Created if transaction date is before or on maturity date.
  * Merges all paid portions into a single installment.
  * GL postings must match original payments.
  * Does not participate in principal/interest redistribution.
* Reversal of re-age:
  
  
  
  
  
  * Only allowed if it is the latest transaction.
  * Removes special collected installment.
  * Restores original installment schedule, charge/fee mappings, and GL postings.
* Backdated re-age:
  
  
  
  
  
  * Transaction date = start date.
  * Reverse + replay logic applied to rebuild schedule correctly.

#### Validation Rules

##### Transaction Date Validation

* Transaction date cannot be before the start of the loan lifecycle.
* For backdated re-age, transaction date = start date.

##### Start Date Validation

* Start date cannot be earlier than the loan disbursement date.
* Start date drives the first installment of the re-aged schedule.

##### Re-Age Eligibility

* Re-aging is allowed only for Progressive loan strategy.
* Charge-off loan accounts are **not eligible** for re-aging.

#### Summary Comparison Table For Interest Handling Scenarios

| Feature | Equal Amortization | Default Behavior | Notes |
| --- | --- | --- | --- |
| Outstanding Principal | Equally split across new installments | Re-aged according to schedule | Only unpaid portion is considered; paid portion preserved |
| Outstanding Interest | Equally split (full or payable) among new installments | Overdue interest moved 100% to first re-aged installment; future interest continues normally | â |
| Charge-back Principal | Equally split | Re-aged according to schedule | â |
| Charge-back Interest | Equally split | Moved 100% to first re-aged installment | â |
| Overdue Fees / Penalties | Equally split | Moved to first re-aged installment | Future fees handled externally, not part of re-age |
| Special Collected Installment | Created if installments after transaction date are partially paid; due date = transaction date; GL postings preserved | Same as Equal Amortization | Not included in principal/interest redistribution |
| User Input Parameters | Start date, number of installments, period type/frequency, interest handling method | Same as Equal Amortization | Inputs drive new schedule generation |

### Delayed Schedule Captures / Full Term Tranches

#### Overview

Full Term Tranche is a feature for **multi-disbursement Progressive loans** where each disbursement (tranche) is amortized over the full original term of the loan, instead of over the remaining term only. This supports use cases where captures (disbursements) can happen later in the loan lifecycle, while still granting the customer the full intended term for each captured amount.

#### Configuration

##### Loan Product Level

The Full Term Tranche feature is configured on the loan product.

The following conditions apply:

* **Multi-disbursement must be enabled**
* **Loan schedule type must be PROGRESSIVE** (which requires the advanced payment allocation strategy)

A boolean configuration flag is available on the loan product:

* `allowFullTermForTranche` â **Allow full term length for each tranche disbursement**
* Default value: `false`
* When set to `true`, the system enables full term schedule calculation for each disbursement
* Validation rules:
  
  
  
  
  
  * If multi-disbursement is not enabled, enabling this flag is rejected
  * If the schedule type is not PROGRESSIVE, enabling this flag is rejected

##### Loan Account Level

On loan creation, the loan-level flag is determined as follows:

* By default, the loan **inherits** the `allowFullTermForTranche` value from the loan product
* The loan application request may optionally include a boolean `allowFullTermForTranche`:
* If present, it overrides the inherited value for that specific loan
* If set to `true` while the product-level flag is `false`, the request is rejected with validation error

The loan entity stores this value as a persistent field.

#### Behavior

##### Base Schedule Generation

For the **first disbursement**, the repayment schedule is generated according to the standard Progressive EMI calculation rules:

* The number of repayments and term are taken from the loan product configuration
* Installment dates follow the pattern defined by:
* Loan term frequency and type
* Repayment frequency and type
* The first installment due date is derived from the loan configuration (disbursement date, repayment frequency, minimum days between disbursement and first repayment, calendar settings if applicable)

When `allowFullTermForTranche` is **disabled** (`false`), subsequent disbursements behave as in the existing multi-disbursement implementation:

* The new amount is distributed over the **remaining** future installments
* The original maturity date is **not** extended due to additional disbursements

##### Full Term Tranche Behavior (Enabled)

When `allowFullTermForTranche` is **enabled** (`true`) and the product has a positive number of repayments configured:

* For **each new disbursement**:
* The system determines the period in the current schedule where the disbursement date falls
* A **temporary full-term schedule** is calculated for the disbursed amount:
* Principal: equal to the disbursed amount
* Term length (number of repayments): equal to the loan productâs number of repayments
* Term frequency and repayment frequency: copied from the loan product
* Start date: the start date of the period that contains the disbursement date (or the current maturity date if no such period exists)
* The temporary schedule covers the full term for that disbursement, starting from the identified start date
* The temporary schedule is then merged into the existing loan schedule:
* If a period in the temporary schedule has the same from-date and due-date as an existing period, the principal and interest due amounts are added to the existing period
* If a period in the temporary schedule does not match any existing period, a new period is added to the schedule
* When installments are created from the merged schedule, only periods with due dates on or after the disbursement date become installments

As a result, overlapping installments from multiple disbursements on the same due date are aggregated into a single installment with summed amounts, and the maturity date can move later than originally configured to accommodate the full term of later disbursements.

##### Disbursement Scenarios

When full term tranche is enabled:

* **Disbursement on an existing installment date**: The due amounts (principal and interest) for that date are increased according to the full-term calculation for the new tranche
* **Disbursement between installment dates (mid-period)**: A new full-term schedule is calculated from the start of the period that contains the disbursement date, and the newly generated installments are merged into the existing schedule
* **Multiple disbursements before the first repayment date**: Each disbursement contributes its own full-term schedule from the same starting point, and the resulting installments reflect the aggregated principal and interest across all tranches

#### API

The `allowFullTermForTranche` field is available in:

* **Loan Product API**: Create/update requests and read responses
* **Loan API**:
* Create/update requests (optional, inherits from product if not provided)
* Read responses (indicates whether the feature is active for the loan)

The repayment schedule returned by the loan read endpoint reflects the merged full-term schedule when this feature is enabled, showing increased installment amounts on overlapping due dates and extended number of installments when later disbursements extend the term.

### Loan Origination Details

#### Overview

Tracks the originator of a loan (merchant, broker, affiliate, platform, or channel) for revenue sharing and reporting. Originator details are propagated through business events and reporting.

#### Configuration

##### Enabling the Module

```properties
fineract.module.loan-origination.enabled=${FINERACT_MODULE_LOAN_ORIGINATION_ENABLED:true}
```

**Enabled by default.** When disabled, API endpoints become unavailable, event enrichment is skipped, and the loan creation flow continues to work without originator processing.

##### Global Configuration

| Configuration Key | Default | Description |
| --- | --- | --- |
| `enable-originator-creation-during-loan-application` | `false` | Allows automatic creation of new originator records when an unknown `externalId` is provided during loan creation |

#### Data Model

##### Originator Registry (m_loan_originator)

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | BIGINT (PK) | Yes | Auto-generated primary key |
| `external_id` | VARCHAR(100) | Yes | Unique, immutable external identifier (a.k.a. Revenue Share ID) |
| `name` | VARCHAR(255) | No | Originator display name |
| `status` | VARCHAR(20) | Yes | `ACTIVE`, `PENDING`, or `INACTIVE` |
| `originator_type_cv_id` | INT (FK) | No | Code value reference to `LoanOriginatorType` |
| `channel_type_cv_id` | INT (FK) | No | Code value reference to `LoanOriginationChannelType` |
| `created_on_utc` | DATETIME | Yes | Record creation timestamp (UTC) |
| `created_by` | BIGINT (FK) | Yes | Foreign key to `m_appuser` — user who created the record |
| `last_modified_on_utc` | DATETIME | Yes | Last modification timestamp (UTC) |
| `last_modified_by` | BIGINT (FK) | Yes | Foreign key to `m_appuser` — user who last modified the record |

##### Loan-Originator Mapping (m_loan_originator_mapping)

Associates loans with originators. Supports multiple originators per loan, though typical usage is one.

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | BIGINT (PK) | Yes | Auto-generated primary key |
| `loan_id` | BIGINT (FK) | Yes | Foreign key to `m_loan` |
| `originator_id` | BIGINT (FK) | Yes | Foreign key to `m_loan_originator` |
| `created_on_utc` | DATETIME | Yes | Record creation timestamp (UTC) |
| `created_by` | BIGINT (FK) | Yes | Foreign key to `m_appuser` — user who created the record |
| `last_modified_on_utc` | DATETIME | Yes | Last modification timestamp (UTC) |
| `last_modified_by` | BIGINT (FK) | Yes | Foreign key to `m_appuser` — user who last modified the record |

A unique constraint on `(loan_id, originator_id)` prevents duplicate assignments.

##### Code Values

**`LoanOriginatorType`** (default values): `MERCHANT`, `BROKER`, `AFFILIATE`, `PLATFORM`

**`LoanOriginationChannelType`** (default values): `ONLINE`, `IN_STORE`, `API`, `AGGREGATOR`

Both code value sets are extensible — additional values can be added via the standard Code Values API.

#### API Endpoints

##### Originator Registry APIs

###### Create a Loan Originator

`POST /v1/loan-originators`

**Permission**: `CREATE_LOAN_ORIGINATOR`

```json
{
  "name": "Best Merchant in US",
  "externalId": "best-merchant-us-east",
  "status": "ACTIVE",
  "originatorTypeId": 12,
  "channelTypeId": 44
}
```

* `externalId` — **required**, unique, max 100 characters
* `name` — optional, max 255 characters
* `status` — optional, defaults to `ACTIVE`. Allowed values: `ACTIVE`, `PENDING`, `INACTIVE`
* `originatorTypeId` — optional, must reference a valid `LoanOriginatorType` code value
* `channelTypeId` — optional, must reference a valid `LoanOriginationChannelType` code value

**Response:**

```json
{
  "resourceId": 13,
  "resourceExternalId": "best-merchant-us-east"
}
```

| HTTP Code | Description |
| --- | --- |
| 200 | Created successfully |
| 400 | Required parameter missing or incorrect format |
| 403 | Duplicate external ID or insufficient permissions |
| 404 | Originator type or channel type does not exist |

###### List All Loan Originators

`GET /v1/loan-originators`

**Permission**: `READ_LOAN_ORIGINATOR`

```json
[
  {
    "id": 13,
    "externalId": "best-merchant-us-east",
    "name": "Best Merchant in US",
    "status": "ACTIVE",
    "originatorType": {
      "id": 12,
      "name": "MERCHANT",
      "active": true,
      "mandatory": false
    },
    "channelType": {
      "id": 44,
      "name": "ONLINE",
      "active": true,
      "mandatory": false
    }
  }
]
```

###### Retrieve a Loan Originator

`GET /v1/loan-originators/{originatorId}`
`GET /v1/loan-originators/external-id/{externalId}`

**Permission**: `READ_LOAN_ORIGINATOR`

###### Get Template Data

`GET /v1/loan-originators/template`

**Permission**: `READ_LOAN_ORIGINATOR`

Returns a pre-generated `externalId`, available status values, and code value options for originator type and channel type.

###### Update a Loan Originator

`PUT /v1/loan-originators/{originatorId}`
`PUT /v1/loan-originators/external-id/{externalId}`

**Permission**: `UPDATE_LOAN_ORIGINATOR`

```json
{
  "status": "PENDING"
}
```

Updatable fields: `name`, `status`, `originatorTypeId`, `channelTypeId`. Only changed fields need to be included.

**Response:**

```json
{
  "resourceId": 13,
  "resourceExternalId": "best-merchant-us-east",
  "changes": {
    "status": "PENDING"
  }
}
```

| HTTP Code | Description |
| --- | --- |
| 200 | Updated successfully |
| 400 | Unsupported parameter (e.g. `externalId`) or incorrect format |
| 404 | Originator not found |

> [!IMPORTANT]
> The `externalId` field **cannot be updated** after creation.

###### Delete a Loan Originator

`DELETE /v1/loan-originators/{originatorId}`
`DELETE /v1/loan-originators/external-id/{externalId}`

**Permission**: `DELETE_LOAN_ORIGINATOR`

| HTTP Code | Description |
| --- | --- |
| 200 | Deleted successfully |
| 403 | Originator is currently mapped to one or more loans |
| 404 | Originator not found |

> [!IMPORTANT]
> An originator cannot be deleted if it is currently mapped to any loans.

##### Loan-Originator Mapping APIs

###### Attach Originator to Loan

`POST /v1/loans/{loanId}/originators/{originatorId}`
`POST /v1/loans/{loanId}/originators/external-id/{originatorExternalId}`
`POST /v1/loans/external-id/{loanExternalId}/originators/{originatorId}`
`POST /v1/loans/external-id/{loanExternalId}/originators/external-id/{originatorExternalId}`

**Permission**: `ATTACH_LOAN_ORIGINATOR`

No request body.

**Response:**

```json
{
  "loanId": 45,
  "loanExternalId": "11793428-12cb-42fe-ab9f-72b4ddf2453a",
  "originatorId": 13,
  "originatorExternalId": "best-merchant-us-east"
}
```

| HTTP Code | Description |
| --- | --- |
| 200 | Attached successfully |
| 403 | Loan is not in Submitted and Pending Approval status, originator is not ACTIVE, or mapping already exists |
| 404 | Loan or originator not found |

###### Detach Originator from Loan

`DELETE /v1/loans/{loanId}/originators/{originatorId}`
`DELETE /v1/loans/{loanId}/originators/external-id/{originatorExternalId}`
`DELETE /v1/loans/external-id/{loanExternalId}/originators/{originatorId}`
`DELETE /v1/loans/external-id/{loanExternalId}/originators/external-id/{originatorExternalId}`

**Permission**: `DETACH_LOAN_ORIGINATOR`

No request body. Response format is the same as Attach.

| HTTP Code | Description |
| --- | --- |
| 200 | Detached successfully |
| 403 | Loan is not in Submitted and Pending Approval status |
| 404 | Loan, originator, or mapping not found |

###### Retrieve Originators for a Loan

`GET /v1/loans/{loanId}/originators`
`GET /v1/loans/external-id/{loanExternalId}/originators`

**Permission**: `READ_LOAN`

```json
{
  "originators": [
    {
      "id": 13,
      "externalId": "best-merchant-us-east",
      "name": "Best Merchant in US",
      "status": "ACTIVE",
      "originatorType": {
        "id": 12,
        "name": "MERCHANT",
        "active": true,
        "mandatory": false
      },
      "channelType": {
        "id": 44,
        "name": "ONLINE",
        "active": true,
        "mandatory": false
      }
    }
  ]
}
```

###### Originators via Retrieve Loan API

Originator details can also be fetched as part of the standard Retrieve Loan API using the `associations` query parameter:

`GET /v1/loans/{loanId}?associations=originators`
`GET /v1/loans/external-id/{loanExternalId}?associations=originators`

**Permission**: `READ_LOAN`

The `originators` association is also included when `associations=all` is used. Since the `associations` parameter defaults to `all`, originator data is included in the Retrieve Loan response by default (even without an explicit `associations` parameter). The response adds an `originators` field to the loan object with the same structure as the dedicated endpoint above.

###### Attach/Detach Validation Rules

> [!IMPORTANT]
> * Attach and detach are **only allowed while the loan is in Submitted and Pending Approval status**
> * The same originator **cannot be attached twice** to the same loan
> * The same originator **cannot be detached twice** (returns 404 if mapping does not exist)
> * Only originators with `ACTIVE` status can be **attached** (no status restriction for detach)

##### Inline Originator Creation During Loan Application

Originators can be provided as part of the loan creation request (`POST /v1/loans`):

```json
{
  "...": "...",
  "originators": [
    {
      "id": 1,
      "externalId": "XYZ",
      "name": "PP Merchant",
      "originatorTypeId": 1,
      "channelTypeId": 2
    }
  ]
}
```

* `id` or `externalId` is mandatory for each entry
* If `id` is provided: attaches the existing originator (lookup by `id` takes priority over `externalId`)
* If only `externalId` is provided:
  
  
  
  
  
  * Attaches the existing originator if found
  * Creates a new originator and attaches it (only when `enable-originator-creation-during-loan-application` is `true`)
  * Returns **403** if originator is not found and creation is not enabled
* `name`, `originatorTypeId`, `channelTypeId` are optional, used only when creating a new entry
* Newly created originators are automatically assigned `ACTIVE` status
* Duplicate originators within the same request are silently skipped

#### Business Events Integration

Originator details are automatically included in all loan and loan transaction external business events.

An `OriginatorDetailsV1` Avro record is added as an optional `originators` field (list) to:

* `LoanAccountDataV1.avsc` — all loan-centric events
* `LoanTransactionDataV1.avsc` — all loan transaction-centric events

```json
{
  "name": "OriginatorDetailsV1",
  "fields": [
    {"name": "id", "type": ["null", "long"]},
    {"name": "externalId", "type": ["null", "string"]},
    {"name": "name", "type": ["null", "string"]},
    {"name": "status", "type": ["null", "string"]},
    {"name": "originatorType", "type": ["null", "CodeValueDataV1"]},
    {"name": "channelType", "type": ["null", "CodeValueDataV1"]}
  ]
}
```

The field is **optional with default `null`**, preserving backward compatibility for existing event consumers.

On any loan or loan transaction event publication, the enricher fetches originator mappings for the loan, builds the `originators` list from the registry, and attaches it to the event payload.

#### Security and Permissions

| Permission | Description |
| --- | --- |
| `CREATE_LOAN_ORIGINATOR` | Create originator records |
| `READ_LOAN_ORIGINATOR` | View originator registry records and template data |
| `READ_LOAN` | View loan-originator associations (`GET /v1/loans/…​/originators`) |
| `UPDATE_LOAN_ORIGINATOR` | Modify originator records |
| `DELETE_LOAN_ORIGINATOR` | Delete originator records (only if not mapped to loans) |
| `ATTACH_LOAN_ORIGINATOR` | Attach an originator to a loan |
| `DETACH_LOAN_ORIGINATOR` | Detach an originator from a loan |

#### Reporting

Originator external IDs are included in the following stretchy reports:

* **Transaction Summary Report**
* **Trial Balance Report**

Report queries join `m_loan_originator_mapping` and `m_loan_originator` via a CTE. Multiple originators per loan are aggregated into a comma-separated string (`STRING_AGG` on PostgreSQL, `GROUP_CONCAT` on MySQL). The resulting column is `originator_external_ids`. Loans without originators have `NULL` in this column.

### Taxes on Loan Charges

> [!NOTE]
> Introduced in [FINERACT-1289](https://issues.apache.org/jira/browse/FINERACT-1289) â Tax component not working as expected: tax bifurcation in journal entries was not applied when a tax group was mapped to a loan charge.

#### Overview

When a loan charge (fee or penalty) is linked to a tax group, the system must produce separate journal entry lines for the base charge amount and the tax portion. Prior to this fix, the tax bifurcation was silently skipped and the full charge amount was posted as a single income entry, causing incorrect GL balances and tax liability omissions.

This fix ensures that every time a loan charge amount is set or recalculated, any configured tax group is evaluated, the tax split is computed per tax component, and both the net charge amount and the tax liability are recorded as distinct journal entries under both accrual-based and cash-based accounting modes.

##### Benefits

* Tax liability GL accounts are credited correctly when a taxed charge is collected.
* Income accounts reflect the net-of-tax charge amount rather than the gross amount.
* Per-component tax breakdowns are persisted, enabling audit trails and reporting.
* Both accrual and cash accounting modes handle tax bifurcation consistently.

#### Design

##### Key Components

| Component | Module | Purpose |
| --- | --- | --- |
| `LoanChargeTaxDetails` | `fineract-loan` | JPA entity (`m_loan_charge_tax_details`) storing the computed tax amount per `TaxComponent` for a single `LoanCharge`. |
| `ChargeTaxApplicationService` / `ChargeTaxApplicationServiceImpl` | `fineract-tax` | Computes the per-component tax split from a `TaxGroup`, a base amount, and an effective date. |
| `LoanChargeService` | `fineract-loan` | Calls `applyTaxIfConfigured()` after every charge amount mutation (set, update, recalculate) to keep tax details in sync. |
| `ChargeTaxPaymentDTO` | `fineract-provider` | Carries per-component tax payment data (charge ID, credit GL account ID, amount, penalty flag) from the loan transaction to the accounting layer. |
| `LoanCommonAccountingHelper` | `fineract-provider` | Shared helper that filters tax payments by type (fee/penalty), computes net charge amounts, and creates credit/debit journal entries for tax liability accounts. |
| `AccrualBasedAccountingProcessorForLoan` | `fineract-provider` | Extended to split fee and penalty journal entries into net income and tax liability entries when tax payments are present. |
| `CashBasedAccountingProcessorForLoan` | `fineract-provider` | Extended with the same tax bifurcation logic for cash-basis accounting. |

##### Data Model

Two schema changes are introduced by migration `1035_add_tax_to_loan_charge.xml`.

```sql
-- Column added to m_loan_charge to store the total tax amount for the charge
ALTER TABLE m_loan_charge
    ADD COLUMN tax_amount DECIMAL(19,6) NULL;

-- New table storing the per-component tax breakdown for each loan charge
CREATE TABLE m_loan_charge_tax_details (
    id              BIGINT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    loan_charge_id  BIGINT          NOT NULL,  -- FK â m_loan_charge.id
    tax_component_id BIGINT         NOT NULL,  -- FK â m_tax_component.id
    amount          DECIMAL(19,6)   NOT NULL
);
```

##### Accounting Impact

When a loan transaction pays a charge that has associated tax, the journal entries are split between the net charge amount and the tax liability.

###### Accrual-Based Accounting â Fee Payment

| Side | Account | Amount |
| --- | --- | --- |
| DR | Fees Receivable | Full fee amount (including tax) |
| CR | Income from Fees | Net fee amount (fee minus tax) |
| CR | Tax Liability (per component) | Tax amount |

###### Accrual-Based Accounting â Fee Reversal

| Side | Account | Amount |
| --- | --- | --- |
| CR | Fees Receivable | Full fee amount (including tax) |
| DR | Income from Fees | Net fee amount |
| DR | Tax Liability (per component) | Tax amount |

The same split applies to penalty charges using the penalty income and receivable accounts. Cash-based accounting follows the same debit/credit rules without the receivable leg.

If no tax group is configured on the charge, or the computed tax is zero, the existing single-entry behaviour is preserved.

#### Configuration

##### Prerequisites

1. Create one or more **Tax Components** (Administration â Tax Configuration â Tax Components) with the applicable percentage rate.
2. Create a **Tax Group** that references the tax components.
3. On the **Charge product**, assign the tax group under the *Tax Group* field.
4. Add the charge to a **Loan Product** that has either **Periodic Accrual** or **Cash-Based** accounting enabled.

##### Validation Rules

* Tax is computed at the time the charge amount is set or updated; a later change to the charge amount triggers recomputation.
* The effective date for tax rate lookup defaults to the charge submission date, falling back to the current business date when the submission date is absent.
* If the tax group yields a zero total tax (e.g., all components have 0% rate on the effective date), no tax entries are created and the charge behaves as untaxed.

#### Usage Example

1. Configure a tax component "VAT 16%" and a tax group "Standard VAT".
2. Create a flat loan fee of 1,000 and link it to the "Standard VAT" group.
3. Add the fee to a loan product with periodic accrual accounting.
4. After disbursement, the fee appears with `amount = 1,000` and `tax_amount = 160`.
5. When the borrower repays the charge the system posts:
  
  
  
  
  
  * DR Fees Receivable 1,000
  * CR Income from Fees 840
  * CR Tax Liability 160

#### Template API Filtering

The charge template API is enhanced to support filtered responses for charge creation.

Previously, the template endpoint returned every possible configuration option regardless of applicability. This behavior remains unchanged when no filter parameters are provided.

With this enhancement, the API supports hierarchical filtering of template options to reduce irrelevant configuration values for Working Capital Loan charge products.

##### Filtering Levels

Filtering is applied in the following order:

1. `chargeAppliesTo`
  
  
  
  
  
  * filters and returns only applicable `chargeTimeType`s
2. `chargeTimeType`
  
  
  
  
  
  * filters and returns only applicable `chargeCalculationType`s

Each filtering level depends on the previous level being provided.

##### chargeAppliesTo Filter

A new query parameter is introduced:

```http
GET /charges/template?chargeAppliesTo=<value>
```

When `chargeAppliesTo` is specified, the API returns only the template fields and dropdown options applicable to the selected entity type.

Supported values include:

* `Working Capital Loan`

##### chargeTimeType Filter

An additional filtering level is available when `chargeAppliesTo` is also provided:

```http
GET /charges/template?chargeAppliesTo=<value>&chargeTimeType=<value>
```

Supported values for WCP Loans:

* `Disbursement` — returns `Flat` and `% Amount`
* `Specified due date` — returns `Flat`

The API response filters the available `chargeCalculationType` options based on the selected charge time type.

When only `chargeAppliesTo` is provided, `chargeCalculationTypeOptions` contains the union across every supported charge time type (`Flat` and `% Amount` for WCP Loans), and `chargePaymetModeOptions` contains `Regular` only.

#### Backward Compatibility

If no query parameters are provided, the template API continues to return all available options to preserve legacy behavior.

include::working-capital-payment-allocation.adoc
:leveloffset: +1