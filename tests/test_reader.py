from excel_reader import read_products, read_customers, read_holidays

def test_excel_reader():
    """Test reading all 3 Excel files"""
    
    print("=" * 60)
    print("TESTING EXCEL READER")
    print("=" * 60)
    
    # Test 1: Read Products
    print("\n" + "=" * 60)
    print("TEST 1: READING PRODUCTS")
    print("=" * 60)
    try:
        products = read_products("input/products.xlsx")
        print(f"\nProducts loaded successfully!")
        print(f"  Total products: {len(products)}")
        print(f"\n  Sample product (first item):")
        if products:
            p = products[0]
            print(f"    Name: {p['item_name']}")
            print(f"    Classification: {p['classification']}")
            print(f"    Import Date: {p['import_date']}")
            print(f"    Stock Date: {p['stock_date']}")
            print(f"    Quantity: {p['quantity_remaining']}")
            print(f"    Unit Cost: {p['unit_cost']:.2f} SAR")
            print(f"    Unit Price (before VAT): {p['unit_price_before_vat']:.2f} SAR")
            print(f"    Profit Margin: {p['profit_margin_pct']}%")
    except Exception as e:
        print(f"\nError reading products: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Read Customers
    print("\n" + "=" * 60)
    print("TEST 2: READING CUSTOMERS")
    print("=" * 60)
    try:
        customers = read_customers("input/customers.xlsx")
        print(f"\nCustomers loaded successfully!")
        print(f"  Total customers: {len(customers)}")
        print(f"\n  Sample customer (first item):")
        if customers:
            c = customers[0]
            print(f"    Name: {c['customer_name']}")
            print(f"    Tax Number: {c['tax_number']}")
            print(f"    Purchase Amount: {c['purchase_amount']:.2f} SAR")
            print(f"    Purchase Date: {c['purchase_date']}")
    except Exception as e:
        print(f"\nError reading customers: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Read Holidays
    print("\n" + "=" * 60)
    print("TEST 3: READING HOLIDAYS")
    print("=" * 60)
    try:
        holidays = read_holidays("input/holidays.xlsx")
        print(f"\nHolidays loaded successfully!")
        print(f"  Total holidays: {len(holidays)}")
        print(f"\n  Sample holidays (first 5):")
        for h in holidays[:5]:
            print(f"    {h}")
    except Exception as e:
        print(f"\nError reading holidays: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE - ALL FILES LOADED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Products: {len(products)}")
    print(f"  Customers: {len(customers)}")
    print(f"  Holidays: {len(holidays)}")
    print(f"\nReady to proceed to next step!")

if __name__ == "__main__":
    test_excel_reader()