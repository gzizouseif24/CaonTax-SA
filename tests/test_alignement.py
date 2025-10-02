from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from config import QUARTERLY_TARGETS
from datetime import date

print("="*60)
print("TESTING ALIGNMENT ALGORITHM - Q3-2023")
print("="*60)

# Load data
print("\nLoading data...")
products = read_products('input/products.xlsx')
customers_2023 = read_customers('input/customers_2023_fabricated.xlsx')
holidays = read_holidays('input/holidays.xlsx')

# Initialize
inventory = InventoryManager(products)
simulator = SalesSimulator(inventory, holidays)
aligner = QuarterlyAligner(simulator)

# Get Q3-2023 data
q3_target = QUARTERLY_TARGETS["Q3-2023"]
start_date = q3_target['start']
end_date = q3_target['end']
target_sales = q3_target['sales']
target_vat = q3_target['vat']

# Filter customers for Q3-2023
q3_customers = [
    c for c in customers_2023
    if start_date <= c['purchase_date'] <= end_date
]

print(f"\nQ3-2023 Setup:")
print(f"  Period: {start_date} to {end_date}")
print(f"  VAT Customers: {len(q3_customers)}")
print(f"  Target Sales: {target_sales:,.2f} SAR")
print(f"  Target VAT: {target_vat:,.2f} SAR")

# Run alignment
invoices = aligner.align_quarter(
    quarter_name="Q3-2023",
    start_date=start_date,
    end_date=end_date,
    target_sales=target_sales,
    target_vat=target_vat,
    vat_customers=q3_customers
)

# Verify results
print("\n" + "="*60)
print("VERIFICATION")
print("="*60)

actual_sales = sum(inv['subtotal'] for inv in invoices)
actual_vat = sum(inv['vat_amount'] for inv in invoices)
actual_total = sum(inv['total'] for inv in invoices)

print(f"\nInvoices generated: {len(invoices)}")
print(f"\nSales before VAT:")
print(f"  Target: {target_sales:,.2f} SAR")
print(f"  Actual: {actual_sales:,.2f} SAR")
print(f"  Diff: {abs(actual_sales - target_sales):.2f} SAR")

print(f"\nVAT:")
print(f"  Target: {target_vat:,.2f} SAR")
print(f"  Actual: {actual_vat:,.2f} SAR")
print(f"  Diff: {abs(actual_vat - target_vat):.2f} SAR")

print(f"\nTotal:")
print(f"  Target: {target_sales + target_vat:,.2f} SAR")
print(f"  Actual: {actual_total:,.2f} SAR")

# Sample invoices
print("\n" + "="*60)
print("SAMPLE INVOICES")
print("="*60)

for inv in invoices[:5]:
    print(f"\n{inv['invoice_number']} ({inv['invoice_type']}):")
    print(f"  Customer: {inv['customer_name']}")
    print(f"  Items: {len(inv['line_items'])}")
    print(f"  Subtotal: {inv['subtotal']:,.2f} SAR")
    print(f"  VAT: {inv['vat_amount']:,.2f} SAR")
    print(f"  Total: {inv['total']:,.2f} SAR")