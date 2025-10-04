"""
Smart Sales Generation Module
Replaces random logic with weighted, deterministic algorithms for realistic sales patterns.

Priority 1 Features:
1. Deterministic Date Distribution - Weighted by business patterns
2. Smart Invoice Size Distribution - Normal distribution with business logic
3. Product Popularity Weighting - Based on price, stock, and seasonality
"""

import random
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple
from hijri_converter import Hijri, Gregorian


class SmartSalesGenerator:
    """
    Generates realistic sales patterns using weighted algorithms.
    """
    
    def __init__(self, inventory, holidays, random_seed: int = 42):
        """
        Initialize smart sales generator.
        
        Args:
            inventory: InventoryManager instance
            holidays: List of holiday dates
            random_seed: Seed for reproducibility
        """
        self.inventory = inventory
        self.holidays = holidays
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        # Cache product weights
        self.product_weights_cache = {}
    
    def calculate_date_weight(
        self,
        target_date: date,
        quarter_start: date,
        quarter_end: date
    ) -> float:
        """
        Calculate how likely sales occur on this date.
        
        Factors:
        - Day of week (Thursday peak, Friday low)
        - Salary days (25-28th of month)
        - End of quarter push
        - Ramadan boost
        
        Returns:
            Weight multiplier (1.0 = normal, 2.0 = 2x likely)
        """
        weight = 1.0
        
        # 1. Day of week pattern
        weekday = target_date.weekday()
        day_weights = {
            0: 1.0,   # Monday
            1: 1.0,   # Tuesday
            2: 1.1,   # Wednesday (mid-week pickup)
            3: 1.5,   # Thursday (pre-weekend shopping peak)
            4: 0.3,   # Friday (half day, low sales)
            5: 1.3,   # Saturday (weekend shopping)
            6: 1.2,   # Sunday
        }
        weight *= day_weights.get(weekday, 1.0)
        
        # 2. Salary days pattern (25-28th = payday, 1-5th = post-payday spending)
        day_of_month = target_date.day
        if 25 <= day_of_month <= 28:  # Salary days
            weight *= 2.0
        elif 1 <= day_of_month <= 5:  # Post-salary spending
            weight *= 1.5
        elif 20 <= day_of_month <= 24:  # Pre-salary buildup
            weight *= 1.3
        elif 10 <= day_of_month <= 15:  # Mid-month dip
            weight *= 0.9
        
        # 3. End of quarter push (businesses rush to meet targets)
        days_to_end = (quarter_end - target_date).days
        if days_to_end <= 3:  # Last 3 days
            weight *= 2.0
        elif days_to_end <= 7:  # Last week
            weight *= 1.8
        elif days_to_end <= 14:  # Last 2 weeks
            weight *= 1.4
        
        # 4. Ramadan boost (approximate - Ramadan 2023: March 23 - April 21, 2024: March 11 - April 9)
        # Simplified check for demo (in production, use hijri_converter properly)
        month = target_date.month
        if month in [3, 4]:  # Ramadan months (approximate)
            # Check if it's actually Ramadan using Hijri calendar
            try:
                hijri_date = Gregorian(target_date.year, target_date.month, target_date.day).to_hijri()
                if hijri_date.month == 9:  # Ramadan is 9th month in Hijri
                    weight *= 2.5
            except:
                # Fallback if hijri_converter not available
                if month == 3 and target_date.day >= 20:
                    weight *= 2.5
                elif month == 4 and target_date.day <= 20:
                    weight *= 2.5
        
        # 5. Beginning of quarter (slower start)
        days_from_start = (target_date - quarter_start).days
        if days_from_start <= 7:  # First week
            weight *= 0.8
        
        return weight
    
    def calculate_invoice_size(
        self,
        target_date: date,
        remaining_target: Decimal,
        days_remaining: int,
        quarter_start: date,
        quarter_end: date
    ) -> Decimal:
        """
        Calculate realistic invoice size using normal distribution.
        
        Args:
            target_date: Date of invoice
            remaining_target: Remaining sales target (ex-VAT)
            days_remaining: Working days remaining
            quarter_start: Start of quarter
            quarter_end: End of quarter
            
        Returns:
            Invoice size (ex-VAT)
        """
        if days_remaining <= 0:
            days_remaining = 1
        
        # Base: Average daily target
        avg_daily = float(remaining_target) / days_remaining
        
        # Adjust by day type
        multiplier = 1.0
        
        # Day of week adjustment
        weekday = target_date.weekday()
        if weekday == 3:  # Thursday (bigger baskets)
            multiplier *= 1.5
        elif weekday in [5, 6]:  # Weekend
            multiplier *= 1.3
        elif weekday == 4:  # Friday (smaller baskets)
            multiplier *= 0.5
        
        # Salary week adjustment
        day_of_month = target_date.day
        if 25 <= day_of_month <= 28:
            multiplier *= 1.8
        elif 1 <= day_of_month <= 5:
            multiplier *= 1.4
        
        # End of quarter urgency
        days_to_end = (quarter_end - target_date).days
        if days_to_end <= 7:
            multiplier *= 1.5
        elif days_to_end <= 14:
            multiplier *= 1.3
        
        # Calculate mean and std dev for normal distribution
        mean = avg_daily * multiplier
        std_dev = mean * 0.3  # 30% standard deviation
        
        # Generate size from normal distribution
        size = np.random.normal(mean, std_dev)
        
        # Clamp to reasonable range
        min_size = 500.0
        max_size = min(float(remaining_target), 10000.0)
        
        clamped_size = max(min_size, min(size, max_size))
        
        return Decimal(str(round(clamped_size, 2)))
    
    def calculate_product_weight(
        self,
        product: Dict,
        target_date: date
    ) -> float:
        """
        Calculate how likely this product sells.
        
        Factors:
        - Price point (cheaper items sell more frequently)
        - Stock level (high stock = popular item)
        - Classification (some categories move faster)
        - Seasonal factors
        
        Returns:
            Weight multiplier (1.0 = normal, 2.0 = 2x likely)
        """
        weight = 1.0
        
        # 1. Price point (cheaper items sell more frequently)
        price = float(product['unit_price_ex_vat'])
        if price < 10:
            weight *= 2.5  # High-frequency items (snacks, small items)
        elif price < 20:
            weight *= 2.0
        elif price < 50:
            weight *= 1.5  # Medium-frequency
        elif price < 100:
            weight *= 1.0  # Normal
        else:
            weight *= 0.5  # Low-frequency (premium items)
        
        # 2. Stock level (items with more stock likely imported more = more popular)
        qty = product['qty_remaining']
        if qty > 1000:
            weight *= 1.8  # Very popular item (large import)
        elif qty > 500:
            weight *= 1.5  # Popular
        elif qty > 200:
            weight *= 1.2  # Normal
        elif qty > 50:
            weight *= 1.0  # Normal
        else:
            weight *= 0.7  # Low stock = less popular or end of life
        
        # 3. Classification (some categories sell faster)
        classification = product.get('shipment_class', '')
        if 'NONEXC_OUTSIDE' in classification:
            weight *= 1.3  # Faster-moving goods
        elif 'NONEXC_INSPECTION' in classification:
            weight *= 1.1  # Normal goods
        # Excise goods (EXC_INSPECTION) keep base weight
        
        # 4. Seasonal factors
        month = target_date.month
        item_name = product['item_description'].lower()
        
        # Summer drinks (June-August)
        if month in [6, 7, 8]:
            if any(word in item_name for word in ['juice', 'عصير', 'شراب', 'drink', 'مشروب']):
                weight *= 1.8
        
        # Ramadan items (coffee, tea, dates)
        if month in [3, 4]:  # Ramadan months (approximate)
            if any(word in item_name for word in ['coffee', 'قهوة', 'tea', 'شاي', 'تمر', 'date']):
                weight *= 2.0
            if any(word in item_name for word in ['juice', 'عصير', 'milk', 'حليب']):
                weight *= 1.6
        
        # Winter comfort foods (December-February)
        if month in [12, 1, 2]:
            if any(word in item_name for word in ['chocolate', 'شوكولاتة', 'coffee', 'قهوة', 'soup', 'شوربة']):
                weight *= 1.4
        
        return weight
    
    def select_weighted_products(
        self,
        available_products: List[Dict],
        target_date: date,
        num_items: int
    ) -> List[Dict]:
        """
        Select products using weighted random selection.
        
        Args:
            available_products: List of products with stock
            target_date: Date for seasonal weighting
            num_items: Number of items to select
            
        Returns:
            List of selected products
        """
        if not available_products:
            return []
        
        # Calculate weights for all products
        weights = []
        for product in available_products:
            # Use cache if available
            cache_key = (product['lot_id'], target_date.month)
            if cache_key in self.product_weights_cache:
                weight = self.product_weights_cache[cache_key]
            else:
                weight = self.calculate_product_weight(product, target_date)
                self.product_weights_cache[cache_key] = weight
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            # Fallback to uniform if all weights are 0
            weights = [1.0] * len(available_products)
            total_weight = len(available_products)
        
        probabilities = [w / total_weight for w in weights]
        
        # Select items (without replacement)
        num_to_select = min(num_items, len(available_products))
        selected_indices = np.random.choice(
            len(available_products),
            size=num_to_select,
            replace=False,
            p=probabilities
        )
        
        return [available_products[i] for i in selected_indices]
    
    def distribute_target_across_dates(
        self,
        working_days: List[date],
        total_target: Decimal,
        quarter_start: date,
        quarter_end: date
    ) -> Dict[date, Decimal]:
        """
        Distribute sales target across dates using weighted distribution.
        
        Args:
            working_days: List of working days in period
            total_target: Total sales target (ex-VAT)
            quarter_start: Start of quarter
            quarter_end: End of quarter
            
        Returns:
            Dictionary mapping date to target amount
        """
        # Calculate weight for each date
        date_weights = {}
        for day in working_days:
            weight = self.calculate_date_weight(day, quarter_start, quarter_end)
            date_weights[day] = weight
        
        # Normalize weights to sum to 1.0
        total_weight = sum(date_weights.values())
        date_probabilities = {
            day: weight / total_weight
            for day, weight in date_weights.items()
        }
        
        # Distribute target proportionally
        daily_targets = {}
        for day, probability in date_probabilities.items():
            daily_targets[day] = (total_target * Decimal(str(probability))).quantize(Decimal('0.01'))
        
        return daily_targets
    
    def get_weighted_date(
        self,
        available_dates: List[date],
        quarter_start: date,
        quarter_end: date
    ) -> date:
        """
        Select a date using weighted random selection.
        
        Args:
            available_dates: List of available dates
            quarter_start: Start of quarter
            quarter_end: End of quarter
            
        Returns:
            Selected date
        """
        if not available_dates:
            return None
        
        # Calculate weights
        weights = [
            self.calculate_date_weight(d, quarter_start, quarter_end)
            for d in available_dates
        ]
        
        # Normalize
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(available_dates)
        
        probabilities = [w / total_weight for w in weights]
        
        # Select
        selected_date = np.random.choice(available_dates, p=probabilities)
        return selected_date
    
    def calculate_realistic_time(self, target_date: date) -> datetime:
        """
        Calculate realistic time of day for invoice.
        
        Args:
            target_date: Date of invoice
            
        Returns:
            Datetime with realistic hour/minute
        """
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
        
        # Adjust for Friday (half day)
        if target_date.weekday() == 4:
            # Shift weight to morning, reduce afternoon
            for hour in range(15, 22):
                hour_weights[hour] *= 0.2
            for hour in range(9, 13):
                hour_weights[hour] *= 1.5
        
        # Weighted random selection
        hours = list(hour_weights.keys())
        weights = list(hour_weights.values())
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        
        hour = np.random.choice(hours, p=probabilities)
        minute = random.randint(0, 59)
        
        return datetime.combine(
            target_date,
            datetime.min.time().replace(hour=hour, minute=minute)
        )


# Utility function for integration
def create_smart_generator(inventory, holidays, random_seed: int = 42) -> SmartSalesGenerator:
    """
    Factory function to create SmartSalesGenerator.
    
    Args:
        inventory: InventoryManager instance
        holidays: List of holiday dates
        random_seed: Seed for reproducibility
        
    Returns:
        SmartSalesGenerator instance
    """
    return SmartSalesGenerator(inventory, holidays, random_seed)
