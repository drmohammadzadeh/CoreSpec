
## ۲. بخش اول: مدیریت تسهیلات، اعتبارات و پرتفوی وام (Lending & Credit Portfolio Domain)

این بخش دربرگیرنده مفاهیم بنیادین چرخه حیات تسهیلات، ریاضیات استهلاک اقساط، متدهای شناسایی سود، مدیریت مطالبات غیرجاری، ساختاربندی مجدد و سوخت مطالبات در هسته اعتبارات آپاچی فاینراکت است.

---

### ۲.۱. اصل تسهیلات / سرمایه وام (Principal)
* **اصطلاح انگلیسی:** Principal (Approved Principal / Disbursed Principal / Principal Outstanding)
* **معادل استاندارد فارسی:** اصل تسهیلات / سرمایه اولیه وام / مانده اصل بدهی
* **تعریف جامع و منطق بانکی:** مبلغ ناخالص پولی که مؤسسه مالی یا بانک در قالب قرارداد اعتباری به وام‌گیرنده پرداخت کرده یا متعهد به واگذاری آن می‌شود. اصل وام پایه اصلی محاسبه سود، ریسک اعتباری و تعهدات بازپرداخت مشتری را تشکیل می‌دهد و استهلاک آن در طول زمان، مانده بازپرداخت‌نشده را کاهش می‌دهد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.loanaccount.domain.Loan`
  * **جدول پایگاه داده:** `m_loan`
  * **فیلدهای کلیدی:** `principal_amount` (اصل مصوب)، `principal_amount_outstanding_derived` (مانده اصل بدهی)، `total_principal_repaid_derived` (مجموع اصل تسویه‌شده).
  * **کلاس تقسیط:** `LoanRepaymentScheduleInstallment` (فیلد `principal_amount` در جدول `m_loan_repayment_schedule`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous* یا *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a loan account is in "ACTIVE" state, the Fineract Loan Engine shall allocate the principal portion of each processed repayment to reduce `principal_amount_outstanding_derived` and the respective installment's `principal_amount`.
    > **فارسی:** تا زمانی که پرونده وام در وضعیت "ACTIVE" قرار دارد، موتور تسهیلات فاینراکت باید بخش اصل هر بازپرداخت پردازش‌شده را جهت کاهش `principal_amount_outstanding_derived` و فیلد `principal_amount` قسط مربوطه تخصیص دهد.

---

### ۲.۲. سود و بهره تسهیلات (Interest)
* **اصطلاح انگلیسی:** Interest (Nominal Interest / Accrued Interest / Interest Outstanding)
* **معادل استاندارد فارسی:** سود تسهیلات / درآمد بهره‌ای / سود متعلقه
* **تعریف جامع و منطق بانکی:** هزینه استقراض سرمایه و بازده مالی بانک در ازای واگذاری حق انتفاع از پول طی دوره بازپرداخت. سود تسهیلات بر اساس نرخ سود اسمی مصوب، روش محاسبه، و مدت زمان در اختیار داشتن اصل سرمایه محاسبه شده و پس از سررسید، به عنوان طلب قطعی بانک در اقساط درج می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `Loan` و `LoanRepaymentScheduleInstallment`
  * **جدول پایگاه داده:** `m_loan` (فیلدهای `nominal_interest_rate_per_period`، `interest_charged_derived`، `interest_outstanding_derived`) و `m_loan_repayment_schedule` (`interest_amount`، `interest_completed_derived`).
  * **تراکنش متناظر:** `LoanTransaction` با نوع `LoanTransactionType.ACCRUAL` (کد ۸) یا استهلاک قسط.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an installment becomes due according to the repayment schedule, the Fineract Loan Engine shall recognize the calculated interest portion as a matured receivable and update `interest_outstanding_derived`.
    > **فارسی:** هنگامی که موعد سررسید یک قسط بر اساس جدول بازپرداخت فرا می‌رسد، موتور تسهیلات فاینراکت باید سهم سود محاسبه‌شده را به عنوان یک مطالبه سررسیدشده شناسایی نموده و مقدار `interest_outstanding_derived` را به‌روزرسانی کند.

---

### ۲.۳. جدول اقساط و بازپرداخت (Repayment Schedule)
* **اصطلاح انگلیسی:** Repayment Schedule (Amortization Schedule)
* **معادل استاندارد فارسی:** جدول بازپرداخت اقساط / دفترچه اقساط وام
* **تعریف جامع و منطق بانکی:** سند محاسباتی و حقوقی زمان‌بندی‌شده‌ای که کلیه مواعد سررسید، مبالغ اقساط، تفکیک سهم اصل و سود هر قسط، کارمزدهای دوره‌ای و مانده نزولی وام پس از هر پرداخت را تا پایان دوره سررسید نهایی مشخص می‌سازد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.loanaccount.domain.LoanRepaymentScheduleInstallment`
  * **جدول پایگاه داده:** `m_loan_repayment_schedule`
  * **موتور تولیدکننده:** `LoanScheduleGenerator`، `ProgressiveLoanScheduleGenerator`
  * **فیلدهای کلیدی:** `installment` (شماره قسط)، `duedate` (تاریخ سررسید)، `principal_amount`، `interest_amount`، `fee_charges_amount`، `penalty_charges_amount`، `completed_derived` (پرچم تسویه قسط).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a loan application is approved and disbursed, the Fineract Loan Schedule Generator shall generate an immutable series of installments in `m_loan_repayment_schedule` matching the product's repayment frequency and amortization method.
    > **فارسی:** هنگامی که تقاضای وام تصویب و وجه آن پرداخت می‌شود، موتور تولید جدول اقساط فاینراکت باید مجموعه‌ای متوالی از اقساط را در جدول `m_loan_repayment_schedule` متناسب با دوره تناوب بازپرداخت و متد استهلاک محصول تولید کند.

---

### ۲.۴. استهلاک با اقساط مساوی (Amortization: Equal Installments / EMI)
* **اصطلاح انگلیسی:** Amortization - Equal Installments (Equated Monthly Installment - EMI)
* **معادل استاندارد فارسی:** استهلاک با اقساط مساوی / قسط ثابت ماهانه
* **تعریف جامع و منطق بانکی:** شیوه‌ای از بازپرداخت وام که در آن مجموع مبالغ اصل و سود پرداختی مشتری در تمامی اقساط برابر است ($EMI = Principal_t + Interest_t = 	ext{Constant}$). در این متد، در اقساط ابتدایی سهم سود بیشتر و سهم اصل کمتر است، و به تدریج با کاهش مانده بدهی، سهم سود کاهش و سهم اصل افزایش می‌یابد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.loanaccount.domain.AmortizationMethod`
  * **مقدار فنی:** `AmortizationMethod.EQUAL_INSTALLMENTS` (مقدار عددی: `0` در ستون `amortization_method_enum` در `m_product_loan` و `m_loan`).
  * **کلاس محاسبه:** `AprCalculator` و فرمول ارزش فعلی اقساط انباشته.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where the loan product is configured with `AmortizationMethod.EQUAL_INSTALLMENTS`, the Fineract Loan Schedule Generator shall calculate installment amounts such that the sum of principal and interest remains uniform across all regular repayment periods.
    > **فارسی:** چنانچه محصول تسهیلاتی با `AmortizationMethod.EQUAL_INSTALLMENTS` پیکربندی شده باشد، موتور تولید اقساط فاینراکت باید مبالغ اقساط را به نحوی محاسبه کند که مجموع اصل و سود در تمامی دوره‌های بازپرداخت عادی یکنواخت و برابر بماند.

---

### ۲.۵. استهلاک با اصل مساوی (Amortization: Equal Principal)
* **اصطلاح انگلیسی:** Amortization - Equal Principal (Declining Installments)
* **معادل استاندارد فارسی:** استهلاک با اصل مساوی / کاهش تدریجی مبلغ کل قسط
* **تعریف جامع و منطق بانکی:** شیوه‌ای از بازپرداخت که در آن اصل سرمایه وام بر تعداد اقساط تقسیم شده و سهم اصل در هر قسط دقیقاً یکسان است ($Principal_t = rac{	ext{Principal}}{N}$). از آنجا که سود هر قسط بر اساس مانده بدهی کاهش‌یافته محاسبه می‌شود، مبلغ کل اقساط با گذشت زمان روندی نزولی پیدا می‌کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `AmortizationMethod`
  * **مقدار فنی:** `AmortizationMethod.EQUAL_PRINCIPAL` (مقدار عددی: `1` در ستون `amortization_method_enum`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where the loan product is configured with `AmortizationMethod.EQUAL_PRINCIPAL`, the Fineract Loan Schedule Generator shall divide the total disbursed principal equally among all active installments while reducing the interest portion in tandem with the declining principal balance.
    > **فارسی:** چنانچه محصول تسهیلاتی با `AmortizationMethod.EQUAL_PRINCIPAL` پیکربندی شده باشد، موتور تولید اقساط فاینراکت باید اصل پرداختی را به طور مساوی میان کلیه اقساط فعال تقسیم نموده و سهم سود را همگام با مانده نزولی اصل تسهیلات کاهش دهد.

---

### ۲.۶. روش محاسبه سود ثابت (Interest Method: Flat)
* **اصطلاح انگلیسی:** Flat Interest Rate Method
* **معادل استاندارد فارسی:** روش محاسبه سود ثابت / سود اسمی بر مبنای اصل اولیه
* **تعریف جامع و منطق بانکی:** روشی که در آن سود تسهیلات همواره بر مبنای مبلغ اولیه اصل وام مصوب برای کل دوره بازپرداخت محاسبه می‌شود، صرف‌نظر از اینکه چه بخشی از اصل وام در طول زمان مستهلک شده است ($	ext{Total Interest} = Principal 	imes Rate 	imes Term$). نرخ بهره موثر واقعی در این متد بسیار بالاتر از نرخ اعلامی است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.loanaccount.domain.InterestMethod`
  * **مقدار فنی:** `InterestMethod.FLAT` (مقدار عددی: `0` در ستون `interest_method_enum` در `m_loan` و `m_product_loan`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a loan utilizes `InterestMethod.FLAT`, the Fineract Loan Engine shall compute the total interest obligation based solely upon the initial disbursed principal without reducing the calculation base as repayments occur.
    > **فارسی:** چنانچه تسهیلات از `InterestMethod.FLAT` استفاده کند، موتور تسهیلات فاینراکت باید تعهد کل سود را صرفاً بر مبنای اصل اولیه پرداخت‌شده محاسبه کند بدون آنکه با انجام بازپرداخت‌ها مبنای محاسبه سود کاهش یابد.

---

### ۲.۷. روش محاسبه سود بر مبنای مانده نزولی (Interest Method: Declining Balance)
* **اصطلاح انگلیسی:** Declining Balance Interest Method (Reducing Balance)
* **معادل استاندارد فارسی:** روش سود بر مبنای مانده نزولی / سود روزشمار مانده بدهی
* **تعریف جامع و منطق بانکی:** استانداردترین روش بانکی مدرن که در آن سود هر دوره بازپرداخت صرفاً بر روی مانده استهلاک‌نیافته اصل وام در همان مقطع زمانی محاسبه می‌شود. با هر پرداخت اصل، مبنای محاسبه سود دوره‌های بعد کاهش می‌یابد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `InterestMethod`
  * **مقدار فنی:** `InterestMethod.DECLINING_BALANCE` (مقدار عددی: `1` در ستون `interest_method_enum`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a loan utilizes `InterestMethod.DECLINING_BALANCE`, the Fineract Loan Engine shall compute the interest for each installment cycle using exclusively the unamortized outstanding principal balance remaining at the start of that cycle.
    > **فارسی:** چنانچه تسهیلات از `InterestMethod.DECLINING_BALANCE` استفاده کند، موتور تسهیلات فاینراکت باید سود هر دوره قسط را منحصراً بر مبنای مانده استهلاک‌نیافته اصل وام در ابتدای همان دوره محاسبه نماید.

---

### ۲.۸. دوره محاسبه سود روزانه (Interest Calculation Period: Daily)
* **اصطلاح انگلیسی:** Interest Calculation Period Method - Daily
* **معادل استاندارد فارسی:** دوره محاسبه سود روزانه / سود روزشمار دقیق
* **تعریف جامع و منطق بانکی:** مکانیزمی که در آن سود تسهیلات بر مبنای تعداد روزهای واقعی سپری‌شده در هر مقطع (روز به روز بر پایه تقویم Actual/365 یا 30/360) محاسبه می‌گردد. این روش به ویژه در بازپرداخت‌های پیش از موعد یا با تأخیر، محاسبات سود عادلانه‌ای فراهم می‌کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.loanaccount.domain.InterestCalculationPeriodMethod`
  * **مقدار فنی:** `InterestCalculationPeriodMethod.DAILY` (مقدار عددی: `0` در ستون `interest_calculation_period_method_enum`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where the interest calculation period method is configured as `DAILY`, the Fineract Loan Engine shall compute accrued interest on a per-day basis reflecting the exact elapsed calendar days between transaction value dates.
    > **فارسی:** چنانچه متد دوره محاسبه سود به صورت `DAILY` پیکربندی شده باشد، موتور تسهیلات فاینراکت باید سود تعهدی را به صورت روزانه و متناسب با روزهای تقویمی سپری‌شده بین تاریخ‌های اعمال تراکنش محاسبه کند.

---

### ۲.۹. دوره محاسبه سود هم‌گام با بازپرداخت (Interest Calculation Period: Same as Repayment)
* **اصطلاح انگلیسی:** Interest Calculation Period Method - Same as Repayment Period
* **معادل استاندارد فارسی:** دوره محاسبه سود هم‌دوره با بازپرداخت / سود ماهانه ثابت
* **تعریف جامع و منطق بانکی:** شیوه‌ای که در آن محاسبات سود نه به صورت روزشمار، بلکه به ازای هر دوره کامل اقساط (مثلاً یک ماه تمام یا یک فصل) بدون توجه به تغییر روزهای تقویمی (۲۸ الی ۳۱ روزه) به صورت کسری یکنواخت از سال محاسبه می‌شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `InterestCalculationPeriodMethod`
  * **مقدار فنی:** `InterestCalculationPeriodMethod.SAME_AS_REPAYMENT_PERIOD` (مقدار عددی: `1`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where `InterestCalculationPeriodMethod.SAME_AS_REPAYMENT_PERIOD` is configured, the Fineract Loan Engine shall treat each installment interval as a uniform fraction of the annual interest period regardless of variation in calendar month lengths.
    > **فارسی:** چنانچه `InterestCalculationPeriodMethod.SAME_AS_REPAYMENT_PERIOD` تنظیم شده باشد، موتور تسهیلات فاینراکت باید هر فاصله اقساط را به عنوان یک کسر یکنواخت از دوره سود سالانه تلقی کند، صرف‌نظر از اختلاف تعداد روزهای ماه‌های تقویمی.

---

### ۲.۱۰. دوره تنفس در اصل وام (Grace Period on Principal)
* **اصطلاح انگلیسی:** Grace Period on Principal (Principal Moratorium)
* **معادل استاندارد فارسی:** دوره تنفس بازپرداخت اصل وام
* **تعریف جامع و منطق بانکی:** بازه زمانی مشخصی در ابتدای دوره وام‌دهی (شامل $K$ قسط نخست) که طی آن وام‌گیرنده از پرداخت بخش اصل بدهی معاف است و صرفاً موظف به پرداخت سود تسهیلات یا کارمزدها می‌باشد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan` و `LoanProduct`
  * **فیلد جدول:** `m_loan.grace_on_principal_periods` و `m_product_loan.grace_on_principal_periods`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a grace period on principal is defined for $N$ periods, the Fineract Loan Schedule Generator shall set the `principal_amount` to zero for the first $N$ installments while billing accrued interest in full.
    > **فارسی:** چنانچه دوره تنفس در اصل وام برای $N$ دوره تعریف شده باشد، موتور تولید اقساط فاینراکت باید مبلغ `principal_amount` را در $N$ قسط نخست برابر با صفر تعیین نماید در حالی که سود تعهدی را به طور کامل مطالبه می‌کند.

---

### ۲.۱۱. دوره تنفس در سود وام (Grace Period on Interest)
* **اصطلاح انگلیسی:** Grace Period on Interest (Interest Free Periods)
* **معادل استاندارد فارسی:** دوره تنفس پرداخت سود وام / معافیت موقت از پرداخت بهره
* **تعریف جامع و منطق بانکی:** بازه‌ای در ابتدای تسهیلات که در آن مشتری از پرداخت سود معاف است. سود متعلقه ممکن است بخشوده شود یا به مانده وام در آینده موکول گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan` و `LoanProduct`
  * **فیلد جدول:** `m_loan.grace_on_interest_periods` و `m_product_loan.grace_on_interest_periods`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a grace period on interest is configured for $N$ periods, the Fineract Loan Schedule Generator shall set `interest_amount` to zero for the designated installments without accruing uncapitalized interest against the borrower.
    > **فارسی:** چنانچه دوره تنفس در سود برای $N$ دوره پیکربندی شده باشد، موتور تولید اقساط فاینراکت باید `interest_amount` را برای اقساط معین برابر با صفر قرار دهد بدون آنکه سود سرمایه‌نشده‌ای بر عهده مشتری شناسایی گردد.

---

### ۲.۱۲. مهلت قانونی تعلیق بازپرداخت و امهال (Moratorium)
* **اصطلاح انگلیسی:** Moratorium (Full Repayment Suspension)
* **معادل استاندارد فارسی:** امهال قانونی / تعلیق کامل بازپرداخت اقساط
* **تعریف جامع و منطق بانکی:** تعلیق کامل کلیه تعهدات بازپرداختی وام‌گیرنده (اصل و سود) به دلایل حوادث قهری، بحران‌های اقتصادی یا سیاست‌های حمایتی حاکمیتی برای مدتی معین. در این دوره، اقساط سررسید نمی‌شوند و موعد سررسید نهایی وام به اندازه دوره امهال تمدید می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan`، `m_loan.grace_on_arreas_ageing`
  * **فرایند بازتنظیم:** `LoanRescheduleRequest` با اعمال معافیت موقت دیرکرد.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While an active loan account is within an authorized moratorium window, the Fineract Delinquency Engine shall suspend delinquency aging and shall not mark installments falling within the moratorium window as overdue.
    > **فارسی:** تا زمانی که پرونده وام فعال در بازه مجاز امهال قرار دارد، موتور محاسبه نکول فاینراکت باید شمارش سن مطالبات را معلق نگه دارد و اقساط واقع در بازه امهال را به عنوان معوق علامت‌گذاری نکند.

---

### ۲.۱۳. پرداخت چندمرحله‌ای و ترانش تسهیلات (Tranche / Multi-disbursal)
* **اصطلاح انگلیسی:** Tranche / Multi-Disbursement
* **معادل استاندارد فارسی:** پرداخت مرحله‌ای / اعطای چندبخشی اصل وام (ترانش)
* **تعریف جامع و منطق بانکی:** سازوکاری که در آن اصل کل مصوب تسهیلات (مثلاً وام‌های ساختمانی یا خطوط اعتباری پروژه‌ای) یک‌جا پرداخت نمی‌شود، بلکه در چند مرحله متوالی (Tranches) با پیشرفت کار یا درخواست مشتری واریز می‌گردد. جدول اقساط و سود باید با هر پرداخت مجدداً محاسبه شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.loanaccount.domain.LoanDisbursementDetails`
  * **جدول دیتابیس:** `m_loan_disbursement_detail`
  * **پیکربندی محصول:** `m_product_loan.multi_disburse_loan = true`، `max_tranche_count`
  * **رویداد:** `LoanDisbursalBusinessEvent`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + When)*
  * **گزاره استاندارد:**
    > **English:** Where multi-disbursement is enabled on the loan product, when a subsequent tranche disbursement is posted, the Fineract Loan Schedule Generator shall dynamically recalculate remaining future installments based on the newly increased outstanding principal balance.
    > **فارسی:** چنانچه پرداخت چندمرحله‌ای روی محصول تسهیلات فعال باشد، هنگامی که پرداخت یک ترانش جدید ثبت می‌گردد، موتور تولید اقساط فاینراکت باید اقساط آتی باقی‌مانده را بر مبنای مانده اصل افزایش‌یافته جدید بازتنظیم و مجدداً محاسبه کند.

---

### ۲.۱۴. استمهال و تغییر ساختار اقساط (Restructure / Reschedule)
* **اصطلاح انگلیسی:** Loan Restructuring / Rescheduling
* **معادل استاندارد فارسی:** تجدید ساختار وام / استمهال و جدول‌بندی مجدد اقساط
* **تعریف جامع و منطق بانکی:** تغییر شرایط قرارداد اولیه تسهیلات به دلیل ناتوانی مالی موجه مشتری در پرداخت اقساط سررسیدشده، شامل افزایش مدت بازپرداخت، تغییر نرخ سود، بخشش جرایم و صدور جدول اقساط کاملاً نوسازی‌شده جهت جلوگیری از سوخت کامل مطالبات.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.loanaccount.rescheduleloan.domain.LoanRescheduleRequest`
  * **جدول دیتابیس:** `m_loan_reschedule_request`
  * **کدهای وضعیت:** `status_enum` (100: Submitted, 200: Approved, 300: Rejected).
  * **ماشین حالت:** امکان گذار به وضعیت `CLOSED_RESCHEDULE_OUTSTANDING_AMOUNT` (کد ۶۰۲) و ایجاد پرونده جدید.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an authorized checker approves a `LoanRescheduleRequest`, the Fineract Loan Reschedule Platform Service shall archive the prior schedule and generate a modified installment plan starting from the agreed reschedule date.
    > **فارسی:** هنگامی که کاربر تاییدکننده (Checker) مجاز، یک `LoanRescheduleRequest` را تایید می‌کند، سرویس پلتفرم استمهال وام فاینراکت باید جدول پیشین را آرشیو کرده و جدول اقساط تعدیل‌شده جدیدی را از تاریخ مصوب استمهال صادر نماید.

---

### ۲.۱۵. بستن و تسویه پیش از موعد قهری (Foreclosure)
* **اصطلاح انگلیسی:** Foreclosure (Pre-closure / Forced Early Settlement)
* **معادل استاندارد فارسی:** تسویه اجباری پیش از موعد / تملک وثیقه و خاتمه قهری پرونده
* **تعریف جامع و منطق بانکی:** خاتمه حقوقی یک‌جانبه قرارداد تسهیلات از سوی بانک به دلیل نکول شدید مشتری یا نقض اساسی شروط قرارداد، که طی آن کلیه اقساط آتی حال گردیده و بانک از طریق به اجرا گذاردن تضامین یا وصول مطالبات، حساب را می‌بندد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس:** `LoanWritePlatformService.forecloseLoan`
  * **جدول:** `m_loan_transaction` با نوع `PREPAYMENT` / `REPAYMENT`، معکوس‌سازی سودهای تحقق‌نیافته.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a loan foreclosure command is executed, the Fineract Loan Engine shall accelerate all future unearned interest obligations, demand the net outstanding principal, and upon receipt of final settlement, transition the loan status to `CLOSED_OBLIGATIONS_MET`.
    > **فارسی:** هنگامی که دستور تسویه اجباری وام (Foreclosure) اجرا می‌شود، موتور تسهیلات فاینراکت باید کلیه تعهدات سود تحقق‌نیافته آتی را ابطال نموده، مانده خالص اصل بدهی را مطالبه کند و پس از وصول تسویه نهایی، وضعیت وام را به `CLOSED_OBLIGATIONS_MET` تغییر دهد.

---

### ۲.۱۶. نکول و سررسیدگذشتگی اعتباری (Delinquency)
* **اصطلاح انگلیسی:** Delinquency (Credit Delinquency)
* **معادل استاندارد فارسی:** نکول اعتباری / قصور در پرداخت اقساط
* **تعریف جامع و منطق بانکی:** وضعیت نقض تعهدات مالی توسط وام‌گیرنده زمانی که یک یا چند قسط در تاریخ سررسید مقرر پرداخت نشده و وارد بازه زمانی تاخیر می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.delinquency.domain.DelinquencyBucket` و `DelinquencyRange`
  * **جدول پایگاه داده:** `m_delinquency_bucket`، `m_delinquency_range`
  * **سرویس دگرگونی:** `DelinquencyWritePlatformService`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a loan account possesses overdue unpaid installments exceeding the configured grace days, the Fineract Delinquency Engine shall classify the loan into the corresponding delinquency range.
    > **فارسی:** تا زمانی که یک حساب وام دارای اقساط معوق پرداخت‌نشده فراتر از روزهای تنفس مجاز باشد، موتور نکول فاینراکت باید وام را در بازه نکول متناظر طبقه‌بندی کند.

---

### ۲.۱۷. دارایی‌های غیرجاری و مطالبات مشکوک‌الوصول (Non-Performing Asset - NPA)
* **اصطلاح انگلیسی:** Non-Performing Asset (NPA) / Non-Accrual Status
* **معادل استاندارد فارسی:** دارایی غیرجاری / تسهیلات غیرجاری مشکوک‌الوصول
* **تعریف جامع و منطق بانکی:** وامی که بازپرداخت اصل یا سود آن برای یک دوره استاندارد نظارتی (معمولاً بیش از ۹۰ روز) به تاخیر افتاده است. بانک‌ها ملزم هستند شناسایی درآمد تعهدی سود این تسهیلات را متوقف کرده و ذخیره مطالبات مشکوک‌الوصول لحاظ نمایند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan`
  * **فیلد جدول:** `m_loan.is_npa` (مقدار بولی)
  * **گام تسویه پایان روز:** `LoanCOBBusinessStep` و توقف شناسایی تعهدی درآمد در `AccrualActivityBusinessStep`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a loan's `is_npa` flag is evaluated as true, the Fineract Accounting Engine shall cease posting accrued interest to the income statement and shall route any accrual to an off-balance suspense ledger.
    > **فارسی:** تا زمانی که پرچم `is_npa` وام به صورت true ارزیابی می‌شود، موتور حسابداری فاینراکت باید ثبت سود تعهدی در صورت سود و زیان را متوقف نموده و هرگونه محاسبه تعهدی را به حساب انتظامی معلق زیر خط ترازنامه هدایت کند.

---

### ۲.۱۸. اقساط سررسید گذشته و معوق (Overdue)
* **اصطلاح انگلیسی:** Overdue (Overdue Installment / Overdue Amount)
* **معادل استاندارد فارسی:** قسط سررسید گذشته / مطالبات معوق
* **تعریف جامع و منطق بانکی:** قسطی که تاریخ سررسید مقرر قانونی آن فرا رسیده یا سپری شده است، اما وجه آن به طور کامل توسط مدیون تسویه نشده است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `LoanRepaymentScheduleInstallment`
  * **فیلدها:** `duedate < CURRENT_DATE`، `completed_derived = false`
  * **گام پایان روز:** `ApplyChargeToOverdueLoansBusinessStep`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an installment crosses its due date without full settlement, the Fineract Close-of-Business Engine shall mark the installment as overdue and apply the configured overdue penalty charge.
    > **فارسی:** هنگامی که موعد سررسید یک قسط بدون تسویه کامل سپری می‌شود، موتور تسویه پایان روز فاینراکت باید قسط را به عنوان معوق علامت‌گذاری کرده و کارمزد جریمه تأخیر پیکربندی‌شده را اعمال نماید.

---

### ۲.۱۹. روزهای سپری‌شده از سررسید (Days Past Due - DPD)
* **اصطلاح انگلیسی:** Days Past Due (DPD)
* **معادل استاندارد فارسی:** شاخص تأخیر زمانی / تعداد روزهای سپری‌شده از سررسید
* **تعریف جامع و منطق بانکی:** تعداد روزهای تقویمی سپری‌شده از کهنه‌ترین قسط پرداخت‌نشده یک پرونده تسهیلاتی نسبت به تاریخ جاری کاری بانک. شاخص DPD معیار اصلی سنجش سلامت اعتباری پرونده و ورود به طبقات معوق است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan` و `LoanDelinquencyData`
  * **محاسبه در گام:** `UpdateLoanArrearsAgingBusinessStep`
  * **جدول:** `m_loan_arrears_aging.overdue_since_date_derived`، فرمول: $DPD = 	ext{BusinessDate} - 	ext{OldestOverdueDate}$.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Delinquency Engine shall calculate Days Past Due (DPD) as the exact calendar difference between the current business date and the due date of the oldest unpaid overdue installment.
    > **فارسی:** موتور نکول فاینراکت باید شاخص روزهای گذشته از سررسید (DPD) را به عنوان اختلاف دقیق روزهای تقویمی بین تاریخ جاری تجاری و تاریخ سررسید کهنه‌ترین قسط معوق پرداخت‌نشده محاسبه کند.

---

### ۲.۲۰. معوقات انباشته و سررسیدگذشته (Arrears)
* **اصطلاح انگلیسی:** Arrears (Total Arrears Amount)
* **معادل استاندارد فارسی:** معوقات انباشته / بدهی معوق اقساط
* **تعریف جامع و منطق بانکی:** مجموع کل مطالبات مالی بانک (شامل اصل، سود، کارمزدها و جرایم) که موعد سررسید آنها سپری شده ولی وصول نشده است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `Loan`
  * **جدول دیتابیس:** `m_loan_arrears_aging` (فیلدهای `principal_overdue_derived`، `interest_overdue_derived`، `fee_charges_overdue_derived`، `penalty_charges_overdue_derived`، `total_overdue_derived`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Loan Engine shall maintain `total_overdue_derived` as the exact aggregate sum of overdue principal, interest, fee charges, and penalty charges across all delinquent installments.
    > **فارسی:** موتور تسهیلات فاینراکت باید فیلد `total_overdue_derived` را به عنوان مجموع دقیق اصل معوق، سود معوق، کارمزدهای معوق و جرایم معوق در تمامی اقساط سررسیدگذشته نگهداری کند.

---

### ۲.۲۱. طبقه‌بندی زمانی مطالبات (Aging Buckets)
* **اصطلاح انگلیسی:** Aging Buckets (Delinquency Buckets / Aging Ranges)
* **معادل استاندارد فارسی:** طبقه‌بندی سنی مطالبات / بازه‌های زمانی معوقات
* **تعریف جامع و منطق بانکی:** دسته‌بندی مطالبات تسهیلاتی بر مبنای مدت زمان سپری‌شده از سررسید (نظیر جاری: ۰ روز، سررسید گذشته: ۱ الی ۳۰ روز، معوق: ۳۱ الی ۹۰ روز، مشکوک‌الوصول: ۹۱ الی ۱۸۰ روز، سوخت‌شده: بالای ۱۸۰ روز) جهت محاسبه ذخایر عمومی و اختصاصی مطالبات.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.delinquency.domain.DelinquencyBucket` و `DelinquencyRange`
  * **جدول پایگاه داده:** `m_delinquency_bucket`، `m_delinquency_range`
  * **گام تسویه:** `SetLoanDelinquencyTagsBusinessStep`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When the Close-of-Business batch job processes active loans, the Fineract Delinquency Engine shall map each account's DPD to the configured Delinquency Ranges and assign the corresponding classification tag.
    > **فارسی:** هنگامی که جاب دسته‌ای پایان روز وام‌های فعال را پردازش می‌کند، موتور نکول فاینراکت باید شاخص DPD هر حساب را با بازه‌های نکول پیکربندی‌شده تطبیق داده و برچسب طبقه‌بندی متناظر را انتساب دهد.

---

### ۲.۲۲. سوخت مطالبات و حذف از ترازنامه (Write-Off)
* **اصطلاح انگلیسی:** Write-Off (Loan Charge-Off / Bad Debt Write-Off)
* **معادل استاندارد فارسی:** سوخت مطالبات / حذف از ترازنامه به عنوان مطالبات لاوصول
* **تعریف جامع و منطق بانکی:** شناسایی قطعی و حسابداری سوخت تسهیلاتی که وصول آنها غیرممکن تشخیص داده شده است. طی این عملیات، مانده طلب از سرفصل دارایی‌های تسهیلاتی ترازنامه حذف شده و در مقابل حساب ذخیره مطالبات مشکوک‌الوصول بدهکار می‌گردد؛ با این وجود، پرونده از نظر حقوقی مختومه نمی‌شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس:** `LoanWritePlatformService.writeOff`
  * **جدول تراکنش:** `m_loan_transaction` با نوع `LoanTransactionType.WRITE_OFF` (کد ۶).
  * **کد وضعیت پایانی:** `LoanStatus.CLOSED_WRITTEN_OFF` (شناسه عددی ۶۰۱ در `m_loan.loan_status_id`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an authorized officer executes a loan write-off transaction, the Fineract Loan Engine shall zero out remaining asset balances, transition the loan status to `CLOSED_WRITTEN_OFF`, and issue a double-entry journal entry debiting Bad Debt Expense and crediting Loans Receivable.
    > **فارسی:** هنگامی که کارشناس مجاز تراکنش سوخت وام را اجرا می‌کند، موتور تسهیلات فاینراکت باید مانده‌های دارایی باقی‌مانده را صفر نموده، وضعیت وام را به `CLOSED_WRITTEN_OFF` تغییر دهد و سند دوبل بدهکار کردن هزینه مطالبات سوخت‌شده و بستانکار کردن تسهیلات اعطایی را صادر نماید.

---

### ۲.۲۳. وصول مطالبات سوخت‌شده (Recovery)
* **اصطلاح انگلیسی:** Recovery (Bad Debt Recovery Repayment)
* **معادل استاندارد فارسی:** وصول مطالبات سوخت‌شده / بازیافت بدهی‌های معدوم
* **تعریف جامع و منطق بانکی:** ثبت وجوه نقد وصول‌شده از وام‌گیرنده یا از محل تملک وثایق پس از آنکه پرونده وام قبلاً به عنوان سوخت‌شده از ترازنامه کسر گردیده بود. این وجوه مستقیماً به عنوان درآمد غیرعملیاتی بازیافت مطالبات در صورت سود و زیان شناسایی می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس تراکنش:** `LoanTransaction` با نوع `LoanTransactionType.RECOVERY_REPAYMENT` (شناسه عددی ۵).
  * **جدول:** `m_loan_transaction`
  * **اثر حسابداری:** بدهکار شدن موجودی نقد (`Cash`) و بستانکار شدن درآمد وصول مطالبات سوخت‌شده (`Income from Recovery of Written-off Loans`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a loan remains in `CLOSED_WRITTEN_OFF` status, when a recovery repayment is posted, the Fineract Loan Engine shall accept the payment without altering the closed loan status and credit the recovery income GL account.
    > **فارسی:** در حالی که پرونده وام در وضعیت `CLOSED_WRITTEN_OFF` قرار دارد، هنگامی که بازپرداخت وصول مطالبات سوخت‌شده ثبت می‌شود، موتور تسهیلات فاینراکت باید پرداخت را بدون تغییر وضعیت بسته پرونده پذیرفته و حساب درآمد حاصل از وصول مطالبات دفتر کل را بستانکار نماید.

---

### ۲.۲۴. درآمد سرمایه‌شده و کارمزد اعطا (Capitalized Income / Origination Fee)
* **اصطلاح انگلیسی:** Capitalized Income / Origination Fee
* **معادل استاندارد فارسی:** درآمد سرمایه‌شده / کارمزد اعطای افزوده به اصل وام
* **تعریف جامع و منطق بانکی:** کارمزد یا درآمدی که در ابتدای پرداخت وام، به جای کسر نقدی از مشتری، به مبلغ اصل تسهیلات افزوده شده و در طول دوره استهلاک وام همراه با اقساط شناسایی می‌گردد (مطابق با استانداردهای تعهدی IFRS 9).
* **تطبیق فنی در فاینراکت:**
  * **مستندات مرجع:** `07-features.md` (Apache Fineract 1.15.0/1.16.0)
  * **پشتیبانی:** منحصراً در `Progressive Loan Schedules` با `Advanced Payment Allocation Strategy`.
  * **جدول:** `m_loan_charge`، فیلد `is_capitalized = true` و نوع استهلاک `EQUAL_AMORTIZATION`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where capitalized income is configured on a progressive loan product, the Fineract Progressive Loan Engine shall add the fee amount to the disbursed principal base and amortize the income over the repayment schedule.
    > **فارسی:** چنانچه درآمد سرمایه‌شده روی محصول تسهیلات پیش‌رونده پیکربندی شده باشد، موتور تسهیلات پیش‌رونده فاینراکت باید مبلغ کارمزد را به مانده اصل اولیه افزوده و درآمد آن را در طول جدول اقساط مستهلک نماید.

---

### ۲.۲۵. استراتژی پیشرفته تخصیص بازپرداخت (Advanced Payment Allocation Strategy)
* **اصطلاح انگلیسی:** Advanced Payment Allocation Strategy
* **معادل استاندارد فارسی:** استراتژی پیشرفته تخصیص اقساط و تسویه
* **تعریف جامع و منطق بانکی:** سازوکار انعطاف‌پذیر و قاعده پذیری که در زمان واریز هر وجه توسط مشتری، اولویت تخصیص پول به اجزای گوناگون بدهی (جرایم دیرکرد، کارمزدها، سود معوق، سود جاری، اصل معوق، اصل جاری) را بر مبنای قوانین محصول یا اولویت‌های نظارتی تعیین می‌کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.loanproduct.domain.PaymentAllocationOrder`
  * **جدول:** `m_loan_product_payment_allocation_rule`
  * **استراتژی پیش‌فرض:** `AdvancedPaymentAllocationStrategy.java`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a repayment transaction is executed, the Fineract Payment Allocation Processor shall distribute the payment amount across delinquent components strictly adhering to the configured allocation priority rules.
    > **فارسی:** هنگامی که تراکنش بازپرداخت اجرا می‌شود، پردازشگر تخصیص پرداخت فاینراکت باید مبلغ واریزی را دقیقاً مطابق با قواعد اولویت‌بندی پیکربندی‌شده میان مؤلفه‌های بدهی توزیع نماید.

---

### ۲.۲۶. تسهیلات پیش‌رونده (Progressive Loan)
* **اصطلاح انگلیسی:** Progressive Loan (Progressive Schedule Engine)
* **معادل استاندارد فارسی:** موتور تسهیلات پیش‌رونده / نسل جدید محاسبات منعطف وام
* **تعریف جامع و منطق بانکی:** موتور محاسباتی مدرن در فاینراکت که به طور اختصاصی برای پشتیبانی از تسهیلات با نرخ سود روزشمار، پرداخت‌های سرمایه‌شده، چندپرداختی نامنظم و استهلاک داینامیک بدون تکیه بر ساختارهای سنتی صلب طراحی شده است.
* **تطبیق فنی در فاینراکت:**
  * **ماژول مستقل:** `fineract-progressive-loan`
  * **کلاس کلیدی:** `org.apache.fineract.portfolio.loanaccount.domain.ProgressiveLoanScheduleGenerator`
  * **جدول:** `m_loan` با شناسه استراتژی تخصیص متناظر.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a loan is provisioned under the progressive loan schedule model, the Fineract Progressive Loan Module shall recalculate compounding and amortization using exact daily interest accrual models upon every transaction.
    > **فارسی:** چنانچه وامی تحت مدل جدول اقساط پیش‌رونده تعریف شده باشد، ماژول تسهیلات پیش‌رونده فاینراکت باید در زمان هر تراکنش، محاسبات بهره مرکب و استهلاک را با استفاده از مدل‌های دقیق سود روزشمار بازتنظیم کند.

---

## ۳. بخش دوم: حساب‌های پس‌انداز و سپرده‌های سرمایه‌گذاری (Savings & Deposit Accounts Domain)

این بخش دربرگیرنده مفاهیم، قواعد حاکم بر موجودی، توثیق وجه، محاسبات سود دوره‌ای، سپرده‌های مدت‌دار و چرخه‌های رکود حساب در ماژول پس‌انداز فاینراکت است.

---

### ۳.۱. مانده در دسترس و قابل برداشت (Available Balance)
* **اصطلاح انگلیسی:** Available Balance
* **معادل استاندارد فارسی:** مانده در دسترس / موجودی قابل برداشت
* **تعریف جامع و منطق بانکی:** خالص وجهی از حساب سپرده که صاحب حساب می‌تواند در لحظه از طریق برداشت نقدی، انتقال وجه یا چک برداشت کند. این مانده حاصل تفریق مبالغ مسدودشده (Hold/Lien) و حداقل موجودی الزامی از مانده دفتری است:
  $$	ext{Available Balance} = 	ext{Ledger Balance} - 	ext{Hold/Lien Amount} - 	ext{Enforced Minimum Balance}$$
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.savings.domain.SavingsAccount`
  * **جدول پایگاه داده:** `m_savings_account`
  * **متد محاسباتی:** `SavingsAccount.getAvailableBalance()`
  * **فیلد:** محاسبه‌شده به صورت دینامیک بر پایه `account_balance_derived` و `on_hold_funds_derived`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Unwanted Behavior (If-Then)*
  * **گزاره استاندارد:**
    > **English:** If a debit withdrawal request exceeds the calculated Available Balance of the savings account, then the Fineract Savings Engine shall reject the transaction with error code `error.msg.savingsaccount.transaction.insufficient.account.balance`.
    > **فارسی:** چنانچه درخواست برداشت وجه از مانده در دسترس محاسبه‌شده حساب سپرده فراتر رود، موتور سپرده فاینراکت باید تراکنش را با کد خطای `error.msg.savingsaccount.transaction.insufficient.account.balance` رد نماید.

---

### ۳.۲. مانده دفتری و ثبتی (Ledger Balance)
* **اصطلاح انگلیسی:** Ledger Balance (Current Account Balance)
* **معادل استاندارد فارسی:** مانده دفتری / مانده اسمی حساب
* **تعریف جامع و منطق بانکی:** کل موجودی ثبت‌شده در سرخط دفتر کل حساب پس‌انداز که برآیند کلیه واریزها و برداشت‌های قطعی تاریخی تا لحظه جاری است، بدون کسر مسدودی‌ها، چک‌های در جریان وصول یا مبالغ وثیقه.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `SavingsAccount`
  * **جدول دیتابیس:** `m_savings_account`
  * **فیلد ذخیره‌شده:** `account_balance_derived`
  * **تراکنش‌ها:** مجموع واریزها منهای برداشت‌ها در `m_savings_account_transaction`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Savings Engine shall maintain `account_balance_derived` as the exact arithmetic sum of all committed credit transactions minus all committed debit transactions.
    > **فارسی:** موتور سپرده فاینراکت باید فیلد `account_balance_derived` را به عنوان حاصل جمع حسابی دقیق کلیه تراکنش‌های قطعی بستانکار منهای کلیه تراکنش‌های قطعی بدهکار نگهداری کند.

---

### ۳.۳. مانده روزانه (Daily Balance)
* **اصطلاح انگلیسی:** Daily Balance (End-of-Day Balance)
* **معادل استاندارد فارسی:** مانده پایان روز / مانده روزشمار مبنای سود
* **تعریف جامع و منطق بانکی:** مانده خالص دفتری حساب در پایان هر روز تقویمی پس از ثبت تمامی تراکنش‌های آن روز، که به عنوان پایه اصلی فرمول‌های انتساب سود روزشمار سپرده‌ها بکار گرفته می‌شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس:** `SavingsAccountInterestCalculationService`
  * **استراتژی محاسبه:** `DailyBalanceSavingsAccountInterestCalculationStrategy`
  * **جدول:** داده‌های تراکنش در `m_savings_account_transaction` ارزیابی‌شده در تاریخ `transaction_date`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Savings Interest Engine shall compute daily accrued interest based on the finalized End-of-Day balance for each respective calendar day in the interest calculation period.
    > **فارسی:** موتور سود سپرده فاینراکت باید سود تعهدی روزانه را بر اساس مانده نهایی پایان روز برای هر یک از روزهای تقویمی در دوره محاسبه سود محاسبه نماید.

---

### ۳.۴. حداقل مانده الزامی (Minimum Balance)
* **اصطلاح انگلیسی:** Minimum Balance (Minimum Required Balance)
* **معادل استاندارد فارسی:** حداقل مانده الزامی نگهداری حساب / کف موجودی
* **تعریف جامع و منطق بانکی:** کمترین مبلغی که طبق قرارداد افتتاح حساب یا ضوابط بانک باید همواره در حساب سپرده باقی بماند تا حساب فعال مانده یا مشمول دریافت کارمزد جریمه کسر موجودی نگردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `SavingsProduct` و `SavingsAccount`
  * **فیلد دیتابیس:** `m_savings_account.min_required_balance` و `enforce_min_required_balance`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + If-Then)*
  * **گزاره استاندارد:**
    > **English:** Where enforcement of minimum balance is enabled, if a withdrawal causes the ledger balance to drop below `min_required_balance`, then the Fineract Savings Engine shall block the transaction and return an unauthorized balance exception.
    > **فارسی:** چنانچه الزام حداقل موجودی فعال باشد، در صورتی که برداشت موجب شود مانده دفتری از `min_required_balance` کمتر گردد، موتور سپرده فاینراکت باید تراکنش را مسدود نموده و خطای عدم کفایت موجودی را بازگرداند.

---

### ۳.۵. مسدودی و توثیق وجه (Hold Amount / Lien)
* **اصطلاح انگلیسی:** Hold Amount / Account Lien
* **معادل استاندارد فارسی:** مسدودی وجه / توثیق سپرده / قرار بازداشت مالی
* **تعریف جامع و منطق بانکی:** حبس موقت بخشی از مانده حساب به دلایل حقوقی (حکم دادگاه)، ضمانت تسهیلات (وثیقه نقدی وام) یا تضمین صدور ضمانت‌نامه/کارت اعتباری، به طوری که وجه همچنان در مالکیت مشتری است اما حق برداشت از آن سلب شده است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.savings.domain.SavingsAccountCharge` یا مسدودی‌های جدول `m_savings_account_on_hold_funds`.
  * **فیلد حساب:** `m_savings_account.on_hold_funds_derived`
  * **تراکنش‌های مرتبط:** `HOLD_AMOUNT` و `RELEASE_AMOUNT`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a hold command is applied to a savings account, the Fineract Savings Engine shall increment `on_hold_funds_derived` and immediately reduce the Available Balance by the exact hold amount.
    > **فارسی:** هنگامی که دستور مسدودی به حساب پس‌انداز اعمال می‌شود، موتور سپرده فاینراکت باید فیلد `on_hold_funds_derived` را افزایش داده و مانده در دسترس را دقیقاً به میزان مبلغ مسدودی کاهش دهد.

---

### ۳.۶. سپرده سرمایه‌گذاری مدت‌دار (Fixed Deposit)
* **اصطلاح انگلیسی:** Fixed Deposit Account (Term Deposit)
* **معادل استاندارد فارسی:** سپرده سرمایه‌گذاری مدت‌دار / حساب سپرده ثابت
* **تعریف جامع و منطق بانکی:** حسابی بانکی که در آن مشتری مبلغی مشخص را برای دوره‌ای معین (مثلاً ۱، ۲ یا ۵ سال) بدون حق برداشت روزمره تودیع می‌کند و در قبال آن سود ثابتی بالاتر از سپرده‌های کوتاه‌مدت دریافت می‌دارد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.savings.domain.FixedDepositAccount` (وارث از `SavingsAccount`).
  * **جدول پایگاه داده:** `m_savings_account` پیوند به `m_deposit_account_term_and_pre_closure`.
  * **فیلدهای اختصاصی:** `deposit_period`، `deposit_period_frequency_id`، `maturity_amount`، `maturity_date`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a Fixed Deposit reaches its configured maturity date, the Fineract Deposit Subsystem shall transition the account status to `MATURED` and execute the selected auto-rollover or payout instruction.
    > **فارسی:** هنگامی که سپرده مدت‌دار به تاریخ سررسید مقرر می‌رسد، زیرسیستم سپرده فاینراکت باید وضعیت حساب را به `MATURED` تغییر داده و دستورالعمل تمدید خودکار یا پرداخت نهایی را اجرا نماید.

---

### ۳.۷. سپرده اندوخته دوره‌ای (Recurring Deposit)
* **اصطلاح انگلیسی:** Recurring Deposit Account
* **معادل استاندارد فارسی:** سپرده اندوخته دوره‌ای / پس‌انداز اقساطی
* **تعریف جامع و منطق بانکی:** حسابی سرمایه‌گذاری که مشتری متعهد می‌شود به صورت منظم و دوره‌ای (ماهانه) مبلغی معین را واریز نماید تا در تاریخ سررسید کل اصل انباشته به همراه سودهای متعلقه سرمایه‌گذاری را دریافت دارد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.savings.domain.RecurringDepositAccount`
  * **جدول دیتابیس:** `m_deposit_account_recurring_detail`، `m_deposit_account_term_and_pre_closure`.
  * **جدول زمان‌بندی واریز:** `m_deposit_account_recurring_installment`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a recurring installment due date is reached, the Fineract Deposit Subsystem shall register an expected mandatory deposit obligation in the recurring deposit schedule.
    > **فارسی:** هنگامی که تاریخ سررسید قسط اندوخته دوره‌ای فرا می‌رسد، زیرسیستم سپرده فاینراکت باید تعهد واریز اجباری مورد انتظار را در جدول واریزهای سپرده دوره‌ای ثبت نماید.

---

### ۳.۸. واریز و اعمال سود به حساب (Interest Posting)
* **اصطلاح انگلیسی:** Interest Posting
* **معادل استاندارد فارسی:** واریز سود به حساب / ثبت قطعی سود سپرده
* **تعریف جامع و منطق بانکی:** عملیات مالی و حسابداری انتقال سودهای محاسبه‌شده تعهدی (Accrued Interest) به اصل مانده حساب سپرده مشتری، که موجب افزایش مانده دفتری و در دسترس سپرده‌گذار می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس تراکنش:** `SavingsAccountTransaction` با نوع `POST_INTEREST` (نوع تراکنش ۳ در `m_savings_account_transaction`).
  * **گام پایان روز یا جاب:** `PostInterestSavingsAccountJob`
  * **سند دفتر کل:** بدهکار شدن هزینه سود سپرده (`Expense: Interest on Deposits`) و بستانکار شدن حساب سپرده مشتری (`Liability: Savings Account`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When the interest posting period frequency triggers, the Fineract Savings Engine shall capitalize cumulative accrued interest by posting a credit transaction to `m_savings_account_transaction` and updating the ledger balance.
    > **فارسی:** هنگامی که دوره تناوب واریز سود فرا می‌رسد، موتور پس‌انداز فاینراکت باید سود تعهدی تجمعی را با ثبت یک تراکنش بستانکار در `m_savings_account_transaction` سرمایه‌گذاری نموده و مانده دفتری را به‌روزرسانی کند.

---

### ۳.۹. دوره محاسبه سود مرکب (Compounding Period)
* **اصطلاح انگلیسی:** Interest Compounding Period
* **معادل استاندارد فارسی:** دوره محاسبه سود مرکب / فاصله مرکب‌سازی سود
* **تعریف جامع و منطق بانکی:** فاصله‌های زمانی مشخصی (روزانه، ماهانه، فصلی، سالانه) که در پایان هر یک، سود محاسبه‌شده دوره به اصل سرمایه افزوده می‌شود تا در دوره‌های بعد به خود این سود نیز سود تعلق گیرد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.savings.SavingsCompoundingInterestPeriodType`
  * **فیلد:** `m_savings_account.interest_compounding_period_type_enum` (روزانه: ۱، ماهانه: ۴، سالانه: ۶).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where monthly interest compounding is configured, the Fineract Savings Engine shall add accrued unposted interest to the principal base at the close of each calendar month.
    > **فارسی:** چنانچه مرکب‌سازی ماهانه سود پیکربندی شده باشد، موتور پس‌انداز فاینراکت باید سود تعهدی واریزنشده را در پایان هر ماه تقویمی به مبنای اصل سرمایه اضافه نماید.

---

### ۳.۱۰. بستن پیش از موعد سپرده و شکست سود (Premature Closure)
* **اصطلاح انگلیسی:** Premature Closure (Early Withdrawal / Pre-closure)
* **معادل استاندارد فارسی:** بستن پیش از موعد سپرده / شکست سرمایه‌گذاری و جریمه ابطال
* **تعریف جامع و منطق بانکی:** انصراف سپرده‌گذار و برداشت اصل وجه پیش از فرارسیدن تاریخ سررسید نهایی سپرده مدت‌دار، که معمولاً همراه با جریمه شکست نرخ سود (Penal Interest Rate / Rate Reduction) و تعدیل سودهای پرداختی گذشته همراه است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس:** `DepositAccountWritePlatformService.prematureClose`
  * **کد وضعیت حساب:** `SavingsAccountStatusType.PRE_MATURE_CLOSURE` (شناسه عددی ۷۰۰ در `m_savings_account.status_enum`).
  * **محاسبه تعدیل:** معکوس‌سازی سود اضافی پرداختی در جدول `m_savings_account_transaction`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a customer requests premature closure of a fixed deposit, the Fineract Deposit Subsystem shall recompute total interest earned using the reduced pre-closure interest rate and recover excess previously paid interest from the principal payout.
    > **فارسی:** هنگامی که مشتری تقاضای بستن پیش از موعد سپرده مدت‌دار را ارائه می‌دهد، زیرسیستم سپرده فاینراکت باید کل سود کسب‌شده را با استفاده از نرخ سود تقلیل‌یافته بازتنظیم کرده و مابه‌التفاوت سود مازاد قبلی را از اصل پرداختی کسر نماید.

---

### ۳.۱۱. رکود و راکد بودن حساب (Dormancy)
* **اصطلاح انگلیسی:** Account Dormancy (Dormant Account Status)
* **معادل استاندارد فارسی:** راکد بودن حساب / رکود عملیاتی سپرده
* **تعریف جامع و منطق بانکی:** وضعیتی که در آن یک حساب سپرده برای مدتی طولانی و مشخص (بیش از دوره مجاز، مثلاً ۱۲ الی ۲۴ ماه) هیچ‌گونه تراکنش با منشأ مشتری (واریز یا برداشت) را ثبت نکرده باشد. این حساب‌ها جهت جلوگیری از سوءاستفاده‌های مالی مسدود می‌شوند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.savings.domain.SavingsAccountSubStatusEnum`
  * **مقدار فنی:** `SavingsAccountSubStatusEnum.DORMANT` (کد عددی ۲۰۰ در `m_savings_account.sub_status_enum`).
  * **گام شناسایی:** جاب پایان روز `UpdateSavingsDormancyJob`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a savings account is in `DORMANT` sub-status, the Fineract Savings Engine shall reject all automated debit operations initiated by third-party systems until the account is formally reactivated by an authorized teller.
    > **فارسی:** تا زمانی که حساب سپرده در زیروضعیت `DORMANT` قرار دارد، موتور پس‌انداز فاینراکت باید کلیه عملیات‌های برداشت خودکار با مبدا سامانه‌های بیرونی را تا زمان فعال‌سازی رسمی حساب توسط متصدی مجاز رد کند.

---

### ۳.۱۲. انتقال وجوه بلاتکلیف به مراجع قانونی (Escheatment)
* **اصطلاح انگلیسی:** Escheatment (Unclaimed Balances Transfer)
* **معادل استاندارد فارسی:** انتقال وجوه بلاتکلیف و بلاصاحب به خزانه‌داری / مراجع قانونی
* **تعریف جامع و منطق بانکی:** الزام قانونی و مقرراتی انتقال مانده حساب‌های راکدی که سال‌ها مالک آنها مراجعه نکرده است به حساب خزانه‌داری کل کشور یا بانک مرکزی به عنوان اموال بلاصاحب.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `SavingsAccountSubStatusEnum.ESCHEAT` (کد عددی ۳۰۰ در `m_savings_account.sub_status_enum`).
  * **تراکنش حسابداری:** انتقال موجودی از سرفصل بدهی به حساب واسط خزانه‌داری دولتی.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an account remains dormant beyond the statutory dormancy threshold, the Fineract Savings Engine shall mark the account sub-status as `ESCHEAT` and transfer the full outstanding ledger balance to the government treasury payable account.
    > **فارسی:** هنگامی که حسابی فراتر از حد آستانه قانونی در وضعیت راکد باقی بماند، موتور پس‌انداز فاینراکت باید زیروضعیت حساب را به `ESCHEAT` تغییر داده و کل مانده دفتری را به حساب بستانکاران خزانه‌داری دولتی منتقل نماید.

---

### ۳.۱۳. اضافه برداشت (Overdraft)
* **اصطلاح انگلیسی:** Overdraft (Savings Overdraft Facility)
* **معادل استاندارد فارسی:** اضافه برداشت / برداشت مازاد بر موجودی حساب
* **تعریف جامع و منطق بانکی:** تسهیلاتی اعتباری متصل به حساب سپرده جاری که به مشتری اجازه می‌دهد تا سقف اعتباری مشخصی، بیش از موجودی واقعی حساب برداشت نموده و حساب دارای مانده منفی گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `SavingsAccount`
  * **فیلدهای جدول:** `m_savings_account.allow_overdraft = true`، `overdraft_limit`، `nominal_annual_interest_rate_overdraft`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where an overdraft limit is enabled on a savings account, the Fineract Savings Engine shall permit debit transactions up to the authorized negative threshold and accrue daily overdraft interest on the negative balance.
    > **فارسی:** چنانچه سقف اضافه برداشت روی حساب سپرده فعال باشد، موتور پس‌انداز فاینراکت باید تراکنش‌های بدهکار را تا سقف مجاز مانده منفی پذیرفته و سود روزشمار اضافه برداشت را بر مانده منفی محاسبه کند.

---

### ۳.۱۴. زیروضعیت‌های انسداد و محدودیت سپرده (Savings Sub-Status: Blocked / Inactive)
* **اصطلاح انگلیسی:** Savings Account Sub-Status (Blocked / Block Debit / Block Credit)
* **معادل استاندارد فارسی:** زیروضعیت‌های انسداد و محدودیت عملیاتی حساب سپرده
* **تعریف جامع و منطق بانکی:** مکانیزم‌های کنترلی دقیق برای مسدودسازی یک‌طرفه یا دوطرفه حساب‌های فعال بر اساس دستورات قضایی، پولشویی یا سیاست‌های نظارتی.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `SavingsAccountSubStatusEnum`
  * **کدهای عددی:** `BLOCK` (400)، `BLOCK_CREDIT` (500)، `BLOCK_DEBIT` (600).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a savings account is set to `BLOCK_DEBIT` sub-status, the Fineract Savings Engine shall permit inbound credit transactions while strictly blocking all outgoing debit requests.
    > **فارسی:** تا زمانی که حساب سپرده در زیروضعیت `BLOCK_DEBIT` قرار دارد، موتور پس‌انداز فاینراکت باید تراکنش‌های واریزی بستانکار را مجاز شمرده اما تمامی درخواست‌های خروجی بدهکار را اکیداً مسدود نماید.

---

## ۴. بخش سوم: سرفصل‌های دفتر کل و حسابداری مالی بانکی (General Ledger & Financial Accounting Domain)

این بخش دربرگیرنده معماری حسابداری دوطرفه (Double-Entry)، درخت سرفصل‌ها، انواع دارایی و بدهی، روش‌های حسابداری نقدی و تعهدی، و آرتیکل‌های سند حسابداری در ماژول حسابداری فاینراکت است.

---

### ۴.۱. حسابداری دوطرفه و ثبت دوبل (Double-Entry Bookkeeping)
* **اصطلاح انگلیسی:** Double-Entry Bookkeeping (Balanced Financial Entries)
* **معادل استاندارد فارسی:** حسابداری دوطرفه / ثبت دوبل اسناد مالی
* **تعریف جامع و منطق بانکی:** اصل بنیادین و تغییرناپذیر حسابداری مالی که طبق آن هر رویداد مالی باید دست‌کم در دو حساب مختلف اثر بگذارد، به طوری که مجموع مقادیر بدهکار دقیقاً با مجموع مقادیر بستانکار برابر باشد ($\sum 	ext{Debits} = \sum 	ext{Credits}$).
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.accounting.journalentry.domain.JournalEntry`
  * **جدول دیتابیس:** `acc_gl_journal_entry`
  * **سرویس اعتبارسنجی:** `JournalEntryWritePlatformService.validateJournalEntriesAreBalanced`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Unwanted Behavior (If-Then)*
  * **گزاره استاندارد:**
    > **English:** If the sum of debit amounts does not exactly equal the sum of credit amounts for a financial transaction payload, then the Fineract Accounting Engine shall reject the transaction and throw an `AccountingValidationException`.
    > **فارسی:** چنانچه در یک تراکنش مالی، مجموع ارقام بدهکار دقیقاً با مجموع ارقام بستانکار برابر نباشد، موتور حسابداری فاینراکت باید تراکنش را رد کرده و استثنای `AccountingValidationException` صادر کند.

---

### ۴.۲. کدینگ و درخت سرفصل‌های حسابداری (Chart of Accounts - COA)
* **اصطلاح انگلیسی:** Chart of Accounts (COA / GL Hierarchy)
* **معادل استاندارد فارسی:** درخت سرفصل‌های حسابداری / کدینگ حساب‌های دفتر کل
* **تعریف جامع و منطق بانکی:** ساختار طبقه‌بندی سلسله‌مراتبی و کدگذاری‌شده کلیه حساب‌های دفتر کل یک مؤسسه مالی که حساب‌ها را در ۵ طبقه استاندارد (دارایی، بدهی، سرمایه، درآمد و هزینه) سازماندهی می‌کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.accounting.glaccount.domain.GLAccount`
  * **جدول پایگاه داده:** `acc_gl_account`
  * **فیلدهای کلیدی:** `gl_code` (کد یکتای سرفصل)، `name`، `classification_enum` (نوع سرفصل ۱ تا ۵)، `parent_id` (پیوند والد/فرزند درختی)، `manual_journal_entries_allowed`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While a GL account is classified as a header or parent account, the Fineract Accounting Engine shall prohibit direct journal entry postings to that account.
    > **فارسی:** تا زمانی که یک حساب دفتر کل به عنوان حساب سرگروه یا کل تعریف شده است، موتور حسابداری فاینراکت باید ثبت مستقیم اسناد حسابداری به آن حساب را ممنوع نماید.

---

### ۴.۳. دارایی (Asset)
* **اصطلاح انگلیسی:** Asset (GL Account Type: Asset)
* **معادل استاندارد فارسی:** دارایی / منابع اقتصادی متعلق به بانک
* **تعریف جامع و منطق بانکی:** منابع اقتصادی کنترل‌شده توسط بانک که انتظار می‌رود جریان منافع اقتصادی آتی برای مؤسسه ایجاد کند (نظیر موجودی نقد، تسهیلات اعطایی به مشتریان، وثایق تملیکی، اموال ثابت). ماهیت مانده عادی این حساب‌ها **بدهکار** است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.accounting.glaccount.domain.GLAccountType`
  * **مقدار فنی:** `GLAccountType.ASSET` (مقدار عددی: `1` در `classification_enum`).
  * **نمونه حساب‌ها در پرتفوی وام:** `Loan Portfolio` (وام‌های اعطایی جاری)، `Interest Receivable`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall classify loan disbursements as an increase in an ASSET account and record a debit entry against the loan portfolio GL code.
    > **فارسی:** موتور حسابداری فاینراکت باید پرداخت تسهیلات را به عنوان افزایش در حساب دارایی (ASSET) طبقه‌بندی نموده و یک ثبت بدهکار در سرفصل تسهیلات اعطایی دفتر کل درج نماید.

---

### ۴.۴. بدهی (Liability)
* **اصطلاح انگلیسی:** Liability (GL Account Type: Liability)
* **معادل استاندارد فارسی:** بدهی / تعهدات مالی بانک به اشخاص ثالث
* **تعریف جامع و منطق بانکی:** تعهدات ناشی از رویدادهای گذشته مؤسسه که تسویه آنها منجر به خروج منابع اقتصادی می‌شود (نظیر سپرده‌های پس‌انداز مشتریان، استقراض از بانک مرکزی، سود پرداختنی). ماهیت مانده عادی این حساب‌ها **بستانکار** است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `GLAccountType`
  * **مقدار فنی:** `GLAccountType.LIABILITY` (مقدار عددی: `2`).
  * **نمونه حساب‌ها در سپرده‌ها:** `Savings Control Account`، `Customer Deposits`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall classify customer deposit inflows as an increase in a LIABILITY account and record a credit entry against the designated savings control GL code.
    > **فارسی:** موتور حسابداری فاینراکت باید ورود سپرده مشتریان را به عنوان افزایش در حساب بدهی (LIABILITY) طبقه‌بندی کرده و یک ثبت بستانکار در سرفصل معین حساب سپرده پس‌انداز درج نماید.

---

### ۴.۵. حقوق صاحبان سهام و سرمایه (Equity)
* **اصطلاح انگلیسی:** Equity (GL Account Type: Equity / Capital)
* **معادل استاندارد فارسی:** حقوق صاحبان سهام / سرمایه و اندوخته‌ها
* **تعریف جامع و منطق بانکی:** باقیمانده منافع در دارایی‌های مؤسسه پس از کسر تمامی بدهی‌های آن ($	ext{Equity} = 	ext{Assets} - 	ext{Liabilities}$). شامل سرمایه پرداخت‌شده، سود انباشته و اندوخته‌های قانونی است. ماهیت عادی آن **بستانکار** است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `GLAccountType`
  * **مقدار فنی:** `GLAccountType.EQUITY` (مقدار عددی: `3`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall classify opening balance equity and retained earnings under EQUITY accounts with normal credit balance behavior.
    > **فارسی:** موتور حسابداری فاینراکت باید سرمایه اولیه افتتاحیه و سود انباشته را تحت سرفصل‌های حقوق صاحبان سهام (EQUITY) با رفتار بستانکار عادی طبقه‌بندی کند.

---

### ۴.۶. درآمد (Income)
* **اصطلاح انگلیسی:** Income (GL Account Type: Income / Revenue)
* **معادل استاندارد فارسی:** درآمد / عایدات عملیاتی و غیرعملیاتی
* **تعریف جامع و منطق بانکی:** افزایش در منافع اقتصادی طی دوره مالی در قالب ورود یا بهبود دارایی‌ها یا کاهش بدهی‌ها که منجر به افزایش حقوق صاحبان سهام می‌شود (نظیر درآمد سود تسهیلات، کارمزد خدمات بانکی و جرایم تاخیر). ماهیت عادی این حساب‌ها **بستانکار** است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `GLAccountType`
  * **مقدار فنی:** `GLAccountType.INCOME` (مقدار عددی: `4`).
  * **نمونه حساب‌ها:** `Interest Income from Loans`، `Fee Income`، `Penalty Income`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When interest or fee revenue is recognized, the Fineract Accounting Engine shall record a credit entry to the designated INCOME GL account.
    > **فارسی:** هنگامی که درآمد سود یا کارمزد شناسایی می‌شود، موتور حسابداری فاینراکت باید یک آرتیکل بستانکار در حساب دفتر کل درآمد متناظر ثبت نماید.

---

### ۴.۷. هزینه (Expense)
* **اصطلاح انگلیسی:** Expense (GL Account Type: Expense)
* **معادل استاندارد فارسی:** هزینه / مصارف مالی و عملیاتی
* **تعریف جامع و منطق بانکی:** کاهش در منافع اقتصادی طی دوره در قالب خروج یا استهلاک دارایی‌ها یا وقوع بدهی‌ها که موجب کاهش حقوق صاحبان سهام می‌گردد (نظیر هزینه سود سپرده‌ها، هزینه مطالبات مشکوک‌الوصول و هزینه‌های پرسنلی). ماهیت عادی این حساب‌ها **بدهکار** است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `GLAccountType`
  * **مقدار فنی:** `GLAccountType.EXPENSE` (مقدار عددی: `5`).
  * **نمونه حساب‌ها:** `Interest Expense on Deposits`، `Loss on Written-off Loans`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When interest is posted to savings accounts or a loan is written off, the Fineract Accounting Engine shall record a debit entry to the designated EXPENSE GL account.
    > **فارسی:** هنگامی که سود به حساب‌های سپرده واریز می‌شود یا وامی سوخت می‌گردد، موتور حسابداری فاینراکت باید یک آرتیکل بدهکار در حساب دفتر کل هزینه متناظر ثبت کند.

---

### ۴.۸. حسابداری نقدی (Cash-based Accounting)
* **اصطلاح انگلیسی:** Cash-based Accounting
* **معادل استاندارد فارسی:** حسابداری برمبنای نقدی
* **تعریف جامع و منطق بانکی:** روش حسابداری که در آن درآمدها تنها در زمان دریافت واقعی وجه نقد و هزینه‌ها صرفاً در زمان پرداخت واقعی وجه نقد ثبت و در دفاتر شناسایی می‌شوند. هیچ‌گونه سند تعهدی پیش از جابجایی فیزیکی پول صادر نمی‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.accounting.common.AccountingRuleType`
  * **مقدار فنی:** `AccountingRuleType.CASH_BASED` (شناسه عددی: `2`).
  * **رفتار تسهیلات:** عدم صدور اسناد `Accrual` در پایان ماه؛ ثبت سود به بستانکار درآمد صرفاً هنگام وصول قسط.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a loan product is configured with `AccountingRuleType.CASH_BASED`, the Fineract Accounting Engine shall recognize interest income solely upon receipt of actual cash repayments and shall not generate periodic accrual journal entries.
    > **فارسی:** چنانچه محصول وام با `AccountingRuleType.CASH_BASED` پیکربندی شده باشد، موتور حسابداری فاینراکت باید درآمد سود را منحصراً هنگام دریافت فیزیکی بازپرداخت شناسایی نموده و اسناد حسابداری تعهدی دوره‌ای صادر نکند.

---

### ۴.۹. حسابداری تعهدی دوره‌ای (Accrual-based Accounting: Periodic)
* **اصطلاح انگلیسی:** Accrual-based Accounting - Periodic (Periodic Accrual)
* **معادل استاندارد فارسی:** حسابداری تعهدی دوره‌ای / شناسایی تدریجی سود پایان ماه
* **تعریف جامع و منطق بانکی:** استاندارد حسابداری بین‌المللی که در آن درآمدها و هزینه‌ها در دوره‌ای که محقق یا واقع می‌شوند (صرف‌نظر از زمان دریافت یا پرداخت نقد) ثبت می‌گردند. در فاینراکت، سود اقساط به صورت دوره‌ای (معمولاً در پایان هر روز کاری یا پایان ماه توسط جاب COB) محاسبه و ثبت می‌گردد:
  $$	ext{Debit: Interest Receivable (Asset)} \quad 	ext{Credit: Interest Income (Income)}$$
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `AccountingRuleType`
  * **مقدار فنی:** `AccountingRuleType.ACCRUAL_PERIODIC` (شناسه عددی: `3`).
  * **گام تسویه:** `AddPeriodicAccrualEntriesBusinessStep`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + When)*
  * **گزاره استاندارد:**
    > **English:** Where a loan utilizes `AccountingRuleType.ACCRUAL_PERIODIC`, when the daily Close-of-Business batch job runs, the Fineract Accounting Engine shall compute accrued earned interest and post a journal entry debiting Interest Receivable and crediting Interest Income.
    > **فارسی:** چنانچه وامی از `AccountingRuleType.ACCRUAL_PERIODIC` استفاده کند، هنگامی که جاب دسته‌ای پایان روز اجرا می‌شود، موتور حسابداری فاینراکت باید سود تحقق‌یافته تعهدی را محاسبه نموده و سند حسابداری بدهکار شدن سود دریافتنی و بستانکار شدن درآمد سود را ثبت کند.

---

### ۴.۱۰. حسابداری تعهدی آنی و اولیه (Accrual-based Accounting: Upfront)
* **اصطلاح انگلیسی:** Accrual-based Accounting - Upfront
* **معادل استاندارد فارسی:** حسابداری تعهدی اولیه / شناسایی یک‌باره سود در زمان اعطا
* **تعریف جامع و منطق بانکی:** روشی از حسابداری تعهدی که در آن در لحظه پرداخت وام، کل سود پیش‌بینی‌شده برای کل طول عمر تسهیلات در حساب سود دریافتنی ثبت شده و در مقابل حساب درآمد معوق (Deferred Income) یا درآمد کل بستانکار می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `AccountingRuleType`
  * **مقدار فنی:** `AccountingRuleType.ACCRUAL_UPFRONT` (شناسه عددی: `4`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + When)*
  * **گزاره استاندارد:**
    > **English:** Where a loan utilizes `AccountingRuleType.ACCRUAL_UPFRONT`, when the loan is disbursed, the Fineract Accounting Engine shall immediately post the total anticipated interest of the entire repayment schedule to Interest Receivable and Deferred Income.
    > **فارسی:** چنانچه وامی از `AccountingRuleType.ACCRUAL_UPFRONT` استفاده کند، هنگامی که وام پرداخت می‌شود، موتور حسابداری فاینراکت باید فوراً کل سود پیش‌بینی‌شده کل جدول اقساط را در حساب سود دریافتنی و درآمد معوق ثبت نماید.

---

### ۴.۱۱. سند حسابداری و آرتیکل دوبل (Journal Entry)
* **اصطلاح انگلیسی:** Journal Entry (GL Transaction Leg)
* **معادل استاندارد فارسی:** سند حسابداری / ردیف آرتیکل دوبل دفتر کل
* **تعریف جامع و منطق بانکی:** کوچک‌ترین واحد ثبتی در سیستم حسابداری مالی که نمایانگر یک سطر بدهکار یا بستانکار با مبلغ مشخص، تاریخ اعمال، شرح، و ارجاع به تراکنش منشأ (وام، سپرده، دریافت و پرداخت) در دفتر کل است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.accounting.journalentry.domain.JournalEntry`
  * **جدول دیتابیس:** `acc_gl_journal_entry`
  * **فیلدهای کلیدی:** `account_id` (پیوند به سرفصل)، `office_id` (کد شعبه)، `entry_date` (تاریخ سند)، `type_enum` (1=DEBIT, 2=CREDIT)، `amount`، `transaction_id`، `reversed` (پرچم ابطال/برگشت سند)، `loan_transaction_id`، `savings_transaction_id`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall ensure that every committed journal entry contains an immutable audit reference linking back to its triggering portfolio transaction ID.
    > **فارسی:** موتور حسابداری فاینراکت باید تضمین نماید که هر سند حسابداری قطعی‌شده دارای یک شناسه ارجاع ممیزی تغییرناپذیر به تراکنش مبدا پرتفوی متناظر خود باشد.

---

### ۴.۱۲. بدهکار (Debit)
* **اصطلاح انگلیسی:** Debit (Debit Entry / Dr)
* **معادل استاندارد فارسی:** بدهکار / ثبت در ستون بدهکار دفتر کل
* **تعریف جامع و منطق بانکی:** ثبتی در حسابداری که موجب افزایش در حساب‌های دارایی و هزینه، و کاهش در حساب‌های بدهی، سرمایه و درآمد می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.accounting.journalentry.domain.JournalEntryType`
  * **مقدار فنی:** `JournalEntryType.DEBIT` (کد عددی: `1` در `type_enum`، مقدار متنی `"D"`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall assign `type_enum = 1` (DEBIT) to any journal leg that increases an ASSET or EXPENSE balance or decreases a LIABILITY, EQUITY, or INCOME balance.
    > **فارسی:** موتور حسابداری فاینراکت باید مقدار `type_enum = 1` (بدهکار) را به هر آرتیکل سندی که مانده دارایی یا هزینه را افزایش می‌دهد یا مانده بدهی، سرمایه یا درآمد را کاهش می‌دهد، اختصاص دهد.

---

### ۴.۱۳. بستانکار (Credit)
* **اصطلاح انگلیسی:** Credit (Credit Entry / Cr)
* **معادل استاندارد فارسی:** بستانکار / ثبت در ستون بستانکار دفتر کل
* **تعریف جامع و منطق بانکی:** ثبتی در حسابداری که موجب افزایش در حساب‌های بدهی، سرمایه و درآمد، و کاهش در حساب‌های دارایی و هزینه می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `JournalEntryType`
  * **مقدار فنی:** `JournalEntryType.CREDIT` (کد عددی: `2` در `type_enum`، مقدار متنی `"C"`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall assign `type_enum = 2` (CREDIT) to any journal leg that increases a LIABILITY, EQUITY, or INCOME balance or decreases an ASSET or EXPENSE balance.
    > **فارسی:** موتور حسابداری فاینراکت باید مقدار `type_enum = 2` (بستانکار) را به هر آرتیکل سندی که مانده بدهی، سرمایه یا درآمد را افزایش می‌دهد یا مانده دارایی یا هزینه را کاهش می‌دهد، اختصاص دهد.

---

### ۴.۱۴. نگاشت فعالیت‌های مالی (Financial Activity Mapping)
* **اصطلاح انگلیسی:** Financial Activity Mapping (Financial Activity Account)
* **معادل استاندارد فارسی:** نگاشت فعالیت‌های مالی به حساب‌های دفتر کل
* **تعریف جامع و منطق بانکی:** پیکربندی خودکار اتصال رویدادهای سیستمی خاص (نظیر انتقال وجه بین‌بانکی، بازیافت مطالبات سوخت‌شده، واریز نقدی به باجه، تسویه صندوق) به سرفصل‌های معین دفتر کل، به منظور خودکارسازی صدور اسناد بدون دخالت دستی کاربر.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.accounting.financialactivityaccount.domain.FinancialActivityAccount`
  * **جدول دیتابیس:** `acc_financial_activity_account`
  * **کدهای فعالیت مالی:** `financial_activity_type` (100: Fund Source, 200: Payables, 300: Opening Balances, etc.).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Accounting Engine shall resolve standard transactional GL targets through the configured `FinancialActivityAccount` mappings when automated system events execute.
    > **فارسی:** موتور حسابداری فاینراکت باید در زمان اجرای رویدادهای خودکار سامانه‌ای، سرفصل‌های استاندارد دفتر کل را از طریق نگاشت‌های پیکربندی‌شده `FinancialActivityAccount` تعیین نماید.

---

### ۴.۱۵. حساب رابط و واسط معلق (Suspense Account)
* **اصطلاح انگلیسی:** Suspense Account (Clearing / Transit Account)
* **معادل استاندارد فارسی:** حساب واسط / حساب رابط و موقت معلق
* **تعریف جامع و منطق بانکی:** حسابی در دفتر کل که مبالغ تراکنش‌های نامشخص، پایاپای در جریان، خطاهای تراکنشی یا مانده‌های تعیین تکلیف‌نشده به طور موقت در آن نگهداری می‌شود تا پس از بررسی اسناد، به سرفصل قطعی خود منتقل گردد.
* **تطبیق فنی در فاینراکت:**
  * **جدول:** `acc_gl_account` (با مشخصه ویژه `suspense_account = true`).
  * **کاربردها:** واریزهای دسته‌جمعی نامنطبق، انتقال وجه در راه، وجوه بلاتکلیف تراکنش‌های ناموفق کارتخوان.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While an inbound external settlement cannot be definitively attributed to an active customer loan or savings account, the Fineract Accounting Engine shall route the unallocated credit leg to the configured Suspense GL Account.
    > **فارسی:** تا زمانی که یک تسویه ورودی بیرونی نتواند به صورت قطعی به حساب وام یا سپرده مشتری منتسب گردد، موتور حسابداری فاینراکت باید آرتیکل بستانکار تخصیص‌نیافته را به حساب واسط معلق دفتر کل هدایت نماید.

---

### ۴.۱۶. تجدید ارزیابی دارایی‌ها و تعهدات ارزی (Revaluation)
* **اصطلاح انگلیسی:** Currency Revaluation (Unrealized Foreign Exchange Gain/Loss)
* **معادل استاندارد فارسی:** تجدید ارزیابی ارزی / شناسایی سود و زیان تسعیر ارز تحقق‌نیافته
* **تعریف جامع و منطق بانکی:** به‌روزرسانی ارزش دفتری دارایی‌ها و بدهی‌های ارزی بانک در پایان دوره‌های مالی بر مبنای آخرین نرخ برابری ارز اعلامی بانک مرکزی، و شناسایی سود یا زیان ناشی از نوسانات تسعیر ارز.
* **تطبیق فنی در فاینراکت:**
  * **جدول و سرویس:** `acc_gl_journal_entry` با پارامترهای تسعیر نرخ و ثبت در سرفصل‌های تسعیر ارز (FX Gain/Loss).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When currency revaluation executes at period end, the Fineract Accounting Engine shall recalculate the base-currency equivalent of foreign currency balances and book unrealized exchange gain or loss to the general ledger.
    > **فارسی:** هنگامی که تجدید ارزیابی ارزی در پایان دوره مالی اجرا می‌شود، موتور حسابداری فاینراکت باید معادل ارزی مانده‌ها به ارز پایه را مجدداً محاسبه نموده و سود یا زیان تسعیر محقق‌نشده را در دفتر کل ثبت کند.

---

## ۵. بخش چهارم: کارمزدها، جرایم و سازوکارهای مالیاتی (Charges, Fees & Taxes Domain)

این بخش دربرگیرنده معماری مالی، انواع کارمزدها و جرایم، متدهای محاسبه مبلغ ثابت و درصدی، کارمزدهای سرمایه‌شده، مالیات‌های تکلیفی و گروه‌های مالیاتی در ماژول‌های Charge و Tax فاینراکت است.

---

### ۵.۱. کارمزد اعطا و پرداخت تسهیلات (Disbursal Fee)
* **اصطلاح انگلیسی:** Disbursal Fee (Loan Origination Fee / Disbursement Charge)
* **معادل استاندارد فارسی:** کارمزد اعطا و پرداخت تسهیلات / هزینه کارشناسی پرونده وام
* **تعریف جامع و منطق بانکی:** مبلغی که در زمان پرداخت اولیه وجه وام به عنوان هزینه ارزیابی اعتبار، کارشناسی، تشکیل پرونده و خدمات اداری وضع می‌گردد. این کارمزد معمولاً یا مستقیماً از اصل پرداختی کسر می‌گردد، یا نقداً دریافت می‌شود، یا به صورت سرمایه‌شده به اصل وام اضافه می‌شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.charge.domain.Charge`
  * **جدول پایگاه داده:** `m_charge` و جدول ارتباطی `m_loan_charge`
  * **کلاس اینام زمان اعمال:** `org.apache.fineract.portfolio.charge.domain.ChargeTimeType`
  * **مقدار فنی:** `ChargeTimeType.DISBURSEMENT` (شناسه عددی: `1` در ستون `charge_time_enum`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a loan disbursement transaction is posted, the Fineract Charge Engine shall deduct any associated `DISBURSEMENT` charges from the payout amount unless configured as a capitalized fee.
    > **فارسی:** هنگامی که تراکنش پرداخت وام ثبت می‌گردد، موتور کارمزد فاینراکت باید کلیه کارمزدهای مرتبط با زمان پرداخت (`DISBURSEMENT`) را از مبلغ پرداختی ناخالص کسر نماید، مگر آنکه به صورت کارمزد سرمایه‌شده پیکربندی شده باشد.

---

### ۵.۲. کارمزد با تاریخ سررسید مشخص (Specified Due Date Charge)
* **اصطلاح انگلیسی:** Specified Due Date Charge
* **معادل استاندارد فارسی:** کارمزد با موعد پرداخت معین / هزینه خدمات زمان‌بندی‌شده
* **تعریف جامع و منطق بانکی:** نوعی از کارمزد که نه در زمان پرداخت وام و نه منطبق بر اقساط عادی، بلکه در یک تاریخ تقویمی صریح و معین در طول حیات پرونده (مثلاً کارمزد بازدید سالانه از پروژه، کارمزد تمدید بیمه‌نامه وثیقه) سررسید و مطالبه می‌شود.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `ChargeTimeType`
  * **مقدار فنی:** `ChargeTimeType.SPECIFIED_DUE_DATE` (شناسه عددی: `2`).
  * **فیلد جدول:** `m_loan_charge.due_for_collection_as_of_date`
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When the current business date reaches the specified due date of an active loan charge, the Fineract Charge Engine shall demand payment and include the charge in the portfolio arrears calculation.
    > **فارسی:** هنگامی که تاریخ جاری کسب‌وکار به تاریخ سررسید مشخص کارمزد فعال وام می‌رسد، موتور کارمزد فاینراکت باید وجه آن را مطالبه نموده و کارمزد را در محاسبات معوقات پرونده لحاظ نماید.

---

### ۵.۳. کارمزد وابسته به هر قسط (Installment Fee)
* **اصطلاح انگلیسی:** Installment Fee (Recurring Installment Charge)
* **معادل استاندارد فارسی:** کارمزد قسطی / هزینه خدمات اضافه به هر قسط
* **تعریف جامع و منطق بانکی:** کارمزدی دوره‌ای که همراه با سررسید هر یک از اقساط وام محاسبه شده و به مبلغ پرداختی همان قسط افزوده می‌شود (مانند حق بیمه ماهانه قسط یا هزینه خدمات پیامکی دوره‌ای).
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `ChargeTimeType`
  * **مقدار فنی:** `ChargeTimeType.INSTALLMENT_FEE` (شناسه عددی: `8`).
  * **جدول:** `m_loan_repayment_schedule.fee_charges_amount` و `m_loan_installment_charge`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Loan Schedule Generator shall append configured `INSTALLMENT_FEE` amounts to each respective repayment period's total installment obligation in `m_loan_repayment_schedule`.
    > **فارسی:** موتور تولید اقساط فاینراکت باید مبالغ پیکربندی‌شده کارمزد قسطی (`INSTALLMENT_FEE`) را به کل تعهدات بازپرداختی هر یک از دوره‌های قسط در `m_loan_repayment_schedule` بیفزاید.

---

### ۵.۴. جریمه تأخیر تأدیه و خسارت دیرکرد (Overdue Penalty)
* **اصطلاح انگلیسی:** Overdue Penalty (Penal Charge / Overdue Fee)
* **معادل استاندارد فارسی:** جریمه تأخیر تأدیه / خسارت دیرکرد اقساط معوق
* **تعریف جامع و منطق بانکی:** مبلغ تنبیهی و بازدارنده‌ای که به دلیل عدم پرداخت اقساط در موعد مقرر بر مشتری تحمیل می‌شود. این جریمه به عنوان ابزار انگیزشی و جبران هزینه ریسک اعتباری، بر مبنای مبلغ قسط معوق یا تعداد روزهای تأخیر محاسبه می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `ChargeTimeType`
  * **مقدار فنی:** `ChargeTimeType.OVERDUE_INSTALLMENT` (شناسه عددی: `9`).
  * **پرچم جریمه بودن:** `m_charge.is_penalty = true`.
  * **گام پایان روز:** `ApplyChargeToOverdueLoansBusinessStep`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an installment becomes overdue past the allowed grace threshold, the Fineract Close-of-Business Engine shall apply the configured `OVERDUE_INSTALLMENT` penalty charge and book it under penalty receivables.
    > **فارسی:** هنگامی که قسطی فراتر از آستانه تنفس مجاز معوق می‌گردد، موتور تسویه پایان روز فاینراکت باید کارمزد جریمه تأخیر (`OVERDUE_INSTALLMENT`) را اعمال کرده و آن را در حساب دریافتنی‌های جریمه ثبت نماید.

---

### ۵.۵. کارمزد مبلغ ثابت (Flat Fee)
* **اصطلاح انگلیسی:** Flat Fee Calculation Type
* **معادل استاندارد فارسی:** کارمزد با مبلغ اسمی ثابت
* **تعریف جامع و منطق بانکی:** کارمزدی که مبلغ آن به صورت یک عدد قطعی و ثابت پولی تعیین شده و هیچ‌گونه وابستگی به مبلغ وام، نرخ سود، مانده بدهی یا مدت زمان قرارداد ندارد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.portfolio.charge.domain.ChargeCalculationType`
  * **مقدار فنی:** `ChargeCalculationType.FLAT` (شناسه عددی: `1` در ستون `charge_calculation_enum`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a charge is configured with `ChargeCalculationType.FLAT`, the Fineract Charge Engine shall assess the exact configured numeric amount without applying percentage multipliers.
    > **فارسی:** چنانچه کارمزدی با `ChargeCalculationType.FLAT` پیکربندی شده باشد، موتور کارمزد فاینراکت باید دقیقاً مبلغ عددی معین‌شده را بدون اعمال ضرایب درصدی مطالبه کند.

---

### ۵.۶. کارمزد تناسبی و درصدی (Pro-rata Fee / Percentage Charge)
* **اصطلاح انگلیسی:** Pro-rata Fee (Percentage of Amount / Interest)
* **معادل استاندارد فارسی:** کارمزد نسبی / کارمزد درصدی بر مبنای اصل یا سود
* **تعریف جامع و منطق بانکی:** کارمزدی که بر مبنای ضریبی از یک متغیر مالی دیگر در پرونده (مثلاً درصدی از کل اصل وام، درصدی از سود قسط، یا متناسب با تعداد روزهای باقیمانده) محاسبه می‌شود:
  $$\text{Fee} = \text{Base Amount} \times \text{Percentage Rate}$$
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `ChargeCalculationType`
  * **مقادیر فنی:**
    * `PERCENT_OF_AMOUNT` (شناسه ۲)
    * `PERCENT_OF_AMOUNT_AND_INTEREST` (شناسه ۳)
    * `PERCENT_OF_INTEREST` (شناسه ۴)
    * `PERCENT_OF_DISBURSEMENT_AMOUNT` (شناسه ۵).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a charge is configured with `ChargeCalculationType.PERCENT_OF_AMOUNT`, the Fineract Charge Engine shall compute the charge amount as the defined percentage multiplied by the relevant principal calculation base.
    > **فارسی:** چنانچه کارمزدی با `ChargeCalculationType.PERCENT_OF_AMOUNT` تنظیم شده باشد، موتور کارمزد فاینراکت باید مبلغ کارمزد را حاصلضرب درصد مصوب در مبنای اصل بدهی متناظر محاسبه نماید.

---

### ۵.۷. مالیات تکلیفی سپرده‌ها (Withholding Tax)
* **اصطلاح انگلیسی:** Withholding Tax (WHT on Interest Income)
* **معادل استاندارد فارسی:** مالیات تکلیفی مکسوره از سود سپرده
* **تعریف جامع و منطق بانکی:** مالیات قانونی که بانک به عنوان عامل وصول موظف است در هنگام پرداخت یا واریز سود به حساب مشتری، از مبلغ ناخالص سود کسر نموده و مستقیماً به سازمان امور مالیاتی کشور واریز کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.tax.domain.TaxGroup`
  * **جدول دیتابیس:** `m_tax_group` و `m_savings_account.tax_group_id`
  * **فیلد حساب سپرده:** `withhold_tax = true`.
  * **اثر حسابداری:** بدهکار شدن هزینه سود، بستانکار شدن مالیات پرداختنی به دولت و واریز مابه‌التفاوت خالص به حساب مشتری.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + When)*
  * **گزاره استاندارد:**
    > **English:** Where withholding tax is enabled on a savings account, when interest posting executes, the Fineract Tax Engine shall calculate and deduct the statutory withholding tax percentage before crediting the net interest to the client account.
    > **فارسی:** چنانچه مالیات تکلیفی روی حساب سپرده فعال باشد، هنگامی که عملیات واریز سود اجرا می‌گردد، موتور مالیاتی فاینراکت باید پیش از واریز سود خالص به حساب مشتری، درصد مالیات تکلیفی قانونی را محاسبه و کسر نماید.

---

### ۵.۸. گروه مالیاتی (Tax Group)
* **اصطلاح انگلیسی:** Tax Group
* **معادل استاندارد فارسی:** گروه مالیاتی / بسته تجمیعی نرخ‌های مالیاتی
* **تعریف جامع و منطق بانکی:** مجموعه‌ای ساختاریافته از یک یا چند جزء مالیاتی (مانند مالیات بر ارزش افزوده عمومی به علاوه عوارض شهرداری) که به صورت یکپارچه بر یک محصول بانکی یا کارمزد اعمال می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.tax.domain.TaxGroup`
  * **جدول پایگاه داده:** `m_tax_group` و جدول نگاشت `m_tax_group_mappings`
  * **فیلدهای کلیدی:** `id`، `name`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Tax Engine shall resolve the total cumulative tax percentage by aggregating all active component rates assigned to the designated `TaxGroup` for the transaction value date.
    > **فارسی:** موتور مالیاتی فاینراکت باید نرخ کل مالیات تجمعی را از طریق جمع کلیه مؤلفه‌های فعال منتسب به `TaxGroup` معین برای تاریخ اعمال تراکنش محاسبه کند.

---

### ۵.۹. جزء و مؤلفه مالیاتی (Tax Component)
* **اصطلاح انگلیسی:** Tax Component
* **معادل استاندارد فارسی:** جزء مالیاتی / نرخ مستقل مالیات یا عوارض
* **تعریف جامع و منطق بانکی:** عنصر پایه‌ای و منفرد محاسبات مالیاتی با درصد مشخص و سرفصل حسابداری مجزا در دفتر کل (مانند ۹٪ مالیات بر ارزش افزوده یا ۳٪ عوارض سلامت).
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.portfolio.tax.domain.TaxComponent`
  * **جدول دیتابیس:** `m_tax_component`
  * **فیلدهای کلیدی:** `percentage` (درصد نرخ)، `debit_account_id`، `credit_account_id` (پیوند به سرفصل دفتر کل بستانکاران مالیاتی).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Tax Engine shall route the calculated monetary portion of each distinct `TaxComponent` to its specifically configured general ledger payable account.
    > **فارسی:** موتور مالیاتی فاینراکت باید بخش ریالی محاسبه‌شده مربوط به هر `TaxComponent` مجزا را به حساب بستانکاران دفتر کل اختصاصی پیکربندی‌شده برای آن هدایت نماید.

---

### ۵.۱۰. کارمزد سرمایه‌شده به اصل تسهیلات (Capitalized Fee)
* **اصطلاح انگلیسی:** Capitalized Fee (Capitalized Loan Charge)
* **معادل استاندارد فارسی:** کارمزد سرمایه‌شده / هزینه ادغام‌شده در اصل بدهی وام
* **تعریف جامع و منطق بانکی:** کارمزدی که مشتری در زمان پرداخت آن را به صورت نقدی نمی‌پردازد، بلکه مبلغ آن به مانده اصل بدهی اضافه شده و استهلاک آن در قالب اقساط آتی تسهیلات انجام می‌گیرد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `LoanCharge`
  * **فیلد جدول:** `m_loan_charge.is_capitalized = true`
  * **پشتیبانی:** تسهیلات ماژول `fineract-progressive-loan` با استراتژی بازپرداخت پیشرفته.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Where (Optional Feature)*
  * **گزاره استاندارد:**
    > **English:** Where a loan charge is flagged as capitalized, the Fineract Loan Engine shall append the charge sum directly into the outstanding principal balance and amortize it through regular installment payments.
    > **فارسی:** چنانچه کارمزد وامی به عنوان سرمایه‌شده نشانه‌گذاری شود، موتور تسهیلات فاینراکت باید مبلغ کارمزد را مستقیماً به مانده اصل بدهی بیفزاید و آن را از طریق بازپرداخت‌های منظم اقساط مستهلک کند.

---

## ۶. بخش پنجم: عملیات پایان روز و موتور تسویه دسته‌ای (Close of Business - COB & Core Operations Domain)

این بخش دربرگیرنده معماری پردازش‌های سنگین پایان روز، زنجیره گام‌های تجاری، قفل‌گذاری حساب، تسویه درون‌خطی، تقویم کاری و پیشروی تاریخ کسب‌وکار در ماژول `fineract-cob` است.

---

### ۶.۱. تاریخ کسب‌وکار و تقویم تجاری (Business Date)
* **اصطلاح انگلیسی:** Business Date (Operational Date vs. COB Date)
* **معادل استاندارد فارسی:** تاریخ تجاری و عملیاتی بانک / تاریخ رسمی کارگزاری
* **تعریف جامع و منطق بانکی:** تاریخ منطقی که کلیه عملیات بانکی، سندزدن‌ها و ارزش‌گذاری تراکنش‌ها بر مبنای آن ثبت می‌شود و کاملاً مستقل از تاریخ ساعت تقویمی سرور فیزیکی (System Clock) است. این امر به بانک امکان می‌دهد تا پیش از اتمام کلیه محاسبات روز، روز کاری را تغییر ندهد یا در محیط‌های آزمایشی، زمان را شبیه‌سازی کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.infrastructure.businessdate.domain.BusinessDate`
  * **جدول دیتابیس:** `m_business_date`
  * **انواع تاریخ:** `BusinessDateType.BUSINESS_DATE` (تاریخ عملیات جاری روزانه)، `BusinessDateType.COB_DATE` (تاریخ روزی که عملیات پایان روز بر مبنای آن در جریان است).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Platform shall utilize the configured `BusinessDateType.BUSINESS_DATE` rather than the host operating system clock as the authoritative timestamp for all domain calculations and financial transactions.
    > **فارسی:** پلتفرم فاینراکت باید تاریخ پیکربندی‌شده `BusinessDateType.BUSINESS_DATE` را به جای ساعت سیستم‌عامل میزبان به عنوان مرجع معتبر زمانی برای تمامی محاسبات دامنه و تراکنش‌های مالی بکار گیرد.

---

### ۶.۲. شناسایی تعهدی پایان روز (Day-End Accrual)
* **اصطلاح انگلیسی:** Day-End Accrual (Daily Accrual Posting)
* **معادل استاندارد فارسی:** شناسایی تعهدی درآمد سود در پایان روز / بستن تعهدی روزانه
* **تعریف جامع و منطق بانکی:** عملیات دسته‌ای پایان روز کاری که در آن سهم سود یک روز از کل مانده تسهیلات جاری به دقت محاسبه شده و سند شناسایی درآمد تعهدی در دفاتر ثبت می‌گردد تا ترازنامه و صورت سود و زیان همواره تصویر دقیقی از بازده سرمایه ارائه دهند.
* **تطبیق فنی در فاینراکت:**
  * **گام تجاری COB:** `org.apache.fineract.cob.loan.AddPeriodicAccrualEntriesBusinessStep` و `AccrualActivityBusinessStep`.
  * **جدول سند:** `acc_gl_journal_entry` با ارجاع به `LoanTransaction` نوع `ACCRUAL` (کد ۸).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When the Close-of-Business day-end accrual step executes, the Fineract Batch Subsystem shall calculate one day of earned interest for every active accrual-based loan and post the resulting journal entries to the ledger.
    > **فارسی:** هنگامی که گام محاسبه تعهدی پایان روز تسویه اجرا می‌شود، زیرسیستم دسته‌ای فاینراکت باید سود تحقق‌یافته یک روز را برای کلیه وام‌های تعهدی فعال محاسبه نموده و اسناد حسابداری حاصل را در دفتر کل ثبت نماید.

---

### ۶.۳. پردازش جبرانی تسویه معوق (COB Catch-Up)
* **اصطلاح انگلیسی:** COB Catch-Up Mode (Multi-Day Batch Catch-Up)
* **معادل استاندارد فارسی:** پردازش تسویه جبرانی / به‌روزرسانی زنجیره‌ای روزهای تسویه‌نشده
* **تعریف جامع و منطق بانکی:** وضعیتی که سامانه بانکی به دلیل قطعی سرورها، تعطیلات متوالی طولانی، یا ارتقای سیستم برای چند روز متوالی عملیات پایان روز را اجرا نکرده است. موتور در این حالت چرخه‌های تسویه پایان روز را به صورت پیاپی به ازای هر روز عقب‌مانده اجرا می‌کند تا تاریخ تسویه به تاریخ جاری برسد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس:** `org.apache.fineract.cob.loan.LoanCOBCatchUpService`
  * **جدول:** ارزیابی ستون `last_closed_business_date` در جدول `m_loan` در برابر `COB_DATE`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *State-Driven*
  * **گزاره استاندارد:**
    > **English:** While the last closed business date lags behind the target operational date, the Fineract COB Catch-Up Service shall execute consecutive Close-of-Business processing cycles until all intermediate business dates are sequentially closed.
    > **فارسی:** تا زمانی که تاریخ آخرین روز بسته‌شده از تاریخ عملیاتی هدف عقب‌تر باشد، سرویس تسویه جبرانی فاینراکت باید چرخه‌های متوالی عملیات پایان روز را تا زمانی که کلیه تاریخ‌های میانی به ترتیب بسته شوند اجرا کند.

---

### ۶.۴. تسویه درون‌خطی و بلادرنگ حساب (Inline COB)
* **اصطلاح انگلیسی:** Inline COB (Inline Catch-Up on Transaction)
* **معادل استاندارد فارسی:** تسویه درون‌خطی پایان روز / همگام‌سازی بلادرنگ حساب حین تراکنش
* **تعریف جامع و منطق بانکی:** قابلیتی نوآورانه که طی آن اگر مشتری به شعبه مراجعه کند و بخواهد روی حسابی که عملیات پایان روز دیروز روی آن هنوز به اتمام نرسیده است تراکنشی ثبت کند، سیستم ابتدا به صورت بلادرنگ و درون‌خطی، محاسبات تسویه تا روز جاری را برای همان حساب انجام می‌دهد و سپس تراکنش مشتری را بدون معطلی پردازش می‌کند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس فیلتر وب:** `org.apache.fineract.cob.loan.LoanCOBApiFilter`
  * **سرویس اجرایی:** `InlineLoanCOBExecution.java`
  * **نوع قفل موقت:** `LockOwner.LOAN_INLINE_COB_PROCESSING` در جدول `m_loan_account_locks`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (While + When)*
  * **گزاره استاندارد:**
    > **English:** While a target loan account is behind the current business date, when an incoming write API command is intercepted, the Fineract Loan COB Filter shall execute Inline COB for that account before releasing the request to the portfolio command handler.
    > **فارسی:** در حالی که یک حساب وام هدف از تاریخ جاری کسب‌وکار عقب‌تر است، هنگامی که یک دستور تغییراتی API رهگیری می‌شود، فیلتر تسویه پایان روز فاینراکت باید پیش از ارسال درخواست به پردازشگر دستورات، عملیات تسویه درون‌خطی را برای آن حساب اجرا نماید.

---

### ۶.۵. قفل انحصاری سطح حساب (Account Lock: Hard Lock vs Soft Lock)
* **اصطلاح انگلیسی:** Account Lock (Loan Account Lock / Hard Lock)
* **معادل استاندارد فارسی:** قفل انحصاری سطح حساب / ممانعت از همزمانی در تسویه
* **تعریف جامع و منطق بانکی:** مکانیزمی جهت جلوگیری از دستکاری و ثبت همزمان تراکنش‌های مالی توسط کاربران یا کانال‌های الکترونیکی روی پرونده‌ای که در همان لحظه توسط جاب تسویه دسته‌ای پایان روز در حال محاسبه سود و تغییر مانده است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.cob.loan.LoanAccountLock`
  * **جدول پایگاه داده:** `m_loan_account_locks`
  * **مالکان قفل (`lock_owner`):** `LOAN_COB_CHUNK_PROCESSING`، `LOAN_INLINE_COB_PROCESSING`.
  * **واکنش به درخواست همزمان:** بازگرداندن وضعیت **HTTP 409 Conflict** با خطای `error.msg.loan.locked`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Unwanted Behavior (If-Then)*
  * **گزاره استاندارد:**
    > **English:** If a write transaction is submitted for a loan that is currently registered in `m_loan_account_locks`, then the Fineract API Gateway shall immediately reject the request with HTTP 409 Conflict and error message `error.msg.loan.locked`.
    > **فارسی:** چنانچه یک تراکنش تغییری برای وامی ارسال شود که هم‌اکنون در `m_loan_account_locks` ثبت شده است، درگاه API فاینراکت باید بلافاصله درخواست را با وضعیت HTTP 409 Conflict و پیام خطای `error.msg.loan.locked` رد کند.

---

### ۶.۶. تقویم تعطیلات رسمی و غیرکاری (Holiday Calendar)
* **اصطلاح انگلیسی:** Holiday Calendar (Public & Bank Holidays)
* **معادل استاندارد فارسی:** تقویم تعطیلات بانکی و روزهای غیرکاری
* **تعریف جامع و منطق بانکی:** تعریف رسمی روزهای تعطیل عمومی، مذهبی و ملی که در آنها شعب بانک تعطیل بوده و سررسید اقساط یا پرداخت‌ها نباید در آن روزها واقع شوند.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.organisation.holiday.domain.Holiday`
  * **جدول پایگاه داده:** `m_holiday` و جدول روزهای کاری هفته `m_working_days`.
  * **وضعیت‌های تعطیلات:** `from_date`، `to_date`، `rescheduling_type`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Calendar Engine shall validate generated repayment dates against active records in `m_holiday` and `m_working_days` for the applicable office branch.
    > **فارسی:** موتور تقویم فاینراکت باید تاریخ‌های بازپرداخت تولیدشده را در برابر رکوردهای فعال در `m_holiday` و `m_working_days` برای شعبه مربوطه اعتبارسنجی کند.

---

### ۶.۷. تغییر سررسید در روزهای تعطیل (Reschedule on Holiday)
* **اصطلاح انگلیسی:** Repayment Rescheduling on Holidays
* **معادل استاندارد فارسی:** انتقال سررسید اقساط در تعطیلات رسمی
* **تعریف جامع و منطق بانکی:** ضابطه خودکاری که تعیین می‌کند در صورتی که سررسید قسطی با یک روز تعطیل رسمی مصادف شد، تاریخ سررسید به چه روزی منتقل گردد: اولین روز کاری بعد (Next Working Day)، روز کاری قبل (Previous Working Day) یا روز جلسه بعدی.
* **تطبیق فنی در فاینراکت:**
  * **کلاس اینام:** `org.apache.fineract.organisation.holiday.domain.RescheduleType`
  * **مقادیر:** `NEXT_WORKING_DAY`، `PREVIOUS_WORKING_DAY`، `SAME_DAY`.
  * **فیلد:** `m_holiday.rescheduling_type` و `m_working_days.repayment_rescheduling_enum`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (Where + When)*
  * **گزاره استاندارد:**
    > **English:** Where a repayment schedule installment falls upon an official holiday, when the calendar validation executes, the Fineract Loan Schedule Generator shall shift the installment due date to the next available working day in accordance with the configured rescheduling policy.
    > **فارسی:** چنانچه سررسید یک قسط جدول بازپرداخت بر یک روز تعطیل رسمی منطبق شود، هنگامی که اعتبارسنجی تقویمی اجرا می‌گردد، موتور تولید اقساط فاینراکت باید تاریخ سررسید قسط را مطابق با خط‌مشی انتقال پیکربندی‌شده به اولین روز کاری مجاز بعدی منتقل نماید.

---

### ۶.۸. زنجیره گام‌های تجاری تسویه (Batch Business Steps)
* **اصطلاح انگلیسی:** Batch Business Steps (COB Step Pipeline)
* **معادل استاندارد فارسی:** زنجیره گام‌های کسب‌وکاری پردازش پایان روز
* **تعریف جامع و منطق بانکی:** توالی استاندارد و مرتب‌شده‌ای از عملیات منطقی و محاسباتی که باید بدون نقص و به ترتیب قطعی در پایان روز روی حساب‌ها اعمال شوند (شامل اعمال جرایم دیرکرد، محاسبه مجدد سود، پایش معوقات، طبقه‌بندی سنی، الصاق برچسب نکول و صدور اسناد تعهدی).
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت JPA:** `org.apache.fineract.cob.domain.BatchBusinessStep`
  * **جدول پایگاه داده:** `m_batch_business_steps`
  * **فیلدهای کلیدی:** `job_name`، `step_name`، `step_order`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract COB Orchestrator shall invoke domain processing steps strictly following the ascending numerical sequence of `step_order` configured in `m_batch_business_steps`.
    > **فارسی:** ارکستراتور تسویه پایان روز فاینراکت باید گام‌های پردازشی دامنه را دقیقاً مطابق با توالی عددی صعودی `step_order` پیکربندی‌شده در `m_batch_business_steps` فراخوانی نماید.

---

### ۶.۹. پارتیشن‌بندی توزیع‌شده چانک‌ها (Remote Partitioning)
* **اصطلاح انگلیسی:** Remote Partitioning (Distributed Spring Batch Partitioning)
* **معادل استاندارد فارسی:** پارتیشن‌بندی توزیع‌شده چانک‌های پردازش تسویه
* **تعریف جامع و منطق بانکی:** قابلیت اجرای موازی و توزیع‌شده محاسبات میلیون‌ها حساب وام در زمان محدود شبانه بین چندین گره سرور کارگر (Worker Nodes) با استفاده از صف‌های پیام Kafka یا ActiveMQ، جهت جلوگیری از گلوگاه‌های عملکردی و تضمین اتمام تسویه پیش از بازگشایی صبحگاهی شعب.
* **تطبیق فنی در فاینراکت:**
  * **کلاس‌های ارکستراسیون:** `LoanCOBPartitioner`، `LoanCOBManagerConfiguration`، `LoanCOBWorkerConfiguration`.
  * **تنظیمات صف:** کانال خروجی Spring Integration، تفکیک شناسه‌ها به بسته‌های چندصدتایی (`fineract.cob.partition-size`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When the master COB job initiates, the Fineract Loan Partitioner shall divide the qualified loan population into discrete partitions and dispatch them across distributed worker channels for concurrent execution.
    > **فارسی:** هنگامی که جاب اصلی تسویه پایان روز آغاز می‌شود، پارتیشن‌کننده تسهیلات فاینراکت باید جامعه وام‌های واجد شرایط را به بخش‌های مجزا تقسیم کرده و آنها را جهت پردازش همزمان به کانال‌های کارگر توزیع‌شده ارسال نماید.

---

## ۷. بخش ششم: بستر پلتفرم، احراز هویت، امنیت و حاکمیت سیستم (Platform, Identity & Governance Domain)

این بخش دربرگیرنده معماری چندمستأجری، الگوی CQRS، سازوکارهای نظارت چهارچشمی (Maker-Checker)، کلیدهای تکرارناپذیری تراکنش (Idempotency)، ممیزی و الگوی صندوق خروجی تراکنشی (Transactional Outbox) در زیرساخت فاینراکت است.

---

### ۷.۱. مستأجر نرم‌افزاری و ایزولاسیون داده‌ها (Tenant)
* **اصطلاح انگلیسی:** Tenant (Multi-Tenancy / Isolated Database per Tenant)
* **معادل استاندارد فارسی:** مستأجر نرم‌افزاری / محیط مستقل چندمستأجری
* **تعریف جامع و منطق بانکی:** یک موجودیت حقوقی، بانک، یا مؤسسه مالی مستقل که در یک زیرساخت نرم‌افزاری و کلاستر اشتراکی میزبانی می‌شود، اما پایگاه داده، جداول، حساب‌های کاربری، تنظیمات مالی و اسناد حسابداری آن به طور ۱۰۰٪ از سایر مستأجرین ایزوله است.
* **تطبیق فنی در فاینراکت:**
  * **کلاس کانتکست:** `org.apache.fineract.infrastructure.core.domain.FineractPlatformTenant`
  * **سرویس مسیریابی:** `TenantAwareRoutingDataSource`
  * **هدر الزامی API:** `Fineract-Platform-TenantId`
  * **جدول کاتالوگ مرکزی:** `tenants` در پایگاه داده مستقل `fineract_tenants`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Multi-Tenant Gateway shall route every incoming HTTP request exclusively to the isolated database connection pool resolved from the mandatory `Fineract-Platform-TenantId` header.
    > **فارسی:** درگاه چندمستأجری فاینراکت باید هر درخواست ورودی HTTP را منحصراً به استخر اتصال پایگاه داده ایزوله‌شده‌ای که بر اساس هدر اجباری `Fineract-Platform-TenantId` تعیین می‌شود، هدایت نماید.

---

### ۷.۲. کاربر پیشنهاددهنده دستور (Maker)
* **اصطلاح انگلیسی:** Maker (Initiating Operator)
* **معادل استاندارد فارسی:** پیشنهاددهنده دستور / کاربر ایجادکننده تراکنش
* **تعریف جامع و منطق بانکی:** کاربر باجه، متصدی تسهیلات یا کارشناسی که درخواست اولیه انجام یک عملیات تغییردهنده وضعیت (نظیر ثبت وام، پرداخت وجه، لغو بدهی یا ایجاد حساب) را در سامانه ایجاد می‌کند، اما اختیار تایید نهایی و اثرگذاری حسابداری آن را ندارد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `org.apache.fineract.useradministration.domain.AppUser`
  * **جدول دستورات معلق:** `m_portfolio_command_source`
  * **فیلد:** `maker_id` (کلید خارجی به `m_appuser`) و `madeon_date`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an operator submits a command requiring maker-checker approval, the Fineract Command Subsystem shall persist the payload into `m_portfolio_command_source` with the operator's ID recorded in `maker_id` and status set to `100` (PENDING).
    > **فارسی:** هنگامی که یک متصدی دستوری نیازمند تصویب ناظر را ثبت می‌کند، زیرسیستم دستورات فاینراکت باید بسته داده را در `m_portfolio_command_source` با ثبت شناسه متصدی در `maker_id` و تنظیم وضعیت روی `100` (در انتظار تایید) ذخیره نماید.

---

### ۷.۳. کاربر ناظر و تاییدکننده (Checker)
* **اصطلاح انگلیسی:** Checker (Approving Supervisor)
* **معادل استاندارد فارسی:** تاییدکننده دستور / ناظر تصویب‌کننده تراکنش
* **تعریف جامع و منطق بانکی:** سرپرست شعبه، مدیر اعتبارات یا ناظر ارشدی که صلاحیت بررسی فنی و حقوقی دستور پیشنهادی ثبت‌شده توسط کاربر Maker را داشته و با صدور تاییدیه (Approve) یا رد (Reject)، به عملیات اعتبار نهایی می‌بخشد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس کنترلر:** `org.apache.fineract.commands.api.MakercheckersApiResource`
  * **مجوز امنیتی:** دسترسی به مجوز `<TASK>_CHECKER` یا `CHECKER_SUPER_USER`.
  * **جدول و فیلد:** `m_portfolio_command_source.checker_id` و `checkedon_date`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When an authorized supervisor approves a pending command via `/v1/makercheckers/{id}`, the Fineract Command Subsystem shall record `checker_id`, update status to `200` (APPROVED), and trigger domain write execution.
    > **فارسی:** هنگامی که ناظر مجاز یک دستور معلق را از طریق اندپوینت `/v1/makercheckers/{id}` تایید می‌کند، زیرسیستم دستورات فاینراکت باید شناسه ناظر را در `checker_id` ثبت کرده، وضعیت را به `200` (تاییدشده) ارتقا دهد و اجرای عملیات در دامنه را کلید بزند.

---

### ۷.۴. اصل نظارت چهارچشمی و تفکیک وظایف (Segregation of Duties - 4-Eyes)
* **اصطلاح انگلیسی:** Segregation of Duties / 4-Eyes Principle
* **معادل استاندارد فارسی:** تفکیک وظایف / اصل کنترل چهارچشمی
* **تعریف جامع و منطق بانکی:** اصل امنیتی و کنترلی بنیادین در بانکداری که تضمین می‌کند هیچ کاربری نمی‌تواند به تنهایی یک تراکنش مالی حساس را ایجاد و خودش آن را تایید نهایی کند ($\text{Maker} \neq \text{Checker}$). این اصل مانع از بروز تقلب، کلاهبرداری و خطای انسانی در نظام بانکی می‌گردد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس سرویس اعتبارسنجی:** `PortfolioCommandSourceWritePlatformServiceImpl`
  * **بررسی عدم تطابق:** مقایسه شناسه کاربر جاری با رکورد ذخیره‌شده:
    ```java
    if (commandSource.getMaker().getId().equals(currentUser.getId())) {
        throw new GeneralPlatformDomainRuleException("error.msg.command.maker.checker.same.user", "Maker and Checker cannot be the same user.");
    }
    ```
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Unwanted Behavior (If-Then)*
  * **گزاره استاندارد:**
    > **English:** If the approving checker user ID matches the original maker user ID of a command, then the Fineract Security Gateway shall reject the approval and throw an `ActionNotPermittedException` with message `error.msg.command.maker.checker.same.user`.
    > **فارسی:** چنانچه شناسه کاربر تاییدکننده (Checker) با شناسه کاربر ایجادکننده اولیه (Maker) یک دستور یکسان باشد، درگاه امنیتی فاینراکت باید تاییدیه را رد کرده و استثنای عدم صلاحیت با پیام `error.msg.command.maker.checker.same.user` صادر نماید.

---

### ۷.۵. کلید تکرارناپذیری تراکنش (Idempotency Key)
* **اصطلاح انگلیسی:** Idempotency Key (Idempotent Execution Guarantee)
* **معادل استاندارد فارسی:** کلید یکتایی تراکنش / تضمین عدم اجرای تکراری دستورات
* **تعریف جامع و منطق بانکی:** شناسه یکتا و منحصر‌به‌فردی (معمولاً در فرمت UUIDv4) که کلاینت یا سامانه پرداخت همراه با درخواست ارسال می‌کند تا در صورت بروز قطعی شبکه و ارسال مجدد بسته، سرور مانع از اجرای مجدد تراکنش (نظیر دو بار کسر قسط یا دو بار پرداخت وام) شده و همان نتیجه درخواست قبلی را بازگرداند.
* **تطبیق فنی در فاینراکت:**
  * **ماژول مستقل:** `fineract-command`
  * **کلاس حل‌کننده:** `org.apache.fineract.commands.service.IdempotencyKeyResolver`
  * **هدر استاندارد درخواست:** `Idempotent-Key: <UUID>`
  * **جدول پایگاه داده:** ستون `idempotency_key` در `m_portfolio_command_source`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Complex (While + When)*
  * **گزاره استاندارد:**
    > **English:** Where an `Idempotent-Key` header is provided, when a request with a previously processed key is received, the Fineract Command Subsystem shall return the cached HTTP response payload without re-executing the underlying business logic.
    > **فارسی:** چنانچه هدر `Idempotent-Key` ارائه شده باشد، هنگامی که درخواستی با کلید پردازش‌شده پیشین دریافت می‌شود، زیرسیستم دستورات فاینراکت باید پاسخ کَش‌شده قبلی را بدون اجرای مجدد منطق تجاری بازگرداند.

---

### ۷.۶. بسته‌بندی و پوشش دستور در CQRS (Command Wrapper)
* **اصطلاح انگلیسی:** Command Wrapper (CQRS Command DTO Encapsulation)
* **معادل استاندارد فارسی:** بسته‌بندی دستور / کپسوله‌سازی زمینه فرمان در معماری CQRS
* **تعریف جامع و منطق بانکی:** شیء داده‌ای استانداردی که تمامی متاداده‌های یک درخواست تغییر وضعیت بانکی—شامل نام موجودیت هدف (`LOAN`، `SAVINGSACCOUNT`)، نام اقدام (`DISBURSE`، `REPAYMENT`)، شناسه موجودیت، متن خام جیسون و بستر امنیتی—را کپسوله کرده و آن را در خط لوله پردازشی انتقال می‌دهد.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `org.apache.fineract.commands.domain.CommandWrapper`
  * **سازنده:** `CommandWrapperBuilder`
  * **جدول ذخیره:** `m_portfolio_command_source` (فیلدهای `action_name`، `entity_name`، `command_as_json`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Command Subsystem shall encapsulate all HTTP write requests into an immutable `CommandWrapper` instance prior to routing through security validation and domain execution handlers.
    > **فارسی:** زیرسیستم دستورات فاینراکت باید تمامی درخواست‌های تغییری HTTP را پیش از هدایت به اعتبارسنجی امنیتی و پردازشگرهای دامنه، در یک شیء تغییرناپذیر `CommandWrapper` کپسوله نماید.

---

### ۷.۷. ردیابی و لاگ ممیزی عملیات (Audit Trail)
* **اصطلاح انگلیسی:** Audit Trail (Historical System Audit Logging)
* **معادل استاندارد فارسی:** ردیابی ممیزی / لاگ‌برداری قانونی و غیرقابل انکار عملیات
* **تعریف جامع و منطق بانکی:** سوابق تغییرناپذیر سیستمی شامل هویت کاربر اقدام‌کننده، آدرس آی‌پی، تاریخ و زمان دقیق، مقادیر اولیه و نهایی داده‌ها، و نتیجه عملیات، به منظور پاسخگویی در بازرسی‌های مالی، دادگاه‌ها و ممیزی‌های انطباق نظارتی.
* **تطبیق فنی در فاینراکت:**
  * **کلاس موجودیت:** `org.apache.fineract.commands.domain.Audit`
  * **سرویس بازخوانی:** `AuditReadPlatformService`
  * **اندپوینت دسترسی:** `GET /v1/audits`
  * **جدول دیتابیس:** `m_portfolio_command_source` (فیلدهای `maker_id`، `madeon_date`، `checker_id`، `checkedon_date`، `command_as_json`).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Platform shall permanently record the user identity, client IP, precise timestamp, and JSON modification payload for every processed write command into the immutable audit repository.
    > **فارسی:** پلتفرم فاینراکت باید هویت کاربر، آدرس IP کلاینت، برچسب زمانی دقیق، و بسته تغییراتی JSON را برای تمامی دستورات تغییری پردازش‌شده به صورت دائمی در مخزن تغییرناپذیر ممیزی ثبت کند.

---

### ۷.۸. ثبت مبتنی بر رویدادها (Event Sourcing)
* **اصطلاح انگلیسی:** Event Sourcing (State Derivation from Event Sequence)
* **معادل استاندارد فارسی:** منبع‌دهی رویدادمحور / بازسازی وضعیت از توالی رویدادها
* **تعریف جامع و منطق بانکی:** الگویی که بر مبنای آن وضعیت جاری یک حساب بانکی (مانده، اقساط معوق، سود روزشمار) به عنوان حاصل جمع جبری و زمانی سلسله‌ای از رویدادهای مالی تغییرناپذیر (تراکنش‌های واریز، برداشت، کارمزد و استهلاک) به دست می‌آید، نه صرفاً به عنوان یک فیلد مجزا.
* **تطبیق فنی در فاینراکت:**
  * **فیلدهای مشتق‌شده:** فیلدهای با پسوند `_derived` در تمامی جداول اصلی (مانند `account_balance_derived` در `m_savings_account`، `principal_amount_outstanding_derived` در `m_loan`).
  * **رویدادهای مبنا:** رکوردهای افزایشی در `m_loan_transaction` و `m_savings_account_transaction`.
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Ubiquitous*
  * **گزاره استاندارد:**
    > **English:** The Fineract Portfolio Engine shall compute all cumulative balance fields ending in `_derived` by replaying the chronological sequence of committed transaction events.
    > **فارسی:** موتور پرتفوی فاینراکت باید کلیه فیلدهای مانده تجمعی با پسوند `_derived` را از طریق بازخوانی توالی زمانی رویدادهای تراکنشی قطعی‌شده محاسبه نماید.

---

### ۷.۹. صندوق خروجی تراکنشی (Transactional Outbox)
* **اصطلاح انگلیسی:** Transactional Outbox Pattern
* **معادل استاندارد فارسی:** الگوی صندوق خروجی تراکنشی / انتشار تضمین‌شده رخدادهای مالی
* **تعریف جامع و منطق بانکی:** الگوی تضمین ثبات داده‌ها در معماری میکروسرویس و توزیع‌شده بانکی، که طی آن تغییر داده‌ها در پایگاه داده محلی و پیام رویداد ارسالی به سایر سیستم‌ها (مانند سیستم کشف تقلب، سامانه پیامک یا بانکداری باز) در یک تراکنش واحد ACID درون جدول دیتابیس ثبت شده و سپس توسط یک پردازه پس‌زمینه به صف‌های Kafka یا JMS ارسال می‌شود.
* **تطبیق فنی در فاینراکت:**
  * **ماژول:** `fineract-provider` و `fineract-avro-schemas`
  * **کلاس سرویس:** `ExternalEventService`
  * **جدول پایگاه داده:** `m_external_event`
  * **فیلدهای کلیدی:** `type` (نام کامل رویداد)، `schema`، `data` (بسته باینری فرمت Avro)، `status` (`TO_BE_SENT` -> `SENT`)، `idempotency_key`، `aggregate_root_id` (کلید پارتیشن Kafka).
* **قاعده استاندارد EARS:**
  * **الگوی نحوی:** *Event-Driven*
  * **گزاره استاندارد:**
    > **English:** When a domain state transition commits, the Fineract Event Subsystem shall write an Avro-serialized event record into `m_external_event` within the same database transaction boundary before dispatching it to external brokers.
    > **فارسی:** هنگامی که یک گذار حالت در دامنه نهایی می‌شود، زیرسیستم رویدادهای فاینراکت باید پیش از ارسال رویداد به کارگزاران خارجی، یک رکورد رویداد سریال‌شده بر مبنای Avro را درون همان مرز تراکنش پایگاه داده در `m_external_event` بنویسد.

---

## ۸. بخش هفتم: قواعد شفاف‌سازی و رفع ابهام بین‌ماژولی (Cross-Module Disambiguation Rules)

در فرایند مهندسی معکوس و استخراج نیازمندی‌های EARS، تشابه ظاهری واژگان می‌تواند به خطاهای فاحش معنایی منجر شود. قواعد این بخش به عنوان احکام الزام‌آور (Binding Semantic Rules) جهت تفکیک دقیق مفاهیم هم‌پوشان یا مبهم تدوین شده‌اند:

---

### ۸.۱. قاعده اول: تفکیک پرداخت وام (Disbursal) از بازپرداخت اقساط (Payment / Repayment)
* **ریشه ابهام:** در زبان انگلیسی و حتی محاورات بانکی، از واژه عام "Payment" گاهی برای پرداخت وجه به مشتری و گاهی برای پرداخت قسط توسط مشتری استفاده می‌شود.
* **حکم الزام‌آور معنایی:**
  * **Loan Disbursal (اعطا و پرداخت تسهیلات):** خروج وجه از بانک به نفع وام‌گیرنده که دارایی وام (`m_loan`) را فعال کرده و تراز دارایی تسهیلات را افزایش می‌دهد. در متون EARS منحصراً باید از فعل `disburse` و عبارت `loan disbursement` استفاده شود.
  * **Loan Repayment (بازپرداخت قسط / واریزی مشتری):** ورود وجه از مشتری به بانک جهت استهلاک اصل، سود، کارمزد یا جریمه. در متون EARS منحصراً باید از `repay` یا `repayment transaction` استفاده شود.
* **جدول مقایسه تطبیقی:**

| مشخصه مقایسه | پرداخت وام (Disbursal) | بازپرداخت اقساط (Repayment) |
| :--- | :--- | :--- |
| **جهت جریان نقد** | خروج نقد از بانک به مشتری (Outflow) | ورود نقد از مشتری به بانک (Inflow) |
| **تراکنش متناظر فاینراکت** | `LoanTransactionType.DISBURSEMENT` (کد ۱) | `LoanTransactionType.REPAYMENT` (کد ۲) |
| **اثر بر مانده بدهی** | ایجاد یا افزایش `principal_amount_outstanding_derived` | کاهش `principal_amount_outstanding_derived` |
| **عبارت استاندارد EARS** | `When a loan disbursement is executed...` | `When a repayment transaction is posted...` |

---

### ۸.۲. قاعده دوم: تفکیک سود تعهدی (Accrued Interest) از سود/درآمد سرمایه‌شده (Capitalized Interest / Income)
* **ریشه ابهام:** هر دو مفهوم نمایانگر سود وام هستند، اما اثر ترازنامه‌ای و نحوه استهلاک آنها کاملاً متفاوت است.
* **حکم الزام‌آور معنایی:**
  * **Accrued Interest (سود تعهدی):** سود کارکرده روزانه که در قالب درآمد در دفاتر شناسایی شده اما هنوز وصول نشده است و به مانده اصل وام افزوده نمی‌شود، بلکه به عنوان طلب جاری سود در حساب `m_loan.interest_outstanding_derived` و `Interest Receivable` باقی می‌ماند.
  * **Capitalized Interest / Income (سود یا درآمد سرمایه‌شده):** سودی که محاسبه شده و مستقیماً به **اصل وام (Principal)** افزوده می‌شود و مبنای اصل بدهی مشتری را افزایش می‌دهد.
* **جدول مقایسه تطبیقی:**

| مشخصه مقایسه | سود تعهدی (Accrued Interest) | سود/درآمد سرمایه‌شده (Capitalized Interest) |
| :--- | :--- | :--- |
| **اثر بر سرفصل اصل بدهی** | هیچ اثری ندارد (اصل وام ثابت می‌ماند) | اصل وام (`principal_amount`) مستقیماً افزایش می‌یابد |
| **سرفصل بدهکار دفتر کل** | سود دریافتنی (`Interest Receivable` - دارایی جاری) | مانده تسهیلات اعطایی (`Loan Portfolio` - دارایی بلندمدت) |
| **نوع تراکنش در فاینراکت** | `LoanTransactionType.ACCRUAL` (کد ۸) | `LoanTransactionType.CAPITALIZED_INTEREST` / کارمزد |
| **عبارت استاندارد EARS** | `...shall accrue earned interest without modifying principal.` | `...shall append capitalized amount to principal base.` |

---

### ۸.۳. قاعده سوم: تفکیک کارمزد خدماتی (Fee) از جریمه تنبیهی (Penalty) و مفهوم عام شارژ (Charge)
* **ریشه ابهام:** در جداول فاینراکت، هر دو مفهوم تحت جدول مشترک `m_charge` تعریف شده‌اند، اما ماهیت مالی و حقوقی آنها مجزاست.
* **حکم الزام‌آور معنایی:**
  * **Charge (شارژ):** ابرمفهوم سیستمی در فاینراکت که هرگونه تعهد مالی غیر از اصل و سود را شامل می‌شود.
  * **Fee (کارمزد خدمات):** مابه‌ازای خدمات اداری، صدور کارت یا ارزیابی فنی که به صورت مشروع و قراردادی دریافت می‌شود (`is_penalty = false`).
  * **Penalty (جریمه تأخیر تأدیه):** مبلغ تنبیهی ناشی از نقض عهد و قصور در پرداخت اقساط در سررسید (`is_penalty = true`).
* **جدول مقایسه تطبیقی:**

| مشخصه مقایسه | کارمزد خدمات (Fee) | جریمه تأخیر (Penalty) |
| :--- | :--- | :--- |
| **فلسفه وضع** | مابه‌ازای ارائه خدمات اداری و بانکی | تنبیه انضباطی و جبران ریسک عدم پرداخت |
| **زمان ایجاد** | زمان پرداخت وام یا مقاطع قراردادی مشخص | پس از سررسید قسط و انقضای مهلت تنفس |
| **پرچم در دیتابیس** | `m_charge.is_penalty = false` | `m_charge.is_penalty = true` |
| **عبارت استاندارد EARS** | `...shall assess the configured service fee...` | `...shall apply overdue penalty charges...` |

---

### ۸.۴. قاعده چهارم: تفکیک سوخت مطالبات (Write-Off) از تسویه قهری (Foreclosure) و تسویه زودهنگام (Pre-closure)
* **ریشه ابهام:** هر سه رویداد می‌توانند منجر به خاتمه زودتر از موعد پرونده وام شوند، اما پیامدهای حقوقی و ثبتی بسیار متفاوتی دارند.
* **حکم الزام‌آور معنایی:**
  * **Write-Off (سوخت حسابداری مطالبات):** اقدام یک‌جانبه بانک برای پاک‌سازی ترازنامه از تسهیلات غیرقابل وصول با بدهکار کردن حساب ذخیره و بستن پرونده در وضعیت `CLOSED_WRITTEN_OFF`. حق پیگیری حقوقی بانک در خارج از ترازنامه باقی است.
  * **Foreclosure (تسویه اجباری قهری):** به اجرا گذاردن قرارداد و وثایق توسط بانک جهت دریافت اصل مطالبات به دلیل تخلف مشتری؛ سودهای آتی حذف و وام با تسویه نهایی بسته می‌شود.
  * **Early Repayment / Pre-closure (تسویه زودهنگام داوطلبانه):** تسویه کامل وام توسط مشتری با اراده خود پیش از موعد مقرر، معمولاً همراه با تخفیف سودهای آتی و بستن پرونده در وضعیت `CLOSED_OBLIGATIONS_MET`.

---

### ۸.۵. قاعده پنجم: تفکیک مانده در دسترس (Available Balance) از مانده دفتری (Ledger Balance) و مانده روزشمار (Daily Balance)
* **ریشه ابهام:** در ماژول سپرده‌ها، استفاده از واژه کلی "Balance" بدون پیشوند مشخص می‌تواند باعث صدور چک بی‌محل یا مسدودسازی اشتباه شود.
* **حکم الزام‌آور معنایی:**
  * **Ledger Balance:** کل موجودی دفتری تاریخی در `m_savings_account.account_balance_derived`.
  * **Available Balance:** موجودی واقعی قابل برداشت پس از کسر مسدودی‌ها (`on_hold_funds_derived`) و حداقل مانده الزامی. اعتبارسنجی برداشت‌ها **منحصراً** باید بر پایه Available Balance انجام گیرد.
  * **Daily Balance:** مانده نهایی در لحظه پایان روز که **منحصراً** مبنای محاسبه سود روزشمار قرار می‌گیرد.

---

### ۸.۶. قاعده ششم: تفکیک حسابداری نقدی (Cash) از تعهدی دوره‌ای (Periodic Accrual) و تعهدی آنی (Upfront Accrual)
* **ریشه ابهام:** انتخاب متد حسابداری در سطح محصول (`m_product_loan.accounting_type`) کل زنجیره اسناد دفتر کل را متحول می‌کند.
* **حکم الزام‌آور معنایی:**
  * در **Cash-based**، هیچ سند سود تعهدی در پایان روز صادر نمی‌شود؛ بستانکار شدن درآمد سود فقط در لحظه واریز نقدی قسط انجام می‌گردد.
  * در **Periodic Accrual**، سود هر روز/ماه به بستانکار حساب درآمد و بدهکار حساب سود دریافتنی ثبت شده، و هنگام واریز قسط، حساب سود دریافتنی بستانکار می‌شود.
  * در **Upfront Accrual**، کل سود جدول اقساط در لحظه پرداخت وام به حساب سود دریافتنی بدهکار و به درآمد معوق بستانکار می‌گردد.

---

### ۸.۷. قاعده هفتم: تفکیک قفل انحصاری COB (Account Lock) از توثیق و مسدودی سپرده (Account Hold / Lien)
* **ریشه ابهام:** هر دو مکانیزم با مسدودسازی تراکنش سر و کار دارند اما در سطوح معماری و اهداف متفاوتی عمل می‌کنند.
* **حکم الزام‌آور معنایی:**
  * **COB Account Lock:** یک قفل موقت فنی چندثانیه‌ای/چنددقیقه‌ای در جدول `m_loan_account_locks` جهت ممانعت از تداخل جاب‌های دسته‌ای پایان روز با درخواست‌های برخط API. بازگشت خطای فنی HTTP 409 Conflict.
  * **Account Hold / Lien:** مسدودی حقوقی یا وثیقه‌ای پایدار مبلغی معین در جدول `m_savings_account_on_hold_funds` که برای ماه‌ها یا سال‌ها مانع برداشت مشتری از مانده سپرده خود می‌شود.

---

### ۸.۸. قاعده هشتم: تفکیک تفکیک وظایف (Segregation of Duties) از منع خودتأییدی (Self-Approval Prohibition)
* **ریشه ابهام:** مفاهیم Maker-Checker و کنترل دسترسی در ادبیات امنیتی گاهی یکسان انگاشته می‌شوند.
* **حکم الزام‌آور معنایی:**
  * **Segregation of Duties (تفکیک نقش‌ها):** تضمین اینکه کاربر ایجادکننده نقش Maker و کاربر تاییدکننده نقش Checker را در ماتریس دسترسی دارا هستند.
  * **Self-Approval Prohibition (منع قطعی خودتأییدی):** یک قید قطعی دامنه در کد که حتی اگر یک کاربر ارشد (Superuser) دارای هر دو مجوز Maker و Checker باشد، سیستم باید مانع تایید دستوری شود که شناسه کاربر ثبت‌کننده آن با کاربر تاییدکننده برابر است (`maker_id != checker_id`).

---

### ۸.۹. قاعده نهم: تفکیک تسهیلات پیش‌رونده (Progressive Loan) از تسهیلات با جدول اقساط کلاسیک (Classic Schedule)
* **ریشه ابهام:** هر دو مدل در فاینراکت وام اعطا می‌کنند، اما موتورهای محاسباتی کاملاً مجزا دارند.
* **حکم الزام‌آور معنایی:**
  * **Classic Schedule:** متکی بر موتور `LoanScheduleGenerator`، اقساط با روش‌های صلب سنتی ماهانه، عدم پشتیبانی از درآمد سرمایه‌شده مدرن.
  * **Progressive Loan:** متکی بر ماژول مستقل `fineract-progressive-loan`، الگوریتم‌های دقیق روزشمار، استراتژی تخصیص پیشرفته اقساط (`AdvancedPaymentAllocationStrategy`) و پشتیبانی کامل از کارمزدهای سرمایه‌شده (`Capitalized Income`).

---

## ۹. بخش هشتم: ماتریس جامع نگاشت، کلاس‌ها، جداول و الگوهای EARS (Comprehensive Traceability Matrix)

جدول زیر نمای جامع و استنادی کلیه اصطلاحات تحلیل‌شده در این واژه‌نامه را جهت سهولت ارجاع تیم‌های مهندسی معکوس ارائه می‌دارد:

| # | اصطلاح انگلیسی (English Term) | معادل مصوب فارسی | دامنه تخصصی | موجودیت متناظر JPA | جدول پایگاه داده | الگوی پیش‌فرض EARS |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| ۱ | Principal | اصل تسهیلات | Lending | `Loan` | `m_loan` | Ubiquitous / State-Driven |
| ۲ | Interest | سود تسهیلات | Lending | `Loan` / `Installment` | `m_loan_repayment_schedule` | Event-Driven |
| ۳ | Repayment Schedule | جدول بازپرداخت اقساط | Lending | `LoanRepaymentScheduleInstallment` | `m_loan_repayment_schedule` | Event-Driven |
| ۴ | Equal Installments | استهلاک با اقساط مساوی | Lending | `AmortizationMethod` | `m_loan` (`amortization_method_enum=0`) | Optional Feature |
| ۵ | Equal Principal | استهلاک با اصل مساوی | Lending | `AmortizationMethod` | `m_loan` (`amortization_method_enum=1`) | Optional Feature |
| ۶ | Flat Interest Method | روش سود ثابت اسمی | Lending | `InterestMethod` | `m_loan` (`interest_method_enum=0`) | Optional Feature |
| ۷ | Declining Balance | سود بر مبنای مانده نزولی | Lending | `InterestMethod` | `m_loan` (`interest_method_enum=1`) | Optional Feature |
| ۸ | Daily Interest Period | دوره محاسبه سود روزانه | Lending | `InterestCalculationPeriodMethod` | `m_loan` (`interest_calc_period_enum=0`) | Optional Feature |
| ۹ | Same as Repayment Period | دوره محاسبه سود هم‌گام | Lending | `InterestCalculationPeriodMethod` | `m_loan` (`interest_calc_period_enum=1`) | Optional Feature |
| ۱۰ | Grace on Principal | دوره تنفس در اصل وام | Lending | `Loan` | `m_loan.grace_on_principal_periods` | Optional Feature |
| ۱۱ | Grace on Interest | دوره تنفس در سود وام | Lending | `Loan` | `m_loan.grace_on_interest_periods` | Optional Feature |
| ۱۲ | Moratorium | امهال قانونی بازپرداخت | Lending | `Loan` / `LoanRescheduleRequest` | `m_loan` | State-Driven |
| ۱۳ | Tranche / Multi-Disbursal | اعطای مرحله‌ای تسهیلات | Lending | `LoanDisbursementDetails` | `m_loan_disbursement_detail` | Complex (Where + When) |
| ۱۴ | Restructure / Reschedule | تجدید ساختار و استمهال | Lending | `LoanRescheduleRequest` | `m_loan_reschedule_request` | Event-Driven |
| ۱۵ | Foreclosure | تسویه اجباری قهری وام | Lending | `Loan` | `m_loan` / `m_loan_transaction` | Event-Driven |
| ۱۶ | Delinquency | نکول و سررسیدگذشتگی | Lending | `DelinquencyBucket` | `m_delinquency_bucket` | State-Driven |
| ۱۷ | Non-Performing Asset (NPA) | دارایی غیرجاری | Lending | `Loan` | `m_loan.is_npa` | State-Driven |
| ۱۸ | Overdue | اقساط سررسید گذشته | Lending | `LoanRepaymentScheduleInstallment` | `m_loan_repayment_schedule` | Event-Driven |
| ۱۹ | Days Past Due (DPD) | شاخص روزهای تأخیر | Lending | `LoanArrearsAging` | `m_loan_arrears_aging` | Ubiquitous |
| ۲۰ | Arrears | معوقات انباشته اقساط | Lending | `LoanArrearsAging` | `m_loan_arrears_aging` | Ubiquitous |
| ۲۱ | Aging Buckets | بازه‌های زمانی معوقات | Lending | `DelinquencyRange` | `m_delinquency_range` | Event-Driven |
| ۲۲ | Write-Off | سوخت مطالبات | Lending | `LoanTransaction` / `Loan` | `m_loan` (`loan_status_id=601`) | Event-Driven |
| ۲۳ | Recovery | وصول مطالبات سوخت‌شده | Lending | `LoanTransaction` | `m_loan_transaction` (`type=5`) | State-Driven |
| ۲۴ | Capitalized Income | درآمد سرمایه‌شده به اصل | Lending | `LoanCharge` | `m_loan_charge.is_capitalized` | Optional Feature |
| ۲۵ | Advanced Payment Allocation | استراتژی پیشرفته تخصیص | Lending | `PaymentAllocationOrder` | `m_loan_product_payment_allocation_rule` | Event-Driven |
| ۲۶ | Progressive Loan | تسهیلات پیش‌رونده | Lending | `ProgressiveLoanScheduleGenerator` | `m_loan` | Optional Feature |
| ۲۷ | Available Balance | مانده در دسترس | Savings | `SavingsAccount` | `m_savings_account` | Unwanted Behavior (If-Then) |
| ۲۸ | Ledger Balance | مانده دفتری ثبتی | Savings | `SavingsAccount` | `m_savings_account.account_balance_derived` | Ubiquitous |
| ۲۹ | Daily Balance | مانده روزشمار پایان روز | Savings | `SavingsAccountTransaction` | `m_savings_account_transaction` | Ubiquitous |
| ۳۰ | Minimum Balance | حداقل مانده الزامی | Savings | `SavingsProduct` / `Account` | `m_savings_account.min_required_balance` | Complex (Where + If-Then) |
| ۳۱ | Hold Amount / Lien | مسدودی و توثیق وجه | Savings | `SavingsAccount` | `m_savings_account_on_hold_funds` | Event-Driven |
| ۳۲ | Fixed Deposit | سپرده مدت‌دار ثابت | Savings | `FixedDepositAccount` | `m_deposit_account_term_and_pre_closure` | Event-Driven |
| ۳۳ | Recurring Deposit | سپرده اندوخته دوره‌ای | Savings | `RecurringDepositAccount` | `m_deposit_account_recurring_detail` | Event-Driven |
| ۳۴ | Interest Posting | واریز سود به حساب | Savings | `SavingsAccountTransaction` | `m_savings_account_transaction` (`type=3`) | Event-Driven |
| ۳۵ | Compounding Period | دوره محاسبه سود مرکب | Savings | `SavingsCompoundingInterestPeriodType`| `m_savings_account.compounding_period` | Optional Feature |
| ۳۶ | Premature Closure | بستن پیش از موعد سپرده | Savings | `FixedDepositAccount` | `m_savings_account` (`status=700`) | Event-Driven |
| ۳۷ | Dormancy | راکد بودن حساب | Savings | `SavingsAccountSubStatusEnum` | `m_savings_account.sub_status_enum=200` | State-Driven |
| ۳۸ | Escheatment | انتقال وجوه به خزانه‌داری | Savings | `SavingsAccountSubStatusEnum` | `m_savings_account.sub_status_enum=300` | Event-Driven |
| ۳۹ | Overdraft | اضافه برداشت سپرده | Savings | `SavingsAccount` | `m_savings_account.allow_overdraft` | Optional Feature |
| ۴۰ | Savings Sub-Status | زیروضعیت‌های انسداد | Savings | `SavingsAccountSubStatusEnum` | `m_savings_account.sub_status_enum` | State-Driven |
| ۴۱ | Double-Entry Bookkeeping | حسابداری دوطرفه | Accounting | `JournalEntry` | `acc_gl_journal_entry` | Unwanted Behavior (If-Then) |
| ۴۲ | Chart of Accounts | کدینگ حساب‌های دفتر کل | Accounting | `GLAccount` | `acc_gl_account` | State-Driven |
| ۴۳ | Asset | دارایی | Accounting | `GLAccountType` | `acc_gl_account` (`type=1`) | Ubiquitous |
| ۴۴ | Liability | بدهی | Accounting | `GLAccountType` | `acc_gl_account` (`type=2`) | Ubiquitous |
| ۴۵ | Equity | حقوق صاحبان سهام | Accounting | `GLAccountType` | `acc_gl_account` (`type=3`) | Ubiquitous |
| ۴۶ | Income | درآمد | Accounting | `GLAccountType` | `acc_gl_account` (`type=4`) | Event-Driven |
| ۴۷ | Expense | هزینه | Accounting | `GLAccountType` | `acc_gl_account` (`type=5`) | Event-Driven |
| ۴۸ | Cash-based Accounting | حسابداری برمبنای نقدی | Accounting | `AccountingRuleType` | `m_product_loan.accounting_type=2` | Optional Feature |
| ۴۹ | Periodic Accrual | حسابداری تعهدی دوره‌ای | Accounting | `AccountingRuleType` | `m_product_loan.accounting_type=3` | Complex (Where + When) |
| ۵۰ | Upfront Accrual | حسابداری تعهدی آنی | Accounting | `AccountingRuleType` | `m_product_loan.accounting_type=4` | Complex (Where + When) |
| ۵۱ | Journal Entry | سند دوبل حسابداری | Accounting | `JournalEntry` | `acc_gl_journal_entry` | Ubiquitous |
| ۵۲ | Debit | بدهکار | Accounting | `JournalEntryType` | `acc_gl_journal_entry.type_enum=1` | Ubiquitous |
| ۵۳ | Credit | بستانکار | Accounting | `JournalEntryType` | `acc_gl_journal_entry.type_enum=2` | Ubiquitous |
| ۵۴ | Financial Activity Mapping | نگاشت فعالیت‌های مالی | Accounting | `FinancialActivityAccount` | `acc_financial_activity_account` | Ubiquitous |
| ۵۵ | Suspense Account | حساب واسط معلق | Accounting | `GLAccount` | `acc_gl_account` | State-Driven |
| ۵۶ | Currency Revaluation | تجدید ارزیابی ارزی | Accounting | `JournalEntry` | `acc_gl_journal_entry` | Event-Driven |
| ۵۷ | Disbursal Fee | کارمزد پرداخت تسهیلات | Charges | `Charge` / `LoanCharge` | `m_charge` (`time_enum=1`) | Event-Driven |
| ۵۸ | Specified Due Date Charge | کارمزد با تاریخ سررسید | Charges | `Charge` / `LoanCharge` | `m_charge` (`time_enum=2`) | Event-Driven |
| ۵۹ | Installment Fee | کارمزد وابسته به قسط | Charges | `Charge` / `LoanCharge` | `m_charge` (`time_enum=8`) | Ubiquitous |
| ۶۰ | Overdue Penalty | جریمه تأخیر تأدیه | Charges | `Charge` / `LoanCharge` | `m_charge` (`is_penalty=true`) | Event-Driven |
| ۶۱ | Flat Fee | کارمزد مبلغ ثابت | Charges | `ChargeCalculationType` | `m_charge.charge_calculation_enum=1` | Optional Feature |
| ۶۲ | Pro-rata Fee | کارمزد تناسبی و درصدی | Charges | `ChargeCalculationType` | `m_charge.charge_calculation_enum=2` | Optional Feature |
| ۶۳ | Withholding Tax | مالیات تکلیفی سود | Charges/Tax | `TaxGroup` | `m_tax_group` | Complex (Where + When) |
| ۶۴ | Tax Group | گروه مالیاتی | Charges/Tax | `TaxGroup` | `m_tax_group` | Ubiquitous |
| ۶۵ | Tax Component | مؤلفه مالیاتی | Charges/Tax | `TaxComponent` | `m_tax_component` | Ubiquitous |
| ۶۶ | Capitalized Fee | کارمزد سرمایه‌شده به اصل | Charges | `LoanCharge` | `m_loan_charge.is_capitalized=true` | Optional Feature |
| ۶۷ | Business Date | تاریخ تجاری بانک | COB/Core | `BusinessDate` | `m_business_date` | Ubiquitous |
| ۶۸ | Day-End Accrual | شناسایی تعهدی پایان روز | COB/Core | `AddPeriodicAccrualEntriesBusinessStep`| `acc_gl_journal_entry` | Event-Driven |
| ۶۹ | COB Catch-Up | پردازش تسویه جبرانی | COB/Core | `LoanCOBCatchUpService` | `m_loan.last_closed_business_date` | State-Driven |
| ۷۰ | Inline COB | تسویه درون‌خطی حین تراکنش | COB/Core | `LoanCOBApiFilter` | `m_loan_account_locks` | Complex (While + When) |
| ۷۱ | Account Lock | قفل انحصاری سطح حساب | COB/Core | `LoanAccountLock` | `m_loan_account_locks` | Unwanted Behavior (If-Then) |
| ۷۲ | Holiday Calendar | تقویم تعطیلات رسمی | COB/Core | `Holiday` | `m_holiday` | Ubiquitous |
| ۷۳ | Reschedule on Holiday | انتقال سررسید در تعطیلات | COB/Core | `RescheduleType` | `m_holiday.rescheduling_type` | Complex (Where + When) |
| ۷۴ | Batch Business Steps | زنجیره گام‌های تسویه | COB/Core | `BatchBusinessStep` | `m_batch_business_steps` | Ubiquitous |
| ۷۵ | Remote Partitioning | پارتیشن‌بندی توزیع‌شده | COB/Core | `LoanCOBPartitioner` | Spring Batch Worker Queues | Event-Driven |
| ۷۶ | Tenant | مستأجر نرم‌افزاری | Platform | `FineractPlatformTenant` | `fineract_tenants.tenants` | Ubiquitous |
| ۷۷ | Maker | پیشنهاددهنده دستور | Platform | `AppUser` | `m_portfolio_command_source.maker_id` | Event-Driven |
| ۷۸ | Checker | تاییدکننده ناظر | Platform | `AppUser` | `m_portfolio_command_source.checker_id` | Event-Driven |
| ۷۹ | Segregation of Duties | نظارت چهارچشمی | Platform | `PortfolioCommandSourceWritePlatformServiceImpl` | `m_permission.can_maker_checker` | Unwanted Behavior (If-Then) |
| ۸۰ | Idempotency Key | کلید تکرارناپذیری تراکنش | Platform | `IdempotencyKeyResolver` | `m_portfolio_command_source.idempotency_key` | Complex (While + When) |
| ۸۱ | Command Wrapper | بسته‌بندی دستور CQRS | Platform | `CommandWrapper` | `m_portfolio_command_source` | Ubiquitous |
| ۸۲ | Audit Trail | ردیابی ممیزی عملیات | Platform | `Audit` | `m_portfolio_command_source` | Ubiquitous |
| ۸۳ | Event Sourcing | بازسازی وضعیت از رویدادها | Platform | `LoanTransaction` / `Derived` | `m_loan.*_derived` | Ubiquitous |
| ۸۴ | Transactional Outbox | صندوق خروجی تراکنشی | Platform | `ExternalEvent` | `m_external_event` | Event-Driven |

---
