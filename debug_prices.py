from excel_reader import read_products
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from config import QUARTERLY_TARGETS
from datetime import date

# Load data
print("Loading products...")
products = read_products('input/products.xlsx')

# Show first few products and their prices
print("\nFirst 5 products from Excel:")
for i, product in enumerate(products[:5]):
    print(f"{i+1}. {product['item_name']}")
    print(f"   Price: {product['unit_price_before_vat']} (type: {type(product['unit_price_before_vat'])})")

# Initialize
inventory = InventoryManager(products)
simulator = SalesSimulator(inventory, [])
aligner = QuarterlyAligner(simulator)

# Generate a small test invoice
print("\nGenerating test invoice...")
q3_target = QUARTERLY_TARGETS["Q3-2023"]

# Create a simple test invoice
test_invoices = aligner.align_quarter(
    quarter_name="Q3-2023",
    start_date=q3_target['start'],
    end_date=q3_target['end'],
    target_sales=q3_target['sales'],
    target_vat=q3_target['vat'],
    vat_customers=[]
)

# Show first invoice line items
if test_invoices:
    first_invoice = test_invoices[0]
    print(f"\nFirst invoice: {first_invoice['invoice_number']}")
    print("Line items:")
    for item in first_invoice['line_items'][:3]:
        print(f"  - {item['item_name']}")
        print(f"    Invoice Price: {item['unit_price']} (type: {type(item['unit_price'])})")
        
        # Find matching product
        matching = [p for p in products if p['item_name'] == item['item_name']]
        if matching:
            expected = matching[0]['unit_price_before_vat']
            print(f"    Expected Price: {expected} (type: {type(expected)})")
            print(f"    Match: {item['unit_price'] == expected}")
        print()