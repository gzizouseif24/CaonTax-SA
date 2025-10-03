"""
Check what prices are actually loaded from Excel by excel_reader.py
"""

from excel_reader import read_products

print("="*80)
print("CHECKING LOADED PRODUCTS")
print("="*80)

products = read_products('input/products.xlsx')

# Find specific items
test_items = ["Caffee classic 200GM", "Caffee classic 15*200GM"]

for item_name in test_items:
    matching = [p for p in products if p['item_name'] == item_name]
    
    print(f"\n{item_name}:")
    print(f"  Found {len(matching)} batch(es)")
    
    for i, product in enumerate(matching):
        print(f"\n  Batch {i+1}:")
        print(f"    unit_cost: {float(product['unit_cost']):.2f}")
        print(f"    profit_margin_pct: {float(product['profit_margin_pct']):.2f}%")
        print(f"    unit_price_before_vat: {float(product['unit_price_before_vat']):.2f}")
        print(f"    customs_declaration: {product['customs_declaration']}")
        print(f"    import_date: {product['import_date']}")
        
        # Check calculation
        from decimal import Decimal
        cost = product['unit_cost']
        margin = product['profit_margin_pct']
        price = product['unit_price_before_vat']
        
        calculated = cost * (1 + margin / 100)
        
        print(f"    Calculated price: {float(calculated):.2f}")
        print(f"    Difference: {float(price - calculated):.2f}")

print("\n" + "="*80)
