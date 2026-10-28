---
source_url: https://fineract.apache.org/docs/1.17.0-SNAPSHOT#_working_capital_loan_projected_amortization_schedule
title: "Working Capital Loan â Projected Amortization Schedule"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/develop
---

## Working Capital Loan â Projected Amortization Schedule

### Overview

Dynamically updated amortization schedule for Working Capital (WC) Loans â zero-interest, discount/fee-based products with flexible, sales-based repayments. Uses EIR methodology for discount fee income recognition, deferral, and NPV calculation.

Each payment period is exactly **one day**: period `N` date = `expectedDisbursementDate + N days`.

### Goal

To design and implement a Working Capital Loan product with an Effective Interest Rate (EIR)-based calculation, enabling accurate discount fee income recognition, regulatory compliance, and flexible repayment structures.

The objective includes building a loan framework capable of:

* Supporting discount/fees-based working capital financing
* Accurately calculating and amortizing loans using EIR methodology, ensuring transparent cost of credit and compliance with accounting and regulatory standards
* Supporting excess payments, fewer payments, and no-payment calculation scenarios without impacting financial accuracy

### Configuration at Loan Product Level

#### Product Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | VARCHAR(100) | Yes | Product name (unique) |
| `shortName` | VARCHAR(4) | Yes | Product short code (unique) |
| `externalId` | VARCHAR(100) | No | External identifier. Must be unique when provided. |
| `description` | VARCHAR(500) | No | Product description |
| `fundId` | BIGINT | No | Fund reference for the product |
| `startDate` | DATE | No | Product start date |
| `closeDate` | DATE | No | Product close date. If supplied with `startDate`, it must be after `startDate`. |
| `currencyCode` | VARCHAR(3) | Yes | ISO currency code |
| `digitsAfterDecimal` | SMALLINT | Yes | Decimal places for currency. Allowed range: 0-6. |
| `inMultiplesOf` | INT | Yes | Currency multiple. Must be zero or greater. |
| `principal` | DECIMAL(19,6) | Yes | Default proposed principal amount. Must be positive. |
| `periodPaymentRate` | DECIMAL(19,6) | Yes | Percentage rate applied to Total Payment Value (for example, `18` = 18%). Must be zero or greater. |
| `npvDayCount` | INT | Yes | Day-count convention for NPV calculation. Must be greater than zero. |
| `amortizationType` | ENUM | Yes | Amortization type: `EIR` (discount fee earned as the effective rate accrues on the balance) or `FLAT` (discount fee earned as a fixed share of every payment, see FLAT amortization). A loan snapshots the product’s value at creation; changing the product afterwards does not affect existing loans. |
| `repaymentEvery` | INT | Yes | Repayment interval count |
| `repaymentFrequencyType` | ENUM | Yes | Repayment frequency type: `DAYS`, `WEEKS`, `MONTHS`, or `YEARS`. |
| `discount` | DECIMAL(19,6) | No | Default discount fee amount. Must be zero or greater when provided. |
| `minPrincipal` / `maxPrincipal` | DECIMAL(19,6) | No | Principal range constraints. `minPrincipal` must be less than or equal to `maxPrincipal`, and `principal` must be within the supplied range. |
| `minPeriodPaymentRate` / `maxPeriodPaymentRate` | DECIMAL(19,6) | No | Period payment rate range constraints. Minimum must be less than or equal to maximum, and `periodPaymentRate` must be within the supplied range. |
| `delinquencyBucketId` | BIGINT | No | Delinquency bucket classification |
| `delinquencyGraceDays` | INT | No | Grace days before delinquency (default: 0) |
| `delinquencyStartType` | ENUM | No | Delinquency start type: `LOAN_CREATION` or `DISBURSEMENT`. |
| `breachId` | BIGINT | No | Breach classification reference |
| `nearBreachId` | BIGINT | No | Near-breach classification reference. Can only be set when `breachId` is provided and must be valid for the selected breach. |
| `paymentAllocation` | ARRAY | Yes | Payment allocation rules for the product. Required on create and validated per transaction type. |
| `allowAttributeOverrides` | OBJECT | No | Optional object that controls which product settings may be overridden at loan level. See Configurable Attributes below. |
| `accountingRule` | ENUM | Yes | Product accounting rule: `NONE` or `CASH_BASED`. `CASH_BASED` requires accounting mappings to be supplied. |

#### Configurable Attributes (Loan-Level Overrides)

These flags control whether the corresponding field can be overridden at the individual loan level:

| Attribute | Description |
| --- | --- |
| `discountDefault` | Allow override of origination fee / discount at loan level |
| `periodPaymentFrequency` | Allow override of repayment interval |
| `periodPaymentFrequencyType` | Allow override of repayment frequency type |
| `delinquencyBucketClassification` | Allow override of delinquency bucket |
| `breach` | Allow override of breach and near-breach classifications |

#### Payment Allocation Rules

Each product defines payment allocation rules per transaction type. Working Capital payment allocation supports only principal, fee, and penalty buckets, with due and in-advance variants:

* `DUE_PENALTY`
* `DUE_FEE`
* `DUE_PRINCIPAL`
* `IN_ADVANCE_PENALTY`
* `IN_ADVANCE_FEE`
* `IN_ADVANCE_PRINCIPAL`

> [!NOTE]
> Working Capital loans have no nominal interest rate. Revenue is generated through discount fee amortization using EIR methodology, tracked through `realizedIncomeFromDiscountFee` and `unrealizedIncomeFromDiscountFee` on the loan balance.

### Origination Fee (Discount) Treatment

The origination fee â referred to as "discount" in the product and loan configuration â is the upfront fee that represents the cost of credit. It is the difference between what the borrower must repay (Total Payment Value) and the net amount disbursed.

#### Lifecycle of the Discount

| Stage | Behavior |
| --- | --- |
| **Create** | Discount amount entered (optional). Defaults to product-level value if not specified. |
| **Approve** | Optional `discountAmount` can override the proposed discount when product configuration allows it. The approved discount cannot exceed the created discount or product default. |
| **Disburse** | Optional `discountAmount` can override the approved discount when product configuration allows it. The disbursed discount cannot exceed the approved discount or product default. A positive discount creates a `DISCOUNT_FEE` transaction related to the disbursement. |
| **Post-Disbursement** | A discount fee can be added once through the discount endpoint, only on the disbursement business date and only when a discount fee transaction is not already related to the disbursement. Discount fee adjustments are supported against an active discount fee transaction up to the remaining discount amount. |

#### Deferred Income at Disbursement

At disbursement, the origination fee becomes the initial **deferred balance** (unrealized income). This amount is progressively recognized as income over the loan lifecycle through the EIR amortization model:

* `principal` = disbursed amount + discount
* `principalOutstanding` = `principal - principalPaid`
* `totalDiscountFee` = discount amount
* `unrealizedIncomeFromDiscountFee` = `totalDiscountFee - realizedIncomeFromDiscountFee`
* `realizedIncomeFromDiscountFee` = 0 (nothing recognized yet)

As repayments are received, the fee earned on the money collected determines how much discount fee income is eligible to move from `unrealizedIncomeFromDiscountFee` to `realizedIncomeFromDiscountFee`.

### Lifecycle

| Stage | Behavior |
| --- | --- |
| **Approve** | Generates a projected schedule from approved loan parameters and expected disbursement date. |
| **Undo approval** | Deletes the approval-time schedule. The loan is back where submission left it, with no projection until it is approved again: submission and modification never write one, so nothing would keep an interim projection in sync with later changes. |
| **Disburse** | Regenerates the schedule using the actual disbursement amount and actual disbursement date. |
| **Undo disbursal** | Projects the schedule again from the approved values, exactly as approval does, once the loan is back on the clean slate of a never disbursed approved loan: the breach schedule, the delinquency range schedule and its tags, the breach, delinquency and near breach actions are deleted, the period payment rate changes are reversed on the business date (their history stays readable, like the transactions undone with them), the loan charges are deactivated and the balance is replaced by a fresh one. A later disbursement anchors its schedules on its own date. |
| **Repayment** | `applyPayment()` records the repayment against the calculated schedule date and rebuilds the schedule. Calculates actual amortization and income modification for applied payment rows. |
| **Period Payment Rate Change** | Records the change’s effective date and rate, and rebuilds; the walk switches to the new rate on the day it reaches that date, re-solving from the balance and unearned fee it is carrying. The effective date may be in the future, in which case the schedule carries the change immediately while the rate stored on the loan is switched over by the `WC_PERIOD_PAYMENT_RATE_EFFECTIVE_DATE` COB step once that date arrives. A date past the end of the schedule takes effect on its last day; a date at or before the first instalment takes effect on the first day, so two changes a day apart either side of it can land on the same day â the one booked later governs it. |

#### State Transitions

| Command | From State | To State | Key Validations |
| --- | --- | --- | --- |
| `approve` | Submitted and Pending Approval | Approved | Approval date not future, not before submitted date; expected disbursement date not before approval date; approved amount ⇐ proposed principal; discount ⇐ created discount/product default |
| `reject` | Submitted and Pending Approval | Rejected | Rejection date not future, not before submitted date |
| `undoapproval` | Approved | Submitted and Pending Approval | Clears approval data and deletes the approval-time schedule; the loan has no projection again until it is approved |
| `disburse` | Approved | Active | Disbursement date not future, not before submitted/approval date, and valid for office calendar; amount > 0 and ⇐ approved principal; client must be active |
| `undodisbursal` | Active | Approved | Allowed only when there are no active monetary transactions other than disbursement, discount fee, discount fee amortization, and discount fee adjustment; reverses transactions, resets balance, deletes the breach and delinquency schedules and every breach, delinquency and near breach action, reverses every rate change still in force, and re-projects the amortization schedule from the approved values |
| repayment transaction | Active or Overpaid | Active, Overpaid, or Closed (Obligations Met) | Transaction date not future and not before disbursement date; amount > 0; payment is allocated and the schedule is rebuilt |
| credit balance refund transaction | Overpaid | Overpaid or Closed (Obligations Met) | Transaction date not future, not before disbursement date, and not backdated before business date; amount > 0 and ⇐ available overpayment |
| goodwill credit transaction | Active, Overpaid, or Closed (Obligations Met) | Active, Overpaid, or Closed (Obligations Met) | Transaction date not future and not before disbursement date; amount > 0; allocation and accounting follow repayment-like processing |

### Input Parameters

The amortization schedule model is calculated from these loan-level parameters:

| Parameter | Type | Description |
| --- | --- | --- |
| `discountFeeAmount` | Money | Upfront discount fee. Amortized over lifecycle. Older stored model JSON may use `originationFeeAmount`. |
| `netDisbursementAmount` | Money | Principal disbursed. Must be positive. |
| `totalPaymentVolume` | Money | Merchant’s TPV. |
| `periodPaymentRate` | BigDecimal | Percentage rate applied to TPV (for example, `18` = 18%). |
| `npvDayCount` | Integer | Day-count convention (e.g., 360). Must be positive. |
| `expectedDisbursementDate` | Date | Loan start date. |

### Formulas

```java
expectedPaymentAmount = round((TPV Ã periodPaymentRate / 100) / npvDayCount)   // floored at one minor unit when positive
grossPayable          = netDisbursement + discountFee
originalPaymentNumber = roundUp(grossPayable / expectedPaymentAmount)
finalPaymentAmount    = grossPayable - expectedPaymentAmount Ã (originalPaymentNumber - 1)
EIR                   = IRR([-netDisbursement, expectedPaymentAmount Ã (n-1), finalPaymentAmount])
paymentsLeft          = max(0, dayWithinCurrentRate - appliedPaymentCount)
discountFactor        = 1 / (1 + EIR) ^ paymentsLeft
npvSource             = actualPayment (if paid) or 0 (if the day elapsed unpaid) or billedInstalment
npvValue              = max(0, npvSource Ã discountFactor)   // row 0: -netDisbursementAmount (unclamped)
```

The rate is solved against the cash flow the borrower actually pays, closing remainder
included, rather than against a uniform annuity. That is what makes the recursion below
close on exactly zero on the last day, with its daily accruals summing to exactly the
discount fee â the property the whole schedule rests on.

#### FLAT amortization

With `amortizationType = FLAT` the schedule keeps the same payment grid, term and final payment, but the discount fee is earned as a fixed share of every payment instead of accruing on the balance:

```java
ratio                  = payableDiscountFee / initialLoanBalance
payableDiscountFee     = discountFee â discountFeeAdjustments
initialLoanBalance     = netDisbursement + discountFee â discountFeeAdjustments
expectedAmortization   = ratio Ã expectedPayment          // per period
actualAmortization     = ratio Ã actualPayment            // per repayment, cumulative rounded once
balance[i]             = balance[i-1] â payment Ã (1 â ratio)
```

Example: 9000 disbursed with a 1000 discount fee gives a ratio of `1000 / 10000 = 10%`; a repayment of 50 earns 5.00 of discount fee. Because the ratio is applied to what is actually paid, a fully paid loan has earned exactly its payable discount fee. A discount fee adjustment changes the ratio and restates the amortization already earned (the COB posts the difference as a discount fee amortization adjustment); a period payment rate change resizes the payments and the term but leaves the ratio unchanged.

No effective interest rate is solved for a FLAT schedule: `effectiveInterestRate` on the schedule and `calculatedAnnualEir` on the loan are `null`, and the discount factor is 1 for every period. The structural checks of the "EIR not calculable" validation still apply to a FLAT loan (a positive daily payment, a term within the calculable cap); when they fail, a FLAT loan is rejected with `error.msg.workingcapitalloan.schedule.not.calculable` / "unable to calculate a valid amortization schedule" instead of the EIR-worded error.

#### Stored Values at Loan Account Level

After EIR calculation, the following values are persisted:

* **Period Payment Amount** â constant daily expected payment
* **Total Days** â loan term in days
* **Calculated Annual EIR** â effective interest rate compounded over `npvDayCount` periods and rounded to six decimals, stored on the amortization schedule. The base schedule’s daily rate is back-calculated from it; a payment rate change does not restate it, and the schedule re-solves its own rate from the day the change takes effect

#### Stored Values per Repayment

For each actual repayment transaction:

* **Payment Amount** â actual cash received
* **Actual Amortization (Income)** â fee income recognized for this payment
* **Income Modification** â difference between actual and expected amortization

### Schedule Fields

| Field | Formula / Description |
| --- | --- |
| `paymentNo` | 1-based. Row 0 = disbursement. |
| `paymentDate` | `expectedDisbursementDate + paymentNo` days. |
| `expectedPaymentAmount` | The daily instalment in force, capped at the balance the day has to close. Row 0: `-netDisbursementAmount`. |
| `discountFactor` | `1/(1+EIR)^paymentsLeft`. Row 0 and paid periods: 1.0. Model only â not returned by the API. |
| `npvValue` | `max(0, npvSource Ã DF)`. Row 0: `-netDisbursementAmount`. Model only â not returned by the API. |
| `balance` | `balance[i-1]Ã(1+EIR) - billedInstalment[i]`. Row 0: `+netDisbursementAmount`. Serialized as `expectedBalance`. |
| `expectedAmortizationAmount` | `round(aggregateAccrual[i]) - round(aggregateAccrual[i-1])`, where the accrual is `balance[i-1] Ã EIR`. Row 0: null. |
| `actualPaymentAmount` | Actual cash paid. Null if no payment. |
| `actualAmortizationAmount` | `round(feeEarned[i]) - round(feeEarned[i-1])`, where `feeEarned` is the plan curve read at the money collected. Null for a day with no record; zero for a day that elapsed unpaid. |
| `incomeModification` | Positive-payment rows: `actualAmort - expectedAmort`. Otherwise null. Model only â not returned by the API. |
| `deferredBalance` | `discountFee - round(aggregateAccrual[i])`, closing on exactly 0. Row 0: `discountFeeAmount`. Serialized as `expectedDiscountFeeBalance`; the actual-driven counterpart is `actualDiscountFeeBalance`. |

#### Disbursement Row (paymentNo = 0)

| `expectedPaymentAmount` | `-netDisbursementAmount` |
| --- | --- |
| `discountFactor` | 1.0 |
| `npvValue` | `-netDisbursementAmount` |
| `balance` | `+netDisbursementAmount` |
| `deferredBalance` | `discountFeeAmount` |
| all other nullable fields | null |

#### Days Past the Term

There are none, in the sense of a separate kind of row. The walk runs until the loan is
square, so a borrower who has fallen behind simply gets more days â same instalment,
balance still declining, fee still being earned â and one who has paid ahead gets fewer.
A day past the original term is an ordinary day of the schedule and fills in the same
columns as any other.

### EIR-Based Income Recognition

#### Fee Earned Is a Function of Money Collected

The discount fee is accrued at disbursement as deferred revenue and amortized as the money
comes in, so what governs recognition is how much has been collected, never how much time
has passed. The fee recognized is read off the plan’s own declining-balance recursion at
the point the money collected has reached â the plan cursor described in the Calculation
Algorithm above.

This mechanism means:

* A payment equal to the instalment recognizes exactly one day’s worth of fee
* A payment larger than the instalment recognizes proportionally more, and takes a day off the end of the schedule â that day was already covered
* A payment smaller than the instalment recognizes proportionally less
* No payment on a given day means no income is recognized for that day, and the schedule runs a day longer
* Repaying the whole payable recognizes the whole fee, however few days it took; paying more than the payable recognizes nothing further, because there is nothing left to earn

#### Income Modification

The `incomeModification` field tracks the difference between what was actually amortized and what was expected:

* **Paid periods**: `incomeModification = actualAmortization - expectedAmortization`
  
  
  
  
  
  * Positive value = more income recognized than expected (excess payment)
  * Negative value = less income recognized than expected (underpayment)
* **Unpaid periods**: no actual amortization is calculated and `incomeModification` is null

#### Deferred Balance Tracking

The deferred balance represents the remaining unrecognized origination fee:

* At disbursement: `deferredBalance = discountFeeAmount`
* After each payment: `deferredBalance = discountFee - cumulativeActualAmortization`
* At loan maturity (fully paid): `deferredBalance = 0`

### Calculation Algorithm

One forward walk over the days, carrying two cursors. The **calendar cursor** takes one step
per day; the **plan cursor** takes one step per instalment of the plan as written, and runs
ahead of the calendar exactly as far as the borrower has paid ahead.

Per day:

1. **Aggregate payments by date** (same-date payments summed, repayments normalized to a valid schedule date). Every elapsed date with nothing against it is seeded with a nil payment, so a missed instalment is recorded rather than absent.
2. **Accrue and bill**: `grown = balance[n-1] Ã (1 + EIR)`, `billedInstalment[n] = min(expectedPaymentAmount, grown)`, `balance[n] = grown - billedInstalment[n]`. No day can bill more than the balance it has to close, and that cap is also what closes the loan: on the day the balance falls below an instalment the day bills the balance, and nothing is left. There is no separate closing amount â `finalPaymentAmount` sizes the cash flow the rate is solved from and is reported as the contractual final instalment, but the schedule bills what is owed, which is the same figure on a loan paid to plan and the right one on a loan a repayment has restated.
3. **Advance the plan cursor** until it has billed at least as much as has been collected, then read back to the amount collected within the step it landed in. That reading is the fee the money received has earned â recognition follows money in, not time passed, so paying the whole payable on day one earns the whole fee on day one.
4. **Normalize both tracks**: `aggNorm[n] = round(aggHp[n])`, and the day reports `aggNorm[n] - aggNorm[n-1]`. The running total is rounded, never the day, which is what stops the fee drifting from itself over a few hundred days.
5. **Restate from reality** on a settled day â one that was paid, or that elapsed unpaid: the balance carried forward becomes what the borrower really owes, and the expected fee total is re-seeded from the actual one. Days that have not come round yet keep the plan they were written with.
6. **Stop** once the balance has closed and the schedule has caught up with the date it is being calculated to â and never before today, or before any day a principal adjustment falls on, since a payment or a rate change dated there needs a row to land on. Stop early only if the instalment cannot cover the day’s accrual, because then no number of further days would close the balance.

#### Rebuild Flow

Every schedule-changing operation triggers a full rebuild, and the rebuild is the walk:
aggregate payments → walk the days → map each day to a row → overlay principal
adjustments. Nothing is settled onto a final period afterwards, and nothing is trimmed off
the end: the schedule ends where the loan closes.

### Loan Balance

The `m_wc_loan_balance` table maintains a running balance snapshot for each loan. Outstanding amounts are derived from stored due and paid amounts:

| Field | Description |
| --- | --- |
| `principal` | Total principal expected for repayment. Initialized at disbursement as `disbursedAmount + discount`. |
| `principalPaid` | Cumulative principal repaid. |
| `principalOutstanding` | Derived as `principal - principalPaid`. |
| `fee` / `feePaid` / `feeOutstanding` | Fee amount, cumulative fee paid, and derived outstanding fee amount. |
| `penalty` / `penaltyPaid` / `penaltyOutstanding` | Penalty amount, cumulative penalty paid, and derived outstanding penalty amount. |
| `realizedIncomeFromDiscountFee` | Discount fee income that has been recognized (amortized). Increases as repayments earn fee off the plan curve and COB posts discount fee amortization. |
| `unrealizedIncomeFromDiscountFee` | Derived as `totalDiscountFee - realizedIncomeFromDiscountFee`. |
| `overpaymentAmount` | Amount paid beyond total outstanding principal, fee, and penalty amounts. Used for credit balance refunds. |
| `totalDisbursement` | Stored total disbursement field. Current balance update flow initializes the balance from the disbursement transaction amount and discount. |
| `totalDiscountFee` | Total discount fee attached to the loan. |
| `totalDiscountFeeAdjustment` | Total discount fee adjustment amount posted against discount fee transactions. |

#### Balance Invariants

* `principalOutstanding >= 0`
* `principalPaid >= 0`
* `feeOutstanding >= 0`
* `penaltyOutstanding >= 0`
* `realizedIncomeFromDiscountFee >= 0`
* `unrealizedIncomeFromDiscountFee >= 0`
* `realizedIncomeFromDiscountFee + unrealizedIncomeFromDiscountFee = totalDiscountFee`

### COB (Close of Business) Processing

The Working Capital COB job processes WC loans daily during the Close of Business batch run.

#### Job Configuration

* Job name: `WORKING_CAPITAL_LOAN_CLOSE_OF_BUSINESS`
* Display name: "Working Capital Loan COB"
* Coexists with the standard `LOAN_CLOSE_OF_BUSINESS` job without interference

#### Processing Behavior

* Updates `lastClosedBusinessDate` to `businessDate - 1` for each eligible loan
* Increments loan `version` for each day processed
* Processes loans one day at a time when catching up over skipped dates
* Releases all account locks after completion

#### Status Eligibility

| Status | Processed by COB? |
| --- | --- |
| Submitted and Pending Approval | Yes |
| Approved | Yes |
| Active | Yes |
| Transfer in Progress | Yes |
| Transfer on Hold | Yes |
| Overpaid | No |
| Closed (Obligations Met) | No |
| Rejected | No |

#### Business Steps

The following business steps are executed during COB for each eligible loan:

| Step Order | Step Name | Description |
| --- | --- | --- |
| 2 | `WC_MISSED_PAYMENT_ACKNOWLEDGEMENT` | Advances the projected schedule to the business date, so instalment dates that passed with no payment against them report a nil payment instead of being left blank. Affects the actual columns only â the expected projection is restated when a payment lands, not when a date elapses. Runs ahead of the steps that read the schedule. |
| 3 | `WC_DELINQUENCY_RANGE_SCHEDULE` | Generates and evaluates delinquency range periods based on product configuration. |
| 4 | `WC_LOAN_DELINQUENCY_CLASSIFICATION` | Assigns or lifts delinquency range tags based on the configured bucket ranges. |
| 5 | `WC_BREACH_SCHEDULE` | Generates and evaluates breach schedule periods. |
| 6 | `WC_NEAR_BREACH_EVALUATION` | Evaluates near-breach conditions against the configured breach. |
| 7 | `WC_DISCOUNT_FEE_AMORTIZATION` | Posts newly recognized discount fee amortization from the projected schedule. |
| 8 | `WC_CHARGE_ACCRUAL` | Accrues charges that have fallen due on the loan. |
| 9 | `WC_PERIOD_PAYMENT_RATE_EFFECTIVE_DATE` | Brings the period payment rate stored on the loan up to date with its rate-change history. A rate change may be booked with a future effective date, and the stored rate is otherwise only refreshed when a change is submitted, so without this step the loan keeps reporting the old rate after the effective date arrives â the projected schedule already carries the new segment, so it is the summary on the loan that would drift. Resolves the rate in force as at the business date; does nothing when the loan has no rate changes or the rate has not moved. |

#### Inline COB

WC loans also support inline COB processing for individual loans, with the same behavior as batch COB. This is useful for immediate processing without waiting for the scheduled batch run.

#### COB Catch-Up

When the system has skipped business dates (e.g., after maintenance), the COB catch-up mechanism processes each missed day sequentially until `lastClosedBusinessDate` reaches `currentBusinessDate - 1`.

### Special Handling

#### Excess Payments

When actual payment exceeds expected payment for a period:

* The excess is distributed backward from the last period, reducing forecast payments
* More origination fee income is recognized (proportional to payment ratio)
* Loan may mature earlier than originally projected

#### Shortfall (Underpayment)

When actual payment is less than expected:

* Less income is recognized for the period
* The schedule runs longer: the balance the day left standing still has to be closed, so the walk keeps producing days until it is

#### No Payment

When no payment is received on a given day:

* No income is recognized (`actualAmortizationAmount = null`)
* `incomeModification = null`
* Deferred balance remains unchanged

#### Repayment Rate Modification

The repayment percentage can be modified during the loan lifecycle:

* Affects expected period payment recalculation
* Triggers full amortization schedule rebuild
* Does not retroactively change already-recognized income

#### Re-Age

Re-aging works only for the delinquency range schedule:

* Does not impact the amortization schedule or income recognition
* Period payment amount is unchanged

#### Payment Holidays

Payment holidays only affect the delinquency range schedules:

* Amortization schedule and income recognition are not directly impacted

#### Charge-Off

Charge-off support is not fully implemented for Working Capital loan accounting. Discount fee amortization supports a charged-off posting path internally, but standard charge-off transaction flows are not documented here as generally available.

#### Write-Off

Write-off support is not documented as a generally available Working Capital loan command in the current API surface.

#### Credit Balance Refund (CBR)

Supported when the loan has a credit balance (overpayment beyond principal). The excess amount can be refunded to the borrower.

### Accounting Entries

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Disbursement | Loan Portfolio (Asset) | Fund Source (Asset) |
| Repayment | Fund Source (Asset) | Loan Portfolio (Asset) |
| Discount Fee Amortization | Unrealized Income / Deferred Income (Liability) | Income from Discount Fee (Income) |

> [!NOTE]
> Working Capital loans do not generate interest-related journal entries. All revenue recognition flows through discount fee amortization via `realizedIncomeFromDiscountFee` and `unrealizedIncomeFromDiscountFee`. The actual GL account IDs are configured at the loan product level.

### API Endpoints

#### POST /v1/working-capital-loan-products

Creates a new Working Capital loan product with EIR amortization configuration.

#### POST /v1/working-capital-loans

Creates a new Working Capital loan application. Required fields include: `productId`, `clientId`, `principalAmount`, `totalPaymentVolume`, `periodPaymentRate`, `submittedOnDate`, and `expectedDisbursementDate`.

#### POST /v1/working-capital-loans/{loanId}?command=approve

Approves a submitted loan application. Required fields include `approvedOnDate` and `expectedDisbursementDate`; optional overrides include `approvedLoanAmount` and `discountAmount`.

#### POST /v1/working-capital-loans/{loanId}?command=disburse

Disburses an approved loan. Required: `actualDisbursementDate`, `transactionAmount`. Triggers amortization schedule generation.

#### POST /v1/working-capital-loans/{loanId}/transactions?command=repayment

Creates a repayment transaction. Required: `transactionDate`, `transactionAmount`.

#### POST /v1/working-capital-loans/{loanId}/transactions?command=creditBalanceRefund

Creates a credit balance refund transaction for an overpaid loan. Required: `transactionDate`, `transactionAmount`.

#### POST /v1/working-capital-loans/{loanId}/transactions?command=goodwillCredit

Creates a goodwill credit transaction. Required: `transactionDate`, `transactionAmount`.

#### POST /v1/working-capital-loans/{loanId}/transactions?command=discountFee

Creates a discount fee transaction related to a disbursement transaction.

#### POST /v1/working-capital-loans/{loanId}/transactions?command=discountFeeAdjustment

Creates a discount fee adjustment transaction related to an active discount fee transaction.

#### PUT /v1/working-capital-loans/{loanId}/discount

Updates the discount (origination fee) amount. Only allowed once after disbursement and only on the disbursement date. Request body uses `discountAmount` field. Also available via external ID: `PUT /v1/working-capital-loans/external-id/{externalId}/discount`.

#### PUT /v1/working-capital-loans/{loanId}/payment-rate

Updates `periodPaymentRate` for an active loan and rebuilds the schedule from the current business date. Also available via external ID: `PUT /v1/working-capital-loans/external-id/{externalId}/payment-rate`.

#### GET /v1/working-capital-loans/{loanId}/rate-changes

Retrieves recorded period payment rate changes for a loan. Also available via external ID: `GET /v1/working-capital-loans/external-id/{externalId}/rate-changes`.

#### GET /v1/working-capital-loans/{loanId}/amortization-schedule

Retrieves the projected amortization schedule for a Working Capital loan.

Example Request:

```
GET /fineract-provider/api/v1/working-capital-loans/1/amortization-schedule
```

Example Response (first 3 payments shown):

```json
{
  "discountFeeAmount": 1000.00,
  "netDisbursementAmount": 9000.00,
  "totalPaymentVolume": 100000.00,
  "periodPaymentRate": 18,
  "npvDayCount": 360,
  "expectedDisbursementDate": "2019-01-01",
  "expectedPaymentAmount": 50.00,
  "originalPaymentNumber": 200,
  "effectiveInterestRate": 0.001067814478737866,
  "payments": [
    {
      "paymentNo": 0,
      "paymentDate": "2019-01-01",
      "expectedPaymentAmount": -9000.00,
      "discountFactor": 1,
      "npvValue": -9000.00,
      "balance": 9000.00,
      "expectedAmortizationAmount": null,
      "actualPaymentAmount": null,
      "actualAmortizationAmount": null,
      "incomeModification": null,
      "deferredBalance": 1000.00
    },
    {
      "paymentNo": 1,
      "paymentDate": "2019-01-02",
      "expectedPaymentAmount": 50.00,
      "discountFactor": 0.998933324523691,
      "npvValue": 49.95,
      "balance": 8959.61,
      "expectedAmortizationAmount": 9.61,
      "actualPaymentAmount": null,
      "actualAmortizationAmount": null,
      "incomeModification": null,
      "deferredBalance": 1000.00
    },
    {
      "paymentNo": 2,
      "paymentDate": "2019-01-03",
      "expectedPaymentAmount": 50.00,
      "discountFactor": 0.9978677868439537,
      "npvValue": 49.89,
      "balance": 8919.18,
      "expectedAmortizationAmount": 9.57,
      "actualPaymentAmount": null,
      "actualAmortizationAmount": null,
      "incomeModification": null,
      "deferredBalance": 1000.00
    }
  ]
}
```

> [!NOTE]
> In the example above:
> * The discount fee of 1000.00 starts as the full `deferredBalance`
> * `expectedAmortizationAmount` starts at 9.61 on day 1 and **decreases daily** (9.57 on day 2), demonstrating the EIR front-loading effect
> * With no actual payments, `actualAmortizationAmount` and `incomeModification` are null
> * The `balance` decreases daily from 9000.00 to exactly 0.00 over the 200-day term, and `deferredBalance` reaches exactly 0.00 with it

### Business Events

#### Loan Lifecycle Events

| Event | Trigger |
| --- | --- |
| `LOAN_APPROVED` | Loan application approved |
| `LOAN_APPROVAL_UNDO` | Loan approval reversed |
| `LOAN_REJECTED` | Loan application rejected |
| `LOAN_DISBURSED` | Loan funds disbursed; amortization schedule generated |
| `LOAN_DISBURSAL_UNDO` | Disbursement reversed; amortization schedule regenerated |
| `LOAN_REPAID_IN_FULL` | Principal outstanding reaches zero |
| `LOAN_OVERPAID` | Repayment-like transaction creates an overpayment |
| `LOAN_CREDIT_BALANCE_REFUND_IN_FULL` | Credit balance refund clears the overpayment on an overpaid loan |

### Database

| Column | Type | Description |
| --- | --- | --- |
| `id` | BIGINT | PK, auto-increment. |
| `version` | INT | Optimistic lock. |
| `loan_id` | BIGINT | FK â `m_wc_loan`. Unique. |
| `json_model` | LONGTEXT (MySQL/MariaDB) / TEXT (PostgreSQL) | Serialized model (Gson). `@JsonExclude` on `MathContext`, `MonetaryCurrency`; restored via `forDeserialization()`. |
| `business_date` | DATE | Last generated/updated. |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | Audit. MySQL / PostgreSQL. |
| `json_model_version` | VARCHAR(10) | Current model version is `"4"`. |

### Transaction Types

Working Capital loans support the following transaction types:

| Transaction Type | Description |
| --- | --- |
| **Disbursement** | Initial funding of the loan. Triggers amortization schedule generation and deferred income initialization. |
| **Repayment** | Merchant payment applied to the loan. Earns fee off the plan curve and triggers a schedule rebuild. Payment allocation follows the product’s `paymentAllocation` rules. |
| **Discount Fee** | Sets the discount fee as a transaction related to the disbursement. |
| **Discount Fee Adjustment** | Reduces an active discount fee transaction and regenerates the schedule from the adjusted discount amount. |
| **Charge / Charge Adjustment** | Fee charges (e.g., NSF fees) added to the loan. Charge adjustments reverse or reduce charges. |
| **Goodwill Credit** | Credit applied to the loan as a gesture of goodwill. |
| **Charge-Off** | Writes off the loan as non-performing. Remaining unrealized income is charged off. |
| **Write-Off** | Writes off outstanding principal and unrealized income. |
| **Credit Balance Refund** | Refunds excess payment (credit balance) back to the borrower. |
| **Reversed Transactions** | Undo disbursal reverses disbursement-related transactions by marking them reversed. Triggers schedule rebuild and recalculate balances. |

### Constraints and Limitations

> [!IMPORTANT]
> Current limitations of the Working Capital amortization model:
> * **Flat amortization**: Defined in the enum (`WorkingCapitalAmortizationType.FLAT`) but not supported in the current implementation. Phase 2.
> * **Partial fee adjustments**: Only full fee adjustments are supported. Partial fee adjustments are planned for Phase 2.
> * **Partial discount fee adjustments**: Discount fee adjustment transactions can reduce an active discount fee up to the remaining discount amount.
> * **Chargeback**: Not yet implemented. Phase 2.
> * **No traditional repayment schedule**: WC loans have no fixed installments or maturity date like term loans. Repayments are sales-based.
> * **Transaction availability depends on status**: Repayments are limited to active/overpaid loans, credit balance refunds to overpaid loans, and goodwill credits to active/closed-obligations-met/overpaid loans.
> * **Single disbursement (business rule)**: While the schema and domain model support multiple disbursement detail rows (`List<WorkingCapitalLoanDisbursementDetails>`), the current business logic restricts WC loans to a single disbursement event.

### Appendix: TVM Functions

**RATE**: Newton-Raphson solving `pvÃ(1+r)^n + pmtÃ((1+r)^nâ1)/r = 0`. Initial guess: `2Ã(pmtÃn+pv)/(pvÃn)`, fallback 0.01. Tolerance 1E-10, max 100 iterations.

**Discount Factor**: `1/(1+eir)^days`. Returns 1.0 when days=0. Throws `IllegalArgumentException` for negative days. The model wraps this via `safeDiscountFactor()` which additionally returns 1.0 when the computed result is â¤ 0.

### Working Capital Loan â Discount Fee Transactions

#### Overview

Discount Fee transactions record the applied Working Capital Loan discount as a monetary transaction. The transaction is linked to the related disbursement and updates the loan balance and projected amortization schedule.

Discount product configuration and staged loan-level override rules are documented separately in `working-capital-discount.adoc`.

##### Purpose

The transaction layer ensures that the applied discount is represented as a loan transaction, linked to the disbursement that created it, and available for balance, amortization, accounting, and event processing.

##### Scope

The scope of this document includes:

* `DISCOUNT_FEE` transaction creation at disbursement and post-disbursement
* `DISCOUNT_FEE_ADJUSTMENT` transaction behavior
* Transaction relations and allocations
* Balance, schedule, accounting, reversal, and business event behavior
* API endpoints and validation rules

#### Discount Fee Transaction

##### Applicability

* Working Capital Loan only
* Loan must be ACTIVE for post-disbursement `discountFee`
* Loan must not be charged off. The Discount Fee is rejected even though it is dated on the disbursement date, which is never after the charge-off date: it would add principal that the charge-off has not written off. A Discount Fee Adjustment dated before the charge-off date is allowed, because it only reduces the discount and the loan is reprocessed to restate the charge-off’s final amortization.
* The related disbursement must not already have an active Discount Fee transaction
* The Discount Fee transaction is dated on the disbursement date. Post-disbursement `discountFee` can be run on a later business date and is then backdated to the disbursement date

##### Transaction Creation

A `DISCOUNT_FEE` transaction can be created in two ways:

* Automatically during disbursement when the resolved discount amount is greater than zero.
* Explicitly after disbursement using `POST /transactions?command=discountFee`, or by naming the disbursement in the path (`/transactions/{transactionId}` or `/transactions/external-id/{transactionExternalId}`), if no Discount Fee was created for the related disbursement.

Each Discount Fee transaction is linked to its disbursement transaction through `m_wc_loan_transaction_relation` with relation type `RELATED`.

##### Allocation

An allocation row is stored in `m_wc_loan_transaction_allocation`. The Discount Fee amount is allocated to the principal portion.

##### Balance and Schedule Impact

On Discount Fee creation:

* `loanProductRelatedDetails.discount` is set to the transaction amount.
* `totalDiscountFee` and principal balance are increased by the discount amount.
* Overpayment is reset to zero.
* The projected amortization schedule is regenerated using the updated discount and disbursement data.

##### Business Event

`WorkingCapitalLoanDiscountFeeTransactionBusinessEvent` is emitted after a successful `DISCOUNT_FEE` transaction is created. The event is emitted both for automatic disbursement-time Discount Fee creation and explicit post-disbursement `discountFee`.

The payload (`WorkingCapitalLoanTransactionDataV1`, shared by all Working Capital Loan transaction events) identifies the transaction by both `id` and `externalId`, and the owning loan by both `wcLoanId` and `externalLoanId`, so a consumer working with external ids does not have to resolve the loan separately.

#### Discount Fee Adjustment

A `DISCOUNT_FEE_ADJUSTMENT` transaction reduces the loan-level discount that was established by an existing, non-reversed `DISCOUNT_FEE` transaction.

##### Applicability

* Loan must be ACTIVE.
* The related Discount Fee transaction (`relatedResourceId`, `relatedExternalResourceId`, or the transaction in the path) must be an active, non-reversed `DISCOUNT_FEE` transaction.
* Multiple adjustments are allowed against the same Discount Fee transaction until the remaining adjustable amount reaches zero.

##### Transaction Behavior

On Discount Fee Adjustment:

* A separate `DISCOUNT_FEE_ADJUSTMENT` transaction is created.
* The adjustment is linked to the original Discount Fee transaction through a `RELATED` transaction relation.
* `loanProductRelatedDetails.discount` is reduced by the adjustment amount, with a floor of zero.
* `totalDiscountFeeAdjustment` is increased and principal balance is reduced by the adjustment amount.
* The projected amortization schedule is regenerated and prior actual repayments are re-applied.

##### Validation Rules

| Rule | Detail |
| --- | --- |
| Amount | Mandatory; must be greater than zero |
| Maximum amount | Must not exceed remaining discount, calculated as original Discount Fee amount minus prior non-reversed adjustments |
| Transaction date | Optional; defaults to the parent Discount Fee transaction date if omitted |
| Date vs Discount Fee | Must not be before the parent Discount Fee transaction date |
| Backdating | Not allowed; transaction date must be on or after the current business date |
| Loan status | Adjustment is allowed only for ACTIVE loans |
| Parent transaction | `relatedResourceId`, `relatedExternalResourceId`, or the transaction in the path, must reference a non-reversed Discount Fee transaction |

##### Allocation

An allocation row is stored in `m_wc_loan_transaction_allocation`. The adjustment amount is allocated entirely to the principal portion.

##### Business Event

`WorkingCapitalLoanDiscountFeeAdjustmentTransactionBusinessEvent` is emitted after a successful `DISCOUNT_FEE_ADJUSTMENT` transaction.

#### Accounting

The Discount Fee transaction updates the Working Capital Loan balance immediately. Income recognition is handled through Discount Fee Amortization transactions. For accrual with deferred revenue amortization accounting products, Discount Fee Amortization debits Deferred Income Liability and credits Income from Discount Fee.

#### Reversal Behavior

Discount Fee transactions are reversed through disbursement reversal. Disbursement reversal permits the related Discount Fee, Discount Fee Amortization, and Discount Fee Adjustment transactions to be handled with the disbursement as long as no disallowed active transaction exists after the disbursement.

When disbursement is reversed:

* The associated Discount Fee transaction is reversed.
* Related Discount Fee Amortization and Adjustment transactions are handled with the reversal flow.
* Loan balance and amortization schedule are reset consistently with the disbursement undo.

#### API Design

##### Create Discount Fee

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=discountFee
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions?command=discountFee
POST /v1/working-capital-loans/{loanId}/transactions/{transactionId}?command=discountFee
POST /v1/working-capital-loans/{loanId}/transactions/external-id/{transactionExternalId}?command=discountFee
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions/{transactionId}?command=discountFee
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions/external-id/{transactionExternalId}?command=discountFee
```

```json
{
  "transactionAmount": 5000.00,
  "relatedResourceId": 123,
  "transactionDate": "2026-01-01",
  "classificationId": 1,
  "externalId": "WC-DISC-001",
  "note": "Discount applied",
  "paymentDetails": {
    "accountNumber": "ACC-001",
    "routingCode": "RTG-001",
    "receiptNumber": "RCP-001",
    "bankNumber": "BNK-001",
    "checkNumber": "CHQ-001"
  },
  "locale": "en",
  "dateFormat": "yyyy-MM-dd"
}
```

On the forms that name the disbursement in the path, the same body is sent without `relatedResourceId`:

```json
{
  "transactionAmount": 5000.00,
  "classificationId": 1,
  "externalId": "WC-DISC-001",
  "note": "Discount applied",
  "locale": "en",
  "dateFormat": "yyyy-MM-dd"
}
```

* `transactionAmount` is optional. If omitted, the service defaults to the loan’s current discount.
* `transactionDate` is optional and defaults to the date of the related disbursement. When sent, it must be equal to the disbursement date, otherwise the request is rejected with 400 (`validation.msg.wc.loan.transaction.date.must.be.equal.disbursement.date`).
* `classificationId` is optional and must reference `working_capital_loan_discount_fee_classification` when provided.
* The related disbursement is named differently per endpoint form:
  
  
  
  
  
  * On `/transactions?command=discountFee`, the disbursement is named in the body: `relatedResourceId` with the transaction ID, or `relatedExternalResourceId` with the transaction external id. Exactly one of the two is mandatory, unless `transactionDate` is sent: the active disbursement on that date is then used, and if there is none, the request is rejected with 400 (`validation.msg.wc.loan.disbursement.transaction.not.found`). Sending both ids is rejected with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedExternalResourceId.cannot.also.be.provided.when.relatedResourceId.is.populated`), and sending neither id nor `transactionDate` with 400 (`validation.msg.wc.loan.related.resource.id.required`).
  * `relatedResourceId` is always read as the internal transaction ID, never as an external id. A value that is not a whole number (for example a UUID) is rejected with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedResourceId.not.a.number`), zero or a negative number with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedResourceId.not.greater.than.zero`).
  * `relatedExternalResourceId` is resolved within the loan and behaves exactly like `relatedResourceId` from there on: an external id that is unknown, or that belongs to another loan, is rejected with 400 (`validation.msg.wc.loan.disbursement.transaction.not.found`), and one that names a transaction that is not an active disbursement with 400 (`validation.msg.wc.loan.disbursement.transaction.invalid`).
  * On `/transactions/{transactionId}` and `/transactions/external-id/{transactionExternalId}` the path names the disbursement, and neither `relatedResourceId` nor `relatedExternalResourceId` is accepted in the body.
  * A `transactionId` or `transactionExternalId` that names no transaction of the loan, including one that belongs to another loan, returns 404 (`error.msg.wc.loan.transaction.not.found`).
* Only `/transactions?command=discountFee` is routed by the Batch API, so over Batch the disbursement is named with `relatedResourceId` or `relatedExternalResourceId`. The forms that name the transaction in the path are available over the regular API only.

##### Create Discount Fee Adjustment

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=discountFeeAdjustment
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions?command=discountFeeAdjustment
POST /v1/working-capital-loans/{loanId}/transactions/{transactionId}?command=discountFeeAdjustment
POST /v1/working-capital-loans/{loanId}/transactions/external-id/{transactionExternalId}?command=discountFeeAdjustment
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions/{transactionId}?command=discountFeeAdjustment
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions/external-id/{transactionExternalId}?command=discountFeeAdjustment
```

```json
{
  "transactionAmount": 50.00,
  "relatedResourceId": 99,
  "transactionDate": "10 January 2026",
  "classificationId": 1,
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "note": "Reduce discount fee",
  "externalId": "WC-DISC-ADJ-001"
}
```

On the forms that name the Discount Fee transaction in the path, the same body is sent without `relatedResourceId`:

```json
{
  "transactionAmount": 50.00,
  "transactionDate": "10 January 2026",
  "classificationId": 1,
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "note": "Reduce discount fee",
  "externalId": "WC-DISC-ADJ-001"
}
```

* `transactionAmount` is mandatory and capped by the remaining adjustable discount.
* `classificationId` is optional and must reference `working_capital_loan_discount_fee_classification` when provided.
* The related Discount Fee transaction is named differently per endpoint form:
  
  
  
  
  
  * On `/transactions?command=discountFeeAdjustment`, the Discount Fee transaction is named in the body: `relatedResourceId` with the transaction ID, or `relatedExternalResourceId` with the transaction external id. Exactly one of the two is mandatory; sending both is rejected with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedExternalResourceId.cannot.also.be.provided.when.relatedResourceId.is.populated`).
  * `relatedResourceId` is always read as the internal transaction ID, never as an external id. A value that is not a whole number (for example a UUID) is rejected with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedResourceId.not.a.number`), zero or a negative number with 400 (`validation.msg.WORKINGCAPITALLOAN.relatedResourceId.not.greater.than.zero`).
  * `relatedExternalResourceId` is resolved within the loan and behaves exactly like `relatedResourceId` from there on: an external id that is unknown, or that belongs to another loan, is rejected with 400 (`validation.msg.wc.loan.discount.transaction.not.found`), and one that names a transaction that is not an active Discount Fee with 400 (`validation.msg.wc.loan.discount.transaction.invalid`).
  * On `/transactions/{transactionId}` and `/transactions/external-id/{transactionExternalId}` the path names the Discount Fee transaction, and neither `relatedResourceId` nor `relatedExternalResourceId` is accepted in the body.
  * A `transactionId` or `transactionExternalId` that names no transaction of the loan, including one that belongs to another loan, returns 404 (`error.msg.wc.loan.transaction.not.found`).
* Only `/transactions?command=discountFeeAdjustment` is routed by the Batch API, so over Batch the Discount Fee transaction is named with `relatedResourceId` or `relatedExternalResourceId`. The forms that name the transaction in the path are available over the regular API only.

#### Summary

Working Capital Loan Discount Fee Transactions document the monetary transaction behavior for applied discounts. Discount configuration determines the amount; this transaction layer records it, links it to disbursement, updates balances and schedules, supports reductions through adjustments, and emits the relevant transaction business events.

### Working Capital Loan Charges

This documentation focuses on Working Capital Loan-related charge changes.

#### Create/Update Charge

Creates or updates a charge product applicable to Working Capital Loans.

##### Supported Fields

###### Mandatory Fields

* `chargeAppliesTo`
  
  
  
  
  
  * Must be set to `5`, as the `WorkingCapitalLoan` enum identifier is `5`.
* `chargeTimeType`
  
  
  
  
  
  * Must be `1` (`DISBURSEMENT`) or `2` (`SPECIFIED_DUE_DATE`).
* `chargeCalculationType`
  
  
  
  
  
  * Must be `1` (`FLAT`) when `chargeTimeType` is `2` (`SPECIFIED_DUE_DATE`).
  * Must be `1` (`FLAT`) or `2` (`PERCENT_OF_AMOUNT`) when `chargeTimeType` is `1` (`DISBURSEMENT`).
* `name`
  
  
  
  
  
  * Must be unique across all charge products.
* `amount`
* `active`
  
  
  
  
  
  * Boolean value.
* `currencyCode`
  
  
  
  
  
  * Refer to the template API for supported currency codes.
* `locale`
  
  
  
  
  
  * Refer to the available platform locales.
* `penalty`
  
  
  
  
  
  * Boolean value.
  * A Working Capital `disbursement` charge product may be flagged as a penalty. The term-loan rule that rejects a penalty due at disbursement does not apply to `chargeAppliesTo` `5`.

###### Optional Fields

* `chargePaymentMode`
  
  
  
  
  
  * Only `regular` (`0`) is accepted, on both create and update. Any other value is rejected with HTTP 400.
  * Defaults to `regular` when not provided on create; an update without it leaves the stored value unchanged.

##### Validation Rules

* The `chargeTimeType` / `chargeCalculationType` pair is validated on create and on update. An update is validated against the state the charge would have after the update, so a single `PUT /charges/{chargeId}` may change both fields together (for example from `disbursement` + `% amount` to `specified due date` + `flat`), while changing only `chargeCalculationType` to `% amount` on a `specified due date` charge is rejected.
* `chargePaymentMode` is validated on both paths: an explicit value other than `regular` is rejected on `POST /charges` and on `PUT /charges/{chargeId}`.

##### Supported Values

###### chargeAppliesTo

* `WorkingCapitalLoan` (`5`)

> [!NOTE]
> `Loan`, `Savings`, `Client`, and `Shares` charge entities are outside the scope of this documentation.

###### chargeTimeType

* `disbursement` (`1`)
* `specified due date` (`2`)

###### chargeCalculationType

* `flat` (`1`) — for both `disbursement` and `specified due date`
* `% amount` (`2`) — for `disbursement` only

#### Loan Account Level Charges

A charge product being valid for `chargeAppliesTo` `5` does not mean it can be attached to a Working Capital Loan account by hand. The account-level endpoints accept only `specified due date` charge products.

##### Add Charge to Loan Account

```http
POST /working-capital-loans/{loanId}/charges
```

* Accepts charge products with `chargeTimeType` `2` (`specified due date`) only. `dueDate` is mandatory, cannot be in the past, and the loan must be active, closed (obligations met) or overpaid.
* A `disbursement` charge product is rejected with HTTP 403 and the error code `error.msg.wc.loan.charge.time.type.not.supported`. Nothing is persisted on the account.
* Requires the `CREATE_WORKINGCAPITALLOANCHARGE` permission (grouping `transaction_loan`, entity `WORKINGCAPITALLOANCHARGE`, action `CREATE`).

##### Loan Account Charge Template

```http
GET /working-capital-loans/{loanId}/charges/template
```

* `chargeOptions` lists only active `specified due date` charge products in the loan currency. `disbursement` charge products are omitted because the endpoint above would reject them.

> [!NOTE]
> Disbursement charge products for Working Capital Loans are currently a product-definition capability only: they can be created, updated and offered through the charge template API, but they are not assessed during a Working Capital Loan disbursement and are not inherited from the loan product. Applying them in the loan lifecycle is outside the scope of this feature.

### Working Capital Loan Charge-Off

This documentation describes the Charge-Off feature for Working Capital Loans.

Charge-off marks a loan account as charged off for accounting purposes. In the Working Capital Loan
module it is modeled as a **pure accounting tag with no portfolio impact**: the loan stays `ACTIVE`, its
schedule and balance are unchanged, and all other actions and calculations behave exactly as they do on
a loan that is not charged off. This differs from the Term Loan implementation, whose charge-off carries
interest-recalculation behaviour â Working Capital Loans have no interest concept, so that machinery does
not apply here.

> [!NOTE]
> Charge-off is an accounting treatment only. It does not change the schedule, balance or delinquency
> data returned by the existing Working Capital Loan APIs; the loan resource only gains the charged-off
> state fields (see Loan Read Model). The loan remains `ACTIVE` until its balance is cured.
> The charged-off tag is cleared by an explicit undo, and also automatically when a backdated money-mover
> (or reversal) leaves nothing outstanding at the charge-off point in the transaction timeline â the
> charge-off transaction is then reversed and the flag is lifted.

#### Charge-Off a Loan

Marks the loan account as charged off and creates a non-monetary charge-off transaction.

* **Endpoint**: `POST /working-capital-loans/{loanId}/transactions?command=chargeOff`
* **Permission**: `CHARGEOFF_WORKINGCAPITALLOAN`

##### Supported Fields

###### Mandatory Fields

* `transactionDate`
  
  
  
  
  
  * The charge-off date. It may be backdated but must not be in the future, and must not be earlier than
    the last user transaction date (system transactions such as accrual or discount-fee amortization are ignored).
* `locale`
* `dateFormat`

###### Optional Fields

* `chargeOffReasonId`
  
  
  
  
  
  * Code value id from the `ChargeOffReasons` code.
* `note`
  
  
  
  
  
  * Free-text note (up to 1000 characters).
* `externalId`
  
  
  
  
  
  * External identifier for the charge-off transaction (up to 100 characters).

##### Behaviour

* A non-monetary `CHARGE_OFF` transaction is created for the charge-off amount, which is the outstanding
  balance as of the charge-off date. The charge-off date cannot precede the last user transaction, and system
  transactions do not move the balance, so the current outstanding balance equals the as-of-date balance.
* The transaction does **not** move the loan balance. Reprocessing walks it in chronological order to refresh
  that outstanding snapshot (or to reverse and lift the charge-off when preceding money-movers have cleared
  the outstanding).
* The loan is flagged as charged off (`chargedOff = true`) and remains `ACTIVE`.
* All credit transactions â repayment, goodwill credit, payout refund, credit balance refund â and payment,
  waiver or adjustment of **existing** charges remain allowed afterwards, so the balance can still be cured.
  Only their accounting treatment changes (see Accounting); the loan otherwise behaves like
  a loan that is not charged off.
* Three actions are blocked while the loan is charged off: adding a **new** charge, adding a discount
  fee, and a discount fee adjustment dated on or after the charge-off date. All three raise or restate
  an amount the charge-off has already written off.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSczOTBweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjk4NXB4O2hlaWdodDozOTBweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA5ODUgMzkwJyB3aWR0aD0nOTg1cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nMjMnIHgyPScyMycgeTE9Jzg0LjA2NzknIHkyPSczMDcuMzA0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzMwMy41JyB4Mj0nMzAzLjUnIHkxPSc4NC4wNjc5JyB5Mj0nMzA3LjMwNCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSc0OTkuNScgeDI9JzQ5OS41JyB5MT0nODQuMDY3OScgeTI9JzMwNy4zMDQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nODE2JyB4Mj0nODE2JyB5MT0nODQuMDY3OScgeTI9JzMwNy4zMDQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nOTQ1JyB4Mj0nOTQ1JyB5MT0nODQuMDY3OScgeTI9JzMwNy4zMDQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczMScgeD0nNScgeT0nNzkuOTY1OSc+VXNlcjwvdGV4dD48ZWxsaXBzZSBjeD0nMjMuNScgY3k9JzEzLjUnIGZpbGw9JyNFMkUyRjAnIHJ4PSc4JyByeT0nOCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTIzLjUsMjEuNSBMMjMuNSw0OC41IE0xMC41LDI5LjUgTDM2LjUsMjkuNSBNMjMuNSw0OC41IEwxMC41LDYzLjUgTTIzLjUsNDguNSBMMzYuNSw2My41ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzEnIHg9JzUnIHk9JzMyMS4yNyc+VXNlcjwvdGV4dD48ZWxsaXBzZSBjeD0nMjMuNScgY3k9JzMzMy44NzE5JyBmaWxsPScjRTJFMkYwJyByeD0nOCcgcnk9JzgnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J00yMy41LDM0MS44NzE5IEwyMy41LDM2OC44NzE5IE0xMC41LDM0OS44NzE5IEwzNi41LDM0OS44NzE5IE0yMy41LDM2OC44NzE5IEwxMC41LDM4My44NzE5IE0yMy41LDM2OC44NzE5IEwzNi41LDM4My44NzE5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjYnIHg9JzI0MC41JyB5PSc1MCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExMicgeD0nMjQ3LjUnIHk9JzcxLjk2NTknPlRyYW5zYWN0aW9ucyBBUEk8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjYnIHg9JzI0MC41JyB5PSczMDYuMzA0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTEyJyB4PScyNDcuNScgeT0nMzI4LjI3Jz5UcmFuc2FjdGlvbnMgQVBJPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTc2JyB4PSc0MTEuNScgeT0nNTAnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjInIHg9JzQxOC41JyB5PSc3MS45NjU5Jz5DaGFyZ2VPZmYgV3JpdGUgU2VydmljZTwvdGV4dD48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE3NicgeD0nNDExLjUnIHk9JzMwNi4zMDQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjInIHg9JzQxOC41JyB5PSczMjguMjcnPkNoYXJnZU9mZiBXcml0ZSBTZXJ2aWNlPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTU5JyB4PSc3MzcnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTQ1JyB4PSc3NDQnIHk9JzcxLjk2NTknPkFjY291bnRpbmcgUHJvY2Vzc29yPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTU5JyB4PSc3MzcnIHk9JzMwNi4zMDQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNDUnIHg9Jzc0NCcgeT0nMzI4LjI3Jz5BY2NvdW50aW5nIFByb2Nlc3NvcjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3MicgeD0nOTA2JyB5PSc3OS45NjU5Jz5tX3djX2xvYW48L3RleHQ+PHBhdGggZD0nTTkyNywyOSBDOTI3LDE5IDk0NSwxOSA5NDUsMTkgQzk0NSwxOSA5NjMsMTkgOTYzLDI5IEw5NjMsNTUgQzk2Myw2NSA5NDUsNjUgOTQ1LDY1IEM5NDUsNjUgOTI3LDY1IDkyNyw1NSBMOTI3LDI5ICcgZmlsbD0nI0UyRTJGMCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBhdGggZD0nTTkyNywyOSBDOTI3LDM5IDk0NSwzOSA5NDUsMzkgQzk0NSwzOSA5NjMsMzkgOTYzLDI5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzInIHg9JzkwNicgeT0nMzIxLjI3Jz5tX3djX2xvYW48L3RleHQ+PHBhdGggZD0nTTkyNywzMzUuMzcxOSBDOTI3LDMyNS4zNzE5IDk0NSwzMjUuMzcxOSA5NDUsMzI1LjM3MTkgQzk0NSwzMjUuMzcxOSA5NjMsMzI1LjM3MTkgOTYzLDMzNS4zNzE5IEw5NjMsMzYxLjM3MTkgQzk2MywzNzEuMzcxOSA5NDUsMzcxLjM3MTkgOTQ1LDM3MS4zNzE5IEM5NDUsMzcxLjM3MTkgOTI3LDM3MS4zNzE5IDkyNywzNjEuMzcxOSBMOTI3LDMzNS4zNzE5ICcgZmlsbD0nI0UyRTJGMCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBhdGggZD0nTTkyNywzMzUuMzcxOSBDOTI3LDM0NS4zNzE5IDk0NSwzNDUuMzcxOSA5NDUsMzQ1LjM3MTkgQzk0NSwzNDUuMzcxOSA5NjMsMzQ1LjM3MTkgOTYzLDMzNS4zNzE5ICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScyOTEuNSwxMTMuNzczOSwzMDEuNSwxMTcuNzczOSwyOTEuNSwxMjEuNzczOSwyOTUuNSwxMTcuNzczOScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjMuNScgeDI9JzI5Ny41JyB5MT0nMTE3Ljc3MzknIHkyPScxMTcuNzczOScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI1NicgeD0nMzAuNScgeT0nMTExLjk2NDknPlBPU1QgLi4uL3RyYW5zYWN0aW9ucz9jb21tYW5kPWNoYXJnZU9mZjwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzQ4Ny41LDE0NS40Nzk5LDQ5Ny41LDE0OS40Nzk5LDQ4Ny41LDE1My40Nzk5LDQ5MS41LDE0OS40Nzk5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMDMuNScgeDI9JzQ5My41JyB5MT0nMTQ5LjQ3OTknIHkyPScxNDkuNDc5OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3MicgeD0nMzEwLjUnIHk9JzE0My42NzA5Jz5jaGFyZ2VPZmYobG9hbklkLCBjb21tYW5kKTwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0OTkuNScgeDI9JzU0MS41JyB5MT0nMTgxLjE4NicgeTI9JzE4MS4xODYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1NDEuNScgeDI9JzU0MS41JyB5MT0nMTgxLjE4NicgeTI9JzE5NC4xODYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1MDAuNScgeDI9JzU0MS41JyB5MT0nMTk0LjE4NicgeTI9JzE5NC4xODYnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzUxMC41LDE5MC4xODYsNTAwLjUsMTk0LjE4Niw1MTAuNSwxOTguMTg2LDUwNi41LDE5NC4xODYnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzMwMycgeD0nNTA2LjUnIHk9JzE3NS4zNzcnPnZhbGlkYXRlIChhY3RpdmUsIG5vdCBhbHJlYWR5IGNoYXJnZWQgb2ZmLCBkYXRlIHJ1bGVzKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzkzMywyMjEuODkyLDk0MywyMjUuODkyLDkzMywyMjkuODkyLDkzNywyMjUuODkyJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0OTkuNScgeDI9JzkzOScgeTE9JzIyNS44OTInIHkyPScyMjUuODkyJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjg3JyB4PSc1MDYuNScgeT0nMjIwLjA4Myc+bWFyayBsb2FuIGNoYXJnZWQgb2ZmICsgY3JlYXRlIENIQVJHRV9PRkYgdHhuPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nODA0LjUsMjUzLjU5OCw4MTQuNSwyNTcuNTk4LDgwNC41LDI2MS41OTgsODA4LjUsMjU3LjU5OCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDk5LjUnIHgyPSc4MTAuNScgeTE9JzI1Ny41OTgnIHkyPScyNTcuNTk4Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTgwJyB4PSc1MDYuNScgeT0nMjUxLjc4OSc+cG9zdCBjaGFyZ2Utb2ZmIGpvdXJuYWwgZW50cmllczwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0LjUsMjg1LjMwNCwyNC41LDI4OS4zMDQsMzQuNSwyOTMuMzA0LDMwLjUsMjg5LjMwNCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzI4LjUnIHgyPSc0OTguNScgeTE9JzI4OS4zMDQnIHkyPScyODkuMzA0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nODInIHg9JzQwLjUnIHk9JzI4My40OTUnPnRyYW5zYWN0aW9uIGlkPC90ZXh0PjwvZz48L3N2Zz4=)

Figure 12. Charge-off request/response flow

#### Undo Charge-Off

Reverses a charge-off that was applied in error.

* **Endpoint**: `POST /working-capital-loans/{loanId}/transactions?command=undoChargeOff`
* **Permission**: `UNDOCHARGEOFF_WORKINGCAPITALLOAN`

Undo removes the charged-off tag, reverses the charge-off transaction and reverses its journal entries.
It is only allowed when the charge-off is still the last user transaction in (transaction date, id) order
(the same restriction as term and progressive loans). A backdated money-mover dated before the charge-off
does not block undo. System transactions (accrual and discount-fee amortization) are not user transactions
and therefore do not block undo.

#### Charge-Off Template

Returns the data needed to prefill the charge-off form.

* **Endpoint**: `GET /working-capital-loans/{loanId}/template?templateType=chargeOff`

| **Field** | **Description** |
| --- | --- |
| `chargeOffAmount` | Auto-calculated outstanding balance as of the charge-off date. Read-only. |
| `chargeOffDate` | Suggested charge-off date, defaulting to the current business date. |
| `chargeOffReasonOptions` | Available `ChargeOffReasons` code values. |
| `currency` | Loan currency. |

#### Loan Read Model

The Working Capital Loan resource exposes the charged-off state:

| **Field** | **Description** |
| --- | --- |
| `chargedOff` | `true` when the loan is charged off, otherwise `false`. |
| `chargedOffOnDate` | The charge-off date. Only present while the loan is charged off. |
| `chargeOffReason` | The `ChargeOffReasons` code value selected at charge-off time, when one was provided. |

#### Validations

| **Operation** | **Rule** | **Error code** |
| --- | --- | --- |
| Charge-off | The loan must be active. | `error.msg.wc.loan.is.not.active` |
| Charge-off | The loan must not already be charged off. | `error.msg.wc.loan.is.already.charged.off` |
| Charge-off | The charge-off date must not be earlier than the last user transaction date. | `cannot.be.before.last.transaction.date` |
| Charge-off | The charge-off date must not be in the future. | `cannot.be.a.future.date` |
| Add charge | New charges cannot be added once the loan is charged off. | `error.msg.wc.loan.is.charged.off` |
| Discount fee | A discount fee cannot be added once the loan is charged off. | `error.msg.wc.loan.is.charged.off` |
| Discount fee adjustment | An adjustment dated on or after the charge-off date is rejected. | `error.msg.wc.loan.is.charged.off` |
| Undo charge-off | The loan must be charged off. | `error.msg.wc.loan.is.not.charged.off` |
| Undo charge-off | Undo is not allowed if any user transaction was posted after the charge-off. | `error.msg.wc.loan.charge.off.is.not.the.last.user.transaction` |

> [!NOTE]
> A second charge-off on an already charged-off loan, and a second undo on a loan that is not charged off,
> both return a validation error.

#### Accounting

Charge-off accounting applies to products configured with the **Accrual (deferred revenue amortization)**
accounting rule. The charge-off transaction writes off the outstanding receivables against the charge-off
expense. There is no interest leg â Working Capital Loans have no interest concept.

| **Portion** | **Debit** | **Credit** |
| --- | --- | --- |
| Principal | `CHARGE_OFF_EXPENSE` | `LOAN_PORTFOLIO` |
| Fee | `INCOME_FROM_CHARGE_OFF_FEES` | `FEES_RECEIVABLE` |
| Penalty | `INCOME_FROM_CHARGE_OFF_PENALTY` | `PENALTIES_RECEIVABLE` |

Undo reverses these journal entries. The charge-off General Ledger accounts are configured per product
through the Working Capital Loan product accounting mapping.

##### While the Loan Is Charged Off

Accounting for a money-mover follows its place in the transaction timeline relative to the charge-off
(date, then submitted-on, then created, then id), not merely whether the loan currently carries the
charged-off flag. A backdated repayment that sorts **before** the charge-off keeps regular portfolio /
receivable credits; a transaction that sorts **after** it uses the recovery / charge-off routing below
(including a same-day repayment posted after the charge-off). Reprocessing refreshes the charge-off
amount from the outstanding at its point in the timeline and restates journal entries when portions or
that routing change.

Transactions posted while the loan carries the charged-off tag are accepted as usual, but their accounting
treatment changes when they fall after the charge-off: credits that would normally reduce the portfolio or
receivables â already written off by the charge-off â instead recognize recovery income or reverse what
the charge-off recognized, and discount-fee amortization is recognized against the charge-off expense
instead of discount-fee income.

| **Transaction** | **Debit** | **Credit** |
| --- | --- | --- |
| Repayment | `FUND_SOURCE` | `INCOME_FROM_RECOVERY` for the principal, fee and penalty portions; `OVERPAYMENT` for any overpaid excess |
| Goodwill credit | `GOODWILL_CREDIT` for the principal and overpayment portions, `INCOME_FROM_GOODWILL_CREDIT_FEES` / `INCOME_FROM_GOODWILL_CREDIT_PENALTY` per portion (unchanged) | `INCOME_FROM_RECOVERY` for the principal, fee and penalty portions; `OVERPAYMENT` for any overpaid excess |
| Payout refund | `FUND_SOURCE` | `CHARGE_OFF_EXPENSE` for the principal portion, `INCOME_FROM_CHARGE_OFF_FEES` / `INCOME_FROM_CHARGE_OFF_PENALTY` per portion â reversing what the charge-off recognized; `OVERPAYMENT` for any overpaid excess |
| Discount-fee amortization | `DEFERRED_INCOME_LIABILITY` | `CHARGE_OFF_EXPENSE` (instead of `INCOME_FROM_DISCOUNT_FEE`) |

Charge accrual keeps its regular treatment (receivable against fee/penalty income). Once the
charge-off is undone, subsequent transactions return to the regular accounting treatment.

##### Charge adjustment

Credit accounts depend on whether the adjustment sorts **before** or **after** the charge-off transaction.
Debit is always the full amount to `INCOME_FROM_FEES` or `INCOME_FROM_PENALTIES`
(fee vs penalty charge). Credits:

| **Portion** | **Sorts before charge-off** | **Sorts after charge-off** |
| --- | --- | --- |
| Principal | `LOAN_PORTFOLIO` | `INCOME_FROM_CHARGE_OFF_FEES` / `INCOME_FROM_CHARGE_OFF_PENALTY` (charge type) |
| Fee | `FEES_RECEIVABLE` | `INCOME_FROM_CHARGE_OFF_FEES` |
| Penalty | `PENALTIES_RECEIVABLE` | `INCOME_FROM_CHARGE_OFF_PENALTY` |
| Excess | `OVERPAYMENT` | `OVERPAYMENT` |

Restated on reprocess when the allocation or before/after charge-off routing changes.

#### Permissions

| **Code** | **Entity** | **Action** |
| --- | --- | --- |
| `CHARGEOFF_WORKINGCAPITALLOAN` | `WORKINGCAPITALLOAN` | `CHARGEOFF` |
| `UNDOCHARGEOFF_WORKINGCAPITALLOAN` | `WORKINGCAPITALLOAN` | `UNDOCHARGEOFF` |

#### Out of Scope

The following are intentionally not part of the first version:

* Overriding the charge-off expense account per charge-off reason (currently the default
  `CHARGE_OFF_EXPENSE` account is used).
* Fraud-expense routing (`CHARGE_OFF_FRAUD_EXPENSE`), which depends on the Working Capital Loan fraud
  feature.

### Working Capital Loan â Credit Balance Refund (CBR)

#### Overview

Credit Balance Refund (CBR) is supported for Working Capital loans when a loan has an overpayment balance.

#### Core Behavior

For Working Capital loans:

* Overpayment is exposed as `overpaymentAmount` on the working capital loan balance
* `principalOutstanding` is not reduced below zero; excess repayment is tracked as overpayment
* CBR reduces `overpaymentAmount` by the refund amount

#### API

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=creditBalanceRefund
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions?command=creditBalanceRefund
```

#### Validation

CBR is allowed only when:

* Loan status is `OVERPAID`
* `overpaymentAmount > 0`
* Refund amount is positive and does not exceed current `overpaymentAmount`
* Transaction date is not in the future, is not before disbursement, and is not before the current business date

#### Status Handling

After CBR:

* If `overpaymentAmount > 0`, the loan remains `OVERPAID`
* If `overpaymentAmount = 0` and `principalOutstanding = 0`, status transitions to `CLOSED_OBLIGATIONS_MET`

### Working Capital Loan â Goodwill Credit Transaction

#### Purpose

The Goodwill Credit transaction represents a **credit adjustment provided to the borrower**, typically as a gesture of goodwill to address **customer grievances, service issues, or operational corrections.**

It ensures:

* Controlled handling of **customer compensation**
* Proper **adjustment of outstanding dues**
* Accurate **accounting of goodwill expenses**

#### Functionality

* Goodwill Credit is a **monetary transaction** applied to a loan account.
* Functionally, it follows the repayment-like transaction flow, but it is recorded as `GOODWILL_CREDIT`.
* It is performed when:
  
  
  
  
  
  * A lender decides to credit an amount to the borrower without expecting repayment.
* It results in:
  
  
  
  
  
  * Reduction in outstanding loan balance
  * Triggering of accounting entries for accrual with deferred revenue amortization accounting products

#### Goodwill Credit Handling

* It results in:
  
  
  
  
  
  * Reduction of outstanding balance
  * Calculation of the actual Amortization amount
  * Posting a Discount Fee Amortization transaction when the loan is closed or overpaid and discount fee income still needs to be recognized
  * Adjustment of the Amortization schedule
  * Allocation of the applied amount to principal outstanding, with any excess tracked as overpayment
  * Triggering of accounting entries for accrual with deferred revenue amortization accounting products

#### Validation Rules

Goodwill credit can be applied only if:
* Loan status is **Active**, **Overpaid**, or **Closed Obligations Met**
Amount validation:
* Must be **greater than zero**

#### Allocation Logic

Goodwill Credit is currently applied against principal outstanding. The service records a principal allocation for the amount applied to outstanding principal, and any amount above the outstanding balance becomes overpayment.

#### Schedule Impact

* On Goodwill Credit:
  
  
  
  
  
  * System will:
    
    
    
    
    
    * Adjust outstanding balances
    * Update amortization schedule
    * Recalculate future periods
* Transaction date must not be in the future and must not be before the first disbursement date.

#### API

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=goodwillCredit
POST /v1/working-capital-loans/external-id/{loanExternalId}/transactions?command=goodwillCredit
```

```json
{
  "transactionDate": "10 January 2026",
  "transactionAmount": 100.00,
  "classificationId": 1,
  "externalId": "WC-GW-001",
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "note": "Customer goodwill credit"
}
```

#### Accounting Treatment

Goodwill Credit triggers Journal Entries (JE) when the Working Capital Loan product uses accrual with deferred revenue amortization accounting.

##### Goodwill Credit

| Dr | Expense from Goodwill Credit | Expense | Principal + Excess |
| --- | --- | --- | --- |
| Dr | Income from Goodwill Credit Fees | Income | Fees |
| Dr | Income from Goodwill Credit Penalty | Income | Penalty |
| Cr | Loan Portfolio | Asset | Principal |
| Cr | Fees Receivable | Asset | Fees |
| Cr | Penalty Receivable | Asset | Penalty |
| Cr | Overpayment Liability | Liability | Excess |

Charge-off accounting for Working Capital Loan Goodwill Credit is not implemented. If the accounting processor is asked to post Goodwill Credit entries with the charged-off flag, it raises a `NotImplementedException`.

#### Special Scenarios

* If the Goodwill Credit produces an overpayment, the excess can later be returned through a Credit Balance Refund transaction.

### Working Capital Loan â Write-Off Transaction

#### Purpose

The Write-Off transaction closes a Working Capital Loan that is deemed uncollectible. It recognizes the remaining outstanding as a loss, so the receivable no longer inflates the portfolio.

It ensures:

* Controlled **closure of uncollectible accounts**
* Recognition of the outstanding balance as a **written-off loss**
* A reversible action, so a write-off applied in error can be **undone**

#### Functionality

* Write-Off is a **terminal** action (unlike Charge-Off, which is a non-monetary tag that keeps the loan `ACTIVE`).
* It is recorded as a `WRITEOFF` transaction whose amount is the outstanding balance at the write-off date.
* It results in:
  
  
  
  
  
  * Zeroing of all outstanding balances (principal, fees, penalty)
  * Moving the loan to status `CLOSED_WRITTEN_OFF`
  * Triggering of accounting entries for accrual with deferred revenue amortization accounting products
* Incoming parameters follow the progressive-loan shape.

#### Write-Off Handling

* Outstanding is zeroed by moving each portion into a **written-off bucket** (`principalWrittenOff` / `feeWrittenOff` / `penaltyWrittenOff`) on the loan balance. The paid columns are untouched, so the original outstanding can be restored by an undo.
* Each active loan charge has its unpaid remainder marked as `amountWrittenOff`, so the charge view reports a zero `amountOutstanding` consistent with the zeroed balance. The charge is **not** marked paid.
* The loan status transitions `ACTIVE → CLOSED_WRITTEN_OFF`.
* Audit fields are recorded on the loan: `writtenOffOnDate`, `closedOnDate`, `closedBy`, and the optional `writeOffReason`.

#### Undo Write-Off

Reverses a write-off applied in error:

* Reverses the `WRITEOFF` transaction (kept in the ledger, flagged reversed).
* Transitions the loan back `CLOSED_WRITTEN_OFF → ACTIVE`.
* Restores the outstanding balance (clears the written-off buckets, on the loan balance and on each charge).
* Clears the write-off audit fields.

#### Validation Rules

Write-off can be applied only if:

* Loan status is **Active**.

Undo write-off can be applied only if:

* Loan status is **Closed (written-off)**.

##### Write-Off Date

`transactionDate` is **required**. It may be backdated, but the write-off must remain the **latest transaction
on the loan account**, so two bounds apply:

* It must not be in the future.
* It must not be earlier than the last user transaction date. System-generated postings (accrual and
  discount-fee amortization) are ignored, so a Close of Business run cannot push the floor forward when there
  was no user activity.

Because the disbursement itself is a user transaction, that lower bound also prevents a write-off from being
backdated before the loan was disbursed â no separate disbursement-date check is needed.

This matches the date rule already applied to Charge-Off, so both operations behave the same way for the
same input.

| **Operation** | **Rule** | **Error code** |
| --- | --- | --- |
| Write-off | The loan must be active. | `error.msg.wc.loan.is.not.active` |
| Write-off | The write-off date is required. | `validation.msg.WORKINGCAPITALLOAN.transactionDate.cannot.be.blank` |
| Write-off | The write-off date must not be in the future. | `cannot.be.a.future.date` |
| Write-off | The write-off date must not be earlier than the last user transaction date. | `cannot.be.before.last.transaction.date` |
| Undo write-off | The loan must be written off. | `error.msg.wc.loan.is.not.written.off` |
| Undo write-off | No recovery payment may be outstanding on the loan. | `cannot.undo.write.off.with.recovery.payments` |

Undoing the write-off restores the full outstanding balance, so any money already collected as recovery income
would then also be replayed against that restored balance â the same cash both recognized as income and
reducing the receivable. Recoveries must be reversed first; see Working Capital Loan â Recovery Payment.

##### Post-write-off lock

A written-off loan is locked: apart from the Recovery Payment described below, no new transaction can be posted
on it and no existing transaction can be undone while it stays in `CLOSED_WRITTEN_OFF`. This is stricter than
term and progressive loans, which reopen the loan on adjustment. The only way out is the undo write-off, which
reopens the loan to `ACTIVE` and restores the balance; from there the account behaves normally again.

The single exception is the **Recovery Payment**, which records money collected after the write-off and is
admitted precisely because the loan is written off. It is a typed exception â opened for the
`RECOVERY_REPAYMENT` transaction type only â so none of the status gates listed below are relaxed. See
Working Capital Loan â Recovery Payment.

The lock is not a check of its own â it falls out of the status gates each operation already applies, none of
which admit `CLOSED_WRITTEN_OFF`:

| **Operation** | **Allowed statuses** | **Error code** |
| --- | --- | --- |
| Repayment, goodwill credit, payout refund | `ACTIVE`, `CLOSED_OBLIGATIONS_MET`, `OVERPAID` | `validation.msg.wc.loan.transition.not.allowed` |
| Undo transaction | `ACTIVE`, `CLOSED_OBLIGATIONS_MET`, `OVERPAID` | `undo.transaction.not.allowed.for.loan.status` |
| Charge adjustment | `ACTIVE`, `CLOSED_OBLIGATIONS_MET`, `OVERPAID` | `wc.loan.charge.adjustment.invalid.status` |
| Charge-off | `ACTIVE` | `error.msg.wc.loan.is.not.active` |
| Period payment rate change | `ACTIVE` | `rate.change.not.allowed.for.non.active.loan` |

#### API

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=writeOff
POST /v1/working-capital-loans/{loanId}/transactions?command=undoWriteOff
```

```json
{
  "transactionDate": "15 January 2026",
  "writeoffReasonId": 1,
  "externalId": "WC-WO-001",
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "note": "Uncollectible"
}
```

```json
{
  "reversalExternalId": "WC-WO-REV-001",
  "note": "Written off in error",
  "locale": "en"
}
```

The write-off amount is not supplied by the caller: it is the outstanding balance computed as of the write-off date.

#### Read Model

The Working Capital Loan resource exposes the written-off state:

| **Field** | **Description** |
| --- | --- |
| `status` | `CLOSED_WRITTEN_OFF` (code `loanStatusType.closed.written.off`) while written off; `ACTIVE` again after an undo. |
| `writtenOffOnDate` | The write-off date. Cleared by an undo. |
| `writeOffReason` | The `WriteOffReasons` code value selected at write-off time, when one was provided. |
| `balance.totalWrittenOff` | Gross amount moved out of the outstanding by the write-off, split per portion in `principalWrittenOff`, `feeWrittenOff` and `penaltyWrittenOff`. Cleared by an undo. |

#### Accounting Treatment

Write-Off triggers Journal Entries (JE) when the Working Capital Loan product uses accrual with deferred revenue amortization accounting. Working Capital Loans have no interest concept, so there is no interest leg.

##### Write-Off

| **Type** | **WCP mapping name** | **GL type** | **Allocation** |
| --- | --- | --- | --- |
| Dr | Losses Written-off | Expense | Principal + Fees + Penalty |
| Cr | Loan Portfolio | Asset | Principal |
| Cr | Fees Receivable | Asset | Fees |
| Cr | Penalties Receivable | Asset | Penalty |

##### Write-Off when the Loan is Charged-Off

When the loan was already charged off, the portfolio and receivable accounts were credited out at charge-off time, so the write-off does not touch them again. Instead it reclassifies the loss out of the charge-off accounts â crediting exactly what the charge-off debited â into Losses Written-off. The net P&L effect is zero; only the presentation of the loss changes:

| **Type** | **WCP mapping name** | **GL type** | **Allocation** |
| --- | --- | --- | --- |
| Dr | Losses Written-off | Expense | Principal + Fees + Penalty |
| Cr | Charge-off Expense (or Charge-off Fraud Expense when the loan is flagged fraud) | Expense | Principal |
| Cr | Income from Charge-off Fees | Income | Fees |
| Cr | Income from Charge-off Penalties | Income | Penalty |

##### Undo Write-Off

Undo posts an offsetting mirror for each entry above (the ledger stays append-only), which nets the write-off to zero. For a loan that was not charged off:

| **Type** | **WCP mapping name** | **GL type** | **Allocation** |
| --- | --- | --- | --- |
| Dr | Loan Portfolio | Asset | Principal |
| Dr | Fees Receivable | Asset | Fees |
| Dr | Penalties Receivable | Asset | Penalty |
| Cr | Losses Written-off | Expense | Principal + Fees + Penalty |

For a loan that was charged off, the mirrors flip the reclassification instead: debit the charge-off accounts, credit Losses Written-off.

#### Business Events

* `WorkingCapitalLoanWriteOffTransactionBusinessEvent` â emitted after a write-off.
* `WorkingCapitalLoanUndoWriteOffTransactionBusinessEvent` â emitted after an undo write-off.
* `WorkingCapitalLoanBalanceChangedBusinessEvent` â emitted by both operations, since the write-off zeroes the
  outstanding balance and the undo restores it.
* `WorkingCapitalLoanStatusChangedBusinessEvent` â emitted by both operations, for the transition to
  `CLOSED_WRITTEN_OFF` and back to `ACTIVE`.
* `WorkingCapitalLoanDelinquencyRangeChangeBusinessEvent` â emitted indirectly when the delinquency reprocess
  that follows either operation changes the loan’s classification tag.

##### Delinquency

Both operations reprocess the delinquency range schedule. A write-off zeroes the outstanding balance, so every
open period is capped to what the customer can still owe and the loan classifies as not delinquent, lifting any
active tag; the undo replays the repayment history against the restored balance and re-derives the
classification. This is not optional housekeeping: a `CLOSED_WRITTEN_OFF` loan is excluded from the Close of
Business scope, so without the reprocess a loan that was delinquent at write-off time would stay tagged
delinquent indefinitely.

#### Permissions

| **Permission** | **Grouping** | **Action** |
| --- | --- | --- |
| `WRITEOFF_WORKINGCAPITALLOAN` | `WORKINGCAPITALLOAN` | `WRITEOFF` |
| `UNDOWRITEOFF_WORKINGCAPITALLOAN` | `WORKINGCAPITALLOAN` | `UNDOWRITEOFF` |

### Working Capital Loan â Recovery Payment

#### Purpose

A Recovery Payment records money collected on a Working Capital Loan **after it was written off**. The loss was already recognized at write-off time, so the money coming back is recognized as **income**, not as a repayment of a receivable that no longer exists.

It ensures:

* Collections on written-off accounts can be **recorded and accounted for**
* The recovered cash is recognized as **recovery income**, leaving the written-off loss intact
* Recoveries cannot exceed the loss that was actually booked
* A recovery captured in error can be **reversed**

#### Functionality

* A Recovery Payment is the **only** monetary transaction admitted while the loan sits in `CLOSED_WRITTEN_OFF` (see Interaction with the post-write-off lock).
* It is recorded as a `RECOVERY_REPAYMENT` transaction for the amount collected.
* It results in:
  
  
  
  
  
  * Recognition of the whole amount as recovery income
  * An increase of the loan’s running `totalRecovered`, which lowers how much is still recoverable
  * Triggering of accounting entries for accrual with deferred revenue amortization accounting products
* It deliberately does **not**:
  
  
  
  
  
  * Change the loan status â the loan stays `CLOSED_WRITTEN_OFF`
  * Move the outstanding balance, which the write-off left at zero and which stays at zero
  * Allocate across principal, fees or penalty â the transaction carries **no allocation**
  * Touch the amortization, delinquency or breach schedules

> [!NOTE]
> The status is left untouched on purpose. A Working Capital Loan in `CLOSED_WRITTEN_OFF` has a zero outstanding, so running the balance-driven status evaluation would try to transition it as **repaid in full**, which is not a legal transition out of `CLOSED_WRITTEN_OFF`. The recovery path therefore never invokes the loan lifecycle state machine.

#### Recovery Payment Handling

* The collected amount is added to `totalRecovered` on the loan balance. That column is the only balance-side effect of the transaction.
* `totalWrittenOff` â the gross amount the write-off moved out of the outstanding â is **not** reduced by recoveries. It remains the accounting record of the loss that was booked.
* What is still collectable is derived: `writtenOffOutstanding = totalWrittenOff - totalRecovered`, floored at zero. This value caps the next recovery payment.

#### Undo Recovery Payment

A recovery captured in error can be reversed through the generic transaction-undo command:

* Reverses the `RECOVERY_REPAYMENT` transaction (kept in the ledger, flagged reversed, with an optional `reversalExternalId`).
* Subtracts the amount from `totalRecovered`, so the money becomes recoverable again.
* Posts the mirror journal entries (see Undo Recovery Payment).
* Leaves the loan in `CLOSED_WRITTEN_OFF`.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc3OTRweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjExNjZweDtoZWlnaHQ6Nzk0cHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTE2NiA3OTQnIHdpZHRoPScxMTY2cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzI5NC42MTE5JyBzdHlsZT0nc3Ryb2tlOiMwMDAwMDA7c3Ryb2tlLXdpZHRoOjEuNTtmaWxsOm5vbmU7JyB3aWR0aD0nMTE0OScgeD0nMTAnIHk9JzE5Ni4xODYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtmaWxsOm5vbmU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzM4JyB4Mj0nMzgnIHkxPSc4NC4wNjc5JyB5Mj0nNzExLjAzNCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O2ZpbGw6bm9uZTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nMzM4LjUnIHgyPSczMzguNScgeTE9Jzg0LjA2NzknIHkyPSc3MTEuMDM0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSc1ODEuNScgeDI9JzU4MS41JyB5MT0nODQuMDY3OScgeTI9JzcxMS4wMzQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtmaWxsOm5vbmU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9Jzg4OScgeDI9Jzg4OScgeTE9Jzg0LjA2NzknIHkyPSc3MTEuMDM0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPScxMDAxJyB4Mj0nMTAwMScgeTE9Jzg0LjA2NzknIHkyPSc3MTEuMDM0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPScxMTA0JyB4Mj0nMTEwNCcgeTE9Jzg0LjA2NzknIHkyPSc3MTEuMDM0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzEnIHg9JzIwJyB5PSc3OS45NjU5Jz5Vc2VyPC90ZXh0PjxlbGxpcHNlIGN4PSczOC41JyBjeT0nMTMuNScgZmlsbD0nI0UyRTJGMCcgcng9JzgnIHJ5PSc4JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cGF0aCBkPSdNMzguNSwyMS41IEwzOC41LDQ4LjUgTTI1LjUsMjkuNSBMNTEuNSwyOS41IE0zOC41LDQ4LjUgTDI1LjUsNjMuNSBNMzguNSw0OC41IEw1MS41LDYzLjUgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczMScgeD0nMjAnIHk9JzcyNC45OTk5Jz5Vc2VyPC90ZXh0PjxlbGxpcHNlIGN4PSczOC41JyBjeT0nNzM3LjYwMTknIGZpbGw9JyNFMkUyRjAnIHJ4PSc4JyByeT0nOCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTM4LjUsNzQ1LjYwMTkgTDM4LjUsNzcyLjYwMTkgTTI1LjUsNzUzLjYwMTkgTDUxLjUsNzUzLjYwMTkgTTM4LjUsNzcyLjYwMTkgTDI1LjUsNzg3LjYwMTkgTTM4LjUsNzcyLjYwMTkgTDUxLjUsNzg3LjYwMTkgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzEyNicgeD0nMjc1LjUnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTEyJyB4PScyODIuNScgeT0nNzEuOTY1OSc+VHJhbnNhY3Rpb25zIEFQSTwvdGV4dD48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzEyNicgeD0nMjc1LjUnIHk9JzcxMC4wMzQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTInIHg9JzI4Mi41JyB5PSc3MzEuOTk5OSc+VHJhbnNhY3Rpb25zIEFQSTwvdGV4dD48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzUyLjEzNTgnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzEzNicgeD0nNTEzLjUnIHk9JzMwLjkzMjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMjInIHg9JzUyMC41JyB5PSc1Mi44OTgnPlJlY292ZXJ5IFBheW1lbnQ8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nODgnIHg9JzUzNy41JyB5PSc3MS45NjU5Jz5Xcml0ZSBTZXJ2aWNlPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nNTIuMTM1OCcgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM2JyB4PSc1MTMuNScgeT0nNzEwLjAzNCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyMicgeD0nNTIwLjUnIHk9JzczMS45OTk5Jz5SZWNvdmVyeSBQYXltZW50PC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg4JyB4PSc1MzcuNScgeT0nNzUxLjA2NzgnPldyaXRlIFNlcnZpY2U8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMDknIHg9JzgzNScgeT0nNTAnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc5NScgeD0nODQyJyB5PSc3MS45NjU5Jz5EYXRhIFZhbGlkYXRvcjwvdGV4dD48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzEwOScgeD0nODM1JyB5PSc3MTAuMDM0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nOTUnIHg9Jzg0MicgeT0nNzMxLjk5OTknPkRhdGEgVmFsaWRhdG9yPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg5JyB4PSc5NTQnIHk9Jzc5Ljk2NTknPkxvYW4gYmFsYW5jZTwvdGV4dD48cGF0aCBkPSdNOTgzLjUsMjkgQzk4My41LDE5IDEwMDEuNSwxOSAxMDAxLjUsMTkgQzEwMDEuNSwxOSAxMDE5LjUsMTkgMTAxOS41LDI5IEwxMDE5LjUsNTUgQzEwMTkuNSw2NSAxMDAxLjUsNjUgMTAwMS41LDY1IEMxMDAxLjUsNjUgOTgzLjUsNjUgOTgzLjUsNTUgTDk4My41LDI5ICcgZmlsbD0nI0UyRTJGMCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBhdGggZD0nTTk4My41LDI5IEM5ODMuNSwzOSAxMDAxLjUsMzkgMTAwMS41LDM5IEMxMDAxLjUsMzkgMTAxOS41LDM5IDEwMTkuNSwyOSAnIGZpbGw9J25vbmUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg5JyB4PSc5NTQnIHk9JzcyNC45OTk5Jz5Mb2FuIGJhbGFuY2U8L3RleHQ+PHBhdGggZD0nTTk4My41LDczOS4xMDE5IEM5ODMuNSw3MjkuMTAxOSAxMDAxLjUsNzI5LjEwMTkgMTAwMS41LDcyOS4xMDE5IEMxMDAxLjUsNzI5LjEwMTkgMTAxOS41LDcyOS4xMDE5IDEwMTkuNSw3MzkuMTAxOSBMMTAxOS41LDc2NS4xMDE5IEMxMDE5LjUsNzc1LjEwMTkgMTAwMS41LDc3NS4xMDE5IDEwMDEuNSw3NzUuMTAxOSBDMTAwMS41LDc3NS4xMDE5IDk4My41LDc3NS4xMDE5IDk4My41LDc2NS4xMDE5IEw5ODMuNSw3MzkuMTAxOSAnIGZpbGw9JyNFMkUyRjAnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS41OycvPjxwYXRoIGQ9J005ODMuNSw3MzkuMTAxOSBDOTgzLjUsNzQ5LjEwMTkgMTAwMS41LDc0OS4xMDE5IDEwMDEuNSw3NDkuMTAxOSBDMTAwMS41LDc0OS4xMDE5IDEwMTkuNSw3NDkuMTAxOSAxMDE5LjUsNzM5LjEwMTkgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuNTsnLz48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzUyLjEzNTgnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzkwJyB4PScxMDU5JyB5PSczMC45MzIxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzYnIHg9JzEwNjYnIHk9JzUyLjg5OCc+QWNjb3VudGluZzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2NScgeD0nMTA3MS41JyB5PSc3MS45NjU5Jz5Qcm9jZXNzb3I8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSc1Mi4xMzU4JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPSc5MCcgeD0nMTA1OScgeT0nNzEwLjAzNCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzc2JyB4PScxMDY2JyB5PSc3MzEuOTk5OSc+QWNjb3VudGluZzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2NScgeD0nMTA3MS41JyB5PSc3NTEuMDY3OCc+UHJvY2Vzc29yPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzI2LjUsMTEzLjc3MzksMzM2LjUsMTE3Ljc3MzksMzI2LjUsMTIxLjc3MzksMzMwLjUsMTE3Ljc3MzknIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM4LjUnIHgyPSczMzIuNScgeTE9JzExNy43NzM5JyB5Mj0nMTE3Ljc3MzknLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMjQnIHg9JzQ1LjUnIHk9JzExMS45NjQ5Jz5QT1NUIC4uLj9jb21tYW5kPXJlY292ZXJ5UGF5bWVudDwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU2OS41LDE0NS40Nzk5LDU3OS41LDE0OS40Nzk5LDU2OS41LDE1My40Nzk5LDU3My41LDE0OS40Nzk5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMzguNScgeDI9JzU3NS41JyB5MT0nMTQ5LjQ3OTknIHkyPScxNDkuNDc5OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIxOScgeD0nMzQ1LjUnIHk9JzE0My42NzA5Jz5yZWNvdmVyeVBheW1lbnQobG9hbklkLCBjb21tYW5kKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9Jzg3Ny41LDE3Ny4xODYsODg3LjUsMTgxLjE4Niw4NzcuNSwxODUuMTg2LDg4MS41LDE4MS4xODYnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU4MS41JyB4Mj0nODgzLjUnIHkxPScxODEuMTg2JyB5Mj0nMTgxLjE4NicvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1NicgeD0nNTg4LjUnIHk9JzE3NS4zNzcnPnZhbGlkYXRlUmVjb3ZlcnlQYXltZW50PC90ZXh0PjxwYXRoIGQ9J00xMCwxOTYuMTg2IEw3MywxOTYuMTg2IEw3MywyMDUuODkyIEw2MywyMTUuODkyIEwxMCwyMTUuODkyIEwxMCwxOTYuMTg2ICcgZmlsbD0nI0VFRUVFRScgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjU7Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyOTQuNjExOScgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjU7JyB3aWR0aD0nMTE0OScgeD0nMTAnIHk9JzE5Ni4xODYnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTgnIHg9JzI1JyB5PScyMTEuMDgzJz5hbHQ8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTEnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3OScgeD0nODgnIHk9JzIwOS45NDQ5Jz5bbG9hbiBub3QgQ0xPU0VEX1dSSVRURU5fT0ZGXTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzQ5LjUsMjM1LjU5OCwzOS41LDIzOS41OTgsNDkuNSwyNDMuNTk4LDQ1LjUsMjM5LjU5OCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzQzLjUnIHgyPSc4ODguNScgeTE9JzIzOS41OTgnIHkyPScyMzkuNTk4Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjMyJyB4PSc1NS41JyB5PScyMzMuNzg5Jz40MDAgZXJyb3IubXNnLndjLmxvYW4uaXMubm90LndyaXR0ZW4ub2ZmPC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPScxMCcgeDI9JzExNTknIHkxPScyNDguNTk4JyB5Mj0nMjQ4LjU5OCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBmb250LXdlaWdodD0nYm9sZCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxOTEnIHg9JzE1JyB5PScyNjAuMzU2OSc+W2Ftb3VudCAmZ3Q7IHdyaXR0ZW5PZmZPdXRzdGFuZGluZ108L3RleHQ+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSc0OS41LDI4NC4yODU5LDM5LjUsMjg4LjI4NTksNDkuNSwyOTIuMjg1OSw0NS41LDI4OC4yODU5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDtzdHJva2UtZGFzaGFycmF5OjIuMCwyLjA7JyB4MT0nNDMuNScgeDI9Jzg4OC41JyB5MT0nMjg4LjI4NTknIHkyPScyODguMjg1OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzM0MicgeD0nNTUuNScgeT0nMjgyLjQ3NjknPjQwMCBjYW5ub3QuYmUuZ3JlYXRlci50aGFuLnJlbWFpbmluZy53cml0dGVuLm9mZi5hbW91bnQ8L3RleHQ+PGxpbmUgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzEwJyB4Mj0nMTE1OScgeTE9JzI5Ny4yODU5JyB5Mj0nMjk3LjI4NTknLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzQnIHg9JzE1JyB5PSczMDkuMDQ0OCc+W3ZhbGlkXTwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1ODEuNScgeDI9JzYyMy41JyB5MT0nMzM2Ljk3MzgnIHkyPSczMzYuOTczOCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYyMy41JyB4Mj0nNjIzLjUnIHkxPSczMzYuOTczOCcgeTI9JzM0OS45NzM4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTgyLjUnIHgyPSc2MjMuNScgeTE9JzM0OS45NzM4JyB5Mj0nMzQ5Ljk3MzgnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU5Mi41LDM0NS45NzM4LDU4Mi41LDM0OS45NzM4LDU5Mi41LDM1My45NzM4LDU4OC41LDM0OS45NzM4JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOTQnIHg9JzU4OC41JyB5PSczMzEuMTY0OCc+Y3JlYXRlIFJFQ09WRVJZX1JFUEFZTUVOVCB0eG4gKG5vIGFsbG9jYXRpb24pPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nOTg5LjUsMzc3LjY3OTgsOTk5LjUsMzgxLjY3OTgsOTg5LjUsMzg1LjY3OTgsOTkzLjUsMzgxLjY3OTgnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU4MS41JyB4Mj0nOTk1LjUnIHkxPSczODEuNjc5OCcgeTI9JzM4MS42Nzk4Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTU5JyB4PSc1ODguNScgeT0nMzc1Ljg3MDgnPnRvdGFsUmVjb3ZlcmVkICs9IGFtb3VudDwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzEwOTIsNDA5LjM4NTgsMTEwMiw0MTMuMzg1OCwxMDkyLDQxNy4zODU4LDEwOTYsNDEzLjM4NTgnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU4MS41JyB4Mj0nMTA5OCcgeTE9JzQxMy4zODU4JyB5Mj0nNDEzLjM4NTgnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNTQnIHg9JzU4OC41JyB5PSc0MDcuNTc2OCc+RHIgRnVuZCBTb3VyY2UgLyBDciBJbmNvbWUgZnJvbSBSZWNvdmVyeTwvdGV4dD48cGF0aCBkPSdNNDY0LDQyNi4zODU4IEw0NjQsNDUzLjM4NTggTDY5OCw0NTMuMzg1OCBMNjk4LDQzNi4zODU4IEw2ODgsNDI2LjM4NTggTDQ2NCw0MjYuMzg1OCAnIGZpbGw9JyNGRUZGREQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J002ODgsNDI2LjM4NTggTDY4OCw0MzYuMzg1OCBMNjk4LDQzNi4zODU4IEw2ODgsNDI2LjM4NTggJyBmaWxsPScjRkVGRkREJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMTMnIHg9JzQ3MCcgeT0nNDQ1LjI4MjknPnN0YXR1cyBzdGF5cyBDTE9TRURfV1JJVFRFTl9PRkY8L3RleHQ+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSc0OS41LDQ3OC43OTc5LDM5LjUsNDgyLjc5NzksNDkuNSw0ODYuNzk3OSw0NS41LDQ4Mi43OTc5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDtzdHJva2UtZGFzaGFycmF5OjIuMCwyLjA7JyB4MT0nNDMuNScgeDI9JzU4MC41JyB5MT0nNDgyLjc5NzknIHkyPSc0ODIuNzk3OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIxJyB4PSc1NS41JyB5PSc0NzYuOTg4OSc+MjAwPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzI2LjUsNTE3LjUwMzksMzM2LjUsNTIxLjUwMzksMzI2LjUsNTI1LjUwMzksMzMwLjUsNTIxLjUwMzknIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM4LjUnIHgyPSczMzIuNScgeTE9JzUyMS41MDM5JyB5Mj0nNTIxLjUwMzknLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNzYnIHg9JzQ1LjUnIHk9JzUxNS42OTQ5Jz5QT1NUIC4uLi90cmFuc2FjdGlvbnMve3R4bklkfT9jb21tYW5kPXVuZG88L3RleHQ+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSc1NjkuNSw1NDkuMjA5OSw1NzkuNSw1NTMuMjA5OSw1NjkuNSw1NTcuMjA5OSw1NzMuNSw1NTMuMjA5OScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzM4LjUnIHgyPSc1NzUuNScgeTE9JzU1My4yMDk5JyB5Mj0nNTUzLjIwOTknLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNDEnIHg9JzM0NS41JyB5PSc1NDcuNDAwOSc+dW5kb1JlY292ZXJ5UGF5bWVudDwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1ODEuNScgeDI9JzYyMy41JyB5MT0nNTg0LjkxNTknIHkyPSc1ODQuOTE1OScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYyMy41JyB4Mj0nNjIzLjUnIHkxPSc1ODQuOTE1OScgeTI9JzU5Ny45MTU5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTgyLjUnIHgyPSc2MjMuNScgeTE9JzU5Ny45MTU5JyB5Mj0nNTk3LjkxNTknLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU5Mi41LDU5My45MTU5LDU4Mi41LDU5Ny45MTU5LDU5Mi41LDYwMS45MTU5LDU4OC41LDU5Ny45MTU5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2NycgeD0nNTg4LjUnIHk9JzU3OS4xMDY5Jz5yZXZlcnNlIHR4bjwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9Jzk4OS41LDYyNS42MjE5LDk5OS41LDYyOS42MjE5LDk4OS41LDYzMy42MjE5LDk5My41LDYyOS42MjE5JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1ODEuNScgeDI9Jzk5NS41JyB5MT0nNjI5LjYyMTknIHkyPSc2MjkuNjIxOScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1NicgeD0nNTg4LjUnIHk9JzYyMy44MTI5Jz50b3RhbFJlY292ZXJlZCAtPSBhbW91bnQ8L3RleHQ+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScxMDkyLDY1Ny4zMjgsMTEwMiw2NjEuMzI4LDEwOTIsNjY1LjMyOCwxMDk2LDY2MS4zMjgnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU4MS41JyB4Mj0nMTA5OCcgeTE9JzY2MS4zMjgnIHkyPSc2NjEuMzI4Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nODInIHg9JzU4OC41JyB5PSc2NTUuNTE5Jz5taXJyb3IgZW50cmllczwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzQ5LjUsNjg5LjAzNCwzOS41LDY5My4wMzQsNDkuNSw2OTcuMDM0LDQ1LjUsNjkzLjAzNCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzQzLjUnIHgyPSc1ODAuNScgeTE9JzY5My4wMzQnIHkyPSc2OTMuMDM0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjEnIHg9JzU1LjUnIHk9JzY4Ny4yMjUnPjIwMDwvdGV4dD48L2c+PC9zdmc+)

Figure 13. Recovery payment and reversal flow

#### Validation Rules

A recovery payment can be applied only if:

* Loan status is **Closed (written-off)**.

A recovery payment can be reversed only if:

* Loan status is still **Closed (written-off)**, and the transaction is not already reversed.

##### Recovery Payment Date

`transactionDate` is **required**. It may be backdated, with the same two bounds Write-Off and Charge-Off apply:

* It must not be in the future.
* It must not be earlier than the last user transaction date.

Because the write-off is itself a user transaction, the lower bound also prevents a recovery from being dated before the write-off that made it possible â no separate check is needed.

##### Recovery Payment Amount

`transactionAmount` is **required** and must be positive. It is capped by `writtenOffOutstanding` â what is **still** recoverable â and not by the gross amount written off.

> [!IMPORTANT]
> This is a deliberate divergence from term and progressive loans, which cap each recovery against the gross written-off figure. Because that figure is never reduced by the recoveries collected against it, successive recoveries can each pass validation on their own and together collect more than the loss that was booked. Working Capital compares against the remaining amount instead, so the recoveries can never add up past the loss.

| **Operation** | **Rule** | **Error code** |
| --- | --- | --- |
| Recovery payment | The loan must be written off. | `error.msg.wc.loan.is.not.written.off` |
| Recovery payment | The transaction date is required. | `validation.msg.WORKINGCAPITALLOAN.transactionDate.cannot.be.blank` |
| Recovery payment | The transaction date must not be in the future. | `cannot.be.a.future.date` |
| Recovery payment | The transaction date must not be earlier than the last user transaction date. | `cannot.be.before.last.transaction.date` |
| Recovery payment | The amount is required and must be positive. | `validation.msg.WORKINGCAPITALLOAN.transactionAmount.cannot.be.blank` |
| Recovery payment | The amount must not exceed what is still recoverable. | `cannot.be.greater.than.remaining.written.off.amount` |
| Undo recovery payment | The transaction must not be already reversed. | `transaction.already.undone` |
| Undo recovery payment | The loan must still be written off. | `error.msg.wc.loan.is.not.written.off` |
| Undo recovery payment | `totalRecovered` must cover the amount being reversed; a smaller running total means the balance row was repaired or migrated inconsistently, and the undo fails rather than silently clamping the figure at zero. | `error.msg.wc.loan.total.recovered.less.than.reversed.amount` |

A repayment classification (`classificationId`) is **not** accepted: a recovery carries no allocation, so there is nothing to classify, and silently ignoring the parameter would hide the mistake.

##### Interaction with the post-write-off lock

A written-off Working Capital Loan is otherwise locked â no transaction can be posted and none can be undone. The recovery payment is the single exception, and it is a **typed** one: the hole is opened for the `RECOVERY_REPAYMENT` transaction type coming from `CLOSED_WRITTEN_OFF`, not by relaxing the status gates that guard repayment, goodwill credit, payout refund, charge adjustment or the generic transaction undo. Those gates are unchanged and still reject a written-off loan.

##### Undoing the write-off while a recovery stands

Undo Write-Off is **rejected** while any recovery payment is outstanding.

Undoing the write-off restores the full outstanding balance. The recovered cash, however, stays booked as recovery income and would then also be replayed against that restored balance â the same money both recognized as income and reducing the receivable. The recoveries must therefore be reversed first, which is exactly what the undo recovery payment is for.

| **Operation** | **Rule** | **Error code** |
| --- | --- | --- |
| Undo write-off | No recovery payment may be outstanding (`totalRecovered` must be zero). | `cannot.undo.write.off.with.recovery.payments` |

#### Transaction Template

The transaction template pre-fills the amount with what is **still** recoverable, so the value it offers is always one the API accepts:

```java
GET /v1/working-capital-loans/{loanId}/template?templateType=recoveryPayment
```

`expectedAmount` returns `writtenOffOutstanding`. On a loan written off for 100 with 30 already recovered, the template offers 70 â not the gross 100, which the API would reject.

#### API

```java
POST /v1/working-capital-loans/{loanId}/transactions?command=recoveryPayment
POST /v1/working-capital-loans/{loanId}/transactions/{transactionId}?command=undo
```

```json
{
  "transactionDate": "20 January 2026",
  "transactionAmount": 40,
  "externalId": "WC-RP-001",
  "dateFormat": "dd MMMM yyyy",
  "locale": "en",
  "note": "Partial collection after write-off",
  "paymentDetails": {
    "paymentTypeId": 1,
    "accountNumber": "ACC-001"
  }
}
```

```json
{
  "reversalExternalId": "WC-RP-REV-001",
  "note": "Captured in error",
  "locale": "en"
}
```

#### Read Model

The Working Capital Loan balance exposes the written-off and recovered figures, so a client can reconcile the zeroed outstanding and explain a rejected amount:

| **Field** | **Description** |
| --- | --- |
| `totalWrittenOff` | Gross amount the write-off moved out of the outstanding. Not reduced by recoveries. |
| `principalWrittenOff`, `feeWrittenOff`, `penaltyWrittenOff` | The same figure split by portion. `principalOutstanding` and its siblings already net these off, so without them the exposed balance cannot be reconciled: a written-off loan reports a gross principal and a zero outstanding with nothing in between to explain the difference. |
| `totalRecovered` | Running total collected after the write-off and recognized as recovery income. |
| `writtenOffOutstanding` | Still recoverable (`totalWrittenOff - totalRecovered`). Caps the next recovery payment and is what the transaction template offers. |

#### Accounting Treatment

A Recovery Payment triggers Journal Entries (JE) when the Working Capital Loan product uses accrual with deferred revenue amortization accounting. The portfolio and receivable accounts were already relieved by the write-off, so there is nothing to credit back: the whole amount is recognized as income against the fund source, with no split by portion.

##### Recovery Payment

| **Type** | **WCP mapping name** | **GL type** | **Allocation** |
| --- | --- | --- | --- |
| Dr | Fund Source | Asset/Liability | Excess amount |
| Cr | Income from Recovery | Income | Excess amount |

##### Undo Recovery Payment

Undo posts an offsetting mirror for each entry above (the ledger stays append-only), which nets the recovery to zero:

| **Type** | **WCP mapping name** | **GL type** | **Allocation** |
| --- | --- | --- | --- |
| Dr | Income from Recovery | Income | Excess amount |
| Cr | Fund Source | Asset/Liability | Excess amount |

> [!NOTE]
> Do not confuse this with a **repayment posted after a charge-off**. That transaction is a real repayment: it moves the balance and is credited to Income from Recovery **by portion**, because a charge-off is a non-monetary tag that leaves the receivable on the books. A recovery payment on a written-off loan moves no balance and books a single line.

#### Business Events

* `WorkingCapitalLoanRecoveryPaymentTransactionBusinessEvent` â emitted after a recovery payment.
* `WorkingCapitalLoanAdjustTransactionBusinessEvent` â emitted alongside the undo event, mirroring the other transaction reversals, so a consumer reconciling reversals generically does not miss recovery ones.

Neither operation emits a balance-changed or status-changed event: the outstanding balance stays at zero and the loan stays in `CLOSED_WRITTEN_OFF` throughout.

#### Permissions

| **Permission** | **Grouping** | **Entity** | **Action** |
| --- | --- | --- | --- |
| `RECOVERYPAYMENT_WORKINGCAPITALLOAN` | `transaction_loan` | `WORKINGCAPITALLOAN` | `RECOVERYPAYMENT` |

The reversal is guarded by the shared transaction-undo permission `UNDO_WORKINGCAPITALLOANTRANSACTION`
(grouping `transaction_loan`, entity `WORKINGCAPITALLOANTRANSACTION`, action `UNDO`), the same permission that
guards the reversal of a repayment, goodwill credit, payout refund or charge adjustment. No permission specific
to the recovery payment reversal exists.

### Working Capital Product Delinquency Management

#### Overview

Delinquency management for Working Capital Loans provides a dedicated, schedule-based framework to track minimum payment compliance, classify loans into configurable delinquency ranges, and apply corrective actions such as pauses and reschedules. Unlike the standard loan delinquency model â which is installment-driven â the Working Capital model operates on rolling time **periods**, each with its own expected minimum payment that must be met before the period’s end date is reached.

The feature is implemented in the `fineract-working-capital-loan` module and is activated through the Working Capital COB (Close of Business) pipeline.

##### Purpose

This feature enables credit operations teams to:

* Automatically detect and classify overdue minimum payment obligations per time period.
* Assign delinquency range tags (e.g., 5â15 days, 15â30 days) per period, independently of other periods.
* Temporarily pause delinquency evaluation during agreed grace windows.
* Reschedule the minimum payment amount and/or frequency on active loans.

##### Scope

The scope of this document includes:

* Product-level delinquency configuration (grace days, stored start type)
* Delinquency bucket and minimum payment rule configuration (`m_wc_delinquency_configuration`)
* Delinquency range schedule â generation and lifecycle (`m_wc_loan_delinquency_range_schedule`)
* Per-period delinquency range tagging (`m_wc_loan_range_delinquency_tag`)
* Delinquency actions: PAUSE and RESCHEDULE (`m_wc_loan_delinquency_action`)
* COB business steps that drive the delinquency pipeline
* API endpoints for actions and schedule retrieval

##### Applicability

* Active Working Capital Loan accounts only.
* Loans whose product has a delinquency bucket configured.
* Loans that have at least one actual disbursement recorded.

##### Definitions and Key Concepts

**Delinquency Range Schedule Period:** A time window (identified by a sequential `periodNumber`) over which the system tracks whether the loan met its minimum payment obligation. Each period has `fromDate`, `toDate`, `expectedAmount`, `paidAmount`, and `outstandingAmount`.

**Minimum Payment Criteria Met (`minPaymentCriteriaMet`):** A boolean flag set when a period is evaluated after its `toDate`. It is `true` if `paidAmount >= expectedAmount`, `false` otherwise, and `null` while the period is open (not yet expired).

**Delinquency Range Tag:** A tag derived from the bucket’s configured ranges (e.g., `5â15 days overdue`) applied per period. The system records a history of tag additions and lifts in `m_wc_loan_range_delinquency_tag`.

**Delinquency Start Type:** Stored on the product and copied to the loan. The current range schedule generation anchors the first period to the first actual disbursement date.

**Delinquency Grace Days:** A product-level integer that is copied to the loan at origination. The COB classification step adds this number of days when determining whether a period is overdue relative to the business date.

**PAUSE Action:** A loan-level action that extends all open and future schedule periods by the duration of the pause, effectively freezing the delinquency clock during the pause window.

**RESCHEDULE Action:** A loan-level action that modifies the minimum payment amount and/or frequency for the current open period and all future unevaluated periods.

**RESUME Action:** A loan-level action that ends an active pause early, on the resume date. The days the pause no longer covers are taken back out of the periods the pause had extended.

**RESET Action:** A loan-level action that marks every period ending before the reset date as `reset`, lifting its delinquency tags and taking it out of evaluation and repayment allocation. With `startNewPeriod = true` it also cuts the current period on the day before the reset date and starts a new period on the reset date itself.

**UNDO_RESET Action:** A loan-level action that closes the latest active reset and clears the `reset` flag on the periods it had flagged, so they are evaluated again. Period dates are left as they are.

#### Design Decisions and Considerations

##### Period-Level Delinquency, Not Loan-Level

Working Capital loans use a period-based delinquency model rather than the standard installment-based model. Each period is an independently evaluated unit. A loan can have some periods marked delinquent while other periods remain current, which reflects the revolving, cash-flow-oriented nature of working capital credit.

##### PAUSE Extends Periods, Not Skips Them

When a PAUSE action is recorded, all open and future schedule periods are extended by the exact number of days of the pause (`ChronoUnit.DAYS.between(pauseStart, pauseEnd)`). This preserves the expected minimum payment schedule while giving the borrower extra time. The pause is applied immediately when the action is created via API â it does not wait for the next COB run.

##### The Reset Date Is a Hard Boundary for Pauses

A reset with `startNewPeriod = true` can be recorded while a pause is active. The period it starts begins on the reset date even though that date is inside the pause: only the pause days from the reset date on extend it, while the earlier pause days stay with the period the reset cut. Without this rule the restarted period would be moved past the whole pause and the days in between would belong to no period, so a repayment dated there could not be allocated anywhere. The same rule holds when that pause is later resumed and when the restarted period is rescheduled. It keeps holding after the reset is undone: unlike breach, a delinquency undo does not merge the cut period back, so the boundary stays in the schedule and stays protected. It is the rule the breach schedule applies, implemented once in `WorkingCapitalLoanPausePeriodUtils` so the two schedules cannot drift.

##### RESCHEDULE Applies Forward-Only

A RESCHEDULE action modifies only the current open period and future unevaluated periods. Periods already evaluated (`minPaymentCriteriaMet != null`) are never modified. This ensures historical accuracy of delinquency reporting.

##### Classification Uses Business Date + 1

The `WorkingCapitalLoanDelinquencyClassificationBusinessStep` classifies delinquency using `businessDate + 1` to evaluate periods whose `toDate` is strictly before the adjusted date, aligning with the convention that a period ending on day D is evaluated on day D+1.

#### Database Design

##### Overview

The delinquency subsystem for Working Capital loans introduces three dedicated tables, and extends the product and loan entities with configuration columns. It reuses the standard `m_delinquency_bucket` and `m_delinquency_range` tables from the core loan module.

##### Existing Tables (Referenced)

**m_delinquency_bucket**: The delinquency bucket assigned to the Working Capital loan product. Defines which ranges are applicable.

**m_delinquency_range**: The individual delinquency ranges inside a bucket (e.g., 5â15 days, 15â30 days). Used for tagging periods.

##### Changes to Existing Tables

###### m_wc_loan_product and m_wc_loan

New columns added by migrations `0013_add_delinquency_grace_days_to_wc_loan.xml`:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `delinquency_grace_days` | INT | nullable | Number of days after a period’s `toDate` before the period is considered delinquent |
| `delinquency_start_type` | VARCHAR(20) | nullable | Enum: `LOAN_CREATION` or `DISBURSEMENT` â determines the anchor date for the first period |

##### Table: m_wc_delinquency_configuration

The `m_wc_delinquency_configuration` table stores the minimum payment rule associated with a delinquency bucket. There is exactly one configuration per bucket (unique constraint on `bucket_id`).

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, not null | Primary key |
| `bucket_id` | BIGINT | FK to `m_delinquency_bucket`, unique, not null | The delinquency bucket this configuration applies to |
| `frequency` | INT | not null | Numeric frequency value for the period duration |
| `frequency_type` | VARCHAR(50) | not null | Enum: `DAYS`, `WEEKS`, `MONTHS`, `YEARS` |
| `minimum_payment` | DECIMAL(19,6) | not null | Minimum payment amount or percentage |
| `minimum_payment_type` | VARCHAR(50) | not null | Enum: `PERCENTAGE`, `FLAT` |
| `created_by` | BIGINT | not null | Audit field |
| `created_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| `last_modified_by` | BIGINT | not null | Audit field |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

##### Table: m_wc_loan_delinquency_range_schedule

The `m_wc_loan_delinquency_range_schedule` table stores one row per rolling period per loan. Periods are generated dynamically during COB processing.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, not null | Primary key |
| `wc_loan_id` | BIGINT | FK to `m_wc_loan`, not null | Associated Working Capital loan |
| `period_number` | INT | not null | Sequential period number (1-based); unique with `wc_loan_id` |
| `version` | INT | not null, default 0 | Optimistic locking version |
| `from_date` | DATE | not null | Start date of the period (inclusive) |
| `to_date` | DATE | not null | End date of the period (inclusive). Extended by pause actions. |
| `expected_amount` | DECIMAL(19,6) | nullable | Minimum payment required for this period |
| `paid_amount` | DECIMAL(19,6) | nullable | Total amount paid toward this period |
| `outstanding_amount` | DECIMAL(19,6) | nullable | Remaining unpaid amount (`expected_amount - paid_amount`) |
| `min_payment_criteria_met` | BOOLEAN | nullable | `null` = open; `true` = criteria met; `false` = criteria not met (delinquent) |
| `delinquent_days` | BIGINT | nullable | Number of days past due for this period, as calculated at last COB run |
| `delinquent_amount` | DECIMAL(19,6) | nullable | Outstanding amount classified as delinquent for this period |
| `created_by` | BIGINT | not null | Audit field |
| `created_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| `last_modified_by` | BIGINT | not null | Audit field |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

##### Table: m_wc_loan_range_delinquency_tag

The `m_wc_loan_range_delinquency_tag` table records the history of delinquency range assignments per period. A new row is inserted when a period enters a range, and `liftedon_date` is set when the period exits the range.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, not null | Primary key |
| `loan_id` | BIGINT | FK to `m_wc_loan`, not null | Associated Working Capital loan |
| `range_id` | BIGINT | FK to `m_wc_loan_delinquency_range_schedule`, not null | The range schedule period this tag belongs to |
| `delinquency_range_id` | BIGINT | FK to `m_delinquency_range`, not null | The delinquency range classification (e.g., 5â15 days) |
| `addedon_date` | DATE | not null | Business date when this tag was applied |
| `liftedon_date` | DATE | nullable | Business date when this tag was lifted (null = still active) |
| `outstanding_amount` | DECIMAL(19,6) | nullable | Outstanding amount at time of tagging |
| `version` | BIGINT | nullable | Optimistic locking version |
| `created_by` | BIGINT | not null | Audit field |
| `created_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| `last_modified_by` | BIGINT | not null | Audit field |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

##### Table: m_wc_loan_delinquency_action

The `m_wc_loan_delinquency_action` table stores loan-level delinquency control actions: PAUSE, RESUME, RESCHEDULE, RESET and UNDO_RESET (DISABLE and ENABLE are covered in the delinquency disable chapter).

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, not null | Primary key |
| `wc_loan_id` | BIGINT | FK to `m_wc_loan`, not null | Associated Working Capital loan |
| `action` | VARCHAR(128) | not null | Enum: `PAUSE`, `RESUME`, `RESCHEDULE`, `RESET`, `UNDO_RESET`, `DISABLE`, `ENABLE` |
| `start_date` | DATE | not null | Effective start date of the action |
| `end_date` | DATE | nullable | PAUSE: end date of the pause window (mandatory). RESET: set to the undo date when the reset is undone; `null` while the reset is active |
| `start_new_period` | BOOLEAN | nullable | RESET only: `true` when the reset also starts a new period on the reset date |
| `minimum_payment` | DECIMAL(19,6) | nullable | New minimum payment value (RESCHEDULE only) |
| `minimum_payment_type` | VARCHAR(50) | nullable | Enum: `PERCENTAGE`, `FLAT` (RESCHEDULE only) |
| `frequency` | INT | nullable | New period frequency value (RESCHEDULE only) |
| `frequency_type` | VARCHAR(50) | nullable | Enum: `DAYS`, `WEEKS`, `MONTHS`, `YEARS` (RESCHEDULE only) |
| `created_by` | BIGINT | not null | Audit field |
| `created_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| `last_modified_by` | BIGINT | not null | Audit field |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

#### Configuration

##### Product-Level Delinquency Configuration

Working Capital loan products support two delinquency configuration fields:

| Field | Type | Description |
| --- | --- | --- |
| `delinquencyGraceDays` | Integer | Number of days after a period’s end before delinquency is triggered. Default: 0. |
| `delinquencyStartType` | Enum | Determines the anchor date for the first period: `LOAN_CREATION` or `DISBURSEMENT`. |

The product must also reference a **Delinquency Bucket** (`m_delinquency_bucket`). Without a bucket, COB steps skip delinquency processing for the loan.

##### Delinquency Bucket Minimum Payment Rule

Each delinquency bucket used with Working Capital loans must have an entry in `m_wc_delinquency_configuration` specifying the default minimum payment rule:

```json
{
  "frequency": 30,                // period length
  "frequencyType": "DAYS",        // DAYS | WEEKS | MONTHS | YEARS
  "minimumPayment": 5.0,          // percentage or flat amount
  "minimumPaymentType": "PERCENTAGE"  // PERCENTAGE | FLAT
}
```

> [!NOTE]
> When `minimumPaymentType` is `PERCENTAGE`, the base amount is the loan’s approved principal plus the loan discount, if a discount is configured. When `FLAT`, the `minimumPayment` value is used directly. A Discount Fee added after disbursement recalculates the expected amount of the period covering the business date and of later periods; periods that have already ended keep theirs.

##### System Configuration

The global configuration flag `enable-instant-delinquency-calculation` (table `c_configuration`) controls whether delinquency classification runs immediately after repayment-like monetary transactions in addition to the scheduled COB run. When enabled, the payment is first applied to the range schedule and then classification is recalculated for the transaction date when the loan has a delinquency bucket.

#### COB Pipeline

Delinquency processing for Working Capital loans is part of the `WORKING_CAPITAL_LOAN_CLOSE_OF_BUSINESS` batch job, executed in two sequential business steps:

| Step Order | Step Name | Description |
| --- | --- | --- |
| 3 | `WC_DELINQUENCY_RANGE_SCHEDULE` | Generates the initial period on first run, advances to the next period when needed, and evaluates all expired periods (sets `minPaymentCriteriaMet`). |
| 4 | `WC_LOAN_DELINQUENCY_CLASSIFICATION` | Iterates over all periods whose `toDate < businessDate + 1` and assigns or lifts delinquency range tags based on the configured bucket ranges. |

Step 3 (`DelinquencyRangeScheduleBusinessStep`) is skipped for loans that have not yet been disbursed. If no delinquency bucket or minimum payment rule exists, no schedule period is generated. Step 4 (`WorkingCapitalLoanDelinquencyClassificationBusinessStep`) is skipped when no delinquency bucket is configured on the product.

#### API Design

##### Delinquency Actions

###### Create Delinquency Action

Creates a delinquency action â PAUSE, RESUME, RESCHEDULE, RESET or UNDO_RESET â for an active Working Capital loan.

```java
POST /v1/working-capital-loans/{loanId}/delinquency-actions
POST /v1/working-capital-loans/external-id/{loanExternalId}/delinquency-actions
```

**Required permission**: `CREATE_WC_DELINQUENCY_ACTION`

**Request Body â PAUSE:**

```json
{
  "action": "pause",
  "startDate": "2024-03-01",      // mandatory â must be after first disbursement date
  "endDate": "2024-03-15",        // mandatory â must be after startDate
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

**Request Body â RESCHEDULE:**

```json
{
  "action": "reschedule",
  "minimumPayment": 3.5,              // optional â new minimum payment value (> 0)
  "minimumPaymentType": "PERCENTAGE", // mandatory if minimumPayment is provided: PERCENTAGE | FLAT
  "frequency": 14,                    // optional â new period frequency (> 0)
  "frequencyType": "DAYS",            // mandatory if frequency is provided: DAYS | WEEKS | MONTHS | YEARS
  "locale": "en"
}
```

> [!NOTE]
> For RESCHEDULE, at least one of the payment group (`minimumPayment` + `minimumPaymentType`) or frequency group (`frequency` + `frequencyType`) must be provided. Both groups can be supplied in the same request.

**Request Body â RESUME:**

```json
{
  "action": "resume",
  "startDate": "2024-03-10",      // mandatory â must be the business date, inside an active pause
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

**Request Body â RESET:**

```json
{
  "action": "reset",
  "startDate": "2024-03-10",      // optional â defaults to the business date and must equal it
  "startNewPeriod": true,         // optional â also cut the current period and start a new one on the reset date
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

**Request Body â UNDO_RESET:**

```json
{
  "action": "undo_reset",
  "startDate": "2024-03-12",      // optional â defaults to the business date and must equal it
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

**Response:**

```json
{
  "officeId": 1,
  "clientId": 42,
  "loanId": 100,
  "resourceId": 15
}
```

The `resourceId` contains the ID of the created `m_wc_loan_delinquency_action` record.

###### Retrieve Delinquency Actions

Retrieves all delinquency actions recorded for a Working Capital loan, ordered by creation.

```java
GET /v1/working-capital-loans/{loanId}/delinquency-actions
GET /v1/working-capital-loans/external-id/{loanExternalId}/delinquency-actions
```

**Required permission**: `READ_WC_DELINQUENCY_ACTION`

**Response:**

```json
[
  {
    "id": 10,
    "action": "PAUSE",
    "startDate": "2024-03-01",
    "endDate": "2024-03-15",
    "minimumPayment": null,
    "minimumPaymentType": null,
    "frequency": null,
    "frequencyType": null
  },
  {
    "id": 11,
    "action": "RESCHEDULE",
    "startDate": "2024-04-01",
    "endDate": null,
    "minimumPayment": 3.5,
    "minimumPaymentType": "PERCENTAGE",
    "frequency": 14,
    "frequencyType": "DAYS"
  }
]
```

##### Delinquency Range Schedule

###### Retrieve Delinquency Range Schedule

Retrieves all range schedule periods for a Working Capital loan, ordered by `periodNumber`.

```java
GET /v1/working-capital-loans/{loanId}/delinquency-range-schedule
```

This endpoint is currently available by loan ID.

**Required permission**: `READ_WORKINGCAPITALLOAN`

**Response:**

```json
[
  {
    "id": 1,
    "loanId": 100,
    "periodNumber": 1,
    "fromDate": "2024-01-15",
    "toDate": "2024-02-14",
    "expectedAmount": 500.00,
    "paidAmount": 500.00,
    "outstandingAmount": 0.00,
    "minPaymentCriteriaMet": true,
    "delinquentDays": 0,
    "delinquentAmount": 0.00
  },
  {
    "id": 2,
    "loanId": 100,
    "periodNumber": 2,
    "fromDate": "2024-02-15",
    "toDate": "2024-03-15",
    "expectedAmount": 500.00,
    "paidAmount": 0.00,
    "outstandingAmount": 500.00,
    "minPaymentCriteriaMet": false,
    "delinquentDays": 10,
    "delinquentAmount": 500.00
  }
]
```

#### Validation Rules

##### General Rules

* Delinquency actions can only be created for **active** Working Capital loan accounts.
* `action` is mandatory; supported values are `pause`, `resume`, `reschedule`, `reset`, `undo_reset`, `disable` and `enable` (case-insensitive).
* PAUSE, RESUME, RESCHEDULE and RESET are rejected while delinquency evaluation is disabled for the loan.

##### Validation Rules for PAUSE

* Both `startDate` and `endDate` are mandatory.
* `startDate` must be strictly before `endDate` (pause must span at least one day).
* `startDate` must be on or after the first actual disbursement date of the loan.
* `startDate` must not fall within or before a period that has already been evaluated (`minPaymentCriteriaMet != null`).
* The pause period must not overlap with any existing PAUSE action for the same loan.
* `startDate` must not be before the start date of the latest active RESET, nor before the start date of a RESET with `startNewPeriod = true` that was undone: a pause cannot re-date periods a reset already settled, and an undo leaves the cut of a new-period reset in place. A pause starting on the reset date itself is accepted.

##### Validation Rules for RESUME

* `startDate` is mandatory and must equal the business date.
* A pause must be active on the business date and not resumed yet, and the resume date must be after that pause’s `startDate` and not after its `endDate`, so the resume actually shortens it.

##### Validation Rules for RESET and UNDO_RESET

* `startDate` is optional; when provided it must equal the business date, and it defaults to the business date otherwise.
* `startNewPeriod` is optional and only meaningful for RESET.
* A RESET may be recorded while a pause is active; see Effect of RESET on Schedule.

##### Validation Rules for RESCHEDULE

* The loan must have at least one actual disbursement recorded.
* An existing delinquency range schedule must exist for the loan.
* At least one of the payment group or the frequency group must be provided.
* If `minimumPayment` is provided, it must be greater than 0 and `minimumPaymentType` is mandatory.
* If `frequency` is provided, it must be greater than 0 and `frequencyType` is mandatory.

#### Business Rules

##### Period Generation

* The initial period is generated by `DelinquencyRangeScheduleBusinessStep` on the first COB run after disbursement, using the bucket’s minimum payment rule (`m_wc_delinquency_configuration`) to calculate `expectedAmount` and `toDate`.
* Subsequent periods are generated automatically when the previous period’s `toDate` is no longer in the future. Periods are generated with a while-loop until the latest period’s `toDate` is ahead of the business date.
* If a RESCHEDULE action has been recorded, the effective frequency and minimum payment for new periods are taken from the most recent RESCHEDULE action, overriding the bucket’s configuration.

##### Period Evaluation and Expiration

* At each COB run, all periods whose `toDate ⇐ businessDate` and `minPaymentCriteriaMet IS NULL` are evaluated.
* Evaluation checks: `paidAmount >= expectedAmount`. If true, `minPaymentCriteriaMet = true`; otherwise `minPaymentCriteriaMet = false`.

##### Repayment Allocation

* Repayment amounts are allocated first to the oldest open past-due periods, then to the current period.
* For each eligible past-due period, the allocation is `min(repaymentAmount, outstandingAmount)`.
* When a period’s `outstandingAmount` reaches zero, `minPaymentCriteriaMet` is immediately set to `true` and `delinquentAmount`/`delinquentDays` are cleared.

##### Delinquency Classification

* The classification step iterates over periods where `toDate < businessDate + 1`.
* Delinquent days for a period are calculated as the classification date minus `period.toDate` (only if `outstandingAmount > 0`). In COB this classification date is `businessDate + 1`.
* The applicable delinquency range is resolved from the bucket by finding the range where `minimumAgeDays ⇐ delinquentDays ⇐ maximumAgeDays`.
* If no range matches (e.g., the period is not overdue), any previously applied tags for that period are lifted.

##### Effect of PAUSE on Schedule

* When a PAUSE action is created, `extendPeriodsForPause` extends all open and future periods.
* For periods that have not yet started when the pause begins, both `fromDate` and `toDate` are shifted forward by the pause duration.
* For the period currently active when the pause begins (if the pause starts mid-period), only `toDate` is extended.
* Periods already evaluated are never modified.
* The pause is applied again, from the recorded actions, whenever a new period is generated: a period whose start falls inside a pause is moved past it, keeping its length, unless the period was started by a reset (see below).

##### Effect of RESUME on Schedule

* The pause effectively ends on the resume date. The days between the resume date and the planned pause end are removed again from every unevaluated period the pause had extended: `toDate` moves back for the period the pause started in and for the later ones, `fromDate` moves back for the periods that started after the pause.
* Periods already evaluated, and periods flagged by a reset, are never modified.

##### Effect of RESET on Schedule

* Every period that is not yet flagged and whose `toDate` is before the reset date gets `reset = true`: its amounts are cleared, its delinquency tags are lifted as of the reset date, and it is skipped by evaluation and by repayment allocation from then on.
* With `startNewPeriod = true` the period containing the reset date is cut so that it ends on the day before the reset date (and is flagged like the others), and the next period is generated starting on the reset date. A reset dated on the first day of that period cuts nothing. The period containing the reset date is usually the last one, but a pause recorded with a start date in an earlier, already generated period pushes the later periods past the business date; those periods have not started yet, so they are discarded and replaced by the period the reset starts.
* **Reset inside an active pause:** the restarted period keeps its start on the reset date. Only the pause days from the reset date on extend its `toDate`; the pause days before the reset stay with the cut period. A later RESUME of that pause shortens the restarted period from its end only, and a later RESCHEDULE of the restarted period counts the pause from the reset date in the same way. A pause recorded after the reset cannot start before it, so it never reaches the cut period.

##### Effect of UNDO_RESET on Schedule

* The latest active RESET gets its `end_date` set to the undo date.
* The `reset` flag is cleared on the periods ending before the undo date that the undone reset had flagged, bounded below by the start date of the previous still-active reset, if any.
* Period dates are not changed: a period the reset cut stays cut, and the period the reset started stays in place. The schedule is then reprocessed, replaying the repayments and re-evaluating the expired periods.
* Because the cut stays, the reset date remains a boundary for pauses after the undo: a later RESUME or RESCHEDULE still keeps the restarted period starting on the reset date, and a new PAUSE cannot start before it.

##### Effect of RESCHEDULE on Schedule

* `rescheduleMinimumPayment` modifies the current open period (not yet evaluated) and all future unevaluated periods.
* The current period’s `expectedAmount` is updated; `outstandingAmount` is recalculated as `max(0, expectedAmount - paidAmount)`.
* Future periods are recalculated from the day after the current period ends, applying the new frequency to determine new `fromDate`/`toDate` and the new `expectedAmount`.
* The most recent RESCHEDULE action (by ID) is always the effective override for future period calculations.

##### Independence from EIR Amortization

Delinquency management and EIR amortization are fully independent systems at the code level. `WorkingCapitalLoanDelinquencyRangeScheduleServiceImpl` has no dependency on `WorkingCapitalLoanAmortizationScheduleWriteService` and makes no call to `applyRateChange()`.

* A RESCHEDULE action updates only the delinquency period schedule; the amortization model retains its original EIR and payment amounts unchanged.
* EIR recalculation is triggered exclusively via `PUT /payment-rate`, which is a separate, manually initiated operation.
* A loan can therefore have its delinquency terms renegotiated (via RESCHEDULE) without altering how discount fee income is recognized, and vice-versa.

#### Example Scenarios

##### Scenario #1: Normal Delinquency Lifecycle

**Setup:**

* Loan disbursed on 2024-01-15, approved principal: 10,000
* Bucket configuration: 30-day periods, 5% minimum payment = 500 per period

**Period 1:** 2024-01-15 â 2024-02-14, expected: 500

* On 2024-02-01: borrower pays 500 â `paidAmount = 500`, `outstandingAmount = 0`, `minPaymentCriteriaMet = true` on period close.

**Period 2:** 2024-02-15 â 2024-03-16, expected: 500

* On 2024-03-17 (COB): period expires, `paidAmount = 0`, `minPaymentCriteriaMet = false`.
* Classification step: `delinquentDays = 1`, tag with range 1â5 days.
* On 2024-03-25 (COB): `delinquentDays = 9`, tag moves to range 5â15 days.

##### Scenario #2: PAUSE Extends Periods

**Setup:** Same loan as Scenario #1. Period 2 is active (2024-02-15 â 2024-03-16).

**PAUSE created:** startDate = 2024-03-01, endDate = 2024-03-15 (14 days).

**Effect:**

* Period 2 `toDate` extends from 2024-03-16 to 2024-03-30 (+ 14 days).
* Period 3 (if already generated) also shifts forward by 14 days.

The borrower now has until 2024-03-30 to meet the minimum payment before the period is evaluated.

##### Scenario #3: RESET With a New Period Inside an Active Pause

**Setup:** Bucket frequency 3 days, minimum payment 25 % of the principal; loan of 800 disbursed on `2026-01-01`. On `2026-01-08` the schedule holds period 1 `[2026-01-01 .. 2026-01-03]` and period 2 `[2026-01-04 .. 2026-01-06]`, both evaluated as not met, and the open period 3 `[2026-01-07 .. 2026-01-09]`.

**PAUSE created on `2026-01-08`:** startDate = `2026-01-08`, endDate = `2026-01-10` (3 days). Period 3 extends to `[2026-01-07 .. 2026-01-12]`.

**RESET with `startNewPeriod = true` on `2026-01-09`, while the pause is active:**

* Periods 1 and 2 are flagged `reset`.
* Period 3 is cut to `[2026-01-07 .. 2026-01-08]` and flagged `reset`.
* Period 4 starts on the reset date: 3 days from `2026-01-09` end on `2026-01-11`, extended by the pause days `2026-01-09` and `2026-01-10` only, giving `[2026-01-09 .. 2026-01-13]` with an expected amount of 200.

A repayment of 200 dated `2026-01-10` is allocated to period 4, which meets its minimum payment. Without the boundary rule period 4 would have been generated as `[2026-01-12 .. 2026-01-14]`, and the repayment, dated on a day covered by no period, would have been lost.

**RESUME variant:** with a pause of `2026-01-08 .. 2026-01-12` instead, period 4 is `[2026-01-09 .. 2026-01-15]`. A RESUME on `2026-01-10` removes the two pause days `2026-01-11` and `2026-01-12`: period 3 keeps its end on `2026-01-08`, period 4 keeps its start on `2026-01-09` and ends on `2026-01-13`.

**UNDO_RESET variant:** the same pause of `2026-01-08 .. 2026-01-12` and reset on `2026-01-09`, with the reset undone on `2026-01-10` before the RESUME on that day. The undo clears the flags but keeps the cut, so the RESUME gives the same dates: period 3 `[2026-01-07 .. 2026-01-08]` and period 4 `[2026-01-09 .. 2026-01-13]`, with no overlap.

These flows are asserted by `WorkingCapitalLoanDelinquencyResetInsidePauseTest` and by the E2E scenarios UC17âUC29 of `WorkingCapitalDelinquencyReset.feature`.

##### Scenario #4: RESCHEDULE Action Without Affecting EIR

**Setup:**

* Loan has daily payments; delinquency bucket configured with monthly periods and a PERCENTAGE minimum payment.
* At business date 2024-03-01, Period 2 (Feb 2024) is delinquent: `paidAmount = 3,000`, minimum was `8,750`.
* The officer applies a RESCHEDULE reducing `minimumPayment` to FLAT 150.00 with monthly frequency.

**Action:**

`WorkingCapitalLoanDelinquencyActionWriteServiceImpl` records the action in `m_wc_loan_delinquency_action` and calls `rangeScheduleService.rescheduleMinimumPayment()`. The current open period’s `expectedAmount` is updated to 150.00, and all future periods are regenerated with the new frequency and expected amount. No call is made to the amortization model.

**Expected Behavior:**

* `m_wc_loan_delinquency_range_schedule` rows from the current open period onward have `expectedAmount = 150.00`.
* Future COB runs evaluate compliance against the new 150.00 threshold.
* `m_wc_loan_amortization_model` is unchanged â EIR, discount factors, and expected payment amounts remain as originally computed.
* To also adjust the amortization model (e.g., because the lender renegotiates the contractual rate), a separate `PUT /payment-rate` call must be made explicitly.

#### Summary

Working Capital Product Delinquency Management provides a purpose-built, period-based framework for tracking minimum payment compliance on revolving Working Capital loans. Key aspects include:

* A dedicated COB pipeline with two ordered steps: range schedule generation and delinquency classification.
* Per-period tracking of expected vs. paid minimum payments, with independent delinquency tags per period.
* A PAUSE action that extends all open and future periods proportionally, freezing the delinquency clock, and a RESUME action that ends it early.
* A RESET action that takes the periods before the reset date out of delinquency, optionally starting a new period on the reset date, and an UNDO_RESET that brings them back.
* The reset date as a hard boundary for pauses: a period started by a reset inside an active pause begins on the reset date and only counts the pause from there, exactly as the breach schedule does.
* A RESCHEDULE action that modifies minimum payment terms for the current and all future periods.
* A configurable minimum payment rule per delinquency bucket, expressed as either a flat amount or a percentage of principal.
* Product-level controls for grace days and the stored delinquency start type.

### Working Capital Loan EIR Calculation

#### Overview

Working Capital Loans with `amortizationType = EIR` derive an Effective Interest Rate (EIR) from the contractual payment structure using a Newton-Raphson solver and project a full amortization schedule with per-payment discount factors, NPV values, and deferred income tracking. The schedule is serialized to JSON and persisted in `m_wc_loan_amortization_model` for efficient reads. Mid-lifecycle rate changes are recorded as an effective date and a rate; the schedule re-solves from the balance and unearned fee it is carrying on that day, preserving historical payment data while recalculating future payments under the new EIR.

##### Purpose

EIR amortization enables lenders to accurately recognize discount fee income over the Working Capital Loan term using time-value-of-money principles. Each scheduled payment carries a discount factor and NPV value that drive present-value-based income amortization through the `deferredBalance` mechanism.

##### Scope

The scope of this document includes:

* EIR calculation algorithm and inputs
* Newton-Raphson solver configuration
* Payment and balance recurrence formulas
* Discount factor and NPV computation per payment
* Amortization model persistence and versioning
* Mid-lifecycle rate changes
* Projected amortization schedule API
* Rate change management API

##### Applicability

* Working Capital Loans with `amortizationType = EIR`
* `FLAT` is present as an enum value, but current product validation accepts only `EIR`
* Rate changes apply to active (disbursed) loans only

##### Definitions and Key Concepts

**Effective Interest Rate (EIR):** The periodic interest rate that equates the present value of all projected payments to the net disbursement amount. Solved by Newton-Raphson over the payment series itself, equivalent to Excel’s `IRR(values)` rather than its `RATE(nper, pmt, pv)`: the closing day pays a smaller remainder than the days before it, so the series is not a uniform annuity and solving it as one would not close the balance on nothing.

**Net Disbursement Amount:** Principal disbursed after deducting any upfront discount fee: `netDisbursement = totalLoanAmount â discountFeeAmount`.

**Total Payment Value (TPV):** The sum of all projected payments over the full loan term, used as the basis for computing the expected daily payment.

**Expected Payment:** The constant per-period payment: `expectedPayment = (TPV Ã periodPaymentRate / 100) / npvDayCount`. `periodPaymentRate` is stored as a percentage value.

**Original Payment Number:** `ceil((netDisbursementAmount + discountFeeAmount) / expectedPayment)` â the total number of payment periods.

**Discount Factor:** `1 / (1 + EIR)^paymentsLeft` â the time-value multiplier applied to a future payment. Held in the model, not returned by the API.

**NPV Value:** The present value of a scheduled payment: `npvValue = npvSource Ã discountFactor`. Held in the model, not returned by the API.

**Amortization Amount:** The portion of each payment that reduces the outstanding deferred income (`deferredBalance`).

**Deferred Balance:** Unrecognized discount fee income remaining at each period: starts at `discountFeeAmount` and closes on exactly zero. The projected figure falls for as long as the rate it is projected at stands still - it is a one-day-ahead projection, so a rate cut deducts a smaller day’s accrual from the same balance and reports more still deferred on the day it takes effect. What the money received has really earned is `actualDiscountFeeBalance`, which is a ledger and only ever falls.

**Rate Segment:** The run of days one rate governs - from the day a change takes effect until the next one does. Nothing stores it: a rate change records only its effective date and rate, and the walk switches rate when it reaches that date, so a segment describes what comes out rather than an entity that is kept.

#### Design Decisions and Considerations

##### Newton-Raphson Solver for EIR

The EIR is solved via `TvmFunctions.irr(cashFlows, mc)`, which finds `r` satisfying:

`Î£ cf[k] / (1+r)^k = 0` for `k = 0 .. n`

where `cf[0]` is the negated balance being solved from, `cf[1..n-1]` are the daily payments
and `cf[n]` is the closing remainder.

The series is solved as it stands rather than as a uniform annuity. The closing day pays only
what is left of the gross payable after the full daily payments, which is smaller than a daily
payment whenever the two do not divide evenly â and it is solving against that exact series
that makes the recurrence close on exactly zero on its last day, with the daily accruals
summing to exactly the discount fee. An annuity solve would leave both a little out.

Key solver parameters:

* Maximum iterations: 500
* Convergence tolerance: `1E-12`
* Initial guess: `|2 Ã (pmt Ã n + pv) / (pv Ã n)|` (linear approximation, absolute value taken)

The initial guess takes the absolute value of the linear approximation to avoid catastrophic divergence when `nper` is large (e.g., daily-payment loans with thousands of periods), where a fixed default of 0.01 would cause `(1.01)^nper` to overflow the `MathContext`.

##### Mid-Lifecycle Rate Changes

A rate change stores only what it was booked with: an `effectiveDate` and a `periodPaymentRate`. Everything the new rate needs â the balance still outstanding and the fee not yet earned against it â is what the schedule walk is already carrying when it reaches that day, so the figure a change is sized against and the figure the schedule is showing cannot disagree. Historical actuals before the effective date are preserved; only the days from it forward are recalculated.

A change already recorded on the same effective date is replaced, making rate changes idempotent on a date. Changes can only be appended, though: a date preceding a change already recorded is rejected, because each change is sized against the balance and unearned fee reached on its own day and an earlier one moves both for every change after it. A backdated change is applied by replaying the whole history in effective-date order onto a fresh model, which is what `regenerateAmortizationScheduleOnRateChange` does.

##### Amortization Model Persistence

The full `ProjectedAmortizationScheduleModel` is serialized to JSON (version `"7"` as of this writing) and stored in `m_wc_loan_amortization_model` (one row per loan, uniquely constrained on `loan_id`). This avoids recomputing the schedule from scratch on every read while still supporting incremental updates as payments and rate changes are recorded. Optimistic locking via the `version` column prevents concurrent overwrites.

##### Payment Date Normalization

Actual payments are applied by transaction date. A payment dated on or before the disbursement date maps to the first installment date, a payment after the final installment maps to the last installment date, and payments within the schedule range use their actual transaction date. Same-date payments are aggregated before the schedule is rebuilt.

#### Database Design

##### Overview

The amortization model is persisted as a JSON snapshot in `m_wc_loan_amortization_model`. Rate change history is tracked in `m_wc_loan_period_payment_rate_change`.

##### Existing Tables

**`m_wc_loan`**: The main Working Capital Loan instance table. Referenced by both amortization and rate change tables via foreign key.

**`m_wc_loan_product`**: Stores `amortization_type`, `npv_day_count`, `period_payment_rate`, and `discount` columns used as inputs to the EIR calculation.

##### Table: m_wc_loan_amortization_model

The `m_wc_loan_amortization_model` table persists the serialized amortization model for each loan. One row per loan; updated in place when a rate change or a payment is recorded.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | BIGINT | PK, not null | Primary key |
| loan_id | BIGINT | FK to m_wc_loan, unique, not null | Associated loan (one model per loan) |
| version | INT | not null | Optimistic locking version |
| json_model | CLOB | not null | Serialized `ProjectedAmortizationScheduleModel` JSON |
| business_date | DATE | not null | Business date when the model was last updated |
| json_model_version | VARCHAR(10) | not null | Schema version of the JSON model format |
| last_modified_on_utc | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

##### Table: m_wc_loan_period_payment_rate_change

The `m_wc_loan_period_payment_rate_change` table records an audit trail of all rate changes applied to a loan. Only one active (non-reversed) entry is expected per loan at any time.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | BIGINT | PK, not null | Primary key |
| wc_loan_id | BIGINT | FK to m_wc_loan, not null | Associated loan |
| effective_date | DATE | not null | Business date the new rate takes effect |
| previous_rate | DECIMAL(19,6) | not null | Period payment rate before the change |
| new_rate | DECIMAL(19,6) | not null | Period payment rate after the change |
| is_reversed | BOOLEAN | not null, default false | Whether this rate change has been superseded by a subsequent change |
| reversed_on_date | DATE | nullable | Business date the reversal was applied |
| created_by | BIGINT | not null | Audit field |
| created_on_utc | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| last_modified_by | BIGINT | not null | Audit field |
| last_modified_on_utc | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| version | INT | not null, default 0 | Optimistic locking version |

#### Configuration

##### Loan Product Configuration

Configure the following fields when creating or updating a Working Capital Loan product to enable EIR amortization:

```json
{
    "amortizationType": "EIR",          // mandatory â current implementation supports EIR
    "npvDayCount": 360,                 // mandatory for EIR â denominator in expected-payment formula
    "periodPaymentRate": 100,           // mandatory for EIR â percentage rate applied to TPV
    "discount": 5000.00                 // optional â upfront discount fee deducted before EIR computation
}
```

> [!NOTE]
> `npvDayCount` and `periodPaymentRate` together define the contractual payment: `expectedPayment = (TPV Ã periodPaymentRate / 100) / npvDayCount`. For example, `periodPaymentRate = 100` means the daily expected payment is approximately `TPV / npvDayCount` when `npvDayCount = 360`.

##### GL Account Mappings

Required GL account mappings when `accounting_type` is not `NONE`:

* **Loan Portfolio (ASSET)**: `loanPortfolioAccountId` â tracks outstanding principal
* **Deferred Income Liability (LIABILITY)**: `deferredIncomeLiabilityAccountId` â holds unrecognized discount fee income until amortized
* **Income from Discount Fee (INCOME)**: `incomeFromDiscountFeeAccountId` â receives amortized income each period

> [!IMPORTANT]
> `loanPortfolioAccountId`, `deferredIncomeLiabilityAccountId`, and `incomeFromDiscountFeeAccountId` are all mandatory when `accounting_type` is not `NONE`. The `accounting_type` column is stored in `m_wc_loan_product` with a default of `NONE`.

#### API Design

##### Endpoints

###### Retrieve Projected Amortization Schedule

Returns the full projected amortization schedule for a Working Capital Loan: the loan’s EIR, and per day the amount billed, both balances, both amortization amounts, and both deferred fee balances. The discount factor, NPV value, payments-left count and income modification are carried inside the model for the calculation but are not part of the response.

```java
GET /v1/working-capital-loans/{loanId}/amortization-schedule
```

**Response:**

```json
{
  "discountFeeAmount": 5000.00,
  "netDisbursementAmount": 95000.00,
  "totalPaymentVolume": 105000.00,
  "periodPaymentRate": 27.77,
  "npvDayCount": 360,
  "expectedDisbursementDate": "2024-01-15",
  "expectedPaymentAmount": 291.67,
  "originalPaymentNumber": 344,
  "effectiveInterestRate": 0.000295,
  "payments": [
    {
      "paymentNo": 1,
      "paymentDate": "2024-01-16",
      "expectedPaymentAmount": 291.67,
      "expectedBalance": 94709.00,
      "expectedAmortizationAmount": 13.89,
      "expectedDiscountFeeBalance": 4986.11,
      "actualPaymentAmount": null,
      "actualBalance": null,
      "actualAmortizationAmount": null,
      "actualDiscountFeeBalance": null
    }
  ]
}
```

> [!NOTE]
> Payment row 0 (disbursement) is also included in the `payments` array with a negative `expectedPaymentAmount` equal to the net disbursement. The four actual columns are `null` for a day that carries no record at all; a day that elapsed with nothing paid reports nil rather than `null`, because a missed instalment is a fact about the loan.

###### Update Period Payment Rate

Modifies the `periodPaymentRate` for an active Working Capital Loan. The operation reverses any existing active rate change, records a new `m_wc_loan_period_payment_rate_change` entry, and triggers recalculation of the amortization schedule from the rate change date forward.

```java
PUT /v1/working-capital-loans/{loanId}/payment-rate
PUT /v1/working-capital-loans/external-id/{loanExternalId}/payment-rate
```

**Request Body:**

```json
{
  "periodPaymentRate": 30,        // mandatory â new period payment rate, as a percentage value
  "note": "Rate renegotiation",    // optional â recorded as a loan note
  "locale": "en_GB"                // optional
}
```

**Response:**

```json
{
  "officeId": 1,
  "clientId": 1,
  "resourceId": 123
}
```

###### Retrieve Rate Change History

Returns all rate change records for the loan in reverse chronological order (most recent first).

```java
GET /v1/working-capital-loans/{loanId}/rate-changes
GET /v1/working-capital-loans/external-id/{loanExternalId}/rate-changes
```

**Response:**

```json
[
  {
    "id": 5,
    "loanId": 123,
    "effectiveDate": "2024-06-01",
    "previousRate": 27.77,
    "newRate": 30,
    "reversed": false,
    "reversedOnDate": null,
    "createdDate": "2024-06-01T10:00:00Z"
  }
]
```

#### Business Rules

##### EIR Computation

* `expectedPayment = (totalPaymentVolume Ã periodPaymentRate / 100) / npvDayCount`
* `originalPaymentNumber = ceil((netDisbursementAmount + discountFeeAmount) / expectedPayment)`
* `finalPayment = (netDisbursementAmount + discountFeeAmount) â expectedPayment Ã (originalPaymentNumber â 1)`
* `EIR = TvmFunctions.irr([ânetDisbursementAmount, expectedPayment Ã (originalPaymentNumber â 1), finalPayment])`
* The Newton-Raphson solver converges to a tolerance of `1E-12` with a maximum of 500 iterations.
* Product validation currently rejects non-EIR amortization types.
* `netDisbursementAmount` must be positive; `npvDayCount` must be positive.

##### Balance and Discount Factor Recurrence

For each day `i` (1-based):

* `balance[i] = balance[iâ1] Ã (1 + EIR) â billedInstalment[i]`, where `billedInstalment[i]` is the instalment in force capped at the balance it has to close
* `discountFactor[i] = 1 / (1 + EIR)^paymentsLeft[i]`
* `npvValue[i] = npvSource[i] Ã discountFactor[i]`
* the day’s high-precision accrual is `balance[iâ1] Ã EIR`, and what it **reports** is `round(aggregateAccrual[i]) â round(aggregateAccrual[iâ1])` â the running total is rounded, not the day
* `deferredBalance[i] = discountFee â round(aggregateAccrual[i])`, closing on exactly 0 and never drifting more than half a minor unit from the exact figure it shadows. It falls for as long as one rate governs the days it is projected at; the day a rate cut takes effect reports more still deferred than the day before, because the same balance is being projected one day forward at a smaller accrual

##### Rate Changes

* A `RateChange` stores only what it was booked with: `effectiveDate` and `periodPaymentRate`. Everything else is derived by the walk when it reaches that day, so the balance a change is sized against and the balance the schedule is showing cannot disagree.
* On the effective day the walk holds `balanceAtSplit` (reality where it is known) and `unearnedFee = discountFee â feeEarnedSoFar`, and re-solves the sub-schedule from them exactly as the original was solved: `newPayment = round((TPV Ã newPeriodPaymentRate / 100) / npvDayCount)`, `term = roundUp((balanceAtSplit + unearnedFee) / newPayment)`, and the EIR as the IRR of that cash flow.
* The plan cursor is repositioned onto the same reality, so fee already earned under the old rate stays earned â a rate change re-prices what is still to come, it does not reach backwards.
* Days before the effective date keep every figure they had.
* A change already recorded on the same effective date is replaced, so booking twice on one day overwrites rather than leaving the day with two rates. A date that precedes a change already recorded is rejected rather than dropping the later ones: `applyRateChange` appends, and a backdated change is applied by replaying the history in order onto a fresh model.
* A change dated at or past the day the schedule currently runs to takes effect on that day; a change against an already-square loan is rejected.
* Several changes compose without any extra machinery: each one re-bases both cursors and the walk carries on.

##### Rate Change Reversal

* Before recording a new rate change, all existing active (non-reversed) entries for the loan are reversed by setting `is_reversed = true` and `reversed_on_date = businessDate`.
* Only one non-reversed rate change entry is maintained per loan at any time.

##### Amortization Model Lifecycle

The `ProjectedAmortizationScheduleModel` progresses through four operations:

1. `generate()` â creates the initial schedule when the loan reaches approval/disbursement processing with the resolved product and loan parameters.
2. `regenerate()` â recalculates with updated amounts at approval or disbursement, preserving already applied payments.
3. `applyPayment()` â records a payment and rebuilds the payment list using the payment-date mapping rules described above.
4. `applyRateChange()` â records the effective date and the new rate, and rebuilds. The walk switches rate on that day and re-solves from the balance and unearned fee it is carrying.

#### Example Scenarios

##### Scenario #1: EIR Schedule for a New Working Capital Loan

**Setup:**
* Loan amount: 100,000; discount fee: 5,000 (deducted upfront)
* `periodPaymentRate = 27.77`, `npvDayCount = 360`, `totalPaymentVolume = 105,000`

**Action:**
The system computes `expectedPayment = (105,000 Ã 27 / 100) / 360 â 291.67` and `originalPaymentNumber = ceil(100,000 / 291.67) = 343`. EIR is solved via Newton-Raphson as the IRR of `[â95,000, 291.67 Ã 342, finalPayment]`, where `finalPayment` is the remainder of the gross payable after those 342 full payments. The schedule is stored in `m_wc_loan_amortization_model` with one row per day (343 payment rows plus the disbursement row).

**Expected Behavior:**

* `effectiveInterestRate` is returned in the amortization schedule API response.
* Each `payments[]` entry includes `expectedPaymentAmount`, `expectedBalance`, `expectedAmortizationAmount`, and `expectedDiscountFeeBalance`.
* `expectedDiscountFeeBalance` decreases from 5,000 to exactly 0 over the 344 days.
* First payment date is `disbursementDate + 1 day`.

##### Scenario #2: Mid-Lifecycle Rate Change

**Setup:**
* Loan has 343 periods total; 144 payments have been applied.
* Outstanding balance at period 144: 60,000.
* New `periodPaymentRate = 30`.

**Action:**
`applyRateChange()` is called with `newPeriodPaymentRate = 30` and `rateChangeDate = businessDate`, which falls on day 145. `newPayment = round((105,000 Ã 30 / 100) / 360) = 350.00`. `balanceAtSplit = 60,000` and `unearnedFee = discountFee â feeEarnedSoFar`, both read off the walk. `term = roundUp((60,000 + unearnedFee) / 350)`, and `EIR_new` is the IRR of that cash flow. The prior active `m_wc_loan_period_payment_rate_change` entry is reversed and a new one is saved.

**Expected Behavior:**

* Periods 1â144 retain their original EIR-based `discountFactor`, `npvValue`, and `expectedAmortizationAmount`.
* Periods 145 onward are recalculated using `EIR_new` and `newPayment`.
* The rate change history endpoint returns the new entry with `previousRate = 27.77` and `newRate = 30`.

#### Summary

Working Capital Loan EIR calculation provides time-value-of-money-based income recognition for revolving credit. Key aspects include:

* EIR is solved numerically using Newton-Raphson from `totalPaymentVolume`, `periodPaymentRate`, `npvDayCount`, and `discountFeeAmount`.
* The full amortization schedule is serialized to JSON in `m_wc_loan_amortization_model` for efficient retrieval without recomputation.
* Each scheduled payment carries a `discountFactor` and `npvValue`, enabling present-value-based income recognition through the `deferredBalance` amortization mechanism.
* Mid-lifecycle rate changes are recorded as a date and a rate, and re-solved during the walk from the balance and unearned fee reached on that day, preserving historical actuals while recalculating only future payments with the new EIR.
* Rate change history is maintained in `m_wc_loan_period_payment_rate_change` with full reversal support.

### Working Capital Loan â Planned and Projected Balances

#### Overview

Working Capital Loan amortization tracks two parallel balance series for each loan: a **planned balance** (based on expected payments) and a **projected balance** (based on actual payments received). Both series use the same Effective Interest Rate (EIR) derived from the contractual loan terms. Together they enable the system to show the theoretical schedule alongside real payment activity, track income deferral separately per track, and compute income modification for each repayment.

##### Purpose

Separating planned and projected balances allows lenders to:

* See the contracted payment schedule independently of payment behaviour
* Measure deviation between expected and actual income recognition period by period
* Report both the theoretical deferred income (based on the contracted schedule) and the actual deferred income remaining (based on cash received)

##### Scope

The scope of this document includes:

* Definition of planned balance (`expectedBalance`) and projected balance (`actualBalance`)
* Definition of planned discount fee balance (`expectedDiscountFeeBalance`) and projected discount fee balance (`actualDiscountFeeBalance`)
* Recurrence formulas for both balance tracks
* How the EIR links the two tracks
* Per-payment schedule fields exposed by the API
* The original projected payments snapshot

##### Applicability

* Working Capital Loans with `amortizationType = EIR`
* Both balance tracks are computed for every loan from disbursement through closure

##### Definitions and Key Concepts

**Planned Balance (`expectedBalance`):** Outstanding principal projected one day forward from what the borrower owes, restated from reality on any day already settled. Computed for every period whether or not a payment was received, and closes on zero. A projection rather than a ledger, so it does not simply run down: on a day that elapsed unpaid it holds, and on the day a rate cut takes effect it can report a higher figure than the day before, because a smaller instalment is deducted from the same balance. What is really owed is `actualBalance`, which only ever falls. Formerly serialized as `balance` in earlier JSON model versions.

**Projected Balance (`actualBalance`):** Running outstanding principal balance based on actual cash payments received. Populated only for days where a payment exists or where `calculatedTillDate` has been reached; `null` for future days nothing is known about. Deviates from the planned balance when actual payments differ from expected. Never below nothing: a borrower who has handed over more than the payable owes nothing at all, and the excess is held as the loan’s `overpayment_amount` rather than as a negative balance - the loan clamps every outstanding bucket the same way, so the schedule must not contradict it.

**Planned Discount Fee Balance (`expectedDiscountFeeBalance`):** Remaining unrecognized discount fee income on the projection: `discountFee â round(aggregateAccrual[i])`, closing on zero. Not the running sum of the reported `expectedAmortizationAmount` column: a settled day restates the total from what the money received has really earned, and the day’s reported share is the movement of the rounded total either side of that, so the column and the balance need not telescope across a restatement. Falls for as long as one rate governs the days being projected. Formerly serialized as `deferredBalance`.

**Projected Discount Fee Balance (`actualDiscountFeeBalance`):** Remaining unrecognized discount fee income based on actual amortizations: `discountFee â Î£(actualAmortizationAmount[1..i])`. `null` for unpaid future periods; deviates from planned when payments differ.

**EIR (Effective Interest Rate):** The daily periodic rate solved by Newton-Raphson as the IRR of the payment series the borrower will actually pay - the net disbursement out, `originalPaymentNumber â 1` daily payments in, and the closing remainder in. The same EIR drives the balance recurrence for both tracks. See the [EIR Calculation](https://fineract.apache.org/docs/working-capital-eir-calculation.html) document for the solver algorithm and how a rate change is applied.

**Income Modification:** The per-period difference `actualAmortization â expectedAmortization`. Positive when the borrower over-pays, negative on underpayment, `null` on no payment.

#### Design Decisions and Considerations

##### Two-Track Balance Model

A single `balance` field cannot distinguish between "what the balance would have been with on-time payments" and "what the balance actually is". The two-track model makes this explicit:

* The planned track is always fully populated and never changes retroactively once built â it is the reference schedule.
* The actual track is populated only where cash has been received or the business date has passed. It moves only when money moves: a day with a zero-amount payment carries the previous balance forward unchanged - nothing accrues on it, because the fee is earned on money in and no money came in - while a day nothing is known about remains `null`.

##### Backward Compatibility via @SerializedName Aliases

`ProjectedPayment` uses Gson `@SerializedName` to deserialize old JSON snapshots transparently:

* `"balance"` â `expectedBalance`
* `"deferredBalance"` â `expectedDiscountFeeBalance`

Model JSON version `"7"` is the current canonical version. The aliases are what let a model persisted under an earlier version be read at all; it is re-persisted under the current version on the next write.

##### Disbursement Row Initializes Both Tracks Identically

Row 0 (disbursement, `paymentNo = 0`) sets both balance tracks to the same starting values:

* `expectedBalance = actualBalance = netDisbursementAmount`
* `expectedDiscountFeeBalance = actualDiscountFeeBalance = discountFeeAmount`

From period 1 onward the tracks diverge based on actual payment behaviour.

#### Balance Computation

##### Planned Balance Recurrence

For every day `i`, until the balance closes and the schedule has caught up with `calculatedTillDate`:

```java
billedInstalment[i]  = min(instalment in force, expectedBalance[i-1] Ã (1 + EIR))
expectedBalance[i]   = expectedBalance[i-1] Ã (1 + EIR) â billedInstalment[i]
accrual[i]           = expectedBalance[i-1] Ã EIR                     (high precision)
aggregateAccrual[i]  = aggregateAccrual[i-1] + accrual[i]              (high precision)
expectedAmortizationAmount[i] = round(aggregateAccrual[i]) â round(aggregateAccrual[i-1])
expectedDiscountFeeBalance[i] = discountFee â round(aggregateAccrual[i])
```

The instalment is capped at the balance it has to close, so no day bills more than is owed.
The reported amortization is the difference between two rounded running totals rather than a
rounded day, which is what keeps `expectedDiscountFeeBalance` from drifting and lets it close
on exactly zero. The final balance converges to zero by construction, because the EIR was
solved against the very cash flow the schedule bills.

There is no fixed number of days: the walk runs until the loan is square. A borrower who has
fallen behind gets more days, one who has paid ahead gets fewer.

##### Projected Balance Recurrence

The actual track is driven by money collected, not by time passed:

```java
collected[i]                = collected[i-1] + actualPayment[i]
feeEarned[i]                = planCurve(collected[i])                  (high precision)
actualAmortizationAmount[i] = round(feeEarned[i]) â round(feeEarned[i-1])
actualBalance[i]            = max(0, netDisbursement â collected[i] + round(feeEarned[i]))
actualDiscountFeeBalance[i] = discountFee â round(feeEarned[i])
```

`planCurve` is the planned recurrence above run on its own instalments, read at the amount
collected â so repaying the whole payable earns the whole fee however few days it took, and
paying beyond the payable earns nothing further. It is walked as a cursor alongside the
calendar, not precomputed.

A rate change moves no money, so the actual balance carries straight through it; only the
instalment and rate the days ahead are solved at change.

For days where no record exists at all (no payment, and not yet elapsed):

* `actualBalance`, `actualPaymentAmount`, `actualAmortizationAmount`, `incomeModification` and `actualDiscountFeeBalance` are `null` â nothing is known about the day yet.
* A day that elapsed with nothing on it reports nil rather than nothing: a missed instalment is a fact about the loan, and it earns no fee.

##### Where the Expected Track Is Restated

A settled day â one that was paid, or that elapsed unpaid â restates what follows it. The
balance carried forward becomes what the borrower really owes, and the expected fee total is
re-seeded from the actual one, both the high-precision total and its rounded form together.
Days that have not come round yet keep the plan they were written with, so an instalment paid
in full and on time moves nothing.

##### EIR Linkage

The EIR is solved once from the contract terms and stored in
`ProjectedAmortizationScheduleModel.effectiveInterestRate`. A rate change re-solves it from
the balance and unearned fee the walk is carrying on the effective day, and it drives both
tracks from that day onward.

#### Schedule Fields

The `ProjectedAmortizationSchedulePaymentData` record exposes per-payment fields from the `GET /v1/working-capital-loans/{loanId}/amortization-schedule` response.

| Field | Nullable | Description |
| --- | --- | --- |
| `paymentNo` | No | 1-based period number. Row 0 = disbursement. |
| `paymentDate` | No | `expectedDisbursementDate + paymentNo` days. |
| `expectedPaymentAmount` | Yes | The daily instalment derived from TPV, `periodPaymentRate` and `npvDayCount`, capped at the balance the day has to close â so the closing day bills only what is left. Row 0: `ânetDisbursementAmount`. |
| `expectedBalance` | Yes | **Planned balance** â what the outstanding principal would be if every instalment from here were paid on time. Restated from reality on any day already settled. Alias `balance` in pre-v4 JSON. |
| `actualBalance` | Yes | **Projected balance** â actual outstanding principal based on received payments. Null for unpaid future periods. |
| `expectedAmortizationAmount` | Yes | Fee income recognized per day under the planned track: `round(aggregateAccrual[i]) â round(aggregateAccrual[i-1])`, the accrual being `expectedBalance[i-1] Ã EIR`. Null for row 0. |
| `actualPaymentAmount` | Yes | Actual cash received. Null for unpaid periods; `0` for past periods with zero-amount payment. |
| `actualAmortizationAmount` | Yes | Fee income recognized per period under the projected track, read off the plan curve at the money collected. Null for periods with no record at all. |
| `expectedDiscountFeeBalance` | Yes | **Planned deferred balance** â remaining unrecognized discount fee under the planned track. Alias `deferredBalance` in pre-v4 JSON. |
| `actualDiscountFeeBalance` | Yes | **Projected deferred balance** â remaining unrecognized discount fee under the projected track. Null for unpaid future periods. |

##### Disbursement Row (paymentNo = 0)

| `expectedPaymentAmount` | `ânetDisbursementAmount` |
| --- | --- |
| `expectedBalance` | `+netDisbursementAmount` |
| `actualBalance` | `+netDisbursementAmount` |
| `expectedAmortizationAmount` | null |
| `actualPaymentAmount` | null |
| `actualAmortizationAmount` | null |
| `expectedDiscountFeeBalance` | `discountFeeAmount` |
| `actualDiscountFeeBalance` | `discountFeeAmount` |

#### API Design

##### Endpoints

###### Retrieve Projected Amortization Schedule

Returns the full amortization schedule including both planned and projected balance tracks for every period.

```java
GET /v1/working-capital-loans/{loanId}/amortization-schedule
```

**Response:**

```json
{
  "discountFeeAmount": 1000.00,
  "netDisbursementAmount": 9000.00,
  "totalPaymentVolume": 100000.00,
  "periodPaymentRate": 18,
  "npvDayCount": 360,
  "expectedDisbursementDate": "2019-01-01",
  "expectedPaymentAmount": 50.00,
  "originalPaymentNumber": 200,
  "effectiveInterestRate": 0.0010678144878363462,
  "payments": [
    {
      "paymentNo": 0,
      "paymentDate": "2019-01-01",
      "expectedPaymentAmount": -9000.00,
      "expectedBalance": 9000.00,
      "actualBalance": 9000.00,
      "expectedAmortizationAmount": null,
      "actualPaymentAmount": null,
      "actualAmortizationAmount": null,
      "expectedDiscountFeeBalance": 1000.00,
      "actualDiscountFeeBalance": 1000.00
    },
    {
      "paymentNo": 1,
      "paymentDate": "2019-01-02",
      "expectedPaymentAmount": 50.00,
      "expectedBalance": 8959.61,
      "actualBalance": null,
      "expectedAmortizationAmount": 9.61,
      "actualPaymentAmount": null,
      "actualAmortizationAmount": null,
      "expectedDiscountFeeBalance": 990.39,
      "actualDiscountFeeBalance": null
    }
  ]
}
```

> [!NOTE]
> When no payments have been received, `actualBalance`, `actualAmortizationAmount`, and `actualDiscountFeeBalance` are `null` for all periods after row 0. As payments are applied the actual fields populate for those periods. `expectedBalance` and `expectedDiscountFeeBalance` are always populated for active schedule rows.

#### Business Rules

##### Planned Track Population

* The planned balance is recomputed for all periods on every rebuild (`rebuildPayments`), including after payments are applied or a rate change is recorded.
* Planned balance values do not change retroactively for past periods after a new payment is applied â they reflect the current contracted payment amount, not historical snapshots.
* On the day a rate change takes effect, the balance carries straight through â a rate change moves no money â and the recurrence continues at the newly solved instalment and EIR.

##### Projected Track Population

* `actualBalance` is populated for a period when `actualPaymentAmount` is not null (positive or zero-amount).
* For past periods where `calculatedTillDate` has advanced past the period date but no payment was received: `actualBalance` carries the last known actual balance forward without reduction (balance does not compound without a payment entry). `actualAmortizationAmount` is zero (not null) for these periods.
* Future periods (after `calculatedTillDate`) that have no payment: `actualBalance` and `actualDiscountFeeBalance` are null.

##### Divergence Between Tracks

The two tracks converge at disbursement and diverge based on payment behavior:

* **Exact payment**: `actualBalance[i] = expectedBalance[i]` for that period (and divergence closes).
* **Overpayment**: `actualBalance[i] < expectedBalance[i]`; projected deferred balance decreases faster than planned.
* **Underpayment or no payment**: `actualBalance[i] > expectedBalance[i]` if positive payment received; or `actualBalance[i] = null` if no payment.

##### Deferred Balance Invariants

* `expectedDiscountFeeBalance` starts at `discountFeeAmount` on row 0, never goes below zero, and falls on every day except one a rate change takes effect on, where the projection is re-priced.
* `actualDiscountFeeBalance` + cumulative `actualAmortizationAmount` = `discountFeeAmount` (for paid periods).
* Both planned and projected deferred balances are capped at `discountFeeAmount` and floored at zero.

#### Example Scenarios

##### Scenario #1: On-Time Payments â Both Tracks Converge

**Setup:**
* `netDisbursementAmount = 9,000`, `discountFeeAmount = 1,000`
* `periodPaymentRate = 18`, `npvDayCount = 360`, `TPV = 100,000`
* Derived: `expectedPayment = 50.00/day`, `originalPaymentNumber = 200`, `EIR â 0.001068`

**Action:**
Borrower pays exactly 50.00 on day 1.

**Expected Behavior:**

* `actualPaymentAmount[1] = 50.00`
* `actualBalance[1] = 9,000 Ã (1 + 0.001068) â 50.00 = 8,959.61` â equals `expectedBalance[1]`
* `actualAmortizationAmount[1] = 9.61` â equals `expectedAmortizationAmount[1]`
* `incomeModification[1] = 0`
* `actualDiscountFeeBalance[1] = 990.39` â equals `expectedDiscountFeeBalance[1]`

##### Scenario #2: No Payment on Day 1, Double Payment on Day 2

**Setup:**
Same loan as Scenario #1.

**Action:**
No payment on day 1; borrower pays 100.00 on day 2.

**Expected Behavior:**

Day 1:

* `actualPaymentAmount[1] = 0` (past period with zero payment)
* `actualBalance[1] = 9,000.00` (actual balance unchanged â no reduction)
* `actualAmortizationAmount[1] = 0`
* `actualDiscountFeeBalance[1] = 1,000.00` (unchanged)
* `expectedBalance[1] = 8,959.61` â planned track still decreases

Day 2:

* `actualPaymentAmount[2] = 100.00`
* `actualBalance[2] = 9,000.00 Ã (1 + EIR) â 100.00 â 8,909.62`
* `actualBalance[2] < expectedBalance[2] = 8,919.18` (projected ahead of planned due to double payment)
* Cursor-based amortization consumes 2 periods of expected amortization (100/50 = 2 periods)
* `actualAmortizationAmount[2] â 9.61 + 9.57 = 19.18`
* `incomeModification[2] = 19.18 â 9.57 = 9.61` (positive: more income than planned)

#### Summary

The Working Capital planned and projected balance model provides two parallel views of each loan’s outstanding principal and deferred income:

* **Planned balances** (`expectedBalance`, `expectedDiscountFeeBalance`) reflect the contracted schedule assuming all payments arrive on time. They are always fully populated and serve as the reference for income recognition targets.
* **Projected balances** (`actualBalance`, `actualDiscountFeeBalance`) reflect real payment activity. They populate period by period as cash is received and diverge from planned whenever payments deviate from the expected amount.
* Both tracks share the same EIR, derived once from the contract terms and re-solved on the day a rate change takes effect, from the balance and unearned fee the walk is carrying then.
* The `incomeModification` field quantifies the per-period difference, enabling lenders to reconcile actual income recognized against the contracted schedule.

### Working Capital Loan Discount Configuration

#### Overview

Working Capital Loans support an upfront discount amount that is deducted from the gross disbursement and used as the basis for EIR income amortization. This document covers how the discount is configured on the product and how the value moves through the loan lifecycle: proposed, approved, and applied at disbursement.

Discount Fee transaction creation, adjustment, accounting, and reversal behavior are documented separately in `working-capital-discount-fee-txn.adoc`.

##### Purpose

The discount configuration gives lenders a controlled way to price Working Capital credit while still allowing the discount to be reduced during origination when the product allows loan-level overrides.

##### Scope

The scope of this document includes:

* Product-level discount default and override configuration
* Discount values at loan submission, approval, and disbursement
* Validation rules for staged discount overrides
* Effective discount amount used by the amortization schedule

##### Applicability

* Working Capital Loans with the currently supported `amortizationType = EIR`
* Discount configuration is available during product and loan lifecycle operations
* The discount is only applied to the loan balance after disbursement

##### Definitions and Key Concepts

**Discount (product default):** The default discount fee amount defined on the Working Capital Loan product. It is copied to the loan instance when the loan is created.

**Discount Proposed (`discount_proposed`):** The discount amount proposed at loan submission time, if the product allows overrides. Stored on `m_wc_loan`.

**Discount Approved (`discount_approved`):** The discount amount set during approval. Cannot exceed `discount_proposed`. Stored on `m_wc_loan`. Cleared when approval is undone.

**Discount (active, `discount`):** The discount amount applied at disbursement. It drives the `discountFeeAmount` used in EIR schedule computation.

**Discount Default Overridable (`discountDefault`):** A product-level configurable attribute. When `true`, the loan officer may override the product discount at loan level. When `false`, the product discount is fixed and override attempts fail with `override.not.allowed.by.product`.

#### Design Decisions and Considerations

##### Staged Discount Override

The discount flows through three stages: proposed (submission) → approved (approval) → applied (disbursement). Each stage can only reduce, not increase, the discount from the prior stage. This keeps the final fee within the product default or the borrower-proposed amount.

##### Applied Discount Drives EIR

The EIR schedule uses the applied `discount` value from the loan product related details. Product default, proposed, and approved values are only staging values until disbursement resolves the amount.

#### Database Design

##### Overview

The discount lifecycle is tracked on the Working Capital Loan product related details and loan instance. Transaction relation tables are covered in `working-capital-discount-fee-txn.adoc`.

##### Existing Tables

**`m_wc_loan_product`**: Defines the product default `discount`.

**`m_wc_loan`**: Stores the proposed, approved, and applied discount values embedded from `WorkingCapitalLoanProductRelatedDetails`.

##### Changes to Existing Tables

###### m_wc_loan

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| discount | DECIMAL(19,6) | nullable | Active discount amount; set at disbursement; used as `discountFeeAmount` in EIR schedule |
| discount_proposed | DECIMAL(19,6) | nullable | Discount proposed at loan submission; upper bound for approval |
| discount_approved | DECIMAL(19,6) | nullable | Discount set during approval; upper bound for disbursement; cleared on undo-approval |

#### Configuration

##### Loan Product Configuration

Configure the discount at product level. The `allowAttributeOverrides` block controls whether loan-level stages can override the product default.

```json
{
    "discount": 5000.00,
    "allowAttributeOverrides": {
        "discountDefault": true
    }
}
```

> [!NOTE]
> `discountDefault = true` means the discount can be overridden at loan level. `discountDefault = false` means the product discount is fixed.

#### API Design

##### Set Discount at Submission

The `discount` field is optional when submitting a loan application. It is allowed only when `discountDefault = true` on the loan product.

```java
POST /v1/working-capital-loans
```

```json
{
  "discount": 4500.00
}
```

##### Set Discount at Approval

The `discountAmount` field is optional during approval. It sets `discount_approved` and cannot exceed `discount_proposed`.

```java
POST /v1/working-capital-loans/{loanId}?command=approve
POST /v1/working-capital-loans/external-id/{loanExternalId}?command=approve
```

```json
{
  "discountAmount": 4000.00
}
```

##### Set Discount at Disbursement

The `discountAmount` field at disbursement resolves the applied loan discount. When the resolved amount is greater than zero, a `DISCOUNT_FEE` transaction is created as part of disbursement processing.

```java
POST /v1/working-capital-loans/{loanId}?command=disburse
POST /v1/working-capital-loans/external-id/{loanExternalId}?command=disburse
```

```json
{
  "discountAmount": 4000.00
}
```

#### Validation Rules

##### Discount at Submission

* `discount` must be zero or positive when provided.
* If `discountDefault = false`, providing `discount` fails with `override.not.allowed.by.product`.
* If `discountDefault = true`, `discount` may be provided and must not exceed the product default discount.

##### Discount at Approval

* `discountAmount` must be zero or positive when provided.
* If `discountDefault = false`, providing `discountAmount` fails with `override.not.allowed.by.product`.
* `discountAmount` cannot exceed `discount_proposed`. If no proposed override exists, it cannot exceed the product default discount.

##### Discount at Disbursement

* `discountAmount` must be zero or positive when provided.
* `discountAmount` cannot exceed the approval-time discount.
* If no approved discount exists, `discountAmount` cannot exceed the product default discount.

#### Business Rules

##### Discount Lifecycle

* At loan creation, the product default `discount` is copied to the loan’s embedded product related details.
* At submission, if the product allows overrides (`discountDefault = true`), the borrower can propose a lower discount. The proposed value is stored as `discount_proposed`.
* At approval, the approver may set `discountAmount`. The approved amount is stored as `discount_approved` and cannot exceed the proposed amount.
* When approval is undone (`undoapproval`), `discount_approved` is cleared to null. The loan returns to SUBMITTED state.
* At disbursement, the applied discount is stored as `discount`.
* If the applied discount is greater than zero, a `DISCOUNT_FEE` transaction is created. Transaction details are covered in `working-capital-discount-fee-txn.adoc`.

##### Effective Discount Amount

The discount used in EIR schedule computation (`discountFeeAmount`) is the resolved active `discount` value on the Working Capital Loan at schedule generation time.

#### Example Scenario

##### Discount Reduced During Origination

**Setup:**
* Loan product with `discount = 5000.00` and `discountDefault = true`.
* Borrower submits with `discount = 4500.00`.
* Approver sets `discountAmount = 4000.00`.

**Action:**
Loan is disbursed with `discountAmount = 4000.00`.

**Expected Behavior:**

* `discount_proposed = 4500.00`, `discount_approved = 4000.00`, and `discount = 4000.00` on `m_wc_loan`.
* The amortization schedule uses `discountFeeAmount = 4000.00`.
* The borrower receives net disbursement reduced by the applied discount.

#### Summary

Working Capital Loan Discount Configuration defines the default discount and the allowed staged overrides before disbursement. The applied discount is the value used by the amortization schedule and, when greater than zero, results in a Discount Fee transaction.

### Savings Interest Posting

#### Overview

Apache Fineract supports several **interest posting period types** for savings and fixed-deposit accounts.
The period type determines the calendar interval at the end of which accrued interest is credited (posted) to the account.

##### Standard Posting Period Types

| Code | Name | Description |
| --- | --- | --- |
| 1 | Daily | Interest is posted every day. |
| 4 | Monthly | Interest is posted on the first day of each calendar month. |
| 5 | Quarterly | Interest is posted on the first day of each calendar quarter, aligned to the configured financial-year beginning month. |
| 6 | Bi-Annual | Interest is posted twice a year, aligned to the configured financial-year beginning month. |
| 7 | Annual | Interest is posted once a year on the first day of the month that begins the configured financial year. |

##### Anniversary-Based Posting Period Types

Anniversary posting periods differ from standard ones in that the posting schedule is anchored to the **day of the month on which the account was activated**, rather than to a fixed calendar boundary (e.g., end of month or end of quarter).

| Code | Name | Description |
| --- | --- | --- |
| 8 | Anniversary Monthly | Interest is posted every month on the same day-of-month as the account activation date. |
| 9 | Anniversary Quarterly | Interest is posted every three months on the same day-of-month as the account activation date. |
| 10 | Anniversary Bi-Annual | Interest is posted every six months on the same day-of-month as the account activation date. |
| 11 | Anniversary Annual | Interest is posted every twelve months on the same day-of-month as the account activation date. |

#### How Anniversary Posting Works

For all anniversary period types:

* The **anchor day** is the day-of-month of the account’s activation (start interest calculation) date.
* Each subsequent posting date is computed by adding the configured interval (1, 3, 6, or 12 months) to the start of the current period and adjusting the result to the anchor day.
* If the target month has fewer days than the anchor day, the posting date is adjusted to the **last day of that month**.

##### Posting Date Examples

**Account opened on January 15 â Anniversary Monthly**

| Period Start | Period End | Posting Date |
| --- | --- | --- |
| Jan 15 | Feb 14 | Feb 15 |
| Feb 15 | Mar 14 | Mar 15 |
| Mar 15 | Apr 14 | Apr 15 |

**Account opened on January 31 â Anniversary Monthly (short-month adjustment)**

| Period Start | Period End | Posting Date |
| --- | --- | --- |
| Jan 31 | Feb 27 | Feb 28 *(last day of Feb)* |
| Feb 28 | Mar 30 | Mar 31 |
| Mar 31 | Apr 29 | Apr 30 *(last day of Apr)* |
| Apr 30 | May 30 | May 31 |

**Account opened on February 29 (leap year) â Anniversary Annual**

| Period Start | Period End | Posting Date |
| --- | --- | --- |
| Feb 29, 2024 | Feb 27, 2025 | Feb 28, 2025 *(2025 is not a leap year)* |
| Feb 28, 2025 | Feb 27, 2026 | Feb 28, 2026 |
| Feb 28, 2026 | Feb 27, 2027 | Feb 28, 2027 |

#### Configuration

Anniversary posting period types are configured at the product level and apply to both **Savings Products** and **Fixed Deposit Products**.

##### API â Create / Update Savings Product

Pass the numeric code in the `interestPostingPeriodType` field:

```json
{
  "interestPostingPeriodType": 8
}
```

##### API â Create / Update Fixed Deposit Product

The same `interestPostingPeriodType` field is used for fixed deposit products.

```json
{
  "interestPostingPeriodType": 9
}
```

> [!NOTE]
> The financial-year beginning month (`financialYearBeginningMonth`) is not used for anniversary period types. Posting periods are determined solely by the account activation date.

#### Behaviour at Period Boundaries

* The last posting period of a calculation run may extend **beyond** the `interestPostingUpToDate`. Truncation to the actual balance date is handled downstream by `PostingPeriod`, not by the period-boundary calculation itself.
* When a manual "post interest as on" date falls within a period, that period is split at the manual date, consistent with the behaviour of all other posting period types.

### Working Capital Breach Management and Near Breach

#### Overview

Breach management for Working Capital (WC) Loans provides a schedule-driven framework to track whether a borrower is meeting minimum periodic payment obligations within each breach period. A **breach** occurs when the cumulative amount paid within a period falls below the configured minimum by the period’s end date. A **near breach** is an earlier warning signal: it fires within a period when the cumulative payments received at one or more evaluation checkpoints fall below a percentage-based threshold of the expected cumulative payment.

Both mechanisms operate on the same underlying **breach schedule** â a series of contiguous time periods generated per-loan by the Close of Business (COB) pipeline. The feature is implemented in the `fineract-working-capital-loan` module.

##### Purpose

This feature enables lenders and credit operations teams to:

* Detect imminent payment shortfalls before a breach actually occurs (near-breach signal).
* Determine definitively, at the end of each breach period, whether the borrower failed to meet the minimum obligation (breach flag).
* Report breach and near-breach status per period via the breach schedule API, enabling downstream workflows such as alerts, collection actions, and covenant enforcement.

##### Scope

The scope of this document includes:

* System-level breach configuration (`m_wc_breach_configuration`) â defines period frequency and minimum payment rule.
* System-level near-breach configuration (`m_wc_near_breach`) â defines evaluation checkpoints and threshold percentage.
* Loan product configuration â association of breach and near-breach configurations to a product, controlled by the breach overridable flag.
* Per-loan breach schedule (`m_wc_loan_breach_schedule`) â generated and maintained by the COB pipeline.
* COB business steps: `WC_BREACH_SCHEDULE` (step 5) and `WC_NEAR_BREACH_EVALUATION` (step 6).
* API endpoints for managing breach and near-breach configurations and retrieving a loan’s breach schedule.
* Validation rules enforced during configuration creation and product setup.

##### Applicability

* Breach schedule generation applies to Working Capital Loan accounts with at least one actual disbursement recorded.
* Breach evaluation applies to loans whose product, or individual loan, has a breach configuration assigned.
* Near-breach evaluation applies only to active loans that also have a near-breach configuration assigned.

##### Definitions and Key Concepts

**Breach Configuration:** A named, reusable set of rules â stored in `m_wc_breach_configuration` â that defines the breach period frequency and the minimum payment amount. Referenced by loan products and individual loans.

**Near-Breach Configuration:** A named, reusable set of rules â stored in `m_wc_near_breach` â that defines evaluation checkpoints within a breach period and the cumulative-payment threshold (as a percentage). When the cumulative paid amount at a checkpoint falls below `(checkpointIndex + 1) Ã threshold% Ã minPaymentAmount`, the period is flagged near-breached.

**Breach Schedule Period:** A contiguous time window (identified by a sequential `periodNumber`) that starts on the actual disbursement date offset by delinquency grace days and repeats at the configured frequency. Each period records `fromDate`, `toDate`, `minPaymentAmount`, `paidAmount`, `outstandingAmount`, a `nearBreach` boolean, and a `breach` boolean.

**Breach Amount Calculation Type:** Determines how `minPaymentAmount` is derived per period. `FLAT` uses the configured `breachAmount` directly. `PERCENTAGE` computes it as `breachAmount%` of `approvedPrincipal + discount`.

**Near-Breach Threshold:** A percentage value (0â100). On each evaluation checkpoint inside a breach period, the system computes `requiredCumulative = (checkpointIndex + 1) Ã (threshold / 100) Ã minPaymentAmount`. If `paidAmount < requiredCumulative`, the period is marked as near-breached.

**Breach Overridable:** A flag on the loan product’s configurable attributes (`breach_overridable`, exposed as `allowAttributeOverrides.breach`) that controls whether the breach and near-breach configurations can be replaced at the individual loan application level.

#### Design Decisions and Considerations

##### Separate Configuration Tables for Breach and Near Breach

Breach and near-breach configurations are maintained as independent, named, reusable entities rather than being embedded in the loan product. This allows multiple loan products â or even individual loans â to share the same configuration, and allows configurations to be updated centrally. The constraint that a near-breach configuration can only be used together with a breach configuration is enforced at loan product and loan application level.

##### Near-Breach Frequency Is Always Shorter Than Breach Frequency

The near-breach configuration defines checkpoints **within** a breach period. The system enforces that the near-breach frequency (i.e., the interval between checkpoints) is strictly less than the breach period frequency. This is validated through `WorkingCapitalNearBreachParseAndValidator.validateNearBreachAgainstBreach` when product or loan application breach settings are validated.

##### Breach Evaluation Is Idempotent, Near Breach Is Re-Derived

`evaluateBreach` checks whether the `breach` flag is already non-null before doing any work. Once a period has been evaluated (flag set to `true` or `false`), the COB step does not re-evaluate it. This prevents double-flagging and keeps COB idempotent.

`nearBreach` of the open period is instead a value derived from the current state of the period. It is re-derived on every COB run and after every monetary event that changes the period’s `paidAmount`, so it can move from `true` to `false` when the borrower catches up and back to `true` when a repayment is undone. Re-deriving an unchanged state yields the same value, so it is idempotent as well.

##### nullMeans "Not Yet Evaluated"

The `breach` and `nearBreach` columns on `m_wc_loan_breach_schedule` use three-state semantics: `null` = period still open and not yet evaluated (for `nearBreach`: no checkpoint of the period has elapsed yet), `false` = evaluated and the condition was not met, `true` = condition triggered. This distinction is important: a period with `paidAmount = 0` but not yet past its `toDate` correctly has `breach = null`.

##### Minimum Payment Applied at Repayment Time

When a repayment is posted on a WC loan, `WorkingCapitalLoanBreachScheduleServiceImpl.applyRepayment` immediately updates the `paidAmount` and `outstandingAmount` on the current breach period. This means the breach and near-breach evaluations in COB operate on up-to-date repayment data.

#### Database Design

##### Overview

The breach subsystem introduces two configuration tables (`m_wc_breach_configuration`, `m_wc_near_breach`) and one per-loan schedule table (`m_wc_loan_breach_schedule`). The existing `m_wc_loan_product`, `m_wc_loan`, and `m_wc_loan_product_configurable_attributes` tables gain foreign-key columns to reference these configurations.

##### Existing Tables

**`m_wc_loan_product`**: Gains `breach_id` (FK to `m_wc_breach_configuration`) and `near_breach_id` (FK to `m_wc_near_breach`) to associate configurations at the product level.

**`m_wc_loan`**: Gains `breach_id` and `near_breach_id` columns, copied from the product at loan origination unless overridden by the loan application.

**`m_wc_loan_product_configurable_attributes`**: Gains `breach_overridable` (BOOLEAN, default `false`) to control whether loan applications may specify different breach and near-breach configurations.

##### Table: m_wc_breach_configuration

The `m_wc_breach_configuration` table stores named breach configurations. Each row defines a breach period length and the minimum payment rule.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, auto-increment, not null | Primary key |
| `name` | VARCHAR(100) | not null, unique | Human-readable configuration name |
| `breach_frequency` | INT | nullable | Number of frequency units in one breach period |
| `breach_frequency_type` | VARCHAR(50) | nullable | Frequency unit: `DAYS`, `WEEKS`, `MONTHS`, or `YEARS` |
| `breach_amount_calculation_type` | VARCHAR(50) | nullable | `FLAT` or `PERCENTAGE` |
| `breach_amount` | DECIMAL(19,6) | nullable | Minimum payment amount or percentage of principal+discount |

##### Table: m_wc_near_breach

The `m_wc_near_breach` table stores named near-breach configurations. Each row defines how frequently checkpoints occur within a breach period and the cumulative threshold percentage.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, auto-increment, not null | Primary key |
| `near_breach_name` | VARCHAR(100) | not null, unique | Human-readable configuration name |
| `near_breach_frequency` | INT | not null | Number of frequency units between consecutive checkpoints |
| `near_breach_frequency_type` | VARCHAR(50) | not null | Frequency unit: `DAYS`, `WEEKS`, `MONTHS`, or `YEARS` |
| `near_breach_threshold` | DECIMAL(19,6) | not null | Percentage (0â100) used to compute the required cumulative payment at each checkpoint |

##### Table: m_wc_loan_breach_schedule

The `m_wc_loan_breach_schedule` table stores one row per breach period per WC loan. It is populated by the COB step `WC_BREACH_SCHEDULE` and updated during repayment posting.

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `id` | BIGINT | PK, auto-increment, not null | Primary key |
| `wc_loan_id` | BIGINT | FK to `m_wc_loan`, not null | Associated WC loan |
| `period_number` | INT | not null, unique with `wc_loan_id` | Sequential period index (1-based) |
| `from_date` | DATE | not null | Start of the breach period (inclusive) |
| `to_date` | DATE | not null | End of the breach period (inclusive) |
| `number_of_days` | INT | nullable | `to_date â from_date + 1` in calendar days |
| `min_payment_amount` | DECIMAL(19,6) | nullable | Minimum amount due within this period |
| `paid_amount` | DECIMAL(19,6) | nullable | Cumulative amount paid within this period so far |
| `outstanding_amount` | DECIMAL(19,6) | nullable | `min_payment_amount â paid_amount` (floor 0) |
| `near_breach` | BOOLEAN | nullable | `true` = paid amount below the requirement of the latest elapsed checkpoint; `false` = requirement met; `null` = no checkpoint elapsed yet |
| `breach` | BOOLEAN | nullable | `true` = breach triggered; `false` = evaluated, not triggered; `null` = not yet evaluated |
| `created_by` | BIGINT | not null | Audit field |
| `created_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |
| `last_modified_by` | BIGINT | not null | Audit field |
| `last_modified_on_utc` | DATETIME(6) / TIMESTAMP WITH TIME ZONE | not null | Audit field |

##### Changes to Existing Tables

###### m_wc_loan_product

New columns:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `breach_id` | BIGINT | FK to `m_wc_breach_configuration`, nullable | Product-level breach configuration |
| `near_breach_id` | BIGINT | FK to `m_wc_near_breach`, nullable | Product-level near-breach configuration |

###### m_wc_loan

New columns:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `breach_id` | BIGINT | FK to `m_wc_breach_configuration`, nullable | Per-loan breach configuration (copied from product or overridden) |
| `near_breach_id` | BIGINT | FK to `m_wc_near_breach`, nullable | Per-loan near-breach configuration (copied from product or overridden together with breach) |

###### m_wc_loan_product_configurable_attributes

New column:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `breach_overridable` | BOOLEAN | default `false` | If `true`, the loan application may specify different `breach_id` and `near_breach_id` values than the product defaults |

#### Configuration

##### Loan Product Configuration

To activate breach management on a Working Capital loan product, include a `breachId` referencing an existing breach configuration. `nearBreachId` is optional but requires `breachId` to be set.

```json
{
    "breachId": 1,              // mandatory to activate breach schedule generation
    "nearBreachId": 2,          // optional; requires breachId; near-breach evaluation only runs if set
    "allowAttributeOverrides": {
        "breach": true          // optional; allows per-loan override of breachId and nearBreachId
    }
}
```

#### API Design

##### Endpoints

###### Breach Configuration Template

Returns available option lists for `breachFrequencyType` and `breachAmountCalculationType`.

```java
GET /v1/working-capital/breach/template
```

**Response:**

```json
{
  "breachFrequencyTypeOptions": [
    { "id": "DAYS",   "code": "DAYS",   "value": "Days" },
    { "id": "WEEKS",  "code": "WEEKS",  "value": "Weeks" },
    { "id": "MONTHS", "code": "MONTHS", "value": "Months" },
    { "id": "YEARS",  "code": "YEARS",  "value": "Years" }
  ],
  "breachAmountCalculationTypeOptions": [
    { "id": "PERCENTAGE", "code": "PERCENTAGE", "value": "Percentage" },
    { "id": "FLAT",       "code": "FLAT",       "value": "Flat" }
  ]
}
```

###### Breach Configuration CRUD

Create, retrieve, update, and delete breach configurations.

```java
GET    /v1/working-capital/breach/breaches
GET    /v1/working-capital/breach/breaches/{breachId}
POST   /v1/working-capital/breach/breaches
PUT    /v1/working-capital/breach/breaches/{breachId}
DELETE /v1/working-capital/breach/breaches/{breachId}
```

**Request Body (POST / PUT):**

```json
{
  "name": "Monthly 20%",                    // mandatory â unique name, max 100 chars
  "breachFrequency": 1,                     // mandatory â positive integer
  "breachFrequencyType": "MONTHS",          // mandatory â DAYS | WEEKS | MONTHS | YEARS
  "breachAmountCalculationType": "PERCENTAGE", // mandatory â PERCENTAGE | FLAT
  "breachAmount": 20.00                     // mandatory â zero or positive
}
```

**Response:**

```json
{
  "resourceId": 1
}
```

> [!IMPORTANT]
> A breach configuration cannot be deleted while it is referenced by at least one Working Capital loan product. The delete operation raises a `PlatformDataIntegrityException` (`error.msg.data.integrity.issue.entity.linked`) in that case.

###### Near-Breach Configuration CRUD

Create, retrieve, update, and delete near-breach configurations.

```java
GET    /v1/working-capital/near-breach
GET    /v1/working-capital/near-breach/{breachId}
POST   /v1/working-capital/near-breach
PUT    /v1/working-capital/near-breach/{breachId}
DELETE /v1/working-capital/near-breach/{breachId}
```

**Request Body (POST / PUT):**

```json
{
  "nearBreachName": "Weekly 15%",           // mandatory â unique name
  "nearBreachFrequency": 1,                 // mandatory â positive integer
  "nearBreachFrequencyType": "WEEKS",       // mandatory â DAYS | WEEKS | MONTHS | YEARS
  "nearBreachThreshold": 15.00              // mandatory â percentage 0â100
}
```

**Response:**

```json
{
  "resourceId": 2
}
```

###### Breach Schedule Retrieval

Returns the list of breach schedule periods for a given WC loan.

```java
GET /v1/working-capital-loans/{loanId}/breach-schedule
```

**Response:**

```json
[
  {
    "id": 101,
    "loanId": 42,
    "periodNumber": 1,
    "fromDate": "2025-01-15",
    "toDate": "2025-02-14",
    "numberOfDays": 31,
    "minPaymentAmount": 2000.00,
    "outstandingAmount": 500.00,
    "nearBreach": true,
    "breach": null
  }
]
```

#### Validation Rules

##### Breach Configuration

* `name` â mandatory, not blank, max 100 characters, globally unique.
* `breachFrequency` â mandatory, must be a positive integer (> 0).
* `breachFrequencyType` â mandatory, must be one of `DAYS`, `WEEKS`, `MONTHS`, `YEARS`.
* `breachAmountCalculationType` â mandatory, must be one of `PERCENTAGE`, `FLAT`.
* `breachAmount` â mandatory, must be zero or positive.
* On update, duplicate-name validation excludes the entity being updated (self-update is allowed).

##### Near-Breach Configuration

* `nearBreachName` â mandatory, not null, globally unique.
* `nearBreachFrequency` â mandatory, must be a positive integer (> 0).
* `nearBreachFrequencyType` â mandatory, must be one of `DAYS`, `WEEKS`, `MONTHS`, `YEARS`.
* `nearBreachThreshold` â mandatory, must be a valid percentage value (validated by `.percentage()`).

##### Loan Product â Cross-Configuration Constraint

* `nearBreachId` may only be set when `breachId` is also set. Setting `nearBreachId` without a `breachId` fails with `cannot.enable.near.breach.without.breach`.
* The near-breach frequency must be strictly lower than the breach period frequency. Validation is performed by `WorkingCapitalNearBreachParseAndValidator.validateNearBreachAgainstBreach`. Failure code: `near.breach.frequency.must.be.lower.than.breach.frequency`.

#### Business Rules

##### Breach Schedule Generation

* The first breach period starts on `actualDisbursementDate + delinquencyGraceDays`. If no actual disbursement has been recorded, generation is deferred to the next COB run.
* Each period ends inclusively: `DAYS` uses `fromDate + frequency - 1 day`; `WEEKS`, `MONTHS`, and `YEARS` add the configured number of units and then subtract one day.
* Periods are generated lazily: the initial period is created once on the first COB run after disbursement; subsequent periods are generated until the latest period’s `toDate` is after the current business date.
* `minPaymentAmount` is calculated from the breach configuration:
  
  
  
  
  
  * `FLAT`: uses `breachAmount` directly.
  * `PERCENTAGE`: applies `breachAmount%` to `approvedPrincipal + discount` (rounded to currency precision).
* A Discount Fee added after disbursement recalculates the minimum payment of the period covering the business date and of later periods. Periods that have already ended keep the minimum payment they were evaluated against.

##### Breach Evaluation

* On each COB run the `WC_BREACH_SCHEDULE` step calls `evaluateBreach` for the period that covers the current business date.
* A period is breached (`breach = true`) if `outstandingAmount > 0` AND `businessDate >= toDate`.
* A period with `outstandingAmount = 0` is marked `breach = false` immediately when fully paid.
* Once `breach` is non-null the COB step skips re-evaluation of that period.

##### Near-Breach Evaluation

* Triggered by the `WC_NEAR_BREACH_EVALUATION` COB step (order 6), which runs after `WC_BREACH_SCHEDULE`.
* The step is skipped for loans that are not active or have no near-breach configuration.
* Evaluation checkpoints within a period are computed as multiples of the near-breach frequency starting from `fromDate`. Checkpoints that fall on or after `toDate` are excluded.
* On each checkpoint date `d` the required cumulative payment is:
  
  
  
  
  ```java
  requiredCumulative = (checkpointIndex + 1) Ã (threshold / 100) Ã minPaymentAmount
  ```
* The value is point-in-time: it compares `paidAmount` with `requiredCumulative` of the latest checkpoint that has elapsed. It is `true` if `paidAmount < requiredCumulative`, `false` otherwise, and `null` while no checkpoint of a period that was never evaluated has elapsed.
* When there is nothing to judge against â no minimum payment, no checkpoint inside the period (for example after a `RESCHEDULE` to a longer frequency) or no checkpoint elapsed yet â COB and monetary events leave the period with the value it has. Only a schedule rebuild that moved the dates or the minimum payment of the period turns its value back into `null` (see below).
* If the business date reaches `toDate`, the value of the last checkpoint closes the period out (`false` when no checkpoint falls inside the period).
* Every COB run re-derives the period covering the COB date, so a later missed checkpoint raises a flag that an earlier catch-up cleared.
* The latest near-breach `RESCHEDULE` action of the loan overrides the threshold and frequency of the product configuration.
* Re-derivation is skipped for loans that are not active, have no near-breach configuration or whose breach evaluation is disabled on the business date (in COB: the COB date). A skipped re-derivation leaves the values untouched, apart from the schedule rebuilds described below, and raises no event.
* `WorkingCapitalLoanNearBreachChangeBusinessEvent` is raised only when the persisted value changes.

##### Near-Breach Re-Evaluation on Monetary Activity

* Outside COB the effective date is the loan’s last closed business date, capped at the day before the business date: a checkpoint counts once COB has closed its day, so a loan whose COB catch-up is still pending is not judged on checkpoints COB has not processed yet. Before the first COB of the loan the day before the business date is used. The disabled-breach guard asks whether evaluation is enabled now, on the business date, the same date the paid-amount update of a repayment is guarded on. On the day breach evaluation is enabled again, the enable reprocess and every repayment re-derive the near breach immediately; on the day it is disabled nothing is re-derived.
* After a repayment-like transaction (`applyRepayment`) or its undo (`applyRepaymentUndo`) the near breach of the period it lands in is re-derived immediately, if that period is still open (`toDate >= businessDate`).
* When an undo moves the loan from closed back to active, the open period is re-derived once more after the status transition, so the undo of a repayment that closed the loan re-raises the flag on the reopened loan.
* Periods that are already closed keep the near breach they were closed out with when a monetary event lands in them.
* A breach reset with restart, the undo of such a reset, an enable and the replay after a pause, resume or breach reschedule compare against a snapshot of the schedule taken before any period is re-dated, deleted or regenerated. They re-derive the open period and every period whose dates, minimum payment or paid amount moved since that snapshot, or that was deleted and regenerated.
* A period that is deleted and regenerated with the same bounds takes over the value of the period it replaces.
* An explicit reprocess (reset with restart, its undo, enable) additionally re-derives every closed period that carries a value, so a value that no longer matches the replayed paid amount does not survive. Such a re-derivation can only switch between `true` and `false`.
* A re-derived period whose dates or minimum payment moved since the snapshot starts over from `null`: it gets a value again only when a checkpoint of its new bounds has elapsed, so a pause that moves the open period’s start, a breach reschedule that cuts the period before its first checkpoint, or an enable that leaves no minimum payment does not leave the value of the old geometry behind. This also applies to loans that are no longer active, where nothing is re-derived.
* A closed period that was never evaluated stays `null`, even when its dates, minimum payment or paid amount moved (for example one that closed while breach evaluation was disabled). Only the open period, or a period that was open in the snapshot and is being closed out now (the period a restart reset cuts), can go from `null` to a value.
* One `WorkingCapitalLoanNearBreachChangeBusinessEvent` is raised when a period holds a different value than in the snapshot. When the period open in the snapshot was deleted, as by the undo of a restart reset, its value is compared with the period open afterwards.

##### Repayment Application

* On every repayment transaction, `WorkingCapitalLoanBreachScheduleServiceImpl.applyRepayment` identifies the breach period covering the transaction date, adds the payment to `paidAmount`, and recomputes `outstandingAmount` (floored at zero). If this reduces `outstandingAmount` to zero and `breach` has not yet been evaluated, the period is marked `breach = false`. This ensures COB evaluations operate on current repayment data.

#### Example Scenarios

##### Scenario #1: Near Breach Triggered Mid-Period

**Setup:**

* Breach configuration: `breachFrequency = 1`, `breachFrequencyType = MONTHS`, `breachAmountCalculationType = FLAT`, `breachAmount = 1000`.
* Near-breach configuration: `nearBreachFrequency = 2`, `nearBreachFrequencyType = WEEKS`, `nearBreachThreshold = 50`.
* Period 1: `fromDate = 2025-01-15`, `toDate = 2025-02-14`, `minPaymentAmount = 1000`.

**Action:**

During COB on `2025-01-29` (two weeks after `fromDate`), the first checkpoint is reached. The borrower has paid 400 to date.

**Expected Behavior:**

* `requiredCumulative = (0+1) Ã 0.50 Ã 1000 = 500`
* `paidAmount (400) < requiredCumulative (500)` â `nearBreach = true` set on period 1.
* The `breach` flag remains `null` â period has not yet ended.

##### Scenario #2: Full Period Paid â No Breach

**Setup:**

Same breach configuration. The borrower makes a 1000 payment on `2025-01-20`.

**Action:**

`applyRepayment` sets `paidAmount = 1000`, `outstandingAmount = 0`, `breach = false`.

**Expected Behavior:**

* During COB on `2025-02-14` the `WC_BREACH_SCHEDULE` step finds `breach` is already non-null and skips evaluation.
* During COB on `2025-01-29` the `WC_NEAR_BREACH_EVALUATION` step computes `requiredCumulative = 500`; `paidAmount (1000) >= 500`, so the period resolves to `nearBreach = false`.

#### Summary

Working Capital Breach Management provides a periodic, schedule-driven mechanism to flag payment shortfalls on WC loans. Key aspects include:

* Independent, reusable breach and near-breach configurations managed at the system level and assigned to loan products.
* A per-loan breach schedule generated by the COB pipeline â one period per breach frequency interval â starting from the disbursement date offset by delinquency grace days.
* A two-stage COB evaluation: `WC_BREACH_SCHEDULE` (step 5) generates periods and evaluates end-of-period breaches; `WC_NEAR_BREACH_EVALUATION` (step 6) assesses mid-period cumulative-payment checkpoints.
* Minimum payment amounts computed as either a flat amount or a percentage of `approvedPrincipal + discount`.
* Idempotent breach evaluation: once a breach flag is resolved (`true` or `false`), subsequent COB runs leave it unchanged.
* A near-breach flag on the open period that follows the current state of the period: re-derived by COB and by every monetary event, frozen once the period is closed.

### Working Capital Breach Grace Days

#### Overview

Breach Grace Days is a per-product (and per-loan) integer setting that shifts the start date of the first period of the Working Capital (WC) Breach Schedule by N days after the actual disbursement date. Because Near-Breach evaluation runs over the same breach schedule, shifting the first breach period implicitly shifts the first Near-Breach evaluation window â no separate Near-Breach grace days field is required.

The feature is implemented in the `fineract-working-capital-loan` module and is exposed on the Working Capital Loan Product and Working Capital Loan REST APIs as `breachGraceDays`.

##### Purpose

Breach Grace Days gives lenders an explicit, intent-revealing knob to delay the start of breach tracking after disbursement, decoupled from the pre-existing `delinquencyGraceDays` (which now exclusively drives delinquency machinery). This allows a product configuration such as "begin enforcing minimum payment obligations 5 days after disbursement" without conflating breach and delinquency semantics.

##### Scope

The scope of this document includes:

* New `breachGraceDays` column on `m_wc_loan_product` and `m_wc_loan`.
* New `breachGraceDays` field on the product and loan REST APIs (create, update, retrieve).
* Validation rule `breachGraceDays >= 0` at both product and loan levels.
* Application of `breachGraceDays` only to the first period generated by `BreachScheduleBusinessStep`.
* Implicit behavior on Near-Breach evaluation as a consequence of the shifted first period.

The scope explicitly excludes:

* No post-period grace â once a period closes with `outstanding_amount > 0`, the period is flagged `breach = true` immediately, regardless of `breachGraceDays`.
* `delinquencyGraceDays` is not renamed and not removed; it retains its original semantics.
* No automatic data migration from `delinquency_grace_days` to `breach_grace_days`.

##### Applicability

* Applies to Working Capital loans whose product (or individual loan) has a breach configuration assigned (`breach_id` not null). When no breach configuration is set, the breach schedule is not generated and `breachGraceDays` is inert.
* Applies only to the first period in the schedule. Subsequent periods chain from `previousPeriod.toDate + 1` and do not re-apply the grace.
* Can be overridden at the loan-application level only when the product allows breach overrides (`allowAttributeOverrides.breach = true`).

##### Definitions and Key Concepts

**`breachGraceDays`:** Optional non-negative integer representing the number of calendar days added to the actual disbursement date before the first breach period begins. Stored on `m_wc_loan_product.breach_grace_days` (product default) and `m_wc_loan.breach_grace_days` (loan-level value, copied from product or overridden). Columns are nullable with DB-level `DEFAULT 0`; runtime treats a `null` value as `0`.

**First Breach Period Start:** `firstPeriod.fromDate = actualDisbursementDate + breachGraceDays days`. Computed by `WorkingCapitalLoanBreachScheduleServiceImpl.generateInitialPeriod` using the helper `getBreachGraceDays(loan)`.

**Implicit Near-Breach Shift:** `WorkingCapitalLoanNearBreachEvaluationServiceImpl.evaluatePeriod` computes its first checkpoint as `firstEvalDate = addFrequency(period.fromDate, frequency, frequencyType)`. Since `period.fromDate` is already shifted by `breachGraceDays`, the first near-breach checkpoint is shifted by the same amount.

#### Design Decisions and Considerations

##### Decoupled fromdelinquencyGraceDays

Prior to this feature, the breach schedule generator read `delinquencyGraceDays` to offset the first period â a coupling that conflated two unrelated business concepts. `breachGraceDays` is a new, independent field. The two fields can now be set to different values on the same product.

##### Sibling Helper Instead of Rename

`WorkingCapitalLoanBreachScheduleServiceImpl` exposes a new private helper `getBreachGraceDays(loan)`. The original `getGraceDays(loan)` (which reads `delinquencyGraceDays`) is intentionally retained to keep the delinquency-side concept available without confusion.

##### Hard Cut-Over Without SQL Backfill

The Liquibase changeset adds `breach_grace_days` as a nullable column with DB-level `DEFAULT 0`; existing rows receive `0` via that default. No automatic copy from `delinquency_grace_days` is performed. Tenants that previously relied on `delinquencyGraceDays` to shift the breach schedule must update `breachGraceDays` explicitly via the REST API or SQL.

##### Null Treated as Zero

The column is nullable with DB-level `DEFAULT 0`, and the Java field has no in-class initializer â so `breachGraceDays` may legitimately be `null` in memory (e.g., after a create request that omits the parameter, before the entity is reloaded from the DB). The service helper `getBreachGraceDays` returns `0` when it encounters a `null` value, so `null` and an explicit `0` are semantically equivalent at runtime.

##### No Override Flag of Its Own

`breachGraceDays` inherits the existing `allowAttributeOverrides.breach` flag. No new boolean is added to `m_wc_loan_product_configurable_attributes`.

#### Database Design

##### Overview

Two existing tables gain one column each. No new tables are introduced.

##### Changes to Existing Tables

###### m_wc_loan_product

New column:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `breach_grace_days` | INT | nullable, default `0` | Product-level default number of days the first breach period start is shifted past the actual disbursement date |

###### m_wc_loan

New column:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| `breach_grace_days` | INT | nullable, default `0` | Loan-level value (copied from product at origination; may be overridden when the product allows breach overrides) |

The Liquibase changeset is `fineract-working-capital-loan/src/main/resources/db/changelog/tenant/module/workingcapitalloan/parts/0043_wc_breach_grace_days.xml`. Both add-column changesets are guarded by `columnExists` preconditions so they are idempotent.

#### Configuration

##### Loan Product Configuration

`breachGraceDays` is optional on the product create/update request. When omitted on create, the DB column default (`0`) applies.

```json
{
    "breachId": 1,                  // breach config required for the schedule to be generated
    "breachGraceDays": 5,           // optional; integer >= 0; column has DB default 0
    "allowAttributeOverrides": {
        "breach": true              // optional; required to allow per-loan override of breachGraceDays
    }
}
```

##### Loan-Level Override

When the loan application omits `breachGraceDays`, the loan inherits the product’s value. When provided, the loan stores its own value. Override only takes effect when the product allows breach overrides; otherwise the assembler keeps the product default.

#### API Design

##### Endpoints

###### Working Capital Loan Product â Create

```java
POST /v1/working-capital/products
```

**Request Body (relevant fields):**

```json
{
  "name": "WC Product",
  "shortName": "WCP",
  "breachId": 1,
  "breachGraceDays": 5,             // optional; integer >= 0; column has DB default 0
  "delinquencyGraceDays": 0,        // unrelated field, retained for delinquency
  "locale": "en_US",
  "dateFormat": "yyyy-MM-dd"
}
```

###### Working Capital Loan Product â Update

```java
PUT /v1/working-capital/products/{productId}
```

Accepts `breachGraceDays` as a partial-update field. When present, the change is tracked in the response `changes` map under the key `breachGraceDays`.

###### Working Capital Loan Product â Retrieve

```java
GET /v1/working-capital/products/{productId}
GET /v1/working-capital/products
```

The response includes `breachGraceDays` (integer) at the top level.

###### Working Capital Loan â Create

```java
POST /v1/working-capital/loans
```

Accepts an optional `breachGraceDays` integer. Inherited from the product when omitted; overrides only apply when the product allows breach overrides.

###### Working Capital Loan â Update

```java
PUT /v1/working-capital/loans/{loanId}
```

Accepts `breachGraceDays` as a partial-update field.

###### Working Capital Loan â Retrieve

```java
GET /v1/working-capital/loans/{loanId}
```

The response includes the loan’s effective `breachGraceDays` value.

#### Validation Rules

##### Product

* `breachGraceDays` is optional on create; when present must be `>= 0`. Error code: `[breachGraceDays] The parameter \`breachGraceDays\` must be zero or greater.` (HTTP 400).
* Enforced by `WorkingCapitalLoanProductDataValidator.validateSettingsFields` via `integerZeroOrGreater()` (applied both for create and partial update).

##### Loan Application

* Same `integerZeroOrGreater()` validation in `WorkingCapitalLoanApplicationDataValidator` for both create and update paths.
* No upper bound is enforced.

#### Business Rules

##### Breach Schedule Generation

* `WorkingCapitalLoanBreachScheduleServiceImpl.generateInitialPeriod` reads `loan.getLoanProductRelatedDetails().getBreachGraceDays()` and computes `fromDate = actualDisbursementDate.plusDays(breachGraceDays)`.
* `numberOfDays = (toDate â fromDate) + 1` (inclusive count).
* The grace is applied only when generating period number `1`. `generateNextPeriodIfNeeded` chains subsequent periods as `nextFromDate = latestPeriod.toDate + 1 day` and never re-applies the grace.
* When the product has no breach configuration, `BreachScheduleBusinessStep` short-circuits and no schedule is created â `breachGraceDays` has no effect.

##### Near-Breach Evaluation

* No code change in `WorkingCapitalLoanNearBreachEvaluationServiceImpl`.
* Near-breach checkpoints are derived from `period.fromDate`. Because the first period’s `fromDate` is already shifted by `breachGraceDays`, the first near-breach checkpoint within period `1` is shifted by the same amount.
* Checkpoints in later periods are unaffected (their periods are chained without re-applying the grace).

##### Loan Assembly From Product

* `WorkingCapitalLoanAssemblerImpl` copies `breachGraceDays` from the product’s `WorkingCapitalLoanProductRelatedDetail` into the loan’s `WorkingCapitalLoanProductRelatedDetails` at origination.
* If the loan create/update request includes `breachGraceDays`, the assembler honours the override only when the product allows breach overrides; otherwise the product default is retained.

#### Example Scenarios

##### Scenario #1: Breach Schedule First Period Shifted

**Setup:**

* Product configured with `breachId` (FLAT, `breachAmount = 500`, `breachFrequency = 1`, `breachFrequencyType = MONTHS`) and `breachGraceDays = 5`.
* Loan disbursed on `2026-01-01` with principal `9000`.

**Action:**

The Close-of-Business pipeline runs `BreachScheduleBusinessStep` on the day of disbursement.

**Expected Behavior:**

* Period `1` is created with `fromDate = 2026-01-06`, `toDate = 2026-02-05`, `numberOfDays = 31`, `minPaymentAmount = 500.00`, `breach = null`, `nearBreach = null`.
* Subsequent periods chain from `2026-02-06` and do not re-apply the 5-day grace.

##### Scenario #2: Near-Breach Window Implicitly Shifted

**Setup:**

* Product configured with breach (FLAT, `breachAmount = 900`, `breachFrequency = 3`, `breachFrequencyType = MONTHS`), near-breach (`nearBreachFrequency = 60 DAYS`, `nearBreachThreshold = 33.33`), and `breachGraceDays = 5`.
* Loan disbursed on `2026-01-01`. No repayment is made.

**Action:**

Business date advances to `2026-03-07` and COB runs.

**Expected Behavior:**

* Period `1` of the breach schedule starts on `2026-01-06` (disbursement + 5 days grace) and ends on `2026-04-05`.
* The first near-breach checkpoint is `2026-01-06 + 60 days = 2026-03-07`.
* Since `paidAmount = 0` at `2026-03-07` and `requiredCumulative = (1) Ã 33.33% Ã 900 â 299.97`, the period is flagged `nearBreach = true`.
* `breach` remains `null` because the period has not yet ended.

#### Summary

`breachGraceDays` is an independent, validated configuration field on the Working Capital Loan Product and Loan that delays the start of the first breach period (and, by chaining, the first near-breach evaluation window). Key aspects:

* Stored as a nullable `INT` column with DB-level `DEFAULT 0` on `m_wc_loan_product` and `m_wc_loan` (changeset `0043_wc_breach_grace_days.xml`); the breach-schedule service treats `null` as `0`.
* Exposed via `breachGraceDays` in product and loan REST APIs (create / update / retrieve).
* Applied only to period `1` of the breach schedule; chained periods are not regraced.
* Drives Near-Breach evaluation shift implicitly â no separate near-breach grace field is needed.
* Decoupled from the legacy `delinquencyGraceDays`, which keeps its original delinquency semantics.

### Working Capital Loan â Disable / Enable

This chapter documents two symmetric operational controls of the Working Capital Loan
module (`fineract-working-capital-loan`): **Delinquency Disable / Enable** and
**Breach Disable / Enable**. Both let an operator temporarily suspend an automatic
evaluation on an active loan â delinquency classification or covenant/limit breach
evaluation, respectively â and later resume it, re-computing the affected schedule as
of the resume date.

The two features share the same command shape, request contract, permission layering,
validation rules and disable/enable persistence model, but they act on different domains and
differ in what is recomputed when the loan is enabled again. The sections below describe the
concept and the differences, the data model, the REST contract, the business rules and the
runtime flows.

#### Overview

Both features are exposed as one more **action** on top of an existing action collection
(delinquency actions and breach actions). Neither introduces a new endpoint or a new table:
`disable` and `enable` are two additional values of the existing `action` parameter, routed
through the same `CREATE` command, and persisted as extra rows in the pre-existing action
table. Only a dedicated permission was added for each feature.

##### Concept

* A **disable** stops the automatic evaluation as of the current business date. From that
  moment the corresponding periodic evaluation (delinquency classification / breach
  evaluation) is skipped for the loan, and any evaluation-driven side effects are suppressed.
* An **enable** re-triggers evaluation as of the current business date, closing the open
  disable window and recomputing the schedule so the loan reflects what would have happened
  had it never been disabled (see the per-feature differences below).
* A disable window is a **singleton**: a loan can hold at most one open (not-yet-enabled)
  disable at a time. Disabling twice, or enabling when nothing is disabled, is rejected.

##### The two features side by side

| **Aspect** | **Delinquency Disable / Enable** | **Breach Disable / Enable** |
| --- | --- | --- |
| Suspended evaluation | Delinquency classification (aging / tagging). | Covenant / limit breach evaluation. |
| Action enum | `DelinquencyAction` (`PAUSE`, `RESUME`, `RESCHEDULE`, `DISABLE`, `ENABLE`) â in `fineract-loan`. | `WorkingCapitalLoanBreachActionType` (`PAUSE`, `RESUME`, `RESCHEDULE`, `RESET`, `UNDO_RESET`, `DISABLE`, `ENABLE`). |
| Action table | `m_wc_loan_delinquency_action`. | `m_wc_loan_breach_action`. |
| Base collection endpoint | `POST /v1/working-capital-loans/{loanId}/delinquency-actions`. | `POST /v1/working-capital-loans/{loanId}/breach-actions`. |
| Base permission (always) | `CREATE_WC_DELINQUENCY_ACTION`. | `CREATE_WC_BREACH_ACTION`. |
| Extra permission for disable/enable | `CREATE_WC_DELINQUENCY_DISABLE`. | `CREATE_WC_BREACH_DISABLE`. |
| "Active disable" predicate | `action = DISABLE AND start_date ⇐ :date AND (end_date IS NULL OR end_date >= :date)`. | `action = DISABLE AND start_date ⇐ :date AND (end_date IS NULL OR end_date >= :date)`. |
| How `enable` is persisted | Adds a dedicated `ENABLE` row and closes the open disable at `end_date` = enable date **minus one day**. | Adds a dedicated `ENABLE` row and closes the open disable at `end_date` = enable date **minus one day**. |
| What `enable` recomputes | Extends open periods by the disabled days (pause-like) and re-classifies as of the enable date. | Reprocesses the whole breach schedule, applying the repayments that accrued while disabled. |
| Actions blocked while disabled | `PAUSE`, `RESUME`, `RESCHEDULE`. | `PAUSE`, `RESUME`, `RESCHEDULE`, `RESET` (only `UNDO_RESET` remains allowed). |

> [!NOTE]
> Delinquency and breach share the same disable/enable persistence model: each action is stored
> as its own row, an enable adds a dedicated `ENABLE` row and closes the open disable at
> `end_date = enableDate - 1`, and the "active disable" predicate is
> `end_date IS NULL OR end_date >= :date`. They differ only in the effect recomputed on enable
> (see the last two rows) â delinquency treats the disabled window as a pause and re-classifies,
> whereas breach reprocesses its own breach schedule. The loan stops being considered disabled
> from the enable date on.

##### Key source references

* Delinquency API â `fineract-working-capital-loan/…​/api/WorkingCapitalLoanDelinquencyActionApiResource.java:75`
  (disable/enable permission check at lines 86-89).
* Breach API â `fineract-working-capital-loan/…​/api/WorkingCapitalLoanBreachActionApiResource.java:74`
  (permission layering in `executeBreachAction`, line 130).
* Delinquency validator â `…​/validator/WorkingCapitalLoanDelinquencyActionParseAndValidator.java`
  (`parseAndValidateDisableOrEnable`).
* Breach validator â `…​/validator/WorkingCapitalLoanBreachActionParseAndValidator.java`
  (`parseAndValidateDisableOrEnable`, `validateDisableState`).
* Delinquency write service â `…​/service/WorkingCapitalLoanDelinquencyActionWriteServiceImpl.java:54`.
* Breach write service â `…​/service/WorkingCapitalLoanBreachActionWriteServiceImpl.java`.
* "Is disabled" queries â `…​/repository/WorkingCapitalLoanDelinquencyActionRepository.java:39`
  and `…​/repository/WorkingCapitalLoanBreachActionRepository.java:37`.

#### Data Model

Disable / Enable does not add a table. Each `disable` or `enable` is a row appended to the
feature’s existing action table, discriminated by the `action` column. The disable/enable
change set (`0052_wc_loan_delinquency_disable.xml`, `0050_wc_loan_breach_disable.xml`) only
inserts the dedicated permission.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSczNTRweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjcwMXB4O2hlaWdodDozNTRweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA3MDEgMzU0JyB3aWR0aD0nNzAxcHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48ZyBpZD0nZWxlbV9sb2FuJz48cmVjdCBjb2RlTGluZT0nNScgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSc2NC4xMzU4JyBpZD0nbG9hbicgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM0JyB4PScyODMnIHk9JzcnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc3MicgeD0nMzE0JyB5PScyNi45NjU5Jz5tX3djX2xvYW48L3RleHQ+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB4MT0nMjg0JyB4Mj0nNDE2JyB5MT0nMzYuMDY3OScgeTI9JzM2LjA2NzknLz48ZWxsaXBzZSBjeD0nMjk0JyBjeT0nNDcuMDY3OScgZmlsbD0nIzAwMDAwMCcgcng9JzMnIHJ5PSczJyBzdHlsZT0nc3Ryb2tlOiMwMDAwMDA7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDgnIHg9JzMwMycgeT0nNTUuMDMzOSc+aWQgOiBCSUdJTlQgwqtQS8K7PC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycgeDE9JzI4NCcgeDI9JzQxNicgeTE9JzYzLjEzNTgnIHkyPSc2My4xMzU4Jy8+PC9nPjxnIGlkPSdlbGVtX2RlbCc+PHJlY3QgY29kZUxpbmU9JzknIGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMjE2LjY3OTInIGlkPSdkZWwnIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzMyNicgeD0nNycgeT0nMTMxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjA4JyB4PSc2NicgeT0nMTUwLjk2NTknPm1fd2NfbG9hbl9kZWxpbnF1ZW5jeV9hY3Rpb248L3RleHQ+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB4MT0nOCcgeDI9JzMzMicgeTE9JzE2MC4wNjc5JyB5Mj0nMTYwLjA2NzknLz48ZWxsaXBzZSBjeD0nMTgnIGN5PScxNzEuMDY3OScgZmlsbD0nIzAwMDAwMCcgcng9JzMnIHJ5PSczJyBzdHlsZT0nc3Ryb2tlOiMwMDAwMDA7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDgnIHg9JzI3JyB5PScxNzkuMDMzOSc+aWQgOiBCSUdJTlQgwqtQS8K7PC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzgnIHgyPSczMzInIHkxPScxODcuMTM1OCcgeTI9JzE4Ny4xMzU4Jy8+PGVsbGlwc2UgY3g9JzE4JyBjeT0nMTk4LjEzNTgnIGZpbGw9JyMwMDAwMDAnIHJ4PSczJyByeT0nMycgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTY2JyB4PScyNycgeT0nMjA2LjEwMTgnPndjX2xvYW5faWQgOiBCSUdJTlQgwqtGS8K7PC90ZXh0PjxlbGxpcHNlIGN4PScxOCcgY3k9JzIxNy4yMDM4JyBmaWxsPScjMDAwMDAwJyByeD0nMycgcnk9JzMnIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE0OCcgeD0nMjcnIHk9JzIyNS4xNjk3Jz5hY3Rpb24gOiBWQVJDSEFSKDEyOCk8L3RleHQ+PGVsbGlwc2UgY3g9JzE4JyBjeT0nMjM2LjI3MTcnIGZpbGw9JyMwMDAwMDAnIHJ4PSczJyByeT0nMycgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTE0JyB4PScyNycgeT0nMjQ0LjIzNzYnPnN0YXJ0X2RhdGUgOiBEQVRFPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzMwMCcgeD0nMjcnIHk9JzI2My4zMDU1Jz5lbmRfZGF0ZSA6IERBVEUgIMKrbnVsbCB3aGlsZSBESVNBQkxFIGFjdGl2ZcK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzOScgeD0nMjcnIHk9JzI4Mi4zNzM0Jz5taW5pbXVtX3BheW1lbnQgOiBERUNJTUFMKDE5LDYpPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI2NCcgeD0nMjcnIHk9JzMwMS40NDE0Jz5taW5pbXVtX3BheW1lbnRfdHlwZSA6IFZBUkNIQVIoNTApPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwNCcgeD0nMjcnIHk9JzMyMC41MDkzJz5mcmVxdWVuY3kgOiBJTlQ8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjAyJyB4PScyNycgeT0nMzM5LjU3NzInPmZyZXF1ZW5jeV90eXBlIDogVkFSQ0hBUig1MCk8L3RleHQ+PC9nPjxnIGlkPSdlbGVtX2JyZSc+PHJlY3QgY29kZUxpbmU9JzIyJyBmaWxsPScjRjFGMUYxJyBoZWlnaHQ9JzIxNi42NzkyJyBpZD0nYnJlJyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPSczMjYnIHg9JzM2OCcgeT0nMTMxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTcyJyB4PSc0NDUnIHk9JzE1MC45NjU5Jz5tX3djX2xvYW5fYnJlYWNoX2FjdGlvbjwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHgxPSczNjknIHgyPSc2OTMnIHkxPScxNjAuMDY3OScgeTI9JzE2MC4wNjc5Jy8+PGVsbGlwc2UgY3g9JzM3OScgY3k9JzE3MS4wNjc5JyBmaWxsPScjMDAwMDAwJyByeD0nMycgcnk9JzMnIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwOCcgeD0nMzg4JyB5PScxNzkuMDMzOSc+aWQgOiBCSUdJTlQgwqtQS8K7PC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM2OScgeDI9JzY5MycgeTE9JzE4Ny4xMzU4JyB5Mj0nMTg3LjEzNTgnLz48ZWxsaXBzZSBjeD0nMzc5JyBjeT0nMTk4LjEzNTgnIGZpbGw9JyMwMDAwMDAnIHJ4PSczJyByeT0nMycgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTY2JyB4PSczODgnIHk9JzIwNi4xMDE4Jz53Y19sb2FuX2lkIDogQklHSU5UIMKrRkvCuzwvdGV4dD48ZWxsaXBzZSBjeD0nMzc5JyBjeT0nMjE3LjIwMzgnIGZpbGw9JyMwMDAwMDAnIHJ4PSczJyByeT0nMycgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTQ4JyB4PSczODgnIHk9JzIyNS4xNjk3Jz5hY3Rpb24gOiBWQVJDSEFSKDEyOCk8L3RleHQ+PGVsbGlwc2UgY3g9JzM3OScgY3k9JzIzNi4yNzE3JyBmaWxsPScjMDAwMDAwJyByeD0nMycgcnk9JzMnIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNCcgeD0nMzg4JyB5PScyNDQuMjM3Nic+c3RhcnRfZGF0ZSA6IERBVEU8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMzAwJyB4PSczODgnIHk9JzI2My4zMDU1Jz5lbmRfZGF0ZSA6IERBVEUgIMKrbnVsbCB3aGlsZSBESVNBQkxFIGFjdGl2ZcK7PC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzOScgeD0nMzg4JyB5PScyODIuMzczNCc+bWluaW11bV9wYXltZW50IDogREVDSU1BTCgxOSw2KTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNDAnIHg9JzM4OCcgeT0nMzAxLjQ0MTQnPm1pbmltdW1fcGF5bWVudF90eXBlIDogVkFSQ0hBUjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDQnIHg9JzM4OCcgeT0nMzIwLjUwOTMnPmZyZXF1ZW5jeSA6IElOVDwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNzgnIHg9JzM4OCcgeT0nMzM5LjU3NzInPmZyZXF1ZW5jeV90eXBlIDogVkFSQ0hBUjwvdGV4dD48L2c+PGcgaWQ9J2xpbmtfbG9hbl9kZWwnPjxwYXRoIGNvZGVMaW5lPSczNScgZD0nTTMwOCw3OS4yMSBDMzA4LDc5LjIxIDMwOCwxMjIuOTggMzA4LDEyMi45OCAnIGZpbGw9J25vbmUnIGlkPSdsb2FuLWRlbCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA4JyB4Mj0nMzE0JyB5MT0nMTIyLjk4JyB5Mj0nMTMwLjk4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA4JyB4Mj0nMzAyJyB5MT0nMTIyLjk4JyB5Mj0nMTMwLjk4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA4JyB4Mj0nMzA4JyB5MT0nMTIyLjk4JyB5Mj0nMTMwLjk4Jy8+PGVsbGlwc2UgY3g9JzMwOCcgY3k9JzExNi45OCcgZmlsbD0nbm9uZScgcng9JzQnIHJ5PSc0JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMDQnIHgyPSczMTInIHkxPSc3NS4yMScgeTI9Jzc1LjIxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA0JyB4Mj0nMzEyJyB5MT0nNzguMjEnIHkyPSc3OC4yMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwOCcgeDI9JzMwOCcgeTE9Jzc5LjIxJyB5Mj0nNzEuMjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2NScgeD0nMjQyJyB5PSc5Ni45OTcnPndjX2xvYW5faWQ8L3RleHQ+PC9nPjxnIGlkPSdsaW5rX2xvYW5fYnJlJz48cGF0aCBjb2RlTGluZT0nMzYnIGQ9J00zOTIuNSw3OS4yMSBDMzkyLjUsNzkuMjEgMzkyLjUsMTIyLjk4IDM5Mi41LDEyMi45OCAnIGZpbGw9J25vbmUnIGlkPSdsb2FuLWJyZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzkyLjUnIHgyPSczOTguNScgeTE9JzEyMi45OCcgeTI9JzEzMC45OCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM5Mi41JyB4Mj0nMzg2LjUnIHkxPScxMjIuOTgnIHkyPScxMzAuOTgnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczOTIuNScgeDI9JzM5Mi41JyB5MT0nMTIyLjk4JyB5Mj0nMTMwLjk4Jy8+PGVsbGlwc2UgY3g9JzM5Mi41JyBjeT0nMTE2Ljk4JyBmaWxsPSdub25lJyByeD0nNCcgcnk9JzQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM4OC41JyB4Mj0nMzk2LjUnIHkxPSc3NS4yMScgeTI9Jzc1LjIxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzg4LjUnIHgyPSczOTYuNScgeTE9Jzc4LjIxJyB5Mj0nNzguMjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczOTIuNScgeDI9JzM5Mi41JyB5MT0nNzkuMjEnIHkyPSc3MS4yMScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY1JyB4PSczMjYuNScgeT0nOTYuOTk3Jz53Y19sb2FuX2lkPC90ZXh0PjwvZz48L2c+PC9zdmc+)

Figure 14. Entity-Relationship â action tables reused by Disable / Enable

##### m_wc_loan_delinquency_action

Created by `0015_wc_loan_delinquency_action.xml`; `end_date` was made nullable by
`0023_wc_loan_delinquency_action_reschedule.xml` (a `DISABLE` row keeps `end_date` null while
active). Entity: `WorkingCapitalLoanDelinquencyAction` (`…​/domain/WorkingCapitalLoanDelinquencyAction.java:43`).

| **Column** | **Type** | **Nullable** | **Meaning for Disable / Enable** |
| --- | --- | --- | --- |
| `id` | BIGINT (PK) | No | Surrogate key. |
| `wc_loan_id` | BIGINT (FK) | No | Owning loan â `m_wc_loan.id`. |
| `action` | VARCHAR(128) | No | `DISABLE` or `ENABLE` (enum `DelinquencyAction`, stored as string). |
| `start_date` | DATE | No | The current business date on which disable/enable was applied. |
| `end_date` | DATE | Yes | For a `DISABLE` row: `null` while active, stamped with `enableDate - 1` once enabled. An `ENABLE` row carries no `end_date`. |
| `minimum_payment` | DECIMAL(19,6) | Yes | Unused by disable/enable (reschedule only). |
| `minimum_payment_type` | VARCHAR(50) | Yes | Unused by disable/enable (reschedule only). |
| `frequency` | INT | Yes | Unused by disable/enable (reschedule only). |
| `frequency_type` | VARCHAR(50) | Yes | Unused by disable/enable (reschedule only). |

##### m_wc_loan_breach_action

Created by `0045_wc_loan_breach_action.xml` with `end_date` already nullable. Entity:
`WorkingCapitalLoanBreachAction` (`…​/domain/WorkingCapitalLoanBreachAction.java`).

| **Column** | **Type** | **Nullable** | **Meaning for Disable / Enable** |
| --- | --- | --- | --- |
| `id` | BIGINT (PK) | No | Surrogate key. |
| `wc_loan_id` | BIGINT (FK) | No | Owning loan â `m_wc_loan.id`. |
| `action` | VARCHAR(128) | No | `DISABLE` or `ENABLE` (enum `WorkingCapitalLoanBreachActionType`, stored as string). |
| `start_date` | DATE | No | The current business date on which disable/enable was applied. |
| `end_date` | DATE | Yes | For a `DISABLE` row: `null` while active, stamped with `enableDate - 1` once enabled. |
| `minimum_payment` | DECIMAL(19,6) | Yes | Unused by disable/enable (reschedule only). |
| `minimum_payment_type` | VARCHAR | Yes | Unused by disable/enable (reschedule only). |
| `frequency` | INT | Yes | Unused by disable/enable (reschedule only). |
| `frequency_type` | VARCHAR | Yes | Unused by disable/enable (reschedule only). |

Both tables extend the auditable base type, so they also carry `created_by`,
`last_modified_by`, `created_on_utc` and `last_modified_on_utc`.

##### Permissions inserted by the feature

| **Permission code** | **Entity name** | **Change set** |
| --- | --- | --- |
| `CREATE_WC_DELINQUENCY_DISABLE` | `WC_DELINQUENCY_DISABLE` | `0052_wc_loan_delinquency_disable.xml:33` |
| `CREATE_WC_BREACH_DISABLE` | `WC_BREACH_DISABLE` | `0050_wc_loan_breach_disable.xml:32` |

Both permissions are inserted with `can_maker_checker = false`.

#### API Contract

Disable and Enable reuse the action-collection endpoints. The verb is carried in the
`action` field of the request body; there is no `command=` query parameter. Every request
requires the `Fineract-Platform-TenantId` header.

##### Delinquency Disable / Enable

###### POST /v1/working-capital-loans/{loanId}/delinquency-actions

Also available by external id: `POST /v1/working-capital-loans/external-id/{loanExternalId}/delinquency-actions`
(resolves the external id to the internal loan id, then delegates to the same handler â
`WorkingCapitalLoanDelinquencyActionApiResource.java:106`).

**Permissions**: `CREATE_WC_DELINQUENCY_ACTION` (checked for every action) **and**
`CREATE_WC_DELINQUENCY_DISABLE` (checked additionally when `action` is `disable` or `enable`)
â `WorkingCapitalLoanDelinquencyActionApiResource.java:86-89`.

```json
{
  "action": "disable",
  "startDate": "2026-03-05",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

```json
{
  "action": "enable",
  "startDate": "2026-03-05",
  "dateFormat": "yyyy-MM-dd",
  "locale": "en"
}
```

| **Field** | **Type** | **Required** | **Rule for disable/enable** |
| --- | --- | --- | --- |
| `action` | String | Yes | Must be `disable` or `enable` (case-insensitive). |
| `startDate` | String (date) | Yes | Must equal the current business date â no backdating. |
| `endDate` | String (date) | No | Must **not** be provided; rejected if present. |
| `dateFormat` | String | Conditional | Required to parse `startDate` (e.g. `yyyy-MM-dd`). |
| `locale` | String | Conditional | Required to parse `startDate` (e.g. `en`). |

`minimumPayment`, `minimumPaymentType`, `frequency`, `frequencyType` belong to the
`reschedule` action and are not used by disable/enable.

##### Breach Disable / Enable

###### POST /v1/working-capital-loans/{loanId}/breach-actions

Also available by external id: `POST /v1/working-capital-loans/external-id/{loanExternalId}/breach-actions`.

**Permissions**: `CREATE_WC_BREACH_ACTION` (base) **and** `CREATE_WC_BREACH_DISABLE`
(additionally for `disable` / `enable`). The same endpoint also guards `reset` /
`undo_reset` with `CREATE_WC_BREACH_RESET` â `WorkingCapitalLoanBreachActionApiResource.java:130`.

The request body is identical in shape to the delinquency contract above (same `action`,
`startDate`, `endDate`, `dateFormat`, `locale` rules for disable/enable).

##### Retrieval

| **Delinquency** | **Breach** |
| --- | --- |
| `GET /v1/working-capital-loans/{loanId}/delinquency-actions` | `GET /v1/working-capital-loans/{loanId}/breach-actions` |
| `GET /v1/working-capital-loans/external-id/{loanExternalId}/delinquency-actions` | `GET /v1/working-capital-loans/external-id/{loanExternalId}/breach-actions` |

Both `GET` variants require the base read permission (`READ_WC_DELINQUENCY_ACTION` /
`READ_WC_BREACH_ACTION`) and return the full action history, including the `DISABLE` and
`ENABLE` rows with their `startDate` / `endDate`.

##### Responses and errors

On success the `POST` returns `200 OK` with a `CommandProcessingResult` (`officeId`,
`clientId`, `resourceId` = the new action id).

| **HTTP** | **Reason** | **Fineract error code** |
| --- | --- | --- |
| 200 | Disable/enable persisted | â |
| 400 | `endDate` supplied for disable/enable | `validation.msg.*.endDate.must.not.be.provided.for.disable.or.enable` |
| 400 | `startDate` is not the current business date | `validation.msg.*.startDate.must.be.current.business.date` |
| 400 | Disable requested while already disabled | `…​delinquency.already.disabled` / `…​breach.already.disabled` |
| 400 | Enable requested with no active disable | `…​no.active.delinquency.disable.to.enable` / `…​no.active.breach.disable.to.enable` |
| 400 | Pause/resume/reschedule (and reset, breach only) while disabled | `…​delinquency.is.disabled` / `…​breach.is.disabled` |
| 400 | Loan is not `ACTIVE` | `…​invalid.loan.state` / `…​loan.is.not.active` |
| 404 | Loan (or external id) not found | `WorkingCapitalLoanNotFoundException` |

#### Business Rules

The rules below apply symmetrically to Delinquency and Breach unless a column notes
otherwise. Origins point at the two `parseAndValidateDisableOrEnable` / `validateDisableState`
validator methods and the write services.

| **ID** | **Category** | **Rule** | **Type** | **Origin in code** |
| --- | --- | --- | --- | --- |
| RN-001 | Authorization | Any action requires the base create permission; `disable`/`enable` additionally require the dedicated disable permission. | Precondition | `*ApiResource` (permission checks) |
| RN-002 | State | The loan must be `ACTIVE`; disable/enable on a non-active loan is rejected. | Precondition | `*ParseAndValidator` (loan-state check) |
| RN-003 | Temporal | `startDate` must equal the current business date; backdating or future-dating is rejected. | Precondition | `parseAndValidateDisableOrEnable` â `must.be.current.business.date` |
| RN-004 | Input | `endDate` must not be present for a `disable`/`enable`. | Precondition | `parseAndValidateDisableOrEnable` â `must.not.be.provided.for.disable.or.enable` |
| RN-005 | Invariant | At most one open disable per loan: a second `disable` while one is active is rejected. | Precondition | `validateDisableState` â `*.already.disabled` |
| RN-006 | Invariant | `enable` requires an active disable; enabling when nothing is disabled is rejected. | Precondition | `validateDisableState` â `no.active.*.disable.to.enable` |
| RN-007 | Behaviour | While disabled, `pause`, `resume`, `reschedule` (and `reset` for breach) are blocked. | Guard | `validateBreachNotDisabled` / `validateDelinquencyNotDisabled` â `*.is.disabled` |
| RN-008 | Behaviour | For breach, `undo_reset` is the only action allowed while disabled (corrective bypass). | Exception | Breach validator (undo-reset bypass) |
| RN-009 | Effect (disable) | Delinquency disable lifts the active classification tag as of the disable date; while disabled, classification is skipped. | Postcondition | `WorkingCapitalLoanDelinquencyClassificationServiceImpl` (skip + lift) |
| RN-010 | Effect (disable) | Breach disable suppresses breach evaluation and schedule updates from repayments while disabled. | Postcondition | `WorkingCapitalLoanBreachScheduleServiceImpl` (skip guards) |
| RN-011 | Effect (enable) | Delinquency enable adds a dedicated `ENABLE` row, closes the disable (`end_date` = today â 1), extends open periods by the disabled days (pause-like) and re-classifies as of today. | Postcondition | `WorkingCapitalLoanDelinquencyActionWriteServiceImpl` |
| RN-012 | Effect (enable) | Breach enable closes the disable (`end_date` = today â 1) and reprocesses the breach schedule, applying repayments accrued while disabled. | Postcondition | `WorkingCapitalLoanBreachActionWriteServiceImpl` â `reprocessBreachSchedule` |

> [!IMPORTANT]
> RN-003 and RN-004 together mean disable/enable are strictly "now" operations with an
> open-ended window: the operator cannot choose the disable window boundaries directly. The
> window opens at the disable business date and closes at the enable business date.

#### Runtime Flows

##### Disable sequence

The sequence is the same for both features; the only per-feature step is the disable-time
side effect (delinquency lifts the active classification; breach only persists the row).

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc3NTZweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjE0OThweDtoZWlnaHQ6NzU2cHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTQ5OCA3NTYnIHdpZHRoPScxNDk4cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nNDknIHgyPSc0OScgeTE9Jzg0LjA2NzknIHkyPSc2NzMuMDcwMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSczMDQnIHgyPSczMDQnIHkxPSc4NC4wNjc5JyB5Mj0nNjczLjA3MDInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nNTkxLjUnIHgyPSc1OTEuNScgeTE9Jzg0LjA2NzknIHkyPSc2NzMuMDcwMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSc4MDMuNScgeDI9JzgwMy41JyB5MT0nODQuMDY3OScgeTI9JzY3My4wNzAyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzEwODYnIHgyPScxMDg2JyB5MT0nODQuMDY3OScgeTI9JzY3My4wNzAyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzEyODQuNScgeDI9JzEyODQuNScgeTE9Jzg0LjA2NzknIHkyPSc2NzMuMDcwMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPScxNDI3LjUnIHgyPScxNDI3LjUnIHkxPSc4NC4wNjc5JyB5Mj0nNjczLjA3MDInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4MicgeD0nNScgeT0nNzkuOTY1OSc+TG9hbiBPZmZpY2VyPC90ZXh0PjxlbGxpcHNlIGN4PSc0OScgY3k9JzEzLjUnIGZpbGw9JyNFMkUyRjAnIHJ4PSc4JyByeT0nOCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTQ5LDIxLjUgTDQ5LDQ4LjUgTTM2LDI5LjUgTDYyLDI5LjUgTTQ5LDQ4LjUgTDM2LDYzLjUgTTQ5LDQ4LjUgTDYyLDYzLjUgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4MicgeD0nNScgeT0nNjg3LjAzNjEnPkxvYW4gT2ZmaWNlcjwvdGV4dD48ZWxsaXBzZSBjeD0nNDknIGN5PSc2OTkuNjM4MScgZmlsbD0nI0UyRTJGMCcgcng9JzgnIHJ5PSc4JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cGF0aCBkPSdNNDksNzA3LjYzODEgTDQ5LDczNC42MzgxIE0zNiw3MTUuNjM4MSBMNjIsNzE1LjYzODEgTTQ5LDczNC42MzgxIEwzNiw3NDkuNjM4MSBNNDksNzM0LjYzODEgTDYyLDc0OS42MzgxICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPSc5OCcgeD0nMjU1JyB5PSc1MCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg0JyB4PScyNjInIHk9JzcxLjk2NTknPkFwaVJlc291cmNlPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nOTgnIHg9JzI1NScgeT0nNjcyLjA3MDInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4NCcgeD0nMjYyJyB5PSc2OTQuMDM2MSc+QXBpUmVzb3VyY2U8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMzcnIHg9JzUyMy41JyB5PSc1MCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyMycgeD0nNTMwLjUnIHk9JzcxLjk2NTknPkNvbW1hbmRIYW5kbGVyPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM3JyB4PSc1MjMuNScgeT0nNjcyLjA3MDInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMjMnIHg9JzUzMC41JyB5PSc2OTQuMDM2MSc+Q29tbWFuZEhhbmRsZXI8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjknIHg9JzczOS41JyB5PSc1MCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNScgeD0nNzQ2LjUnIHk9JzcxLjk2NTknPldyaXRlU2VydmljZUltcGw8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjknIHg9JzczOS41JyB5PSc2NzIuMDcwMicvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNScgeD0nNzQ2LjUnIHk9JzY5NC4wMzYxJz5Xcml0ZVNlcnZpY2VJbXBsPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM4JyB4PScxMDE3JyB5PSc1MCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEyNCcgeD0nMTAyNCcgeT0nNzEuOTY1OSc+UGFyc2VBbmRWYWxpZGF0b3I8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMzgnIHg9JzEwMTcnIHk9JzY3Mi4wNzAyJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI0JyB4PScxMDI0JyB5PSc2OTQuMDM2MSc+UGFyc2VBbmRWYWxpZGF0b3I8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjcnIHg9JzEyMjEuNScgeT0nNTAnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTMnIHg9JzEyMjguNScgeT0nNzEuOTY1OSc+QWN0aW9uUmVwb3NpdG9yeTwvdGV4dD48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzEyNycgeD0nMTIyMS41JyB5PSc2NzIuMDcwMicvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExMycgeD0nMTIyOC41JyB5PSc2OTQuMDM2MSc+QWN0aW9uUmVwb3NpdG9yeTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzEzNTguNScgeT0nNzkuOTY1OSc+bV93Y19sb2FuXypfYWN0aW9uPC90ZXh0PjxwYXRoIGQ9J00xNDEwLDI5IEMxNDEwLDE5IDE0MjgsMTkgMTQyOCwxOSBDMTQyOCwxOSAxNDQ2LDE5IDE0NDYsMjkgTDE0NDYsNTUgQzE0NDYsNjUgMTQyOCw2NSAxNDI4LDY1IEMxNDI4LDY1IDE0MTAsNjUgMTQxMCw1NSBMMTQxMCwyOSAnIGZpbGw9JyNFMkUyRjAnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS41OycvPjxwYXRoIGQ9J00xNDEwLDI5IEMxNDEwLDM5IDE0MjgsMzkgMTQyOCwzOSBDMTQyOCwzOSAxNDQ2LDM5IDE0NDYsMjkgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzEzNTguNScgeT0nNjg3LjAzNjEnPm1fd2NfbG9hbl8qX2FjdGlvbjwvdGV4dD48cGF0aCBkPSdNMTQxMCw3MDEuMTM4MSBDMTQxMCw2OTEuMTM4MSAxNDI4LDY5MS4xMzgxIDE0MjgsNjkxLjEzODEgQzE0MjgsNjkxLjEzODEgMTQ0Niw2OTEuMTM4MSAxNDQ2LDcwMS4xMzgxIEwxNDQ2LDcyNy4xMzgxIEMxNDQ2LDczNy4xMzgxIDE0MjgsNzM3LjEzODEgMTQyOCw3MzcuMTM4MSBDMTQyOCw3MzcuMTM4MSAxNDEwLDczNy4xMzgxIDE0MTAsNzI3LjEzODEgTDE0MTAsNzAxLjEzODEgJyBmaWxsPScjRTJFMkYwJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuNTsnLz48cGF0aCBkPSdNMTQxMCw3MDEuMTM4MSBDMTQxMCw3MTEuMTM4MSAxNDI4LDcxMS4xMzgxIDE0MjgsNzExLjEzODEgQzE0MjgsNzExLjEzODEgMTQ0Niw3MTEuMTM4MSAxNDQ2LDcwMS4xMzgxICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScyOTIsMTMxLjQ3OTksMzAyLDEzNS40Nzk5LDI5MiwxMzkuNDc5OSwyOTYsMTM1LjQ3OTknIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQ5JyB4Mj0nMjk4JyB5MT0nMTM1LjQ3OTknIHkyPScxMzUuNDc5OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2OScgeD0nNTYnIHk9JzExMS45NjQ5Jz5QT1NUIC4uLi9kZWxpbnF1ZW5jeS1hY3Rpb25zPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzMScgeD0nNTYnIHk9JzEyOS42NzA5Jz57ICJhY3Rpb24iOiJkaXNhYmxlIiwgInN0YXJ0RGF0ZSI6IHRvZGF5IH08L3RleHQ+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA0JyB4Mj0nMzQ2JyB5MT0nMTY3LjE4NicgeTI9JzE2Ny4xODYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYnIHgyPSczNDYnIHkxPScxNjcuMTg2JyB5Mj0nMTgwLjE4NicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwNScgeDI9JzM0NicgeTE9JzE4MC4xODYnIHkyPScxODAuMTg2Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczMTUsMTc2LjE4NiwzMDUsMTgwLjE4NiwzMTUsMTg0LjE4NiwzMTEsMTgwLjE4Nicgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjcxJyB4PSczMTEnIHk9JzE2MS4zNzcnPnZhbGlkYXRlSGFzQ3JlYXRlUGVybWlzc2lvbihXQ18uLi5fQUNUSU9OKTwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMDQnIHgyPSczNDYnIHkxPScyMTEuODkyJyB5Mj0nMjExLjg5MicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0NicgeDI9JzM0NicgeTE9JzIxMS44OTInIHkyPScyMjQuODkyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzA1JyB4Mj0nMzQ2JyB5MT0nMjI0Ljg5MicgeTI9JzIyNC44OTInLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzMxNSwyMjAuODkyLDMwNSwyMjQuODkyLDMxNSwyMjguODkyLDMxMSwyMjQuODkyJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNzQnIHg9JzMxMScgeT0nMjA2LjA4Myc+dmFsaWRhdGVIYXNDcmVhdGVQZXJtaXNzaW9uKFdDXy4uLl9ESVNBQkxFKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU4MCwyNTIuNTk4LDU5MCwyNTYuNTk4LDU4MCwyNjAuNTk4LDU4NCwyNTYuNTk4JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMDQnIHgyPSc1ODYnIHkxPScyNTYuNTk4JyB5Mj0nMjU2LjU5OCcvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3OScgeD0nMzExJyB5PScyNTAuNzg5Jz5sb2dDb21tYW5kU291cmNlIChDUkVBVEUpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNzkyLDI4NC4zMDQsODAyLDI4OC4zMDQsNzkyLDI5Mi4zMDQsNzk2LDI4OC4zMDQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU5MicgeDI9Jzc5OCcgeTE9JzI4OC4zMDQnIHkyPScyODguMzA0Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTg4JyB4PSc1OTknIHk9JzI4Mi40OTUnPmNyZWF0ZUFjdGlvbihsb2FuSWQsIGNvbW1hbmQpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMTA3NCwzMTYuMDEsMTA4NCwzMjAuMDEsMTA3NCwzMjQuMDEsMTA3OCwzMjAuMDEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzgwNCcgeDI9JzEwODAnIHkxPSczMjAuMDEnIHkyPSczMjAuMDEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNTgnIHg9JzgxMScgeT0nMzE0LjIwMSc+dmFsaWRhdGVBbmRQYXJzZShjb21tYW5kLCBsb2FuLCBleGlzdGluZyk8L3RleHQ+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMTA4NicgeDI9JzExMjgnIHkxPSczNTEuNzE2JyB5Mj0nMzUxLjcxNicvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzExMjgnIHgyPScxMTI4JyB5MT0nMzUxLjcxNicgeTI9JzM2NC43MTYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMDg3JyB4Mj0nMTEyOCcgeTE9JzM2NC43MTYnIHkyPSczNjQuNzE2Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScxMDk3LDM2MC43MTYsMTA4NywzNjQuNzE2LDEwOTcsMzY4LjcxNiwxMDkzLDM2NC43MTYnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2NycgeD0nMTA5MycgeT0nMzQ1LjkwNyc+c3RhcnREYXRlID09IGJ1c2luZXNzIGRhdGUgPzwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMDg2JyB4Mj0nMTEyOCcgeTE9JzM5Ni40MjIxJyB5Mj0nMzk2LjQyMjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMTI4JyB4Mj0nMTEyOCcgeTE9JzM5Ni40MjIxJyB5Mj0nNDA5LjQyMjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMDg3JyB4Mj0nMTEyOCcgeTE9JzQwOS40MjIxJyB5Mj0nNDA5LjQyMjEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzEwOTcsNDA1LjQyMjEsMTA4Nyw0MDkuNDIyMSwxMDk3LDQxMy40MjIxLDEwOTMsNDA5LjQyMjEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwNCcgeD0nMTA5MycgeT0nMzkwLjYxMzEnPmVuZERhdGUgYWJzZW50ID88L3RleHQ+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScxMjczLDQzNy4xMjgxLDEyODMsNDQxLjEyODEsMTI3Myw0NDUuMTI4MSwxMjc3LDQ0MS4xMjgxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMDg2JyB4Mj0nMTI3OScgeTE9JzQ0MS4xMjgxJyB5Mj0nNDQxLjEyODEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNzUnIHg9JzEwOTMnIHk9JzQzNS4zMTkxJz5pc0Rpc2FibGVkQXNPZihsb2FuSWQsIHRvZGF5KTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzEwOTcsNDY4LjgzNDEsMTA4Nyw0NzIuODM0MSwxMDk3LDQ3Ni44MzQxLDEwOTMsNDcyLjgzNDEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPScxMDkxJyB4Mj0nMTI4NCcgeTE9JzQ3Mi44MzQxJyB5Mj0nNDcyLjgzNDEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNycgeD0nMTEwMycgeT0nNDY3LjAyNTEnPmZhbHNlPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nODE1LDUwMC41NDAxLDgwNSw1MDQuNTQwMSw4MTUsNTA4LjU0MDEsODExLDUwNC41NDAxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDtzdHJva2UtZGFzaGFycmF5OjIuMCwyLjA7JyB4MT0nODA5JyB4Mj0nMTA4NScgeTE9JzUwNC41NDAxJyB5Mj0nNTA0LjU0MDEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMzEnIHg9JzgyMScgeT0nNDk4LjczMTEnPnBhcnNlZCBESVNBQkxFIGFjdGlvbiAoZW5kRGF0ZSA9IG51bGwpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMTQxNiw1MzIuMjQ2MSwxNDI2LDUzNi4yNDYxLDE0MTYsNTQwLjI0NjEsMTQyMCw1MzYuMjQ2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODA0JyB4Mj0nMTQyMicgeTE9JzUzNi4yNDYxJyB5Mj0nNTM2LjI0NjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMjcnIHg9JzgxMScgeT0nNTMwLjQzNzEnPmluc2VydCBESVNBQkxFIHJvdyAoZW5kX2RhdGUgPSBOVUxMKTwvdGV4dD48cGF0aCBkPSdNNzExLDU0OS4yNDYxIEw3MTEsNTk0LjI0NjEgTDg5Nyw1OTQuMjQ2MSBMODk3LDU1OS4yNDYxIEw4ODcsNTQ5LjI0NjEgTDcxMSw1NDkuMjQ2MSAnIGZpbGw9JyNGRUZGREQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J004ODcsNTQ5LjI0NjEgTDg4Nyw1NTkuMjQ2MSBMODk3LDU1OS4yNDYxIEw4ODcsNTQ5LjI0NjEgJyBmaWxsPScjRkVGRkREJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzcxNycgeT0nNTY4LjE0MzEnPkRlbGlucXVlbmN5OiBsaWZ0IGFjdGl2ZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjUnIHg9JzcxNycgeT0nNTg1Ljg0OTInPmNsYXNzaWZpY2F0aW9uIGFzIG9mIHN0YXJ0RGF0ZTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzMxNSw2MTkuMzY0MiwzMDUsNjIzLjM2NDIsMzE1LDYyNy4zNjQyLDMxMSw2MjMuMzY0Micgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzMwOScgeDI9JzgwMycgeTE9JzYyMy4zNjQyJyB5Mj0nNjIzLjM2NDInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMzcnIHg9JzMyMScgeT0nNjE3LjU1NTInPkNvbW1hbmRQcm9jZXNzaW5nUmVzdWx0KHJlc291cmNlSWQpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNjAsNjUxLjA3MDIsNTAsNjU1LjA3MDIsNjAsNjU5LjA3MDIsNTYsNjU1LjA3MDInIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPSc1NCcgeDI9JzMwMycgeTE9JzY1NS4wNzAyJyB5Mj0nNjU1LjA3MDInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0MicgeD0nNjYnIHk9JzY0OS4yNjEyJz4yMDAgT0s8L3RleHQ+PC9nPjwvc3ZnPg==)

Figure 15. Disable â request to persistence

##### Enable sequence

On enable the validator confirms an active disable exists, the write service persists a
dedicated `ENABLE` row and closes the open disable (at `enableDate - 1`), and then each feature
recomputes its own schedule.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc3MjFweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjE1MDRweDtoZWlnaHQ6NzIxcHg7YmFja2dyb3VuZDojRkZGRkZGOycgdmVyc2lvbj0nMS4xJyB2aWV3Qm94PScwIDAgMTUwNCA3MjEnIHdpZHRoPScxNTA0cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48cmVjdCBoZWlnaHQ9JzE2MS41MTInIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS41O2ZpbGw6bm9uZTsnIHdpZHRoPSczNDYuNScgeD0nNTc5LjUnIHk9JzM5Ni4xMjgxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSc0OScgeDI9JzQ5JyB5MT0nODQuMDY3OScgeTI9JzYzOC4wNTIxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPSczMDInIHgyPSczMDInIHkxPSc4NC4wNjc5JyB5Mj0nNjM4LjA1MjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtmaWxsOm5vbmU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzY1My41JyB4Mj0nNjUzLjUnIHkxPSc4NC4wNjc5JyB5Mj0nNjM4LjA1MjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTtmaWxsOm5vbmU7c3Ryb2tlLWRhc2hhcnJheTo1LjAsNS4wOycgeDE9JzkzNicgeDI9JzkzNicgeTE9Jzg0LjA2NzknIHkyPSc2MzguMDUyMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41O2ZpbGw6bm9uZTtzdHJva2UtZGFzaGFycmF5OjUuMCw1LjA7JyB4MT0nMTEzNC41JyB4Mj0nMTEzNC41JyB5MT0nODQuMDY3OScgeTI9JzYzOC4wNTIxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7ZmlsbDpub25lO3N0cm9rZS1kYXNoYXJyYXk6NS4wLDUuMDsnIHgxPScxMjc3LjUnIHgyPScxMjc3LjUnIHkxPSc4NC4wNjc5JyB5Mj0nNjM4LjA1MjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4MicgeD0nNScgeT0nNzkuOTY1OSc+TG9hbiBPZmZpY2VyPC90ZXh0PjxlbGxpcHNlIGN4PSc0OScgY3k9JzEzLjUnIGZpbGw9JyNFMkUyRjAnIHJ4PSc4JyByeT0nOCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTQ5LDIxLjUgTDQ5LDQ4LjUgTTM2LDI5LjUgTDYyLDI5LjUgTTQ5LDQ4LjUgTDM2LDYzLjUgTTQ5LDQ4LjUgTDYyLDYzLjUgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc4MicgeD0nNScgeT0nNjUyLjAxOCc+TG9hbiBPZmZpY2VyPC90ZXh0PjxlbGxpcHNlIGN4PSc0OScgY3k9JzY2NC42MicgZmlsbD0nI0UyRTJGMCcgcng9JzgnIHJ5PSc4JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cGF0aCBkPSdNNDksNjcyLjYyIEw0OSw2OTkuNjIgTTM2LDY4MC42MiBMNjIsNjgwLjYyIE00OSw2OTkuNjIgTDM2LDcxNC42MiBNNDksNjk5LjYyIEw2Miw3MTQuNjIgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cmVjdCBmaWxsPScjRTJFMkYwJyBoZWlnaHQ9JzMzLjA2NzknIHJ4PScyLjUnIHJ5PScyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9Jzk4JyB4PScyNTMnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nODQnIHg9JzI2MCcgeT0nNzEuOTY1OSc+QXBpUmVzb3VyY2U8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPSc5OCcgeD0nMjUzJyB5PSc2MzcuMDUyMScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzE0JyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg0JyB4PScyNjAnIHk9JzY1OS4wMTgnPkFwaVJlc291cmNlPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTI5JyB4PSc1ODkuNScgeT0nNTAnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTUnIHg9JzU5Ni41JyB5PSc3MS45NjU5Jz5Xcml0ZVNlcnZpY2VJbXBsPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTI5JyB4PSc1ODkuNScgeT0nNjM3LjA1MjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTUnIHg9JzU5Ni41JyB5PSc2NTkuMDE4Jz5Xcml0ZVNlcnZpY2VJbXBsPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM4JyB4PSc4NjcnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI0JyB4PSc4NzQnIHk9JzcxLjk2NTknPlBhcnNlQW5kVmFsaWRhdG9yPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTM4JyB4PSc4NjcnIHk9JzYzNy4wNTIxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI0JyB4PSc4NzQnIHk9JzY1OS4wMTgnPlBhcnNlQW5kVmFsaWRhdG9yPC90ZXh0PjxyZWN0IGZpbGw9JyNFMkUyRjAnIGhlaWdodD0nMzMuMDY3OScgcng9JzIuNScgcnk9JzIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTI3JyB4PScxMDcxLjUnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTEzJyB4PScxMDc4LjUnIHk9JzcxLjk2NTknPkFjdGlvblJlcG9zaXRvcnk8L3RleHQ+PHJlY3QgZmlsbD0nI0UyRTJGMCcgaGVpZ2h0PSczMy4wNjc5JyByeD0nMi41JyByeT0nMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjcnIHg9JzEwNzEuNScgeT0nNjM3LjA1MjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTMnIHg9JzEwNzguNScgeT0nNjU5LjAxOCc+QWN0aW9uUmVwb3NpdG9yeTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzEyMDguNScgeT0nNzkuOTY1OSc+bV93Y19sb2FuXypfYWN0aW9uPC90ZXh0PjxwYXRoIGQ9J00xMjYwLDI5IEMxMjYwLDE5IDEyNzgsMTkgMTI3OCwxOSBDMTI3OCwxOSAxMjk2LDE5IDEyOTYsMjkgTDEyOTYsNTUgQzEyOTYsNjUgMTI3OCw2NSAxMjc4LDY1IEMxMjc4LDY1IDEyNjAsNjUgMTI2MCw1NSBMMTI2MCwyOSAnIGZpbGw9JyNFMkUyRjAnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS41OycvPjxwYXRoIGQ9J00xMjYwLDI5IEMxMjYwLDM5IDEyNzgsMzkgMTI3OCwzOSBDMTI3OCwzOSAxMjk2LDM5IDEyOTYsMjkgJyBmaWxsPSdub25lJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxNCcgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMzMnIHg9JzEyMDguNScgeT0nNjUyLjAxOCc+bV93Y19sb2FuXypfYWN0aW9uPC90ZXh0PjxwYXRoIGQ9J00xMjYwLDY2Ni4xMiBDMTI2MCw2NTYuMTIgMTI3OCw2NTYuMTIgMTI3OCw2NTYuMTIgQzEyNzgsNjU2LjEyIDEyOTYsNjU2LjEyIDEyOTYsNjY2LjEyIEwxMjk2LDY5Mi4xMiBDMTI5Niw3MDIuMTIgMTI3OCw3MDIuMTIgMTI3OCw3MDIuMTIgQzEyNzgsNzAyLjEyIDEyNjAsNzAyLjEyIDEyNjAsNjkyLjEyIEwxMjYwLDY2Ni4xMiAnIGZpbGw9JyNFMkUyRjAnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS41OycvPjxwYXRoIGQ9J00xMjYwLDY2Ni4xMiBDMTI2MCw2NzYuMTIgMTI3OCw2NzYuMTIgMTI3OCw2NzYuMTIgQzEyNzgsNjc2LjEyIDEyOTYsNjc2LjEyIDEyOTYsNjY2LjEyICcgZmlsbD0nbm9uZScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjU7Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScyOTAsMTMxLjQ3OTksMzAwLDEzNS40Nzk5LDI5MCwxMzkuNDc5OSwyOTQsMTM1LjQ3OTknIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQ5JyB4Mj0nMjk2JyB5MT0nMTM1LjQ3OTknIHkyPScxMzUuNDc5OScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE2OScgeD0nNTYnIHk9JzExMS45NjQ5Jz5QT1NUIC4uLi9kZWxpbnF1ZW5jeS1hY3Rpb25zPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIyOScgeD0nNTYnIHk9JzEyOS42NzA5Jz57ICJhY3Rpb24iOiJlbmFibGUiLCAic3RhcnREYXRlIjogdG9kYXkgfTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzY0MiwxNjMuMTg2LDY1MiwxNjcuMTg2LDY0MiwxNzEuMTg2LDY0NiwxNjcuMTg2JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMDInIHgyPSc2NDgnIHkxPScxNjcuMTg2JyB5Mj0nMTY3LjE4NicvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzMyOCcgeD0nMzA5JyB5PScxNjEuMzc3Jz5jcmVhdGVBY3Rpb24obG9hbklkLCBjb21tYW5kKSAodmlhIENSRUFURSBjb21tYW5kKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzkyNCwxOTQuODkyLDkzNCwxOTguODkyLDkyNCwyMDIuODkyLDkyOCwxOTguODkyJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2NTQnIHgyPSc5MzAnIHkxPScxOTguODkyJyB5Mj0nMTk4Ljg5MicvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI1OCcgeD0nNjYxJyB5PScxOTMuMDgzJz52YWxpZGF0ZUFuZFBhcnNlKGNvbW1hbmQsIGxvYW4sIGV4aXN0aW5nKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzExMjMsMjI2LjU5OCwxMTMzLDIzMC41OTgsMTEyMywyMzQuNTk4LDExMjcsMjMwLjU5OCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nOTM2JyB4Mj0nMTEyOScgeTE9JzIzMC41OTgnIHkyPScyMzAuNTk4Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTc1JyB4PSc5NDMnIHk9JzIyNC43ODknPmlzRGlzYWJsZWRBc09mKGxvYW5JZCwgdG9kYXkpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nOTQ3LDI1OC4zMDQsOTM3LDI2Mi4zMDQsOTQ3LDI2Ni4zMDQsOTQzLDI2Mi4zMDQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPSc5NDEnIHgyPScxMTM0JyB5MT0nMjYyLjMwNCcgeTI9JzI2Mi4zMDQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjMnIHg9Jzk1MycgeT0nMjU2LjQ5NSc+dHJ1ZSAoYWN0aXZlIERJU0FCTEUgZm91bmQpPC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNjY1LDI5MC4wMSw2NTUsMjk0LjAxLDY2NSwyOTguMDEsNjYxLDI5NC4wMScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzY1OScgeDI9JzkzNScgeTE9JzI5NC4wMScgeTI9JzI5NC4wMScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEzMScgeD0nNjcxJyB5PScyODguMjAxJz5wYXJzZWQgRU5BQkxFIGFjdGlvbjwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzEyNjYsMzIxLjcxNiwxMjc2LDMyNS43MTYsMTI2NiwzMjkuNzE2LDEyNzAsMzI1LjcxNicgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjU0JyB4Mj0nMTI3MicgeTE9JzMyNS43MTYnIHkyPSczMjUuNzE2Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjA5JyB4PSc2NjEnIHk9JzMxOS45MDcnPmNsb3NlIGFjdGl2ZSBESVNBQkxFIChzZXQgZW5kX2RhdGUpPC90ZXh0PjxwYXRoIGQ9J00xMjgzLDMzOC43MTYgTDEyODMsMzgzLjcxNiBMMTQ5NywzODMuNzE2IEwxNDk3LDM0OC43MTYgTDE0ODcsMzM4LjcxNiBMMTI4MywzMzguNzE2ICcgZmlsbD0nI0ZFRkZERCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHBhdGggZD0nTTE0ODcsMzM4LjcxNiBMMTQ4NywzNDguNzE2IEwxNDk3LDM0OC43MTYgTDE0ODcsMzM4LjcxNiAnIGZpbGw9JyNGRUZGREQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE4NCcgeD0nMTI4OScgeT0nMzU3LjYxMzEnPkRlbGlucXVlbmN5OiBlbmRfZGF0ZSA9IHRvZGF5PC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE5MycgeD0nMTI4OScgeT0nMzc1LjMxOTEnPkJyZWFjaDogZW5kX2RhdGUgPSB0b2RheSAtIDEgZGF5PC90ZXh0PjxwYXRoIGQ9J001NzkuNSwzOTYuMTI4MSBMNjQyLjUsMzk2LjEyODEgTDY0Mi41LDQwNS44MzQxIEw2MzIuNSw0MTUuODM0MSBMNTc5LjUsNDE1LjgzNDEgTDU3OS41LDM5Ni4xMjgxICcgZmlsbD0nI0VFRUVFRScgc3R5bGU9J3N0cm9rZTojMDAwMDAwO3N0cm9rZS13aWR0aDoxLjU7Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScxNjEuNTEyJyBzdHlsZT0nc3Ryb2tlOiMwMDAwMDA7c3Ryb2tlLXdpZHRoOjEuNTsnIHdpZHRoPSczNDYuNScgeD0nNTc5LjUnIHk9JzM5Ni4xMjgxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGZvbnQtd2VpZ2h0PSdib2xkJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE4JyB4PSc1OTQuNScgeT0nNDExLjAyNTEnPmFsdDwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzYnIHg9JzY1Ny41JyB5PSc0MDkuODg3Jz5bRGVsaW5xdWVuY3ldPC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzY1NCcgeDI9JzY5NicgeTE9JzQ1Ny4yNDYxJyB5Mj0nNDU3LjI0NjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2OTYnIHgyPSc2OTYnIHkxPSc0NTcuMjQ2MScgeTI9JzQ3MC4yNDYxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjU1JyB4Mj0nNjk2JyB5MT0nNDcwLjI0NjEnIHkyPSc0NzAuMjQ2MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNjY1LDQ2Ni4yNDYxLDY1NSw0NzAuMjQ2MSw2NjUsNDc0LjI0NjEsNjYxLDQ3MC4yNDYxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMjYnIHg9JzY2MScgeT0nNDMzLjczMTEnPmV4dGVuZCBvcGVuIHBlcmlvZHMgYnkgZGlzYWJsZWQgZGF5czwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMDgnIHg9JzY2MScgeT0nNDUxLjQzNzEnPihwYXVzZS1saWtlKSArIHJlLWNsYXNzaWZ5IGFzIG9mIHRvZGF5PC90ZXh0PjxsaW5lIHN0eWxlPSdzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPSc1NzkuNScgeDI9JzkyNicgeTE9JzQ3OS4yNDYxJyB5Mj0nNDc5LjI0NjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgZm9udC13ZWlnaHQ9J2JvbGQnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNDcnIHg9JzU4NC41JyB5PSc0OTEuMDA1Jz5bQnJlYWNoXTwvdGV4dD48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2NTQnIHgyPSc2OTYnIHkxPSc1MzYuNjQwMScgeTI9JzUzNi42NDAxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjk2JyB4Mj0nNjk2JyB5MT0nNTM2LjY0MDEnIHkyPSc1NDkuNjQwMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzY1NScgeDI9JzY5NicgeTE9JzU0OS42NDAxJyB5Mj0nNTQ5LjY0MDEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzY2NSw1NDUuNjQwMSw2NTUsNTQ5LjY0MDEsNjY1LDU1My42NDAxLDY2MSw1NDkuNjQwMScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTMnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTg3JyB4PSc2NjEnIHk9JzUxMy4xMjUnPnJlcHJvY2Vzc0JyZWFjaFNjaGVkdWxlKGxvYW4pPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI1MycgeD0nNjYxJyB5PSc1MzAuODMxJz4oYXBwbHkgcmVwYXltZW50cyBhY2NydWVkIHdoaWxlIGRpc2FibGVkKTwvdGV4dD48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzMxMyw1ODQuMzQ2MSwzMDMsNTg4LjM0NjEsMzEzLDU5Mi4zNDYxLDMwOSw1ODguMzQ2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7c3Ryb2tlLWRhc2hhcnJheToyLjAsMi4wOycgeDE9JzMwNycgeDI9JzY1MycgeTE9JzU4OC4zNDYxJyB5Mj0nNTg4LjM0NjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjUnIHg9JzMxOScgeT0nNTgyLjUzNzEnPkNvbW1hbmRQcm9jZXNzaW5nUmVzdWx0PC90ZXh0Pjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNjAsNjE2LjA1MjEsNTAsNjIwLjA1MjEsNjAsNjI0LjA1MjEsNTYsNjIwLjA1MjEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wO3N0cm9rZS1kYXNoYXJyYXk6Mi4wLDIuMDsnIHgxPSc1NCcgeDI9JzMwMScgeTE9JzYyMC4wNTIxJyB5Mj0nNjIwLjA1MjEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0MicgeD0nNjYnIHk9JzYxNC4yNDMxJz4yMDAgT0s8L3RleHQ+PC9nPjwvc3ZnPg==)

Figure 16. Enable â closing the window and recomputing

##### Decision flow (validation)

The activity below captures the validation gate shared by disable and enable.

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PScxMzE5cHgnIHByZXNlcnZlQXNwZWN0UmF0aW89J25vbmUnIHN0eWxlPSd3aWR0aDo5MzVweDtoZWlnaHQ6MTMxOXB4O2JhY2tncm91bmQ6I0ZGRkZGRjsnIHZlcnNpb249JzEuMScgdmlld0JveD0nMCAwIDkzNSAxMzE5JyB3aWR0aD0nOTM1cHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48ZWxsaXBzZSBjeD0nMzQ2LjI1JyBjeT0nMjAnIGZpbGw9JyMyMjIyMjInIHJ4PScxMCcgcnk9JzEwJyBzdHlsZT0nc3Ryb2tlOiMyMjIyMjI7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cmVjdCBmaWxsPScjRjFGMUYxJyBoZWlnaHQ9JzM2LjM0NDEnIHJ4PScxMi41JyByeT0nMTIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTk5JyB4PScyNDYuNzUnIHk9JzUwJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTc5JyB4PScyNTYuNzUnIHk9JzcyLjgyODEnPlJlY2VpdmUgYWN0aW9uIGRpc2FibGUgb3IgZW5hYmxlPC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPSc3OCcgeD0nMzA3LjI1JyB5PScxNTUuODM1MScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzU4JyB4PSczMTcuMjUnIHk9JzE3OC42NjMxJz5SZWplY3QgNDAzPC90ZXh0PjxlbGxpcHNlIGN4PSczNDYuMjUnIGN5PScyMzAuNTA3MScgcng9JzExJyByeT0nMTEnIHN0eWxlPSdzdHJva2U6IzIyMjIyMjtzdHJva2Utd2lkdGg6MS4wO2ZpbGw6bm9uZTsnLz48ZWxsaXBzZSBjeD0nMzQ2LjI1JyBjeT0nMjMwLjUwNzEnIGZpbGw9JyMyMjIyMjInIHJ4PSc2JyByeT0nNicgc3R5bGU9J3N0cm9rZTojMTExMTExO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nI0YxRjFGMScgcG9pbnRzPScyNDcuMjUsMTA2LjM0NDEsNDQ1LjI1LDEwNi4zNDQxLDQ1Ny4yNSwxMTguMzQ0MSw0NDUuMjUsMTMwLjM0NDEsMjQ3LjI1LDEzMC4zNDQxLDIzNS4yNSwxMTguMzQ0MSwyNDcuMjUsMTA2LjM0NDEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE0JyB4PSczNTAuMjUnIHk9JzE0Mi4xMDMnPm5vPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE5OCcgeD0nMjQ3LjI1JyB5PScxMjIuNjEyMSc+QmFzZSBhbmQgZGlzYWJsZSBwZXJtaXNzaW9uIGdyYW50ZWQ/PC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxNzUnIHg9JzI1OC43NScgeT0nMzMyLjk5ODEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTUnIHg9JzI2OC43NScgeT0nMzU1LjgyNjEnPlJlamVjdCA0MDAgaW52YWxpZC5sb2FuLnN0YXRlPC90ZXh0PjxlbGxpcHNlIGN4PSczNDYuMjUnIGN5PSc0MDcuNjcwMScgcng9JzExJyByeT0nMTEnIHN0eWxlPSdzdHJva2U6IzIyMjIyMjtzdHJva2Utd2lkdGg6MS4wO2ZpbGw6bm9uZTsnLz48ZWxsaXBzZSBjeD0nMzQ2LjI1JyBjeT0nNDA3LjY3MDEnIGZpbGw9JyMyMjIyMjInIHJ4PSc2JyByeT0nNicgc3R5bGU9J3N0cm9rZTojMTExMTExO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nI0YxRjFGMScgcG9pbnRzPSczMDUuMjUsMjgzLjUwNzEsMzg3LjI1LDI4My41MDcxLDM5OS4yNSwyOTUuNTA3MSwzODcuMjUsMzA3LjUwNzEsMzA1LjI1LDMwNy41MDcxLDI5My4yNSwyOTUuNTA3MSwzMDUuMjUsMjgzLjUwNzEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE0JyB4PSczNTAuMjUnIHk9JzMxOS4yNjYnPm5vPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzgyJyB4PSczMDUuMjUnIHk9JzI5OS43NzUxJz5Mb2FuIGlzIEFDVElWRT88L3RleHQ+PHJlY3QgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSczNi4zNDQxJyByeD0nMTIuNScgcnk9JzEyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzI1MCcgeD0nMjIxLjI1JyB5PSc1MTAuMTYxMScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzMCcgeD0nMjMxLjI1JyB5PSc1MzIuOTg5Mic+UmVqZWN0IDQwMCBtdXN0LmJlLmN1cnJlbnQuYnVzaW5lc3MuZGF0ZTwvdGV4dD48ZWxsaXBzZSBjeD0nMzQ2LjI1JyBjeT0nNTg0LjgzMzEnIHJ4PScxMScgcnk9JzExJyBzdHlsZT0nc3Ryb2tlOiMyMjIyMjI7c3Ryb2tlLXdpZHRoOjEuMDtmaWxsOm5vbmU7Jy8+PGVsbGlwc2UgY3g9JzM0Ni4yNScgY3k9JzU4NC44MzMxJyBmaWxsPScjMjIyMjIyJyByeD0nNicgcnk9JzYnIHN0eWxlPSdzdHJva2U6IzExMTExMTtzdHJva2Utd2lkdGg6MS4wOycvPjxwb2x5Z29uIGZpbGw9JyNGMUYxRjEnIHBvaW50cz0nMjY0LjI1LDQ2MC42NzAxLDQyOC4yNSw0NjAuNjcwMSw0NDAuMjUsNDcyLjY3MDEsNDI4LjI1LDQ4NC42NzAxLDI2NC4yNSw0ODQuNjcwMSwyNTIuMjUsNDcyLjY3MDEsMjY0LjI1LDQ2MC42NzAxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNCcgeD0nMzUwLjI1JyB5PSc0OTYuNDI5Jz5ubzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNjQnIHg9JzI2NC4yNScgeT0nNDc2LjkzODEnPnN0YXJ0RGF0ZSBlcXVhbHMgYnVzaW5lc3MgZGF0ZT88L3RleHQ+PHJlY3QgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSczNi4zNDQxJyByeD0nMTIuNScgcnk9JzEyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzMxNycgeD0nMTg3Ljc1JyB5PSc2ODcuMzI0MScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5NycgeD0nMTk3Ljc1JyB5PSc3MTAuMTUyMic+UmVqZWN0IDQwMCBtdXN0Lm5vdC5iZS5wcm92aWRlZC5mb3IuZGlzYWJsZS5vci5lbmFibGU8L3RleHQ+PGVsbGlwc2UgY3g9JzM0Ni4yNScgY3k9Jzc2MS45OTYxJyByeD0nMTEnIHJ5PScxMScgc3R5bGU9J3N0cm9rZTojMjIyMjIyO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycvPjxlbGxpcHNlIGN4PSczNDYuMjUnIGN5PSc3NjEuOTk2MScgZmlsbD0nIzIyMjIyMicgcng9JzYnIHJ5PSc2JyBzdHlsZT0nc3Ryb2tlOiMxMTExMTE7c3Ryb2tlLXdpZHRoOjEuMDsnLz48cG9seWdvbiBmaWxsPScjRjFGMUYxJyBwb2ludHM9JzI5Ni4yNSw2MzcuODMzMSwzOTYuMjUsNjM3LjgzMzEsNDA4LjI1LDY0OS44MzMxLDM5Ni4yNSw2NjEuODMzMSwyOTYuMjUsNjYxLjgzMzEsMjg0LjI1LDY0OS44MzMxLDI5Ni4yNSw2MzcuODMzMScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTEnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTcnIHg9JzM1MC4yNScgeT0nNjczLjU5Mic+eWVzPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwMCcgeD0nMjk2LjI1JyB5PSc2NTQuMTAxMSc+ZW5kRGF0ZSBwcm92aWRlZD88L3RleHQ+PHBvbHlnb24gZmlsbD0nI0YxRjFGMScgcG9pbnRzPSczMDIuMjUsODE0Ljk5NjEsMzkwLjI1LDgxNC45OTYxLDQwMi4yNSw4MjYuOTk2MSwzOTAuMjUsODM4Ljk5NjEsMzAyLjI1LDgzOC45OTYxLDI5MC4yNSw4MjYuOTk2MSwzMDIuMjUsODE0Ljk5NjEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9Jzg4JyB4PSczMDIuMjUnIHk9JzgzMS4yNjQxJz5hY3Rpb24gaXMgZGlzYWJsZT88L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTEnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTcnIHg9JzI3My4yNScgeT0nODIzLjc3MzEnPnllczwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczNScgeD0nNDAyLjI1JyB5PSc4MjMuNzczMSc+ZW5hYmxlPC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxNzMnIHg9JzMxLjUnIHk9Jzg5OC40ODcxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTUzJyB4PSc0MS41JyB5PSc5MjEuMzE1Mic+UmVqZWN0IDQwMCBhbHJlYWR5LmRpc2FibGVkPC90ZXh0PjxlbGxpcHNlIGN4PScxMTgnIGN5PSc5NzMuMTU5MScgcng9JzExJyByeT0nMTEnIHN0eWxlPSdzdHJva2U6IzIyMjIyMjtzdHJva2Utd2lkdGg6MS4wO2ZpbGw6bm9uZTsnLz48ZWxsaXBzZSBjeD0nMTE4JyBjeT0nOTczLjE1OTEnIGZpbGw9JyMyMjIyMjInIHJ4PSc2JyByeT0nNicgc3R5bGU9J3N0cm9rZTojMTExMTExO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nI0YxRjFGMScgcG9pbnRzPSc3Miw4NDguOTk2MSwxNjQsODQ4Ljk5NjEsMTc2LDg2MC45OTYxLDE2NCw4NzIuOTk2MSw3Miw4NzIuOTk2MSw2MCw4NjAuOTk2MSw3Miw4NDguOTk2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTEnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTcnIHg9JzEyMicgeT0nODg0Ljc1NSc+eWVzPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzExJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzkyJyB4PSc3MicgeT0nODY1LjI2NDEnPkFscmVhZHkgZGlzYWJsZWQ/PC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScyMTQnIHg9JzExJyB5PScxMDI2LjE1OTEnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxOTQnIHg9JzIxJyB5PScxMDQ4Ljk4NzInPlBlcnNpc3QgRElTQUJMRSByb3csIGVuZF9kYXRlIG51bGw8L3RleHQ+PHBhdGggZD0nTTIwMCwxMDg2LjgyMjMgTDIwMCwxMDk2LjY3NTMgTDE4MCwxMTAwLjY3NTMgTDIwMCwxMTA0LjY3NTMgTDIwMCwxMTE0LjUyODMgQTAsMCAwIDAgMCAyMDAsMTExNC41MjgzIEwzOTYsMTExNC41MjgzIEEwLDAgMCAwIDAgMzk2LDExMTQuNTI4MyBMMzk2LDEwOTYuODIyMyBMMzg2LDEwODYuODIyMyBMMjAwLDEwODYuODIyMyBBMCwwIDAgMCAwIDIwMCwxMDg2LjgyMjMgJyBmaWxsPScjRkVGRkREJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48cGF0aCBkPSdNMzg2LDEwODYuODIyMyBMMzg2LDEwOTYuODIyMyBMMzk2LDEwOTYuODIyMyBMMzg2LDEwODYuODIyMyAnIGZpbGw9JyNGRUZGREQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3NScgeD0nMjA2JyB5PScxMTA1LjcxOTMnPmRlbGlucXVlbmN5IGxpZnRzIGNsYXNzaWZpY2F0aW9uPC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMjQnIHg9JzU2JyB5PScxMDgyLjUwMzInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDQnIHg9JzY2JyB5PScxMTA1LjMzMTMnPkZlYXR1cmUgc2lkZSBlZmZlY3Q8L3RleHQ+PHJlY3QgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSczNi4zNDQxJyByeD0nMTIuNScgcnk9JzEyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzIyOScgeD0nNDYwJyB5PSc4OTguNDg3MScvPjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIwOScgeD0nNDcwJyB5PSc5MjEuMzE1Mic+UmVqZWN0IDQwMCBuby5hY3RpdmUuZGlzYWJsZS50by5lbmFibGU8L3RleHQ+PGVsbGlwc2UgY3g9JzU3NC41JyBjeT0nOTczLjE1OTEnIHJ4PScxMScgcnk9JzExJyBzdHlsZT0nc3Ryb2tlOiMyMjIyMjI7c3Ryb2tlLXdpZHRoOjEuMDtmaWxsOm5vbmU7Jy8+PGVsbGlwc2UgY3g9JzU3NC41JyBjeT0nOTczLjE1OTEnIGZpbGw9JyMyMjIyMjInIHJ4PSc2JyByeT0nNicgc3R5bGU9J3N0cm9rZTojMTExMTExO3N0cm9rZS13aWR0aDoxLjA7Jy8+PHBvbHlnb24gZmlsbD0nI0YxRjFGMScgcG9pbnRzPSc1MjAuNSw4NDguOTk2MSw2MjguNSw4NDguOTk2MSw2NDAuNSw4NjAuOTk2MSw2MjguNSw4NzIuOTk2MSw1MjAuNSw4NzIuOTk2MSw1MDguNSw4NjAuOTk2MSw1MjAuNSw4NDguOTk2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTEnIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTQnIHg9JzU3OC41JyB5PSc4ODQuNzU1Jz5ubzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMScgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMDgnIHg9JzUyMC41JyB5PSc4NjUuMjY0MSc+QWN0aXZlIGRpc2FibGUgZXhpc3RzPzwvdGV4dD48cmVjdCBmaWxsPScjRjFGMUYxJyBoZWlnaHQ9JzM2LjM0NDEnIHJ4PScxMi41JyByeT0nMTIuNScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7JyB3aWR0aD0nMTMwJyB4PSc1MDkuNScgeT0nMTAyNi4xNTkxJy8+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTEwJyB4PSc1MTkuNScgeT0nMTA0OC45ODcyJz5QZXJzaXN0IEVOQUJMRSByb3c8L3RleHQ+PHJlY3QgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSczNi4zNDQxJyByeD0nMTIuNScgcnk9JzEyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzMxNycgeD0nNDE2JyB5PScxMDgyLjUwMzInLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOTcnIHg9JzQyNicgeT0nMTEwNS4zMzEzJz5DbG9zZSBESVNBQkxFIHJvdywgc3RhbXAgZW5kX2RhdGUgPSBlbmFibGVEYXRlIC0gMTwvdGV4dD48cGF0aCBkPSdNNjYyLjUsMTEzNC4zMTM0IEw2NjIuNSwxMTUzLjAxOTQgTDY0Mi41LDExNTcuMDE5NCBMNjYyLjUsMTE2MS4wMTk0IEw2NjIuNSwxMTc5LjcyNTQgQTAsMCAwIDAgMCA2NjIuNSwxMTc5LjcyNTQgTDkyMy41LDExNzkuNzI1NCBBMCwwIDAgMCAwIDkyMy41LDExNzkuNzI1NCBMOTIzLjUsMTE0NC4zMTM0IEw5MTMuNSwxMTM0LjMxMzQgTDY2Mi41LDExMzQuMzEzNCBBMCwwIDAgMCAwIDY2Mi41LDExMzQuMzEzNCAnIGZpbGw9JyNGRUZGREQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41OycvPjxwYXRoIGQ9J005MTMuNSwxMTM0LjMxMzQgTDkxMy41LDExNDQuMzEzNCBMOTIzLjUsMTE0NC4zMTM0IEw5MTMuNSwxMTM0LjMxMzQgJyBmaWxsPScjRkVGRkREJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMycgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNDAnIHg9JzY2OC41JyB5PScxMTUzLjIxMDQnPmRlbGlucXVlbmN5OiBleHRlbmQgcGVyaW9kcyArIHJlLWNsYXNzaWZ5PC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEzJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIwNScgeD0nNjY4LjUnIHk9JzExNzAuOTE2NCc+YnJlYWNoOiByZXByb2Nlc3MgYnJlYWNoIHNjaGVkdWxlPC90ZXh0PjxyZWN0IGZpbGw9JyNGMUYxRjEnIGhlaWdodD0nMzYuMzQ0MScgcng9JzEyLjUnIHJ5PScxMi41JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjAuNTsnIHdpZHRoPScxMzYnIHg9JzUwNi41JyB5PScxMTM4Ljg0NzMnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTYnIHg9JzUxNi41JyB5PScxMTYxLjY3NTQnPlJlY29tcHV0ZSBzY2hlZHVsZTwvdGV4dD48cG9seWdvbiBmaWxsPScjRjFGMUYxJyBwb2ludHM9JzM0Ni4yNSwxMTg1LjcyNTQsMzU4LjI1LDExOTcuNzI1NCwzNDYuMjUsMTIwOS43MjU0LDMzNC4yNSwxMTk3LjcyNTQsMzQ2LjI1LDExODUuNzI1NCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDowLjU7Jy8+PHJlY3QgZmlsbD0nI0YxRjFGMScgaGVpZ2h0PSczNi4zNDQxJyByeD0nMTIuNScgcnk9JzEyLjUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MC41Oycgd2lkdGg9JzE3MScgeD0nMjYwLjc1JyB5PScxMjI5LjcyNTQnLz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTEnIHg9JzI3MC43NScgeT0nMTI1Mi41NTM1Jz5SZXR1cm4gMjAwIHdpdGggcmVzb3VyY2VJZDwvdGV4dD48ZWxsaXBzZSBjeD0nMzQ2LjI1JyBjeT0nMTI5Ny4wNjk1JyByeD0nMTEnIHJ5PScxMScgc3R5bGU9J3N0cm9rZTojMjIyMjIyO3N0cm9rZS13aWR0aDoxLjA7ZmlsbDpub25lOycvPjxlbGxpcHNlIGN4PSczNDYuMjUnIGN5PScxMjk3LjA2OTUnIGZpbGw9JyMyMjIyMjInIHJ4PSc2JyByeT0nNicgc3R5bGU9J3N0cm9rZTojMTExMTExO3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nMzAnIHkyPSc1MCcvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzQyLjI1LDQwLDM0Ni4yNSw1MCwzNTAuMjUsNDAsMzQ2LjI1LDQ0JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYuMjUnIHgyPSczNDYuMjUnIHkxPScxOTIuMTc5MicgeTI9JzIxOS41MDcxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsMjA5LjUwNzEsMzQ2LjI1LDIxOS41MDcxLDM1MC4yNSwyMDkuNTA3MSwzNDYuMjUsMjEzLjUwNzEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0Ni4yNScgeDI9JzM0Ni4yNScgeTE9JzEzMC4zNDQxJyB5Mj0nMTU1LjgzNTEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSwxNDUuODM1MSwzNDYuMjUsMTU1LjgzNTEsMzUwLjI1LDE0NS44MzUxLDM0Ni4yNSwxNDkuODM1MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDU3LjI1JyB4Mj0nNDY5LjI1JyB5MT0nMTE4LjM0NDEnIHkyPScxMTguMzQ0MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNDY1LjI1LDE4OS41MDcxLDQ2OS4yNSwxOTkuNTA3MSw0NzMuMjUsMTg5LjUwNzEsNDY5LjI1LDE5My41MDcxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0NjkuMjUnIHgyPSc0NjkuMjUnIHkxPScxMTguMzQ0MScgeTI9JzI2My41MDcxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDY5LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nMjYzLjUwNzEnIHkyPScyNjMuNTA3MScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0Ni4yNScgeDI9JzM0Ni4yNScgeTE9JzI2My41MDcxJyB5Mj0nMjgzLjUwNzEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSwyNzMuNTA3MSwzNDYuMjUsMjgzLjUwNzEsMzUwLjI1LDI3My41MDcxLDM0Ni4yNSwyNzcuNTA3MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nODYuMzQ0MScgeTI9JzEwNi4zNDQxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsOTYuMzQ0MSwzNDYuMjUsMTA2LjM0NDEsMzUwLjI1LDk2LjM0NDEsMzQ2LjI1LDEwMC4zNDQxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYuMjUnIHgyPSczNDYuMjUnIHkxPSczNjkuMzQyMicgeTI9JzM5Ni42NzAxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsMzg2LjY3MDEsMzQ2LjI1LDM5Ni42NzAxLDM1MC4yNSwzODYuNjcwMSwzNDYuMjUsMzkwLjY3MDEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0Ni4yNScgeDI9JzM0Ni4yNScgeTE9JzMwNy41MDcxJyB5Mj0nMzMyLjk5ODEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSwzMjIuOTk4MSwzNDYuMjUsMzMyLjk5ODEsMzUwLjI1LDMyMi45OTgxLDM0Ni4yNSwzMjYuOTk4MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzk5LjI1JyB4Mj0nNDQzLjc1JyB5MT0nMjk1LjUwNzEnIHkyPScyOTUuNTA3MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNDM5Ljc1LDM2Ni42NzAxLDQ0My43NSwzNzYuNjcwMSw0NDcuNzUsMzY2LjY3MDEsNDQzLjc1LDM3MC42NzAxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0NDMuNzUnIHgyPSc0NDMuNzUnIHkxPScyOTUuNTA3MScgeTI9JzQ0MC42NzAxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDQzLjc1JyB4Mj0nMzQ2LjI1JyB5MT0nNDQwLjY3MDEnIHkyPSc0NDAuNjcwMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0Ni4yNScgeDI9JzM0Ni4yNScgeTE9JzQ0MC42NzAxJyB5Mj0nNDYwLjY3MDEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSw0NTAuNjcwMSwzNDYuMjUsNDYwLjY3MDEsMzUwLjI1LDQ1MC42NzAxLDM0Ni4yNSw0NTQuNjcwMScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nNTQ2LjUwNTInIHkyPSc1NzMuODMzMScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzQyLjI1LDU2My44MzMxLDM0Ni4yNSw1NzMuODMzMSwzNTAuMjUsNTYzLjgzMzEsMzQ2LjI1LDU2Ny44MzMxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYuMjUnIHgyPSczNDYuMjUnIHkxPSc0ODQuNjcwMScgeTI9JzUxMC4xNjExJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsNTAwLjE2MTEsMzQ2LjI1LDUxMC4xNjExLDM1MC4yNSw1MDAuMTYxMSwzNDYuMjUsNTA0LjE2MTEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQ0MC4yNScgeDI9JzQ4MS4yNScgeTE9JzQ3Mi42NzAxJyB5Mj0nNDcyLjY3MDEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzQ3Ny4yNSw1NDMuODMzMSw0ODEuMjUsNTUzLjgzMzEsNDg1LjI1LDU0My44MzMxLDQ4MS4yNSw1NDcuODMzMScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDgxLjI1JyB4Mj0nNDgxLjI1JyB5MT0nNDcyLjY3MDEnIHkyPSc2MTcuODMzMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQ4MS4yNScgeDI9JzM0Ni4yNScgeTE9JzYxNy44MzMxJyB5Mj0nNjE3LjgzMzEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYuMjUnIHgyPSczNDYuMjUnIHkxPSc2MTcuODMzMScgeTI9JzYzNy44MzMxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsNjI3LjgzMzEsMzQ2LjI1LDYzNy44MzMxLDM1MC4yNSw2MjcuODMzMSwzNDYuMjUsNjMxLjgzMzEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzM0Ni4yNScgeDI9JzM0Ni4yNScgeTE9JzcyMy42NjgyJyB5Mj0nNzUwLjk5NjEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSw3NDAuOTk2MSwzNDYuMjUsNzUwLjk5NjEsMzUwLjI1LDc0MC45OTYxLDM0Ni4yNSw3NDQuOTk2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nNjYxLjgzMzEnIHkyPSc2ODcuMzI0MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzQyLjI1LDY3Ny4zMjQxLDM0Ni4yNSw2ODcuMzI0MSwzNTAuMjUsNjc3LjMyNDEsMzQ2LjI1LDY4MS4zMjQxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MDguMjUnIHgyPSc1MTQuNzUnIHkxPSc2NDkuODMzMScgeTI9JzY0OS44MzMxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSc1MTAuNzUsNzIwLjk5NjEsNTE0Ljc1LDczMC45OTYxLDUxOC43NSw3MjAuOTk2MSw1MTQuNzUsNzI0Ljk5NjEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzUxNC43NScgeDI9JzUxNC43NScgeTE9JzY0OS44MzMxJyB5Mj0nNzk0Ljk5NjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1MTQuNzUnIHgyPSczNDYuMjUnIHkxPSc3OTQuOTk2MScgeTI9Jzc5NC45OTYxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nNzk0Ljk5NjEnIHkyPSc4MTQuOTk2MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzQyLjI1LDgwNC45OTYxLDM0Ni4yNSw4MTQuOTk2MSwzNTAuMjUsODA0Ljk5NjEsMzQ2LjI1LDgwOC45OTYxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMTgnIHgyPScxMTgnIHkxPSc5MzQuODMxMicgeTI9Jzk2Mi4xNTkxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScxMTQsOTUyLjE1OTEsMTE4LDk2Mi4xNTkxLDEyMiw5NTIuMTU5MSwxMTgsOTU2LjE1OTEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzExOCcgeDI9JzExOCcgeTE9Jzg3Mi45OTYxJyB5Mj0nODk4LjQ4NzEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzExNCw4ODguNDg3MSwxMTgsODk4LjQ4NzEsMTIyLDg4OC40ODcxLDExOCw4OTIuNDg3MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMTc2JyB4Mj0nMjE0LjUnIHkxPSc4NjAuOTk2MScgeTI9Jzg2MC45OTYxJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPScyMTAuNSw5MzIuMTU5MSwyMTQuNSw5NDIuMTU5MSwyMTguNSw5MzIuMTU5MSwyMTQuNSw5MzYuMTU5MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjE0LjUnIHgyPScyMTQuNScgeTE9Jzg2MC45OTYxJyB5Mj0nMTAwNi4xNTkxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjE0LjUnIHgyPScxMTgnIHkxPScxMDA2LjE1OTEnIHkyPScxMDA2LjE1OTEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMTgnIHgyPScxMTgnIHkxPScxMDA2LjE1OTEnIHkyPScxMDI2LjE1OTEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzExNCwxMDE2LjE1OTEsMTE4LDEwMjYuMTU5MSwxMjIsMTAxNi4xNTkxLDExOCwxMDIwLjE1OTEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzExOCcgeDI9JzExOCcgeTE9JzEwNjIuNTAzMicgeTI9JzEwODIuNTAzMicvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMTE0LDEwNzIuNTAzMiwxMTgsMTA4Mi41MDMyLDEyMiwxMDcyLjUwMzIsMTE4LDEwNzYuNTAzMicgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTc0LjUnIHgyPSc1NzQuNScgeTE9JzkzNC44MzEyJyB5Mj0nOTYyLjE1OTEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU3MC41LDk1Mi4xNTkxLDU3NC41LDk2Mi4xNTkxLDU3OC41LDk1Mi4xNTkxLDU3NC41LDk1Ni4xNTkxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1NzQuNScgeDI9JzU3NC41JyB5MT0nODcyLjk5NjEnIHkyPSc4OTguNDg3MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNTcwLjUsODg4LjQ4NzEsNTc0LjUsODk4LjQ4NzEsNTc4LjUsODg4LjQ4NzEsNTc0LjUsODkyLjQ4NzEnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzY0MC41JyB4Mj0nNjk5JyB5MT0nODYwLjk5NjEnIHkyPSc4NjAuOTk2MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNjk1LDkzMi4xNTkxLDY5OSw5NDIuMTU5MSw3MDMsOTMyLjE1OTEsNjk5LDkzNi4xNTkxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2OTknIHgyPSc2OTknIHkxPSc4NjAuOTk2MScgeTI9JzEwMDYuMTU5MScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzY5OScgeDI9JzU3NC41JyB5MT0nMTAwNi4xNTkxJyB5Mj0nMTAwNi4xNTkxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTc0LjUnIHgyPSc1NzQuNScgeTE9JzEwMDYuMTU5MScgeTI9JzEwMjYuMTU5MScvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nNTcwLjUsMTAxNi4xNTkxLDU3NC41LDEwMjYuMTU5MSw1NzguNSwxMDE2LjE1OTEsNTc0LjUsMTAyMC4xNTkxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1NzQuNScgeDI9JzU3NC41JyB5MT0nMTA2Mi41MDMyJyB5Mj0nMTA4Mi41MDMyJy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSc1NzAuNSwxMDcyLjUwMzIsNTc0LjUsMTA4Mi41MDMyLDU3OC41LDEwNzIuNTAzMiw1NzQuNSwxMDc2LjUwMzInIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU3NC41JyB4Mj0nNTc0LjUnIHkxPScxMTE4Ljg0NzMnIHkyPScxMTM4Ljg0NzMnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU3MC41LDExMjguODQ3Myw1NzQuNSwxMTM4Ljg0NzMsNTc4LjUsMTEyOC44NDczLDU3NC41LDExMzIuODQ3Mycgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjkwLjI1JyB4Mj0nMTE4JyB5MT0nODI2Ljk5NjEnIHkyPSc4MjYuOTk2MScvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzExOCcgeDI9JzExOCcgeTE9JzgyNi45OTYxJyB5Mj0nODQ4Ljk5NjEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzExNCw4MzguOTk2MSwxMTgsODQ4Ljk5NjEsMTIyLDgzOC45OTYxLDExOCw4NDIuOTk2MScgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAyLjI1JyB4Mj0nNTc0LjUnIHkxPSc4MjYuOTk2MScgeTI9JzgyNi45OTYxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTc0LjUnIHgyPSc1NzQuNScgeTE9JzgyNi45OTYxJyB5Mj0nODQ4Ljk5NjEnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzU3MC41LDgzOC45OTYxLDU3NC41LDg0OC45OTYxLDU3OC41LDgzOC45OTYxLDU3NC41LDg0Mi45OTYxJyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMTgnIHgyPScxMTgnIHkxPScxMTE4Ljg0NzMnIHkyPScxMTk3LjcyNTQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMTgnIHgyPSczMzQuMjUnIHkxPScxMTk3LjcyNTQnIHkyPScxMTk3LjcyNTQnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzMyNC4yNSwxMTkzLjcyNTQsMzM0LjI1LDExOTcuNzI1NCwzMjQuMjUsMTIwMS43MjU0LDMyOC4yNSwxMTk3LjcyNTQnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjxsaW5lIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzU3NC41JyB4Mj0nNTc0LjUnIHkxPScxMTc1LjE5MTUnIHkyPScxMTk3LjcyNTQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1NzQuNScgeDI9JzM1OC4yNScgeTE9JzExOTcuNzI1NCcgeTI9JzExOTcuNzI1NCcvPjxwb2x5Z29uIGZpbGw9JyMxODE4MTgnIHBvaW50cz0nMzY4LjI1LDExOTMuNzI1NCwzNTguMjUsMTE5Ny43MjU0LDM2OC4yNSwxMjAxLjcyNTQsMzY0LjI1LDExOTcuNzI1NCcgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzQ2LjI1JyB4Mj0nMzQ2LjI1JyB5MT0nMTIwOS43MjU0JyB5Mj0nMTIyOS43MjU0Jy8+PHBvbHlnb24gZmlsbD0nIzE4MTgxOCcgcG9pbnRzPSczNDIuMjUsMTIxOS43MjU0LDM0Ni4yNSwxMjI5LjcyNTQsMzUwLjI1LDEyMTkuNzI1NCwzNDYuMjUsMTIyMy43MjU0JyBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczNDYuMjUnIHgyPSczNDYuMjUnIHkxPScxMjY2LjA2OTUnIHkyPScxMjg2LjA2OTUnLz48cG9seWdvbiBmaWxsPScjMTgxODE4JyBwb2ludHM9JzM0Mi4yNSwxMjc2LjA2OTUsMzQ2LjI1LDEyODYuMDY5NSwzNTAuMjUsMTI3Ni4wNjk1LDM0Ni4yNSwxMjgwLjA2OTUnIHN0eWxlPSdzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MS4wOycvPjwvZz48L3N2Zz4=)

Figure 17. Disable / Enable validation gate

### Working Capital Loan â Accrual with Deferred Revenue Amortization Accounting

#### Overview

Working Capital Loan products support accrual with deferred revenue amortization accounting, where journal entries are posted only when cash actually moves. The accounting rule is selected at the product level via `accountingRule = ACC_DEF_REV_AM`. Each monetary transaction on a Working Capital Loan (repayment, goodwill credit, reversals) drives a balanced set of journal entries against GL accounts mapped on the loan product.

##### Purpose

Accrual with deferred revenue amortization accounting allows lenders to record the financial impact of Working Capital Loan transactions in the general ledger at the moment cash is received or disbursed, without recognizing accrued income or receivables in advance. This is the simpler of the two accounting bases and is appropriate when income recognition should track cash flow rather than economic activity.

##### Scope

The scope of this document includes:

* Working Capital Loan product accounting rule configuration
* GL account mappings required for accrual with deferred revenue amortization accounting
* Journal entries posted on repayment (regular and charged-off)
* Journal entries posted on goodwill credit
* Reversal journal entries
* Fund source mapping by payment type
* Read-side mapping retrieval

EIR-specific discount fee amortization journal entries are documented separately in `working-capital-eir-calculation-accounting.adoc`.

##### Applicability

* Working Capital Loan products with `accountingRule = ACC_DEF_REV_AM`
* Working Capital Loans linked to such products

##### Definitions and Key Concepts

**Accounting Rule:** Product-level configuration that selects the accounting basis. For Working Capital Loans the supported values are `NONE` (no journal entries posted) and `ACC_DEF_REV_AM`.

**GL Account Mapping:** Persisted link between a Working Capital Loan product, an accounting placeholder (e.g., `LOAN_PORTFOLIO`), and a concrete `GLAccount` row.

**Fund Source:** The bank or cash GL account used as the contra side for cash movements. May be overridden per payment type.

**Charged-Off Loan:** A loan marked as `isChargedOff = true`. After charge-off, repayments post to `INCOME_FROM_RECOVERY` instead of the regular portfolio/fees/penalties accounts.

#### Design Decisions and Considerations

##### Dedicated Working Capital Accounting Processor

Working Capital Loans use a dedicated `WorkingCapitalLoanAccountingProcessor` interface with a single `AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan` implementation. This keeps Working Capital posting logic independent from the standard Loan accounting processors, which avoids coupling the Working Capital allocation model (`WorkingCapitalLoanTransactionAllocation`) to the standard loan data structures.

##### Accrual Basis Not Supported

The `WorkingCapitalAccountingRuleType` enum only exposes `NONE` and `ACC_DEF_REV_AM`. Accrual-based accounting is not implemented for Working Capital Loan products.

#### Database Design

##### Existing Tables

**m_product_loan_gl_account_mapping**: Stores the mapping between a Working Capital Loan product, a cash account placeholder (`CashAccountsForLoan` value), an optional payment type / charge / code value, and the target `GLAccount`. Working Capital mappings are identified by `product_type = PortfolioProductType.WORKING_CAPITAL_LOAN.value` (4).

**acc_gl_journal_entry**: Standard journal entry table. Accrual with deferred revenue amortization Working Capital postings are written here with a transaction id prefixed by `WC` (see `AccountingProcessorHelper.WORKING_CAPITAL_LOAN_TRANSACTION_IDENTIFIER`) and `entity_type = WORKING_CAPITAL_LOAN`.

##### Changes to Existing Tables

###### m_wc_loan_product

The product-level accounting rule is persisted in:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| accounting_type | VARCHAR(20) | not null, default `NONE` | Selected `WorkingCapitalAccountingRuleType` (`NONE` or `ACC_DEF_REV_AM`) |

#### Configuration

##### Loan Product Configuration

The accounting rule and GL account mappings are supplied when creating or updating a Working Capital Loan product:

```json
{
  "accountingRule": "ACC_DEF_REV_AM",
  "fundSourceAccountId": 1,
  "loanPortfolioAccountId": 2,
  "transfersInSuspenseAccountId": 3,
  "receivableFeeAccountId": 19,
  "receivablePenaltyAccountId": 20,
  "incomeFromFeeAccountId": 6,
  "incomeFromPenaltyAccountId": 6,
  "incomeFromRecoveryAccountId": 7,
  "writeOffAccountId": 8,
  "overpaymentLiabilityAccountId": 9,
  "goodwillCreditAccountId": 16,
  "incomeFromGoodwillCreditFeesAccountId": 12,
  "incomeFromGoodwillCreditPenaltyAccountId": 13,
  "chargeOffExpenseAccountId": 17,
  "chargeOffFraudExpenseAccountId": 18,
  "incomeFromChargeOffFeesAccountId": 10,
  "incomeFromChargeOffPenaltyAccountId": 11,
  "paymentChannelToFundSourceMappings": [
    { "paymentTypeId": 1, "fundSourceAccountId": 100 }
  ],
  "feeToIncomeAccountMappings": [
    { "chargeId": 1, "incomeAccountId": 6 }
  ],
  "penaltyToIncomeAccountMappings": [
    { "chargeId": 2, "incomeAccountId": 6 }
  ],
  "chargeOffReasonToExpenseAccountMappings": [
    { "chargeOffReasonCodeValueId": 1, "expenseAccountId": 17 }
  ],
  "writeOffReasonsToExpenseMappings": [
    { "writeOffReasonCodeValueId": 1, "expenseAccountId": 8 }
  ]
}
```

##### GL Account Mappings

When `accountingRule = ACC_DEF_REV_AM`, the platform persists one `ProductToGLAccountMapping` row per supplied mapping. The placeholder enum is `CashAccountsForLoan`:

* **Fund Source (Asset)**: `fundSourceAccountId` â cash account that is debited on repayment and may be overridden per payment type via `paymentChannelToFundSourceMappings`
* **Loan Portfolio (Asset)**: `loanPortfolioAccountId` â credited for the principal portion of regular repayments
* **Fees Receivable (Asset)**: `receivableFeeAccountId` â credited for the fees portion of regular repayments
* **Penalties Receivable (Asset)**: `receivablePenaltyAccountId` â credited for the penalty portion of regular repayments
* **Overpayment Liability (Liability)**: `overpaymentLiabilityAccountId` â credited for any amount in excess of principal + fees + penalties
* **Income from Recovery (Income)**: `incomeFromRecoveryAccountId` â credited for all repayment portions when the loan is charged off
* **Goodwill Credit (Expense)**: `goodwillCreditAccountId` â debited for principal + overpayment portion of a goodwill credit
* **Income from Goodwill Credit Fees (Income)**: `incomeFromGoodwillCreditFeesAccountId` â debited for fees portion of a goodwill credit
* **Income from Goodwill Credit Penalty (Income)**: `incomeFromGoodwillCreditPenaltyAccountId` â debited for penalty portion of a goodwill credit
* **Charge-off Expense (Expense)** / **Charge-off Fraud Expense (Expense)**: optional, used by charge-off reason mappings

Additional advanced mappings:

* **Payment Channel to Fund Source**: per-payment-type override of the default fund source account
* **Fee/Penalty to Income**: per-charge income account override
* **Charge-off Reason to Expense**: per-reason expense account override
* **Write-off Reason to Expense**: per-reason expense account override

> [!IMPORTANT]
> GL account mappings are validated at product create/update time. Duplicated entries in `paymentChannelToFundSourceMappings`, `feeToIncomeAccountMappings`, `penaltyToIncomeAccountMappings`, `chargeOffReasonToExpenseAccountMappings`, or `writeOffReasonsToExpenseMappings` are rejected with `duplicated.enrty.for.<mapping>`.

#### API Design

##### Endpoints

###### Configure Accounting on a Working Capital Loan Product

Accounting fields are part of the standard Working Capital Loan product endpoints:

```java
POST /v1/working-capital-loan-products
PUT  /v1/working-capital-loan-products/{productId}
PUT  /v1/working-capital-loan-products/external-id/{externalProductId}
GET  /v1/working-capital-loan-products/{productId}
GET  /v1/working-capital-loan-products/external-id/{externalProductId}
GET  /v1/working-capital-loan-products/template
```

The `GET` responses expose:

* `accountingRule` â current rule as a `StringEnumOptionData`
* `accountingMappings` â map of placeholder name to `GLAccountData` (only populated when the rule is `ACC_DEF_REV_AM`)
* `accountingMappingOptions` (template) â lookup data for the UI: fund source, payment channels, fee/penalty income, charge-off / write-off reason mappings

#### Validation Rules

##### General Rules

* `accountingRule` must be a valid `WorkingCapitalAccountingRuleType` name (`NONE` or `ACC_DEF_REV_AM`).
* When `accountingRule = NONE`, no GL account mappings are persisted; if previously `ACC_DEF_REV_AM`, the prior mappings are deleted.

##### Validation Rules for Mappings

* Each advanced mapping array (`paymentChannelToFundSourceMappings`, `feeToIncomeAccountMappings`, `penaltyToIncomeAccountMappings`, `chargeOffReasonToExpenseAccountMappings`, `writeOffReasonsToExpenseMappings`) must not contain duplicates on its key field.

#### Business Rules

##### Branch Closure Check

Before posting any journal entries for a transaction date, the processor calls `helper.checkForBranchClosures(…​)`. If the transaction date falls on or before the latest accounting closure for the loan’s branch, posting is rejected.

##### Repayment â Regular

When a repayment is posted on a non-charged-off Working Capital Loan, the processor reads principal, fees, and penalties portions from the `WorkingCapitalLoanTransactionAllocation`, computes the overpayment portion as the residual of the transaction amount, and posts:

* a credit per non-zero portion (principal â `LOAN_PORTFOLIO`, fees â `FEES_RECEIVABLE`, penalties â `PENALTIES_RECEIVABLE`, overpayment â `OVERPAYMENT`)
* a single debit to the fund source for the full transaction amount, resolved against `paymentChannelToFundSourceMappings` using `paymentDetail.paymentType.id` when present

##### Repayment â Charged Off

When the loan is already charged off, all three credit legs are redirected to `INCOME_FROM_RECOVERY` instead of the regular portfolio/receivable accounts. The fund source debit is unchanged.

##### Goodwill Credit

For a goodwill credit on a non-charged-off loan, the processor posts:

* debit `GOODWILL_CREDIT` for principal + overpayment portion
* debit `INCOME_FROM_GOODWILL_CREDIT_FEES` for fees portion
* debit `INCOME_FROM_GOODWILL_CREDIT_PENALTY` for penalty portion
* credit `LOAN_PORTFOLIO`, `FEES_RECEIVABLE`, `PENALTIES_RECEIVABLE`, `OVERPAYMENT` for the matching portions

Posting a goodwill credit while the loan is charged off raises `NotImplementedException("Charge off is not implemented yet for Goodwill Credit for Working Capital Loan")`.

##### Unsupported Transaction Types

If `postJournalEntries` is invoked with a transaction type other than `REPAYMENT` or `GOODWILL_CREDIT`, it raises `NotImplementedException("Post Journal Entries is not implemented yet for <code> for Working Capital Loan")`. Discount fee amortization and its adjustment are handled by dedicated processor methods (see `working-capital-eir-calculation-accounting.adoc`).

##### Reversal

`postReversalJournalEntries` reads existing journal entries for the transaction identifier `WC<txnId>` and `entityType = WORKING_CAPITAL_LOAN`, then for each one creates a mirror entry with the opposite `JournalEntryType`. The original entries are marked `reversed = true` and linked to their reversal entry. The reversal posting date is `txn.reversedOnDate` when present, otherwise the current business date.

##### Zero-Amount Skipping

Each journal leg checks `MathUtil.isGreaterThanZero(amount)` before creating the entry. Zero or null portions produce no journal entry.

#### Accounting Entries

##### Repayment â Regular

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Repayment (principal) | Fund Source (Asset) | Loan Portfolio (Asset) |
| Repayment (fees) | Fund Source (Asset) | Fees Receivable (Asset) |
| Repayment (penalties) | Fund Source (Asset) | Penalties Receivable (Asset) |
| Repayment (overpayment) | Fund Source (Asset) | Overpayment Liability (Liability) |

##### Repayment â Charged Off

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Repayment (principal) | Fund Source (Asset) | Income from Recovery (Income) |
| Repayment (fees) | Fund Source (Asset) | Income from Recovery (Income) |
| Repayment (penalties) | Fund Source (Asset) | Income from Recovery (Income) |
| Repayment (overpayment) | Fund Source (Asset) | Overpayment Liability (Liability) |

##### Goodwill Credit (not charged off)

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| Goodwill Credit (principal + overpayment) | Goodwill Credit (Expense) | Loan Portfolio (Asset) |
| Goodwill Credit (fees) | Income from Goodwill Credit Fees (Income) | Fees Receivable (Asset) |
| Goodwill Credit (penalty) | Income from Goodwill Credit Penalty (Income) | Penalties Receivable (Asset) |
| Goodwill Credit (overpayment) |  | Overpayment Liability (Liability) |

##### Reversal

Every journal entry written for a Working Capital Loan transaction can be reversed. The reversal posts a balanced mirror entry per leg, swapping debit and credit, and marks the original entries `reversed = true`.

#### Example Scenarios

##### Scenario #1: Regular repayment with fees and overpayment

**Setup:**

* Working Capital Loan product with `accountingRule = ACC_DEF_REV_AM`
* Mappings configured for Fund Source, Loan Portfolio, Fees Receivable, Overpayment
* Active loan with outstanding principal 800 and fees 50

**Action:**

A repayment of 1,000 is posted. The allocator records principal = 800, fees = 50, penalties = 0, leaving an overpayment of 150.

**Expected Behavior:**

* Debit Fund Source 1,000
* Credit Loan Portfolio 800
* Credit Fees Receivable 50
* Credit Overpayment Liability 150
* All entries share transaction id `WC<txnId>` and `entityType = WORKING_CAPITAL_LOAN`

##### Scenario #2: Repayment after charge-off

**Setup:**

* Same product, but the loan was previously charged off (`isChargedOff = true`)
* Mappings include `Income from Recovery`

**Action:**

A repayment of 500 is posted with allocation principal = 300, fees = 100, penalties = 100.

**Expected Behavior:**

* Debit Fund Source 500
* Credit Income from Recovery 300 (principal)
* Credit Income from Recovery 100 (fees)
* Credit Income from Recovery 100 (penalties)
* No entries to Loan Portfolio / Fees Receivable / Penalties Receivable

#### Summary

Working Capital Loan accrual with deferred revenue amortization accounting provides cash-aligned journal entries for repayments and goodwill credits via a dedicated `AccrualWithDeferredRevenueAmortizationAccountingProcessorForWorkingCapitalLoan`. Key aspects include:

* Product-level `accountingRule` selecting `NONE` or `ACC_DEF_REV_AM`
* `CashAccountsForLoan`-based GL account mappings, with advanced overrides per payment type, charge, and reason code
* Distinct posting flows for regular vs. charged-off repayments
* Dedicated goodwill credit posting with charge-off explicitly unsupported
* Symmetric reversal that mirrors every leg of the original transaction

### Working Capital Loan â EIR Calculation Accounting

#### Overview

Working Capital Loans amortize discount fee income across the loan term using an Effective Interest Rate (EIR) schedule. When the COB business step `WC_DISCOUNT_FEE_AMORTIZATION` advances the realized income figure, the accounting processor posts a balanced pair of journal entries that move the newly recognized amount out of the **Deferred Income Liability** placeholder and into income (or, when the loan is charged off, into the charge-off expense placeholder).

The EIR calculation itself â solver, schedule shape, rate changes â is documented in `working-capital-eir-calculation.adoc`. This document focuses on the journal entries derived from the schedule.

##### Purpose

EIR-based income recognition spreads the discount fee over the life of the Working Capital Loan in proportion to its present value at each period, rather than recognizing it at disbursement. The corresponding journal entries keep the general ledger in step with the periodic income figure produced by the amortization schedule.

##### Scope

The scope of this document includes:

* The COB business step that drives EIR income recognition
* Calculation of the periodic amortization amount from the schedule
* Journal entries for `DISCOUNT_FEE_AMORTIZATION`
* Journal entries for `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT`
* Charge-off behavior for amortization entries
* Reversal handling

General Working Capital Loan repayment and goodwill credit accounting are documented in `working-capital-accrual-deferred-revenue-amortization-accounting.adoc`.

##### Applicability

* Working Capital Loan products with `accountingRule = ACC_DEF_REV_AM`
* Working Capital Loans with `amortizationType = EIR` and a non-zero discount fee, OR with previously recognized discount fee income that needs to be reconciled downward

##### Definitions and Key Concepts

**Discount Fee:** The upfront fee charged on a Working Capital Loan, persisted on `loanProductRelatedDetails.discount`.

**Deferred Income Liability:** The unrecognized portion of the discount fee, sitting as a liability on the lender’s balance sheet until it is amortized into income.

**Realized Income from Discount Fee:** The cumulative amount of discount fee that has already been recognized as income for the loan. Persisted on the loan balance as `realizedIncomeFromDiscountFee`.

**Schedule Amortization:** The income figure produced by the EIR amortization schedule up to the current business date, accessed via `ProjectedAmortizationScheduleModel.totalActualAmortization()`.

**Amortization Transaction:** A monetary Working Capital Loan transaction (`DISCOUNT_FEE_AMORTIZATION` or `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT`) that carries the journal-entry amount.

#### Design Decisions and Considerations

##### Separate Adjustment Path for Downward Reconciliation

Two transaction types and two processor methods are used: `postJournalEntriesForDiscountFeeAmortization` for the normal increase in realized income and `postJournalEntriesForDiscountFeeAmortizationAdjustment` for downward reconciliation (for example after a discount fee adjustment reduces the discount). The adjustment path swaps debit and credit so the previously recognized income is reversed against the deferred liability rather than recorded as a negative amortization. This avoids posting a debit balance against an income account.

##### Charged-Off Loans Redirect to Charge-Off Expense

When the loan is charged off, the income leg of both amortization and adjustment is redirected from `INCOME_FROM_DISCOUNT_FEE` to `CHARGE_OFF_EXPENSE`. This keeps post-charge-off discount fee movement out of the income statement and aligns it with the charge-off expense recognized at the time of charge-off.

#### Database Design

##### Existing Tables

**m_wc_loan_balance**: Holds the cumulative realized income for the loan via `realized_income_from_discount_fee`. This value is consulted on every business step run to decide how much new amortization to post and is updated after the journal entries are written.

**m_wc_loan_amortization_model**: Serialized `ProjectedAmortizationScheduleModel` (JSON CLOB) keyed by loan id. The processor reads this to compute the schedule’s `totalActualAmortization` for the current business date.

**m_wc_loan_transaction**: Stores the `DISCOUNT_FEE_AMORTIZATION` (45) and `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` (47) transactions that carry the journal entry amount.

**acc_gl_journal_entry**: Receives the balanced debit/credit pair for each amortization or adjustment, with transaction id `WC<txnId>` and `entityType = WORKING_CAPITAL_LOAN`.

##### Changes to Existing Tables

###### m_batch_business_steps

The COB step that drives EIR income recognition is registered as:

| Column Name | Type | Constraints | Description |
| --- | --- | --- | --- |
| job_name | VARCHAR | not null | `WORKING_CAPITAL_LOAN_CLOSE_OF_BUSINESS` |
| step_name | VARCHAR | not null | `WC_DISCOUNT_FEE_AMORTIZATION` |
| step_order | INT | not null | `7` |

#### Configuration

##### Loan Product Configuration

EIR amortization accounting is gated on:

```json
{
  "amortizationType": "EIR",
  "accountingRule": "CASH_BASED",
  "deferredIncomeLiabilityAccountId": 4,
  "incomeFromDiscountFeeAccountId": 5,
  "chargeOffExpenseAccountId": 17
}
```

##### GL Account Mappings

Required GL account mappings for EIR calculation accounting:

* **Deferred Income Liability (Liability)**: `deferredIncomeLiabilityAccountId` â the liability that holds unrecognized discount fee income; debited as income is amortized and credited when amortization is reduced
* **Income from Discount Fee (Income)**: `incomeFromDiscountFeeAccountId` â credited as discount fee is recognized into income (or debited on adjustment) when the loan is not charged off
* **Charge-off Expense (Expense)**: `chargeOffExpenseAccountId` â used in place of `Income from Discount Fee` when the loan is charged off

> [!IMPORTANT]
> The Deferred Income Liability mapping is required whenever `amortizationType = EIR` is used together with `accountingRule = CASH_BASED`. Without it the processor cannot resolve the debit leg for amortization entries.

#### API Design

EIR amortization journal entries are not exposed through dedicated REST endpoints. They are produced internally by the COB business step. The resulting transactions are visible through the standard Working Capital Loan transaction endpoints:

```java
GET /v1/working-capital-loans/{loanId}/transactions/{transactionId}
GET /v1/working-capital-loans/external-id/{loanExternalId}/transactions/external-id/{externalTransactionId}
```

#### Business Rules

##### Discount Fee Amortization Business Step

The `DiscountFeeAmortizationBusinessStep` (COB step `WC_DISCOUNT_FEE_AMORTIZATION`, order 7) runs at end of day. It skips the loan when both of the following are true:

* `loanProductRelatedDetails.discount` is zero or null, AND
* `loanBalance.realizedIncomeFromDiscountFee` is zero or null

Otherwise the step delegates to `WorkingCapitalLoanDiscountFeeAmortizationServiceImpl.processDiscountFeeAmortization(loan, businessDate)`.

##### Amortization Amount Calculation

The service reads `scheduleAmortization` from the amortization model (`totalActualAmortization`) and `alreadyPosted` from `loanBalance.realizedIncomeFromDiscountFee`. The amount to post is:

* If the loan is overpaid and `discount > 0`: `amortizationAmount = discount â alreadyPosted` (catch realization up to the full discount on overpayment)
* Otherwise: `amortizationAmount = scheduleAmortization â alreadyPosted`

If the amortization amount is zero (or both schedule and already-posted are zero on a non-overpaid loan), the step exits without posting.

##### Posting Direction

* `amortizationAmount > 0` â create a `DISCOUNT_FEE_AMORTIZATION` transaction for that amount and call `postJournalEntriesForDiscountFeeAmortization`.
* `amortizationAmount < 0` â create a `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` transaction for the absolute value, link it via `m_wc_loan_transaction_relation` (`RELATED`) to the most recent `DISCOUNT_FEE_ADJUSTMENT` transaction, and call `postJournalEntriesForDiscountFeeAmortizationAdjustment`.

After posting, `loanBalance.realizedIncomeFromDiscountFee` is set to `alreadyPosted + amortizationAmount`.

##### Branch Closure Check

Both `postJournalEntriesForDiscountFeeAmortization` and `postJournalEntriesForDiscountFeeAmortizationAdjustment` call `helper.checkForBranchClosures(…​)`. If the transaction date falls on or before the latest accounting closure for the loan’s branch, posting is rejected.

##### Zero-Amount Skip

Both processor methods short-circuit when `MathUtil.isGreaterThanZero(amount)` is false, so a zero-amount transaction never produces journal entries.

##### Charge-Off Behavior

When the loan is charged off (`isChargedOff = true`), the income placeholder is replaced by `CHARGE_OFF_EXPENSE` on both the amortization and the adjustment posting. The Deferred Income Liability leg is unchanged.

##### Reversal

EIR amortization transactions reverse through the same generic mechanism as other Working Capital Loan transactions: `postReversalJournalEntries` reads the existing entries for transaction id `WC<txnId>` and writes a mirror entry per leg, then flags the originals as reversed.

#### Accounting Entries

##### Discount Fee Amortization â Not Charged Off

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| `DISCOUNT_FEE_AMORTIZATION` | Deferred Income Liability (Liability) | Income from Discount Fee (Income) |

##### Discount Fee Amortization â Charged Off

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| `DISCOUNT_FEE_AMORTIZATION` | Deferred Income Liability (Liability) | Charge-off Expense (Expense) |

##### Discount Fee Amortization Adjustment â Not Charged Off

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` | Income from Discount Fee (Income) | Deferred Income Liability (Liability) |

##### Discount Fee Amortization Adjustment â Charged Off

| Transaction Type | Debit | Credit |
| --- | --- | --- |
| `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` | Charge-off Expense (Expense) | Deferred Income Liability (Liability) |

##### Reversal

Every leg can be reversed; the reversal posts a balanced mirror entry per leg and flags the originals as reversed (see `working-capital-accrual-deferred-revenue-amortization-accounting.adoc`).

#### Example Scenarios

##### Scenario #1: Daily amortization on a non-charged-off loan

**Setup:**

* Working Capital Loan product with `amortizationType = EIR` and `accountingRule = CASH_BASED`
* Mappings configured for Deferred Income Liability and Income from Discount Fee
* Discount fee = 1,000, schedule has advanced to `totalActualAmortization = 120`
* `loanBalance.realizedIncomeFromDiscountFee = 100`

**Action:**

The `WC_DISCOUNT_FEE_AMORTIZATION` business step runs at end of day.

**Expected Behavior:**

* New amortization amount = 120 â 100 = 20
* A `DISCOUNT_FEE_AMORTIZATION` transaction of 20 is created
* Debit Deferred Income Liability 20, Credit Income from Discount Fee 20
* `realizedIncomeFromDiscountFee` becomes 120

##### Scenario #2: Downward reconciliation after a discount adjustment

**Setup:**

* Same product, `realizedIncomeFromDiscountFee = 200`
* A `DISCOUNT_FEE_ADJUSTMENT` has reduced the discount and the schedule now reports `totalActualAmortization = 150`

**Action:**

The business step runs.

**Expected Behavior:**

* Amortization amount = 150 â 200 = â50, so a `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` of 50 is created
* The adjustment transaction is linked (`RELATED`) to the most recent `DISCOUNT_FEE_ADJUSTMENT`
* Debit Income from Discount Fee 50, Credit Deferred Income Liability 50
* `realizedIncomeFromDiscountFee` becomes 150

##### Scenario #3: Overpaid loan catches up to the full discount

**Setup:**

* Same product, loan status is `OVERPAID`
* Discount fee = 1,000, `realizedIncomeFromDiscountFee = 800`, schedule reports `totalActualAmortization = 950`

**Action:**

The business step runs.

**Expected Behavior:**

* Because the loan is overpaid and `discount > 0`, the amount uses the discount as the target: 1,000 â 800 = 200
* A `DISCOUNT_FEE_AMORTIZATION` of 200 is created
* Debit Deferred Income Liability 200, Credit Income from Discount Fee 200
* `realizedIncomeFromDiscountFee` becomes 1,000

##### Scenario #4: Amortization on a charged-off loan

**Setup:**

* Same product, but the loan was charged off after disbursement
* Mappings include Charge-off Expense

**Action:**

The business step posts a 30-unit amortization for the day.

**Expected Behavior:**

* A `DISCOUNT_FEE_AMORTIZATION` of 30 is created
* Debit Deferred Income Liability 30, Credit Charge-off Expense 30 (the income placeholder is replaced)
* `realizedIncomeFromDiscountFee` advances by 30

#### Summary

EIR calculation accounting recognizes Working Capital Loan discount fee income over time, in proportion to the EIR amortization schedule. Key aspects include:

* COB step `WC_DISCOUNT_FEE_AMORTIZATION` drives nightly recognition based on the difference between schedule amortization and already-posted income
* `DISCOUNT_FEE_AMORTIZATION` (upward) and `DISCOUNT_FEE_AMORTIZATION_ADJUSTMENT` (downward) transactions carry the journal entry amounts
* Journal entries move value between Deferred Income Liability and Income from Discount Fee, with charged-off loans redirecting the income leg to Charge-off Expense
* The loan balance field `realizedIncomeFromDiscountFee` is the source of truth for what has already been recognized and is updated atomically with the journal entries

### Working Capital Loan Start Dates (Breach and Delinquency)

#### Overview

The Working Capital (WC) Loan retrieve response exposes four read-only derived fields, `breachStartDate`, `breachEffectiveStartDate`, `delinquencyStartDate` and `delinquencyEffectiveStartDate`, that tell a consumer **when** a loan first entered breach and when it first became delinquent. All four values are computed on-the-fly from the loan’s breach schedule and delinquency-range schedule when a single WC loan is fetched. They are `null` while the loan is healthy and become populated once the corresponding schedule period is flagged by the WC Close-of-Business (COB) job.

The feature is implemented in the `fineract-working-capital-loan` module and is exposed on the WC Loan retrieve REST API as `breachStartDate`, `breachEffectiveStartDate`, `delinquencyStartDate` and `delinquencyEffectiveStartDate`.

##### Purpose

Lenders and collection officers need a single, stable anchor date for each loan that answers "since when has this loan been in trouble?" â for ageing reports, dunning timelines, and SLA tracking. Rather than forcing API consumers to scan the full breach/delinquency schedule and re-apply grace-day arithmetic themselves, the platform derives the earliest affected period and returns its start date directly.

The first breach period and the first delinquency period can additionally be shifted by their grace days (`breachGraceDays` and `delinquencyGraceDays`), which act as a "cool off" period for the borrower. `breachEffectiveStartDate` and `delinquencyEffectiveStartDate` make that shift explicit so it can be shared with the customer without the consumer having to know how the schedules are generated.

##### Scope

The scope of this document includes:

* Read-only fields `breachStartDate`, `breachEffectiveStartDate`, `delinquencyStartDate` and `delinquencyEffectiveStartDate` on the WC Loan retrieve response.
* Derivation logic in `WorkingCapitalLoanApplicationReadPlatformServiceImpl.enrichWithStartDates`.
* Two repository finder methods that locate the earliest breached / delinquent period.
* The grace-day handling shared by the breach schedule and the delinquency-range schedule.

The scope explicitly excludes:

* No new database tables or columns â all values are derived at read time from existing schedules.
* No dedicated business events are emitted for these fields. They do travel inside every WC loan business event payload, because `WorkingCapitalLoanBusinessEventSerializer` builds that payload from `retrieveOne`.
* The fields are populated only by the single-loan retrieve path (`retrieveOne`); they are not enriched in the paginated list response.

##### Applicability

* Applies to Working Capital loans returned by `GET /v1/working-capital-loans/{loanId}` and `GET /v1/working-capital-loans/external-id/{loanExternalId}`.
* `breachStartDate` and `breachEffectiveStartDate` are meaningful only when the product/loan has a breach configuration (`breach_id` not null) so that a breach schedule exists.
* `delinquencyStartDate` and `delinquencyEffectiveStartDate` are meaningful only when the loan has a delinquency bucket assigned so that a delinquency-range schedule exists.
* `breachEffectiveStartDate` and `delinquencyEffectiveStartDate` are additionally restricted to the first period of their schedule, which is the only one the grace days shift.
* Values reflect the state at the time of the last WC COB run; a loan whose periods have not yet been evaluated will report `null`.

##### Definitions and Key Concepts

**`breachStartDate`:** The `fromDate` of the earliest breached breach-schedule period (`m_wc_loan_breach_schedule` row with `breach = true`, ordered by `from_date` ascending). The breach schedule applies `breachGraceDays` to the `toDate` of its first period, so no adjustment is applied to the `fromDate`. `null` when no period is in breach.

**`breachEffectiveStartDate`:** `breachStartDate` shifted forward by `breachGraceDays` â the date the breach clock effectively starts ticking once the cool off period is taken into account. It is set **only** when the earliest breached period is the first one (`period_number = 1`) and `breachGraceDays > 0`; `null` otherwise.

**`delinquencyStartDate`:** The `fromDate` of the earliest delinquent range-schedule period (`m_wc_loan_delinquency_range_schedule` row with `min_payment_criteria_met = false`, ordered by `from_date` ascending). The delinquency-range schedule already reflects `delinquencyGraceDays` in the `toDate` of its first period, so no further adjustment is applied to the `fromDate`. `null` when no period is delinquent.

**`delinquencyEffectiveStartDate`:** `delinquencyStartDate` shifted forward by `delinquencyGraceDays` â the date the delinquency clock effectively starts ticking once the cool off period is taken into account. It is set **only** when the earliest delinquent period is the first one (`period_number = 1`) and `delinquencyGraceDays > 0`; `null` otherwise.

**Breach period (`breach = true`):** A breach-schedule period whose `outstanding_amount > 0` after its `toDate` has passed and the WC COB has evaluated it.

**Delinquent period (`min_payment_criteria_met = false`):** A delinquency-range-schedule period whose required minimum payment was not met by its `toDate` once evaluated by the WC COB.

#### Design Decisions and Considerations

##### Grace Days Extend the First Period, They Do Not Move Its Start

Both schedules treat grace days the same way: the **first** period’s `toDate` is extended by the grace days and every subsequent period is chained from that end date. The first period therefore becomes longer, while its `fromDate` stays on the raw anchor.

* **Breach schedule**: `WorkingCapitalLoanBreachScheduleServiceImpl.naturalToDate` adds `breachGraceDays` only when `periodNumber == 1`.
* **Delinquency-range schedule**: `WorkingCapitalLoanDelinquencyRangeScheduleServiceImpl.generateInitialPeriod` adds `delinquencyGraceDays` to the first period’s `toDate`; `generateNextPeriodIfNeeded` chains later periods from `toDate + 1` without any grace.

Because the whole chain shifts with the first period’s end date, extending the first period by `g` days is equivalent to starting it `g` days later. That equivalence is what `breachEffectiveStartDate` and `delinquencyEffectiveStartDate` expose: `fromDate + graceDays` is the date the borrower’s cool off period ends and the breach / delinquency window effectively begins.

`breachStartDate` and `delinquencyStartDate` are therefore both the raw `fromDate` of their earliest flagged period, with no grace arithmetic applied. See Example Scenarios.

##### Derived at Read Time, Not Persisted

All four fields are computed in `enrichWithStartDates` during `retrieveOne` rather than stored as columns. This keeps the values always consistent with the current schedule state (e.g., after a backdated payment clears the earliest breached period, the next retrieve naturally reports the new earliest breached period) without requiring a migration or a maintenance job to keep a denormalized column in sync.

##### The Effective Start Date Is Only Emitted When It Adds Information

Both effective start dates are resolved by the same `resolveEffectiveStartDate`, which returns `null` rather than echoing the plain start date:

```java
if (!Integer.valueOf(1).equals(periodNumber) || graceDays == null || graceDays <= 0) {
    return null;
}
final LocalDate effectiveStartDate = fromDate.plusDays(graceDays);
return DateUtils.isAfter(effectiveStartDate, toDate) ? null : effectiveStartDate;
```

A `null` or zero grace value yields `null`, as does any period other than the first one â those periods carry no grace days, so an "effective" start identical to the plain start would only be noise for the consumer.

##### A Cool Off Period That Never Took Place Is Not Reported

The grace days belong to the first period, and an operation can end that period before they are over. On the breach schedule, a reset that restarts the schedule from its own date cuts the first period down to `[fromDate, resetDate - 1]` while keeping it as period 1, and once that shortened period expires unpaid it is flagged as breached like any other.

When `fromDate + graceDays` falls after the period’s own `toDate`, the cool off period never finished running inside the period it belongs to, so there is nothing to report and `resolveEffectiveStartDate` returns `null`. Reporting the raw arithmetic instead would hand the consumer a date after the period had already ended â and, in the reset case, after the breach itself had been flagged.

The guard is shared by both effective start dates and covers any future operation that shortens a first period; it is not specific to resets.

#### Database Design

##### Overview

No tables or columns are introduced by this feature. All four fields are derived by querying two existing schedule tables.

##### Existing Tables

**`m_wc_loan_breach_schedule`**: read to find the earliest period flagged `breach = true`. The relevant columns are `wc_loan_id`, `from_date`, `to_date`, `period_number`, and `breach`.

**`m_wc_loan_delinquency_range_schedule`**: read to find the earliest period flagged `min_payment_criteria_met = false`. The relevant columns are `wc_loan_id`, `from_date`, `to_date`, `period_number`, and `min_payment_criteria_met`.

#### API Design

##### Endpoints

###### Retrieve a Working Capital Loan

Returns the full WC loan detail, including the derived start dates.

```java
GET /v1/working-capital-loans/{loanId}
GET /v1/working-capital-loans/external-id/{loanExternalId}
```

**Response (relevant fields only):**

```json
{
  "delinquencyGraceDays": 3,            // product/loan delinquency grace days
  "delinquencyStartType": { "id": 2, "code": "DISBURSEMENT", "value": "Disbursement" },
  "breachGraceDays": 5,                 // product/loan breach grace days
  "breachStartDate": [2026, 1, 1],              // fromDate of earliest breached period
  "breachEffectiveStartDate": [2026, 1, 6],     // breachStartDate + breachGraceDays (first period only)
  "delinquencyStartDate": [2026, 1, 1],         // fromDate of earliest delinquent period
  "delinquencyEffectiveStartDate": [2026, 1, 4] // delinquencyStartDate + delinquencyGraceDays (first period only)
}
```

> [!NOTE]
> `breachStartDate`, `breachEffectiveStartDate`, `delinquencyStartDate` and `delinquencyEffectiveStartDate` are read-only and derived. They cannot be set in a create/update request and are absent (or `null`) on responses where the loan is not yet in breach / delinquency, or where the breach / delinquency configuration is not present.

##### Business Events

Every WC loan business event carries the same `breach` and `delinquency` blocks as the retrieve response, because `WorkingCapitalLoanBusinessEventSerializer` builds its Avro payload from `retrieveOne`. `breachEffectiveStartDate` is an optional (`null`-defaulted) addition to `WorkingCapitalBreachDataV1` and `delinquencyEffectiveStartDate` is an optional (`null`-defaulted) addition to `WorkingCapitalLoanDelinquencyDataV1`, so existing consumers remain compatible.

#### Business Rules

##### Breach Start Date

* `breachStartDate` is the `fromDate` of the earliest `m_wc_loan_breach_schedule` row with `breach = true` (`findTopByLoanIdAndBreachTrueOrderByFromDateAsc`), with no grace arithmetic applied.
* The breach schedule is anchored according to `breachStartType`: `LOAN_CREATION` anchors the first period on the loan submitted-on date, while `DISBURSEMENT` (or an unset type) anchors it on the actual disbursement date.
* The breach grace days are **not** added â the breach schedule generator applies them to the first period’s `toDate`, not to its `fromDate`.
* When no breach period exists or none is flagged `breach = true`, `breachStartDate` is `null`.

##### Breach Effective Start Date

* `breachEffectiveStartDate` is `breachStartDate + breachGraceDays`.
* It is emitted only when the earliest breached period is the first one (`period_number = 1`) â later periods carry no grace days.
* It is emitted only when `breachGraceDays` is set and greater than `0`; a `null` or `0` grace yields `null`.
* It is emitted only when the resulting date falls within the period it belongs to. When an operation cut that period short â a reset restarting the schedule from its own date â and `breachStartDate + breachGraceDays` lands after the period’s `toDate`, the value is `null`.
* When no breached period exists, `breachEffectiveStartDate` is `null`.

##### Delinquency Start Date

* `delinquencyStartDate` is the `fromDate` of the earliest still-open past delinquency-range-schedule period that already carries a positive classified `delinquentDays` (`findOpenPastDuePeriodsOrderByFromDateAsc`: `min_payment_criteria_met` is `null` or `false`, `reset = false`, `to_date` on or before the business date), with no grace arithmetic applied. `null` is included because instant classification can mark a period delinquent before COB evaluates `min_payment_criteria_met`.
* The delinquency schedule itself is anchored according to `delinquencyStartType`: `LOAN_CREATION` anchors the first period on the loan submitted-on date, while `DISBURSEMENT` (or an unset type) anchors it on the actual disbursement date. This anchor is resolved in `WorkingCapitalLoanDelinquencyRangeScheduleServiceImpl.generateInitialPeriod`.
* When no delinquent period exists, `delinquencyStartDate` is `null`.

##### Delinquency Effective Start Date

* `delinquencyEffectiveStartDate` is `delinquencyStartDate + delinquencyGraceDays`.
* It is emitted only when the earliest delinquent period is the first one (`period_number = 1`) â later periods carry no grace days.
* It is emitted only when `delinquencyGraceDays` is set and greater than `0`; a `null` or `0` grace yields `null`.
* It is emitted only when the resulting date falls within the period it belongs to; otherwise it is `null`.
* When no delinquent period exists, `delinquencyEffectiveStartDate` is `null`.

#### Example Scenarios

##### Scenario #1: Loan breaches and becomes delinquent on the same COB run

**Setup:**

* Disbursement date `D = 2026-01-01`.
* Breach configuration: 15-day frequency, `breachGraceDays = 5` â first breach period is `[D .. D+14+5]` = `[2026-01-01 .. 2026-01-20]`.
* Delinquency bucket: 20-day frequency, `delinquencyGraceDays = 3` â first delinquency period is `[D .. D+19+3]` = `[2026-01-01 .. 2026-01-23]`.
* The borrower makes no qualifying payment.

**Action:**

The business date is advanced to `2026-01-26`, past the end of both first periods, and the `WC_LOAN_COB` job runs for the loan. A single COB run flags both the first breach period (`breach = true`) and the first delinquency period (`min_payment_criteria_met = false`).

**Expected Behavior:**

* `breachStartDate = 2026-01-01` â the `fromDate` of the first breached period; the breach grace only extended its `toDate`.
* `breachEffectiveStartDate = 2026-01-06` â `breachStartDate` plus `breachGraceDays` (`+5`): the cool off period runs through `2026-01-05`.
* `delinquencyStartDate = 2026-01-01` â the `fromDate` of the first delinquent period.
* `delinquencyEffectiveStartDate = 2026-01-04` â `delinquencyStartDate` plus `delinquencyGraceDays` (`+3`): the cool off period runs through `2026-01-03`.

This is the exact behavior asserted by `WorkingCapitalLoanStartDatesTest.testStartDatesArePopulatedWhenLoanBreachesAndBecomesDelinquent`.

##### Scenario #2: Healthy loan â all start dates null

**Setup:**

* Same product/loan configuration as Scenario #1, disbursed on `D = 2026-01-01`.

**Action:**

The `WC_LOAN_COB` job runs on the disbursement date itself, before any schedule period has expired. No period is flagged.

**Expected Behavior:**

* `breachStartDate = null` â the loan is not in breach.
* `breachEffectiveStartDate = null` â there is no breached period to shift.
* `delinquencyStartDate = null` â the loan is not delinquent.
* `delinquencyEffectiveStartDate = null` â there is no delinquent period to shift.

This is asserted by `WorkingCapitalLoanStartDatesTest.testStartDatesAreNullForHealthyLoan`.

##### Scenario #3: The first period is met and a later one turns delinquent

**Setup:**

* Same product/loan configuration as Scenario #1, disbursed on `D = 2026-01-01`.
* First delinquency period `[2026-01-01 .. 2026-01-23]`, second period `[2026-01-24 .. 2026-02-12]`.

**Action:**

The borrower pays the minimum payment on `2026-01-05`, so the first period meets its criteria. No further payment is made, and the `WC_LOAN_COB` job runs on `2026-02-13`, after the second period has ended.

**Expected Behavior:**

* `delinquencyStartDate = 2026-01-24` â the `fromDate` of the second period, now the earliest delinquent one.
* `delinquencyEffectiveStartDate = null` â the second period carries no grace days, so there is no cool off period to report.

This is asserted by `WorkingCapitalLoanStartDatesTest.testDelinquencyEffectiveStartDateIsNullWhenTheDelinquentPeriodIsNotTheFirstOne`. The breach counterpart is asserted by `WorkingCapitalLoanStartDatesTest.testBreachEffectiveStartDateIsNullWhenTheBreachedPeriodIsNotTheFirstOne`.

##### Scenario #4: Reset inside the breach grace window

**Setup:**

* Same product/loan configuration as Scenario #1, disbursed on `D = 2026-01-01`, so the first breach period is `[2026-01-01 .. 2026-01-20]` and the cool off period would end on `2026-01-06`.

**Action:**

On `2026-01-03` â inside the grace window â a `reset` breach action with `restartPeriodFromResetDate = true` is recorded. `splitPeriodAtReset` cuts the first period down to `[2026-01-01 .. 2026-01-02]` and starts a new period on the reset date. The business date is advanced to `2026-01-04` and the `WC_LOAN_COB` job runs, flagging the shortened first period as breached.

**Expected Behavior:**

* `breachStartDate = 2026-01-01` â the `fromDate` of the cut first period, unchanged by the reset.
* `breachEffectiveStartDate = null` â the cool off period would have ended on `2026-01-06`, after the period itself ended on `2026-01-02`, so there is no cool off period to report.

Undoing the reset rebuilds the first period from its natural length through `restoreSplitPeriod`, which puts the grace days back. Once that restored period expires unpaid, `breachEffectiveStartDate` reports `2026-01-06` again.

This is asserted by `WorkingCapitalLoanStartDatesTest.testBreachEffectiveStartDateIsNullWhenAResetCutsTheFirstPeriodInsideTheGraceWindow` and `WorkingCapitalLoanStartDatesTest.testBreachEffectiveStartDateComesBackWhenTheResetIsUndone`.

##### Exception Cases

* **No breach configuration:** When the product/loan has no `breach_id`, the breach schedule is never generated; `findTopByLoanIdAndBreachTrueOrderByFromDateAsc` returns empty and both `breachStartDate` and `breachEffectiveStartDate` stay `null` regardless of payment behavior.
* **No delinquency bucket:** With no delinquency-range schedule generated, both `delinquencyStartDate` and `delinquencyEffectiveStartDate` stay `null`.
* **`null` or zero grace days:** The plain start date is unaffected and the matching effective start date is `null`, because there is no cool off period to report. Asserted by `WorkingCapitalLoanStartDatesTest.testBreachEffectiveStartDateIsNullWhenNoGraceDaysConfigured` and `WorkingCapitalLoanStartDatesTest.testDelinquencyEffectiveStartDateIsNullWhenNoGraceDaysConfigured`.
* **Flagged period other than the first:** `breachEffectiveStartDate` / `delinquencyEffectiveStartDate` is `null`; only the first period is shifted by the grace days.
* **Reset inside the breach grace window:** A reset that restarts the schedule cuts the first period at the reset date. When that cut lands before the grace days are over, `breachEffectiveStartDate` is `null`; undoing the reset restores the period’s natural end date and the value becomes reportable again.
* **Earliest period subsequently cured:** Because the values are derived at read time, if a backdated payment clears the earliest breached/delinquent period, the **next** retrieve reports the new earliest still-flagged period â or `null` if none remain.
* **List vs. single retrieve:** The paginated WC loan list response does not invoke `enrichWithStartDates`; these fields are populated only by the single-loan retrieve path.

#### Summary

Working Capital Loan Start Dates surface four derived, read-only anchor dates on the WC loan retrieve response. Key aspects include:

* `breachStartDate` â the `fromDate` of the earliest breached breach-schedule period. The breach grace days extend the first period’s `toDate`, so they do not move this date.
* `breachEffectiveStartDate` â `breachStartDate` plus `breachGraceDays`, emitted only for the first breach period, only when grace days are configured, and only when the resulting date still falls inside that period.
* `delinquencyStartDate` â the `fromDate` of the earliest delinquent range-schedule period, likewise unaffected by the delinquency grace days.
* `delinquencyEffectiveStartDate` â `delinquencyStartDate` plus `delinquencyGraceDays`, under the same rules as `breachEffectiveStartDate`.
* The two effective start dates are the customer-facing answer to "when does the cool off period end?".
* All four values are computed at read time in `enrichWithStartDates`, are `null` while the loan is healthy or unconfigured, and stay consistent with the current schedule state without any persisted column.

### Working Capital Loan â Mark as Fraud

#### Purpose

Marking a Working Capital Loan as fraudulent flags an account that has been identified as fraud, so that a
later charge-off routes the write-off to a dedicated **fraud expense** account instead of the regular
charge-off expense account.

The fraud flag is **independent of the charge-off action itself**: it only records that the loan is
fraudulent. It has no accounting effect until the loan is charged off.

#### Functionality

* `fraud` is a boolean flag on the loan account (column `is_fraud` on `m_wc_loan`), defaulting to `false`.
* A loan can be marked as fraud **only while it is active**. Clearing the flag is allowed regardless of status.
* Marking a loan as fraud **does not change the loan status** â the loan keeps its `ACTIVE` status.
* The operation is idempotent: re-sending the same value is a no-op and reports no changes.

#### Validation Rules

* `fraud` is **required** and must be a boolean (`true` or `false`).
* The loan must be **active** to be marked as fraud (`fraud = true`). Clearing the flag (`fraud = false`) is
  allowed in any status.

#### Authorization

The command requires the `SETFRAUD_WORKINGCAPITALLOAN` permission. Users with `ALL_FUNCTIONS` (super user)
are allowed implicitly. Maker-checker is supported and can be enabled for this permission; it is disabled by
default.

#### API

The loan can be addressed by id or by external id:

```java
PUT /v1/working-capital-loans/{loanId}/mark-as-fraud
PUT /v1/working-capital-loans/external-id/{loanExternalId}/mark-as-fraud
```

Both take the same body and produce the same result. An unknown external id returns a 404.

```json
{
  "fraud": true
}
```

Response (`CommandProcessingResult`):

```json
{
  "officeId": 1,
  "clientId": 5,
  "loanId": 12,
  "resourceId": 12,
  "changes": {
    "fraud": true
  }
}
```

`changes` is empty when the flag already had the requested value.

#### Retrieval

The current value is exposed as the `fraud` field of the loan retrieval response:

```java
GET /v1/working-capital-loans/{loanId}
```

#### Accounting Impact

Marking a loan as fraud produces **no journal entries** on its own. The flag is consumed at charge-off time:
a charged-off fraudulent loan debits the **Charge-Off Fraud Expense** account instead of the regular
**Charge-Off Expense** account. All other charge-off processing is identical.

> [!NOTE]
> This command is served through the legacy command-source pipeline, like every other Working Capital
> Loan command, so it is recorded in the command audit trail and can participate in maker-checker.

### Global Configuration Allowed Values

Some global configurations accept only a fixed set of values in `stringValue`. Updates to these configurations are validated against the allowed values, and the allowed values are exposed in the configuration API.

#### Restricted Configurations

| Configuration | Allowed values | Multiple | When the stored value is invalid |
| --- | --- | --- | --- |
| `charge-accrual-date` | `due-date`, `submitted-date` | no | `due-date` is used |
| `next-payment-due-date` | `earliest-unpaid-date`, `next-unpaid-due-date` | no | `earliest-unpaid-date` is used |
| `wcl-charge-accrual-time` | `eod`, `real-time` | no | `eod` is used |
| `pl-charge-accrual-time` | `eod`, `real-time` | no | `eod` is used |
| `account-mapping-for-payment-type` | `Asset`, `Liability`, `Expense` | yes | `Asset` is used |
| `account-mapping-for-charge` | `Income`, `Liability`, `Expense` | yes | `Income` is used |
| `outstanding-interest-calculation-strategy-for-external-asset-transfer` | `TOTAL_OUTSTANDING_INTEREST`, `PAYABLE_OUTSTANDING_INTEREST` | no | operations that read it fail |
| `allowed-loan-statuses-for-external-asset-transfer` | any loan status except `INVALID` | yes | operations that read it fail |
| `allowed-loan-statuses-of-delayed-settlement-for-external-asset-transfer` | any loan status except `INVALID` | yes | operations that read it fail |

#### Updating a Restricted Configuration

`PUT /configurations/{configId}` and `PUT /configurations/name/{configName}` reject a `stringValue` that is not allowed with HTTP 400 and the error code `validation.msg.globalConfiguration.stringValue.is.not.one.of.expected.enumerations`. Every entry of a comma-separated list is checked, and each invalid entry is reported separately.

Values are matched ignoring case and surrounding whitespace, duplicate list entries are dropped, and the value is stored in the spelling listed in `allowedValues`. For example, `EOD` is stored as `eod`.

A configuration that is locked (a trap door configuration after the first loan, savings or share account was created) is reported as locked before its value is checked.

#### Retrieving a Restricted Configuration

Configuration responses carry two additional fields for restricted configurations. Both are omitted for unrestricted configurations.

* `allowedValues` - the allowed values, in the spelling they are stored in
* `multipleValuesAllowed` - whether `stringValue` holds a comma-separated list of allowed values

```json
{
  "name": "wcl-charge-accrual-time",
  "enabled": true,
  "stringValue": "eod",
  "allowedValues": ["eod", "real-time"],
  "multipleValuesAllowed": false
}
```

#### Upgrading

Stored values are not rewritten during the upgrade. Values that differ from an allowed value only in case or surrounding whitespace keep working, and get the stored spelling the next time they are updated through the API.

After the tenant databases are upgraded, every restricted configuration of every tenant is checked once at startup, and a blank or invalid value is logged:

* For a configuration with a default, a `WARN` names the default that is used instead.
* For the external asset transfer configurations, an `ERROR` is logged and the stored value is not replaced: initiating a transfer, or calculating the outstanding interest of a transfer, fails with `error.msg.configuration.property.value.not.allowed` until the value is corrected. Substituting a default would silently change which loans may be transferred, or the amount they are transferred for.

Check the startup log after upgrading and correct any reported value through the configuration API.

Behaviour that changes for an invalid stored value:

| Configuration | Before | Now |
| --- | --- | --- |
| `charge-accrual-date` (working capital loans) | no charge accruals were created | accrues on `due-date` |
| `next-payment-due-date` | delinquency returned no next payment date | `earliest-unpaid-date` is used |
| `account-mapping-for-payment-type`, `account-mapping-for-charge` | the raw value was returned in the template response | the default is returned |
| `allowed-loan-statuses-*` | transfers failed with an `IllegalArgumentException` | transfers fail with `error.msg.configuration.property.value.not.allowed`, naming the configuration and the stored value |
| `outstanding-interest-calculation-strategy-for-external-asset-transfer` | transfers failed with an `UnsupportedOperationException`, or a `NullPointerException` for a blank value | transfers fail with `error.msg.configuration.property.value.not.allowed`, naming the configuration and the stored value |

#### Changes for Custom Modules

Custom modules that call the affected Java APIs need to be updated:

* `ConfigurationDomainService` getters return enums instead of strings:
  
  
  
  
  
  * `getAllowedLoanStatusesForExternalAssetTransfer()` and `getAllowedLoanStatusesOfDelayedSettlementForExternalAssetTransfer()` return `List<LoanStatus>`
  * `getAccrualDateConfigForCharge()` returns `ChargeAccrualDateConfig`
  * `getNextPaymentDateConfigForLoan()` returns `NextPaymentDueDateConfig`
  * `getAssetOwnerTransferOustandingInterestStrategy()` returns `OutstandingInterestStrategyConfig`
* `ConfigurationDomainService` has a new method, `getWclChargeAccrualTime()`, which custom implementations of the interface must provide.
* `TemporaryConfigurationServiceContainer.getAccrualDateConfigForCharge()` was removed; inject `ConfigurationDomainService` instead.
* `Loan.EARLIEST_UNPAID_DATE` and `Loan.NEXT_UNPAID_DUE_DATE` were removed; use `NextPaymentDueDateConfig`.

#### Restricting Another Configuration

1. Add an `AllowedValues` constant to `GlobalConfigurationAllowedValues` and list it in `ALL`. Give it a default unless falling back to one could change a financial outcome.
2. Read the value through `resolve` or `resolveAll` instead of parsing the raw string.
3. Make sure the configuration’s changelog inserts an allowed value. `GlobalConfigurationTest.testRestrictedConfigurationsHoldAllowedValues` fails otherwise.