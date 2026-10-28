# سند نیازمندی‌های مهندسی معکوس پرتفوی تسهیلات، اعتبارات و چرخه حیات وام در Apache Fineract 1.15.0
## (Tier 1: Core Lending, Progressive Loans & Loan Lifecycle Requirements Specification)

---

## ۱. نمای کلی حوزه، معماری دامنه و ناورداهای بنیادین (Executive Summary & Domain Invariants)

این سند مرجع رسمی و استخراج‌شده از سورس‌کد **Apache Fineract 1.15.0** جهت پوشش نیازمندی‌های عملکردی و غیرعملکردی حوزه اعتبارات و مدیریت پرتفوی تسهیلات (Loan Portfolio Domain) در قالب استاندارد بین‌المللی **EARS (Easy Approach to Requirements Syntax)** به صورت دوزبانه (فارسی - انگلیسی) است.

### ارکان معماری و ماژول‌های فعال در این حوزه:
1. **موتور هسته اعتبارات (`fineract-loan`):** مدیریت موجودیت مجتمع تسهیلات (`Loan`)، ماشین وضعیت چرخه حیات (`DefaultLoanLifecycleStateMachine`)، اعتبارسنجی اقساط، پردازش تراکنش‌ها و نگهداری حسابداری وام.
2. **موتور تسهیلات پیش‌رونده (`fineract-progressive-loan`):** سیستم نوین تقسیط و استهلاک داینامیک روزشمار، بازاستهلاک (Re-amortization)، بازتنظیم سن بدهی (Re-aging)، و پیاده‌سازی تخصیص پیشرفته اقساط (`AdvancedPaymentScheduleTransactionProcessor`).
3. **لایه سرویس و هماهنگ‌سازی (`fineract-provider`):** کلاس‌های نگاشت CQRS، نقاط انتهایی REST در JAX-RS (`LoansApiResource`، `LoanProductsApiResource`)، و ترانزکشن‌های دیتابیس با OpenJPA/Hibernate.
4. **موتور مدیریت نکول و معوقات (`Delinquency Subsystem`):** ارزیابی روزهای گذشته از سررسید (DPD)، انتساب بازه‌های سنی (`m_delinquency_bucket` / `m_delinquency_range`)، طبقه‌بندی تسهیلات غیرجاری (NPA) و تعلیق محاسبه نکول (`Pause Delinquency`).

### ناورداهای ریاضی و مالی حاکم بر سیستم (Mathematical & Domain Invariants):
* **توازن مانده بدهی (Balance Conservation Law):**
  $$\text{Total Outstanding} = \text{Principal Outstanding} + \text{Interest Outstanding} + \text{Fee Charges Outstanding} + \text{Penalty Charges Outstanding}$$
* **استهلاک اقساط مساوی (Equated Monthly Installment - EMI):**
  $$EMI = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$$
  که در آن $P$ مانده اصل، $r$ نرخ سود دوره و $n$ تعداد اقساط باقی‌مانده است.
* **محاسبه شاخص روزهای سپری‌شده از سررسید (Days Past Due - DPD):**
  $$DPD = \text{CurrentBusinessDate} - \min(\{\text{DueDate}_i \mid \text{Installment}_i \text{ is Overdue and Unpaid}\})$$

---

## ۲. خلاصه ماتریس نیازمندی‌ها (Requirements Index Matrix)

| شناسه نیازمندی | عنوان نیازمندی (فارسی) | الگوی EARS | کلاس و لایه سورس Fineract |
| :--- | :--- | :--- | :--- |
| **REQ-LOAN-PROD-001** | اعتبارسنجی ارز چندگانه و حدود سقف، کف و مقدار پیش‌فرض اصل تسهیلات | Complex | `LoanProductDataValidator.java` |
| **REQ-LOAN-PROD-002** | متدهای استهلاک اقساط مساوی و اصل مساوی | Optional Feature | `AbstractCumulativeLoanScheduleGenerator.java` |
| **REQ-LOAN-PROD-003** | متدهای محاسبه سود ثابت و مانده نزولی | Optional Feature | `CumulativeFlatInterestLoanScheduleGenerator.java` |
| **REQ-LOAN-PROD-004** | استراتژی پیشرفته تخصیص اقساط و اولویت‌بندی تسویه مؤلفه‌های بدهی | Event-Driven | `AdvancedPaymentScheduleTransactionProcessor.java` |
| **REQ-LOAN-SCHED-001** | تولید جدول اقساط کلاسیک با تجمیع سود دوره‌ای و روزشمار | Event-Driven | `CalculateLoanSchedulePlatformServiceImpl.java` |
| **REQ-LOAN-SCHED-002** | موتور محاسباتی تسهیلات پیش‌رونده با تجدید ساختار داینامیک سود روزشمار | Optional Feature | `ProgressiveLoanScheduleGenerator.java` |
| **REQ-LOAN-SCHED-003** | دوره‌های تنفس در اصل و سود تسهیلات | Optional Feature | `LoanScheduleGeneratorService.java` |
| **REQ-LOAN-SCHED-004** | پیش‌پرداخت اولیه و کاهش فوری مانده اصل تسهیلات | Optional Feature | `LoanDownPaymentHandlerServiceImpl.java` |
| **REQ-LOAN-SCHED-005** | پرداخت چندمرحله‌ای ترانش‌ها و بازتنظیم جدول استهلاک | Complex | `LoanWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-LIFE-001** | ثبت درخواست و ایجاد پرونده تسهیلات در وضعیت در انتظار بررسی | Event-Driven | `LoanApplicationWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-LIFE-002** | تصویب، رد یا انصراف متقاضی از پرونده تسهیلاتی | Complex | `DefaultLoanLifecycleStateMachine.java` |
| **REQ-LOAN-LIFE-003** | پرداخت اولیه و فعال‌سازی پرونده تسهیلات | Complex | `LoanWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-LIFE-004** | تسویه کامل تعهدات و خاتمه عادی پرونده | State-Driven | `DefaultLoanLifecycleStateMachine.java` |
| **REQ-LOAN-LIFE-005** | شناسایی و مدیریت وضعیت مازاد پرداختی مشتری | Complex | `DefaultLoanLifecycleStateMachine.java` |
| **REQ-LOAN-TXN-001** | ثبت بازپرداخت‌های عادی و تخصیص میان اجزای اقساط | Event-Driven | `LoanWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-TXN-002** | تسویه پیش از موعد اختیاری و بازتنظیم سودهای آتی | Event-Driven | `RecalculateInterestPoster.java` |
| **REQ-LOAN-TXN-003** | تسویه اجباری پرونده تسهیلاتی و حال شدن تعهدات آتی | Event-Driven | `LoanAccountDomainService.java` |
| **REQ-LOAN-TXN-004** | معکوس‌سازی تراکنش‌ها، ابطال پرداخت و بازتنظیم سن بدهی | Event-Driven | `LoanWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-TXN-005** | سوخت مطالبات، حذف از ترازنامه و وصول مطالبات سوخت‌شده | Complex | `LoanWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-LOAN-DELINQ-001** | محاسبه اقساط سررسیدگذشته و شاخص روزهای گذشته از موعد | Ubiquitous | `LoanArrearsAgingServiceImpl.java` |
| **REQ-LOAN-DELINQ-002** | دسته‌بندی زمانی مطالبات در سبدهای نکول و بازه‌های سنی | Event-Driven | `DelinquencyWritePlatformServiceImpl.java` |
| **REQ-LOAN-DELINQ-003** | طبقه‌بندی تسهیلات غیرجاری و توقف شناسایی درآمد تعهدی | State-Driven | `LoanAccrualsProcessingService.java` |
| **REQ-LOAN-DELINQ-004** | مکانیزم تعلیق و توقف موقت محاسبه نکول | Complex | `DelinquencyEffectivePauseHelperImpl.java` |
| **REQ-LOAN-RESCHED-001** | ثبت درخواست استمهال و اعتبارسنجی شرایط قرارداد | Event-Driven | `LoanRescheduleRequestDataValidatorImpl.java` |
| **REQ-LOAN-RESCHED-002** | تصویب استمهال با تمدید مدت، تعدیل نرخ سود و دوره تنفس جدید | Complex | `LoanRescheduleRequestWritePlatformServiceImpl.java` |
| **REQ-LOAN-RESCHED-003** | بازتنظیم سن بدهی و بازاستهلاک در موتور تسهیلات پیش‌رونده | Optional Feature | `ProgressiveLoanModelRecalculationService.java` |

---

## ۳. کاتالوگ تفصیلی کارت‌های نیازمندی به تفکیک حوزه‌ها

### بخش ۱: پیکربندی محصول تسهیلات و ناورداهای خط‌مشی اعتباری (Loan Product Configuration & Policy Invariants)

#### REQ-LOAN-PROD-001: اعتبارسنجی ارز چندگانه و حدود سقف، کف و مقدار پیش‌فرض اصل تسهیلات
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While defining or modifying a loan product, when a product configuration payload is submitted, the Fineract Loan Engine shall validate that the currency code conforms to ISO 4217, the fractional digits are within the closed interval `[0, 6]`, and the default principal amount strictly falls within the closed range defined by `[minPrincipal, maxPrincipal]`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  هنگام تعریف یا ویرایش محصول اعتباری در سامانه فاینراکت، مدیر سیستم موظف است پارامترهای پایه‌ای مالی نظیر واحد پول، تعداد ارقام اعشار، ضریب گرد کردن و بازه مجاز اصل تسهیلات (حداقل، پیش‌فرض، حداکثر) را تعیین نماید. موتور اعتبارات فاینراکت باید صحت ساختاری کد ارز سه‌حرفی، مثبت بودن مقادیر و منطقی بودن حدود مجاز را بررسی کند به نحوی که حداقل اصل تسهیلات هرگز بزرگتر از حداکثر آن نبوده و مقدار پیش‌فرض تسهیلات دقیقا در درون این بازه بسته قرار گیرد. این قید مانع از ثبت قراردادهای تسهیلاتی با مبالغ خارج از اختیارات مصوب اعتباری محصول می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the currency code parameter is missing or exceeds 3 characters in length, then the Fineract Loan Engine shall reject the request and return error code "validation.msg.loanproduct.currencyCode.cannot.be.empty".`
  * `If digitsAfterDecimal is not within the range of 0 to 6, then the Fineract Loan Engine shall reject the request and return error code "validation.msg.loanproduct.digitsAfterDecimal.is.not.within.expected.range".`
  * `If minPrincipal is greater than maxPrincipal, then the Fineract Loan Engine shall reject the configuration and return error code "validation.msg.loanproduct.maxPrincipal.must.be.greater.than.or.equal.to.minPrincipal".`
  * `If the default principal amount is less than minPrincipal or greater than maxPrincipal, then the Fineract Loan Engine shall abort persistence and return error code "validation.msg.loanproduct.principal.amount.must.be.within.min.max.range".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanproduct/serialization/LoanProductDataValidator.java`
  * **متد اجرایی:** `#validateForCreate(String json)` و `#validateForUpdate(String json, LoanProduct loanProduct)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('CREATE_LOANPRODUCT')")`, `validation.msg.loanproduct.principal.amount.must.be.within.min.max.range`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_product_loan` (ستون‌های `currency_code`, `currency_digits`, `min_principal_amount`, `principal_amount`, `max_principal_amount`), کلاس `@Entity LoanProduct`

---

#### REQ-LOAN-PROD-002: متدهای استهلاک اقساط مساوی و اصل مساوی
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where the loan product is configured with `AmortizationMethod.EQUAL_INSTALLMENTS`, the Fineract Loan Schedule Generator shall calculate installment amounts such that the sum of principal and interest remains uniform across all regular repayment periods, whereas where configured with `AmortizationMethod.EQUAL_PRINCIPAL`, the Fineract Loan Schedule Generator shall divide the total disbursed principal equally across active installments while allowing the interest portion to decline concurrently with the reducing principal balance.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  محصولات تسهیلاتی می‌توانند ساختار بازپرداخت اقساط را بر پایه دو مدل ریاضی استاندارد بانکی تنظیم کنند:
  ۱. **روش اقساط مساوی (Equal Installments / EMI):** کل مبلغ پرداختی متقاضی (اصل + سود) در تمام دوره‌ها یکسان است. در اقساط نخست، سهم سود بیشتر و سهم اصل کمتر بوده و به تدریج با کاهش مانده بدهی، سهم اصل افزایش می‌یابد.
  ۲. **روش اصل مساوی (Equal Principal):** سهم اصل پرداختی در تمام اقساط ثابت است ($P / N$) و سود هر قسط بر اساس مانده بدهی محاسبه می‌شود، بنابراین مبلغ کل هر قسط با گذشت زمان روندی نزولی پیدا می‌کند.
  موتور تولید اقساط فاینراکت باید بر اساس فیلد `amortization_method_enum` در محصول، فرمول استهلاک مناسب را انتخاب و اعمال نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the amortizationType parameter is not equal to 0 (EQUAL_INSTALLMENTS) or 1 (EQUAL_PRINCIPAL), then the Fineract Loan Engine shall reject the command and return error code "validation.msg.loanproduct.amortizationType.is.not.within.expected.range".`
  * `If isEqualAmortization is set to true on a product that does not support progressive equal amortization schedules, then the Fineract Loan Engine shall raise an "EqualAmortizationUnsupportedFeatureException".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/AbstractCumulativeLoanScheduleGenerator.java`
  * **متد اجرایی:** `#calculateRepaymentSchedule(...)` و `LoanProductDataValidator#validateForCreate()`
  * **کدهای خطا و انوتیشن‌ها:** `validation.msg.loanproduct.amortizationType.is.not.within.expected.range`, اینام `AmortizationMethod`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_product_loan` (ستون `amortization_method_enum`), جدول `m_loan` (ستون `amortization_method_enum`), انتیتی `LoanProductRelatedDetail`

---

#### REQ-LOAN-PROD-003: متدهای محاسبه سود ثابت و مانده نزولی
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a loan product utilizes `InterestMethod.FLAT`, the Fineract Loan Engine shall compute the borrower's total interest obligation based solely upon the initial disbursed principal across the entire tenure, whereas where configured with `InterestMethod.DECLINING_BALANCE`, the Fineract Loan Engine shall compute the interest for each installment cycle strictly upon the outstanding unamortized principal balance at the beginning of that cycle.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  روش محاسبه سود یکی از حیاتی‌ترین پارامترهای هر محصول تسهیلاتی است:
  ۱. **روش سود ثابت (Flat Method):** سود تسهیلات بر اساس اصل اولیه کل تسهیلات و نرخ اسمی برای کل مدت ضرب می‌شود و بازپرداخت‌های میان‌دوره تاثیری در کاهش پایه محاسبه سود ندارند.
  ۲. **روش مانده نزولی (Declining Balance Method):** سود هر دوره منحصراً بر روی مانده اصل مستهلک‌نشده در ابتدای دوره محاسبه می‌شود. در این روش، واریزهای مشتری بی‌درنگ مانده اصل را کاهش داده و در نتیجه سود دوره‌های آتی کاهش می‌یابد.
  سامانه فاینراکت بر اساس پیکربندی محصول، ژنراتور متناظر (`CumulativeFlatInterestLoanScheduleGenerator` یا `CumulativeDecliningBalanceInterestLoanScheduleGenerator`) را فراخوانی می‌کند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the interestType parameter is not in the set {0 (FLAT), 1 (DECLINING_BALANCE)}, then the Fineract Loan Engine shall reject the request and return error code "validation.msg.loanproduct.interestType.is.not.within.expected.range".`
  * `If interestType is configured as FLAT while interestCalculationPeriodType is set to DAILY, then the Fineract Loan Engine shall reject the setup and return error code "validation.msg.loanproduct.interestCalculationPeriodType.flat.not.allowed.with.daily".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/CumulativeFlatInterestLoanScheduleGenerator.java` و `CumulativeDecliningBalanceInterestLoanScheduleGenerator.java`
  * **متد اجرایی:** `DefaultLoanScheduleGeneratorFactory#create(LoanScheduleType, InterestMethod)`
  * **کدهای خطا و انوتیشن‌ها:** `validation.msg.loanproduct.interestType.is.not.within.expected.range`, اینام `InterestMethod`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_product_loan` (ستون `interest_method_enum`), جدول `m_loan` (ستون `interest_method_enum`)

---

#### REQ-LOAN-PROD-004: استراتژی پیشرفته تخصیص اقساط و اولویت‌بندی تسویه مؤلفه‌های بدهی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When a repayment transaction is executed on a loan governed by `AdvancedPaymentScheduleTransactionProcessor`, the Fineract Payment Allocation Processor shall allocate the payment funds across delinquent, current, and advance balances in strict adherence to the ordered list of `PaymentAllocationType` mappings defined in `m_loan_product_payment_allocation_rule` for the active `PaymentAllocationTransactionType`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در بانکداری مدرن و استاندارد Fineract 1.15.0، تخصیص وجه واریزی مشتری نمی‌تواند یک اولویت‌بندی صلب و هاردکد شده باشد. از این رو سامانه «تخصیص پیشرفته پرداخت» (Advanced Payment Allocation) را پیاده‌سازی کرده است که به مؤسسه مالی اجازه می‌دهد به ازای هر نوع تراکنش (نظیر بازپرداخت عادی، پیش‌پرداخت، استرداد پذیرنده، یا تسویه کارمزد)، اولویت تسویه مؤلفه‌ها را در سه وضعیت زمانی زیر تعیین کند:
  - مطالبات معوق سررسیدگذشته (`PAST_DUE_PENALTY`, `PAST_DUE_FEE`, `PAST_DUE_INTEREST`, `PAST_DUE_PRINCIPAL`)
  - مطالبات سررسیدشده جاری (`DUE_PENALTY`, `DUE_FEE`, `DUE_INTEREST`, `DUE_PRINCIPAL`)
  - مطالبات آتی و پیش از موعد (`IN_ADVANCE_PENALTY`, `IN_ADVANCE_FEE`, `IN_ADVANCE_INTEREST`, `IN_ADVANCE_PRINCIPAL`)
  علاوه بر این، در صورت وجود وجه مازاد بر قسط جاری، قاعده رفتار با اقساط آتی (`FutureInstallmentAllocationRule`) تعیین‌کننده استهلاک قسط بعدی (`NEXT_INSTALLMENT`)، استهلاک قسط آخر (`LAST_INSTALLMENT`) یا بازاستهلاک کل برنامه (`REAMORTIZATION`) خواهد بود.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the payment allocation rules configured for a loan product omit mandatory allocation components or introduce duplicates, then the Fineract Loan Engine shall reject the product configuration and return error code "error.msg.payment.allocation.rule.invalid".`
  * `If a loan product enables advanced payment allocation but omits the configuration for the DEFAULT transaction type, then the Fineract Loan Engine shall reject persistence and return error code "error.msg.payment.allocation.default.rule.missing".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/transactionprocessor/impl/AdvancedPaymentScheduleTransactionProcessor.java`
  * **متد اجرایی:** `#processPaymentAllocationRule(...)` و `AdvancedPaymentAllocationsValidator#validate()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.payment.allocation.rule.invalid`, اینام `PaymentAllocationType`, اینام `FutureInstallmentAllocationRule`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_product_payment_allocation_rule` (قید یکتایی `uq_m_loan_product_payment_allocation_rule`), انتیتی `LoanProductPaymentAllocationRule`

---

### بخش ۲: الگوریتم‌های تولید جدول اقساط و استهلاک (Schedule Generation & Amortization Algorithms)

#### REQ-LOAN-SCHED-001: تولید جدول اقساط کلاسیک با تجمیع سود دوره‌ای و روزشمار
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When a schedule generation request is received for a classic cumulative loan, the Fineract Loan Schedule Generator shall generate an ordered sequence of installments in `m_loan_repayment_schedule` honoring the configured repayment frequency, calendar day convention (Actual/Actual, Actual/365, Actual/364, or 30/360), and interest calculation period.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  موتور تولید اقساط سنتی فاینراکت (`Cumulative Loan Schedule Generator`) بر مبنای پارامترهای تعداد اقساط (`numberOfRepayments`)، دوره تناوب بازپرداخت (`repaymentEvery` + روز/هفته/ماه/سال)، تاریخ اولین پرداخت و روش شمارش روزها (Days in Year: 360, 365, 364, Actual و Days in Month: 30, Actual)، جدول زمانی سررسیدها را ایجاد می‌کند. موتور برای هر قسط، سهم سود تعهدی، سهم اصل استهلاک‌یافته، کارمزدهای سررسیدشده و مانده نزولی را تا تسویه کامل اصل وام در آخرین قسط محاسبه و ذخیره می‌نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If repaymentEvery is null or less than or equal to zero, then the Fineract Loan Engine shall reject schedule generation and return error code "validation.msg.loan.repaymentEvery.must.be.greater.than.zero".`
  * `If numberOfRepayments is less than 1, then the Fineract Loan Engine shall reject schedule calculation and return error code "validation.msg.loan.numberOfRepayments.must.be.greater.than.zero".`
  * `If the first repayment date falls prior to or exactly on the disbursement date, then the Fineract Loan Engine shall abort calculation and return error code "error.msg.loan.first.repayment.date.cannot.be.before.disbursement.date".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/AbstractCumulativeLoanScheduleGenerator.java`
  * **متد اجرایی:** `#generate(MathContext mc, LoanApplicationTerms loanApplicationTerms, Set<LoanCharge> loanCharges, HolidayDetailDTO holidayDetailDTO)`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.first.repayment.date.cannot.be.before.disbursement.date`, `validation.msg.loan.repaymentEvery.must.be.greater.than.zero`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_repayment_schedule` (ستون‌های `installment`, `fromdate`, `duedate`, `principal_amount`, `interest_amount`), انتیتی `LoanRepaymentScheduleInstallment`

---

#### REQ-LOAN-SCHED-002: موتور محاسباتی تسهیلات پیش‌رونده با تجدید ساختار داینامیک سود روزشمار
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a loan product is configured with `LoanScheduleProcessingType.PROGRESSIVE`, the Fineract Progressive Loan Engine shall project dynamic interest accruals using exact daily compounding models, adjust future amortization schedules upon every financial transaction, and prevent mutation of settled historic installment periods.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  ماژول جدید `fineract-progressive-loan` برای برطرف کردن محدودیت‌های محاسباتی صلب در جدول اقساط کلاسیک طراحی شده است. در تسهیلات پیش‌رونده، سود وام به صورت روزشمار دقیق و روز به روز بر مبنای مانده واقعی بدهی محاسبه می‌گردد. با هرگونه تراکنش واریزی زودتر یا دیرتر از موعد، یا ثبت پرداخت‌های چندمرحله‌ای، موتور محاسباتی `ProgressiveEMICalculator` ارزش فعلی اقساط آتی را بدون دست‌کاری اقساط تسویه‌شده گذشته مجدداً شبیه‌سازی و بازاستهلاک می‌کند. این ویژگی امکان شناسایی دقیق کارمزدهای سرمایه‌شده (`Capitalized Income`) و بازتنظیم منعطف برنامه را فراهم می‌سازد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a loan with progressive schedule is configured without an Advanced Payment Allocation Strategy, then the Fineract Loan Engine shall abort creation and return error code "error.msg.loan.progressive.requires.advanced.payment.allocation".`
  * `If an interest rate change operation in a progressive loan contains an effective date prior to the last interest recalculation point, then the Fineract Loan Engine shall reject the operation and return error code "error.msg.progressive.loan.interest.rate.change.date.invalid".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/loanschedule/domain/ProgressiveLoanScheduleGenerator.java`
  * **متد اجرایی:** `#generate(MathContext mc, LoanApplicationTerms loanApplicationTerms, Set<LoanCharge> loanCharges, HolidayDetailDTO holidayDetailDTO)` و `ProgressiveLoanModelRecalculationService#recalculateProgressiveLoanModel()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.progressive.requires.advanced.payment.allocation`, کلاس `ProgressiveEMICalculator`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون `loan_schedule_processing_type`), جدول `m_loan_repayment_schedule`, انتیتی `ProgressiveLoanModel`

---

#### REQ-LOAN-SCHED-003: دوره‌های تنفس در اصل و سود تسهیلات
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a loan account defines `graceOnPrincipalPayment` for $M$ periods and `graceOnInterestPayment` for $K$ periods, the Fineract Loan Schedule Generator shall set the scheduled principal obligation to zero for the first $M$ repayment installments and the scheduled interest obligation to zero for the first $K$ repayment installments, distributing the remaining principal amortization across subsequent regular installments.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در تسهیلات حمایتی، تولیدی و خوداشتغالی، بانک‌ها برای تسهیل بازپرداخت در ماه‌های آغازین کسب‌وکار، دوره تنفس (Grace Period) قائل می‌شوند:
  - **تنفس در اصل وام (`graceOnPrincipalPayment`):** در $M$ قسط اول، مشتری هیچ مبلغی بابت اصل پرداخت نمی‌کند (`principal_amount = 0`) و تنها سود متعلقه ماهانه را تسویه می‌نماید. اصل وام پس از پایان دوره تنفس مستهلک می‌شود.
  - **تنفس در سود وام (`graceOnInterestPayment`):** در $K$ قسط نخست، سود مطالبه نمی‌شود (`interest_amount = 0`).
  موتور تقسیط فاینراکت موظف است جدول استهلاک را مطابق با این متغیرها به صورت خودکار مقیاس‌بندی نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If graceOnPrincipalPayment is greater than or equal to the numberOfRepayments, then the Fineract Loan Engine shall reject the contract terms and return error code "error.msg.loan.graceOnPrincipalPayment.must.be.less.than.numberOfRepayments".`
  * `If graceOnInterestPayment exceeds the total repayment count, then the Fineract Loan Engine shall reject the configuration and return error code "error.msg.loan.graceOnInterestPayment.must.be.less.than.numberOfRepayments".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanScheduleGeneratorService.java`
  * **متد اجرایی:** `AbstractCumulativeLoanScheduleGenerator#applyGracePeriods(...)`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.graceOnPrincipalPayment.must.be.less.than.numberOfRepayments`, `error.msg.loan.graceOnInterestPayment.must.be.less.than.numberOfRepayments`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `grace_on_principal_periods`, `grace_on_interest_periods`), جدول `m_product_loan`

---

#### REQ-LOAN-SCHED-004: پیش‌پرداخت اولیه و کاهش فوری مانده اصل تسهیلات
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where the down payment policy is enabled on a loan product, when the initial loan disbursement is executed, the Fineract Loan Engine shall automatically generate a down payment transaction based on `disbursedAmountPercentageForDownPayment`, immediately reduce the disbursed principal balance, and calculate the amortization schedule strictly upon the net financed principal.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در تسهیلات خرید مسکن، خودرو یا لیزینگ کالا، بانک بخشی از ارزش کل دارایی را به عنوان «آورده متقاضی یا پیش‌پرداخت» (Down Payment) در نظر می‌گیرد. در فاینراکت، با فعال‌سازی این قابلیت در سطح محصول، هنگام پرداخت اولین مرحله وام، سیستم بلافاصله یک تراکنش با نوع `DOWN_PAYMENT` ثبت کرده، مانده اصل بدهی را کاهش می‌دهد، و جدول اقساط را صرفاً بر مبنای مبلغ خالص تامین‌مالی‌شده ($Disbursed - DownPayment$) تنظیم می‌نماید. اسناد حسابداری مربوط به دریافت پیش‌پرداخت نیز به صورت خودکار صادر می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If disbursedAmountPercentageForDownPayment is not within the range (0.00, 100.00], then the Fineract Loan Engine shall reject the product or loan setup and return error code "validation.msg.loanproduct.disbursedAmountPercentageForDownPayment.not.within.expected.range".`
  * `If the calculated down payment amount equals or exceeds the total approved disbursement amount, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.downpayment.amount.exceeds.disbursement".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanDownPaymentHandlerServiceImpl.java`
  * **متد اجرایی:** `#handleDownPayment(ScheduleGeneratorDTO, JsonCommand, LoanTransaction, Loan)`
  * **کدهای خطا و انوتیشن‌ها:** `LoanDownPaymentTransactionValidator#validate()`, `validation.msg.loanproduct.disbursedAmountPercentageForDownPayment.not.within.expected.range`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_product_loan` (ستون‌های `enable_down_payment`, `disbursed_amount_percentage_down_payment`), جدول `m_loan`, جدول `m_loan_transaction` (تراکنش نوع `DOWN_PAYMENT`)

---

#### REQ-LOAN-SCHED-005: پرداخت چندمرحله‌ای ترانش‌ها و بازتنظیم جدول استهلاک
* **الگوی EARS:** Complex
* **EARS Statement:**
  > Where multi-disbursal is enabled on a loan product, while a loan account is in "ACTIVE" state, when a subsequent tranche disbursement is posted within the approved principal limit and maximum tranche count, the Fineract Loan Engine shall record the tranche details in `m_loan_disbursement_detail` and recalculate future installment principal and interest obligations to amortize the increased outstanding principal.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در تسهیلات ساخت‌وساز یا پروژه‌های عمرانی، اصل تسهیلات یک‌باره پرداخت نمی‌شود بلکه متناسب با صورت‌وضعیت‌ها در قالب ترانش‌های متوالی (Tranches) به حساب مشتری واریز می‌گردد. فاینراکت موظف است با هر پرداخت ترانش جدید، ضمن حصول اطمینان از عدم تجاوز مجموع پرداختی‌ها از سقف کل مصوب و رعایت حداکثر تعداد ترانش‌های مجاز (`max_tranche_count`)، جدول اقساط سررسیدنشده آتی را بازنگری کرده و اقساط جدید را متناسب با مانده اصل افزایش‌یافته و تاریخ‌های جدید بازمحاسبه نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the sum of all disbursed and requested tranches exceeds the approved loan principal amount, then the Fineract Loan Engine shall reject the disbursement and return error code "error.msg.loan.disbursement.cannot.be.greater.than.approved.principal".`
  * `If the tranche disbursement date is prior to the previous actual disbursement date, then the Fineract Loan Engine shall reject the tranche and return error code "error.msg.loan.disbursement.date.cannot.be.prior.to.previous.disbursements".`
  * `If the total number of disbursed tranches exceeds maxTrancheCount, then the Fineract Loan Engine shall abort the payout and return error code "error.msg.loan.disbursements.exceed.max.tranche.count".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#disburseLoan(Long loanId, JsonCommand command, Boolean isAccountTransfer)`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.disbursement.cannot.be.greater.than.approved.principal`, `error.msg.loan.disbursements.exceed.max.tranche.count`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_disbursement_detail` (ستون‌های `principal`, `disbursement_date`), انتیتی `LoanDisbursementDetails`, جدول `m_product_loan` (ستون `multi_disburse_loan`)

---

### بخش ۳: گذار ماشین وضعیت و چرخه حیات پرونده تسهیلاتی (Loan Account Lifecycle & State Transitions)

#### REQ-LOAN-LIFE-001: ثبت درخواست و ایجاد پرونده تسهیلات در وضعیت در انتظار بررسی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When a valid loan application request payload is submitted by an authorized loan officer, the Fineract Loan Engine shall validate client eligibility, persist the new loan aggregate in `m_loan` with status code 100 (`SUBMITTED_AND_PENDING_APPROVAL`), generate a unique tenant-scoped account number, and publish a `LoanCreatedBusinessEvent`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  نقطه آغاز چرخه حیات تسهیلات، ثبت فرم درخواست تسهیلات توسط کارشناس شعبه است. سیستم فاینراکت موظف است هویت متقاضی (شخص حقیقی یا حقوقی فعال)، تطابق شرایط درخواستی با مقررات محصول (مبلغ، مدت، نرخ سود، کارمزدها)، عدم وجود سابقه منفی ناسازگار و انتساب کارشناس تسهیلات (`loan_officer_id`) را بررسی نماید. با ثبت موفقیت‌آمیز، پرونده در وضعیت اولیه «ثبت‌شده و در انتظار تصویب» (کد ۱۰۰) قرار گرفته و شماره حساب منحصر‌به‌فردی به آن تخصیص می‌یابد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the target client or group is not in an "ACTIVE" state at the time of submission, then the Fineract Loan Engine shall reject the application and return error code "error.msg.loan.client.or.group.must.be.active".`
  * `If the loan product referenced is inactive or outside its validity date window, then the Fineract Loan Engine shall reject creation and return error code "error.msg.loan.product.is.not.active".`
  * `If the submitted principal amount violates the min/max constraints of the loan product, then the Fineract Loan Engine shall reject the payload and return error code "error.msg.loan.principal.amount.is.not.within.min.max.range".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanApplicationWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#submitApplication(JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('CREATE_LOAN')")`, رویداد `LoanCreatedBusinessEvent`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `loan_status_id = 100`, `submittedon_date`), انتیتی `Loan`

---

#### REQ-LOAN-LIFE-002: تصویب، رد یا انصراف متقاضی از پرونده تسهیلاتی
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a loan account is in `SUBMITTED_AND_PENDING_APPROVAL` status, when an approval, rejection, or withdrawal command is received from an authorized officer, the Fineract Loan State Machine shall transition the account status to `APPROVED` (200), `REJECTED` (500), or `WITHDRAWN_BY_CLIENT` (400) respectively, recording the decision timestamp, officer user ID, and audit notes.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  پس از ارزیابی اعتباری و اعتبارسنجی وثایق، پرونده در کارتابل کمیته اعتبارات قرار می‌گیرد:
  ۱. **تصویب (Approval):** در صورت تایید، پرونده به وضعیت مصوب (۲۰۰) منتقل شده و تاریخ و کاربر تاییدکننده ثبت می‌شود. امکان تعدیل مبلغ مصوب (`approved_principal`) نسبت به تقاضای اولیه وجود دارد.
  ۲. **رد تقاضا (Rejection):** در صورت عدم احراز شرایط اعتباری، وضعیت پرونده به ردشده (۵۰۰) تغییر یافته و مختومه می‌شود.
  ۳. **انصراف متقاضی (Withdrawal):** در صورت درخواست کتبی متقاضی پیش از تصویب، پرونده به وضعیت انصراف‌یافته (۴۰۰) منتقل می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an approval command is executed on an account whose status is not "SUBMITTED_AND_PENDING_APPROVAL", then the Fineract Loan Engine shall reject the transition and return error code "error.msg.loan.not.submitted.and.pending.approval".`
  * `If the approval date is prior to the application submitted date, then the Fineract Loan Engine shall reject the command and return error code "error.msg.loan.approval.date.cannot.be.before.submitted.date".`
  * `If the approved principal exceeds the applied amount and over-applied amounts are not enabled on the product, then the Fineract Loan Engine shall reject the action and return error code "error.msg.loan.approved.amount.cannot.exceed.applied.amount".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#approveLoanApplication(Long loanId, JsonCommand command)`, `#rejectLoanApplication(...)`, `#withdrawLoanApplication(...)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('APPROVE_LOAN')")`, اینام `LoanStatus` (200, 400, 500)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `loan_status_id`, `approvedon_date`, `approvedby_id`, `rejectedon_date`, `withdrawnon_date`), کلاس `DefaultLoanLifecycleStateMachine`

---

#### REQ-LOAN-LIFE-003: پرداخت اولیه و فعال‌سازی پرونده تسهیلات
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a loan account is in `APPROVED` status, when a disbursement command is executed with a valid disbursement date, the Fineract Loan Engine shall release the approved principal, transition the loan status to `ACTIVE` (300), generate the binding repayment schedule installments, apply origination charges, and post balanced journal entries debiting the loan portfolio asset account and crediting the source funding account.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  هنگامی که تسهیلات مصوب می‌شود، شعبه مجاز به پرداخت وجه به مشتری (واریز نقدی یا انتقال به حساب پس‌انداز مشتری از طریق `disburseToSavings`) است. با تایید پرداخت، وضعیت پرونده از مصوب (۲۰۰) به فعال (۳۰۰) منتقل می‌شود، تاریخ واقعی پرداخت (`disbursedon_date`) ثبت شده، اقساط نهایی قطعی می‌گردند و اسناد حسابداری دوبل در دفتر کل (GL) صادر می‌شود. همچنین کارمزدهای بدو پرداخت شناسایی یا از وجه کسر می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the loan account is not in "APPROVED" status at the time of disbursement, then the Fineract Loan Engine shall reject the command and return error code "error.msg.loan.not.approved".`
  * `If the disbursement date is prior to the loan approval date, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.disbursement.date.cannot.be.before.approved.date".`
  * `If the disbursement date is in the future relative to the system business date and future disbursals are disabled, then the Fineract Loan Engine shall reject the request and return error code "error.msg.loan.disbursement.date.cannot.be.in.the.future".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#disburseLoan(Long loanId, JsonCommand command, Boolean isAccountTransfer)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('DISBURSE_LOAN')")`, رویداد `LoanDisbursalBusinessEvent`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `loan_status_id = 300`, `disbursedon_date`, `disbursedby_id`), جدول `m_loan_transaction` (تراکنش نوع ۱: `DISBURSEMENT`), جدول `acc_gl_journal_entry`

---

#### REQ-LOAN-LIFE-004: تسویه کامل تعهدات و خاتمه عادی پرونده
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While a loan account is in `ACTIVE` status, when a financial transaction reduces the outstanding principal, interest, fees, and penalties to zero and all charges are settled or waived, the Fineract Loan State Machine shall transition the account status to `CLOSED_OBLIGATIONS_MET` (600), record `closedon_date`, and release associated active loan collaterals.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  خاتمه مطلوب و عادی یک قرارداد اعتباری زمانی اتفاق می‌افتد که مدیون تمامی تعهدات مندرج در جدول اقساط (شامل اصل، سود، کارمزدها و جرایم دیرکرد احتمالی) را پرداخت نماید. ماشین وضعیت فاینراکت پس از هر تراکنش واریز، مانده‌های تجمیعی را چک کرده و در صورت صفر شدن بدهی و پرداخت کامل هزینه‌ها، بدون نیاز به اقدام دستی کاربر، وضعیت پرونده را به «تسویه کامل تعهدات» (کد ۶۰۰) تغییر می‌دهد و وثایق ترهین‌شده را جهت آزادسازی علامت‌گذاری می‌کند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an active loan account still possesses unpaid active charges, then the Fineract Loan State Machine shall not transition the account to "CLOSED_OBLIGATIONS_MET" until all charges are fully settled or formally waived.`
  * `If a subsequent transaction reversal occurs on a loan in "CLOSED_OBLIGATIONS_MET" status that re-establishes an outstanding debt, then the Fineract Loan State Machine shall revert the loan status back to "ACTIVE".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/DefaultLoanLifecycleStateMachine.java`
  * **متد اجرایی:** `#determineTransitionFromActive(Loan loan, boolean isOverpaid, boolean isRepaidInFull, boolean isAllChargesPaid, LocalDate transactionDate)`
  * **کدهای خطا و انوتیشن‌ها:** رویداد `LoanStatusTransition.to(LoanStatus.CLOSED_OBLIGATIONS_MET, LoanEvent.REPAID_IN_FULL)`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `loan_status_id = 600`, `closedon_date`), انتیتی `Loan`

---

#### REQ-LOAN-LIFE-005: شناسایی و مدیریت وضعیت مازاد پرداختی مشتری
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a loan account is in `ACTIVE` or `CLOSED_OBLIGATIONS_MET` status, when a processed payment exceeds the total outstanding balance, the Fineract Loan State Machine shall credit the surplus to `total_overpaid_derived`, transition the loan status to `OVERPAID` (700), record `overpaidon_date`, and hold the balance for credit balance refund or account transfer.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  چنانچه مشتری مبلغی بیش از مجموع کل بدهی خود واریز کند، سیستم نباید مانده اصل یا سود را منفی کند، بلکه موظف است مازاد پرداختی را در فیلد اختصاصی `total_overpaid_derived` شناسایی نماید. ماشین وضعیت، پرونده را به وضعیت مازاد پرداختی (`OVERPAID` - کد ۷۰۰) منتقل می‌کند. این حساب تا زمان استرداد وجه به متقاضی (از طریق تراکنش `LOAN_CREDIT_BALANCE_REFUND`) یا انتقال به حساب پس‌انداز، به عنوان بدهی بانک به مشتری در دفاتر ثبت می‌گردد. پس از استرداد کامل مازاد، پرونده به وضعیت ۶۰۰ بازگردانده می‌شود.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a credit balance refund is requested for an amount greater than total_overpaid_derived, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.refund.amount.exceeds.overpaid.amount".`
  * `If an overpaid refund transaction brings the overpaid amount to zero while total outstanding remains zero, then the Fineract Loan State Machine shall transition the account status to "CLOSED_OBLIGATIONS_MET".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/DefaultLoanLifecycleStateMachine.java`
  * **متد اجرایی:** `#determineTransitionFromOverpaid(...)` و `LoanWritePlatformServiceJpaRepositoryImpl#refundLoanPayment(...)`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.refund.amount.exceeds.overpaid.amount`, رویداد `LoanEvent.LOAN_OVERPAYMENT`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون‌های `loan_status_id = 700`, `total_overpaid_derived`, `overpaidon_date`)

---

### بخش ۴: تراکنش‌های مالی و پردازش بازپرداخت تسهیلات (Loan Transactions & Financial Operations)

#### REQ-LOAN-TXN-001: ثبت بازپرداخت‌های عادی و تخصیص میان اجزای اقساط
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized loan repayment command is received for an active loan account, the Fineract Loan Transaction Processing Service shall validate the transaction date, persist a new `LoanTransaction` of type `REPAYMENT`, allocate the funds across installment dues in accordance with the transaction processing strategy, decrement outstanding balances, and emit a `LoanTransactionMakeRepaymentPostBusinessEvent`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  عملیات بازپرداخت اقساط توسط وام‌گیرنده از طریق شعبه، اینترنت‌بانک، درگاه‌های پرداخت، یا کسر خودکار از حساب پس‌انداز انجام می‌پذیرد. سرویس پردازش تراکنش فاینراکت ابتدا تاریخ و مبلغ واریزی را اعتبارسنجی می‌کند، سپس یک سابقه تراکنش در `m_loan_transaction` با نوع ۲ (`REPAYMENT`) ایجاد می‌نماید و با فراخوانی استراتژی تخصیص محصول، وجه را به ترتیب به جرایم معوق، کارمزدهای معوق، سود معوق، سود جاری، اصل معوق و اصل جاری اختصاص می‌دهد. اسناد حسابداری دوبل متناظر بلافاصله صادر می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the repayment transaction amount is null or less than or equal to zero, then the Fineract Loan Engine shall reject the operation and return error code "error.msg.loan.transaction.amount.must.be.greater.than.zero".`
  * `If the repayment transaction date is prior to the loan disbursement date, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.transaction.cannot.be.prior.to.disbursement.date".`
  * `If the repayment transaction date is set to a future calendar date, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.transaction.cannot.be.in.the.future".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#makeLoanRepayment(LoanTransactionType repaymentTransactionType, Long loanId, JsonCommand command, boolean isRecoveryRepayment)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('REPAYMENT_LOAN')")`, `error.msg.loan.transaction.cannot.be.prior.to.disbursement.date`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_transaction` (ستون‌های `transaction_type_enum = 2`, `amount`, `transaction_date`), جدول `m_loan_repayment_schedule`, انتیتی `LoanTransaction`

---

#### REQ-LOAN-TXN-002: تسویه پیش از موعد اختیاری و بازتنظیم سودهای آتی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an early prepayment transaction is executed by a borrower in an amount exceeding the current installment due, the Fineract Loan Engine shall allocate the surplus to accelerate principal amortization, recalculate subsequent daily accrued interest on the lowered principal, and compress or re-amortize future schedule installments according to the product's prepayment policy.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  وام‌گیرندگان بر اساس قرارداد و قوانین بانکی حق دارند پیش از فرارسیدن موعد سررسید، بخشی از اصل تسهیلات یا کل بدهی را واریز کنند. سامانه فاینراکت در صورت دریافت پیش‌پرداخت، پس از تسویه قسط جاری، مازاد وجه را مستقیماً به کاهش اصل تسهیلات اختصاص می‌دهد. در صورت فعال بودن قابلیت بازمحاسبه سود (`isInterestRecalculationEnabled`)، سیستم با انتشار رویداد و پردازش توسط `RecalculateInterestPoster`، سود روزهای آتی را بر مبنای اصل کاهش‌یافته بازتنظیم می‌کند که این امر بار سود کل تسهیلات را برای مشتری به صورت عادلانه کاهش می‌دهد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a prepayment transaction is attempted on an account that is closed or charged off, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.is.closed".`
  * `If an early prepayment exceeds the total net debt required to fully close the loan, then the Fineract Loan Engine shall absorb the required payoff amount to settle obligations and credit the remaining balance to total_overpaid_derived.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#makeLoanRepayment(...)` و `RecalculateInterestPoster#postInterestRecalculation(...)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('REPAYMENT_LOAN')")`, `LoanTransactionType.PREPAYMENT`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_transaction`, جدول `m_loan_repayment_schedule`, انتیتی `LoanRepaymentScheduleInstallment`

---

#### REQ-LOAN-TXN-003: تسویه اجباری پرونده تسهیلاتی و حال شدن تعهدات آتی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized officer executes a foreclosure command on an active loan, the Fineract Loan Engine shall verify that no undisbursed tranches remain, accelerate all unearned future interest obligations to be waived, compute the exact payoff balance as of the foreclosure date, and upon settlement, archive the schedule and transition the account sub-status to `FORECLOSED`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  تسویه اجباری (Foreclosure) فرآیندی حقوقی و مالی است که طی آن بانک به دلیل نقض تعهدات، توثیق وثایق، یا تقاضای تسویه اضطراری، کلیه اقساط آتی تسهیلات را حال می‌کند. در فاینراکت، با اجرای دستور `forecloseLoan`، ابتدا بررسی می‌شود که هیچ ترانش پرداخت‌نشده‌ای قبل از تاریخ تسویه وجود نداشته باشد. سپس سودهای تحقق‌نیافته پس از تاریخ تسویه ابطال/بخشوده شده و مانده خالص اصل بدهی به همراه سود تعهدی تا روز جاری مطالبه می‌شود. پس از صدور سند، جدول اقساط قبلی در `m_loan_repayment_schedule_history` آرشیو شده و پرونده با زیروضعیت `FORECLOSED` قفل می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a loan has undisbursed tranches scheduled prior to or on the foreclosure date, then the Fineract Loan Engine shall abort the operation and return error code "loan.with.undisbursed.tranche.before.foreclosure.cannot.be.foreclosured".`
  * `If an attempt is made to adjust or reopen a foreclosed loan transaction, then the Fineract Loan Engine shall reject the modification and return error code "loan.cannot.be.reopened.as.it.is.foreclosured".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#forecloseLoan(Long loanId, JsonCommand command)` و `LoanAccountDomainService#foreCloseLoan(...)`
  * **کدهای خطا و انوتیشن‌ها:** `loan.with.undisbursed.tranche.before.foreclosure.cannot.be.foreclosured`, `loan.cannot.be.reopened.as.it.is.foreclosured`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون `loan_sub_status_id`), جدول `m_loan_transaction`, جدول `m_loan_repayment_schedule_history`

---

#### REQ-LOAN-TXN-004: معکوس‌سازی تراکنش‌ها، ابطال پرداخت و بازتنظیم سن بدهی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized transaction reversal or adjustment command (`undodisbursal` or `adjustTransaction`) is processed, the Fineract Loan Engine shall mark the target transaction as reversed (`is_reversed = true`), back out the corresponding GL journal entries, replay all subsequent transactions in strict chronological order, and restore the repayment schedule and arrears aging states.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در صورت بروز اشتباه کاربر شعبه در ثبت مبلغ یا تاریخ پرداخت، یا برگشت خوردن چک/حواله، سیستم نیاز به مکانیزم برگشت تراکنش دارد. فاینراکت هرگز رکوردهای مالی را به صورت فیزیکی از دیتابیس حذف نمی‌کند (`Audit Trail Integrity`). در عوض، پرچم `is_reversed` تراکنش هدف را برابر با true قرار داده، اسناد اصلاحی در دفتر کل صادر می‌کند، و کلیه تراکنش‌های ثبت‌شده پس از آن تاریخ را به ترتیب زمانی مجدداً بازپردازش (`reprocess`) می‌نماید تا مانده اقساط، سود تعهدی و سن معوقات دقیقاً به وضعیت صحیح بازگردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If undo loan disbursal is attempted on an account that is already charged-off, then the Fineract Loan Engine shall reject the operation and return error code "error.msg.loan.is.charged.off".`
  * `If transaction adjustment is attempted on a loan transaction linked to active chargebacks, then the Fineract Loan Engine shall reject the adjustment and return error code "error.msg.loan.transaction.update.not.allowed".`
  * `If adjusting an interest refund transaction is attempted directly, then the Fineract Loan Engine shall reject the action and return error code "error.msg.loan.transaction.update.not.allowed".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#undoLoanDisbursal(Long loanId, JsonCommand command)` و `#adjustLoanTransaction(Long loanId, Long transactionId, JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('DISBURSALUNDO_LOAN')")`, `error.msg.loan.is.charged.off`, رویداد `LoanUndoDisbursalBusinessEvent`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_transaction` (ستون `is_reversed`), جدول `acc_gl_journal_entry` (اسناد معکوس), انتیتی `LoanTransaction`

---

#### REQ-LOAN-TXN-005: سوخت مطالبات، حذف از ترازنامه و وصول مطالبات سوخت‌شده
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While an active loan possesses uncollectible arrears, when an authorized write-off command is executed, the Fineract Loan Engine shall derecognize remaining asset balances, transition the loan status to `CLOSED_WRITTEN_OFF` (601), and issue journal entries debiting Bad Debt Expense and crediting Loans Receivable; and while in `CLOSED_WRITTEN_OFF` status, when a recovery payment is received, the Fineract Loan Engine shall accept the payment without reopening the loan and credit the Bad Debt Recovery Income account.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  هنگامی که وصول یک فقره تسهیلات بر اساس ارزیابی‌های اعتباری و حقوقی غیرممکن تشخیص داده شود، بانک اقدام به سوخت مطالبات (Write-Off) می‌کند. طی این عملیات، مانده طلب از سرفصل دارایی‌های تسهیلاتی ترازنامه حذف شده، وضعیت پرونده به `CLOSED_WRITTEN_OFF` (۶۰۱) تغییر یافته و به حساب هزینه مطالبات سوخت‌شده منتقل می‌شود؛ پرونده از حیث پیگیری‌های حقوقی باز می‌ماند. اگر پس از سوخت، وجهی از مشتری یا محل وثایق وصول شود، تراکنش با نوع `RECOVERY_REPAYMENT` ثبت شده و وجه به عنوان درآمد متفرقه وصول مطالبات سوخت‌شده بستانکار می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a write-off transaction is attempted on a loan account that is not in "ACTIVE" status, then the Fineract Loan Engine shall reject the request and return error code "error.msg.loan.cannot.be.written.off.not.active".`
  * `If a recovery repayment amount exceeds the total remaining written-off principal balance, then the Fineract Loan Engine shall reject the transaction and return error code "error.msg.loan.recovery.repayment.amount.cannot.be.greater.than.written.off.amount".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#writeOff(Long loanId, JsonCommand command)` و `LoanDownPaymentHandlerServiceImpl#handleRepaymentOrRecoveryOrWaiverTransaction(...)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('WRITEOFF_LOAN')")`, `error.msg.loan.recovery.repayment.amount.cannot.be.greater.than.written.off.amount`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون `loan_status_id = 601`), جدول `m_loan_transaction` (تراکنش نوع ۶: `WRITE_OFF` و نوع ۵: `RECOVERY_REPAYMENT`)

---

### بخش ۵: مدیریت دیرکرد، معوقات و دارایی‌های غیرجاری (Delinquency, NPA & Overdue Management)

#### REQ-LOAN-DELINQ-001: محاسبه اقساط سررسیدگذشته و شاخص روزهای گذشته از موعد
* **الگوی EARS:** Ubiquitous
* **EARS Statement:**
  > The Fineract Delinquency Engine shall calculate Days Past Due (DPD) for every active loan account during the Close-of-Business batch run as the exact calendar difference between the current business date and the due date of the oldest unpaid overdue installment, maintaining the aggregate sum of overdue principal, interest, fees, and penalties in `m_loan_arrears_aging`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  شاخص DPD (تعداد روزهای سپری‌شده از سررسید) بنیادی‌ترین سنجه سنجش سلامت پرتفوی اعتباری است. موتور محاسبه معوقات فاینراکت در انتهای هر روز کاری (COB)، با اجرای جاب دسته‌ای، تمامی اقساط پرداخت‌نشده‌ای را که تاریخ سررسید آن‌ها قبل از تاریخ جاری کسب‌وکار است شناسایی می‌کند. کهنه‌ترین قسط معوق مبنای محاسبه DPD کل پرونده قرار گرفته و مبالغ معوق اصل، سود، کارمزد و جریمه در جدول `m_loan_arrears_aging` تفکیک و تجمیع می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an active loan account has all historical installments fully settled or waived, then the Fineract Delinquency Engine shall set DPD to zero and reset total_overdue_derived to zero.`
  * `If the days past due are within the product-level graceOnArrearsAgeing window, then the Fineract Delinquency Engine shall not increment arrears aging until the grace period is breached.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/LoanArrearsAgingServiceImpl.java`
  * **متد اجرایی:** `#updateLoanArrearsAgeingDetails(Loan loan)`
  * **کدهای خطا و انوتیشن‌ها:** جاب پردازش پایان روز `UpdateLoanArrearsAgingBusinessStep`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_arrears_aging` (ستون‌های `principal_overdue_derived`, `interest_overdue_derived`, `fee_charges_overdue_derived`, `penalty_charges_overdue_derived`, `total_overdue_derived`, `overdue_since_date_derived`)

---

#### REQ-LOAN-DELINQ-002: دسته‌بندی زمانی مطالبات در سبدهای نکول و بازه‌های سنی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When the Close-of-Business delinquency batch job processes an active loan, the Fineract Delinquency Engine shall match the account's DPD against the configured `DelinquencyRange` items within the product's associated `DelinquencyBucket`, record historical transitions in `m_loan_delinquency_tag_history`, and attach current classification tags to the loan and its delinquent installments.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  جهت تطبیق با استانداردهای نظارتی بانک مرکزی و الزامات کمیته بازل، مطالبات باید در سبدهای زمانی معین (Aging Buckets) نظیر: ۱ تا ۳۰ روز (سررسید گذشته)، ۳۱ تا ۶۰ روز (معوق)، ۶۱ تا ۹۰ روز (سررسید گذشته حاد) و بالای ۹۰ روز (مشکوک‌الوصول) طبقه‌بندی شوند. زیرسیستم نکول فاینراکت با انطباق DPD هر پرونده با بازه‌های تعریف‌شده در `m_delinquency_range`، برچسب‌های متناظر را در جدول تاریخچه برچسب‌ها ثبت کرده و مبنای محاسبه ذخایر مطالبات مشکوک‌الوصول را فراهم می‌سازد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If configured delinquency ranges within a bucket have overlapping age day boundaries, then the Fineract Delinquency Engine shall reject bucket creation and return error code "error.msg.delinquency.bucket.range.overlapping".`
  * `If minAgeDays is greater than maxAgeDays in any range specification, then the Fineract Delinquency Engine shall abort and return error code "error.msg.delinquency.range.invalid.ages".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/delinquency/service/DelinquencyWritePlatformServiceImpl.java`
  * **متد اجرایی:** `#applyDelinquencyTagToLoan(Loan loan, DelinquencyBucket bucket)`
  * **کدهای خطا و انوتیشن‌ها:** `DelinquencyBucketAgesOverlapedException`, `DelinquencyRangeInvalidAgesException`
  * **پایگاه داده و انتیتی‌ها:** جداول `m_delinquency_bucket`, `m_delinquency_range`, `m_delinquency_bucket_mappings`, `m_loan_delinquency_tag_history`

---

#### REQ-LOAN-DELINQ-003: طبقه‌بندی تسهیلات غیرجاری و توقف شناسایی درآمد تعهدی
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While an active loan's DPD exceeds the product-configured `overdueDaysForNPA` limit, the Fineract Loan Engine shall classify the loan as Non-Performing by setting `is_npa = true`, and while marked as NPA, the Fineract Accounting Engine shall halt booking accrued interest to the income statement and reroute accruals to off-balance suspense accounts.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  طبق استانداردهای بین‌المللی حسابداری بانکی (IFRS 9) و دستورالعمل‌های بانک مرکزی، هنگامی که تاخیر تسهیلاتی از حد معینی (معمولاً ۹۰ روز یا مقدار مشخص‌شده در `overdue_days_for_npa`) فراتر رود، تسهیلات به طبقه «غیرجاری» (Non-Performing Asset - NPA) منتقل می‌شود. اثر حیاتی این تغییر وضعیت در سیستم حسابداری فاینراکت، توقف بی‌درنگ شناسایی سود تعهدی در صورت سود و زیان است تا از شناسایی درآمدهای موهوم جلوگیری شود. بازگشت به وضعیت جاری تنها پس از تسویه کامل معوقات صورت می‌گیرد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an account is in NPA status and accountMovesOutOfNpaOnlyOnArrearsCompletion is configured as true, then the Fineract Loan Engine shall not clear the "is_npa" flag upon partial repayments until total_overdue_derived is reduced strictly to zero.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/domain/Loan.java`
  * **متد اجرایی:** `#updateIsNPA(LocalDate businessDate, Long overdueDaysForNPA, Boolean accountMovesOutOfNpaOnlyOnArrearsCompletion)`
  * **کدهای خطا و انوتیشن‌ها:** گام پردازشی `AccrualActivityBusinessStep`, تنظیم حساب‌های انتظامی
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan` (ستون `is_npa`), جدول `m_product_loan` (ستون‌های `overdue_days_for_npa`, `account_moves_out_of_npa_only_on_arrears_completion`)

---

#### REQ-LOAN-DELINQ-004: مکانیزم تعلیق و توقف موقت محاسبه نکول
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While an active loan account is subject to an active `LoanDelinquencyAction` with action `PAUSE` spanning the current business date, the Fineract Delinquency Engine shall freeze DPD calculation and suspend delinquency bucket aging, preserving existing classification tags until an explicit `RESUME` action is executed or the pause duration expires.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  قابلیت تعلیق نکول (Pause Delinquency) امکانی قدرتمند در نسخه 1.15.0 فاینراکت است که به بانک اجازه می‌دهد به دلایل موجه (نظیر بلایای طبیعی، بحران‌های اقتصادی، یا توافقات موردی امهال با مشتری)، پیشروی سن معوقات یک پرونده را به صورت موقت متوقف کند. در طی دوره تعلیق، سیستم در فرآیند پایان روز، DPD را افزایش نمی‌دهد و برچسب‌های سبد معوقه را تغییر نمی‌دهد. به محض فرارسیدن تاریخ خاتمه تعلیق یا ثبت دستور `RESUME`، ارزیابی مجدد آغاز می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a pause delinquency request is submitted with a date range overlapping an existing active pause period on the loan, then the Fineract Delinquency Engine shall reject the command and return error code "error.msg.loan.delinquency.action.pause.period.overlap".`
  * `If the pause start date is set after the pause end date, then the Fineract Delinquency Engine shall reject the payload and return error code "error.msg.loan.delinquency.action.start.date.after.end.date".`
  * `If a resume action is executed on an account that does not possess an active pause action, then the Fineract Delinquency Engine shall reject the call and return error code "error.msg.loan.delinquency.action.resume.without.active.pause".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/delinquency/helper/DelinquencyEffectivePauseHelperImpl.java`
  * **متد اجرایی:** `#isPaused(Long loanId, LocalDate businessDate)` و `DelinquencyActionParseAndValidator#validate()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.delinquency.action.pause.period.overlap`, اینام `DelinquencyAction` (`PAUSE`, `RESUME`)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_delinquency_action` (ستون‌های `loan_id`, `action`, `start_date`, `end_date`), انتیتی `LoanDelinquencyAction`

---

### بخش ۶: استمهال، تجدید ساختار و بازتنظیم اقساط تسهیلات (Loan Restructuring & Rescheduling)

#### REQ-LOAN-RESCHED-001: ثبت درخواست استمهال و اعتبارسنجی شرایط قرارداد
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When a loan reschedule request payload is submitted for an active loan, the Fineract Loan Reschedule Platform Service shall validate that the reschedule start date aligns with future installment boundaries, confirm that the rescheduling reason code exists in `m_code_value`, and persist the request in `m_loan_reschedule_request` with status code 100 (`SUBMITTED_AND_PENDING_APPROVAL`).
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  استمهال (Reschedule) فرایندی است که طی آن به دلیل مشکلات مالی موجه وام‌گیرنده، شرایط اولیه قرارداد تغییر می‌یابد. کاربر درخواست استمهال را با مشخص کردن تاریخ آغاز استمهال، علت موجه استمهال (انتخاب از کدهای `LoanRescheduleReason`)، و نوع تغییرات (افزایش تعداد اقساط، تغییر نرخ سود یا اعمال تنفس) ثبت می‌کند. سیستم پس از اعتبارسنجی اولیه، رکورد را در جدول درخواست‌های استمهال ذخیره کرده و جهت تایید به سطح مدیریتی ارجاع می‌دهد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a reschedule request is submitted for a loan account whose status is not "ACTIVE", then the Fineract Loan Reschedule Service shall reject the request and return error code "error.msg.loan.reschedule.loan.is.not.active".`
  * `If another pending reschedule request already exists for the specified loan account, then the Fineract Loan Reschedule Service shall abort and return error code "error.msg.loan.reschedule.request.already.pending".`
  * `If the reschedule from date is earlier than the loan disbursement date, then the Fineract Loan Reschedule Service shall reject the command and return error code "error.msg.loan.reschedule.from.date.before.disbursement.date".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/rescheduleloan/data/LoanRescheduleRequestDataValidatorImpl.java`
  * **متد اجرایی:** `#validateForCreateAction(JsonCommand command, Loan loan)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('CREATE_RESCHEDULELOAN')")`, `error.msg.loan.reschedule.loan.is.not.active`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_loan_reschedule_request` (ستون‌های `status_enum = 100`, `reschedule_from_date`, `reschedule_reason_cv_id`), انتیتی `LoanRescheduleRequest`

---

#### REQ-LOAN-RESCHED-002: تصویب استمهال با تمدید مدت، تعدیل نرخ سود و دوره تنفس جدید
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a loan reschedule request is in pending approval status, when an authorized checker approves the request, the Fineract Loan Reschedule Platform Service shall archive the prior installment schedule into `m_loan_repayment_schedule_history`, apply the agreed term variations in `m_loan_term_variations`, generate a restructured repayment schedule starting from the reschedule date, and transition the request status to 200 (`APPROVED`).
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  با تایید نهایی درخواست استمهال توسط مدیر مجاز (Checker)، تغییرات قرارداد به مرحله اجرا درمی‌آید. فاینراکت ابتدا رونوشتی کامل از جدول اقساط قبلی را در `m_loan_repayment_schedule_history` جهت حفظ سوابق حسابرسی ذخیره می‌کند. سپس متغیرهای جدید (شامل تمدید تعداد اقساط، تغییر نرخ سود سالانه، یا اعطای دوره تنفس در اصل/سود) را در جدول `m_loan_term_variations` اعمال کرده و جدول بازپرداخت نوینی از تاریخ استمهال تولید می‌نماید تا مشتری بتواند با اقساط تعدیل‌شده به بازپرداخت ادامه دهد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the approved reschedule creates a schedule extending beyond the maximum loan term allowed by the loan product, then the Fineract Loan Reschedule Service shall reject the approval and return error code "error.msg.loan.reschedule.exceeds.max.term".`
  * `If approval is submitted by a user lacking checker authority, then the Fineract Loan Engine shall abort the transaction and return error code "error.msg.authorisation.failed".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/loanaccount/rescheduleloan/service/LoanRescheduleRequestWritePlatformServiceImpl.java`
  * **متد اجرایی:** `#approve(JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('APPROVE_RESCHEDULELOAN')")`, `error.msg.loan.reschedule.exceeds.max.term`
  * **پایگاه داده و انتیتی‌ها:** جداول `m_loan_reschedule_request` (ستون `status_enum = 200`), `m_loan_repayment_schedule_history`, `m_loan_term_variations`, انتیتی `LoanTermVariations`

---

#### REQ-LOAN-RESCHED-003: بازتنظیم سن بدهی و بازاستهلاک در موتور تسهیلات پیش‌رونده
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a progressive loan requires credit restructuring, when an authorized re-aging or re-amortization command is executed, the Fineract Progressive Loan Module shall adjust overdue balances without resetting contractual maturity or recalculate the uniform installment annuity over the remaining term in compliance with the specified `LoanReAmortizationInterestHandlingType`.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در تسهیلات پیش‌رونده (`Progressive Loans`)، دو سازوکار متمایز و پیشرفته برای مدیریت بدهی‌های سررسیدگذشته تعبیه شده است:
  ۱. **بازتنظیم سن بدهی (Loan Re-Aging):** بدون تغییر در سررسید نهایی قرارداد، اقساط معوق تجمیع شده و سن بدهی (DPD) به وضعیت جاری بازنشانی می‌شود تا وام‌گیرنده فرصت تنفس بدون سوختن رتبه اعتباری پیدا کند.
  ۲. **بازاستهلاک (Loan Re-Amortization):** مانده اصل پرداخت‌نشده به همراه سودهای سرمایه‌شده بر روی اقساط باقی‌مانده بازتقسیم شده و اقساط مساوی جدیدی بر مبنای فرمول ارزش فعلی محاسبه می‌گردد.
  این عملیات در ماژول پیش‌رونده بدون تغییر در سوابق اقساط پرداخت‌شده قبلی انجام می‌پذیرد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If re-amortization is requested on a standard cumulative loan that is not configured as progressive, then the Fineract Loan Engine shall reject the operation and return error code "error.msg.loan.re-amortization.only.supported.for.progressive.loans".`
  * `If the re-aging parameters define an effective date prior to the most recent loan transaction date, then the Fineract Loan Engine shall reject the command and return error code "error.msg.loan.re-aging.date.invalid".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-progressive-loan/src/main/java/org/apache/fineract/portfolio/loanaccount/service/ProgressiveLoanModelRecalculationService.java`
  * **متد اجرایی:** `#recalculateProgressiveLoanModel(...)` و `ProgressiveLoanRescheduleRequestDataValidator#validate()`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.loan.re-amortization.only.supported.for.progressive.loans`, اینام `LoanReAmortizationInterestHandlingType`
  * **پایگاه داده و انتیتی‌ها:** جداول `m_loan_reage_parameter`, `m_loan_reamortization_parameter`, انتیتی `LoanReAmortizationParameter`

---

## ۴. کنترل‌های تمامیت داده و حسابداری دفتر کل (Data Integrity & Ledger Accounting Invariants)

1. **انزوای مستأجر و یکتایی شماره حساب (`Multi-Tenancy & Account Uniqueness`):**
   - هر شماره حساب در جدول `m_loan` تحت قید یکتایی `loan_account_no_unique` در سطح اسکیمای مستأجر محافظت می‌شود.
2. **یکپارچگی دوبل اسناد حسابداری (`Double-Entry Accounting Invariant`):**
   - به ازای هر تراکنش مالی (`LoanTransaction`)، مجموع اقلام بدهکار (`Debit`) و بستانکار (`Credit`) ثبت‌شده در جدول `acc_gl_journal_entry` باید دقیقاً برابر باشد:
   $$\sum \text{DebitAmount} = \sum \text{CreditAmount}$$
3. **عدم حذف فیزیکی تراکنش‌ها (`Immutable Financial Audit Trail`):**
   - هیچ تراکنشی از جدول `m_loan_transaction` حذف فیزیکی نمی‌شود؛ اصلاحات منحصراً از طریق معکوس‌سازی و ایجاد رکوردهای جبرانی مدیریت می‌گردند.
