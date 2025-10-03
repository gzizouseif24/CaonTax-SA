from excel_reader import read_products, read_holidays, read_customers
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from pdf_generator import PDFGenerator
from report_generator import ReportGenerator
from config import QUARTERLY_TARGETS, UNDER_SELECTIVE
import os
from datetime import datetime

print("="*60)
print("GENERATING ALL QUARTERS (2023-2024)")
print("="*60)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Step 1: Load data
print("\n" + "="*60)
print("STEP 1: LOADING DATA")
print("="*60)
products = read_products('input/products.xlsx')
holidays = read_holidays('input/holidays.xlsx')
customers_2024 = read_customers('input/customers.xlsx')  # If you have this file


# Step 2: Initialize components
print("\n" + "="*60)
print("STEP 2: INITIALIZING COMPONENTS")
print("="*60)
inventory = InventoryManager(products)
simulator = SalesSimulator(inventory, holidays)
aligner = QuarterlyAligner(simulator)
pdf_gen = PDFGenerator(template_dir='templates')
report_gen = ReportGenerator(output_dir='output/reports')

# Step 3: Generate invoices for all quarters
print("\n" + "="*60)
print("STEP 3: GENERATING INVOICES FOR ALL QUARTERS")
print("="*60)

all_invoices = []
quarterly_results = []

for quarter_name, target in QUARTERLY_TARGETS.items():
    print(f"\n{'='*60}")
    print(f"Processing {quarter_name}")
    print(f"{'='*60}")
    
    # Determine VAT customers by year
    if '2023' in quarter_name:
        vat_customers = []  # 2023 = all cash
    else:  # 2024
        # Filter customers for this quarter
        vat_customers = [
            c for c in customers_2024
            if target['start'] <= c['purchase_date'] <= target['end']
        ]
        print(f"  VAT customers for {quarter_name}: {len(vat_customers)}")
    # Generate invoices
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=target['sales'],
        target_vat=target['vat'],
        vat_customers=vat_customers
    )
    
    # Calculate actuals
    actual_sales = sum(inv['subtotal'] for inv in invoices)
    actual_vat = sum(inv['vat_amount'] for inv in invoices)
    
    # Store results
    quarterly_results.append({
        'quarter': quarter_name,
        'target_sales': target['sales'],
        'actual_sales': actual_sales,
        'target_vat': target['vat'],
        'actual_vat': actual_vat,
        'invoice_count': len(invoices),
        'matched': abs(actual_sales - target['sales']) < 0.10 and abs(actual_vat - target['vat']) < 0.10
    })
    
    all_invoices.extend(invoices)
    
    print(f"\n{quarter_name} Summary:")
    print(f"  Invoices: {len(invoices)}")
    print(f"  Sales: {actual_sales:,.2f} (Target: {target['sales']:,.2f})")
    print(f"  VAT: {actual_vat:,.2f} (Target: {target['vat']:,.2f})")
    print(f"  Match: {'✓' if quarterly_results[-1]['matched'] else '✗'}")

# Step 4: Generate sample PDFs (first 5 of each quarter)
print("\n" + "="*60)
print("STEP 4: GENERATING SAMPLE INVOICE PDFs")
print("="*60)

os.makedirs('output/sample_invoices', exist_ok=True)

sample_count = 5
for quarter_name in QUARTERLY_TARGETS.keys():
    quarter_invoices = [inv for inv in all_invoices if quarter_name in inv['invoice_number'] or inv['invoice_date'].date() >= QUARTERLY_TARGETS[quarter_name]['start'] and inv['invoice_date'].date() <= QUARTERLY_TARGETS[quarter_name]['end']]
        
    # Filter for invoices containing UNDER_SELECTIVE items only
    from config import UNDER_SELECTIVE
    
    selective_invoices = []
    for inv in quarter_invoices:
        # Check if ANY item in this invoice is UNDER_SELECTIVE
        has_selective = any(
            item.get('classification') == UNDER_SELECTIVE 
            for item in inv['line_items']
        )
        if has_selective:
            selective_invoices.append(inv)
    
    samples = selective_invoices[:sample_count]
    print(f"  {quarter_name}: Found {len(selective_invoices)} invoices with selective items, generating {len(samples)} samples")
    for inv in samples:
        try:
            output_path = f"output/sample_invoices/{inv['invoice_number'].replace('/', '-')}.pdf"
            pdf_gen.generate_pdf(inv, output_path)
            print(f"  Generated: {inv['invoice_number']}")
        except Exception as e:
            print(f"  Error generating {inv['invoice_number']}: {e}")

# Step 5: Generate reports for each quarter
print("\n" + "="*60)
print("STEP 5: GENERATING REPORTS")
print("="*60)

for quarter_name in QUARTERLY_TARGETS.keys():
    target = QUARTERLY_TARGETS[quarter_name]
    
    # Filter invoices for this quarter
    quarter_invoices = [
        inv for inv in all_invoices 
        if target['start'] <= inv['invoice_date'].date() <= target['end']
    ]
    
    if quarter_invoices:
        report_gen.generate_all_reports(
            quarter_name=quarter_name,
            invoices=quarter_invoices,
            target_sales=target['sales'],
            target_vat=target['vat']
        )

# Step 6: Generate overall summary
print("\n" + "="*60)
print("OVERALL SUMMARY")
print("="*60)

total_invoices = len(all_invoices)
total_sales = sum(inv['subtotal'] for inv in all_invoices)
total_vat = sum(inv['vat_amount'] for inv in all_invoices)

print(f"\nTotal Invoices Generated: {total_invoices:,}")
print(f"Total Sales (before VAT): {total_sales:,.2f} SAR")
print(f"Total VAT: {total_vat:,.2f} SAR")
print(f"Total Revenue: {total_sales + total_vat:,.2f} SAR")

print(f"\n{'='*60}")
print("QUARTERLY BREAKDOWN")
print(f"{'='*60}")

for result in quarterly_results:
    status = "✓ MATCHED" if result['matched'] else "✗ NOT MATCHED"
    print(f"\n{result['quarter']}: {status}")
    print(f"  Invoices: {result['invoice_count']}")
    print(f"  Sales: {result['actual_sales']:,.2f} (Target: {result['target_sales']:,.2f})")
    print(f"  VAT: {result['actual_vat']:,.2f} (Target: {result['target_vat']:,.2f})")

# Final summary
all_matched = all(r['matched'] for r in quarterly_results)
print(f"\n{'='*60}")
if all_matched:
    print("✓✓✓ ALL QUARTERS MATCHED! ✓✓✓")
else:
    print("⚠ SOME QUARTERS DID NOT MATCH")
print(f"{'='*60}")

print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\nOutput locations:")
print(f"  Sample PDFs: output/sample_invoices/")
print(f"  Reports: output/reports/")