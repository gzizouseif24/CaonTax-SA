"""
Show the problem: Multiple batches with different prices for same item.
"""

from excel_reader import read_products
from collections import defaultdict


def show_problem():
    """Show items with multiple batches and different prices."""
    
    print("="*80)
    print("SHOWING THE PROBLEM: Multiple Batches = Different Prices")
    print("="*80)
    
    # Load products
    products = read_products('input/products.xlsx')
    
    # Group by item name
    by_item = defaultdict(list)
    for p in products:
        by_item[p['item_name']].append(p)
    
    # Find items with multiple batches
    print("\nItems with multiple batches:")
    print("="*80)
    
    test_items = [
        "Caffee classic 200GM",
        "Caffee classic 15*200GM",
        "أجبان"
    ]
    
    for item_name in test_items:
        batches = by_item.get(item_name, [])
        
        if len(batches) > 0:
            print(f"\n{item_name}:")
            print(f"  Total batches: {len(batches)}")
            
            prices = [float(b['unit_price_before_vat']) for b in batches]
            unique_prices = set(prices)
            
            print(f"  Prices: {sorted(prices)}")
            print(f"  Unique prices: {len(unique_prices)}")
            
            if len(unique_prices) > 1:
                print(f"  ⚠️  PROBLEM: Multiple different prices!")
                print(f"  When random.choice() picks a batch, it might pick:")
                for i, batch in enumerate(batches):
                    print(f"    Batch {i+1}: {float(batch['unit_price_before_vat']):.2f} SAR (Customs: {batch['customs_declaration']})")
            else:
                print(f"  ✅ OK: All batches have same price")
    
    print(f"\n{'='*80}")
    print("SOLUTION:")
    print("="*80)
    print("""
The fix ensures that get_available_items_by_classification() returns
only ONE record per unique item name, not multiple batches.

This way, when random.choice() picks an item, it always gets the
same price for that item (the first available batch's price).
    """)
    print(f"{'='*80}\n")


if __name__ == "__main__":
    show_problem()
