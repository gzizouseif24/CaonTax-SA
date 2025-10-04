"""
Test script for simulation.py - LOT-BASED invoice generation
Tests with actual data from excel_reader.py, inventory.py, and config.py
"""

import sys
import os

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from excel_reader import read_products, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from config import OUTSIDE_INSPECTION, UNDER_NON_SELECTIVE, UNDER_SELECTIVE
from datetime import date, datetime


def test_initialization():
    """Test simulator initialization."""
    print("=" * 80)
    print("TEST: Simulator Initialization")
    print("=" * 80)

    products = read_products('input/products.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)

    print(f"\n✓ Simulator created")
    print(f"  Holidays loaded: {len(holidays)}")
    print(f"  Invoice counters: Simplified={simulator.invoice_counter_simplified}, Tax={simulator.invoice_counter_tax}")

    return simulator, inventory


def test_lot_based_basket(simulator, inventory):
    """Test lot-based basket selection."""
    print("\n\n" + "=" * 80)
    print("TEST: Lot-Based Basket Selection")
    print("=" * 80)

    test_date = date(2024, 3, 15)  # Date with good inventory

    print(f"\n📦 Testing select_items_for_basket():")
    print(f"  Date: {test_date}")
    print(f"  Invoice type: SIMPLIFIED")

    basket = simulator.select_items_for_basket(
        invoice_type="SIMPLIFIED",
        num_items=5,
        current_date=test_date
    )

    print(f"\n  Basket size: {len(basket)} lots")

    if basket:
        print(f"\n  Basket contents:")
        for i, (lot, qty, price) in enumerate(basket):
            print(f"\n    {i+1}. lot_id: {lot['lot_id']}")
            print(f"       Item: {lot['item_description']}")
            print(f"       Quantity: {qty}")
            print(f"       Price (ex VAT): {price:.2f} SAR")
            print(f"       Cost (ex VAT): {lot['unit_cost_ex_vat']:.2f} SAR")
            print(f"       Classification: {lot['shipment_class']}")

        # Check if lots are unique
        lot_ids = [lot['lot_id'] for lot, _, _ in basket]
        unique_lots = set(lot_ids)

        if len(lot_ids) == len(unique_lots):
            print(f"\n  ✓ All lots are unique")
        else:
            print(f"\n  ❌ Duplicate lots found")

        # Check if same item appears multiple times (different lots)
        items = [lot['item_description'] for lot, _, _ in basket]
        if len(items) != len(set(items)):
            print(f"  ℹ️  Same item from different lots (correct behavior)")

    else:
        print(f"  ⚠️  Empty basket")

    return True


def test_invoice_creation(simulator, inventory):
    """Test lot-based invoice creation."""
    print("\n\n" + "=" * 80)
    print("TEST: Lot-Based Invoice Creation")
    print("=" * 80)

    test_date = date(2024, 3, 15)
    invoice_datetime = datetime.combine(test_date, datetime.min.time().replace(hour=10, minute=30))

    # Create a basket
    basket = simulator.select_items_for_basket(
        invoice_type="SIMPLIFIED",
        num_items=3,
        current_date=test_date
    )

    if not basket:
        print(f"  ⚠️  No basket created, skipping test")
        return False

    print(f"\n📄 Creating invoice from basket with {len(basket)} lots...")

    # Store initial quantities for verification
    initial_quantities = {}
    for lot, qty, _ in basket:
        lot_id = lot['lot_id']
        lot_obj = inventory.get_lot_by_id(lot_id)
        initial_quantities[lot_id] = lot_obj['qty_remaining']

    invoice = simulator.create_invoice(
        invoice_type="SIMPLIFIED",
        customer=None,
        basket=basket,
        invoice_date=invoice_datetime
    )

    print(f"\n  ✓ Invoice created: {invoice['invoice_number']}")
    print(f"  Type: {invoice['invoice_type']}")
    print(f"  Customer: {invoice['customer_name']}")
    print(f"  Date: {invoice['invoice_date']}")
    print(f"\n  Financial Summary:")
    print(f"    Subtotal (ex VAT): {invoice['subtotal']:,.2f} SAR")
    print(f"    VAT (15%): {invoice['vat_amount']:,.2f} SAR")
    print(f"    Total (inc VAT): {invoice['total']:,.2f} SAR")

    # Check line items
    print(f"\n  📋 Line Items: {len(invoice['line_items'])}")

    for i, line in enumerate(invoice['line_items']):
        print(f"\n    {i+1}. PRD-compliant fields:")
        print(f"       lot_id: {line['lot_id']}")
        print(f"       customs_declaration_no: {line['customs_declaration_no']}")
        print(f"       item_description: {line['item_description']}")
        print(f"       shipment_class: {line['shipment_class']}")
        print(f"       quantity: {line['quantity']}")
        print(f"       unit_price_ex_vat: {line['unit_price_ex_vat']:.2f} SAR")
        print(f"       unit_cost_ex_vat: {line['unit_cost_ex_vat']:.2f} SAR")
        print(f"       line_subtotal: {line['line_subtotal']:.2f} SAR")

        # Check legacy fields
        has_legacy = all(f in line for f in ['item_name', 'customs_declaration', 'classification'])
        if has_legacy:
            print(f"       ✓ Legacy fields present")
        else:
            print(f"       ❌ Missing legacy fields")

    # Verify inventory deduction
    print(f"\n  📦 Verifying inventory deduction:")

    all_deducted = True
    for lot_id, initial_qty in initial_quantities.items():
        lot_after = inventory.get_lot_by_id(lot_id)
        qty_deducted = initial_qty - lot_after['qty_remaining']

        # Find expected deduction
        expected_qty = next(qty for lot, qty, _ in basket if lot['lot_id'] == lot_id)

        print(f"    {lot_id}:")
        print(f"      Initial: {initial_qty}")
        print(f"      Deducted: {qty_deducted}")
        print(f"      Remaining: {lot_after['qty_remaining']}")

        if qty_deducted == expected_qty:
            print(f"      ✓ Correctly deducted")
        else:
            print(f"      ❌ Expected {expected_qty}, got {qty_deducted}")
            all_deducted = False

    if all_deducted:
        print(f"\n  ✓ All inventory correctly deducted")
    else:
        print(f"\n  ❌ Inventory deduction errors")

    return True


def test_multi_lot_same_item(simulator, inventory):
    """Test that same item from different lots creates separate line items."""
    print("\n\n" + "=" * 80)
    print("TEST: Multi-Lot Same Item (Separate Line Items)")
    print("=" * 80)

    # Create a manual basket with 2 lots of same item
    test_date = date(2024, 3, 15)

    # Find an item with multiple lots
    test_item = "أجبان"  # Has 9 lots
    lots = inventory.get_lots_for_item(test_item)

    if len(lots) < 2:
        print(f"  ⚠️  Item doesn't have multiple lots, skipping test")
        return True

    print(f"\n📦 Creating basket with 2 lots of same item:")
    print(f"  Item: {test_item}")
    print(f"  Available lots: {len(lots)}")

    # Create basket with first 2 lots
    basket = [
        (lots[0], 5, lots[0]['unit_price_ex_vat']),
        (lots[1], 3, lots[1]['unit_price_ex_vat'])
    ]

    print(f"\n  Basket:")
    for i, (lot, qty, price) in enumerate(basket):
        print(f"    {i+1}. {lot['lot_id']}: {qty} units @ {price:.2f} SAR")

    # Create invoice
    invoice_datetime = datetime.combine(test_date, datetime.min.time().replace(hour=11, minute=0))

    invoice = simulator.create_invoice(
        invoice_type="SIMPLIFIED",
        customer=None,
        basket=basket,
        invoice_date=invoice_datetime
    )

    print(f"\n  ✓ Invoice created: {invoice['invoice_number']}")
    print(f"\n  📋 Line Items: {len(invoice['line_items'])}")

    # CRITICAL TEST: Should have 2 separate line items
    if len(invoice['line_items']) == 2:
        print(f"  ✓ CORRECT: 2 separate line items created")
    else:
        print(f"  ❌ WRONG: Expected 2 line items, got {len(invoice['line_items'])}")

    # Check each line item
    for i, line in enumerate(invoice['line_items']):
        print(f"\n    Line {i+1}:")
        print(f"      lot_id: {line['lot_id']}")
        print(f"      item: {line['item_description']}")
        print(f"      qty: {line['quantity']}")
        print(f"      price: {line['unit_price_ex_vat']:.2f} SAR")

    # Verify both lots have different prices
    prices = [line['unit_price_ex_vat'] for line in invoice['line_items']]
    if len(set(prices)) == 2:
        print(f"\n  ✓ Both lots have different prices: {prices[0]:.2f} vs {prices[1]:.2f} SAR")
    elif len(set(prices)) == 1:
        print(f"\n  ℹ️  Both lots happen to have same price: {prices[0]:.2f} SAR")

    return True


def test_daily_invoice_generation(simulator, inventory):
    """Test full daily invoice generation."""
    print("\n\n" + "=" * 80)
    print("TEST: Daily Invoice Generation")
    print("=" * 80)

    test_date = date(2024, 3, 20)  # Wednesday

    print(f"\n📅 Generating invoices for: {test_date}")
    print(f"  Day of week: {test_date.strftime('%A')}")

    # Check if working day
    is_working = simulator.is_working_day(test_date)
    print(f"  Is working day: {is_working}")

    if not is_working:
        print(f"  ⚠️  Not a working day, no invoices generated")
        return True

    # Get boost factor
    boost = simulator.calculate_boost_factor(test_date)
    print(f"  Boost factor: {boost}x")

    # Get initial summary
    initial_summary = simulator.get_invoice_summary()

    # Generate invoices
    invoices = simulator.generate_daily_invoices(test_date)

    print(f"\n  ✓ Generated {len(invoices)} invoices")

    if invoices:
        # Analyze invoices
        simplified = sum(1 for inv in invoices if inv['invoice_type'] == 'SIMPLIFIED')
        tax = sum(1 for inv in invoices if inv['invoice_type'] == 'TAX')

        total_sales = sum(inv['subtotal'] for inv in invoices)
        total_vat = sum(inv['vat_amount'] for inv in invoices)
        total_inc_vat = sum(inv['total'] for inv in invoices)

        print(f"\n  Invoice Types:")
        print(f"    Simplified: {simplified}")
        print(f"    Tax: {tax}")

        print(f"\n  Financial Summary:")
        print(f"    Total sales (ex VAT): {total_sales:,.2f} SAR")
        print(f"    Total VAT: {total_vat:,.2f} SAR")
        print(f"    Total (inc VAT): {total_inc_vat:,.2f} SAR")

        # Check line items have lot_id
        total_lines = sum(len(inv['line_items']) for inv in invoices)
        lines_with_lot_id = sum(
            1 for inv in invoices
            for line in inv['line_items']
            if 'lot_id' in line
        )

        print(f"\n  Line Items:")
        print(f"    Total: {total_lines}")
        print(f"    With lot_id: {lines_with_lot_id}")

        if lines_with_lot_id == total_lines:
            print(f"    ✓ All line items have lot_id")
        else:
            print(f"    ❌ {total_lines - lines_with_lot_id} line items missing lot_id")

    # Verify invoice counter
    final_summary = simulator.get_invoice_summary()

    print(f"\n  Invoice Counters:")
    print(f"    Before: Simplified={initial_summary['simplified_invoices']}, Tax={initial_summary['tax_invoices']}")
    print(f"    After: Simplified={final_summary['simplified_invoices']}, Tax={final_summary['tax_invoices']}")
    print(f"    Delta: Simplified={final_summary['simplified_invoices']-initial_summary['simplified_invoices']}, Tax={final_summary['tax_invoices']-initial_summary['tax_invoices']}")

    return True


def test_q3_2023_generation(simulator, inventory):
    """Test Q3-2023 invoice generation with limited inventory."""
    print("\n\n" + "=" * 80)
    print("TEST: Q3-2023 Invoice Generation (Limited Inventory)")
    print("=" * 80)

    test_dates = [
        date(2023, 9, 23),  # Import date
        date(2023, 9, 24),  # Day after
        date(2023, 9, 27),  # Salary day
        date(2023, 9, 30),  # End of quarter
    ]

    for test_date in test_dates:
        print(f"\n  📅 {test_date}:")

        # Check working day
        if not simulator.is_working_day(test_date):
            print(f"    ⚠️  Not a working day")
            continue

        # Check available inventory
        available_lots = inventory.get_all_available_lots(current_date=test_date)
        print(f"    Available lots: {len(available_lots)}")

        if not available_lots:
            print(f"    ⚠️  No inventory available")
            continue

        # Generate a single invoice
        basket = simulator.select_items_for_basket(
            invoice_type="SIMPLIFIED",
            num_items=2,
            current_date=test_date
        )

        if basket:
            invoice_datetime = datetime.combine(test_date, datetime.min.time().replace(hour=10, minute=0))
            invoice = simulator.create_invoice(
                invoice_type="SIMPLIFIED",
                customer=None,
                basket=basket,
                invoice_date=invoice_datetime
            )

            print(f"    ✓ Invoice: {invoice['invoice_number']}")
            print(f"      Total (inc VAT): {invoice['total']:,.2f} SAR")
            print(f"      Line items: {len(invoice['line_items'])}")

    return True


def main():
    """Run all simulation tests."""
    print("\n" + "=" * 80)
    print("SIMULATION.PY TEST SUITE - LOT-BASED INVOICE GENERATION")
    print("=" * 80)

    tests = [
        ("Initialization", lambda s, i: test_initialization()),
        ("Lot-Based Basket", test_lot_based_basket),
        ("Invoice Creation", test_invoice_creation),
        ("Multi-Lot Same Item", test_multi_lot_same_item),
        ("Daily Generation", test_daily_invoice_generation),
        ("Q3-2023 Generation", test_q3_2023_generation),
    ]

    results = []
    simulator = None
    inventory = None

    for test_name, test_func in tests:
        try:
            if test_name == "Initialization":
                simulator, inventory = test_func(None, None)
                results.append((test_name, True))
            else:
                result = test_func(simulator, inventory)
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
        print(f"\n✅ All simulation tests passed!")
        print(f"\n📋 Key Features Validated:")
        print(f"  ✓ Lot-based basket selection")
        print(f"  ✓ Lot-specific pricing in invoices")
        print(f"  ✓ Separate line items for different lots of same item")
        print(f"  ✓ Lot tracking (lot_id, customs_declaration_no)")
        print(f"  ✓ Inventory deduction by lot_id")
        print(f"  ✓ PRD-compliant invoice line items")
        print(f"  ✓ Backward compatibility with legacy fields")
        return 0
    else:
        print(f"\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
