# سند نیازمندی‌های مهندسی معکوس حساب‌های پس‌انداز، سپرده‌های مدت‌دار و مدیریت وجوه در Apache Fineract 1.15.0
## (Tier 2: Savings Accounts, Fixed & Recurring Deposits, Interest Compounding, Dormancy & Amount Holds Specification)

---

## ۱. نمای کلی حوزه، معماری دامنه و ناورداهای بنیادین (Executive Summary & Domain Invariants)

این سند مرجع رسمی، تحلیلی و استخراج‌شده از سورس‌کد **Apache Fineract 1.15.0** جهت پوشش نیازمندی‌های عملکردی و غیرعملکردی حوزه حساب‌های پس‌انداز، سپرده‌های سرمایه‌گذاری مدت‌دار (Fixed Deposits)، سپرده‌های اندوخته دوره‌ای (Recurring Deposits)، موتور محاسبه و اعمال سود مرکب، مسدودی و توثیق وجوه (Amount Holds & Liens) و چرخه حیات حساب‌های راکد و بلاصاحب (Dormancy & Escheatment) در قالب استاندارد بین‌المللی **EARS (Easy Approach to Requirements Syntax)** به صورت دوزبانه (فارسی - انگلیسی) است.

### ارکان معماری و ماژول‌های فعال در این حوزه:
1. **ماژول هسته پس‌انداز (`fineract-savings`):**
   - موجودیت ریشه تجمعی (`SavingsAccount` و زیرکلاس‌های `FixedDepositAccount` و `RecurringDepositAccount`).
   - تعاریف محصولات پس‌انداز و سپرده (`SavingsProduct`, `FixedDepositProduct`, `RecurringDepositProduct`).
   - سرویس‌های پردازش تراکنش‌ها، محاسبات سود دوره‌ای (`SavingsAccountInterestPostingService`, `SavingsAccountPostInterestService`) و جستجوی تراکنش‌ها.
2. **ماژول هسته پایه‌ای (`fineract-core`):**
   - اینام‌ها و ساختارهای داده‌ای سود مرکب (`SavingsCompoundingInterestPeriodType`, `SavingsPostingInterestPeriodType`, `SavingsInterestCalculationType`, `SavingsInterestCalculationDaysInYearType`).
   - بسته محاسبات ریاضی بازه‌های زمانی (`org.apache.fineract.portfolio.savings.domain.interest.*` شامل `PostingPeriod`, `DailyCompoundingPeriod`, `MonthlyCompoundingPeriod`, `QuarterlyCompoundingPeriod`, `BiAnnualCompoundingPeriod`, `AnnualCompoundingPeriod`, `EndOfDayBalance`).
   - ماشین وضعیت حساب‌ها و زیروضعیت‌های مسدودی و رکود (`SavingsAccountStatusType`, `SavingsAccountSubStatusEnum`).
3. **لایه سرویس و هماهنگ‌سازی (`fineract-provider`):**
   - کنترلرهای RESTful در JAX-RS (`SavingsAccountsApiResource`, `SavingsAccountTransactionsApiResource`, `FixedDepositAccountsApiResource`, `RecurringDepositAccountsApiResource`, `DepositAccountOnHoldFundTransactionsApiResource`).
   - سرویس‌های ثبت تغییرات دیتابیس CQRS (`SavingsAccountWritePlatformServiceJpaRepositoryImpl`, `DepositAccountWritePlatformServiceJpaRepositoryImpl`, `SavingsApplicationProcessWritePlatformServiceJpaRepositoryImpl`).
   - اعتبارسنج‌های ساختاری و بیزنسی (`SavingsProductDataValidator`, `SavingsAccountDataValidator`, `DepositProductDataValidator`, `DepositAccountDataValidator`, `SavingsAccountTransactionDataValidator`).
   - جاب‌ها و تسکلت‌های دسته‌ای پایان روز (`UpdateSavingsDormantAccountsTasklet`, `PostInterestForSavingTasklet`).

---

### ناورداهای ریاضی و مالی حاکم بر سیستم (Mathematical & Domain Invariants):

* **معادله مانده در دسترس و قابل برداشت (Available Balance Conservation Law):**
  $$\text{Available Balance} = \text{Ledger Balance} - \text{OnHold Funds} - \text{Savings Hold Amount} - \text{Enforced Minimum Balance} + \text{Overdraft Limit}$$
  در پیاده‌سازی متد `SavingsAccount.getWithdrawableBalance()`، سیستم مانده دفتری (`account_balance_derived`) را ارزیابی نموده و تعهدات وثیقه‌ای و کف قانونی موجودی را کسر می‌نماید.

* **روش محاسبه سود روزشمار (Daily Balance Method):**
  در این متد، سود هر روز تقویمی بر مبنای مانده قطعی پایان روز (End-of-Day Balance) محاسبه می‌شود:
  $$I_{\text{daily}} = \text{Balance}_{\text{EOD}} \times \frac{r_{\text{nominal}}}{\text{DaysInYear}}$$
  $$\text{DaysInYear} \in \{360, 365\}$$
  سود کل دوره تناوب واریز برابر با مجموع سودهای روزانه در بازه زمانی است:
  $$I_{\text{period}} = \sum_{d=1}^{N} I_{\text{daily}}(d)$$

* **روش محاسبه میانگین مانده روزانه (Average Daily Balance Method):**
  در این روش، میانگین موزون مانده‌ها در کل دوره محاسبه شده و سود بر پایه آن تعیین می‌شود:
  $$\overline{B} = \frac{\sum_{i=1}^{k} (B_i \times D_i)}{\sum_{i=1}^{k} D_i}$$
  $$I_{\text{period}} = \overline{B} \times \left( \frac{r_{\text{nominal}}}{\text{DaysInYear}} \right) \times N_{\text{total days}}$$
  که در آن $B_i$ مانده روزانه در بازه $i$ام و $D_i$ تعداد روزهای پایداری آن مانده است.

* **فرمول استهلاک جریمه بستن پیش از موعد سپرده ثابت (Premature Closure Penalty Invariant):**
  $$r_{\text{effective}} = \max\left(0, r_{\text{slab}} - r_{\text{penalty}}\right)$$
  که بر اساس نوع جریمه (`PreClosurePenalInterestOnType`):
  - در حالت `WHOLE_TERM (1)`، نرخ بر کل دوره اسمی تعدیل می‌شود.
  - در حالت `TILL_PREMATURE_WITHDRAWAL (2)`، نرخ بر بازه واقعی سپری‌شده تا تاریخ انصراف با بازبینی اسلب متناظر اعمال می‌گردد.

* **ناوردای تقدم زمانی رکود حساب (Dormancy Timeline Monotonicity Invariant):**
  $$0 < \text{days\_to\_inactive} < \text{days\_to\_dormancy} < \text{days\_to\_escheat}$$
  این قید در کلاس `SavingsProductDataValidator` تضمین می‌کند که یک حساب پیش از ورود به وضعیت رکود (Dormant) الزاماً وارد دوره غیرفعال (Inactive) شده و پیش از انتقال به خزانه‌داری (Escheat) مدت زمان قانونی را در رکود سپری کرده باشد.

---

## ۲. خلاصه ماتریس نیازمندی‌ها (Requirements Index Matrix)

| شناسه نیازمندی | عنوان نیازمندی (فارسی) | الگوی EARS | کلاس و لایه سورس Fineract |
| :--- | :--- | :--- | :--- |
| **REQ-SAV-PROD-001** | اعتبارسنجی ارز چندگانه، ارقام اعشار و نرخ سود اسمی سالانه محصول پس‌انداز | Complex | `SavingsProductDataValidator.java` |
| **REQ-SAV-PROD-002** | متدهای محاسبه سود بر مبنای مانده روزانه و میانگین مانده به همراه سال مبنای مالی | Optional Feature | `MonthlyCompoundingPeriod.java` |
| **REQ-SAV-PROD-003** | بازه‌های تناوب مرکب‌سازی سود و دوره‌های واریز قطعی به حساب | State-Driven | `PostingPeriod.java` |
| **REQ-SAV-PROD-004** | خط‌مشی‌های حداقل مانده الزامی، قفل زمانی برداشت و سقف اضافه برداشت | Complex | `SavingsProductDataValidator.java` |
| **REQ-SAV-DEP-001** | حدود مجاز مدت سپرده‌گذاری، فواصل زمانی و دستورالعمل‌های تسویه در سررسید | Complex | `DepositProductDataValidator.java` |
| **REQ-SAV-DEP-002** | اعمال جریمه شکست نرخ سود و تعدیل پرداختی‌ها در بستن پیش از موعد سپرده ثابت | Event-Driven | `FixedDepositAccount.java` |
| **REQ-SAV-DEP-003** | تولید خودکار جدول اقساط اجباری دوره در حساب‌های سپرده اندوخته اقساطی | Complex | `DepositAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-DEP-004** | تخصیص پیش‌پرداخت به اقساط آتی و پایش تعهدات معوق در سپرده‌های اندوخته | Optional Feature | `RecurringDepositAccount.java` |
| **REQ-SAV-LIFE-001** | ثبت و اعتبارسنجی تقاضای افتتاح حساب در وضعیت در انتظار بررسی | Event-Driven | `SavingsApplicationProcessWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-LIFE-002** | تصویب، ابطال تصویب، رد تقاضا و انصراف متقاضی در پرونده پس‌انداز | Complex | `SavingsApplicationProcessWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-LIFE-003** | فعال‌سازی حساب پس‌انداز با تسویه واریز اولیه و تعیین موعد قفل زمانی | Complex | `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-LIFE-004** | بستن عادی حساب پس‌انداز و الزام صفر بودن مانده دفتری | State-Driven | `SavingsAccount.java` |
| **REQ-SAV-LIFE-005** | ماشین وضعیت انسداد عملیاتی و محدودیت تراکنش‌های بدهکار و بستانکار | State-Driven | `SavingsAccount.java` |
| **REQ-SAV-TXN-001** | پردازش تراکنش واریز نقدی و انتقالی با ثبت قطعی در دفتر کل | Event-Driven | `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-TXN-002** | پردازش تراکنش برداشت وجه، اعتبارسنجی مانده در دسترس و کسر کارمزد برداشت | Complex | `SavingsAccount.java` |
| **REQ-SAV-TXN-003** | موتور محاسبه خودکار سود دوره‌ای، کسر مالیات تکلیفی و سرمایه‌گذاری سود | Ubiquitous | `SavingsAccount.java` |
| **REQ-SAV-TXN-004** | ابطال و معکوس‌سازی تراکنش‌ها با بازسازی مانده‌های تاریخی و اسناد معکوس | Event-Driven | `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-HOLD-001** | اعمال مسدودی و توثیق وجه جهت ضمانت تسهیلات و احکام حقوقی | Event-Driven | `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-HOLD-002** | رفع توثیق و آزادسازی وجوه مسدودشده با بازگشت آنی به مانده در دسترس | Event-Driven | `SavingsAccountWritePlatformServiceJpaRepositoryImpl.java` |
| **REQ-SAV-HOLD-003** | کنترل سقف مجاز وثیقه‌گذاری و منع تعارض اضافه برداشت با توثیق سپرده | Complex | `SavingsAccountTransactionDataValidator.java` |
| **REQ-SAV-DORM-001** | شناسایی سیستماتیک حساب‌های راکد، تغییر به وضعیت غیرفعال و کسر کارمزد عدم فعالیت | Event-Driven | `UpdateSavingsDormantAccountsTasklet.java` |
| **REQ-SAV-DORM-002** | گذار خودکار به وضعیت خوابیده (Dormant) و انسداد برداشت‌های سامانه‌ای | State-Driven | `UpdateSavingsDormantAccountsTasklet.java` |
| **REQ-SAV-DORM-003** | سلب مالکیت، واریز مانده به سرفصل خزانه‌داری دولت و مختومه کردن پرونده | Complex | `SavingsAccount.java` |
| **REQ-SAV-DORM-004** | احراز هویت مجدد، رفع انسداد و خروج خودکار از رکود با تراکنش مشتری | Complex | `SavingsAccount.java` |

---

## ۳. کاتالوگ تفصیلی کارت‌های نیازمندی به تفکیک حوزه‌ها

### بخش ۱: پیکربندی محصول پس‌انداز و ناورداهای خط‌مشی (Savings Product Configuration & Policy Invariants)

#### REQ-SAV-PROD-001: اعتبارسنجی ارز چندگانه، ارقام اعشار و نرخ سود اسمی سالانه محصول پس‌انداز
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While defining or modifying a savings product, when a product configuration payload is submitted, the Fineract Savings Engine shall validate that the currency code conforms to ISO 4217, the digitsAfterDecimal is within the closed range `[0, 6]`, the nominalAnnualInterestRate is greater than or equal to zero, and the shortName does not exceed 4 characters in length.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  هنگام تعریف یا ویرایش محصول حساب پس‌انداز در سامانه فاینراکت، مدیر سیستم پارامترهای پایه‌ای مالی نظیر نام محصول، شناسه کوتاه (حداکثر ۴ نویسه)، کد ارز سه‌حرفی مطابق استاندارد ISO 4217، تعداد ارقام اعشار مجاز (بین ۰ تا ۶) و نرخ سود اسمی سالانه را تعیین می‌کند. موتور پس‌انداز فاینراکت باید صحت تمامی این فیلدها را به دقت ارزیابی نموده و از ذخیره‌سازی داده‌های نامعتبر، نرخ سود منفی یا کدهای ارزی ناشناخته جلوگیری به عمل آورد. این کنترل پایه‌ای ضامن صحت محاسبات حسابداری و یکپارچگی ارزی در سطح دفاتر کل است.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the currencyCode parameter is missing or blank, then the Fineract Savings Engine shall reject the configuration with error code "validation.msg.savingsproduct.currencyCode.cannot.be.empty".`
  * `If digitsAfterDecimal is not within the range 0 to 6, then the Fineract Savings Engine shall reject the configuration with error code "validation.msg.savingsproduct.digitsAfterDecimal.is.not.within.expected.range".`
  * `If nominalAnnualInterestRate is negative or null, then the Fineract Savings Engine shall abort creation with error code "validation.msg.savingsproduct.nominalAnnualInterestRate.cannot.be.blank".`
  * `If shortName exceeds 4 characters in length, then the Fineract Savings Engine shall reject the setup with error code "validation.msg.savingsproduct.shortName.exceeds.max.length".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/data/SavingsProductDataValidator.java`
  * **متد اجرایی:** `#validateForCreate(String json)` و `#validateForUpdate(String json, SavingsProduct product)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('CREATE_SAVINGS_PRODUCT')")`, `validation.msg.savingsproduct.currencyCode.cannot.be.empty`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_product` (ستون‌های `currency_code`, `currency_digits`, `nominal_annual_interest_rate`, `short_name`), کلاس `@Entity SavingsProduct`

---

#### REQ-SAV-PROD-002: متدهای محاسبه سود بر مبنای مانده روزانه و میانگین مانده به همراه سال مبنای مالی
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where a savings product is configured with `SavingsInterestCalculationType.DAILY_BALANCE`, the Fineract Savings Interest Engine shall compute daily accrued interest based on the finalized End-of-Day ledger balance for each respective calendar day, whereas where configured with `SavingsInterestCalculationType.AVERAGE_DAILY_BALANCE`, the Fineract Savings Interest Engine shall compute the arithmetic mean of daily balances across each compounding period and calculate interest on that periodic average balance using either a 360-day or 365-day statutory annual convention.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  بانک‌ها و مؤسسات مالی بر حسب نوع محصول سپرده از دو استراتژی محاسباتی استاندارد برای تعیین سود استفاده می‌کنند:
  ۱. **روش مانده روزانه (Daily Balance):** در این روش سود هر روز مستقلاً بر روی مانده پایانی همان روز ($Balance_{\text{EOD}}$) ضربدر نرخ روزشمار ($\frac{r}{360}$ یا $\frac{r}{365}$) محاسبه شده و در پایان دوره مجموع سودهای روزانه با هم جمع می‌شوند.
  ۲. **روش میانگین مانده روزانه (Average Daily Balance):** در این مدل، کل مانده‌های روزانه در طول دوره تجمیع شده و بر تعداد روزهای دوره تقسیم می‌شود تا مانده متوسط روزانه به دست آید؛ سپس سود یکجا بر روی این میانگین مانده محاسبه می‌شود.
  سامانه فاینراکت موظف است بر پایه فیلد `interest_calculation_type_enum` و `interest_calculation_days_in_year_type_enum` استراتژی محاسباتی دقیق را در موتور سود فعال سازد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If interestCalculationType is not equal to 1 (DAILY_BALANCE) or 2 (AVERAGE_DAILY_BALANCE), then the Fineract Savings Engine shall reject the setup with error code "validation.msg.savingsproduct.interestCalculationType.is.not.within.expected.range".`
  * `If interestCalculationDaysInYearType is not equal to 360 or 365, then the Fineract Savings Engine shall reject the setup with error code "validation.msg.savingsproduct.interestCalculationDaysInYearType.is.not.within.expected.range".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-core/src/main/java/org/apache/fineract/portfolio/savings/domain/interest/MonthlyCompoundingPeriod.java` و `DailyCompoundingPeriod.java`
  * **متد اجرایی:** `#calculateInterest(...)` و `MonthlyCompoundingPeriod#calculateUsingAverageDailyBalanceMethod(...)`
  * **کدهای خطا و انوتیشن‌ها:** اینام `SavingsInterestCalculationType`, اینام `SavingsInterestCalculationDaysInYearType`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_product` (ستون‌های `interest_calculation_type_enum`, `interest_calculation_days_in_year_type_enum`), انتیتی `SavingsProduct`

---

#### REQ-SAV-PROD-003: بازه‌های تناوب مرکب‌سازی سود و دوره‌های واریز قطعی به حساب
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While evaluating interest accrual for an active savings account, the Fineract Savings Interest Engine shall accrue and compound unposted interest at the end of each configured compounding interval (Daily, Monthly, Quarterly, Semi-Annual, Annual), and shall capitalize and post cumulative accrued interest into the account ledger balance only upon reaching the configured posting frequency boundary (Daily, Monthly, Quarterly, Biannual, Annual, or Anniversary-based cycles).
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در نظام بانکداری، تفکیک شفافی میان «فاصله مرکب‌شدن سود» (Compounding Period) و «فاصله واریز قطعی سود به حساب» (Posting Period) وجود دارد. برای نمونه، در حسابی با واریز فصلی (Quarterly Posting) و مرکب‌سازی ماهانه (Monthly Compounding)، در پایان هر ماه سود تعهدی محاسبه‌شده به مبنای سرمایه دوره بعد افزوده می‌شود اما وجه واقعی سود تا پایان فصل در سرخط مانده دفتری مشتری ثبت نمی‌شود. سامانه فاینراکت از کلاس‌های تخصصی هندسه زمانی نظیر `PostingPeriod` و `CompoundingPeriod` جهت تفکیک دقیق مرزهای تعهدی و مرکب‌سازی استفاده می‌کند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If interestCompoundingPeriodType is not in the set {1 (DAILY), 4 (MONTHLY), 5 (QUARTERLY), 6 (BI_ANNUAL), 7 (ANNUAL)}, then the Fineract Savings Engine shall reject the configuration with error code "validation.msg.savingsproduct.interestCompoundingPeriodType.is.not.within.expected.range".`
  * `If interestPostingPeriodType is invalid or missing, then the Fineract Savings Engine shall reject the product payload with error code "validation.msg.savingsproduct.interestPostingPeriodType.is.not.within.expected.range".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-core/src/main/java/org/apache/fineract/portfolio/savings/domain/interest/PostingPeriod.java`
  * **متد اجرایی:** `#calculateInterest(CompoundInterestValues compoundInterestValues)`
  * **کدهای خطا و انوتیشن‌ها:** اینام `SavingsCompoundingInterestPeriodType`, اینام `SavingsPostingInterestPeriodType`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_product` (ستون‌های `interest_compounding_period_enum`, `interest_posting_period_enum`), جدول `m_savings_account`

---

#### REQ-SAV-PROD-004: خط‌مشی‌های حداقل مانده الزامی، قفل زمانی برداشت و سقف اضافه برداشت
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While configuring or maintaining a savings product, when minimum balance rules, lock-in period frequencies, or overdraft facilities are defined, the Fineract Savings Engine shall validate that lockinPeriodFrequency is paired with a valid frequency unit (Days, Weeks, Months, Years), enforce that overdraftLimit is greater than or equal to zero, and verify that overdraftLimit does not exceed maxAllowedLienLimit when account lien is simultaneously enabled.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  محصولات پس‌انداز می‌توانند قواعد انضباطی مالی و تسهیلات اعتباری را تعریف کنند:
  ۱. **دوره قفل‌شدگی (Lock-in Period):** مدت زمانی پس از افتتاح که طی آن مشتری مجاز به هیچ‌گونه برداشت وجهی نیست.
  ۲. **حداقل مانده الزامی (Minimum Required Balance):** کفی از موجودی که برای استمرار فعالیت حساب الزامی است.
  ۳. **اضافه برداشت (Overdraft Facility):** سقف مجاز بدهکار شدن حساب پس‌انداز به همراه نرخ سود اضافه برداشت سالانه.
  ۴. **تداخل وثیقه و اضافه برداشت:** چنانچه روی محصولی توثیق سپرده (Lien) فعال باشد، سقف اضافه برداشت نباید از سقف توثیق مجاز فراتر رود تا از ایجاد ریسک اعتباری کنترل‌نشده برای بانک جلوگیری گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If lockinPeriodFrequency is provided without lockinPeriodFrequencyType, then the Fineract Savings Engine shall reject the request with error code "validation.msg.savingsproduct.lockinPeriodFrequencyType.cannot.be.blank".`
  * `If overdraftLimit is less than zero, then the Fineract Savings Engine shall abort with error code "validation.msg.savingsproduct.overdraftLimit.must.be.zero.or.positive".`
  * `If lienAllowed is true and allowOverdraft is true and overdraftLimit exceeds maxAllowedLienLimit, then the Fineract Savings Engine shall fail with error code "Overdraft.limit.can.not.be.greater.than.lien.limit".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/data/SavingsProductDataValidator.java`
  * **متد اجرایی:** `#validateOverdraftParams(...)` و `#validateLienParams(...)`
  * **کدهای خطا و انوتیشن‌ها:** `Overdraft.limit.can.not.be.greater.than.lien.limit`, `validation.msg.savingsproduct.minRequiredOpeningBalance.must.be.zero.or.positive`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_product` (ستون‌های `lockin_period_frequency`, `allow_overdraft`, `overdraft_limit`, `is_lien_allowed`, `max_allowed_lien_limit`, `enforce_min_required_balance`)

---

### بخش ۲: محصولات و حساب‌های سپرده سرمایه‌گذاری مدت‌دار و اندوخته اقساطی (Fixed & Recurring Deposits)

#### REQ-SAV-DEP-001: حدود مجاز مدت سپرده‌گذاری، فواصل زمانی و دستورالعمل‌های تسویه در سررسید
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While validating a Fixed Deposit product or application, when tenure and closure parameters are defined, the Fineract Deposit Subsystem shall validate that minDepositTerm is strictly greater than zero, maxDepositTerm is greater than or equal to minDepositTerm, depositAmount is within the closed interval `[depositMinAmount, depositMaxAmount]`, and upon reaching the configured maturity date, the Fineract Deposit Subsystem shall execute the designated maturity closure instruction (Withdraw Deposit, Transfer to Linked Savings Account, Reinvest Principal and Interest, or Reinvest Principal Only).
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  سپرده‌های سرمایه‌گذاری مدت‌دار (Fixed Deposit) نیازمند انضباط زمانی و مبلغی دقیق هستند. در تعریف محصول یا قرارداد حساب، حداقل دوره تودیع وجه، حداکثر دوره مجاز و مضارب زمانی مجاز (روز، هفته، ماه، سال) تعیین می‌گردد. همچنین در زمان افتتاح حساب، متقاضی نوع تسویه در سررسید (`DepositAccountOnClosureType`) را انتخاب می‌کند:
  - دریافت نقدی اصل و سود (`WITHDRAW_DEPOSIT - 100`)
  - انتقال به حساب پس‌انداز متصل (`TRANSFER_TO_SAVINGS - 200`)
  - تمدید خودکار اصل و سود به عنوان سپرده مدت‌دار جدید (`REINVEST_PRINCIPAL_AND_INTEREST - 300`)
  - تمدید فقط اصل و واریز سود به حساب جاری/پس‌انداز (`REINVEST_PRINCIPAL_ONLY - 400`).
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If minDepositTerm is null or less than or equal to zero, then the Fineract Deposit Subsystem shall reject the command with error code "validation.msg.fixeddepositproduct.minDepositTerm.must.be.greater.than.zero".`
  * `If maxDepositTerm is less than minDepositTerm, then the Fineract Deposit Subsystem shall reject the command with error code "validation.msg.fixeddepositproduct.maxDepositTerm.cannot.be.less.than.minDepositTerm".`
  * `If depositAmount is outside the range defined by depositMinAmount and depositMaxAmount, then the Fineract Deposit Subsystem shall reject the account opening with error code "validation.msg.fixeddepositaccount.depositAmount.is.not.within.min.max.range".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/data/DepositProductDataValidator.java` و `DepositAccountDataValidator.java`
  * **متد اجرایی:** `#validateDepositTermDeatilForCreate(...)` و `DepositAccountTermAndPreClosure#update(...)`
  * **کدهای خطا و انوتیشن‌ها:** اینام `DepositAccountOnClosureType`, `validation.msg.fixeddepositproduct.minDepositTerm.must.be.greater.than.zero`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_deposit_account_term_and_preclosure` (ستون‌های `min_deposit_term`, `max_deposit_term`, `on_account_closure_enum`, `maturity_date`, `maturity_amount`), کلاس `@Entity DepositAccountTermAndPreClosure`

---

#### REQ-SAV-DEP-002: اعمال جریمه شکست نرخ سود و تعدیل پرداختی‌ها در بستن پیش از موعد سپرده ثابت
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When a customer requests premature closure of a fixed deposit account prior to its contractual maturity date, the Fineract Deposit Subsystem shall evaluate pre_closure_penal_applicable, reduce the applicable interest rate by pre_closure_penal_interest according to whether the penalty is assessed on the whole contractual term or strictly till the premature closure date, transition the account status to `PRE_MATURE_CLOSURE` (700), and recover any excess previously posted interest from the final principal payout.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  چنانچه سپرده‌گذار پیش از سررسید نهایی تقاضای فسخ و بستن سپرده مدت‌دار را نماید، بانک متحمل ریسک نقدینگی و عدم تطابق سررسید دارایی-بدهی (ALM) می‌شود. لذا طبق قرارداد:
  ۱. نرخ سود متناظر بر اساس جدول نرخ‌های اسلب (`m_savings_account_interest_rate_chart`) مجدداً ارزیابی می‌شود (در حالت `TILL_PREMATURE_WITHDRAWAL` اسلب متناظر با مدت واقعی ماندگاری سپرده ملاک قرار می‌گیرد).
  ۲. جریمه شکست سود (`pre_closure_penal_interest`) از نرخ اسلب کسر می‌شود ($r_{\text{effective}} = \max(0, r_{\text{slab}} - r_{\text{penalty}})$).
  ۳. کل سودهای پرداخت‌شده قبلی بر اساس نرخ جدید بازمحاسبه شده و مابه‌التفاوت اضافی واریز شده از اصل پرداختی نهایی کسر می‌گردد.
  ۴. وضعیت حساب به مقدار عددی ۷۰۰ (`PRE_MATURE_CLOSURE`) تغییر می‌یابد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If preClosurePenalApplicable is true while preClosurePenalInterest is blank or null, then the Fineract Deposit Subsystem shall reject the configuration with error code "validation.msg.fixeddepositproduct.preClosurePenalInterest.cannot.be.blank".`
  * `If preClosurePenalInterestOnType is missing when penal interest is applicable, then the Fineract Deposit Subsystem shall reject the command with error code "validation.msg.fixeddepositproduct.preClosurePenalInterestOnTypeId.cannot.be.blank".`
  * `If a premature closure is attempted on an account that does not have an active term contract, then the Fineract Deposit Subsystem shall raise an exception with error code "can.not.close.as.premature".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/domain/FixedDepositAccount.java`
  * **متد اجرایی:** `#getEffectiveInterestRateAsFraction(MathContext mc, LocalDate interestPostingUpToDate, boolean isPreMatureClosure)` و `DepositAccountDomainServiceJpa#handleFDAccountPreMatureClosure(...)`
  * **کدهای خطا و انوتیشن‌ها:** اینام `PreClosurePenalInterestOnType`, `SavingsAccountStatusType.PRE_MATURE_CLOSURE` (کد ۷۰۰)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_deposit_account_term_and_preclosure` (ستون‌های `pre_closure_penal_applicable`, `pre_closure_penal_interest`, `pre_closure_penal_interest_on_enum`), جدول `m_savings_account` (ستون `status_enum`)

---

#### REQ-SAV-DEP-003: تولید خودکار جدول اقساط اجباری دوره در حساب‌های سپرده اندوخته اقساطی
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While activating a Recurring Deposit (RD) account where mandatory periodic deposit is configured, when the activation command is processed, the Fineract Deposit Subsystem shall generate a complete installment schedule in table "m_mandatory_savings_schedule", computing sequence numbers, from-dates, due-dates, and mandatory installment deposit amounts across the entire contractual tenure.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  سپرده‌های اندوخته دوره‌ای (Recurring Deposit) قراردادهایی هستند که در آنها مشتری متعهد می‌شود ماهانه یا در فواصل منظم معین، مبلغی ثابت را به حساب واریز نماید تا در پایان دوره کل مبالغ تودیع‌شده به همراه سودهای متعلقه را دریافت دارد. در لحظه فعال‌سازی حساب، موتور سپرده فاینراکت موظف است جدول اقساط اجباری را در جدول `m_mandatory_savings_schedule` ایجاد کند. هر سطر از جدول دارای شناسه قسط، تاریخ آغاز دوره، سررسید واریز (`duedate`) و مبلغ تعهد (`deposit_amount`) بوده و وضعیت تسویه آن به صورت پیوسته پایش می‌شود.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If mandatoryDepositAmount is missing or less than or equal to zero during RD application, then the Fineract Deposit Subsystem shall reject the creation with error code "validation.msg.recurringdepositaccount.mandatoryRecommendedDepositAmount.cannot.be.blank".`
  * `If recurringFrequency is missing when schedule generation is triggered, then the Fineract Deposit Subsystem shall abort with error code "validation.msg.recurringdepositaccount.recurringFrequency.cannot.be.blank".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/domain/RecurringDepositAccount.java` و `RecurringDepositScheduleInstallment.java`
  * **متد اجرایی:** `DepositAccountWritePlatformServiceJpaRepositoryImpl#activateRDAccount(Long savingsId, JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `validation.msg.recurringdepositaccount.mandatoryRecommendedDepositAmount.cannot.be.blank`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_mandatory_savings_schedule` (ستون‌های `installment`, `fromdate`, `duedate`, `deposit_amount`, `completed_derived`), انتیتی `@Entity RecurringDepositScheduleInstallment`

---

#### REQ-SAV-DEP-004: تخصیص پیش‌پرداخت به اقساط آتی و پایش تعهدات معوق در سپرده‌های اندوخته
* **الگوی EARS:** Optional Feature
* **EARS Statement:**
  > Where `adjustAdvanceTowardsFuturePayments` is enabled on a Recurring Deposit product, when a customer deposit exceeds the outstanding amount of the current installment, the Fineract Deposit Subsystem shall allocate the surplus amount sequentially to upcoming installments in the schedule and record the paid amount in `total_paid_in_advance_derived` while marking obligations as fulfilled.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در سپرده‌های اندوخته اقساطی، مشتری ممکن است در یک نوبت مبلغی بیش از تعهد قسط جاری واریز کند. چنانچه قابلیت تنظیم پیش‌پرداخت برای اقساط آتی فعال باشد، موتور سپرده مبلغ مازاد را به ترتیب زمانی به اقساط بعدی تخصیص داده و فیلد `total_paid_in_advance_derived` آن اقساط را افزایش می‌دهد. در مقابل، چنانچه قسطی در سررسید مقرر پرداخت نشود، سیستم آن قسط را معوق شناخته و در صورت تعریف کارمزد دیرکرد، جریمه دیرکرد اندوخته را بر حساب اعمال می‌نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a withdrawal is attempted on a recurring deposit account where allowWithdrawal is false, then the Fineract Deposit Subsystem shall reject the transaction with error code "error.msg.recurringdepositaccount.withdrawals.not.allowed".`
  * `If depositAmount submitted is less than the minimum installment threshold, then the Fineract Deposit Subsystem shall reject the deposit with error code "error.msg.recurringdepositaccount.transaction.amount.less.than.mandatory.deposit".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/domain/RecurringDepositAccount.java`
  * **متد اجرایی:** `DepositAccountWritePlatformServiceJpaRepositoryImpl#depositToRDAccount(Long savingsId, JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `error.msg.recurringdepositaccount.withdrawals.not.allowed`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_mandatory_savings_schedule` (ستون‌های `deposit_amount_completed_derived`, `total_paid_in_advance_derived`, `total_paid_late_derived`), انتیتی `RecurringDepositAccount`

---

### بخش ۳: چرخه حیات حساب پس‌انداز و ماشین وضعیت رسمی (Savings Account Lifecycle & State Machine)

#### REQ-SAV-LIFE-001: ثبت و اعتبارسنجی تقاضای افتتاح حساب در وضعیت در انتظار بررسی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized staff member submits a savings application payload for an active client or group, the Fineract Savings Application Engine shall validate all product policy parameters, generate a unique account number, persist the account with status `SUBMITTED_AND_PENDING_APPROVAL` (100) and sub-status `NONE` (0), and record submittedon_date and submittedon_userid audit metadata.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  نقطه آغاز چرخه حیات حساب پس‌انداز، ثبت تقاضای افتتاح حساب برای مشتری حقیقی یا گروه است. متقاضی باید دارای پرونده مشتری فعال در شعبه باشد. موتور پس‌انداز صحت اطلاعات هویتی، محصول انتخابی، تنظیمات سود و کارمزدهای پیوست‌شده را اعتبارسنجی می‌کند. پس از احراز شروط، شماره حساب یکتای پس‌انداز (تولیدشده توسط ژنراتور شماره حساب) به پرونده منتسب شده و وضعیت اولیه حساب دقیقا بر روی کد ۱۰۰ (`SUBMITTED_AND_PENDING_APPROVAL`) و زیروضعیت بر روی کد ۰ (`NONE`) ثبت می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the associated client is not in ACTIVE state, then the Fineract Savings Application Engine shall reject the application with error code "error.msg.savingsaccount.client.not.active".`
  * `If submittedOnDate is in the future relative to the tenant's current business date, then the Fineract Savings Application Engine shall reject the request with error code "validation.msg.savingsaccount.submittedOnDate.cannot.be.in.the.future".`
  * `If submittedOnDate is before the client's official activation date, then the Fineract Savings Application Engine shall reject the creation with error code "validation.msg.savingsaccount.submittedOnDate.cannot.be.before.client.activation.date".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsApplicationProcessWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#submitApplication(JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('CREATE_SAVINGSACCOUNT')")`, `validation.msg.savingsaccount.submittedOnDate.cannot.be.in.the.future`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `account_no`, `status_enum`, `sub_status_enum`, `submittedon_date`, `submittedon_userid`), انتیتی `SavingsAccount`

---

#### REQ-SAV-LIFE-002: تصویب، ابطال تصویب، رد تقاضا و انصراف متقاضی در پرونده پس‌انداز
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a savings account application is in status `SUBMITTED_AND_PENDING_APPROVAL` (100), when an approval, rejection, or applicant withdrawal command is executed, the Fineract Savings Engine shall transition the account status to `APPROVED` (200), `REJECTED` (500), or `WITHDRAWN_BY_APPLICANT` (400) respectively, whereas while in status `APPROVED` (200), when an undoApproval command is executed, the Fineract Savings Engine shall revert the account status back to `SUBMITTED_AND_PENDING_APPROVAL` (100) and clear approval audit metadata.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  پیش از فعال‌سازی حساب و پذیرش تراکنش، پرونده در چرخه بررسی و تصویب قرار می‌گیرد:
  ۱. **تصویب (Approve):** کاربر دارای مجوز، تقاضا را بررسی و با تاریخ مصوب (`approvedon_date`) تایید می‌کند؛ وضعیت به ۲۰۰ (`APPROVED`) تغییر می‌یابد.
  ۲. **لغو تصویب (Undo Approval):** چنانچه تصویب به اشتباه صادر شده باشد، تا پیش از فعال‌سازی می‌توان آن را ملغی نمود؛ حساب به وضعیت ۱۰۰ بازگشته و فراداده‌های تصویب پاک می‌شوند.
  ۳. **رد تقاضا (Reject):** در صورت عدم احراز شرایط، تقاضا با وضعیت ۵۰۰ مختومه می‌گردد.
  ۴. **انصراف متقاضی (Withdraw by Applicant):** انصراف مشتری با وضعیت ۴۰۰ ثبت و پرونده بسته می‌شود.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an approval command is submitted for an account that is not in SUBMITTED_AND_PENDING_APPROVAL state, then the Fineract Savings Engine shall reject the command with error code "not.in.submittedandpendingapproval.state".`
  * `If approvedOnDate is before submittedOnDate, then the Fineract Savings Engine shall reject the approval with error code "cannot.be.before.submittal.date".`
  * `If approvedOnDate is after the current business date, then the Fineract Savings Engine shall fail with error code "cannot.be.a.future.date".`
  * `If undoApproval is executed on an account that is not in APPROVED state, then the Fineract Savings Engine shall throw an exception with error code "not.in.approved.state".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#approveApplication(...)` و `#undoApplicationApproval()`
  * **کدهای خطا و انوتیشن‌ها:** `not.in.submittedandpendingapproval.state`, `cannot.be.before.submittal.date`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `status_enum`, `approvedon_date`, `approvedon_userid`, `rejectedon_date`, `withdrawnon_date`)

---

#### REQ-SAV-LIFE-003: فعال‌سازی حساب پس‌انداز با تسویه واریز اولیه و تعیین موعد قفل زمانی
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a savings account is in status `APPROVED` (200), when an activate command is processed with an activation date on or after the approval date and on or after client activation, the Fineract Savings Engine shall transition the account status to `ACTIVE` (300), calculate the locked-in period end date in `lockedin_until_date_derived`, and if a minimum opening balance is required, shall concurrently execute the initial deposit transaction.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  با صدور دستور فعال‌سازی (`activate`)، حساب وارد فاز عملیاتی بانکی می‌شود. موتور پس‌انداز بررسی می‌کند که حساب الزاماً مصوب بوده و تاریخ فعال‌سازی قبل از تاریخ تصویب یا تاریخ فعال‌سازی مشتری نباشد. در صورت وجود شرط حداقل موجودی افتتاحیه (`minRequiredOpeningBalance`) یا مبلغ واریز اولیه اعلام‌شده در تقاضا، سیستم به طور خودکار تراکنش واریز نقدی (`SavingsAccountTransactionType.DEPOSIT - 1`) را ثبت کرده و مانده دفتری را افزایش می‌دهد. همچنین تاریخ پایان دوره قفل‌شدگی حساب بر مبنای تناوب‌های روز، هفته، ماه یا سال محاسبه و در ستون `lockedin_until_date_derived` ذخیره می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an activate command is executed for an account that is not in APPROVED state, then the Fineract Savings Engine shall reject the activation with error code "not.in.approved.state".`
  * `If activatedOnDate is before approvedOnDate, then the Fineract Savings Engine shall reject the activation with error code "command.activatedOnDate.cannot.be.before.approval.date".`
  * `If activatedOnDate is before the client's activation date, then the Fineract Savings Engine shall fail with error code "cannot.be.before.client.activation.date".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#activate(Long savingsId, JsonCommand command)` و `SavingsAccount#activate(...)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('ACTIVATE_SAVINGSACCOUNT')")`, `not.in.approved.state`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `status_enum`, `activatedon_date`, `activatedon_userid`, `lockedin_until_date_derived`)

---

#### REQ-SAV-LIFE-004: بستن عادی حساب پس‌انداز و الزام صفر بودن مانده دفتری
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While a savings account is in status `ACTIVE` (300), when a close command is submitted with a closure date on or after the activation date and on or after the last transaction date, the Fineract Savings Engine shall transition the account status to `CLOSED` (600) only if the final ledger balance is exactly zero.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  بستن اختیاری یا نهایی حساب پس‌انداز زمانی مجاز است که حساب در وضعیت فعال بوده و تمامی تعهدات مالی طرفین تسویه شده باشد. طبق قوانین بانکداری، حساب پس‌انداز نمی‌تواند با مانده مثبت (طلب مشتری) یا مانده منفی (اضافه برداشت و بدهی به بانک) بسته شود. کاربر موظف است پیش از ارسال دستور بستن، مانده حساب را از طریق برداشت نهایی یا واریز تسویه به صفر برساند. تاریخ بستن نمی‌تواند پیش از تاریخ فعال‌سازی یا قبل از تاریخ آخرین تراکنش ثبت‌شده باشد. پس از بسته شدن، هیچ‌گونه تراکنش مالی بر روی حساب مجاز نخواهد بود.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a close command is submitted on an account that is not ACTIVE, then the Fineract Savings Engine shall reject the request with error code "not.in.active.state".`
  * `If closedOnDate is before activatedOnDate, then the Fineract Savings Engine shall reject the command with error code "must.be.after.activation.date".`
  * `If closedOnDate is before the last transaction date, then the Fineract Savings Engine shall reject the command with error code "must.be.after.last.transaction.date".`
  * `If the ledger balance of the account is not exactly zero (balance != 0.0), then the Fineract Savings Engine shall block closure with error code "results.in.balance.not.zero".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#close(AppUser currentUser, JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `results.in.balance.not.zero`, `must.be.after.last.transaction.date`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `status_enum`, `closedon_date`, `closedon_userid`), وضعیت ۶۰۰ (`CLOSED`)

---

#### REQ-SAV-LIFE-005: ماشین وضعیت انسداد عملیاتی و محدودیت تراکنش‌های بدهکار و بستانکار
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While a savings account is in status `ACTIVE` (300), the Fineract Savings Engine shall enforce transaction blocking policies according to `sub_status_enum` such that while set to `BLOCK` (400) all debit and credit operations shall be rejected, while set to `BLOCK_DEBIT` (600) outgoing debits shall be rejected while incoming credits shall be permitted, and while set to `BLOCK_CREDIT` (500) incoming deposits shall be rejected while debit withdrawals shall remain permissible.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  جهت تطبیق با الزامات مبارزه با پولشویی (AML)، دستورات مراجع قضایی و مدیریت ریسک، فاینراکت مکانیزم کنترل دندانه‌ریز زیروضعیت‌ها (`sub_status_enum`) را پیاده‌سازی نموده است:
  ۱. **انسداد کامل (`BLOCK` - کد ۴۰۰):** هرگونه تراکنش مالی (بدهکار یا بستانکار) بر روی حساب ممنوع است.
  ۲. **مسدودی بدهکار (`BLOCK_DEBIT` - کد ۶۰۰):** مشتری حق برداشت وجه، انتقال به بیرون یا پرداخت کارمزد را ندارد، اما واریز وجوه به حساب جهت تسویه تعهدات مجاز است.
  ۳. **مسدودی بستانکار (`BLOCK_CREDIT` - کد ۵۰۰):** واریز به حساب ممنوع است اما مشتری می‌تواند مانده موجود را برداشت نماید.
  انتقال میان زیروضعیت‌ها به صورت هوشمند است؛ مثلا اگر حسابی در مسدودی بدهکار باشد و دستور مسدودی بستانکار دریافت کند، به طور خودکار به انسداد کامل (`BLOCK`) ارتقا می‌یابد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a debit transaction is attempted while sub_status is BLOCK or BLOCK_DEBIT, then the Fineract Savings Engine shall throw a SavingsAccountDebitsBlockedException or SavingsAccountBlockedException.`
  * `If a deposit is attempted while sub_status is BLOCK or BLOCK_CREDIT, then the Fineract Savings Engine shall throw a SavingsAccountCreditsBlockedException or SavingsAccountBlockedException.`
  * `If an unblock command is executed on an account that is not in a blocked state, then the Fineract Savings Engine shall reject the command with error code "not.in.blocked.state".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#block()`, `#unblock()`, `#blockCredits(...)`, `#blockDebits(...)`, `#validateForDebitBlock()`, `#validateForCreditBlock()`
  * **کدهای خطا و انوتیشن‌ها:** `SavingsAccountBlockedException`, `SavingsAccountDebitsBlockedException`, `SavingsAccountCreditsBlockedException`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `sub_status_enum`, `reason_for_block`), اینام `SavingsAccountSubStatusEnum`

---

### بخش ۴: پردازش تراکنش‌ها و عملیات مالی حساب پس‌انداز (Savings Financial Transactions & Operations)

#### REQ-SAV-TXN-001: پردازش تراکنش واریز نقدی و انتقالی با ثبت قطعی در دفتر کل
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized teller or integration system processes a deposit command on an `ACTIVE` savings account whose credit operations are unblocked, the Fineract Savings Engine shall validate that transactionDate is not in the future and not before activationDate, insert a credit transaction of type `DEPOSIT` (1) into table "m_savings_account_transaction", increment account_balance_derived, and trigger the corresponding accounting double-entry journal entries.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  عملیات واریز وجه (نقدی، انتقال حسابی، حواله یا چک) یکی از پرتکرارترین فرآیندهای بانکی است. سیستم بررسی می‌کند که حساب در وضعیت فعال بوده و واریز به آن مسدود نباشد. تاریخ تراکنش نمی‌تواند در آینده یا قبل از تاریخ افتتاح/فعال‌سازی حساب باشد. پس از صحت‌سنجی، رکورد تراکنش در جدول `m_savings_account_transaction` با نوع ۱ (`DEPOSIT`) درج شده، مانده تجمعی دفتری (`account_balance_derived`) بلافاصله به میزان مبلغ واریزی افزایش می‌یابد و اسناد حسابداری دوبل (بدهکار شدن صندوق/بانک و بستانکار شدن سرفصل سپرده مشتری) تولید می‌گردد. همچنین چنانچه حساب در وضعیت غیرفعال یا خوابیده باشد، با این تراکنش خودکار به وضعیت عادی بازمی‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If transactionDate is in the future, then the Fineract Savings Engine shall reject the deposit with error code "error.msg.savingsaccount.transaction.in.the.future".`
  * `If transactionDate is prior to the account activation date, then the Fineract Savings Engine shall reject the deposit with error code "error.msg.savingsaccount.transaction.before.activation.date".`
  * `If the transaction amount is zero or negative, then the Fineract Savings Engine shall reject the command with error code "validation.msg.savingsaccounttransaction.transactionAmount.not.greater.than.zero".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#deposit(Long savingsId, JsonCommand command)` و `SavingsAccount#deposit(...)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('DEPOSIT_SAVINGSACCOUNT')")`, `error.msg.savingsaccount.transaction.in.the.future`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction` (نوع تراکنش ۱), جدول `m_savings_account` (ستون `account_balance_derived`)

---

#### REQ-SAV-TXN-002: پردازش تراکنش برداشت وجه، اعتبارسنجی مانده در دسترس و کسر کارمزد برداشت
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a savings account is in status `ACTIVE` (300) outside of any lock-in period and with debit operations unblocked, when a withdrawal transaction command is submitted, the Fineract Savings Engine shall calculate the Available Balance, verify that the withdrawal amount plus any auto-calculated withdrawal fee does not exceed this available balance, insert a debit transaction of type `WITHDRAWAL` (2), deduct the withdrawal fee, update the running ledger balance, and trigger accounting journal entries.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  برداشت وجه از حساب پس‌انداز مستلزم بررسی‌های سخت‌گیرانه چندگانه است:
  ۱. **دوره قفل‌شدگی:** حساب نباید در بازه قفل زمانی (`lockedin_until_date_derived`) باشد.
  ۲. **کفایت مانده در دسترس:** مبلغ درخواستی به علاوه کارمزد برداشت نباید از فرمول مانده در دسترس فراتر رود:
  $$\text{Debit Amount} + \text{Withdrawal Fee} \le \text{Ledger Balance} - \text{Holds} - \text{Enforced Min Balance} + \text{Overdraft Limit}$$
  ۳. **محاسبه خودکار کارمزد:** در صورت وجود تعرفه کارمزد برداشت، یک تراکنش مجزای کارمزد با نوع ۴ (`WITHDRAWAL_FEE`) همزمان ثبت و از حساب کسر می‌گردد.
  ۴. **به‌روزرسانی مانده:** مانده دفتری کاهش یافته و رکوردهای دفتر کل ثبت می‌شوند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If a withdrawal is attempted during the lock-in period, then the Fineract Savings Engine shall reject the transaction with error code "error.msg.savingsaccount.transaction.withdrawals.blocked.during.lockin.period".`
  * `If the withdrawal amount exceeds the calculated Available Balance, then the Fineract Savings Engine shall throw an InsufficientAccountBalanceException with error code "error.msg.savingsaccount.transaction.insufficient.account.balance".`
  * `If the withdrawal violates the enforced minimum balance, then the Fineract Savings Engine shall throw an InsufficientAccountBalanceException with error code "error.msg.savingsaccount.transaction.insufficient.account.balance.withdraw".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#withdraw(...)`, `#getWithdrawableBalance()`, `#violatesMinRequiredBalance(...)`
  * **کدهای خطا و انوتیشن‌ها:** `InsufficientAccountBalanceException`, `error.msg.savingsaccount.transaction.withdrawals.blocked.during.lockin.period`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction` (انواع ۲ و ۴), جدول `m_savings_account`

---

#### REQ-SAV-TXN-003: موتور محاسبه خودکار سود دوره‌ای، کسر مالیات تکلیفی و سرمایه‌گذاری سود
* **الگوی EARS:** Ubiquitous
* **EARS Statement:**
  > The Fineract Savings Interest Engine shall compute cumulative interest earned across daily balances in each compounding period, subtract applicable withholding tax where configured, and capitalize net interest earned by posting a credit transaction of type `INTEREST_POSTING` (3) into table "m_savings_account_transaction", thereby increasing the account ledger balance at the close of every interest posting period.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  محاسبه و پرداخت سود سپرده‌ها به صورت کاملاً خودکار و در پایان دوره‌های مالی (ماهانه، فصلی، سالانه) توسط جاب دسته‌ای یا دستور کاربر انجام می‌شود. موتور سود فاینراکت:
  ۱. مانده‌های پایان روز (`EndOfDayBalance`) را در طول دوره استخراج می‌کند.
  ۲. سود مرکب را در فواصل تجمیع تعیین‌شده محاسبه می‌نماید.
  ۳. چنانچه کسر مالیات تکلیفی (`withhold_tax`) فعال باشد، درصد مالیات مصوب گروه مالیاتی را محاسبه و در قالب تراکنش بدهکار مالیات با نوع ۱۸ (`WITHHOLD_TAX`) منظور می‌دارد.
  ۴. خالص سود متعلقه را با یک تراکنش بستانکار سود با نوع ۳ (`INTEREST_POSTING`) به اصل مانده حساب اضافه می‌کند (سرمایه‌گذاری سود / Capitalization).
  ۵. اسناد حسابداری شامل بدهکار شدن هزینه سود سپرده‌ها و بستانکار شدن حساب پس‌انداز مشتری در دفتر کل درج می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If interest posting is attempted for a future date, then the Fineract Savings Engine shall reject the execution with error code "error.msg.savingsaccount.postInterest.cannot.be.future.date".`
  * `If posting is triggered prior to the minimum balance calculation date, then the Fineract Savings Engine shall abort with a PostInterestAsOnDateException.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#calculateInterestUsing(...)` و `SavingsAccountWritePlatformServiceJpaRepositoryImpl#postInterest(JsonCommand command)`
  * **کدهای خطا و انوتیشن‌ها:** `PostInterestAsOnDateException`, نوع تراکنش ۳ (`INTEREST_POSTING`), نوع تراکنش ۱۸ (`WITHHOLD_TAX`)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction`, جاب `PostInterestForSavingTasklet`

---

#### REQ-SAV-TXN-004: ابطال و معکوس‌سازی تراکنش‌ها با بازسازی مانده‌های تاریخی و اسناد معکوس
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized staff member executes an undo or reverse transaction command for an eligible savings transaction, the Fineract Savings Engine shall create a compensating reversal transaction or mark the original transaction as reversed (is_reversed = true), automatically undo any associated secondary charges (such as withdrawal fees), recalculate running balances for all subsequent chronological transactions, recompute periodic interest, and post reversing journal entries to the general ledger.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  در صورت بروز اشتباه کاربر شعبه در واریز یا برداشت وجه، سامانه دو سازوکار اصلاحی ارائه می‌دهد:
  ۱. **لغو تراکنش (Undo Transaction):** رکورد اصلی را به عنوان ابطال‌شده نشانه‌گذاری می‌کند (`is_reversed = true`) و در صورت وجود کارمزد برداشت متصل به آن، کارمزد را نیز همزمان ملغی می‌سازد.
  ۲. **معکوس‌سازی صریح (Reverse Transaction):** یک تراکنش جبرانی معکوس با پیوند به تراکنش اولیه (`original_transaction_id`) و نشانگر `is_reversal = true` صادر می‌نماید.
  پس از ابطال، موتور پس‌انداز مانده‌های لحظه‌ای (`running_balance_derived`) کلیه تراکنش‌های تاریخی پس از آن تاریخ را مجدداً از نو زنجیره‌وار محاسبه کرده و در صورت اثرگذاری بر پایه‌های سود گذشته، سودهای دوره‌ای را بازمحاسبه و اصلاح می‌نماید. طبق قوانین بانکی، تراکنش‌های ناشی از انتقال وجه بین‌حسابی (Account Transfer) به دلیل ریسک دوطرفه قابل لغو مستقیم نیستند.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an attempt is made to undo or reverse a transaction that originated from an account transfer, then the Fineract Savings Engine shall reject the operation with error code "error.msg.saving.account.transfer.transaction.update.not.allowed".`
  * `If the target transaction is not found for the specified account, then the Fineract Savings Engine shall throw a SavingsAccountTransactionNotFoundException.`
  * `If reversing a transaction causes any subsequent historical balance to drop below zero (violating overdraft bounds), then the Fineract Savings Engine shall abort the reversal with an InsufficientAccountBalanceException.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#reverseTransaction(...)`, `#undoTransaction(...)`, `SavingsAccount#undoSavingsTransaction(Long transactionId)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('REVERSETRANSACTION_SAVINGSACCOUNT')")`, `error.msg.saving.account.transfer.transaction.update.not.allowed`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction` (ستون‌های `is_reversed`, `is_reversal`, `original_transaction_id`), Liquibase changelog `0005_savings_transaction_reversal.xml`

---

### بخش ۵: توثیق سپرده، مسدودی وجه و مدیریت وثایق نقدی (Holds, Liens & Collateral Management)

#### REQ-SAV-HOLD-001: اعمال مسدودی و توثیق وجه جهت ضمانت تسهیلات و احکام حقوقی
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized user or collateral subsystem submits a holdAmount command on an `ACTIVE` savings account, the Fineract Savings Engine shall validate that the requested hold amount does not exceed the available withdrawable balance (or the maxAllowedLienLimit if marked as a lien), persist an `AMOUNT_HOLD` (20) transaction in table "m_savings_account_transaction", increment on_hold_funds_derived in table "m_savings_account", and immediately reduce the Available Balance by the exact hold amount.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  مسدودی وجه (Hold) و توثیق سپرده (Lien) مکانیزم‌های بنیادین برای حبس بخشی از مانده حساب جهت تضمین بازپرداخت تسهیلات اعطایی (وثیقه نقدی وام)، تضمین ضمانت‌نامه‌های بانکی یا اجرای احکام قضایی توقیف اموال هستند. وجه مسدودشده همچنان در مالکیت مشتری باقی مانده و در صورت سودده بودن حساب، مشمول سود روزشمار می‌گردد؛ اما مشتری حق برداشت یا انتقال آن را ندارد. موتور پس‌انداز با دریافت دستور، ستون `on_hold_funds_derived` و `total_savings_amount_on_hold` را افزایش داده و مانده در دسترس را بی‌درنگ کاهش می‌دهد. علت مسدودی از جدول کدهای سیستمی (`SavingsAccountBlockReasons`) ثبت می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the hold amount exceeds the account's available withdrawable balance, then the Fineract Savings Engine shall reject the hold with error code "insufficient.balance".`
  * `If the account is not in ACTIVE state, then the Fineract Savings Engine shall reject the hold request with error code "not.in.active.state".`
  * `If lienAllowed is specified but the product does not permit liens, then the Fineract Savings Engine shall reject the command with error code "lien.is.not.allowed.in.product.level".`
  * `If the hold amount exceeds maxAllowedLienLimit, then the Fineract Savings Engine shall abort with error code "lien.limit.exceeded".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#holdAmount(Long savingsId, JsonCommand command)` و `SavingsAccount#holdAmount(BigDecimal amount)`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('HOLDAMOUNT_SAVINGSACCOUNT')")`, `lien.limit.exceeded`, `insufficient.balance`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون‌های `on_hold_funds_derived`, `total_savings_amount_on_hold`), جدول `m_savings_account_transaction` (نوع ۲۰ `AMOUNT_HOLD`), جدول `m_deposit_account_on_hold_transaction`

---

#### REQ-SAV-HOLD-002: رفع توثیق و آزادسازی وجوه مسدودشده با بازگشت آنی به مانده در دسترس
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When an authorized staff member or automated loan settlement process triggers a releaseAmount command against an active hold transaction, the Fineract Savings Engine shall verify that the transaction amount is currently on hold, insert an `AMOUNT_RELEASE` (21) transaction referencing the original hold transaction ID, decrement on_hold_funds_derived in table "m_savings_account", and immediately restore the released amount to the account's Available Balance.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  پس از تسویه کامل تعهدات وام تضمین‌شده، انقضای ضمانت‌نامه بانکی یا لغو دستور قضایی توقیف، وجوه مسدودشده باید آزاد گردند. کاربر یا فرآیند خودکار، شناسه تراکنش مسدودی اولیه را به متد آزادسازی ارسال می‌نماید. موتور پس‌انداز بررسی می‌کند که وجه مذکور قبلاً آزاد نشده باشد. سپس یک تراکنش متناظر با نوع ۲۱ (`AMOUNT_RELEASE`) ثبت شده و شناسه آزادسازی در فیلد `release_id` تراکنش اولیه نشانده می‌شود. همزمان مقدار `on_hold_funds_derived` به میزان وجه آزادشده کاهش یافته و این مبلغ بدون فوت وقت به موجودی قابل برداشت و در دسترس مشتری اضافه می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If the referenced hold transaction has already been released (releaseId is not null), then the Fineract Savings Engine shall reject the release with error code "validation.msg.amount.is.not.on.hold".`
  * `If the target hold transaction ID is not found, then the Fineract Savings Engine shall throw a SavingsAccountTransactionNotFoundException.`
  * `If the savings account is not in ACTIVE state during release, then the Fineract Savings Engine shall reject the release with error code "not.in.active.state".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#releaseAmount(Long savingsId, Long savingsTransactionId, JsonCommand command)` و `SavingsAccount#releaseOnHoldAmount(BigDecimal amount)`
  * **کدهای خطا و انوتیشن‌ها:** `validation.msg.amount.is.not.on.hold`, نوع تراکنش ۲۱ (`AMOUNT_RELEASE`)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction` (نوع ۲۱), جدول `m_savings_account` (ستون `on_hold_funds_derived`), جدول `m_deposit_account_on_hold_transaction`

---

#### REQ-SAV-HOLD-003: کنترل سقف مجاز وثیقه‌گذاری و منع تعارض اضافه برداشت با توثیق سپرده
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While configuring savings products or placing account-level liens, where lien capabilities and overdraft facilities are concurrently enabled, the Fineract Savings Engine shall enforce that overdraftLimit never exceeds maxAllowedLienLimit, and shall reject any lien placement that causes the cumulative lien balance to exceed the authorized ceiling.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  همزمانی توثیق وجه و اضافه برداشت بر روی یک حساب می‌تواند سبب تعارض منطقی در محاسبات مانده و ریسک اعتباری شدید گردد؛ زیرا توثیق وجه مستلزم حبس دارایی واقعی مشتری است در حالی که اضافه برداشت ماهیت بدهی دارد. از این رو، موتور اعتبارسنجی فاینراکت ناوردای سفت‌وسختی را وضع کرده است: در صورتی که هر دو قابلیت فعال باشند، سقف اضافه برداشت هرگز نباید بزرگتر از سقف مجاز توثیق (`maxAllowedLienLimit`) باشد. همچنین مجموع مبالغ توثیق‌شده در هر لحظه توسط اعتبارسنج بررسی شده و از ایجاد تعهدات مازاد بر سقف مصوب جلوگیری می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If allowOverdraft is true and lienAllowed is true and overdraftLimit exceeds maxAllowedLienLimit, then the Fineract Savings Engine shall abort with error code "Overdraft.limit.can.not.be.greater.than.lien.limit".`
  * `If a lien hold request causes the cumulative lien amount to breach maxAllowedLienLimit, then the Fineract Savings Engine shall reject the transaction with error code "lien.limit.exceeded".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/data/SavingsAccountTransactionDataValidator.java`
  * **متد اجرایی:** `#validateHoldAndAssembleForm(...)`
  * **کدهای خطا و انوتیشن‌ها:** `Overdraft.limit.can.not.be.greater.than.lien.limit`, `lien.limit.exceeded`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_product` (ستون‌های `is_lien_allowed`, `max_allowed_lien_limit`), جدول `m_savings_account`

---

### بخش ۶: رکود، توقیف اموال بلاصاحب و نگهداری حساب (Dormancy, Escheatment & Account Maintenance)

#### REQ-SAV-DORM-001: شناسایی سیستماتیک حساب‌های راکد، تغییر به وضعیت غیرفعال و کسر کارمزد عدم فعالیت
* **الگوی EARS:** Event-Driven
* **EARS Statement:**
  > When the scheduled dormancy tracking batch job executes at the Close-of-Business, the Fineract Savings Maintenance Engine shall query for all `ACTIVE` accounts with sub-status `NONE` whose elapsed days since the last customer-initiated transaction (DEPOSIT or WITHDRAWAL) or activation date is greater than or equal to `days_to_inactive`, transition their sub-status to `INACTIVE` (100), and auto-deduct any configured inactivity charges.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  حساب‌هایی که برای مدتی طولانی توسط صاحب حساب استفاده نشوند، بر اساس سیاست‌های نظارتی باید وارد چرخه رکود گردند تا از خطرات کلاهبرداری و سوءاستفاده‌های داخلی مصون بمانند. جاب شبانه پایان روز (`UpdateSavingsDormantAccountsTasklet`) حساب‌های فعالی را که از تاریخ آخرین تراکنش مشتری‌محور (فقط واریز یا برداشت با کدهای ۱ و ۲، نه واریز خودکار سود توسط سیستم) بیش از آستانه `days_to_inactive` گذشته باشد شناسایی می‌کند. سیستم زیروضعیت حساب را به ۱۰۰ (`INACTIVE`) تغییر می‌دهد. چنانچه برای حساب کارمزد عدم فعالیت (`isSavingsNoActivity`) تعریف شده باشد، سیستم مبلغ کارمزد را محاسبه نموده و به صورت خودکار از مانده حساب کسر می‌نماید.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If daysToInactive is less than or equal to zero on a product with dormancy tracking enabled, then the Fineract Savings Engine shall reject the product setup with error code "validation.msg.savingsproduct.daysToInactive.must.be.greater.than.zero".`
  * `If inactivity fee deduction causes an account without overdraft facility to breach zero, then the Fineract Savings Engine shall cap the fee deduction up to the available balance.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/jobs/updatesavingsdormantaccounts/UpdateSavingsDormantAccountsTasklet.java`
  * **متد اجرایی:** `#execute(StepContribution contribution, ChunkContext chunkContext)` و `SavingsAccount#setSubStatusInactive(boolean backdatedTxnsAllowedTill)`
  * **کدهای خطا و انوتیشن‌ها:** اینام `SavingsAccountSubStatusEnum.INACTIVE` (کد ۱۰۰), اینام `ChargeTimeType.SAVINGS_NO_ACTIVITY`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون `sub_status_enum`), جدول `m_savings_account_charge`

---

#### REQ-SAV-DORM-002: گذار خودکار به وضعیت خوابیده (DORMANT) و انسداد برداشت‌های سامانه‌ای
* **الگوی EARS:** State-Driven
* **EARS Statement:**
  > While a savings account is in sub-status `INACTIVE` (100), when the dormancy tracking job evaluates that elapsed days without customer-initiated activity is greater than or equal to `days_to_dormancy`, the Fineract Savings Engine shall transition the account sub-status to `DORMANT` (200) and reject all automated and third-party debit operations until explicit KYC reactivation is completed.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  چنانچه دوره عدم فعالیت حساب همچنان تداوم یابد و از آستانه دوم یعنی `days_to_dormancy` فراتر رود، حساب وارد مرحله خواب کامل عملیاتی یا وضعیت راکد (`DORMANT` - کد ۲۰۰) می‌گردد. در این وضعیت، ریسک پولشویی و استفاده غیرمجاز به شدت بالا برآورد می‌شود؛ لذا سامانه فاینراکت کلیه درخواست‌های برداشت اتوماتیک، کسر اقساط توسط سامانه‌های واسط، انتقال‌های دسته‌ای و پرداخت‌های اینترنتی را به طور کامل مسدود می‌سازد. حساب در وضعیت راکد قفل مانده و خروج از آن نیازمند حضور مشتری در شعبه و اجرای فرآیند احراز هویت مجدد است.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If daysToDormancy is configured to be less than or equal to daysToInactive, then the Fineract Savings Engine shall reject the product configuration with error code "validation.msg.savingsproduct.daysToDormancy.must.be.greater.than.daysToInactive".`
  * `If an external third-party debit is attempted while an account is in DORMANT state, then the Fineract Savings Engine shall reject the transaction with an operational error.`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountReadPlatformServiceImpl.java`
  * **متد اجرایی:** `#retrieveSavingsIdsPendingDormant(LocalDate tenantLocalDate)` و `SavingsAccount#setSubStatusDormant()`
  * **کدهای خطا و انوتیشن‌ها:** `SavingsAccountSubStatusEnum.DORMANT` (کد ۲۰۰)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون `sub_status_enum`), جدول `m_savings_product` (ستون‌های `is_dormancy_tracking_active`, `days_to_dormancy`)

---

#### REQ-SAV-DORM-003: سلب مالکیت، واریز مانده به سرفصل خزانه‌داری دولت و مختومه کردن پرونده
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a savings account is in sub-status `DORMANT` (200), when the dormancy tracking job detects that elapsed days without customer activity is greater than or equal to `days_to_escheat`, the Fineract Savings Engine shall transition status_enum to `CLOSED` (600) and sub_status_enum to `ESCHEAT` (300), generate an `ESCHEAT` debit transaction (type 19) to exhaust the full outstanding ledger balance, and transfer the liability to the designated government escheat liability account in the General Ledger.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  طبق قوانین پولی و بانکی در اکثر حوزه‌های قضایی، چنانچه حسابی سالیان متمادی در وضعیت راکد باقی بماند و مالک آن شناسایی نشود، وجوه موجود در آن به عنوان «اموال بلاصاحب و بلاتکلیف» (Unclaimed Property / Escheatment) تلقی شده و باید به حساب خزانه‌داری کل کشور یا بانک مرکزی واریز گردد. جاب پایان روز فاینراکت پس از فرارسیدن موعد `days_to_escheat`:
  ۱. وضعیت حساب را به ۶۰۰ (`CLOSED`) و زیروضعیت را به ۳۰۰ (`ESCHEAT`) تغییر می‌دهد.
  ۲. یک تراکنش بدهکار تخلیه موجودی با نوع ۱۹ (`ESCHEAT`) به میزان کل مانده دفتری ثبت می‌کند تا مانده حساب صفر گردد.
  ۳. سند حسابداری دفتر کل ثبت شده و بدهی بانک از سرفصل سپرده‌های پس‌انداز کسر و به حساب بستانکاران دولت (`ESCHEAT_LIABILITY`) منتقل می‌گردد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If daysToEscheat is less than or equal to daysToDormancy, then the Fineract Savings Engine shall reject the configuration with error code "validation.msg.savingsproduct.daysToEscheat.must.be.greater.than.daysToDormancy".`
  * `If escheatLiabilityAccountId is missing when dormancy tracking is active, then the Fineract Savings Engine shall abort creation with error code "validation.msg.savingsproduct.escheatLiabilityAccountId.cannot.be.blank".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-savings/src/main/java/org/apache/fineract/portfolio/savings/domain/SavingsAccount.java`
  * **متد اجرایی:** `#escheat(AppUser appUser)` و `SavingsAccountWritePlatformServiceJpaRepositoryImpl#escheat(Long savingsId)`
  * **کدهای خطا و انوتیشن‌ها:** نوع تراکنش ۱۹ (`ESCHEAT`), `SavingsAccountSubStatusEnum.ESCHEAT` (کد ۳۰۰), `SavingsAccountStatusType.CLOSED` (کد ۶۰۰)
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account_transaction` (نوع ۱۹), جدول `m_savings_account` (ستون‌های `status_enum`, `sub_status_enum`, `closedon_date`), جدول `acc_gl_account`

---

#### REQ-SAV-DORM-004: احراز هویت مجدد، رفع انسداد و خروج خودکار از رکود با تراکنش مشتری
* **الگوی EARS:** Complex
* **EARS Statement:**
  > While a savings account has sub-status `INACTIVE` (100) or `DORMANT` (200), when a valid customer-initiated deposit or teller-executed transaction is processed, the Fineract Savings Engine shall automatically restore sub_status_enum to `NONE` (0), or when an authorized staff member executes an explicit unblock command with KYC validation notes, the Fineract Savings Engine shall reset sub-status to `NONE` (0) and restore all operational capabilities.
* **شرح نیازمندی و سناریوی بیزنس (فارسی):**
  خروج حساب از رکود و غیرفعالی از دو مسیر قانونی میسر است:
  ۱. **فعال‌سازی خودکار بر اثر تراکنش مشتری:** چنانچه یک تراکنش واریز یا برداشت حضوری با منشأ تاییدشده صاحب حساب به سامانه واصل شود، متد `SavingsAccount.withdraw` یا `SavingsAccount.deposit` به صورت درون‌برنامه‌ای چک می‌کند که اگر زیروضعیت حساب `INACTIVE` یا `DORMANT` باشد، بلافاصله آن را به کد ۰ (`NONE`) بازگردانده و رکود را منتفی می‌سازد.
  ۲. **فعال‌سازی رسمی توسط متصدی شعبه (Reactivation KYC):** در صورت مسدودی کامل یا خواب حساب، متصدی شعبه پس از دریافت مدارک هویتی و به‌روزرسانی پرونده مشتری، دستور `unblockAccount` را اجرا می‌کند. سیستم یادداشت‌های احراز هویت را ثبت نموده، زیروضعیت را صفر کرده و کلیه محدودیت‌های بدهکار و بستانکار را مرتفع می‌سازد.
* **رفتارهای ناخواسته و شروط خطا (EARS If-Then):**
  * `If an unblock command is submitted for an account whose sub-status is already NONE, then the Fineract Savings Engine shall reject the request with error code "not.in.blocked.state".`
  * `If unblockAccount is executed on an account that is not in ACTIVE state, then the Fineract Savings Engine shall fail with error code "not.in.active.state".`
* **ماتریس ردیابی به سورس‌کد (Traceability Matrix):**
  * **مسیر فایل و کلاس سورس:** `apache-fineract-src-1.15.0/fineract-provider/src/main/java/org/apache/fineract/portfolio/savings/service/SavingsAccountWritePlatformServiceJpaRepositoryImpl.java`
  * **متد اجرایی:** `#unblockAccount(Long savingsId)` و `SavingsAccount#unblock()`
  * **کدهای خطا و انوتیشن‌ها:** `@PreAuthorize("hasAuthority('UNBLOCK_SAVINGSACCOUNT')")`, `not.in.blocked.state`
  * **پایگاه داده و انتیتی‌ها:** جدول `m_savings_account` (ستون `sub_status_enum`), اینام `SavingsAccountSubStatusEnum.NONE` (کد ۰)

---

## ۴. ماتریس ردیابی فنی و ارکان پایگاه داده (Technical Traceability & Database Schema Matrix)

| موجودیت دامنه (Entity) | جدول دیتابیس (DB Table) | چنج‌لاگ Liquibase | عملیات کلیدی (Key Operations) | تغییرات وضعیت (State Transitions) |
| :--- | :--- | :--- | :--- | :--- |
| **SavingsProduct** | `m_savings_product` | `0001_initial_schema.xml`<br/>`0010_lien_allowed.xml` | تعریف محصول، نرخ سود، دوره‌های مرکب‌سازی و واریز، حدود وثیقه | پیکربندی اولیه و تغییرات سیستمی |
| **SavingsAccount** | `m_savings_account` | `0001_initial_schema.xml`<br/>`0009_hold_reason.xml` | ایجاد حساب، فعال‌سازی، بستن، انسداد، توثیق وجوه | $100 \to 200 \to 300 \to 600$<br/>زیروضعیت: $0 \to 100 \to 200 \to 300 / 400$ |
| **SavingsAccountTransaction** | `m_savings_account_transaction` | `0001_initial_schema.xml`<br/>`0005_savings_reversal.xml` | واریز، برداشت، واریز سود، کسر مالیات، توثیق وجه، آزادسازی، معکوس‌سازی | انواع تراکنش ۱ تا ۲۱، نشانگر ابطال (`is_reversed`, `is_reversal`) |
| **DepositAccountTermAndPreClosure** | `m_deposit_account_term_and_preclosure` | `0001_initial_schema.xml` | مدیریت دوره سپرده مدت‌دار، نرخ جریمه شکست سود، تسویه در سررسید | وضعیت‌های ۷۰۰ (`PRE_MATURE_CLOSURE`) و ۸۰۰ (`MATURED`) |
| **RecurringDepositScheduleInstallment** | `m_mandatory_savings_schedule` | `0001_initial_schema.xml` | تولید اقساط اجباری، پایش سررسید، پیش‌پرداخت، ثبت دیرکرد | فیلدهای `completed_derived`, `obligations_met_on_date` |
| **DepositAccountOnHoldTransaction** | `m_deposit_account_on_hold_transaction` | `0001_initial_schema.xml` | ثبت مسدودی وثیقه نقدی برای تسهیلات و احکام، پیوند به ضامنین | تغییر فیلد `on_hold_funds_derived` در حساب پس‌انداز |
| **SavingsAccountCharge** | `m_savings_account_charge` | `0001_initial_schema.xml` | کارمزدهای برداشت، کارمزد سالانه، کارمزد عدم فعالیت، کارمزد ماهانه | پرداخت، انصراف (Waive)، غیرفعال‌سازی |
