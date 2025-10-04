from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
import random
from hijri_converter import Gregorian
from config import *
from inventory import InventoryManager


class SalesSimulator:
    """
    Generates realistic sales invoices based on business rules.
    """
    
    def __init__(self, inventory: InventoryManager, holidays: List[date]):
        self.inventory = inventory
        self.holidays = holidays
        self.invoice_counter_simplified = 0
        self.invoice_counter_tax = 0
    
    def is_working_day(self, check_date: date) -> bool:
        """
        Check if sales should occur on this date.
        
        Args:
            check_date: Date to check
            
        Returns:
            True if it's a working day, False if Friday or holiday
        """
        # Check if Friday (weekday 4)
        if check_date.weekday() == 4:
            return False
        
        # Check if in holidays list
        if check_date in self.holidays:
            return False
        
        return True
    
    def calculate_boost_factor(self, check_date: date) -> float:
        """
        Calculate sales boost multiplier for a specific date.
        
        Boosts:
        - Ramadan/Shaaban: 2.0x
        - Day 27 (salary day): 1.5x
        - Day 1 (social security): 1.2x
        - Day 10 (citizen account): 1.1x
        
        Args:
            check_date: Date to calculate boost for
            
        Returns:
            Boost multiplier (1.0 = normal, 2.0 = double sales, etc.)
        """
        boost = 1.0
        
        # Check Hijri calendar for Ramadan (month 9) or Shaaban (month 8)
        try:
            hijri_date = Gregorian(check_date.year, check_date.month, check_date.day).to_hijri()
            if hijri_date.month in [8, 9]:  # Shaaban or Ramadan
                boost *= RAMADAN_BOOST
        except:
            pass  # If conversion fails, skip Hijri boost
        
        # Check salary days
        day_of_month = check_date.day
        if day_of_month == 27:
            boost *= SALARY_DAY_27_BOOST
        elif day_of_month == 1:
            boost *= SALARY_DAY_1_BOOST
        elif day_of_month == 10:
            boost *= SALARY_DAY_10_BOOST
        
        return boost
    

    def select_items_for_basket(
        self,
        invoice_type: str,
        num_items: int,
        adjustment_factor: float = 1.0,
        current_date: date = None
    ) -> List[Tuple[Dict, int, Decimal]]:
        """
        Select LOTS for an invoice basket respecting classification rules.
        Now works with LOT-BASED inventory (not aggregated items).
        Only select lots that are in stock by current_date.

        Returns:
            List of tuples: (lot_dict, quantity, lot_price)
        """
        basket = []

        # Decide if this basket will be OUTSIDE_INSPECTION (20% chance)
        use_outside_inspection = random.random() < 0.2

        if use_outside_inspection:
            # OUTSIDE_INSPECTION must be alone
            available_lots = self.inventory.get_available_lots_by_classification(
                OUTSIDE_INSPECTION,
                current_date=current_date
            )

            if available_lots:
                # Pick one random LOT
                lot = random.choice(available_lots)
                # Try different quantities until we find one that works
                for qty in [40, 30, 20, 10, 5, 3]:
                    if self.inventory.check_lot_stock_available(lot['lot_id'], qty):
                        lot_price = lot['unit_price_ex_vat']  # LOT-SPECIFIC PRICE
                        basket.append((lot, qty, lot_price))
                        return basket

        # Regular basket (not OUTSIDE_INSPECTION)
        if invoice_type == "TAX":
            # TAX invoices: Only UNDER_NON_SELECTIVE
            available_lots = self.inventory.get_available_lots_by_classification(
                UNDER_NON_SELECTIVE,
                current_date=current_date
            )
        else:
            # SIMPLIFIED invoices: ALL classifications
            non_selective = self.inventory.get_available_lots_by_classification(
                UNDER_NON_SELECTIVE,
                current_date=current_date
            )
            selective = self.inventory.get_available_lots_by_classification(
                UNDER_SELECTIVE,
                current_date=current_date
            )
            outside = self.inventory.get_available_lots_by_classification(
                OUTSIDE_INSPECTION,
                current_date=current_date
            )
            available_lots = non_selective + selective + outside

            # Weight towards selective items (70% selective, 30% non-selective)
            if selective and non_selective:
                if random.random() < 0.7 and selective:
                    available_lots = selective
                else:
                    available_lots = non_selective

        if not available_lots:
            return []  # No lots available

        # Try to select lots until we have enough in basket
        attempts = 0
        max_attempts = num_items * 3
        selected_lot_ids = set()  # Track selected lots to avoid duplicates

        while len(basket) < min(num_items, len(available_lots)) and attempts < max_attempts:
            attempts += 1
            lot = random.choice(available_lots)

            # Skip if this specific lot already in basket
            if lot['lot_id'] in selected_lot_ids:
                continue

            # Try different quantities (start high, go lower if needed)
            for qty in [40, 30, 20, 15, 10, 5, 3]:
                if self.inventory.check_lot_stock_available(lot['lot_id'], qty):
                    lot_price = lot['unit_price_ex_vat']  # LOT-SPECIFIC PRICE
                    basket.append((lot, qty, lot_price))
                    selected_lot_ids.add(lot['lot_id'])
                    break

        return basket
    def create_invoice(
        self,
        invoice_type: str,
        customer: Optional[Dict],
        basket: List[Tuple[Dict, int, Decimal]],
        invoice_date: datetime
    ) -> Dict:
        """
        Create an invoice from a basket of LOTS.
        Now LOT-BASED: Each line item tracks lot_id and lot-specific pricing.

        Args:
            invoice_type: "SIMPLIFIED" or "TAX"
            customer: Customer dict (None for cash customers)
            basket: List of (lot_dict, quantity, lot_price) tuples
            invoice_date: Date and time of invoice

        Returns:
            Invoice dictionary with lot-tracked line items
        """
        # Generate invoice number
        if invoice_type == "SIMPLIFIED":
            self.invoice_counter_simplified += 1
            invoice_number = f"INV-SIMP-{self.invoice_counter_simplified:06d}"
        else:
            self.invoice_counter_tax += 1
            invoice_number = f"INV-TAX-{self.invoice_counter_tax:06d}"

        # Calculate line items - ONE LINE PER LOT
        # CRITICAL: If basket has multiple lots of same item_description,
        # each lot gets its OWN line item
        line_items = []
        subtotal = Decimal("0")
        vat_total = Decimal("0")

        for lot, quantity, lot_price in basket:
            line_subtotal = lot_price * quantity
            line_vat = line_subtotal * VAT_RATE
            line_total = line_subtotal + line_vat

            # Create line item with LOT tracking
            line_item = {
                # PRD-compliant fields
                'lot_id': lot['lot_id'],
                'customs_declaration_no': lot['customs_declaration_no'],
                'item_description': lot['item_description'],
                'shipment_class': lot['shipment_class'],
                'quantity': quantity,
                'unit_price_ex_vat': lot_price,
                'unit_cost_ex_vat': lot['unit_cost_ex_vat'],
                'line_subtotal': line_subtotal,
                'vat_amount': line_vat,
                'line_total': line_total,

                # Legacy fields for backward compatibility
                'item_name': lot['item_name'],
                'customs_declaration': lot['customs_declaration'],
                'classification': lot['classification'],
                'unit_price': lot_price
            }

            line_items.append(line_item)
            subtotal += line_subtotal
            vat_total += line_vat

            # Deduct from inventory using LOT-SPECIFIC deduction
            self.inventory.deduct_stock(lot['lot_id'], quantity)

        # Round to 2 decimal places
        subtotal = subtotal.quantize(Decimal('0.01'))
        vat_total = vat_total.quantize(Decimal('0.01'))
        total = subtotal + vat_total

        # Create invoice
        invoice = {
            'invoice_number': invoice_number,
            'invoice_type': invoice_type,
            'customer_name': customer['customer_name'] if customer else CASH_CUSTOMER_NAME,
            'customer_tax_number': customer['tax_number'] if customer else None,
            'customer_address': customer.get('address', '') if customer else None,
            'invoice_date': invoice_date,
            'line_items': line_items,
            'subtotal': subtotal,
            'vat_amount': vat_total,
            'total': total,
            'qr_code_data': f"INV:{invoice_number}|{SELLER_NAME}|{SELLER_ADDRESS}|{SELLER_TAX_NUMBER}"
        }

        return invoice
    
    def generate_daily_invoices(
        self,
        target_date: date,
        adjustment_factor: float = 1.0,
        invoice_type_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate all invoices for a specific day.
        
        Args:
            target_date: Date to generate invoices for
            adjustment_factor: Price adjustment multiplier
            invoice_type_filter: If set, only generate this type ("SIMPLIFIED" or "TAX")
            
        Returns:
            List of invoice dictionaries
        """
        # Check if working day
        if not self.is_working_day(target_date):
            return []
        
        # Calculate boost
        boost = self.calculate_boost_factor(target_date)
        
        # Base number of invoices per day (5-20)
        base_invoices = random.randint(5, 20)
        num_invoices = int(base_invoices * boost)
        
        invoices = []
        
        for i in range(num_invoices):
            # Random time during working hours
            hour = random.randint(WORKING_HOURS[0], WORKING_HOURS[1])
            minute = random.randint(0, 59)
            invoice_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Decide invoice type (if not filtered)
            if invoice_type_filter:
                invoice_type = invoice_type_filter
            else:
                # 80% simplified, 20% tax
                invoice_type = "SIMPLIFIED" if random.random() < 0.8 else "TAX"
            
            # Select items for basket
            num_items = random.randint(MIN_ITEMS_PER_INVOICE, MAX_ITEMS_PER_INVOICE)
            basket = self.select_items_for_basket(invoice_type, num_items, adjustment_factor, target_date)
            
            if not basket:
                continue  # No items available, skip
            
            # Create invoice
            customer = None  # For now, always cash customer (we'll handle VAT customers in alignment)
            invoice = self.create_invoice(invoice_type, customer, basket, invoice_datetime)
            invoices.append(invoice)
        
        return invoices
    
    def get_invoice_summary(self) -> Dict:
        """
        Get summary of generated invoices.
        
        Returns:
            Dictionary with counts
        """
        return {
            'simplified_invoices': self.invoice_counter_simplified,
            'tax_invoices': self.invoice_counter_tax,
            'total_invoices': self.invoice_counter_simplified + self.invoice_counter_tax
        }