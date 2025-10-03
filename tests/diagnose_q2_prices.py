"""
Diagnostic: Compare Q2-2024 sales report prices with products.xlsx
Find out why prices like "Caffee classic 15*200GM" are different.
"""

import pandas as pd
from decimal import Decimal


def diagnose_q2_prices():
    """Compare Q2 report prices with products Excel."""
    
    print("="*80)
    print("Q2-2024 PRICE DIAGNOSTIC")
    print("="*80)
    
    # 1. Load products Excel
    print("\n1. Loading products.xlsx...")
    products_df = pd.read_excel('input/products.xlsx')
    products_df.columns = products_df.columns.str.strip()
    
    print(f"   Columns: {list(products_df.columns)}")
    print(f"   Total rows: {len(products_df)}")
    
    # Build lookup: item_name -> list of (price, cost, customs_declaration, import_date)
    products_lookup = {}
    for idx, row in products_df.iterrows():
        item_name = str(row['item_name']).strip()
        price = Decimal(str(row['unit_price_before_vat']))
        cost = Decimal(str(row['unit_cost']))
        customs = str(row['customs_declaration'])
        import_date = row['import_date']
        
        if item_name not in products_lookup:
            products_lookup[item_name] = []
        
        products_lookup[item_name].append({
            'price': price,
            'cost': cost,
            'customs': customs,
            'import_date': import_date,
            'row_index': idx + 2  # Excel row (1-indexed + header)
        })
    
    print(f"   Unique items: {len(products_lookup)}")
    
    # Show specific items
    print("\n2. Checking specific items from products.xlsx:")
    
    test_items = [
        "Caffee classic 200GM",
        "Caffee classic 15*200GM"
    ]
    
    for item in test_items:
        if item in products_lookup:
            print(f"\n   {item}:")
            for i, batch in enumerate(products_lookup[item]):
                print(f"     Batch {i+1} (Row {batch['row_index']}): Price={float(batch['price']):.2f}, Cost={float(batch['cost']):.2f}, Customs={batch['customs']}")
        else:
            print(f"\n   {item}: NOT FOUND")
    
    # 2. Load Q2 sales report
    print("\n3. Loading Q2-2024 sales report...")
    try:
        q2_df = pd.read_excel('output/reports/Q2-2024_detailed_sales.xlsx')
        print(f"   Total line items: {len(q2_df)}")
        print(f"   Columns: {list(q2_df.columns)}")
    except FileNotFoundError:
        print("   ❌ Q2-2024 report not found. Run: python test_reports_q2.py first")
        return
    
    # 3. Compare prices
    print("\n4. Comparing prices...")
    print("="*80)
    
    mismatches = []
    exact_matches = 0
    
    for idx, row in q2_df.iterrows():
        item_name = row['اسم الصنف']
        invoice_price = Decimal(str(row['سعر الوحدة (قبل الضريبة)']))
        
        # Get Excel prices for this item
        excel_batches = products_lookup.get(item_name, [])
        
        if not excel_batches:
            mismatches.append({
                'item': item_name,
                'invoice_price': float(invoice_price),
                'excel_prices': 'NOT FOUND',
                'issue': 'Item not in Excel'
            })
            continue
        
        # Check if invoice price matches ANY batch price
        excel_prices = [b['price'] for b in excel_batches]
        price_match = any(abs(invoice_price - ep) < Decimal("0.01") for ep in excel_prices)
        
        if price_match:
            exact_matches += 1
        else:
            mismatches.append({
                'item': item_name,
                'invoice_price': float(invoice_price),
                'excel_prices': [float(p) for p in excel_prices],
                'excel_batches': excel_batches,
                'issue': 'Price mismatch'
            })
    
    # 4. Report results
    print(f"\n{'='*80}")
    print("DIAGNOSTIC RESULTS")
    print(f"{'='*80}")
    print(f"Total line items: {len(q2_df)}")
    print(f"Exact matches: {exact_matches} ({exact_matches/len(q2_df)*100:.1f}%)")
    print(f"Mismatches: {len(mismatches)} ({len(mismatches)/len(q2_df)*100:.1f}%)")
    
    if len(mismatches) > 0:
        print(f"\n{'='*80}")
        print("❌ PRICE MISMATCHES FOUND")
        print(f"{'='*80}")
        
        # Focus on the specific items mentioned
        print("\n🔍 SPECIFIC ITEMS ANALYSIS:")
        
        for test_item in test_items:
            item_mismatches = [m for m in mismatches if m['item'] == test_item]
            
            if item_mismatches:
                print(f"\n{test_item}:")
                print(f"  Occurrences in Q2 report: {len(item_mismatches)}")
                
                # Get unique invoice prices used
                unique_prices = set(m['invoice_price'] for m in item_mismatches)
                print(f"  Invoice prices used: {sorted([f'{p:.2f}' for p in unique_prices])}")
                
                # Get Excel prices
                if item_mismatches[0]['excel_prices'] != 'NOT FOUND':
                    excel_prices = item_mismatches[0]['excel_prices']
                    print(f"  Excel prices: {sorted([f'{p:.2f}' for p in excel_prices])}")
                    
                    # Show batch details
                    print(f"  Excel batches:")
                    for i, batch in enumerate(item_mismatches[0]['excel_batches']):
                        print(f"    Batch {i+1} (Row {batch['row_index']}): Price={float(batch['price']):.2f}, Cost={float(batch['cost']):.2f}")
                else:
                    print(f"  Excel prices: NOT FOUND IN EXCEL")
        
        # Show all mismatches grouped by item
        print(f"\n{'='*80}")
        print("ALL MISMATCHES (Grouped by Item):")
        print(f"{'='*80}")
        
        from collections import defaultdict
        by_item = defaultdict(list)
        for m in mismatches:
            by_item[m['item']].append(m)
        
        # Sort by number of occurrences
        sorted_items = sorted(by_item.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (item_name, item_mismatches) in enumerate(sorted_items[:20]):
            print(f"\n{i+1}. {item_name}")
            print(f"   Occurrences: {len(item_mismatches)}")
            
            unique_prices = set(m['invoice_price'] for m in item_mismatches)
            print(f"   Invoice prices: {sorted([f'{p:.2f}' for p in unique_prices])}")
            
            if item_mismatches[0]['excel_prices'] != 'NOT FOUND':
                excel_prices = item_mismatches[0]['excel_prices']
                print(f"   Excel prices: {sorted([f'{p:.2f}' for p in excel_prices])}")
                
                # Calculate difference
                if len(unique_prices) == 1 and len(excel_prices) == 1:
                    diff = list(unique_prices)[0] - excel_prices[0]
                    diff_pct = (diff / excel_prices[0] * 100) if excel_prices[0] > 0 else 0
                    print(f"   Difference: {diff:.2f} SAR ({diff_pct:.1f}%)")
    else:
        print(f"\n✅ PERFECT! All prices match Excel")
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    diagnose_q2_prices()
