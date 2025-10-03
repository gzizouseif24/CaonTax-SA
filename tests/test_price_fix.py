"""
Test the price fix - verify that invoice prices now match Excel exactly.
"""

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from config import QUARTERLY_TARGETS
import pandas as pd
from decimal import Decimal


def test_price_fix():
    """Test that prices now match Excel."""
    
    print("="*80)
    print("TESTING PRICE FIX")
    print("="*80)
    
    # Load data
    print("\n1. Loading data...")
    products = read_products('input/products.xlsx')
    customers_2024 = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Initialize system
    print("2. Initializing system...")
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator)
    
    # Generate a small test - just 5 invoices
    print("\n3. Generating test invoices...")
    quarter_name = "Q1-2024"
    target = QUARTERLY_TARGETS[quarter_name]
    
    vat_customers = [
        c for c in customers_2024
        if target['start'] <= c['purchase_date'] <= target['end']
    ][:2]  # Just 2 customers for quick test
    
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=Decimal("50000"),  # Small target for quick test
        target_vat=Decimal("7500"),
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
    print("\n6. Checking invoice prices against Excel...")
    total_items = 0
    exact_matches = 0
    mismatches = []
    
    for invoice in invoices:
        for line_item in invoice['line_items']:
            total_items += 1
            item_name = line_item['item_name']
            invoice_price = line_item['unit_price']
            
            valid_prices = excel_prices.get(item_name, [])
            
            # Check if invoice price matches ANY valid Excel price
            price_match = any(abs(invoice_price - vp) < Decimal("0.0001") for vp in valid_prices)
            
            if price_match:
                exact_matches += 1
            else:
                mismatches.append({
                    'item': item_name,
                    'invoice_price': float(invoice_price),
                    'excel_prices': [float(p) for p in valid_prices]
                })
    
    # Report results
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"Total line items: {total_items}")
    print(f"Exact matches: {exact_matches} ({exact_matches/total_items*100:.1f}%)")
    print(f"Mismatches: {len(mismatches)} ({len(mismatches)/total_items*100:.1f}%)")
    
    if len(mismatches) == 0:
        print(f"\n✅✅✅ SUCCESS! ALL PRICES MATCH EXCEL EXACTLY! ✅✅✅")
    elif len(mismatches) < total_items * 0.1:  # Less than 10%
        print(f"\n✅ GOOD! Over 90% of prices match Excel")
        print(f"\nRemaining mismatches (showing first 5):")
        for m in mismatches[:5]:
            print(f"  - {m['item']}: Invoice={m['invoice_price']:.2f}, Excel={m['excel_prices']}")
    else:
        print(f"\n❌ STILL ISSUES - {len(mismatches)} mismatches found")
        print(f"\nFirst 10 mismatches:")
        for m in mismatches[:10]:
            print(f"  - {m['item']}: Invoice={m['invoice_price']:.2f}, Excel={m['excel_prices']}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    test_price_fix()
