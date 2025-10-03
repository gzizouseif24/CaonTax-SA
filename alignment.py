from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Dict
from simulation import SalesSimulator
from config import VAT_RATE, TOLERANCE, CASH_CUSTOMER_NAME
import random


class QuarterlyAligner:
    """
    Aligns simulated sales to exact quarterly targets.
    """
    
    def __init__(self, simulator: SalesSimulator):
        self.simulator = simulator
    
    def align_quarter(
        self,
        quarter_name: str,
        start_date: date,
        end_date: date,
        target_sales: Decimal,
        target_vat: Decimal,
        vat_customers: List[Dict] = None
    ) -> List[Dict]:
        """Generate invoices matching exact quarterly targets."""
        
        print(f"\n{'='*60}")
        print(f"ALIGNING {quarter_name}")
        print(f"{'='*60}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Target Sales: {target_sales:,.2f} SAR")
        print(f"Target VAT: {target_vat:,.2f} SAR")
        
        # Phase 1: Generate VAT customer invoices
        vat_invoices = []
        vat_sales = Decimal("0")
        vat_vat = Decimal("0")
        
        if vat_customers:
            print(f"\nPhase 1: Generating {len(vat_customers)} VAT customer invoices...")
            vat_invoices = self._generate_vat_customer_invoices(vat_customers)
            vat_sales = sum(inv['subtotal'] for inv in vat_invoices)
            vat_vat = sum(inv['vat_amount'] for inv in vat_invoices)
            print(f"  Generated: {len(vat_invoices)} invoices")
            print(f"  VAT Customer Sales: {vat_sales:,.2f} SAR")
            print(f"  VAT Customer VAT: {vat_vat:,.2f} SAR")
        else:
            print(f"\nPhase 1: No VAT customers for this quarter")
        
        # Phase 2: Calculate remaining gap
        remaining_sales = target_sales - vat_sales
        remaining_vat = target_vat - vat_vat
        
        print(f"\nPhase 2: Remaining to fill with cash sales:")
        print(f"  Sales needed: {remaining_sales:,.2f} SAR")
        print(f"  VAT needed: {remaining_vat:,.2f} SAR")
        
        # Phase 3: Generate controlled cash sales
        print(f"\nPhase 3: Generating cash sales to match target...")
        cash_invoices = self._generate_controlled_cash_sales(
            start_date,
            end_date,
            remaining_sales,
            remaining_vat
        )
        
        print(f"  Generated: {len(cash_invoices)} cash invoices")
        
        # Combine
        all_invoices = vat_invoices + cash_invoices
        
        # Verify
        actual_sales = sum(inv['subtotal'] for inv in all_invoices)
        actual_vat = sum(inv['vat_amount'] for inv in all_invoices)
        
        sales_diff = abs(actual_sales - target_sales)
        vat_diff = abs(actual_vat - target_vat)
        
        print(f"\n{'='*60}")
        print(f"ALIGNMENT COMPLETE")
        print(f"{'='*60}")
        print(f"Total Invoices: {len(all_invoices)}")
        print(f"  - VAT customers: {len(vat_invoices)}")
        print(f"  - Cash sales: {len(cash_invoices)}")
        print(f"\nTarget Sales: {target_sales:,.2f} SAR")
        print(f"Actual Sales: {actual_sales:,.2f} SAR")
        print(f"Difference: {sales_diff:.2f} SAR")
        print(f"\nTarget VAT: {target_vat:,.2f} SAR")
        print(f"Actual VAT: {actual_vat:,.2f} SAR")
        print(f"Difference: {vat_diff:.2f} SAR")
        
        if sales_diff < TOLERANCE and vat_diff < TOLERANCE:
            print(f"\n✓ MATCHED within tolerance (±{TOLERANCE} SAR)")
        else:
            print(f"\n⚠ NOT MATCHED - Difference exceeds tolerance")
        
        return all_invoices
    
    def _generate_vat_customer_invoices(self, customers: List[Dict]) -> List[Dict]:
        """Generate invoices for VAT customers with exact amounts."""
        invoices = []
        
        for customer in customers:
            # Customer amount includes VAT
            total_with_vat = customer['purchase_amount']
            subtotal = (total_with_vat / Decimal("1.15")).quantize(Decimal('0.01'))
            vat_amount = (subtotal * VAT_RATE).quantize(Decimal('0.01'))
            
            # Random date and time
            purchase_date = customer['purchase_date']
            invoice_datetime = datetime.combine(
                purchase_date,
                datetime.min.time().replace(
                    hour=random.randint(9, 21),
                    minute=random.randint(0, 59)
                )
            )
            
            # Create line items that sum to subtotal
            line_items = self._create_line_items_for_amount(
                subtotal,
                vat_amount,
                purchase_date,
                invoice_type="TAX"
            )
            
            if not line_items:
                print(f"  Warning: Could not create items for {customer['customer_name']}")
                continue
            
            # Build invoice
            self.simulator.invoice_counter_tax += 1
            invoice_number = f"INV-TAX-{self.simulator.invoice_counter_tax:06d}"

            # Handle both column name variations
            tax_number = customer.get('tax_id') or customer.get('tax_number', '')
            address = customer.get('adress') or customer.get('address', '')

            invoice = {
                'invoice_number': invoice_number,
                'invoice_type': 'TAX',
                'customer_name': customer['customer_name'],
                'customer_tax_number': tax_number,  # Use the variable
                'customer_address': address,  # Use the variable
                'invoice_date': invoice_datetime,
                'line_items': line_items,
                'subtotal': subtotal,
                'vat_amount': vat_amount,
                'total': (subtotal + vat_amount).quantize(Decimal('0.01')),
                'qr_code_data': f"INV:{invoice_number}|{customer['customer_name']}"
            }

            invoices.append(invoice)
        
        return invoices
    
    def _generate_controlled_cash_sales(
        self,
        start_date: date,
        end_date: date,
        target_sales: Decimal,
        target_vat: Decimal
    ) -> List[Dict]:
        """Generate cash invoices that match target exactly."""
        
        # Calculate working days
        working_days = []
        current = start_date
        while current <= end_date:
            if self.simulator.is_working_day(current):
                working_days.append(current)
            current += timedelta(days=1)
        
        print(f"    Working days: {len(working_days)}")
        
        # Calculate target number of invoices
        # Average ~3-8 invoices per working day
        target_invoice_count = len(working_days) * random.randint(3, 8)
        
        # Average invoice size
        avg_invoice = target_sales / target_invoice_count
        
        print(f"    Target invoices: ~{target_invoice_count}")
        print(f"    Avg invoice size: {avg_invoice:,.2f} SAR")
        
        invoices = []
        remaining = target_sales
        
        # Generate invoices
        for i in range(target_invoice_count):
            # Select random working day
            invoice_date = random.choice(working_days)
            
            # Calculate this invoice's amount
            if i == target_invoice_count - 1:
                # Last invoice gets exact remainder
                invoice_subtotal = remaining
            else:
                # Random amount around average (±30% variance)
                min_amount = float(avg_invoice) * 0.7
                max_amount = float(avg_invoice) * 1.3
                invoice_subtotal = Decimal(str(random.uniform(min_amount, max_amount)))
                
                # Don't exceed remaining
                if invoice_subtotal > remaining:
                    invoice_subtotal = remaining
            
            invoice_subtotal = invoice_subtotal.quantize(Decimal('0.01'))
            invoice_vat = (invoice_subtotal * VAT_RATE).quantize(Decimal('0.01'))
            
            # Create line items
            line_items = self._create_line_items_for_amount(
                invoice_subtotal,
                invoice_vat,
                invoice_date,
                invoice_type="SIMPLIFIED"
            )
            
            if not line_items:
                continue
            
            # Build invoice
            invoice_datetime = datetime.combine(
                invoice_date,
                datetime.min.time().replace(
                    hour=random.randint(9, 21),
                    minute=random.randint(0, 59)
                )
            )
            
            self.simulator.invoice_counter_simplified += 1
            invoice_number = f"INV-SIMP-{self.simulator.invoice_counter_simplified:06d}"
            
            invoice = {
                'invoice_number': invoice_number,
                'invoice_type': 'SIMPLIFIED',
                'customer_name': CASH_CUSTOMER_NAME,
                'customer_tax_number': None,
                'customer_address': None,
                'invoice_date': invoice_datetime,
                'line_items': line_items,
                'subtotal': invoice_subtotal,
                'vat_amount': invoice_vat,
                'total': (invoice_subtotal + invoice_vat).quantize(Decimal('0.01')),
                'qr_code_data': f"INV:{invoice_number}|{CASH_CUSTOMER_NAME}"
            }
            
            invoices.append(invoice)
            remaining -= invoice_subtotal
            
            if remaining <= Decimal("0.01"):
                break
        
        return invoices
    
    def _create_line_items_for_amount(
        self,
        target_subtotal: Decimal,
        target_vat: Decimal,
        invoice_date: date,
        invoice_type: str
    ) -> List[Dict]:
        """Create line items that sum to exact amount."""
        
        # Get available items
        from config import UNDER_NON_SELECTIVE, UNDER_SELECTIVE, OUTSIDE_INSPECTION
        
        if invoice_type == "TAX":
            # Only non-selective for VAT customers
            available = self.simulator.inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE)
        else:
            # Cash customers can buy ALL classifications (including OUTSIDE_INSPECTION)
            available = (
                self.simulator.inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE) +
                self.simulator.inventory.get_available_items_by_classification(UNDER_SELECTIVE) +
                self.simulator.inventory.get_available_items_by_classification(OUTSIDE_INSPECTION)
            )
        
        # Filter by stock date
        available = [item for item in available if item['stock_date'] <= invoice_date]
        
        if not available:
            print(f"    No items available for {invoice_type} invoice on {invoice_date}")
            return []
        
        # Number of items (1-5, but at least 1)
        max_items = min(5, len(available))
        num_items = random.randint(1, max_items) if max_items >= 1 else 1
        
        # Can't select more items than available
        num_items = min(num_items, len(available))
        
        # Select random items
        selected_items = random.sample(available, num_items)
        
        line_items = []
        remaining = target_subtotal
        
        for i, product in enumerate(selected_items):
            # Last item gets remainder
            if i == num_items - 1:
                line_subtotal = remaining
            else:
                # Split evenly with some variance
                line_subtotal = remaining / (num_items - i)
                variance = random.uniform(0.8, 1.2)
                line_subtotal = line_subtotal * Decimal(str(variance))
            
            line_subtotal = line_subtotal.quantize(Decimal('0.01'))
            
            # Calculate quantity and unit price
            qty = random.randint(3, 20)
            
            # Check stock availability
            if not self.simulator.inventory.check_stock_available(product['item_name'], qty):
                # Try smaller quantity
                qty = min(qty, self.simulator.inventory.get_available_quantity(product['item_name']))
                if qty < 1:
                    continue
            
            unit_price = (line_subtotal / qty).quantize(Decimal('0.01'))
            line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))
            
            # Deduct from inventory
            try:
                self.simulator.inventory.deduct_stock(product['item_name'], qty)
            except ValueError:
                continue
            
            line_items.append({
                'item_name': product['item_name'],
                'quantity': qty,
                'unit_price': unit_price,
                'line_subtotal': line_subtotal,
                'vat_amount': line_vat,
                'line_total': line_subtotal + line_vat
            })
            
            remaining -= line_subtotal
        
        return line_items