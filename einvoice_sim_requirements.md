# ملف المتطلبات الهندسية — سكربت محاكاة فوترة تاريخية (Python + AI)

## 1) حالة المؤسسة (Context)
- **الفترة:** من 2023-09-23 حتى 2024-12-31.
- **الوضع الحالي:** المؤسسة استوردت وباعت فعليًّا خلال الفترة، لكنها **لم تُسجِّل أي مبيعات** ولا تملك سجلات محاسبية/فواتير.
- **ما توفر من أدلة محاسبية:**
  - ملف **`imports-catalog-pricing.xlsx`**: يضم كل الشحنات/الأصناف المستورَدة، تكاليف الشحنة، هامش الربح المقترح، **سعر البيع قبل الضريبة**، تاريخ الاستيراد، وتصنيف الشحنة **`shipment_class`**.
  - ملف **`vat-returns.xlsx`**: شيتات ربع سنوية من `2023Q4` حتى `2024Q4`، تحوي **المبيعات الأساسية (Ex-VAT)** و**ضريبة القيمة المضافة** و**الإجمالي (Inc-VAT)** لكل فترة ضريبية مصرح بها في الإقرارات.
  - ملف **`official-holidays.xlsx`**: شيت `y2023` وشيت `y2024` بتواريخ الإجازات الرسمية (توقف البيع).
  - ملف **`b2b-customers-purchases.xlsx`**: أسماء عملاء B2B المسجلين ضريبيًا + **مبالغ مشترياتهم** وتواريخها وأرقامهم الضريبية.

> **الخلاصة:** لدينا بيانات تكفي لإعادة بناء (محاكاة) حركة المبيعات الواقعية بصورة منطقية، لإصدار فواتير وتقارير متسقة مع القيود التشغيلية والضريبية.

---

## 2) الهدف (Objective)
بناء **سكربت بايثون** (CLI) يوظّف منطقًا خوارزميًا + طبقة ذكاء اصطناعي خفيفة لمحاكاة المبيعات التاريخية وإصدار:
1. **دفتر فواتير** متسلسل (Simplified B2C / Tax B2B) متوافق مع البيانات.
2. **تقارير مبيعات** مجمّعة وتقرير خاص بالسلع الانتقائية.
3. **قيود حوكمة** تمنع تجاوز مبيعات الفترات المصرَّح بها في الإقرارات.

---

## 3) المدخلات (Data Inputs)
### 3.1 `imports-catalog-pricing.xlsx` (ورقة: `imports`)
- أعمدة إلزامية: `customs_declaration_no`, `sku`, `item_description`, `shipment_class`, `import_date`, `qty_imported`, `unit_cost_ex_vat` *(اختياري إذا توفّر `landed_cost_total`)*, `margin_pct`, `unit_price_ex_vat`.
- ملاحظات:
  - نفس الـ `sku` قد يتكرر عبر بيانات جمركية مختلفة بأسعار مختلفة ⇒ **Lot** مستقل لكل `customs_declaration_no:sku`.
  - **تصنيف الشحنة**: أحد `EXC_INSPECTION`, `NONEXC_INSPECTION`, `NONEXC_OUTSIDE`.

### 3.2 `vat-returns.xlsx` (شيتات: `2023Q4`…`2024Q4`)
- أعمدة: `period_start`, `period_end`, `sales_ex_vat`, `vat_amount`, `sales_inc_vat` (ويجب تحقق المعادلة).

### 3.3 `official-holidays.xlsx` (شيت: `y2023`, `y2024`)
- أعمدة: `holiday_date`, `holiday_name`, `is_public_holiday` *(و/أو `is_closed`)*.

### 3.4 `b2b-customers-purchases.xlsx` (شيت: `purchases_b2b` أو `customers_purchases`)
- أعمدة: `client_name`, `vat_number`, `address_line`, `amount_inc_vat`, `purchase_date` *(ISO)*.

---

## 4) المتطلبات الوظيفية (Functional Requirements)
### 4.1 Model-1 — **Inventory Loader (Lot-Aware)**
- يُنشئ **Lot** لكل صف استيراد: `lot_id = customs_declaration_no:sku`.
- **تفعيل المخزون**: لا تُضاف الكميات للمخزون إلا بعد **Δ يوم = [7..12]** من `import_date` (لنقل الشحنة من الجمارك للمستودع).
- السعر المرجعي للبيع لكل Lot = `unit_price_ex_vat` من الملف، مع احتفاظ **منفصل** بتكلفة الوحدة `unit_cost_ex_vat` (للتدقيق).
- الاستهلاك الافتراضي عند البيع: **FIFO على مستوى الـLot** (قابل للتبديل إلى Weighted-Avg لاحقًا).

### 4.2 Model-2 — **Sales Engine**
- نافذة البيع: **من 2023-09-23 إلى 2024-12-31**.
- البيع **محكوم بالمخزون**: لا بيع عند نفاد الرصيد لأي Lot (لا يسمح بمخزون سالب).
- القيود الزمنية: أيام عمل وساعات عمل قابلة للتهيئة + **توقف كامل في الإجازات الرسمية**.
- توليد فواتير متعددة البنود (Compound): 1..K أصناف، مع خلط أصناف انتقائية/غير انتقائية.
- **B2C (Simplified):** بيع عشوائي لعميل نقدي عندما لا يوجد تطابق B2B موجه.
- **B2B (Tax):** عند تطابق التاريخ مع `b2b-customers-purchases`, يولّد فاتورة باسم العميل ورقمه الضريبي بقيمة تستهدف **`amount_ex_vat`** المستنتجة من `amount_inc_vat` (تقريبًا ±Tolerance).
- **ترقيم الفواتير:** تسلسل أحادي `{PREFIX}-{YYYYMM}-{SEQ}` بلا فجوات غير مبررة.
- **TLV Base64** لرمز QR للفواتير المبسطة فقط (حقل في الرأس، صورة QR اختيارية لاحقًا).

### 4.3 Model-3 — **Orchestrator / Quota Governor**
- يقرأ سقوف كل ربع من `vat-returns.xlsx` (حقل `sales_ex_vat`).
- يمنع تجاوز **المبيعات قبل الضريبة** المتراكمة للربع لحد **`cap_ex_vat × target_ratio`** (افتراضي 100% أو 98%).
- يرحّل المخزون المتبقي للفترات التالية تلقائيًا.

### 4.4 التقارير (Outputs)
- `invoices_header.csv`: `invoice_number`, `invoice_datetime`, `invoice_type`, `client_name`, `client_vat`, `total_ex_vat`, `vat_amount`, `total_inc_vat`, `qr_tlv_base64`, `has_excise_items`.
- `invoices_lines.csv`: `invoice_number`, `line_no`, `sku`, `description`, `class`, `lot_id`, `qty`, `unit_price_ex_vat`, `line_total_ex_vat`.
- `sales_summary_header.csv` و `sales_summary_by_sku.csv`.
- `excise_invoices.csv`: كل فاتورة تحتوي بندًا من `EXC_INSPECTION`.

## ⚠️ قاعدة حاسمة: التسعير على مستوى الـLot وليس الـSKU
- قد يتكرر نفس `sku` في **بيانات جمركية مختلفة** (أرقام بيان مختلفة) مع **تكاليف وأسس تسعير مختلفة**.
- **ممنوع** اعتماد سعر موحد على مستوى الـSKU. يجب أن يكون **السعر والتكلفة على مستوى الـLot**:
  - تعريف الـLot: `lot_id = customs_declaration_no:sku`
  - حقول السعر/التكلفة المُلزِمة لكل Lot:
    - `unit_cost_ex_vat` — تكلفة الوحدة (من تكلفة الشحنة / الكمية)
    - `unit_price_ex_vat` — **سعر بيع الوحدة** الخاص بذلك الـLot فقط
- الاستهلاك المسموح به افتراضيًا: **FIFO حسب الـLot**. عند استهلاك كميات من أكثر من Lot لنفس الصنف داخل فاتورة واحدة، يجب إنشاء **سطرين منفصلين** حفاظًا على السعر الخاص بكل Lot.
- **حظر صريح**: لا يجوز للسكربت تطبيق تسعير متوسط تلقائي على مستوى الـSKU ما لم يُفعَّل ذلك صراحةً عبر إعداد `pricing_policy = "weighted_avg"`، والقيمة الافتراضية **"lot_price"**.
- تقارير المخرجات يجب أن تُظهر `lot_id` و`unit_price_ex_vat` لكل سطر فاتورة لضمان التتبع والمراجعة المحاسبية.

---

## 5) قواعد الأعمال (Business Rules)
- **VAT 15%** على المبيعات الخاضعة.
- نوع الفاتورة:
  - B2C → **Simplified Tax Invoice** (بدون اسم عميل، مع `qr_tlv_base64`).
  - B2B → **Tax Invoice** (اسم ورقم ضريبي إلزامي من الملف B2B).
- **عدم البيع دون مخزون** (لا سالب).
- **Mix-Allowed**: السماح بخلط أصناف انتقائية وغير انتقائية داخل الفاتورة.
- **تصنيف البيان الجمركي** يتحكم في تقارير الانتقائية.

---

## 6) طبقة الإعدادات (Configuration)
- ملف `settings.yaml`, مثال:
```yaml
vat_rate: 0.15
work_days: [0,1,2,3,4]              # الاثنين..الجمعة (0=الاثنين)
business_hours: { start: "09:00", end: "17:00" }
random_seed: 42
invoice_prefix: "SINV"
lot_activation_days: { min: 7, max: 12 }
line_items_per_invoice: { min: 1, max: 5 }
b2c_probability: 0.6
pricing_policy: "lot_price"         # القيم المتاحة: lot_price | weighted_avg
quarter_caps_target_ratio: 1.00
paths:
  imports: "./data/imports-catalog-pricing.xlsx"
  vat_returns: "./data/vat-returns.xlsx"
  holidays: "./data/official-holidays.xlsx"
  b2b_customers: "./data/b2b-customers-purchases.xlsx"
```

---

## 7) تدفق التنفيذ (Execution Flow)
1) **Validate Inputs**: تحقق المخططات والصيغ (تواريخ ISO، علاقات الجمع، نطاق القيم). 
2) **Load Inventory (Model-1)**: إنشاء الـLots وتفعيلها بعد Δ يوم.
3) **Simulate Sales (Model-2 + Model-3)**: عبر الأيام العاملة، إنشاء فواتير وفق المخزون والقيود، مع حقن فواتير B2B في تواريخها.
4) **Export Reports**: CSV/Excel + (اختياري) PDF للفواتير.

**Pseudo:**
```pseudo
validate_all_inputs()
inv = build_inventory_lots(imports, activation_delay=7..12)
accumulator = init_quarter_accumulator(vat_returns)

for day in daterange(2023-09-23, 2024-12-31):
  if not is_working_day(day, holidays): continue
  for _ in range(rand_invoices_today()):
    client = pick_client(day, b2b_purchases)
    lines  = allocate_lines_from_inventory(inv, K, fifo_by_lot=True)
    totals = compute_totals(lines, vat=15%)
    if orchestrator_allows(day, totals.ex_vat, accumulator):
       persist_invoice(client, lines, totals)
       decrement_stock(inv, lines)
```

---

## 8) الذكاء الاصطناعي (AI Layer) — اختياري/مرحلة 2
- **Controller MLP/Probabilistic**: ضبط توزيع المبيعات (اختيار الأصناف والكميات) لتعكس نمطًا واقعيًا ضمن حدود الإقرار الربعي.
- **Tolerance Tuner**: نموذج بسيط يضبط هامش الخطأ لمطابقة مبالغ B2B المستهدفة بأقل انحراف.
- **Anomaly Detection (لاحقًا)**: عزل فواتير شاذة مقارنة بالنمط العام.

> المرحلة الأولى يمكن أن تكون خوارزمية عشوائية منضبطة بالقواعد (Deterministic-Random) مع `random_seed` لإعادة الإنتاج.

---

## 9) الواجهات والأوامر (CLI)
```
python -m app.validate   --data ./data --config ./config/settings.yaml
python -m app.inventory  --data ./data --config ./config/settings.yaml --out ./outputs
python -m app.sales      --data ./data --config ./config/settings.yaml --out ./outputs
python -m app.reporting  --in ./outputs --out ./outputs
```

---

## 10) معايير القبول (Acceptance Criteria)
- [AC-1] لا يصبح رصيد أي **Lot** سالبًا.
- [AC-2] لا تتجاوز المبيعات **Ex-VAT** الحد الربع سنوي المصرّح به.
- [AC-3] فواتير **B2B** تُنشَأ في تواريخها وبقيمة قريبة من `amount_ex_vat` (±Tolerance محدَّد).
- [AC-4] تسلسل ترقيم الفواتير أحادي بلا فجوات غير مبررة.
- [AC-5] الفواتير المبسطة تتضمن `qr_tlv_base64`.
- [AC-6] تقرير السلع الانتقائية يتضمن 100% من الفواتير التي تحتوي عناصر `EXC_INSPECTION`.
- [AC-7] كل الملفات تُقرأ دون تعديل يدوي للأسماء/المخططات القياسية.
- **[AC-8] تسعير الـSKU حسب الـLot:** كل سطر فاتورة يحمل `lot_id` وسعره `unit_price_ex_vat` الخاص به. **ممنوع** استخدام سعر موحّد للـSKU عبر لوتات مختلفة. عند المزج من لوتين لنفس الـSKU داخل فاتورة، تُنشأ **أسطر متعددة** بأسعارها الخاصة.

---

## 11) التحقق والجودة (Validation & QA)
- **Schema Checks** لكل ملف قبل التشغيل.
- **Reproducibility** عبر `random_seed` ثابت.
- **Logging** مُفصّل (تفعيل Lots، قرارات Orchestrator، حالات رفض/تعديل فواتير). 
- **Unit Tests** لوحدات: Loader, Sales, Orchestrator, TLV.
- **Test Case إضافي (لهذه القاعدة):** إدخال نفس `sku` عبر بيانين بسعرين مختلفين ثم محاكاة بيع يجبر على السحب من اللوتين داخل فاتورة واحدة؛ التحقق من ظهور **سطرين** بأسعار مختلفة وربط كل سطر بـ`lot_id` الصحيح.

---

## 12) المخرجات (Artifacts)
- CSV/Excel للتقارير المذكورة.
- (اختياري) PDF للفواتير مع QR للفواتير المبسطة.
- ملف سجل تشغيل (LOG) + ملخص تشغيل.

---

## 13) ملاحظات تنفيذية
- التواريخ بصيغة **ISO `YYYY-MM-DD`** حصراً.
- الحفاظ على **نصية** حقول مثل `vat_number` لتفادي فقد الأصفار.
- دعم العربية في الأوصاف، مع أعمدة برمجية **snake_case**.
- إمكانية تعديل سياسة الاستهلاك (FIFO↔Weighted-Avg) عبر الإعدادات.

*تاريخ الإصدار:* 2025-10-03