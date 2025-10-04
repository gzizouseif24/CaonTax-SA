"""
Generate all quarterly reports with SMART ALGORITHM + ITERATIVE REFINEMENT.
This will show the magic across all 6 quarters!
"""

import sys
import os
from decimal import Decimal

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from report_generator import ReportGenerator
from config import QUARTERLY_TARGETS


def main():
    """Generate all quarters with smart algorithm + refinement."""
    
    print("\n" + "="*80)
    print("🚀 GENERATING ALL QUARTERS WITH SMART ALGORITHM + REFINEMENT")
    print("="*80)
    print("\nExpected: Near-perfect variance across all quarters!")
    print("Let's see the magic... ✨\n")
    
    # Load data
    print("📂 Loading input data...")
    products = read_products('input/products.xlsx')
    customers = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    print(f"   ✓ Products: {len(products)} lots")
    print(f"   ✓ Customers: {len(customers)} B2B customers")
    print(f"   ✓ Holidays: {len(holidays)} holidays")
    
    # Initialize system with SMART ALGORITHM
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator, use_smart_algorithm=True)  # SMART ENABLED!
    generator = ReportGenerator(output_dir='output/reports')
    
    # Track results
    all_results = []
    
    # Process each quarter
    quarters = ["Q3-2023", "Q4-2023", "Q1-2024", "Q2-2024", "Q3-2024", "Q4-2024"]
    
    for quarter_name in quarters:
        print(f"\n{'='*80}")
        print(f"📊 PROCESSING {quarter_name}")
        print(f"{'='*80}")
        
        config = QUARTERLY_TARGETS[quarter_name]
        
        # Filter B2B customers for this quarter
        quarter_customers = [
            c for c in customers
            if config['period_start'] <= c['purchase_date'] <= config['period_end']
        ]
        
        print(f"\n  Period: {config['period_start']} to {config['period_end']}")
        print(f"  Target (inc VAT): {config['sales_inc_vat']:,.2f} SAR")
        print(f"  B2B customers: {len(quarter_customers)}")
        print(f"  Mode: {'Best Effort' if config['allow_variance'] else 'Strict'}")
        
        # Generate invoices with SMART ALGORITHM + REFINEMENT
        try:
            invoices = aligner.align_quarter(
                quarter_name=quarter_name,
                start_date=config['period_start'],
                end_date=config['period_end'],
                target_total_inc_vat=config['sales_inc_vat'],
                vat_customers=quarter_customers,
                allow_variance=config['allow_variance']
            )
            
            print(f"\n  ✓ Generated {len(invoices)} invoices")
            
            # Calculate actuals
            actual_sales_ex_vat = sum(inv['subtotal'] for inv in invoices)
            actual_vat = sum(inv['vat_amount'] for inv in invoices)
            actual_total_inc_vat = sum(inv['total'] for inv in invoices)
            
            # Calculate targets (ex-VAT)
            target_sales_ex_vat = config['sales_inc_vat'] / Decimal('1.15')
            target_vat = config['sales_inc_vat'] - target_sales_ex_vat
            
            # Variance
            variance = actual_total_inc_vat - config['sales_inc_vat']
            variance_pct = (variance / config['sales_inc_vat']) * 100
            
            # Count invoice types
            b2b_count = sum(1 for inv in invoices if inv['invoice_type'] == 'TAX')
            b2c_count = sum(1 for inv in invoices if inv['invoice_type'] == 'SIMPLIFIED')
            
            # Count line items
            total_line_items = sum(len(inv['line_items']) for inv in invoices)
            
            print(f"\n  💰 Financial Summary:")
            print(f"     Target (inc VAT): {config['sales_inc_vat']:,.2f} SAR")
            print(f"     Actual (inc VAT): {actual_total_inc_vat:,.2f} SAR")
            print(f"     Variance: {variance:,.2f} SAR ({variance_pct:.3f}%)")
            
            # Evaluation
            if abs(variance_pct) < 0.01:
                status = "✅ PERFECT"
            elif abs(variance_pct) < 0.05:
                status = "✅ EXCELLENT"
            elif abs(variance_pct) < 1.0:
                status = "✅ VERY GOOD"
            else:
                status = "⚠️ ACCEPTABLE"
            
            print(f"     Status: {status}")
            
            print(f"\n  📋 Invoice Breakdown:")
            print(f"     B2B (Tax): {b2b_count}")
            print(f"     B2C (Simplified): {b2c_count}")
            print(f"     Total line items: {total_line_items}")
            
            # Generate reports
            print(f"\n  📄 Generating Excel reports...")
            reports = generator.generate_all_reports(
                quarter_name=quarter_name,
                invoices=invoices,
                target_sales=target_sales_ex_vat,
                target_vat=target_vat
            )
            
            # Store results
            result = {
                'quarter': quarter_name,
                'invoices': len(invoices),
                'b2b': b2b_count,
                'b2c': b2c_count,
                'line_items': total_line_items,
                'target_inc_vat': float(config['sales_inc_vat']),
                'actual_inc_vat': float(actual_total_inc_vat),
                'variance': float(variance),
                'variance_pct': float(variance_pct),
                'status': status,
                'reports': reports,
                'success': True
            }
            all_results.append(result)
            
        except Exception as e:
            print(f"\n  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            result = {
                'quarter': quarter_name,
                'success': False,
                'error': str(e)
            }
            all_results.append(result)
    
    # Final summary
    print(f"\n\n{'='*80}")
    print("🎉 GENERATION COMPLETE - SMART ALGORITHM RESULTS")
    print(f"{'='*80}\n")
    
    successful = [r for r in all_results if r.get('success')]
    failed = [r for r in all_results if not r.get('success')]
    
    print(f"✅ Successful: {len(successful)}/{len(quarters)}")
    print(f"❌ Failed: {len(failed)}/{len(quarters)}\n")
    
    if successful:
        print("="*80)
        print("QUARTER RESULTS (SMART + REFINEMENT)")
        print("="*80)
        
        for r in successful:
            print(f"\n{r['quarter']}:")
            print(f"  Invoices: {r['invoices']} (B2B: {r['b2b']}, B2C: {r['b2c']})")
            print(f"  Line items: {r['line_items']}")
            print(f"  Target: {r['target_inc_vat']:,.2f} SAR")
            print(f"  Actual: {r['actual_inc_vat']:,.2f} SAR")
            print(f"  Variance: {r['variance']:,.2f} SAR ({r['variance_pct']:.3f}%)")
            print(f"  Status: {r['status']}")
    
    if failed:
        print(f"\n{'='*80}")
        print("❌ FAILED QUARTERS")
        print(f"{'='*80}")
        for r in failed:
            print(f"  {r['quarter']}: {r.get('error', 'Unknown error')}")
    
    # Statistics
    print(f"\n\n{'='*80}")
    print("📊 VARIANCE STATISTICS")
    print(f"{'='*80}\n")
    
    if successful:
        variances = [abs(r['variance_pct']) for r in successful]
        avg_variance = sum(variances) / len(variances)
        max_variance = max(variances)
        min_variance = min(variances)
        
        perfect = sum(1 for v in variances if v < 0.01)
        excellent = sum(1 for v in variances if v < 0.05)
        
        print(f"Average variance: {avg_variance:.3f}%")
        print(f"Best variance: {min_variance:.3f}%")
        print(f"Worst variance: {max_variance:.3f}%")
        print(f"\nPerfect (< 0.01%): {perfect}/{len(successful)}")
        print(f"Excellent (< 0.05%): {excellent}/{len(successful)}")
    
    print(f"\n{'='*80}")
    print("✅ ALL REPORTS GENERATED WITH SMART ALGORITHM")
    print(f"{'='*80}")
    print(f"\n📁 Location: output/reports/")
    print(f"   Total files: {len(successful) * 3} Excel files (3 per quarter)")
    
    print(f"\n\n{'='*80}")
    print("🎯 NEXT STEP: VALIDATE REPORTS")
    print(f"{'='*80}")
    print("\nRun validation to verify data quality:")
    print("  python validate_reports.py")
    
    print(f"\n{'='*80}\n")
    
    return all_results


if __name__ == "__main__":
    results = main()
    
    # Exit code
    success_count = sum(1 for r in results if r.get('success'))
    sys.exit(0 if success_count == len(results) else 1)
