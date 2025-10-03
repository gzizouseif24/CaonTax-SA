"""
Regenerate Q2-2024 report with the fixed system.
This will overwrite the old report with correct prices.
"""

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from report_generator import ReportGenerator
from config import QUARTERLY_TARGETS


def main():
    print("="*80)
    print("REGENERATING Q2-2024 REPORT WITH FIXED PRICES")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    products = read_products('input/products.xlsx')
    customers_2024 = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Initialize
    print("Initializing system...")
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator)
    
    # Generate Q2-2024
    quarter_name = "Q2-2024"
    target = QUARTERLY_TARGETS[quarter_name]
    
    vat_customers = [
        c for c in customers_2024
        if target['start'] <= c['purchase_date'] <= target['end']
    ]
    
    print(f"\nGenerating {quarter_name} invoices...")
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=target['sales'],
        target_vat=target['vat'],
        vat_customers=vat_customers,
        allow_variance=False
    )
    
    # Generate reports
    print(f"\nGenerating reports...")
    report_gen = ReportGenerator(output_dir="output/reports")
    
    report_paths = report_gen.generate_all_reports(
        quarter_name=quarter_name,
        invoices=invoices,
        target_sales=target['sales'],
        target_vat=target['vat']
    )
    
    print(f"\n{'='*80}")
    print("✅ Q2-2024 REPORTS REGENERATED")
    print(f"{'='*80}")
    print("\nNow run: python diagnose_q2_prices.py")
    print("It should show 100% price match!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
