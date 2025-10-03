# Pricing System Fix - Use Consistent Excel Prices

## Problem
The system uses FIFO prices which vary by batch, causing invoice prices to not match the Excel file consistently.

## Root Cause
When `deduct_stock()` is called, it returns the price from the OLDEST batch (FIFO), which can be different from other batches of the same item.

Example:
- Item "أجبان" has 9 batches with prices: 14.82, 20.34, 26.44, 26.90, 27.04, 30.04, 30.07, 92.76
- FIFO returns 14.82 (oldest), but Excel might show 30.04 for a newer batch
- This causes 100% price mismatch in the diagnostic

## Solution Options

### Option 1: Use Average Price (RECOMMENDED)
Calculate the weighted average price across all batches for each item.

**Pros:**
- Consistent pricing across all invoices
- Reflects the true average cost
- Still profitable (average is above average cost)

**Cons:**
- Price won't exactly match any single Excel row
- Need to recalculate when batches change

### Option 2: Use Most Common Price
Use the price that appears most frequently in Excel for that item.

**Pros:**
- Matches an actual Excel price
- Simple to implement

**Cons:**
- Might not be the most representative
- Could still have multiple "most common" prices

### Option 3: Use Latest Batch Price
Always use the price from the newest batch (reverse FIFO for pricing only).

**Pros:**
- Matches current market price
- Simple logic

**Cons:**
- Might be higher than older batches
- Could reduce sales if prices increased

### Option 4: Keep FIFO but Document It
Accept that FIFO pricing is correct per the implementation plan.

**Pros:**
- Follows original spec
- Realistic inventory accounting

**Cons:**
- Prices won't match Excel exactly
- User expects exact Excel prices

## Recommended Implementation

**Use Option 1: Weighted Average Price**

### Changes Needed:

1. **Add method to InventoryManager:**
```python
def get_average_price(self, item_name: str) -> Decimal:
    """Get weighted average price for an item across all batches."""
    batches = [p for p in self.products if p['item_name'] == item_name]
    
    if not batches:
        raise ValueError(f"Item not found: {item_name}")
    
    total_value = sum(
        p['unit_price_before_vat'] * p['quantity_imported'] 
        for p in batches
    )
    total_quantity = sum(p['quantity_imported'] for p in batches)
    
    return (total_value / total_quantity).quantize(Decimal('0.01'))
```

2. **Modify alignment.py to use average price:**
In `_create_authentic_price_line_items()`, replace:
```python
# OLD: Use FIFO price
fifo_price = deductions[0][2]

# NEW: Use average price
average_price = self.simulator.inventory.get_average_price(product['item_name'])
```

3. **Update cost validation:**
Compare average price against average cost (not FIFO cost).

## Alternative: User Configuration

Add a config option to let user choose pricing strategy:
```python
PRICING_STRATEGY = "average"  # Options: "fifo", "average", "latest", "most_common"
```

This gives flexibility while maintaining the FIFO inventory tracking.
