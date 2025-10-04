# 🔄 Iterative Refinement Algorithm - Post-Processing Optimization

## 📊 Problem Analysis

### Current Issue:
- Smart algorithm: -0.30% variance
- Random algorithm: -0.24% variance
- **Smart is slightly worse** because weighted patterns constrain flexibility

### Root Cause:
We generate invoices with realistic patterns, but don't **fine-tune** afterward to hit exact target.

---

## 🎯 Solution: Iterative Refinement Loop

### Concept:
After initial generation with smart patterns, **iteratively adjust** invoice sizes to match target precisely while **preserving** the realistic distribution.

### Algorithm Flow:
```
1. Generate initial invoices (smart algorithm)
2. Calculate variance from target
3. While variance > tolerance:
   a. Identify invoices to adjust
   b. Calculate adjustment needed
   c. Modify invoice sizes (add/remove items)
   d. Recalculate variance
4. Return refined invoices
```

---

## 🔧 Implementation Strategy

### Phase 1: **Micro-Adjustments** (Preserve Patterns)

**Idea:** Make small adjustments to existing invoices without changing dates

```python
def refine_to_target(invoices, target_total, tolerance=Decimal("10.00")):
    """
    Iteratively refine invoices to match target.
    
    Strategy:
    1. Calculate current total
    2. If under target: Add items to largest invoices
    3. If over target: Remove items from smallest invoices
    4. Preserve date distribution
    """
    
    max_iterations = 10
    
    for iteration in range(max_iterations):
        current_total = sum(inv['total'] for inv in invoices)
        variance = target_total - current_total
        
        if abs(variance) <= tolerance:
            break  # Close enough!
        
        if variance > 0:  # Need more sales
            # Add items to invoices on peak days (Thursday, salary days)
            candidates = [inv for inv in invoices if is_peak_day(inv['invoice_date'])]
            if candidates:
                invoice_to_adjust = max(candidates, key=lambda x: x['total'])
                add_items_to_invoice(invoice_to_adjust, variance / 2)
        
        else:  # Need less sales
            # Remove items from invoices on slow days
            candidates = [inv for inv in invoices if not is_peak_day(inv['invoice_date'])]
            if candidates:
                invoice_to_adjust = min(candidates, key=lambda x: x['total'])
                remove_items_from_invoice(invoice_to_adjust, abs(variance) / 2)
    
    return invoices
```

---

### Phase 2: **Smart Invoice Addition/Removal**

**Idea:** Add or remove entire invoices strategically

```python
def refine_with_invoice_changes(invoices, target_total, inventory, quarter_start, quarter_end):
    """
    Add or remove invoices to match target.
    
    Strategy:
    1. If under target: Generate additional invoices on peak days
    2. If over target: Remove smallest invoices from slow days
    3. Maintain realistic patterns
    """
    
    current_total = sum(inv['total'] for inv in invoices)
    variance = target_total - current_total
    
    if variance > Decimal("100.00"):  # Need more sales
        # Generate additional invoices on peak days
        peak_dates = get_peak_dates(quarter_start, quarter_end)
        num_to_add = int(variance / Decimal("5000"))  # Estimate
        
        for _ in range(num_to_add):
            date = weighted_choice(peak_dates)
            new_invoice = generate_small_invoice(date, variance / num_to_add)
            invoices.append(new_invoice)
    
    elif variance < Decimal("-100.00"):  # Need less sales
        # Remove smallest invoices from slow days
        slow_invoices = [inv for inv in invoices if is_slow_day(inv['invoice_date'])]
        slow_invoices.sort(key=lambda x: x['total'])
        
        to_remove = []
        removed_total = Decimal("0")
        for inv in slow_invoices:
            if removed_total >= abs(variance):
                break
            to_remove.append(inv)
            removed_total += inv['total']
        
        for inv in to_remove:
            invoices.remove(inv)
    
    return invoices
```

---

### Phase 3: **Quantity Adjustments** (Finest Control)

**Idea:** Adjust quantities of line items within invoices

```python
def refine_with_quantity_adjustments(invoices, target_total, tolerance=Decimal("1.00")):
    """
    Fine-tune by adjusting quantities in line items.
    
    Strategy:
    1. Calculate variance
    2. Find invoices with adjustable items (qty > 1)
    3. Increase/decrease quantities by 1-2 units
    4. Recalculate totals
    """
    
    max_iterations = 20
    
    for iteration in range(max_iterations):
        current_total = sum(inv['total'] for inv in invoices)
        variance = target_total - current_total
        
        if abs(variance) <= tolerance:
            break
        
        # Find invoice with adjustable items
        adjustable = [
            inv for inv in invoices
            if any(item['quantity'] > 1 for item in inv['line_items'])
        ]
        
        if not adjustable:
            break
        
        # Select invoice to adjust
        if variance > 0:
            # Increase quantity in largest invoice
            invoice = max(adjustable, key=lambda x: x['total'])
            adjust_quantity(invoice, +1)
        else:
            # Decrease quantity in smallest invoice
            invoice = min(adjustable, key=lambda x: x['total'])
            adjust_quantity(invoice, -1)
        
        # Recalculate invoice totals
        recalculate_invoice_totals(invoice)
    
    return invoices
```

---

## 🎯 Complete Refinement Pipeline

### Multi-Stage Approach:

```python
def iterative_refinement_pipeline(
    invoices,
    target_total_inc_vat,
    inventory,
    quarter_start,
    quarter_end,
    tolerance=Decimal("5.00")
):
    """
    Complete refinement pipeline with multiple strategies.
    
    Stages:
    1. Coarse adjustment (add/remove invoices)
    2. Medium adjustment (modify invoice sizes)
    3. Fine adjustment (quantity tweaks)
    """
    
    print(f"\n🔄 Starting iterative refinement...")
    print(f"   Target: {target_total_inc_vat:,.2f} SAR")
    
    initial_total = sum(inv['total'] for inv in invoices)
    initial_variance = target_total_inc_vat - initial_total
    
    print(f"   Initial: {initial_total:,.2f} SAR")
    print(f"   Initial variance: {initial_variance:,.2f} SAR ({initial_variance/target_total_inc_vat*100:.2f}%)")
    
    # Stage 1: Coarse adjustment (if variance > 100 SAR)
    if abs(initial_variance) > Decimal("100.00"):
        print(f"\n   Stage 1: Coarse adjustment (add/remove invoices)...")
        invoices = refine_with_invoice_changes(
            invoices, target_total_inc_vat, inventory, quarter_start, quarter_end
        )
        
        current_total = sum(inv['total'] for inv in invoices)
        current_variance = target_total_inc_vat - current_total
        print(f"   After Stage 1: {current_total:,.2f} SAR (variance: {current_variance:,.2f})")
    
    # Stage 2: Medium adjustment (if variance > 10 SAR)
    current_total = sum(inv['total'] for inv in invoices)
    current_variance = target_total_inc_vat - current_total
    
    if abs(current_variance) > Decimal("10.00"):
        print(f"\n   Stage 2: Medium adjustment (modify invoice sizes)...")
        invoices = refine_to_target(invoices, target_total_inc_vat, tolerance=Decimal("10.00"))
        
        current_total = sum(inv['total'] for inv in invoices)
        current_variance = target_total_inc_vat - current_total
        print(f"   After Stage 2: {current_total:,.2f} SAR (variance: {current_variance:,.2f})")
    
    # Stage 3: Fine adjustment (if variance > tolerance)
    current_total = sum(inv['total'] for inv in invoices)
    current_variance = target_total_inc_vat - current_total
    
    if abs(current_variance) > tolerance:
        print(f"\n   Stage 3: Fine adjustment (quantity tweaks)...")
        invoices = refine_with_quantity_adjustments(invoices, target_total_inc_vat, tolerance)
        
        current_total = sum(inv['total'] for inv in invoices)
        current_variance = target_total_inc_vat - current_total
        print(f"   After Stage 3: {current_total:,.2f} SAR (variance: {current_variance:,.2f})")
    
    # Final result
    final_total = sum(inv['total'] for inv in invoices)
    final_variance = target_total_inc_vat - final_total
    final_variance_pct = (final_variance / target_total_inc_vat * 100)
    
    print(f"\n   ✅ Refinement complete!")
    print(f"   Final: {final_total:,.2f} SAR")
    print(f"   Final variance: {final_variance:,.2f} SAR ({final_variance_pct:.3f}%)")
    print(f"   Improvement: {abs(initial_variance) - abs(final_variance):,.2f} SAR")
    
    return invoices
```

---

## 📊 Expected Results

### Before Refinement:
- Smart algorithm: -0.30% variance
- Realistic patterns: ✅
- Target matching: ⚠️

### After Refinement:
- Smart algorithm: **< 0.05% variance** ✅
- Realistic patterns: ✅ (preserved)
- Target matching: ✅ (improved)

---

## 🎯 Key Principles

### 1. **Preserve Patterns**
- Don't destroy Thursday peaks
- Don't destroy salary day spikes
- Maintain realistic distribution

### 2. **Minimal Changes**
- Make smallest adjustments possible
- Prefer quantity tweaks over invoice removal
- Prefer adding to peak days over slow days

### 3. **Iterative Approach**
- Multiple small adjustments
- Check variance after each change
- Stop when close enough

### 4. **Fallback Strategy**
- If can't refine further, accept result
- Better to have realistic patterns with small variance
- Than perfect match with unrealistic patterns

---

## 🔧 Implementation Priority

### Priority 1: **Quantity Adjustments** (Easiest)
- Adjust quantities in existing invoices
- Minimal impact on patterns
- Quick to implement

### Priority 2: **Invoice Size Modification** (Medium)
- Add/remove items from invoices
- Moderate impact on patterns
- Requires inventory checks

### Priority 3: **Invoice Addition/Removal** (Complex)
- Add new invoices or remove existing
- Larger impact on patterns
- Requires full invoice generation

---

## 💡 Recommendation

**Implement Priority 1 first** (Quantity Adjustments):
- Simplest approach
- Minimal code changes
- Biggest impact on variance
- Preserves patterns

**Expected outcome:**
- Variance: -0.30% → **-0.05%** (6× better)
- Patterns: Preserved ✅
- Time: +2-3 seconds per quarter

---

**Next Step:** Implement quantity adjustment refinement in `alignment.py`

