"""
Generate sample reports for Q2-2024
This demonstrates the report generation with the fixed pricing system.
"""

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from report_generator import ReportGenerator
from config import QUARTERLY_TARGETS
from decimal import Decimal


def main():
    """Generate sample reports for Q2-2024."""
    
    print("="*80)
    print("SAMPLE REPORT GENERATION - Q2-2024")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    products = read_products('input/products.xlsx')
    customers_2024 = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Initialize system
    print("Initializing system...")
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator)
    
    # Get Q2-2024 target
    quarter_name = "Q2-2024"
    target = QUARTERLY_TARGETS[quarter_name]
    
    # Filter customers for Q2-2024
    vat_customers = [
        c for c in customers_2024
        if target['start'] <= c['purchase_date'] <= target['end']
    ]
    
    print(f"\nGenerating invoices for {quarter_name}...")
    print(f"  Target Sales: {float(target['sales']):,.2f} SAR")
    print(f"  Target VAT: {float(target['vat']):,.2f} SAR")
    print(f"  VAT Customers: {len(vat_customers)}")
    
    # Generate invoices
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=target['sales'],
        target_vat=target['vat'],
        vat_customers=vat_customers,
        allow_variance=False  # 2024 strict mode
    )
    
    # Calculate actuals
    actual_sales = sum(inv['subtotal'] for inv in invoices)
    actual_vat = sum(inv['vat_amount'] for inv in invoices)
    
    print(f"\n{'='*80}")
    print("INVOICE GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total Invoices: {len(invoices)}")
    print(f"  - Tax Invoices: {len([i for i in invoices if i['invoice_type'] == 'TAX'])}")
    print(f"  - Simplified: {len([i for i in invoices if i['invoice_type'] == 'SIMPLIFIED'])}")
    print(f"Actual Sales: {float(actual_sales):,.2f} SAR")
    print(f"Actual VAT: {float(actual_vat):,.2f} SAR")
    print(f"Sales Difference: {float(actual_sales - target['sales']):.2f} SAR")
    print(f"VAT Difference: {float(actual_vat - target['vat']):.2f} SAR")
    
    # Generate reports
    print(f"\n{'='*80}")
    print("GENERATING EXCEL REPORTS")
    print(f"{'='*80}\n")
    
    report_gen = ReportGenerator(output_dir="output/reports")
    
    report_paths = report_gen.generate_all_reports(
        quarter_name=quarter_name,
        invoices=invoices,
        target_sales=target['sales'],
        target_vat=target['vat']
    )
    
    # Summary
    print(f"\n{'='*80}")
    print("✅ REPORT GENERATION COMPLETE")
    print(f"{'='*80}")
    print("\nGenerated files:")
    print(f"  1. Detailed Sales: {report_paths['detailed']}")
    print(f"  2. Invoice Summary: {report_paths['summary']}")
    print(f"  3. Quarterly Summary: {report_paths['quarterly']}")
    
    # Show sample data from detailed report
    print(f"\n{'='*80}")
    print("SAMPLE DATA FROM DETAILED REPORT (First 5 items)")
    print(f"{'='*80}")
    
    for i, invoice in enumerate(invoices[:2]):  # First 2 invoices
        print(f"\nInvoice: {invoice['invoice_number']}")
        print(f"Customer: {invoice['customer_name']}")
        print(f"Date: {invoice['invoice_date']}")
        
        for j, item in enumerate(invoice['line_items'][:3]):  # First 3 items
            print(f"  {j+1}. {item['item_name']}")
            print(f"     Price: {float(item['unit_price']):.2f} SAR")
            print(f"     Qty: {item['quantity']}")
            print(f"     Subtotal: {float(item['line_subtotal']):.2f} SAR")
    
    print(f"\n{'='*80}")
    print("You can now open the Excel files to review the complete reports.")
    print("All prices should match the original Excel file exactly!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
