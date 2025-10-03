"""
Excel Data Verification Script
Checks for common data issues in products.xlsx
"""

import pandas as pd
from decimal import Decimal

def verify_products_excel(file_path='input/products.xlsx'):
    """Verify products.xlsx for common data issues."""
    
    print("="*80)
    print("EXCEL DATA VERIFICATION - products.xlsx")
    print("="*80)
    
    # Read Excel
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    
    print(f"\nTotal products: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    issues = []
    warnings = []
    
    # Check 1: Price vs Cost relationship
    print("\n" + "="*80)
    print("CHECK 1: PRICE vs COST VALIDATION")
    print("="*80)
    
    price_issues = []
    for idx, row in df.iterrows():
        if pd.notna(row['unit_cost']) and pd.notna(row['unit_price_before_vat']):
            cost = Decimal(str(row['unit_cost']))
            price = Decimal(str(row['unit_price_before_vat']))
            
            if price < cost:
                price_issues.append({
                    'row': idx + 2,  # Excel row (accounting for header)
                    'item': row['item_name'],
                    'cost': float(cost),
                    'price': float(price),
                    'loss': float(cost - price),
                    'loss_pct': float((cost - price) / cost * 100)
                })
    
    if price_issues:
        print(f"\n❌ CRITICAL: Found {len(price_issues)} items with price < cost!")
        print("\nTop 10 worst cases:")
        price_issues.sort(key=lambda x: x['loss_pct'], reverse=True)
        for i, issue in enumerate(price_issues[:10]):
            print(f"\n{i+1}. Row {issue['row']}: {issue['item']}")
            print(f"   Cost: {issue['cost']:.2f} SAR")
            print(f"   Price: {issue['price']:.2f} SAR")
            print(f"   Loss: {issue['loss']:.2f} SAR ({issue['loss_pct']:.1f}%)")
        
        issues.append(f"{len(price_issues)} items have price < cost (will cause losses)")
    else:
        print("\n✅ PASSED: All prices are >= costs")
    
    # Check 2: Profit margin validation
    print("\n" + "="*80)
    print("CHECK 2: PROFIT MARGIN VALIDATION")
    print("="*80)
    
    low_margin_items = []
    negative_margin_items = []
    
    for idx, row in df.iterrows():
        if pd.notna(row['unit_cost']) and pd.notna(row['unit_price_before_vat']):
            cost = Decimal(str(row['unit_cost']))
            price = Decimal(str(row['unit_price_before_vat']))
            
            if price > 0:
                margin = ((price - cost) / cost * 100)
                
                if margin < 0:
                    negative_margin_items.append({
                        'row': idx + 2,
                        'item': row['item_name'],
                        'margin': float(margin)
                    })
                elif margin < 5:
                    low_margin_items.append({
                        'row': idx + 2,
                        'item': row['item_name'],
                        'margin': float(margin)
                    })
    
    if negative_margin_items:
        print(f"\n❌ CRITICAL: {len(negative_margin_items)} items have NEGATIVE margins!")
        for item in negative_margin_items[:5]:
            print(f"   Row {item['row']}: {item['item']} ({item['margin']:.1f}%)")
        issues.append(f"{len(negative_margin_items)} items have negative margins")
    
    if low_margin_items:
        print(f"\n⚠️  WARNING: {len(low_margin_items)} items have margins below 5%")
        warnings.append(f"{len(low_margin_items)} items have very low margins (<5%)")
    
    if not negative_margin_items and not low_margin_items:
        print("\n✅ PASSED: All items have healthy profit margins")
    
    # Check 3: Missing data
    print("\n" + "="*80)
    print("CHECK 3: MISSING DATA")
    print("="*80)
    
    required_columns = ['item_name', 'import_date', 'quantity', 'total_cost', 
                       'unit_cost', 'unit_price_before_vat', 'classification']
    
    missing_data = {}
    for col in required_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_data[col] = missing_count
    
    if missing_data:
        print(f"\n⚠️  WARNING: Found missing data:")
        for col, count in missing_data.items():
            print(f"   {col}: {count} missing values")
        warnings.append("Some required fields have missing data")
    else:
        print("\n✅ PASSED: No missing data in required columns")
    
    # Check 4: Duplicate items
    print("\n" + "="*80)
    print("CHECK 4: DUPLICATE DETECTION")
    print("="*80)
    
    duplicates = df[df.duplicated(subset=['item_name', 'import_date'], keep=False)]
    
    if len(duplicates) > 0:
        print(f"\n⚠️  WARNING: Found {len(duplicates)} potentially duplicate rows")
        print("\nFirst 5 duplicates:")
        for idx, row in duplicates.head().iterrows():
            print(f"   Row {idx + 2}: {row['item_name']} on {row['import_date']}")
        warnings.append(f"{len(duplicates)} potential duplicate entries")
    else:
        print("\n✅ PASSED: No duplicate entries found")
    
    # Check 5: Classification values
    print("\n" + "="*80)
    print("CHECK 5: CLASSIFICATION VALUES")
    print("="*80)
    
    expected_classifications = [
        "خارج حالة الفحص غير انتقائية",
        "محل الفحص سلع انتقائية",
        "محل الفحص سلع غير انتقائية"
    ]
    
    actual_classifications = df['classification'].unique()
    
    print(f"\nFound {len(actual_classifications)} unique classifications:")
    for classification in actual_classifications:
        count = len(df[df['classification'] == classification])
        print(f"   {classification}: {count} items")
    
    unexpected = [c for c in actual_classifications if c not in expected_classifications]
    if unexpected:
        print(f"\n⚠️  WARNING: Found unexpected classification values:")
        for c in unexpected:
            print(f"   {c}")
        warnings.append("Unexpected classification values found")
    else:
        print("\n✅ PASSED: All classifications are valid")
    
    # Check 6: Date ranges
    print("\n" + "="*80)
    print("CHECK 6: DATE RANGES")
    print("="*80)
    
    df['import_date'] = pd.to_datetime(df['import_date'], errors='coerce')
    min_date = df['import_date'].min()
    max_date = df['import_date'].max()
    
    print(f"\nImport date range:")
    print(f"   Earliest: {min_date}")
    print(f"   Latest: {max_date}")
    
    if min_date.year < 2023 or max_date.year > 2024:
        warnings.append("Import dates outside expected range (2023-2024)")
    
    # Check 7: Quantity validation
    print("\n" + "="*80)
    print("CHECK 7: QUANTITY VALIDATION")
    print("="*80)
    
    zero_qty = df[df['quantity'] == 0]
    negative_qty = df[df['quantity'] < 0]
    
    if len(zero_qty) > 0:
        print(f"\n⚠️  WARNING: {len(zero_qty)} items have zero quantity")
        warnings.append(f"{len(zero_qty)} items with zero quantity")
    
    if len(negative_qty) > 0:
        print(f"\n❌ CRITICAL: {len(negative_qty)} items have negative quantity!")
        issues.append(f"{len(negative_qty)} items with negative quantity")
    
    if len(zero_qty) == 0 and len(negative_qty) == 0:
        print("\n✅ PASSED: All quantities are valid")
    
    # Final Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    if not issues and not warnings:
        print("\n🎉 EXCELLENT! No issues found in Excel data!")
        print("Your data is ready for invoice generation.")
        return True
    else:
        if issues:
            print(f"\n❌ CRITICAL ISSUES FOUND: {len(issues)}")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            print("\n⚠️  These MUST be fixed before running the system!")
        
        if warnings:
            print(f"\n⚠️  WARNINGS: {len(warnings)}")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
            print("\nThese may cause issues but are not critical.")
        
        if price_issues:
            print("\n" + "="*80)
            print("RECOMMENDED FIX FOR PRICE ISSUES")
            print("="*80)
            print("\nOption 1: Fix manually in Excel")
            print("  - Open products.xlsx")
            print("  - For each flagged item, ensure unit_price_before_vat > unit_cost")
            print("  - Recalculate: price = cost × (1 + profit_margin/100)")
            
            print("\nOption 2: Auto-fix in code (add to excel_reader.py after line 86):")
            print("  if unit_price_before_vat <= unit_cost:")
            print("      unit_price_before_vat = unit_cost * Decimal('1.15')  # Force 15% margin")
            
            # Save problem items to Excel
            try:
                problem_df = pd.DataFrame(price_issues)
                problem_df.to_excel('PRICE_PROBLEMS.xlsx', index=False)
                print("\n💾 Saved problem items to: PRICE_PROBLEMS.xlsx")
            except:
                pass
        
        return False


if __name__ == "__main__":
    verify_products_excel()