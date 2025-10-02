from excel_reader import read_products
from inventory import InventoryManager

def test_inventory():
    print("=" * 60)
    print("TESTING INVENTORY MANAGER")
    print("=" * 60)
    
    # Load products
    products = read_products("input/products.xlsx")
    
    # Initialize inventory
    inventory = InventoryManager(products)
    
    # Test 1: Get summary
    print("\nTest 1: Inventory Summary")
    summary = inventory.get_inventory_summary()
    print(f"  Total batches: {summary['total_batches']}")
    print(f"  Batches with stock: {summary['batches_with_stock']}")
    print(f"  Total quantity: {summary['total_quantity_remaining']}")
    
    # Test 2: Count by classification
    print("\nTest 2: Items by Classification")
    counts = inventory.get_items_by_classification_count()
    for classification, count in counts.items():
        print(f"  {classification}: {count} items")
    
    # Test 3: Get available items for a classification
    print("\nTest 3: Available Items (first classification)")
    first_classification = list(counts.keys())[0]
    items = inventory.get_available_items_by_classification(first_classification)
    print(f"  Found {len(items)} items for '{first_classification}'")
    if items:
        print(f"  Sample: {items[0]['item_name']} ({items[0]['quantity_remaining']} units)")
    
    # Test 4: Check stock for specific item
    print("\nTest 4: Stock Check")
    test_item = products[0]['item_name']
    available = inventory.get_available_quantity(test_item)
    print(f"  Item: {test_item}")
    print(f"  Available: {available} units")
    
    # Test 5: Get unit price (FIFO)
    print("\nTest 5: Get Unit Price (FIFO)")
    price = inventory.get_unit_price(test_item)
    print(f"  Item: {test_item}")
    print(f"  Unit Price (oldest batch): {price:.2f} SAR")
    
    # Test 6: Deduct stock (FIFO)
    print("\nTest 6: Deduct Stock (FIFO)")
    qty_to_deduct = 10
    print(f"  Deducting {qty_to_deduct} units of {test_item}")
    deductions = inventory.deduct_stock(test_item, qty_to_deduct)
    print(f"  Deductions made from {len(deductions)} batch(es)")
    for customs_decl, qty, price in deductions:
        print(f"    - {qty} units @ {price:.2f} SAR from batch {customs_decl}")
    
    # Verify stock was deducted
    new_available = inventory.get_available_quantity(test_item)
    print(f"  Remaining stock: {new_available} units (was {available})")
    
    # Test 7: Try to deduct more than available (should raise error)
    print("\nTest 7: Insufficient Stock Error")
    try:
        inventory.deduct_stock(test_item, 999999)
        print("  ERROR: Should have raised exception!")
    except ValueError as e:
        print(f"  ✓ Correctly raised error: {e}")
    
    print("\n" + "=" * 60)
    print("INVENTORY TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_inventory()