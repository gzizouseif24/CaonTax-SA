# 🎯 E-Invoicing Simulation Script - AI Coder Instructions

## 📋 PROJECT OVERVIEW

**Objective:** Create a Python script that generates realistic invoices matching exact quarterly tax targets

**Output:** Invoices (PDFs) + Reports (Excel) - NOT a web application

**Duration:** Single script, run once, produce results

---

## 🎯 WHAT WE'RE BUILDING

A **standalone Python script** that:
1. Reads 3 Excel files (products, customers, holidays)
2. Simulates sales from Sept 2023 → Dec 2024
3. Generates realistic daily invoices that SUM to exact quarterly targets
4. Outputs: 1000s of invoice PDFs + Excel reports

**THIS IS NOT:**
- ❌ A web application
- ❌ A SaaS platform
- ❌ An API or database system

**THIS IS:**
- ✅ A single Python script
- ✅ Run once, get results
- ✅ Hardcoded for these specific targets

---

## 📁 FILE STRUCTURE (SIMPLE)

```
invoice_generator/
├── main.py                      # Main script - run this
├── config.py                    # Hardcoded targets & settings
├── excel_reader.py              # Read 3 Excel files
├── inventory.py                 # FIFO stock tracking
├── simulation.py                # Generate sales
├── alignment.py                 # Match quarterly targets
├── pdf_generator.py             # Create invoice PDFs
├── report_generator.py          # Create Excel reports
├── requirements.txt             # Dependencies
├── fonts/                       # Arabic fonts
│   └── Amiri-Regular.ttf
├── input/                       # Excel files go here
│   ├── products.xlsx
│   ├── customers.xlsx
│   └── holidays.xlsx
└── output/                      # Generated files
    ├── invoices/                # All PDF invoices
    └── reports/                 # Excel reports
```

---

## 📦 DEPENDENCIES (requirements.txt)

```
pandas==2.2.1
openpyxl==3.1.2
reportlab==4.1.0
arabic-reshaper==3.0.0
python-bidi==0.4.2
pillow==10.2.0
qrcode[pil]==7.4.2
hijri-converter==2.3.1
xlsxwriter==3.2.0
```

---

## 🎯 config.py - HARDCODED TARGETS

Create a config file with:

**Quarterly Targets (exact numbers):**
```python
QUARTERLY_TARGETS = {
    "Q3-2023": {"sales": 341130.43, "vat": 51169.56, "start": "2023-07-01", "end": "2023-09-30"},
    "Q4-2023": {"sales": 277913.04, "vat": 41686.96, "start": "2023-10-01", "end": "2023-12-31"},
    "Q1-2024": {"sales": 916376.73, "vat": 137456.51, "start": "2024-01-01", "end": "2024-03-31"},
    "Q2-2024": {"sales": 1211936.80, "vat": 181790.52, "start": "2024-04-01", "end": "2024-06-30"},
    "Q3-2024": {"sales": 2029080.00, "vat": 304362.00, "start": "2024-07-01", "end": "2024-09-30"},
    "Q4-2024": {"sales": 776215.00, "vat": 116432.25, "start": "2024-10-01", "end": "2024-12-31"}
}
```

**Seller Info (fixed):**
```python
SELLER_NAME = "مؤسسة رائد الإنجاز للخدمات التجارية"
SELLER_ADDRESS = "الرياض، السلي 14322"
SELLER_PHONE = "0555866344"
SELLER_EMAIL = "M.ALSHAIKHI1993@GMAIL.COM"
SELLER_TAX_NUMBER = "302167780700003"
```

**Simulation Settings:**
```python
VAT_RATE = 0.15
RAMADAN_BOOST = 2.0
SALARY_DAY_27_BOOST = 1.5
SALARY_DAY_1_BOOST = 1.2
SALARY_DAY_10_BOOST = 1.1
WORKING_DAYS = [0, 1, 2, 3, 4, 5, 6]  # Monday-Sunday, except Friday=4
```

**Classifications:**
```python
OUTSIDE_INSPECTION = "خارج حالة الفحص غير انتقائية"
UNDER_NON_SELECTIVE = "محل الفحص سلع غير انتقائية"
UNDER_SELECTIVE = "محل الفحص سلع انتقائية"
```

---

## 📖 INSTRUCTION 1: excel_reader.py

**Task:** Read the 3 Excel files into Python data structures

**Input Files:**
1. `products.xlsx` - 203 products with import dates, costs, margins, classifications
2. `customers.xlsx` - 70 VAT customers with purchase dates/amounts
3. `holidays.xlsx` - Official holidays (2023 & 2024)

**What to do:**
- Use pandas to read each Excel file
- Handle Arabic column names properly (UTF-8)
- Convert Excel date serials to Python dates
- Store products as list of dictionaries
- Store customers as list of dictionaries
- Store holidays as list of dates

**Column Mappings:**
Products Excel has these Arabic columns that map to:
- `الصنف` → item_name
- `تاريخ الاستيراد` → import_date (Excel serial, convert to date)
- `البيان الجمركي للشحنة` → customs_declaration
- `الكمية` → quantity
- `اجمالي التكاليف` → total_cost
- `نسبة هامش الربح` → profit_margin_pct
- `النوع` → classification

Customers Excel:
- `اسم المشتري` → customer_name
- `الرقم الضريبي` → tax_number
- `مبلغ الشراء` → purchase_amount
- `تاريخ الشراء` → purchase_date (DD/MM/YYYY format)

**Output:** Return 3 data structures (products_list, customers_list, holidays_list)

---

## 📖 INSTRUCTION 2: inventory.py

**Task:** Implement FIFO inventory tracking

**Data Structure:**
Keep batches in memory as list of dictionaries:
```python
{
    "item_name": "شيبس بطاطس",
    "customs_declaration": "195512",
    "classification": "خارج حالة الفحص غير انتقائية",
    "import_date": date(2023, 9, 23),
    "stock_date": date(2023, 10, 2),  # import_date + random 7-12 days
    "quantity_remaining": 10800,
    "unit_cost": 6.46,
    "unit_price_before_vat": 7.43,
    "profit_margin": 0.15
}
```

**Functions needed:**

1. **initialize_inventory(products_list):**
   - For each product, create a batch
   - Calculate stock_date = import_date + random(7, 12) days
   - Store all batches in list

2. **get_available_items_by_classification(classification):**
   - Return items that have quantity_remaining > 0
   - Filter by classification

3. **deduct_stock(item_name, quantity):**
   - Find oldest batch (by stock_date) for this item
   - Deduct quantity from that batch
   - If batch runs out, move to next batch (FIFO)
   - Raise error if insufficient stock

4. **get_unit_price(item_name):**
   - Return unit_price_before_vat from oldest available batch

---

## 📖 INSTRUCTION 3: simulation.py

**Task:** Generate realistic daily invoices

**Main Function: generate_invoices_for_quarter(quarter_name, target_sales, target_vat, customers_for_quarter)**

**Logic:**
1. Get date range for quarter
2. Loop through each day in the quarter
3. For each day:
   - Skip if Friday (weekday == 4)
   - Skip if in holidays_list
   - Calculate boost factor (check Ramadan, check salary days)
   - Generate N invoices (base 5-20, multiply by boost)
   - For each invoice: decide type (cash vs VAT customer), build basket, calculate totals

**Helper Functions:**

1. **is_working_day(date, holidays_list):**
   - Return False if Friday or in holidays
   - Return True otherwise

2. **calculate_boost(date):**
   - Check if date is in Ramadan/Shaaban (use hijri-converter)
   - Check if day of month is 27, 1, or 10
   - Return multiplier (1.0 to 2.0)

3. **select_invoice_type(customers_remaining):**
   - If customers_remaining has people → maybe create TAX invoice (30% chance)
   - Otherwise → SIMPLIFIED invoice

4. **build_basket(invoice_type, inventory):**
   - Select 2-10 random items
   - Each item: quantity 3-40
   - **Classification Rules:**
     - If OUTSIDE_INSPECTION → must be alone in basket
     - If TAX invoice → only UNDER_NON_SELECTIVE allowed
     - If SIMPLIFIED → can mix UNDER_NON_SELECTIVE + UNDER_SELECTIVE
   - Check inventory availability before adding

5. **create_invoice(invoice_type, customer, basket, date):**
   - Generate invoice number (sequential: INV-SIMP-0001, INV-TAX-0001)
   - Calculate line items: qty × unit_price
   - Calculate subtotal, VAT (15%), total
   - Deduct from inventory
   - Return invoice dictionary

---

## 📖 INSTRUCTION 4: alignment.py

**Task:** THE HARD PART - Make totals match exact targets

**Main Function: align_quarter_to_target(quarter_name, target_sales, target_vat, customers_for_quarter)**

**Algorithm (iterative adjustment):**

```
1. Initialize adjustment_factor = 1.0

2. PHASE 1: Generate VAT customer invoices
   - For each customer in customers_for_quarter:
     - Create invoice on their purchase_date
     - Use ONLY UNDER_NON_SELECTIVE items
     - Adjust item prices so subtotal = customer.purchase_amount / 1.15
     - This is FIXED, don't change in iterations
   
3. PHASE 2: Calculate gap
   - gap_sales = target_sales - sum(vat_customer_invoices.subtotal)
   - gap_vat = target_vat - sum(vat_customer_invoices.vat)

4. PHASE 3: Iterative cash sales (max 1000 iterations)
   For iteration in 1..1000:
     a. Generate all cash invoices for quarter using simulation.py
        - Pass adjustment_factor to modify prices
        - Only SIMPLIFIED invoices
     
     b. Calculate actual totals
        - actual_sales = sum(all_invoices.subtotal)
        - actual_vat = sum(all_invoices.vat)
     
     c. Check if matched
        - If abs(actual_sales - target_sales) < 0.01 AND
             abs(actual_vat - target_vat) < 0.01:
          → SUCCESS! Return all invoices
     
     d. Adjust strategy
        - If actual_sales < target_sales:
            adjustment_factor *= 1.05  # Increase prices 5%
        - Else:
            adjustment_factor *= 0.95  # Decrease prices 5%
     
     e. Clear generated invoices, try again

5. FALLBACK: If didn't converge after 1000 iterations
   - Create ONE balancing invoice with exact amount needed
   - Pick random item, calculate quantity/price to hit exact gap
```

**The adjustment_factor modifies prices:**
```python
# In create_invoice function
adjusted_price = unit_price * adjustment_factor
```

---

## 📖 INSTRUCTION 5: pdf_generator.py

**Task:** Generate invoice PDFs with Arabic RTL support

**Two Types:**

### Type 1: Simplified Invoice (Thermal Receipt)
- Size: 80mm wide (thermal paper)
- Format: Simple text receipt
- Customer: "عميل نقدي" (Cash Customer)
- Include: Seller info, line items, totals, QR code

### Type 2: Tax Invoice (A4)
- Size: A4
- Format: Professional invoice
- Customer: Full name, tax number, address
- Include: Header, seller/buyer info, table of items, totals, QR code

**Arabic RTL Setup:**
```python
# Install: arabic-reshaper, python-bidi
# Register font: Amiri-Regular.ttf
# For each Arabic text:
from arabic_reshaper import reshape
from bidi.algorithm import get_display

arabic_text = "مؤسسة رائد الإنجاز"
reshaped = reshape(arabic_text)
bidi_text = get_display(reshaped)
# Now use bidi_text in PDF with Arabic font
```

**QR Code:**
```python
# Generate QR with: invoice_number, seller_name, address, tax_number
# Use qrcode library
# Embed image in PDF
```

**Function signatures:**
- `generate_simplified_pdf(invoice_dict) → save to output/invoices/`
- `generate_tax_pdf(invoice_dict) → save to output/invoices/`

---

## 📖 INSTRUCTION 6: report_generator.py

**Task:** Generate Excel reports

**Report 1: Detailed Sales (all line items)**
Columns:
- Invoice Number
- Invoice Date
- Item Name
- Unit Price (before VAT)
- Quantity
- Subtotal
- VAT Amount
- Total

Use pandas to create DataFrame, export to Excel with formatting

**Report 2: Invoice Summary**
Columns:
- Invoice Number
- Date
- Subtotal
- VAT
- Total

**Report 3: Quarterly Summary**
For each quarter:
- Quarter Name
- Total Sales (before VAT)
- Total VAT
- Total (with VAT)
- Match Status (✓ if matched target)

Save all reports to `output/reports/` folder

---

## 📖 INSTRUCTION 7: main.py - ORCHESTRATE EVERYTHING

**Main script flow:**

```python
1. Print banner "E-Invoicing Generator Starting..."

2. Load configuration from config.py

3. Read Excel files
   - products = read_products("input/products.xlsx")
   - customers = read_customers("input/customers.xlsx")
   - holidays = read_holidays("input/holidays.xlsx")
   - Print: "✓ Loaded 203 products, 70 customers, X holidays"

4. Initialize inventory
   - inventory = initialize_inventory(products)
   - Print: "✓ Inventory initialized with FIFO tracking"

5. For each quarter in QUARTERLY_TARGETS:
   - Print: f"Processing {quarter}..."
   - customers_for_quarter = filter customers by purchase_date
   - invoices = align_quarter_to_target(quarter, target, customers_for_quarter)
   - Print: f"✓ Generated {len(invoices)} invoices"
   - Print: f"   Sales: {sum(inv.subtotal)} (Target: {target.sales})"
   - Print: f"   VAT: {sum(inv.vat)} (Target: {target.vat})"
   - Print: f"   Match: {'✓' if matched else '✗'}"

6. Generate PDFs for all invoices
   - Print progress: "Generating PDFs... 1000/4523"
   - Save to output/invoices/

7. Generate reports
   - detailed_report.xlsx
   - summary_report.xlsx
   - quarterly_summary.xlsx
   - Print: "✓ Reports saved to output/reports/"

8. Print summary
   - Total invoices generated
   - Total sales
   - Total VAT
   - All quarters matched: ✓
   - Time taken

9. Done!
```

**Progress indicators:**
- Show progress bars or percentage during long operations
- Print which quarter is being processed
- Show convergence iterations

---

## 🎯 CRITICAL RULES TO ENFORCE

### 1. Classification Mixing
```
OUTSIDE_INSPECTION items:
  → MUST be alone in invoice
  → Cannot mix with anything

TAX invoices:
  → ONLY UNDER_NON_SELECTIVE items
  → Customer MUST be from customers list

SIMPLIFIED invoices:
  → Can have UNDER_NON_SELECTIVE
  → Can have UNDER_SELECTIVE
  → Can mix both
  → Customer = "عميل نقدي"
```

### 2. FIFO Strict
- Always deduct from oldest batch first
- Never break FIFO order
- Track remaining quantity carefully

### 3. Exact Matching
- Quarterly totals must match to ±0.01 SAR
- Don't accept "close enough"
- Use Decimal type for money (not float)

### 4. Date Rules
- No sales on Fridays
- No sales on holidays
- Add 7-12 random days to import_date for stock_date

### 5. Boosts
- Ramadan: ×2.0 (check Hijri calendar)
- Day 27: ×1.5
- Day 1: ×1.2
- Day 10: ×1.1
- Multiply all boosts that apply

---

## 🚀 EXECUTION STEPS

**Step 1: Setup**
```bash
pip install -r requirements.txt
mkdir -p input output/invoices output/reports
# Put 3 Excel files in input/
# Put Amiri-Regular.ttf in fonts/
```

**Step 2: Run**
```bash
python main.py
```

**Step 3: Check Output**
```
output/
├── invoices/
│   ├── INV-SIMP-0001.pdf
│   ├── INV-SIMP-0002.pdf
│   ├── ...
│   ├── INV-TAX-0001.pdf
│   └── ... (4000+ PDFs)
└── reports/
    ├── detailed_report.xlsx
    ├── summary_report.xlsx
    └── quarterly_summary.xlsx
```

---

## 📊 EXPECTED OUTPUT

**Console Output Example:**
```
═══════════════════════════════════════
E-Invoicing Generator v1.0
═══════════════════════════════════════

📖 Loading data...
✓ Products: 203 items loaded
✓ Customers: 70 VAT customers loaded
✓ Holidays: 45 dates loaded
✓ Inventory initialized (FIFO)

🎯 Processing Q3-2023 (Jul-Sep 2023)...
   Iteration 1: Sales=335000 (Target=341130) Δ=6130
   Iteration 2: Sales=340500 (Target=341130) Δ=630
   Iteration 3: Sales=341125 (Target=341130) Δ=5
   ✓ Converged! Generated 287 invoices
   Sales: 341130.43 ✓
   VAT: 51169.56 ✓

🎯 Processing Q4-2023 (Oct-Dec 2023)...
   ... similar output ...

📄 Generating PDFs...
   [████████████████████] 100% (4523/4523)
   ✓ Saved to output/invoices/

📊 Generating reports...
   ✓ detailed_report.xlsx
   ✓ summary_report.xlsx
   ✓ quarterly_summary.xlsx

═══════════════════════════════════════
✓ COMPLETED SUCCESSFULLY
═══════════════════════════════════════
Total Invoices: 4,523
Total Sales: 5,552,652.00 SAR
Total VAT: 832,897.80 SAR
All Quarters Matched: ✓
Time: 15m 42s
```

---

## 🎯 FINAL CHECKLIST

Before considering done:
- [ ] All 6 quarters match exactly (±0.01 SAR)
- [ ] VAT customers only buy UNDER_NON_SELECTIVE items
- [ ] All UNDER_SELECTIVE items only in SIMPLIFIED invoices
- [ ] No invoices on Fridays or holidays
- [ ] FIFO never violated
- [ ] Arabic displays correctly in PDFs (RTL)
- [ ] QR codes scannable
- [ ] 4000+ invoice PDFs generated
- [ ] 3 Excel reports generated
- [ ] Script completes in <30 minutes

---

## 💡 OPTIMIZATION TIPS

**If slow:**
- Don't save PDFs during alignment iterations
- Only generate PDFs after final invoices confirmed
- Use multiprocessing for PDF generation (4 workers)
- Cache Ramadan date calculations

**If not converging:**
- Reduce step size (1.05 → 1.02)
- Increase max iterations
- Add randomness to avoid oscillation
- Use adaptive step size (big steps early, small steps late)

**If running out of inventory:**
- Check stock_date calculations
- Verify deduction logic
- May need to adjust profit margins more aggressively

---

## 🎯 DELIVERABLES

After running script once:
1. **4000+ PDF invoices** in output/invoices/
2. **3 Excel reports** in output/reports/
3. **Console log** showing all quarters matched
4. **Script completes successfully**

**That's it. No database, no API, no web interface. Just run once, get files.**