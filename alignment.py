from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Dict
from simulation import SalesSimulator
from config import VAT_RATE, TOLERANCE, CASH_CUSTOMER_NAME
import random


class QuarterlyAligner:
    """
    Aligns simulated sales to exact quarterly targets.
    CRITICAL: NEVER sells below cost. Tracks actual FIFO costs for accurate profitability.
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
        
        # Phase 3: Generate cash sales
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
        
        # Tolerance check
        tolerance = Decimal("5.00")
        
        if sales_diff < tolerance and vat_diff < tolerance:
            print(f"\n✅ EXCELLENT MATCH - Targets achieved with authentic pricing")
            print(f"  Sales difference: {sales_diff:.2f} SAR")
            print(f"  VAT difference: {vat_diff:.2f} SAR")
        else:
            print(f"\n⚠️ TARGET VARIANCE - Authentic pricing maintained, some variance exists")
            print(f"  Sales difference: {sales_diff:.2f} SAR")
            print(f"  VAT difference: {vat_diff:.2f} SAR")
            print(f"  Note: This is acceptable - NEVER selling below cost takes priority")
        
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
            
            # Create line items using authentic prices ONLY
            line_items = self._create_authentic_price_line_items(
                subtotal,
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
                'customer_tax_number': tax_number,
                'customer_address': address,
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
        """Generate cash invoices that match target using authentic prices and quantity adjustment."""
        
        # Calculate working days
        working_days = []
        current = start_date
        while current <= end_date:
            if self.simulator.is_working_day(current):
                working_days.append(current)
            current += timedelta(days=1)
        
        print(f"    Working days: {len(working_days)}")
        print(f"    Using ONLY authentic Excel prices - adjusting quantities to hit targets")
        
        invoices = []
        actual_sales = Decimal("0")
        actual_vat = Decimal("0")
        
        # Generate invoices until we hit the target
        max_invoices = len(working_days) * 20
        
        for i in range(max_invoices):
            # Stop if we're close to target
            remaining_sales = target_sales - actual_sales
            remaining_vat = target_vat - actual_vat
            
            if remaining_sales <= Decimal("1.00"):
                break
            
            # Select random working day
            invoice_date = random.choice(working_days)
            
            # Target size for this invoice
            target_invoice_size = min(remaining_sales, Decimal("3000.00"))
            
            # Create invoice using authentic prices ONLY
            line_items = self._create_authentic_price_line_items(
                target_invoice_size,
                invoice_date,
                invoice_type="SIMPLIFIED"
            )
            
            if not line_items:
                continue
            
            # Calculate actual totals from line items
            invoice_subtotal = sum(item['line_subtotal'] for item in line_items)
            invoice_vat = sum(item['vat_amount'] for item in line_items)
            
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
            actual_sales += invoice_subtotal
            actual_vat += invoice_vat
        
        print(f"    Generated: {len(invoices)} invoices")
        print(f"    Actual sales: {actual_sales:,.2f} SAR (Target: {target_sales:,.2f})")
        print(f"    Actual VAT: {actual_vat:,.2f} SAR (Target: {target_vat:,.2f})")
        
        return invoices
    
    def _create_authentic_price_line_items(
        self,
        target_subtotal: Decimal,
        invoice_date: date,
        invoice_type: str
    ) -> List[Dict]:
        """
        Create line items using ONLY authentic Excel prices.
        NOW TRACKS ACTUAL FIFO COSTS for accurate profitability validation.
        """
        
        # Get available items by classification
        from config import UNDER_NON_SELECTIVE, UNDER_SELECTIVE, OUTSIDE_INSPECTION
        
        if invoice_type == "TAX":
            available = self.simulator.inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE)
        else:
            available = (
                self.simulator.inventory.get_available_items_by_classification(UNDER_NON_SELECTIVE) +
                self.simulator.inventory.get_available_items_by_classification(UNDER_SELECTIVE) +
                self.simulator.inventory.get_available_items_by_classification(OUTSIDE_INSPECTION)
            )
        
        # Filter by stock date
        available = [item for item in available if item['stock_date'] <= invoice_date]
        
        if not available:
            return []
        
        # Build line items approaching target
        line_items = []
        remaining_target = target_subtotal
        max_attempts = 50
        
        for attempt in range(max_attempts):
            if remaining_target <= Decimal("1.00"):
                break
            
            # Select random product
            product = random.choice(available)
            
            # Get AUTHENTIC price from Excel
            authentic_price = product['unit_price_before_vat']
            
            # Calculate ideal quantity WITHOUT changing price
            ideal_qty = int(remaining_target / authentic_price)
            ideal_qty = max(1, min(ideal_qty, 40))
            
            # Check stock availability
            available_qty = self.simulator.inventory.get_available_quantity(product['item_name'])
            
            if available_qty < 1:
                continue
            
            # Use minimum of ideal and available
            qty = min(ideal_qty, available_qty)
            
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
                
                remaining_target -= line_subtotal
        
        return line_items
    
    def validate_invoice_prices(self, invoices: List[Dict]) -> bool:
        """
        Validate that ALL invoice prices are profitable using ACTUAL FIFO costs.
        NOW USES STORED COSTS for accurate validation.
        """
        print(f"\n{'='*80}")
        print("PROFITABILITY VALIDATION - USING ACTUAL FIFO COSTS")
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
                
                # Calculate totals
                line_revenue = unit_price * quantity
                line_cost = unit_cost * quantity
                
                total_revenue += line_revenue
                total_cost += line_cost
                
                # Check if selling below ACTUAL cost
                if unit_price < unit_cost:
                    loss_sales.append({
                        'invoice': invoice['invoice_number'],
                        'item': line_item['item_name'],
                        'selling_price': float(unit_price),
                        'actual_cost': float(unit_cost),
                        'loss': float(unit_cost - unit_price),
                        'loss_pct': float((unit_cost - unit_price) / unit_cost * 100)
                    })
        
        # Calculate profitability
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"\n📊 Financial Summary:")
        print(f"  Total line items: {total_items}")
        print(f"  Total revenue: {float(total_revenue):,.2f} SAR")
        print(f"  Total cost (FIFO actual): {float(total_cost):,.2f} SAR")
        print(f"  Gross profit: {float(gross_profit):,.2f} SAR")
        print(f"  Profit margin: {float(profit_margin):.2f}%")
        
        if len(loss_sales) == 0:
            print(f"\n✅ PERFECT! NO LOSS SALES!")
            print(f"All {total_items} items sold profitably using actual FIFO costs!")
            return True
        else:
            print(f"\n❌ CRITICAL: FOUND {len(loss_sales)} LOSS SALES")
            
            # Show worst cases
            loss_sales.sort(key=lambda x: x['loss_pct'], reverse=True)
            print(f"\nWorst loss sales:")
            for i, loss in enumerate(loss_sales[:10]):
                print(f"  {i+1}. {loss['item']}")
                print(f"     Sold at: {loss['selling_price']:.2f} SAR")
                print(f"     Actual cost: {loss['actual_cost']:.2f} SAR")
                print(f"     Loss: {loss['loss']:.2f} SAR ({loss['loss_pct']:.1f}%)")
            
            return False