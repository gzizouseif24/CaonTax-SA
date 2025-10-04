"""
Compare Smart vs Random algorithms on Q4-2023.
This will show the difference in patterns and variance.
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
from config import QUARTERLY_TARGETS


def test_algorithm(use_smart: bool, quarter: str = "Q4-2023"):
    """Test one algorithm."""
    
    algo_name = "SMART" if use_smart else "RANDOM"
    print(f"\n{'='*80}")
    print(f"🧪 TESTING {algo_name} ALGORITHM - {quarter}")
    print(f"{'='*80}")
    
    # Load data
    products = read_products('input/products.xlsx')
    customers = read_customers('input/customers.xlsx')
    holidays = read_holidays('input/holidays.xlsx')
    
    # Initialize system
    inventory = InventoryManager(products)
    simulator = SalesSimulator(inventory, holidays)
    aligner = QuarterlyAligner(simulator, use_smart_algorithm=use_smart)
    
    # Get quarter config
    config = QUARTERLY_TARGETS[quarter]
    
    # Filter customers
    quarter_customers = [
        c for c in customers
        if config['period_start'] <= c['purchase_date'] <= config['period_end']
    ]
    
    # Generate invoices
    invoices = aligner.align_quarter(
        quarter_name=quarter,
        start_date=config['period_start'],
        end_date=config['period_end'],
        target_total_inc_vat=config['sales_inc_vat'],
        vat_customers=quarter_customers,
        allow_variance=config['allow_variance']
    )
    
    # Calculate results
    actual_total_inc_vat = sum(inv['total'] for inv in invoices)
    variance = actual_total_inc_vat - config['sales_inc_vat']
    variance_pct = (variance / config['sales_inc_vat']) * 100
    
    # Analyze patterns
    from collections import Counter
    
    # Date distribution
    dates = [inv['invoice_date'].date() for inv in invoices]
    date_counts = Counter(dates)
    
    # Day of week distribution
    weekdays = [d.weekday() for d in dates]
    weekday_counts = Counter(weekdays)
    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Invoice size distribution
    sizes = [float(inv['subtotal']) for inv in invoices]
    avg_size = sum(sizes) / len(sizes) if sizes else 0
    min_size = min(sizes) if sizes else 0
    max_size = max(sizes) if sizes else 0
    
    # Product frequency
    items = []
    for inv in invoices:
        for line in inv['line_items']:
            items.append(line['item_description'])
    item_counts = Counter(items)
    top_items = item_counts.most_common(5)
    
    # Results
    print(f"\n{'='*80}")
    print(f"📊 RESULTS - {algo_name} ALGORITHM")
    print(f"{'='*80}")
    
    print(f"\n💰 Financial:")
    print(f"  Target: {config['sales_inc_vat']:,.2f} SAR")
    print(f"  Actual: {actual_total_inc_vat:,.2f} SAR")
    print(f"  Variance: {variance:,.2f} SAR ({variance_pct:.2f}%)")
    
    print(f"\n📋 Invoices:")
    print(f"  Count: {len(invoices)}")
    print(f"  Avg size: {avg_size:,.2f} SAR")
    print(f"  Min size: {min_size:,.2f} SAR")
    print(f"  Max size: {max_size:,.2f} SAR")
    
    print(f"\n📅 Day of Week Distribution:")
    for i, name in enumerate(weekday_names):
        count = weekday_counts.get(i, 0)
        pct = (count / len(invoices) * 100) if invoices else 0
        bar = '█' * int(pct / 2)
        print(f"  {name}: {bar} {count} ({pct:.1f}%)")
    
    print(f"\n📦 Top 5 Products:")
    for item, count in top_items:
        pct = (count / len(items) * 100) if items else 0
        print(f"  {item[:40]}: {count} ({pct:.1f}%)")
    
    print(f"\n📊 Date Concentration:")
    top_dates = date_counts.most_common(5)
    for date, count in top_dates:
        pct = (count / len(invoices) * 100) if invoices else 0
        print(f"  {date}: {count} invoices ({pct:.1f}%)")
    
    return {
        'algorithm': algo_name,
        'invoices': len(invoices),
        'variance': float(variance),
        'variance_pct': float(variance_pct),
        'avg_size': avg_size,
        'weekday_dist': weekday_counts,
        'top_items': top_items,
        'date_concentration': max(date_counts.values()) if date_counts else 0
    }


def main():
    """Compare both algorithms."""
    
    print("\n" + "="*80)
    print("🔬 ALGORITHM COMPARISON: SMART vs RANDOM")
    print("="*80)
    print("\nTesting Q4-2023 with both algorithms...")
    print("This will show differences in patterns and realism.")
    
    # Test both
    random_results = test_algorithm(use_smart=False, quarter="Q4-2023")
    smart_results = test_algorithm(use_smart=True, quarter="Q4-2023")
    
    # Comparison
    print(f"\n\n{'='*80}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"{'Metric':<30} {'Random':<20} {'Smart':<20} {'Winner'}")
    print(f"{'-'*80}")
    
    # Variance
    random_var = abs(random_results['variance_pct'])
    smart_var = abs(smart_results['variance_pct'])
    var_winner = "Smart ✅" if smart_var <= random_var else "Random ✅"
    print(f"{'Variance (abs %)':<30} {random_var:<20.2f} {smart_var:<20.2f} {var_winner}")
    
    # Invoice count
    print(f"{'Invoice Count':<30} {random_results['invoices']:<20} {smart_results['invoices']:<20}")
    
    # Average size
    print(f"{'Avg Invoice Size':<30} {random_results['avg_size']:<20,.2f} {smart_results['avg_size']:<20,.2f}")
    
    # Thursday concentration (should be higher for smart)
    random_thu = random_results['weekday_dist'].get(3, 0)
    smart_thu = smart_results['weekday_dist'].get(3, 0)
    random_thu_pct = (random_thu / random_results['invoices'] * 100) if random_results['invoices'] else 0
    smart_thu_pct = (smart_thu / smart_results['invoices'] * 100) if smart_results['invoices'] else 0
    thu_winner = "Smart ✅" if smart_thu_pct > random_thu_pct else "Random"
    print(f"{'Thursday % (should be high)':<30} {random_thu_pct:<20.1f} {smart_thu_pct:<20.1f} {thu_winner}")
    
    # Friday concentration (should be lower for smart)
    random_fri = random_results['weekday_dist'].get(4, 0)
    smart_fri = smart_results['weekday_dist'].get(4, 0)
    random_fri_pct = (random_fri / random_results['invoices'] * 100) if random_results['invoices'] else 0
    smart_fri_pct = (smart_fri / smart_results['invoices'] * 100) if smart_results['invoices'] else 0
    fri_winner = "Smart ✅" if smart_fri_pct < random_fri_pct else "Random"
    print(f"{'Friday % (should be low)':<30} {random_fri_pct:<20.1f} {smart_fri_pct:<20.1f} {fri_winner}")
    
    # Date concentration (smart should be more concentrated on peak days)
    date_winner = "Smart ✅" if smart_results['date_concentration'] > random_results['date_concentration'] else "Random"
    print(f"{'Max invoices/day':<30} {random_results['date_concentration']:<20} {smart_results['date_concentration']:<20} {date_winner}")
    
    print(f"\n{'='*80}")
    print("🎯 CONCLUSION")
    print(f"{'='*80}\n")
    
    if smart_var <= random_var:
        print("✅ Smart algorithm has BETTER or EQUAL variance")
    else:
        print("⚠️  Random algorithm has slightly better variance")
    
    if smart_thu_pct > random_thu_pct + 2:
        print("✅ Smart algorithm shows realistic Thursday peak")
    else:
        print("⚠️  Thursday peak not significant")
    
    if smart_fri_pct < random_fri_pct:
        print("✅ Smart algorithm shows realistic Friday dip")
    else:
        print("⚠️  Friday dip not significant")
    
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATION")
    print(f"{'='*80}\n")
    
    if smart_var <= random_var * 1.1:  # Within 10% of random
        print("✅ USE SMART ALGORITHM")
        print("   - Similar or better variance")
        print("   - More realistic patterns")
        print("   - Better explainability")
        print("   - Ready for production!")
    else:
        print("⚠️  NEEDS TUNING")
        print("   - Smart algorithm needs weight adjustment")
        print("   - Consider hybrid approach")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
