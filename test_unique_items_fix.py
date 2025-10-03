"""
Test that the unique items fix works correctly.
Verify that we only get ONE record per item, not multiple batches.
"""

from excel_reader import read_products
from inventory import InventoryManager


def test_unique_items():
    """Test that inventory returns unique items only."""
    
    print("="*80)
    print("TESTING UNIQUE ITEMS FIX")
    print("="*80)
    
    # Load products
    print("\n1. Loading products...")
    products = read_products('input/products.xlsx')
    print(f"   Total product batches: {len(products)}")
    
    # Count unique items
    unique_names = set(p['item_name'] for p in products)
    print(f"   Unique item names: {len(unique_names)}")
    
    # Initialize inventory
    print("\n2. Initializing inventory...")
    inventory = InventoryManager(products)
    
    # Test get_all_available_items
    print("\n3. Testing get_all_available_items()...")
    all_items = inventory.get_all_available_items()
    print(f"   Returned items: {len(all_items)}")
    
    # Check for duplicates
    item_names = [p['item_name'] for p in all_items]
    unique_returned = set(item_names)
    print(f"   Unique items: {len(unique_returned)}")
    
    if len(item_names) == len(unique_returned):
        print("   ✅ No duplicates - each item appears only once!")
    else:
        print("   ❌ Duplicates found!")
        # Find duplicates
        from collections import Counter
        counts = Counter(item_names)
        duplicates = {name: count for name, count in counts.items() if count > 1}
        print(f"   Duplicate items: {len(duplicates)}")
        for name, count in list(duplicates.items())[:5]:
            print(f"     - {name}: {count} times")
    
    # Test specific items
    print("\n4. Testing specific items...")
    test_items = [
        "Caffee classic 200GM",
        "Caffee classic 15*200GM",
        "أجبان"
    ]
    
    for item_name in test_items:
        # Count batches in original data
        batches = [p for p in products if p['item_name'] == item_name]
        # Count in returned items
        returned = [p for p in all_items if p['item_name'] == item_name]
        
        print(f"\n   {item_name}:")
        print(f"     Batches in Excel: {len(batches)}")
        print(f"     Returned by inventory: {len(returned)}")
        
        if len(batches) > 0:
            print(f"     Excel prices: {[float(b['unit_price_before_vat']) for b in batches]}")
        
        if len(returned) > 0:
            print(f"     Returned price: {float(returned[0]['unit_price_before_vat'])}")
        
        if len(returned) == 1:
            print(f"     ✅ Correct - only ONE record returned")
        elif len(returned) == 0:
            print(f"     ⚠️  No stock available")
        else:
            print(f"     ❌ ERROR - {len(returned)} records returned (should be 1)")
    
    print(f"\n{'='*80}")
    if len(item_names) == len(unique_returned):
        print("✅ FIX SUCCESSFUL - Inventory returns unique items only!")
    else:
        print("❌ FIX INCOMPLETE - Still returning duplicate items")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_unique_items()
