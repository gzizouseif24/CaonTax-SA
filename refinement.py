"""
Iterative Refinement Module
Post-processing optimization to match targets precisely while preserving realistic patterns.

Strategy: Make minimal adjustments to invoice quantities to hit exact target.
"""

from decimal import Decimal
from typing import List, Dict
from config import VAT_RATE


def refine_invoices_to_target(
    invoices: List[Dict],
    target_total_inc_vat: Decimal,
    tolerance: Decimal = Decimal("5.00"),
    max_iterations: int = 50
) -> List[Dict]:
    """
    Iteratively refine invoices to match target by adjusting quantities.
    
    Strategy:
    1. Calculate current variance from target
    2. Find invoices with adjustable items (qty > 1 or can add more)
    3. Increase/decrease quantities by 1 unit at a time
    4. Recalculate totals
    5. Repeat until variance < tolerance
    
    This preserves the realistic date/product distribution while fine-tuning totals.
    
    Args:
        invoices: List of generated invoices
        target_total_inc_vat: Target total (inc VAT)
        tolerance: Acceptable variance (default: 5 SAR)
        max_iterations: Maximum adjustment iterations
        
    Returns:
        Refined list of invoices
    """
    
    print(f"\n🔄 Iterative Refinement:")
    
    # Calculate initial state
    initial_total = sum(inv['total'] for inv in invoices)
    initial_variance = target_total_inc_vat - initial_total
    
    print(f"   Initial total: {initial_total:,.2f} SAR")
    print(f"   Target: {target_total_inc_vat:,.2f} SAR")
    print(f"   Initial variance: {initial_variance:,.2f} SAR ({initial_variance/target_total_inc_vat*100:.3f}%)")
    
    if abs(initial_variance) <= tolerance:
        print(f"   ✅ Already within tolerance!")
        return invoices
    
    # Iterative refinement
    for iteration in range(max_iterations):
        current_total = sum(inv['total'] for inv in invoices)
        variance = target_total_inc_vat - current_total
        
        if abs(variance) <= tolerance:
            print(f"   ✅ Converged after {iteration} iterations")
            break
        
        # Decide: increase or decrease?
        if variance > 0:
            # Need MORE sales - increase quantity
            success = _increase_invoice_quantity(invoices, variance)
            if not success:
                print(f"   ⚠️  Cannot increase further (no adjustable invoices)")
                break
        else:
            # Need LESS sales - decrease quantity
            success = _decrease_invoice_quantity(invoices, abs(variance))
            if not success:
                print(f"   ⚠️  Cannot decrease further (no adjustable invoices)")
                break
    
    # Final result
    final_total = sum(inv['total'] for inv in invoices)
    final_variance = target_total_inc_vat - final_total
    improvement = abs(initial_variance) - abs(final_variance)
    
    print(f"   Final total: {final_total:,.2f} SAR")
    print(f"   Final variance: {final_variance:,.2f} SAR ({final_variance/target_total_inc_vat*100:.3f}%)")
    print(f"   Improvement: {improvement:,.2f} SAR")
    
    return invoices


def _increase_invoice_quantity(invoices: List[Dict], variance: Decimal) -> bool:
    """
    Increase quantity in one invoice to add sales.
    
    Strategy: Pick invoice with largest line items (easier to add 1 unit)
    """
    
    # Find invoices with items we can increase
    candidates = []
    for inv in invoices:
        for line_idx, line in enumerate(inv['line_items']):
            # Can we add 1 more unit?
            # (In production, check inventory availability)
            candidates.append((inv, line_idx, line))
    
    if not candidates:
        return False
    
    # Pick the line item with price closest to variance (for efficiency)
    # But not exceeding variance by too much
    best_candidate = None
    best_diff = float('inf')
    
    for inv, line_idx, line in candidates:
        unit_price_inc_vat = line['unit_price_ex_vat'] * (1 + VAT_RATE)
        diff = abs(float(variance) - float(unit_price_inc_vat))
        
        # Prefer items that get us closer to target
        if diff < best_diff and unit_price_inc_vat <= variance * Decimal("1.5"):
            best_diff = diff
            best_candidate = (inv, line_idx, line)
    
    if not best_candidate:
        # Fallback: just pick smallest item
        best_candidate = min(candidates, key=lambda x: x[2]['unit_price_ex_vat'])
    
    # Increase quantity by 1
    inv, line_idx, line = best_candidate
    line['quantity'] += 1
    
    # Recalculate line totals
    line['line_subtotal'] = (line['unit_price_ex_vat'] * line['quantity']).quantize(Decimal('0.01'))
    line['vat_amount'] = (line['line_subtotal'] * VAT_RATE).quantize(Decimal('0.01'))
    line['line_total'] = (line['line_subtotal'] + line['vat_amount']).quantize(Decimal('0.01'))
    
    # Recalculate invoice totals
    inv['subtotal'] = sum(item['line_subtotal'] for item in inv['line_items'])
    inv['vat_amount'] = sum(item['vat_amount'] for item in inv['line_items'])
    inv['total'] = (inv['subtotal'] + inv['vat_amount']).quantize(Decimal('0.01'))
    
    return True


def _decrease_invoice_quantity(invoices: List[Dict], variance: Decimal) -> bool:
    """
    Decrease quantity in one invoice to reduce sales.
    
    Strategy: Pick invoice with items that have qty > 1
    """
    
    # Find invoices with items we can decrease (qty > 1)
    candidates = []
    for inv in invoices:
        for line_idx, line in enumerate(inv['line_items']):
            if line['quantity'] > 1:
                candidates.append((inv, line_idx, line))
    
    if not candidates:
        return False
    
    # Pick the line item with price closest to variance
    best_candidate = None
    best_diff = float('inf')
    
    for inv, line_idx, line in candidates:
        unit_price_inc_vat = line['unit_price_ex_vat'] * (1 + VAT_RATE)
        diff = abs(float(variance) - float(unit_price_inc_vat))
        
        if diff < best_diff and unit_price_inc_vat <= variance * Decimal("1.5"):
            best_diff = diff
            best_candidate = (inv, line_idx, line)
    
    if not best_candidate:
        # Fallback: pick smallest item
        best_candidate = min(candidates, key=lambda x: x[2]['unit_price_ex_vat'])
    
    # Decrease quantity by 1
    inv, line_idx, line = best_candidate
    line['quantity'] -= 1
    
    # If quantity becomes 0, remove the line item
    if line['quantity'] == 0:
        inv['line_items'].pop(line_idx)
    else:
        # Recalculate line totals
        line['line_subtotal'] = (line['unit_price_ex_vat'] * line['quantity']).quantize(Decimal('0.01'))
        line['vat_amount'] = (line['line_subtotal'] * VAT_RATE).quantize(Decimal('0.01'))
        line['line_total'] = (line['line_subtotal'] + line['vat_amount']).quantize(Decimal('0.01'))
    
    # Recalculate invoice totals
    inv['subtotal'] = sum(item['line_subtotal'] for item in inv['line_items'])
    inv['vat_amount'] = sum(item['vat_amount'] for item in inv['line_items'])
    inv['total'] = (inv['subtotal'] + inv['vat_amount']).quantize(Decimal('0.01'))
    
    return True


def refine_with_smart_adjustments(
    invoices: List[Dict],
    target_total_inc_vat: Decimal,
    tolerance: Decimal = Decimal("5.00")
) -> List[Dict]:
    """
    Smart refinement that preserves realistic patterns.
    
    Prioritizes adjustments on:
    - Peak days (Thursday, salary days) for increases
    - Slow days (Monday, mid-month) for decreases
    
    This maintains the realistic distribution while fine-tuning.
    """
    
    print(f"\n🔄 Smart Iterative Refinement:")
    
    initial_total = sum(inv['total'] for inv in invoices)
    initial_variance = target_total_inc_vat - initial_total
    
    print(f"   Initial variance: {initial_variance:,.2f} SAR ({initial_variance/target_total_inc_vat*100:.3f}%)")
    
    if abs(initial_variance) <= tolerance:
        print(f"   ✅ Already within tolerance!")
        return invoices
    
    # Classify invoices by day type
    peak_invoices = []
    slow_invoices = []
    
    for inv in invoices:
        date = inv['invoice_date'].date() if hasattr(inv['invoice_date'], 'date') else inv['invoice_date']
        weekday = date.weekday()
        day_of_month = date.day
        
        # Peak days: Thursday, Saturday, salary days (25-28)
        is_peak = (weekday == 3 or weekday == 5 or (25 <= day_of_month <= 28))
        
        if is_peak:
            peak_invoices.append(inv)
        else:
            slow_invoices.append(inv)
    
    print(f"   Peak day invoices: {len(peak_invoices)}")
    print(f"   Slow day invoices: {len(slow_invoices)}")
    
    # Refine strategically
    max_iterations = 50
    for iteration in range(max_iterations):
        current_total = sum(inv['total'] for inv in invoices)
        variance = target_total_inc_vat - current_total
        
        if abs(variance) <= tolerance:
            print(f"   ✅ Converged after {iteration} iterations")
            break
        
        if variance > 0:
            # Increase on peak days (maintains realistic pattern)
            target_invoices = peak_invoices if peak_invoices else invoices
            success = _increase_invoice_quantity(target_invoices, variance)
            if not success:
                # Fallback to any invoice
                success = _increase_invoice_quantity(invoices, variance)
            if not success:
                break
        else:
            # Decrease on slow days (maintains realistic pattern)
            target_invoices = slow_invoices if slow_invoices else invoices
            success = _decrease_invoice_quantity(target_invoices, abs(variance))
            if not success:
                # Fallback to any invoice
                success = _decrease_invoice_quantity(invoices, abs(variance))
            if not success:
                break
    
    final_total = sum(inv['total'] for inv in invoices)
    final_variance = target_total_inc_vat - final_total
    
    print(f"   Final variance: {final_variance:,.2f} SAR ({final_variance/target_total_inc_vat*100:.3f}%)")
    
    return invoices
