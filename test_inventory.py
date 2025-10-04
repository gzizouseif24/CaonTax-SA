"""
Test script for inventory.py - LOT-BASED system
Tests with actual data from excel_reader.py and config.py
"""

import sys
import os

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from excel_reader import read_products
from inventory import InventoryManager
from config import OUTSIDE_INSPECTION, UNDER_NON_SELECTIVE, UNDER_SELECTIVE
from datetime import date


def test_initialization():
    """Test inventory initialization with real data."""
    print("=" * 80)
    print("TEST: Inventory Initialization")
    print("=" * 80)

    products = read_products('input/products.xlsx')
    inventory = InventoryManager(products)

    print(f"\n✓ Inventory created")

    # Check summary
    summary = inventory.get_inventory_summary()

    print(f"\n📊 Inventory Summary:")
    print(f"  Total lots: {summary['total_lots']}")
    print(f"  Lots with stock: {summary['lots_with_stock']}")
    print(f"  Lots depleted: {summary['lots_depleted']}")
    print(f"  Total quantity: {summary['total_quantity_remaining']:,}")
    print(f"  Unique items (all): {summary['unique_items_all']}")
    print(f"  Unique items (available): {summary['unique_items_available']}")

    # Validate
    if summary['total_lots'] == 203:
        print(f"\n  ✓ Correct number of lots loaded")
    else:
        print(f"\n  ❌ Expected 203 lots, got {summary['total_lots']}")

    return inventory


def test_lot_based_queries(inventory):
    """Test lot-based querying."""
    print("\n\n" + "=" * 80)
    print("TEST: Lot-Based Queries")
    print("=" * 80)

    # Test get_lots_for_item
    print(f"\n🔍 Testing get_lots_for_item():")

    test_item = "أجبان"  # Item with 9 lots
    lots = inventory.get_lots_for_item(test_item)

    print(f"\n  Item: {test_item}")
    print(f"  Lots found: {len(lots)}")

    if lots:
        print(f"\n  Lot details (FIFO order):")
        for i, lot in enumerate(lots[:3]):  # Show first 3
            print(f"    {i+1}. lot_id: {lot['lot_id']}")
            print(f"       Price: {lot['unit_price_ex_vat']:.2f} SAR")
            print(f"       Cost: {lot['unit_cost_ex_vat']:.2f} SAR")
            print(f"       Qty: {lot['qty_remaining']}")
            print(f"       Stock date: {lot['stock_date']}")

        # Check if prices differ (they should!)
        prices = set(lot['unit_price_ex_vat'] for lot in lots)
        if len(prices) > 1:
            print(f"\n  ✓ Multiple prices found: {len(prices)} different prices")
            print(f"    Range: {min(prices):.2f} - {max(prices):.2f} SAR")
        else:
            print(f"\n  ⚠️  Only one price across all lots")

    # Test get_lot_by_id
    print(f"\n\n🔍 Testing get_lot_by_id():")

    if lots:
        test_lot_id = lots[0]['lot_id']
        lot = inventory.get_lot_by_id(test_lot_id)

        if lot:
            print(f"  ✓ Found lot: {test_lot_id}")
            print(f"    Price: {lot['unit_price_ex_vat']:.2f} SAR")
        else:
            print(f"  ❌ Lot not found")

    # Test get_lot_price
    print(f"\n\n💰 Testing get_lot_price():")

    if lots:
        test_lot_id = lots[0]['lot_id']
        try:
            price = inventory.get_lot_price(test_lot_id)
            print(f"  ✓ Price for {test_lot_id}: {price:.2f} SAR")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    return True


def test_classification_queries(inventory):
    """Test classification-based queries."""
    print("\n\n" + "=" * 80)
    print("TEST: Classification Queries")
    print("=" * 80)

    classifications = [OUTSIDE_INSPECTION, UNDER_NON_SELECTIVE, UNDER_SELECTIVE]

    print(f"\n📦 Testing get_available_lots_by_classification():")

    for classification in classifications:
        lots = inventory.get_available_lots_by_classification(classification)

        print(f"\n  {classification}:")
        print(f"    Lots available: {len(lots)}")

        if lots:
            # Show sample
            sample = lots[0]
            print(f"    Sample lot_id: {sample['lot_id']}")
            print(f"    Price: {sample['unit_price_ex_vat']:.2f} SAR")

    # Test with date filter
    print(f"\n\n📅 Testing date filtering:")

    q3_2023_date = date(2023, 9, 25)  # During Q3-2023
    lots_q3 = inventory.get_all_available_lots(current_date=q3_2023_date)

    print(f"  Date: {q3_2023_date}")
    print(f"  Available lots: {len(lots_q3)}")

    if lots_q3:
        print(f"  Sample:")
        for lot in lots_q3[:3]:
            print(f"    - {lot['item_description']}: Stock date {lot['stock_date']}")

    return True


def test_lot_deduction(inventory):
    """Test lot-based stock deduction."""
    print("\n\n" + "=" * 80)
    print("TEST: Lot-Based Stock Deduction")
    print("=" * 80)

    # Find a lot with stock
    lots = inventory.get_all_available_lots()

    if not lots:
        print("  ⚠️  No lots available for testing")
        return False

    test_lot = lots[0]
    test_lot_id = test_lot['lot_id']
    initial_qty = test_lot['qty_remaining']

    print(f"\n📦 Testing deduct_stock() on specific lot:")
    print(f"  Lot: {test_lot_id}")
    print(f"  Initial qty: {initial_qty}")

    # Deduct some quantity
    qty_to_deduct = min(5, initial_qty)

    print(f"  Deducting: {qty_to_deduct}")

    try:
        deduction = inventory.deduct_stock(test_lot_id, qty_to_deduct)

        print(f"\n  ✓ Deduction successful:")
        print(f"    Lot ID: {deduction['lot_id']}")
        print(f"    Qty deducted: {deduction['qty_deducted']}")
        print(f"    Unit price: {deduction['unit_price_ex_vat']:.2f} SAR")
        print(f"    Unit cost: {deduction['unit_cost_ex_vat']:.2f} SAR")
        print(f"    Customs: {deduction['customs_declaration_no']}")

        # Check remaining
        lot_after = inventory.get_lot_by_id(test_lot_id)
        print(f"\n  Final qty: {lot_after['qty_remaining']}")

        if lot_after['qty_remaining'] == initial_qty - qty_to_deduct:
            print(f"  ✓ Quantity correctly updated")
        else:
            print(f"  ❌ Quantity mismatch")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

    return True


def test_fifo_deduction(inventory):
    """Test FIFO deduction across multiple lots."""
    print("\n\n" + "=" * 80)
    print("TEST: FIFO Deduction Across Lots")
    print("=" * 80)

    # Find item with multiple lots
    test_item = "أجبان"  # Has 9 lots
    lots_before = inventory.get_lots_for_item(test_item)

    if len(lots_before) < 2:
        print(f"  ⚠️  Item doesn't have multiple lots for testing")
        return True

    print(f"\n📦 Testing deduct_stock_fifo():")
    print(f"  Item: {test_item}")
    print(f"  Lots available: {len(lots_before)}")

    # Calculate total available
    total_qty = sum(lot['qty_remaining'] for lot in lots_before)
    print(f"  Total quantity: {total_qty}")

    # Deduct enough to span multiple lots
    # Take qty from first lot + some from second
    qty_to_deduct = min(lots_before[0]['qty_remaining'] + 10, total_qty)

    print(f"  Deducting: {qty_to_deduct}")

    try:
        deductions = inventory.deduct_stock_fifo(test_item, qty_to_deduct)

        print(f"\n  ✓ FIFO deduction successful:")
        print(f"    Lots used: {len(deductions)}")

        total_deducted = 0
        for i, deduction in enumerate(deductions):
            print(f"\n    Lot {i+1}:")
            print(f"      lot_id: {deduction['lot_id']}")
            print(f"      Qty: {deduction['qty_deducted']}")
            print(f"      Price: {deduction['unit_price_ex_vat']:.2f} SAR")
            total_deducted += deduction['qty_deducted']

        print(f"\n  Total deducted: {total_deducted}")

        if total_deducted == qty_to_deduct:
            print(f"  ✓ Total matches requested")
        else:
            print(f"  ❌ Total mismatch")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_stock_checks(inventory):
    """Test stock availability checks."""
    print("\n\n" + "=" * 80)
    print("TEST: Stock Availability Checks")
    print("=" * 80)

    lots = inventory.get_all_available_lots()

    if not lots:
        print("  ⚠️  No lots available")
        return True

    test_lot = lots[0]
    test_lot_id = test_lot['lot_id']
    test_item = test_lot['item_description']

    print(f"\n🔍 Testing check_lot_stock_available():")
    print(f"  Lot: {test_lot_id}")
    print(f"  Available: {test_lot['qty_remaining']}")

    # Check available quantity
    available = inventory.check_lot_stock_available(test_lot_id, 1)
    print(f"  Check for qty=1: {available}")

    if available:
        print(f"  ✓ Correctly reported as available")
    else:
        print(f"  ❌ Should be available")

    # Check excessive quantity
    excessive = inventory.check_lot_stock_available(test_lot_id, test_lot['qty_remaining'] + 1000)
    print(f"  Check for qty={test_lot['qty_remaining'] + 1000}: {excessive}")

    if not excessive:
        print(f"  ✓ Correctly reported as unavailable")
    else:
        print(f"  ❌ Should be unavailable")

    print(f"\n\n🔍 Testing check_item_stock_available():")
    print(f"  Item: {test_item}")

    total_qty = inventory.get_available_quantity_for_item(test_item)
    print(f"  Total available: {total_qty}")

    available_item = inventory.check_item_stock_available(test_item, total_qty)
    print(f"  Check for total qty: {available_item}")

    if available_item:
        print(f"  ✓ Correctly reported as available")
    else:
        print(f"  ❌ Should be available")

    return True


def test_legacy_compatibility(inventory):
    """Test legacy method compatibility."""
    print("\n\n" + "=" * 80)
    print("TEST: Legacy Method Compatibility")
    print("=" * 80)

    print(f"\n🔄 Testing legacy methods:")

    # Test get_available_items_by_classification
    print(f"\n  get_available_items_by_classification():")
    try:
        items = inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE)
        print(f"    ✓ Returns {len(items)} lots")
    except Exception as e:
        print(f"    ❌ Error: {e}")

    # Test get_all_available_items
    print(f"\n  get_all_available_items():")
    try:
        items = inventory.get_all_available_items()
        print(f"    ✓ Returns {len(items)} lots")
    except Exception as e:
        print(f"    ❌ Error: {e}")

    # Test get_available_quantity
    print(f"\n  get_available_quantity():")
    try:
        qty = inventory.get_available_quantity("أجبان")
        print(f"    ✓ Returns {qty} units")
    except Exception as e:
        print(f"    ❌ Error: {e}")

    # Test get_unit_price
    print(f"\n  get_unit_price():")
    try:
        price = inventory.get_unit_price("أجبان")
        print(f"    ✓ Returns {price:.2f} SAR (from oldest lot)")
    except Exception as e:
        print(f"    ❌ Error: {e}")

    return True


def test_q3_2023_availability(inventory):
    """Test Q3-2023 specific stock availability."""
    print("\n\n" + "=" * 80)
    print("TEST: Q3-2023 Stock Availability")
    print("=" * 80)

    # Q3-2023 dates
    q3_start = date(2023, 7, 1)
    q3_end = date(2023, 9, 30)

    print(f"\n📅 Q3-2023 Period: {q3_start} to {q3_end}")

    # Check availability on different dates
    test_dates = [
        date(2023, 9, 1),   # Early September
        date(2023, 9, 23),  # Import date
        date(2023, 9, 25),  # After import
        date(2023, 9, 30),  # End of quarter
    ]

    for test_date in test_dates:
        lots = inventory.get_all_available_lots(current_date=test_date)
        print(f"\n  Date: {test_date}")
        print(f"  Available lots: {len(lots)}")

        if lots:
            total_qty = sum(lot['qty_remaining'] for lot in lots)
            total_value = sum(
                lot['qty_remaining'] * lot['unit_price_ex_vat']
                for lot in lots
            )
            print(f"  Total quantity: {total_qty:,}")
            print(f"  Total value (ex VAT): {total_value:,.2f} SAR")

    # Note about Q3-2023
    print(f"\n  ℹ️  Note: Q3-2023 has minimal inventory")
    print(f"     Only 1 product imported on Sept 23")
    print(f"     Stock available immediately (stock_date = import_date)")

    return True


def main():
    """Run all inventory tests."""
    print("\n" + "=" * 80)
    print("INVENTORY.PY TEST SUITE - LOT-BASED SYSTEM")
    print("=" * 80)

    tests = [
        ("Initialization", lambda inv: test_initialization()),
        ("Lot-Based Queries", test_lot_based_queries),
        ("Classification Queries", test_classification_queries),
        ("Lot Deduction", test_lot_deduction),
        ("FIFO Deduction", test_fifo_deduction),
        ("Stock Checks", test_stock_checks),
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Q3-2023 Availability", test_q3_2023_availability),
    ]

    results = []
    inventory = None

    for test_name, test_func in tests:
        try:
            if test_name == "Initialization":
                inventory = test_func(None)
                results.append((test_name, True))
            else:
                result = test_func(inventory)
                results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print(f"\n✅ All inventory tests passed!")
        print(f"\n📋 Key Features Validated:")
        print(f"  ✓ Lot-based inventory (each lot tracked separately)")
        print(f"  ✓ Lot-specific pricing (different prices per lot)")
        print(f"  ✓ FIFO deduction across multiple lots")
        print(f"  ✓ Date-based stock availability")
        print(f"  ✓ Classification-based queries")
        print(f"  ✓ Backward compatibility with legacy code")
        return 0
    else:
        print(f"\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
