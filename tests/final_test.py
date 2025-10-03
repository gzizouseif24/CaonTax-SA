"""
Final comprehensive test after unique items fix.
This should show 100% price match with Excel.
"""

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from config import QUARTERLY_TARGETS
from decimal import Decimal
import pandas as pd


def final_test():
    """Run final test with unique items fix."""
    
    print("="*80)
    print("FINAL COMPREHENSIVE TEST")
    print("="*80)
    
    # Load data
    print("\n1. Loading data...")
    products = read_products('input/products.xlsx')
    customers_2024 = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Initialize
    print("2. Initializing system...")
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator)
    
    # Test with Q2-2024
    print("\n3. Generating Q2-2024 invoices...")
    quarter_name = "Q2-2024"
    target = QUARTERLY_TARGETS[quarter_name]
    
    vat_customers = [
        c for c in customers_2024
        if target['start'] <= c['purchase_date'] <= target['end']
    ]
    
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=target['sales'],
        target_vat=target['vat'],
        vat_customers=vat_customers,
        allow_variance=False
    )
    
    print(f"\n4. Generated {len(invoices)} invoices")
    
    # Build Excel price lookup
    print("\n5. Building Excel price lookup...")
    excel_prices = {}
    for product in products:
        item_name = product['item_name']
        price = product['unit_price_before_vat']
        
        if item_name not in excel_prices:
            excel_prices[item_name] = []
        excel_prices[item_name].append(price)
    
    # Check prices
    print("\n6. Validating prices...")
    total_items = 0
    exact_matches = 0
    mismatches = []
    
    for invoice in invoices:
        for line_item in invoice['line_items']:
            total_items += 1
            item_name = line_item['item_name']
            invoice_price = line_item['unit_price']
            
            valid_prices = excel_prices.get(item_name, [])
            price_match = any(abs(invoice_price - vp) < Decimal("0.01") for vp in valid_prices)
            
            if price_match:
                exact_matches += 1
            else:
                mismatches.append({
                    'item': item_name,
                    'invoice_price': float(invoice_price),
                    'excel_prices': [float(p) for p in valid_prices]
                })
    
    # Results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Total line items: {total_items}")
    print(f"Exact matches: {exact_matches} ({exact_matches/total_items*100:.1f}%)")
    print(f"Mismatches: {len(mismatches)} ({len(mismatches)/total_items*100:.1f}%)")
    
    if len(mismatches) == 0:
        print(f"\n✅✅✅ PERFECT! 100% PRICE MATCH! ✅✅✅")
    else:
        print(f"\n⚠️  Still have {len(mismatches)} mismatches")
        print("\nFirst 10 mismatches:")
        for m in mismatches[:10]:
            print(f"  - {m['item']}: Invoice={m['invoice_price']:.2f}, Excel={m['excel_prices']}")
    
    # Check specific items
    print(f"\n{'='*80}")
    print("CHECKING SPECIFIC ITEMS")
    print(f"{'='*80}")
    
    test_items = ["Caffee classic 15*200GM", "Caffee classic 200GM"]
    
    for test_item in test_items:
        item_lines = [line for inv in invoices for line in inv['line_items'] if line['item_name'] == test_item]
        
        if item_lines:
            prices_used = set(float(line['unit_price']) for line in item_lines)
            excel_prices_for_item = excel_prices.get(test_item, [])
            
            print(f"\n{test_item}:")
            print(f"  Occurrences: {len(item_lines)}")
            print(f"  Invoice prices used: {sorted([f'{p:.2f}' for p in prices_used])}")
            print(f"  Excel prices: {sorted([f'{float(p):.2f}' for p in excel_prices_for_item])}")
            
            if len(prices_used) == 1:
                print(f"  ✅ Consistent - only ONE price used")
            else:
                print(f"  ❌ Inconsistent - {len(prices_used)} different prices used")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    final_test()
