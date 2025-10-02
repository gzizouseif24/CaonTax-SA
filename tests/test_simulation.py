from datetime import date, timedelta
from excel_reader import read_products, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator

def test_simulation():
    print("=" * 60)
    print("TESTING SALES SIMULATION ENGINE")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    products = read_products("input/products.xlsx")
    holidays = read_holidays("input/holidays.xlsx")
    
    # Initialize
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    
    # Test 1: Check working days
    print("\nTest 1: Working Day Check")
    test_dates = [
        date(2024, 1, 5),   # Friday
        date(2024, 1, 6),   # Saturday (working)
        date(2024, 1, 1),   # New Year (holiday)
    ]
    for d in test_dates:
        is_working = simulator.is_working_day(d)
        print(f"  {d} ({d.strftime('%A')}): {'Working' if is_working else 'Holiday/Friday'}")
    
    # Test 2: Boost factors
    print("\nTest 2: Boost Factor Calculation")
    test_dates = [
        date(2024, 3, 15),  # Regular day
        date(2024, 3, 27),  # Salary day (27th)
        date(2024, 3, 1),   # Salary day (1st)
        date(2024, 3, 10),  # Salary day (10th)
    ]
    for d in test_dates:
        boost = simulator.calculate_boost_factor(d)
        print(f"  {d}: {boost}x boost")
    
    # Test 3: Generate invoices for one day
    print("\nTest 3: Generate Invoices for Single Day")
    test_date = date(2024, 6, 15)  # Use a date when stock should be available
    
    # Debug: Check available items by classification
    print(f"  Debug: Checking inventory for {test_date}")
    from config import OUTSIDE_INSPECTION, UNDER_NON_SELECTIVE, UNDER_SELECTIVE
    
    # First, let's see what classifications actually exist in the data
    all_items = inventory.get_all_available_items()
    classifications = set(item['classification'] for item in all_items)
    print(f"    Actual classifications in data: {classifications}")
    print(f"    Expected classifications:")
    print(f"      OUTSIDE_INSPECTION: '{OUTSIDE_INSPECTION}'")
    print(f"      UNDER_NON_SELECTIVE: '{UNDER_NON_SELECTIVE}'")
    print(f"      UNDER_SELECTIVE: '{UNDER_SELECTIVE}'")
    
    outside_items = inventory.get_available_items_by_classification(OUTSIDE_INSPECTION)
    non_selective_items = inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE)
    selective_items = inventory.get_available_items_by_classification(UNDER_SELECTIVE)
    
    print(f"    OUTSIDE_INSPECTION: {len(outside_items)} items")
    print(f"    UNDER_NON_SELECTIVE: {len(non_selective_items)} items")
    print(f"    UNDER_SELECTIVE: {len(selective_items)} items")
    
    # Check stock dates for any available items
    if all_items:
        sample_item = all_items[0]
        print(f"    Sample stock date: {sample_item['stock_date']} (test date: {test_date})")
        available_by_date = [item for item in all_items if item['stock_date'] <= test_date]
        print(f"    Items available by {test_date}: {len(available_by_date)}")
        
        # Show a few sample items
        print(f"    Sample items:")
        for i, item in enumerate(all_items[:3]):
            print(f"      {i+1}. {item['item_name']} - {item['classification']} - Stock: {item['stock_date']}")
    
    invoices = simulator.generate_daily_invoices(test_date)
    print(f"  Generated {len(invoices)} invoices for {test_date}")
    
    if invoices:
        sample = invoices[0]
        print(f"\n  Sample Invoice:")
        print(f"    Number: {sample['invoice_number']}")
        print(f"    Type: {sample['invoice_type']}")
        print(f"    Date: {sample['invoice_date']}")
        print(f"    Customer: {sample['customer_name']}")
        print(f"    Items: {len(sample['line_items'])}")
        print(f"    Subtotal: {sample['subtotal']:.2f} SAR")
        print(f"    VAT: {sample['vat_amount']:.2f} SAR")
        print(f"    Total: {sample['total']:.2f} SAR")
        
        print(f"\n  Line Items:")
        for item in sample['line_items'][:3]:  # Show first 3 items
            print(f"    - {item['item_name']}: {item['quantity']} x {item['unit_price']:.2f} = {item['line_total']:.2f} SAR")
    
    # Test 4: Generate for a week
    print("\nTest 4: Generate Invoices for One Week")
    start_date = date(2024, 6, 15)
    total_invoices = 0
    total_sales = 0
    
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_invoices = simulator.generate_daily_invoices(current_date)
        daily_total = sum(inv['total'] for inv in daily_invoices)
        total_invoices += len(daily_invoices)
        total_sales += daily_total
        
        print(f"  {current_date} ({current_date.strftime('%A')}): {len(daily_invoices)} invoices, {daily_total:.2f} SAR")
    
    print(f"\n  Week Summary:")
    print(f"    Total Invoices: {total_invoices}")
    print(f"    Total Sales: {total_sales:.2f} SAR")
    
    # Test 5: Check inventory depletion
    print("\nTest 5: Inventory Status After Simulation")
    summary = inventory.get_inventory_summary()
    print(f"  Batches with stock: {summary['batches_with_stock']}/{summary['total_batches']}")
    print(f"  Total quantity remaining: {summary['total_quantity_remaining']}")
    
    # Test 6: Invoice counters
    print("\nTest 6: Invoice Counters")
    counters = simulator.get_invoice_summary()
    print(f"  Simplified: {counters['simplified_invoices']}")
    print(f"  Tax: {counters['tax_invoices']}")
    print(f"  Total: {counters['total_invoices']}")
    
    print("\n" + "=" * 60)
    print("SIMULATION TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_simulation()