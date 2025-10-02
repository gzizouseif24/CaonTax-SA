from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from report_generator import ReportGenerator
from config import QUARTERLY_TARGETS
from datetime import date

print("="*60)
print("TESTING REPORT GENERATION - Q3-2023")
print("="*60)

# Load data
print("\n1. Loading data...")
products = read_products('input/products.xlsx')
customers_2023 = read_customers('input/customers_2023_fabricated.xlsx')
holidays = read_holidays('input/holidays.xlsx')

# Initialize
inventory = InventoryManager(products)
simulator = SalesSimulator(inventory, holidays)
aligner = QuarterlyAligner(simulator)

# Generate Q3-2023 invoices
print("\n2. Generating Q3-2023 invoices...")
q3_target = QUARTERLY_TARGETS["Q3-2023"]
q3_customers = [
    c for c in customers_2023
    if q3_target['start'] <= c['purchase_date'] <= q3_target['end']
]

invoices = aligner.align_quarter(
    quarter_name="Q3-2023",
    start_date=q3_target['start'],
    end_date=q3_target['end'],
    target_sales=q3_target['sales'],
    target_vat=q3_target['vat'],
    vat_customers=q3_customers
)

print(f"\n✓ Generated {len(invoices)} invoices")

# Initialize report generator
print("\n3. Initializing report generator...")
report_gen = ReportGenerator(output_dir='output/reports')

# Generate all reports
print("\n4. Generating reports...")
report_paths = report_gen.generate_all_reports(
    quarter_name="Q3-2023",
    invoices=invoices,
    target_sales=q3_target['sales'],
    target_vat=q3_target['vat']
)

# Display summary
print("\n" + "="*60)
print("REPORT GENERATION COMPLETE")
print("="*60)
print(f"\nGenerated files:")
print(f"  1. Detailed Sales: {report_paths['detailed']}")
print(f"  2. Invoice Summary: {report_paths['summary']}")
print(f"  3. Quarterly Summary: {report_paths['quarterly']}")
print(f"\nOpen these files to verify:")
print(f"  - Arabic column headers display correctly")
print(f"  - Numbers format properly")
print(f"  - All data is accurate")
print(f"  - Totals match alignment results")