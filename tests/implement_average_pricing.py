"""
Script to implement weighted average pricing fix.
This will modify the system to use consistent average prices instead of FIFO prices.
"""

print("="*80)
print("PRICING SYSTEM FIX - IMPLEMENTATION GUIDE")
print("="*80)

print("""
PROBLEM:
--------
Current system uses FIFO prices which vary by batch, causing 100% price mismatch
with Excel file.

Example: Item "أجبان" has prices 14.82, 20.34, 26.44, 30.04, 92.76 across batches.
FIFO returns 14.82 (oldest), but this doesn't match most Excel rows.

SOLUTION:
---------
Use WEIGHTED AVERAGE PRICE across all batches for each item.

This ensures:
1. Consistent pricing (same item always has same price)
2. Prices reflect true average from Excel
3. Still profitable (average price > average cost)
4. FIFO inventory tracking remains unchanged

IMPLEMENTATION STEPS:
--------------------

Step 1: Add get_average_price() method to InventoryManager (inventory.py)
Step 2: Modify alignment.py to use average price instead of FIFO price
Step 3: Update cost validation to use average cost
Step 4: Test with Q1-2024 to verify prices match Excel

MANUAL CHANGES REQUIRED:
------------------------

1. Open inventory.py
2. Add this method to InventoryManager class:

```python
def get_average_price(self, item_name: str) -> Decimal:
    \"\"\"
    Get weighted average price for an item across all batches.
    
    Args:
        item_name: Name of the item
        
    Returns:
        Weighted average unit_price_before_vat
    \"\"\"
    batches = [p for p in self.products if p['item_name'] == item_name]
    
    if not batches:
        raise ValueError(f"Item not found: {item_name}")
    
    # Calculate weighted average
    total_value = sum(
        p['unit_price_before_vat'] * p['quantity_imported'] 
        for p in batches
    )
    total_quantity = sum(p['quantity_imported'] for p in batches)
    
    if total_quantity == 0:
        raise ValueError(f"No quantity for item: {item_name}")
    
    avg_price = (total_value / total_quantity).quantize(Decimal('0.01'))
    return avg_price

def get_average_cost(self, item_name: str) -> Decimal:
    \"\"\"
    Get weighted average cost for an item across all batches.
    
    Args:
        item_name: Name of the item
        
    Returns:
        Weighted average unit_cost
    \"\"\"
    batches = [p for p in self.products if p['item_name'] == item_name]
    
    if not batches:
        raise ValueError(f"Item not found: {item_name}")
    
    # Calculate weighted average
    total_value = sum(
        p['unit_cost'] * p['quantity_imported'] 
        for p in batches
    )
    total_quantity = sum(p['quantity_imported'] for p in batches)
    
    if total_quantity == 0:
        raise ValueError(f"No quantity for item: {item_name}")
    
    avg_cost = (total_value / total_quantity).quantize(Decimal('0.01'))
    return avg_cost
```

3. Open alignment.py
4. Find the _create_authentic_price_line_items() method
5. Replace the FIFO price logic with average price:

FIND THIS (around line 400-420):
```python
# Deduct from inventory (FIFO)
try:
    deductions = self.simulator.inventory.deduct_stock(product['item_name'], qty)
except ValueError:
    continue

# CRITICAL: Calculate ACTUAL FIFO costs from deductions
actual_cost_total = Decimal("0")
fifo_price = deductions[0][2]  # Price from oldest batch

for customs_decl, qty_deducted, batch_price in deductions:
    # Find the batch to get its cost
    batch = next((p for p in self.simulator.inventory.products 
                 if p['customs_declaration'] == customs_decl 
                 and p['item_name'] == product['item_name']), None)
    
    if batch:
        actual_cost_total += batch['unit_cost'] * qty_deducted

unit_cost_actual = actual_cost_total / qty

# CRITICAL VALIDATION: Ensure price is profitable
if fifo_price < unit_cost_actual:
    print(f"  ⚠️ Skipping {product['item_name']} - FIFO price {fifo_price} below cost {unit_cost_actual}")
    continue
```

REPLACE WITH:
```python
# Get average price for this item (consistent across all batches)
try:
    average_price = self.simulator.inventory.get_average_price(product['item_name'])
    average_cost = self.simulator.inventory.get_average_cost(product['item_name'])
except ValueError as e:
    print(f"  ⚠️ Skipping {product['item_name']} - {e}")
    continue

# CRITICAL VALIDATION: Ensure average price is profitable
if average_price < average_cost:
    print(f"  ⚠️ Skipping {product['item_name']} - Avg price {average_price} below avg cost {average_cost}")
    continue

# Deduct from inventory (FIFO for tracking only, not pricing)
try:
    deductions = self.simulator.inventory.deduct_stock(product['item_name'], qty)
except ValueError:
    continue
```

6. Update the line item creation to use average_price and average_cost:

FIND THIS:
```python
# Calculate line totals using AUTHENTIC FIFO price
line_subtotal = (fifo_price * qty).quantize(Decimal('0.01'))
line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))

# Only add if it doesn't overshoot target too much
if line_subtotal <= remaining_target + Decimal("100.00"):
    line_items.append({
        'item_name': product['item_name'],
        'quantity': qty,
        'unit_price': fifo_price,  # FIFO selling price
        'unit_cost_actual': unit_cost_actual,  # ACTUAL FIFO cost (NEW!)
        'line_subtotal': line_subtotal,
        'vat_amount': line_vat,
        'line_total': line_subtotal + line_vat,
        'classification': product['classification']
    })
```

REPLACE WITH:
```python
# Calculate line totals using AVERAGE price (consistent)
line_subtotal = (average_price * qty).quantize(Decimal('0.01'))
line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))

# Only add if it doesn't overshoot target too much
if line_subtotal <= remaining_target + Decimal("100.00"):
    line_items.append({
        'item_name': product['item_name'],
        'quantity': qty,
        'unit_price': average_price,  # Average price (consistent)
        'unit_cost_actual': average_cost,  # Average cost
        'line_subtotal': line_subtotal,
        'vat_amount': line_vat,
        'line_total': line_subtotal + line_vat,
        'classification': product['classification']
    })
```

TESTING:
--------
After making these changes:

1. Run: python test_reports.py
2. Run: python diagnose_prices.py
3. Check that price match percentage improves significantly

EXPECTED RESULTS:
-----------------
- Price matches should go from 0% to 80-100%
- Remaining mismatches will be due to rounding differences
- All sales remain profitable (average price > average cost)
- FIFO inventory tracking still works correctly

""")

print("="*80)
print("Ready to implement? Follow the manual steps above.")
print("="*80)
