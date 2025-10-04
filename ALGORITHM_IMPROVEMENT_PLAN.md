# 🧠 Sales Generation Algorithm - Improvement Plan

## 📊 Current Algorithm Analysis

### What We're Doing Now (Problems):

1. **Random Date Selection** ❌
   - Picks random working days
   - No consideration for realistic sales patterns
   - Doesn't reflect actual business behavior

2. **Random Invoice Sizes** ❌
   - Uses `random.randint(2000, 8000)` for invoice amounts
   - No correlation with day of week, month, or season
   - Unrealistic distribution

3. **Random Item Selection** ❌
   - Picks items randomly from available stock
   - No consideration for:
     - Product popularity
     - Seasonal demand
     - Customer preferences
     - Fast-moving vs slow-moving items

4. **No Time-of-Day Logic** ❌
   - Random hours between 9-21
   - No peak hours (lunch, evening)
   - No slow hours (morning, late night)

5. **No Customer Behavior** ❌
   - All cash customers treated identically
   - No repeat customers
   - No basket correlation (items bought together)

---

## 🎯 Proposed Improvements

### Phase 1: **Deterministic Date Distribution** (High Impact)

**Instead of:** Random date selection  
**Use:** Weighted distribution based on real business patterns

```python
def calculate_date_weight(date, quarter_start, quarter_end):
    """Calculate how likely sales occur on this date."""
    weight = 1.0
    
    # 1. Day of week pattern
    weekday = date.weekday()
    if weekday == 3:  # Thursday (pre-weekend shopping)
        weight *= 1.5
    elif weekday == 4:  # Friday (weekend)
        weight *= 0.3  # Lower sales (half day)
    elif weekday == 5:  # Saturday
        weight *= 1.3
    elif weekday == 6:  # Sunday
        weight *= 1.2
    
    # 2. Month progression (sales increase toward end of month)
    day_of_month = date.day
    if 25 <= day_of_month <= 28:  # Salary days
        weight *= 2.0
    elif day_of_month <= 5:  # Post-salary spending
        weight *= 1.5
    elif day_of_month >= 20:  # Pre-salary buildup
        weight *= 1.3
    
    # 3. Ramadan boost (if applicable)
    # Check if date falls in Ramadan
    if is_ramadan(date):
        weight *= 2.5
    
    # 4. End of quarter push
    days_to_end = (quarter_end - date).days
    if days_to_end <= 7:  # Last week of quarter
        weight *= 1.8
    elif days_to_end <= 14:  # Last 2 weeks
        weight *= 1.4
    
    return weight
```

**Impact:** More realistic date distribution, better matches real business patterns

---

### Phase 2: **Smart Invoice Size Distribution** (High Impact)

**Instead of:** Random sizes  
**Use:** Normal distribution with business logic

```python
def calculate_invoice_size(date, remaining_target, days_remaining):
    """Calculate realistic invoice size."""
    
    # Base: Average daily target
    avg_daily = remaining_target / max(days_remaining, 1)
    
    # Adjust by day type
    weekday = date.weekday()
    if weekday == 3:  # Thursday (bigger baskets)
        multiplier = 1.5
    elif weekday in [5, 6]:  # Weekend
        multiplier = 1.3
    else:
        multiplier = 1.0
    
    # Adjust by time in quarter
    if days_remaining <= 7:  # End of quarter urgency
        multiplier *= 1.5
    
    # Use normal distribution (not uniform random)
    # Mean = avg_daily * multiplier
    # Std dev = 30% of mean
    mean = float(avg_daily * Decimal(str(multiplier)))
    std_dev = mean * 0.3
    
    size = np.random.normal(mean, std_dev)
    
    # Clamp to reasonable range
    min_size = 500
    max_size = min(remaining_target, Decimal("10000"))
    
    return Decimal(str(max(min_size, min(size, float(max_size)))))
```

**Impact:** More realistic invoice sizes, better distribution

---

### Phase 3: **Product Popularity Weighting** (Medium Impact)

**Instead of:** Random item selection  
**Use:** Weighted selection based on product characteristics

```python
def calculate_product_weight(product, date):
    """Calculate how likely this product sells."""
    weight = 1.0
    
    # 1. Price point (cheaper items sell more frequently)
    price = product['unit_price_ex_vat']
    if price < 10:
        weight *= 2.0  # High-frequency items
    elif price < 50:
        weight *= 1.5  # Medium-frequency
    elif price < 100:
        weight *= 1.0  # Normal
    else:
        weight *= 0.5  # Low-frequency (premium items)
    
    # 2. Stock level (items with more stock likely imported more = more popular)
    qty = product['qty_remaining']
    if qty > 1000:
        weight *= 1.5  # Popular item (large import)
    elif qty > 500:
        weight *= 1.2
    elif qty < 50:
        weight *= 0.7  # Low stock = less popular or end of life
    
    # 3. Classification (some categories sell faster)
    if product['shipment_class'] == 'NONEXC_OUTSIDE':
        weight *= 1.3  # Faster-moving goods
    
    # 4. Seasonal factors
    month = date.month
    item_name = product['item_description'].lower()
    
    # Summer drinks
    if month in [6, 7, 8] and any(word in item_name for word in ['juice', 'عصير', 'شراب']):
        weight *= 1.8
    
    # Ramadan items
    if is_ramadan(date) and any(word in item_name for word in ['coffee', 'قهوة', 'tea', 'شاي']):
        weight *= 2.0
    
    return weight
```

**Impact:** More realistic product mix, reflects actual demand patterns

---

### Phase 4: **Basket Correlation** (Medium Impact)

**Instead of:** Independent item selection  
**Use:** Items that are commonly bought together

```python
# Define product affinities
PRODUCT_AFFINITIES = {
    'قهوة': ['حليب', 'سكر', 'كريمة'],  # Coffee with milk, sugar, creamer
    'شيبس': ['مشروبات', 'عصير'],       # Chips with drinks
    'جبن': ['خبز', 'زبدة'],            # Cheese with bread, butter
}

def select_basket_items(primary_item, available_products, target_items=3):
    """Select items that go well together."""
    basket = [primary_item]
    
    # Get affinity items
    primary_name = primary_item['item_description']
    affinity_keywords = []
    
    for key, values in PRODUCT_AFFINITIES.items():
        if key in primary_name:
            affinity_keywords = values
            break
    
    # Add affinity items if available
    for product in available_products:
        if len(basket) >= target_items:
            break
        
        if any(keyword in product['item_description'] for keyword in affinity_keywords):
            basket.append(product)
    
    # Fill remaining with weighted random
    while len(basket) < target_items:
        remaining = [p for p in available_products if p not in basket]
        if not remaining:
            break
        basket.append(weighted_random_choice(remaining))
    
    return basket
```

**Impact:** More realistic baskets, reflects shopping behavior

---

### Phase 5: **Time-of-Day Distribution** (Low Impact)

**Instead of:** Random hours  
**Use:** Realistic hourly distribution

```python
def select_invoice_time(date):
    """Select realistic time for invoice."""
    
    # Define hourly weights (9 AM to 10 PM)
    hour_weights = {
        9: 0.3,   # Slow morning
        10: 0.5,
        11: 0.8,
        12: 1.2,  # Lunch rush
        13: 1.5,  # Peak
        14: 1.0,
        15: 0.8,
        16: 0.9,
        17: 1.3,  # Evening rush
        18: 1.8,  # Peak evening
        19: 1.5,
        20: 1.0,
        21: 0.6,  # Closing
    }
    
    # Adjust for day of week
    if date.weekday() == 4:  # Friday (half day)
        # Shift weight to morning
        for hour in range(15, 22):
            hour_weights[hour] *= 0.3
    
    # Weighted random selection
    hours = list(hour_weights.keys())
    weights = list(hour_weights.values())
    hour = random.choices(hours, weights=weights)[0]
    minute = random.randint(0, 59)
    
    return datetime.min.time().replace(hour=hour, minute=minute)
```

**Impact:** More realistic timestamps, minor improvement

---

## 🎯 Implementation Priority

### Priority 1: **Must Have** (Implement First)
1. ✅ **Deterministic Date Distribution** - Biggest impact on realism
2. ✅ **Smart Invoice Size Distribution** - Better target matching
3. ✅ **Product Popularity Weighting** - More realistic product mix

### Priority 2: **Should Have** (Implement Second)
4. ⏳ **Basket Correlation** - Nice to have, moderate complexity
5. ⏳ **Time-of-Day Distribution** - Low impact, easy to add



---

## 📊 Expected Improvements

### Before (Current):
- ❌ Random, unrealistic patterns
- ❌ Poor date distribution
- ❌ Uniform random sizes
- ❌ No product preferences
- ⚠️ Works but looks artificial

### After (Improved):
- ✅ Realistic business patterns
- ✅ Weighted date distribution (salary days, weekends, end of quarter)
- ✅ Normal distribution for sizes
- ✅ Popular items sell more
- ✅ Looks like real business data

---

## 🔧 Implementation Strategy

### Step 1: Create New Module `smart_sales.py`
```python
"""
Smart sales generation with realistic patterns.
Replaces random logic with weighted, deterministic algorithms.
"""

class SmartSalesGenerator:
    def __init__(self, inventory, holidays):
        self.inventory = inventory
        self.holidays = holidays
        self.product_weights = self._calculate_product_weights()
    
    def generate_realistic_sales(self, start_date, end_date, target_sales):
        """Generate sales with realistic patterns."""
        # Calculate date weights
        date_weights = self._calculate_date_weights(start_date, end_date)
        
        # Distribute target across dates
        daily_targets = self._distribute_target(target_sales, date_weights)
        
        # Generate invoices for each day
        invoices = []
        for date, daily_target in daily_targets.items():
            day_invoices = self._generate_day_invoices(date, daily_target)
            invoices.extend(day_invoices)
        
        return invoices
```

### Step 2: Integrate with Existing System
- Keep current `alignment.py` as fallback
- Add flag to switch between random and smart generation
- Test both side-by-side

### Step 3: Validate Results
- Compare variance before/after
- Check if patterns look more realistic
- Verify calculations still correct

---

## 🧪 Testing Plan

### Test 1: Date Distribution
- Generate 1000 invoices
- Plot by day of week
- Verify Thursday/Saturday peaks
- Verify Friday dips

### Test 2: Invoice Size Distribution
- Generate 1000 invoices
- Plot histogram
- Verify normal distribution
- Check mean matches target

### Test 3: Product Mix
- Generate 1000 invoices
- Count item frequencies
- Verify popular items appear more
- Check against stock levels

### Test 4: Target Matching
- Run full quarter generation
- Compare variance with current algorithm
- Should be similar or better

---

## 💡 Key Insights

### Why This is Better:

1. **Deterministic** - Same seed = same results (reproducible)
2. **Realistic** - Matches real business patterns
3. **Explainable** - Can justify why sales happened when they did
4. **Flexible** - Easy to adjust weights for different scenarios
5. **Auditable** - Clear logic, not black box randomness

### Trade-offs:

1. **More Complex** - More code to maintain
2. **More Parameters** - Need to tune weights
3. **Slower** - More calculations per invoice
4. **Less Random** - Might look "too perfect"

---

## 🎯 Recommendation

**Implement Priority 1 items first:**
1. Date weighting
2. Invoice size distribution
3. Product popularity

**Expected outcome:**
- Similar or better variance
- Much more realistic patterns
- Easier to explain to auditors
- Better reflects actual business

**Time estimate:** 4-6 hours for Priority 1

---

**Next Step:** Should we implement this? I can create the `smart_sales.py` module with these improvements.

