"""
Price validation: Ensures invoices use authentic Excel prices only

This standalone script validates that all generated invoice prices
exactly match the original Excel prices (unit_price_before_vat).
"""

import pandas as pd
from decimal import Decimal
import json


def load_excel_prices(excel_path='input/products.xlsx'):
    """Load original Excel prices and build lookup dictionary."""
    
    print(f"Loading prices from {excel_path}...")
    df = pd.read_excel(excel_path)
    df.columns = df.columns.str.strip()
    
    # Build price lookup: {item_name: [list of valid prices]}
    excel_prices = {}
    for _, row in df.iterrows():
        item_name = str(row['item_name']).strip()
        price = Decimal(str(row['unit_price_before_vat']))
        
        if item_name not in excel_prices:
            excel_prices[item_name] = []
        excel_prices[item_name].append(price)
    
    print(f"✓ Loaded {len(excel_prices)} unique items from Excel")
    
    # Show items with multiple prices
    multi_price_items = {k: v for k, v in excel_prices.items() if len(v) > 1}
    if multi_price_items:
        print(f"  Note: {len(multi_price_items)} items have multiple batches with different prices")
    
    return excel_prices


def load_invoices_from_json(json_path='debug_results.json'):
    """Load invoices from the debug results JSON file."""
    
    print(f"\nLoading invoices from {json_path}...")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Note: The current debug_results.json doesn't include invoices
        # This is a placeholder for when invoices are added to the output
        print("⚠️  Note: debug_results.json doesn't contain invoice details")
        print("   Run testing.py first to generate invoices")
        return []
    
    except FileNotFoundError:
        print(f"❌ File not found: {json_path}")
        print("   Run testing.py first to generate results")
        return []
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return []


def validate_invoice_prices(invoices, excel_prices):
    """Compare invoice prices against original Excel prices."""
    
    print(f"\n{'='*80}")
    print("VALIDATING INVOICE PRICES")
    print("="*80)
    
    if not invoices:
        print("⚠️  No invoices to validate")
        return True
    
    mismatches = []
    total_line_items = 0
    
    for invoice in invoices:
        for line_item in invoice.get('line_items', []):
            total_line_items += 1
            
            item_name = line_item['item_name']
            used_price = Decimal(str(line_item['unit_price']))
            
            valid_prices = excel_prices.get(item_name, [])
            
            # Check if price matches any valid Excel price
            price_match = any(abs(used_price - vp) < Decimal("0.0001") for vp in valid_prices)
            
            if not price_match:
                mismatches.append({
                    'invoice': invoice['invoice_number'],
                    'item': item_name,
                    'used_price': float(used_price),
                    'valid_prices': [float(p) for p in valid_prices]
                })
    
    # Report results
    print(f"\nTotal line items checked: {total_line_items}")
    
    if len(mismatches) == 0:
        print("\n✅✅✅ VALIDATED: All invoice prices match Excel! ✅✅✅")
        print(f"All {total_line_items} line items use authentic Excel prices")
        return True
    else:
        print(f"\n❌ FOUND {len(mismatches)} PRICE MISMATCHES:")
        
        # Show first 10 mismatches
        for i, m in enumerate(mismatches[:10]):
            print(f"\n{i+1}. Invoice: {m['invoice']}")
            print(f"   Item: {m['item']}")
            print(f"   Used price: {m['used_price']:.2f} SAR")
            print(f"   Valid Excel prices: {[f'{p:.2f}' for p in m['valid_prices']]} SAR")
        
        if len(mismatches) > 10:
            print(f"\n   ... and {len(mismatches) - 10} more mismatches")
        
        return False


def main():
    """Run standalone price validation."""
    
    print("="*80)
    print("STANDALONE PRICE VALIDATION")
    print("="*80)
    print("\nThis script validates that all invoice prices match Excel prices.")
    print("It requires:")
    print("  1. input/products.xlsx (original Excel file)")
    print("  2. Invoices from testing.py (currently integrated)")
    
    # Load Excel prices
    excel_prices = load_excel_prices()
    
    # Load invoices
    # Note: Currently, invoices are not saved to JSON
    # This validation is integrated into testing.py instead
    invoices = load_invoices_from_json()
    
    # Validate
    if invoices:
        is_valid = validate_invoice_prices(invoices, excel_prices)
        
        print(f"\n{'='*80}")
        if is_valid:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")
        print("="*80)
    else:
        print(f"\n{'='*80}")
        print("ℹ️  INTEGRATION NOTE")
        print("="*80)
        print("\nPrice validation is integrated into testing.py")
        print("Run: python testing.py")
        print("\nThe validation will automatically check all invoice prices")
        print("against the original Excel prices during the test run.")


if __name__ == "__main__":
    main()
