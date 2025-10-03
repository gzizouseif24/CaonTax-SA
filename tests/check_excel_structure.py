"""
Check the Excel file structure to understand the pricing.
"""

import pandas as pd
from decimal import Decimal

print("="*80)
print("CHECKING EXCEL FILE STRUCTURE")
print("="*80)

# Load Excel
df = pd.read_excel('input/products.xlsx')
df.columns = df.columns.str.strip()

print("\nColumns:", list(df.columns))

# Check specific items
test_items = ["Caffee classic 200GM", "Caffee classic 15*200GM"]

for item_name in test_items:
    rows = df[df['item_name'].str.contains(item_name, na=False, regex=False)]
    
    if len(rows) > 0:
        row = rows.iloc[0]
        
        print(f"\n{item_name}:")
        print(f"  unit_cost: {row['unit_cost']:.2f}")
        print(f"  profit_margin_pct: {row['profit_margin_pct']:.2f}%")
        print(f"  unit_price_before_vat: {row['unit_price_before_vat']:.2f}")
        
        # Calculate what the price should be
        cost = Decimal(str(row['unit_cost']))
        margin_pct = Decimal(str(row['profit_margin_pct']))
        
        calculated_price = cost * (1 + margin_pct / 100)
        excel_price = Decimal(str(row['unit_price_before_vat']))
        
        print(f"  Calculated (cost * (1 + margin%)): {float(calculated_price):.2f}")
        print(f"  Difference: {float(excel_price - calculated_price):.2f}")
        
        if abs(excel_price - calculated_price) < Decimal("0.01"):
            print(f"  ✅ Excel price matches calculation")
        else:
            print(f"  ⚠️  Excel price doesn't match calculation")
            
            # Try reverse calculation
            reverse_margin = ((excel_price / cost) - 1) * 100
            print(f"  Reverse calculated margin: {float(reverse_margin):.2f}%")

print("\n" + "="*80)
