"""
Test the FINAL fix - reading prices from Excel instead of calculating.
"""

from excel_reader import read_products

print("="*80)
print("TESTING FINAL FIX - Reading Prices from Excel")
print("="*80)

products = read_products('input/products.xlsx')

# Check specific items
test_items = ["Caffee classic 200GM", "Caffee classic 15*200GM"]

print("\nExpected prices from Excel:")
print("  Caffee classic 200GM: 28.86 SAR")
print("  Caffee classic 15*200GM: 24.23 SAR")

print("\nActual prices loaded:")

for item_name in test_items:
    matching = [p for p in products if p['item_name'] == item_name]
    
    if matching:
        product = matching[0]
        price = float(product['unit_price_before_vat'])
        cost = float(product['unit_cost'])
        
        print(f"\n{item_name}:")
        print(f"  Loaded price: {price:.2f} SAR")
        print(f"  Cost: {cost:.2f} SAR")
        print(f"  Calculated (cost * 1.15): {cost * 1.15:.2f} SAR")
        
        # Check if it matches expected
        if item_name == "Caffee classic 200GM" and abs(price - 28.86) < 0.01:
            print(f"  ✅ CORRECT! Matches Excel (28.86)")
        elif item_name == "Caffee classic 15*200GM" and abs(price - 24.23) < 0.01:
            print(f"  ✅ CORRECT! Matches Excel (24.23)")
        else:
            print(f"  ❌ WRONG! Doesn't match Excel")

print("\n" + "="*80)
print("If prices match Excel, the fix is successful!")
print("="*80 + "\n")
