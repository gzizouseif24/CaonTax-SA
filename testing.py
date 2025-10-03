"""
Comprehensive Debug Script for All Quarters (2023-2024)
Tests the entire invoice generation system and identifies all issues.
FIXED: Now uses actual FIFO costs and handles JSON serialization properly.
"""

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from config import QUARTERLY_TARGETS
from datetime import date
from decimal import Decimal
from collections import defaultdict
import json


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date and Decimal objects."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def analyze_product_batches(products):
    """Analyze products to find items with multiple batches and different prices."""
    print("\n" + "="*80)
    print("PRODUCT BATCH ANALYSIS")
    print("="*80)
    
    # Group by item name
    item_groups = defaultdict(list)
    for product in products:
        item_groups[product['item_name']].append(product)
    
    # Find items with multiple batches
    multi_batch_items = []
    for item_name, batches in item_groups.items():
        if len(batches) > 1:
            prices = [batch['unit_price_before_vat'] for batch in batches]
            costs = [batch['unit_cost'] for batch in batches]
            unique_prices = set(prices)
            
            if len(unique_prices) > 1:
                multi_batch_items.append({
                    'item_name': item_name,
                    'batch_count': len(batches),
                    'prices': [float(p) for p in prices],
                    'costs': [float(c) for c in costs],
                    'min_price': float(min(prices)),
                    'max_price': float(max(prices)),
                    'price_variance': float(max(prices) - min(prices)),
                    'stock_dates': [batch['stock_date'].strftime('%Y-%m-%d') for batch in batches]
                })
    
    print(f"\nTotal unique items: {len(item_groups)}")
    print(f"Items with multiple batches: {len([g for g in item_groups.values() if len(g) > 1])}")
    print(f"Items with DIFFERENT prices across batches: {len(multi_batch_items)}")
    
    if multi_batch_items:
        print(f"\n⚠️  CRITICAL: {len(multi_batch_items)} items have price variations across batches")
        print("\nTop 10 items with largest price variance:")
        multi_batch_items.sort(key=lambda x: x['price_variance'], reverse=True)
        
        for i, item in enumerate(multi_batch_items[:10]):
            print(f"\n{i+1}. {item['item_name']}")
            print(f"   Batches: {item['batch_count']}")
            print(f"   Price range: {item['min_price']:.2f} - {item['max_price']:.2f} SAR")
            print(f"   Variance: {item['price_variance']:.2f} SAR")
    
    return multi_batch_items


def analyze_inventory_state(inventory):
    """Analyze current inventory state."""
    print("\n" + "="*80)
    print("INVENTORY STATE ANALYSIS")
    print("="*80)
    
    summary = inventory.get_inventory_summary()
    print(f"\nTotal product batches: {summary['total_batches']}")
    print(f"Batches with stock: {summary['batches_with_stock']}")
    print(f"Depleted batches: {summary['batches_depleted']}")
    print(f"Total quantity remaining: {summary['total_quantity_remaining']}")
    
    # Classification breakdown
    classification_counts = inventory.get_items_by_classification_count()
    print(f"\nAvailable items by classification:")
    for classification, count in classification_counts.items():
        print(f"  {classification}: {count} items")
    
    return summary


def validate_quarter_profitability(invoices, quarter_name):
    """
    Validate profitability using ACTUAL FIFO costs stored in line items.
    This is now accurate because costs are captured during invoice creation.
    """
    print(f"\n{'='*80}")
    print(f"PROFITABILITY VALIDATION: {quarter_name}")
    print(f"{'='*80}")
    
    loss_sales = []
    total_items = 0
    total_revenue = Decimal("0")
    total_cost = Decimal("0")
    
    for invoice in invoices:
        for line_item in invoice['line_items']:
            total_items += 1
            
            unit_price = line_item['unit_price']
            unit_cost = line_item.get('unit_cost_actual', Decimal("0"))
            quantity = line_item['quantity']
            
            # Calculate totals using ACTUAL costs
            line_revenue = unit_price * quantity
            line_cost = unit_cost * quantity
            
            total_revenue += line_revenue
            total_cost += line_cost
            
            # Check if selling below ACTUAL cost
            if unit_price < unit_cost:
                loss_sales.append({
                    'invoice': invoice['invoice_number'],
                    'item': line_item['item_name'],
                    'quantity': quantity,
                    'selling_price': float(unit_price),
                    'actual_cost': float(unit_cost),
                    'loss_per_unit': float(unit_cost - unit_price),
                    'total_loss': float((unit_cost - unit_price) * quantity),
                    'loss_pct': float((unit_cost - unit_price) / unit_cost * 100) if unit_cost > 0 else 0
                })
    
    # Calculate overall profitability
    gross_profit = total_revenue - total_cost
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    print(f"\n📊 Financial Summary (Using ACTUAL FIFO Costs):")
    print(f"  Total line items: {total_items}")
    print(f"  Total revenue: {float(total_revenue):,.2f} SAR")
    print(f"  Total cost (actual FIFO): {float(total_cost):,.2f} SAR")
    print(f"  Gross profit: {float(gross_profit):,.2f} SAR")
    print(f"  Profit margin: {float(profit_margin):.2f}%")
    
    if len(loss_sales) == 0:
        print(f"\n✅ PERFECT! NO LOSS SALES!")
        print(f"   All {total_items} items sold profitably")
        return True, None
    else:
        print(f"\n❌ CRITICAL: FOUND {len(loss_sales)} LOSS SALES")
        
        # Calculate total losses
        total_loss_amount = sum(loss['total_loss'] for loss in loss_sales)
        print(f"   Total loss amount: {total_loss_amount:,.2f} SAR")
        
        # Show worst cases
        loss_sales.sort(key=lambda x: x['loss_pct'], reverse=True)
        print(f"\n   Top 10 worst loss sales:")
        for i, loss in enumerate(loss_sales[:10]):
            print(f"   {i+1}. {loss['item']}")
            print(f"      Sold at: {loss['selling_price']:.2f} SAR (Cost: {loss['actual_cost']:.2f})")
            print(f"      Loss: {loss['loss_per_unit']:.2f} SAR/unit × {loss['quantity']} = {loss['total_loss']:.2f} SAR")
            print(f"      Loss %: {loss['loss_pct']:.1f}%")
        
        return False, loss_sales


def test_quarter(
    aligner,
    quarter_name,
    target,
    vat_customers,
    allow_variance=False
):
    """Test a single quarter and return results."""
    
    print(f"\n{'='*80}")
    print(f"TESTING QUARTER: {quarter_name}")
    print(f"{'='*80}")
    print(f"Period: {target['start']} to {target['end']}")
    print(f"Target Sales: {float(target['sales']):,.2f} SAR")
    print(f"Target VAT: {float(target['vat']):,.2f} SAR")
    print(f"VAT Customers: {len(vat_customers)}")
    
    if allow_variance:
        print(f"⚠️  This quarter allows variance (no strict matching)")
    
    # Generate invoices
    invoices = aligner.align_quarter(
        quarter_name=quarter_name,
        start_date=target['start'],
        end_date=target['end'],
        target_sales=target['sales'],
        target_vat=target['vat'],
        vat_customers=vat_customers
    )
    
    # Calculate actuals
    actual_sales = sum(inv['subtotal'] for inv in invoices)
    actual_vat = sum(inv['vat_amount'] for inv in invoices)
    actual_total = actual_sales + actual_vat
    
    # Calculate differences
    sales_diff = actual_sales - target['sales']
    vat_diff = actual_vat - target['vat']
    sales_diff_pct = (sales_diff / target['sales'] * 100) if target['sales'] > 0 else 0
    vat_diff_pct = (vat_diff / target['vat'] * 100) if target['vat'] > 0 else 0
    
    # Count invoice types
    tax_count = len([inv for inv in invoices if inv['invoice_type'] == 'TAX'])
    simplified_count = len([inv for inv in invoices if inv['invoice_type'] == 'SIMPLIFIED'])
    
    # Validate profitability using ACTUAL costs
    is_profitable, loss_details = validate_quarter_profitability(invoices, quarter_name)
    
    # Determine if targets matched
    tolerance = Decimal("5.00")
    targets_matched = (
        abs(sales_diff) < tolerance and 
        abs(vat_diff) < tolerance
    ) or allow_variance
    
    results = {
        'quarter': quarter_name,
        'period': f"{target['start']} to {target['end']}",
        'target_sales': float(target['sales']),
        'actual_sales': float(actual_sales),
        'sales_diff': float(sales_diff),
        'sales_diff_pct': float(sales_diff_pct),
        'target_vat': float(target['vat']),
        'actual_vat': float(actual_vat),
        'vat_diff': float(vat_diff),
        'vat_diff_pct': float(vat_diff_pct),
        'target_total': float(target['sales'] + target['vat']),
        'actual_total': float(actual_total),
        'invoice_count': len(invoices),
        'tax_invoices': tax_count,
        'simplified_invoices': simplified_count,
        'vat_customers': len(vat_customers),
        'targets_matched': targets_matched,
        'is_profitable': is_profitable,
        'loss_count': len(loss_details) if loss_details else 0,
        'allow_variance': allow_variance
    }
    
    # Print summary
    print(f"\n{'='*80}")
    print(f"QUARTER SUMMARY: {quarter_name}")
    print(f"{'='*80}")
    print(f"Invoices: {len(invoices)} ({tax_count} TAX, {simplified_count} SIMPLIFIED)")
    print(f"\nSales Comparison:")
    print(f"  Target:  {results['target_sales']:>15,.2f} SAR")
    print(f"  Actual:  {results['actual_sales']:>15,.2f} SAR")
    print(f"  Diff:    {results['sales_diff']:>15,.2f} SAR ({results['sales_diff_pct']:>6.2f}%)")
    print(f"\nVAT Comparison:")
    print(f"  Target:  {results['target_vat']:>15,.2f} SAR")
    print(f"  Actual:  {results['actual_vat']:>15,.2f} SAR")
    print(f"  Diff:    {results['vat_diff']:>15,.2f} SAR ({results['vat_diff_pct']:>6.2f}%)")
    print(f"\nStatus:")
    print(f"  Targets: {'✅ MATCHED' if results['targets_matched'] else '❌ NOT MATCHED'}")
    print(f"  Profitability: {'✅ PROFITABLE' if results['is_profitable'] else '❌ LOSS SALES FOUND'}")
    
    return results, invoices


def main():
    """Run comprehensive system test."""
    
    print("="*80)
    print("COMPREHENSIVE SYSTEM DEBUG - ALL QUARTERS (2023-2024)")
    print("FIXED: Now tracks actual FIFO costs for accurate profitability")
    print("="*80)
    print("\nThis script will:")
    print("1. Analyze product batch pricing")
    print("2. Test all 6 quarters sequentially")
    print("3. Validate profitability using ACTUAL FIFO costs")
    print("4. Identify all pricing issues")
    print("5. Generate comprehensive report")
    
    # Load data
    print("\n" + "="*80)
    print("LOADING DATA")
    print("="*80)
    products = read_products('input/products.xlsx')
    customers_2024 = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Analyze product batches FIRST
    multi_batch_items = analyze_product_batches(products)
    
    # Initialize system
    print("\n" + "="*80)
    print("INITIALIZING SYSTEM")
    print("="*80)
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator)
    
    # Initial inventory state
    analyze_inventory_state(inventory)
    
    # Test all quarters
    all_results = []
    all_invoices = []
    
    for quarter_name, target in QUARTERLY_TARGETS.items():
        # Determine VAT customers
        if '2023' in quarter_name:
            vat_customers = []  # 2023 = all cash
            allow_variance = True  # 2023 can have variance
        else:
            # Filter customers for this quarter
            vat_customers = [
                c for c in customers_2024
                if target['start'] <= c['purchase_date'] <= target['end']
            ]
            allow_variance = False  # 2024 must match targets
        
        # Test quarter
        results, invoices = test_quarter(
            aligner,
            quarter_name,
            target,
            vat_customers,
            allow_variance
        )
        
        all_results.append(results)
        all_invoices.extend(invoices)
        
        # Show inventory state after this quarter
        print(f"\nInventory state after {quarter_name}:")
        summary = analyze_inventory_state(inventory)
    
    # Generate final report
    print("\n" + "="*80)
    print("FINAL COMPREHENSIVE REPORT")
    print("="*80)
    
    # Overall statistics
    total_invoices = sum(r['invoice_count'] for r in all_results)
    total_tax_invoices = sum(r['tax_invoices'] for r in all_results)
    total_simplified = sum(r['simplified_invoices'] for r in all_results)
    total_target_sales = sum(r['target_sales'] for r in all_results)
    total_actual_sales = sum(r['actual_sales'] for r in all_results)
    total_target_vat = sum(r['target_vat'] for r in all_results)
    total_actual_vat = sum(r['actual_vat'] for r in all_results)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Invoices: {total_invoices:,}")
    print(f"    - Tax Invoices: {total_tax_invoices:,} ({total_tax_invoices/total_invoices*100:.1f}%)")
    print(f"    - Simplified: {total_simplified:,} ({total_simplified/total_invoices*100:.1f}%)")
    print(f"\n  Total Sales (before VAT):")
    print(f"    Target:  {total_target_sales:,.2f} SAR")
    print(f"    Actual:  {total_actual_sales:,.2f} SAR")
    print(f"    Diff:    {total_actual_sales - total_target_sales:,.2f} SAR")
    print(f"\n  Total VAT:")
    print(f"    Target:  {total_target_vat:,.2f} SAR")
    print(f"    Actual:  {total_actual_vat:,.2f} SAR")
    print(f"    Diff:    {total_actual_vat - total_target_vat:,.2f} SAR")
    
    # Quarter-by-quarter summary
    print(f"\n📋 QUARTER-BY-QUARTER SUMMARY:")
    print(f"\n{'Quarter':<12} {'Invoices':<10} {'Target Sales':<15} {'Actual Sales':<15} {'Diff':<12} {'Profit':<8} {'Status'}")
    print("-" * 100)
    
    for r in all_results:
        profit_status = "✅" if r['is_profitable'] else "❌"
        target_status = "✅" if r['targets_matched'] else "❌"
        status = f"{profit_status} {target_status}"
        print(f"{r['quarter']:<12} {r['invoice_count']:<10} {r['target_sales']:>14,.2f} {r['actual_sales']:>14,.2f} {r['sales_diff']:>11,.2f} {profit_status:<8} {status}")
    
    # Issues summary
    quarters_with_issues = [r for r in all_results if not r['is_profitable']]
    quarters_off_target = [r for r in all_results if not r['targets_matched'] and not r['allow_variance']]
    
    print(f"\n🔍 ISSUES IDENTIFIED:")
    print(f"  Quarters with loss sales: {len(quarters_with_issues)}")
    print(f"  Quarters off target: {len(quarters_off_target)}")
    print(f"  Items with price variance: {len(multi_batch_items)}")
    
    if quarters_with_issues:
        print(f"\n  ⚠️  Quarters with profitability issues:")
        for r in quarters_with_issues:
            print(f"    - {r['quarter']}: {r['loss_count']} loss sales")
    
    if quarters_off_target:
        print(f"\n  ⚠️  Quarters off target (2024 only):")
        for r in quarters_off_target:
            print(f"    - {r['quarter']}: {r['sales_diff']:,.2f} SAR diff")
    
    # Final verdict
    print(f"\n{'='*80}")
    all_profitable = all(r['is_profitable'] for r in all_results)
    targets_ok = all(r['targets_matched'] for r in all_results)
    
    if all_profitable and targets_ok:
        print("✅✅✅ SYSTEM VALIDATION: PASSED ✅✅✅")
        print("All quarters are profitable and targets are matched!")
    elif all_profitable:
        print("⚠️  SYSTEM VALIDATION: PARTIAL PASS")
        print("All quarters are profitable, but some targets not matched exactly")
    else:
        print("❌❌❌ SYSTEM VALIDATION: FAILED ❌❌❌")
        print("Critical issues found - see details above")
    print("="*80)
    
    # Save results to JSON (with custom encoder for dates/decimals)
    try:
        with open('debug_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'overall': {
                    'total_invoices': total_invoices,
                    'total_target_sales': total_target_sales,
                    'total_actual_sales': total_actual_sales,
                    'total_target_vat': total_target_vat,
                    'total_actual_vat': total_actual_vat,
                    'all_profitable': all_profitable,
                    'targets_matched': targets_ok
                },
                'quarters': all_results,
                'multi_batch_items': multi_batch_items[:20]  # Top 20 only
            }, f, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        
        print(f"\n💾 Detailed results saved to: debug_results.json")
    except Exception as e:
        print(f"\n⚠️  Could not save JSON: {e}")


if __name__ == "__main__":
    main()