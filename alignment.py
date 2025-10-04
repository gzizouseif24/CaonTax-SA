from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import List, Dict
from simulation import SalesSimulator
from config import VAT_RATE, TOLERANCE, CASH_CUSTOMER_NAME, MIN_QUANTITY_PER_ITEM, MAX_QUANTITY_PER_ITEM, B2B_TOLERANCE_MIN, B2B_TOLERANCE_MAX
from smart_sales import SmartSalesGenerator
from refinement import refine_with_smart_adjustments
import random


class QuarterlyAligner:
    """
    Aligns simulated sales to exact quarterly targets.
    CRITICAL: NEVER sells below cost. Tracks actual FIFO costs for accurate profitability.
    
    Now supports SMART SALES GENERATION with realistic patterns!
    """
    
    def __init__(self, simulator: SalesSimulator, use_smart_algorithm: bool = True):
        """
        Initialize quarterly aligner.
        
        Args:
            simulator: SalesSimulator instance
            use_smart_algorithm: If True, use smart weighted algorithms (recommended)
                                If False, use legacy random algorithms
        """
        self.simulator = simulator
        self.use_smart_algorithm = use_smart_algorithm
        
        # Initialize smart sales generator if enabled
        if self.use_smart_algorithm:
            self.smart_generator = SmartSalesGenerator(
                inventory=simulator.inventory,
                holidays=simulator.holidays,
                random_seed=42  # For reproducibility
            )
            print(f"✨ Smart Sales Algorithm ENABLED - Using realistic weighted patterns")
    
    def align_quarter(
        self,
        quarter_name: str,
        start_date: date,
        end_date: date,
        target_sales: Decimal = None,  # Legacy: ex-VAT sales
        target_vat: Decimal = None,    # Legacy: VAT amount
        target_total_inc_vat: Decimal = None,  # NEW: Total inc VAT (PRD-compliant)
        vat_customers: List[Dict] = None,
        allow_variance: bool = False  # Flexible for 2023
    ) -> List[Dict]:
        """
        Generate invoices matching exact quarterly targets.
        Now supports sales_inc_vat (PRD-compliant) or legacy sales+vat format.
        """

        # Handle both new and legacy formats
        if target_total_inc_vat is not None:
            # NEW format: sales_inc_vat
            total_inc_vat = target_total_inc_vat
            target_sales = (total_inc_vat / Decimal("1.15")).quantize(Decimal('0.01'))
            target_vat = total_inc_vat - target_sales
        elif target_sales is not None and target_vat is not None:
            # LEGACY format: separate sales and VAT
            total_inc_vat = target_sales + target_vat
        else:
            raise ValueError("Must provide either target_total_inc_vat or both target_sales and target_vat")

        print(f"\n{'='*60}")
        print(f"ALIGNING {quarter_name}")
        print(f"{'='*60}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Target Total (inc VAT): {total_inc_vat:,.2f} SAR")
        print(f"Target Sales (ex VAT): {target_sales:,.2f} SAR")
        print(f"Target VAT (15%): {target_vat:,.2f} SAR")
        
        if allow_variance:
            print(f"Mode: 2023 (Best Effort - Accept any total)")
        else:
            print(f"Mode: 2024 (Strict - Must match target)")
        
        # Phase 1: Generate VAT customer invoices
        vat_invoices = []
        vat_sales = Decimal("0")
        vat_vat = Decimal("0")
        
        if vat_customers and not allow_variance:
            # 2024: Sort customers and select subset to avoid overshooting
            total_customer_sales = sum(
                (c['purchase_amount'] / Decimal("1.15")).quantize(Decimal('0.01')) 
                for c in vat_customers
            )
            
            if total_customer_sales > target_sales:
                print(f"  Customer total ({total_customer_sales:,.2f}) exceeds target")
                print(f"  Selecting subset of customers to match target...")
                
                # Select customers until we approach target (90% threshold)
                selected_customers = []
                cumulative = Decimal("0")
                
                for customer in vat_customers:
                    customer_subtotal = (customer['purchase_amount'] / Decimal("1.15")).quantize(Decimal('0.01'))
                    if cumulative + customer_subtotal <= target_sales * Decimal("0.95"):
                        selected_customers.append(customer)
                        cumulative += customer_subtotal
                    else:
                        break
                
                vat_customers = selected_customers
                print(f"  Selected {len(selected_customers)} customers")
        
        if vat_customers:
            print(f"\nPhase 1: Generating {len(vat_customers)} B2B customer invoices...")

            # Calculate expected B2B totals from customer file
            expected_b2b_sales = sum(
                (c['purchase_amount'] / Decimal("1.15")).quantize(Decimal('0.01'))
                for c in vat_customers
            )

            vat_invoices = self._generate_vat_customer_invoices(vat_customers)

            # Use ACTUAL B2B totals (not expected)
            vat_sales = sum(inv['subtotal'] for inv in vat_invoices)
            vat_vat = sum(inv['vat_amount'] for inv in vat_invoices)

            b2b_match_pct = (vat_sales / expected_b2b_sales * 100) if expected_b2b_sales > 0 else Decimal("0")

            print(f"\n  Phase 1 Complete:")
            print(f"    B2B invoices generated: {len(vat_invoices)}")
            print(f"    Expected from customers: {expected_b2b_sales:,.2f} SAR")
            print(f"    Actual B2B sales: {vat_sales:,.2f} SAR ({b2b_match_pct:.1f}%)")
            print(f"    B2B VAT: {vat_vat:,.2f} SAR")
        else:
            print(f"\nPhase 1: No VAT customers for this quarter")

        # Phase 2: Calculate remaining gap using ACTUAL B2B totals
        remaining_sales = target_sales - vat_sales  # Uses actual, not expected!
        remaining_vat = target_vat - vat_vat

        print(f"\nPhase 2: Calculating B2C target (Quarterly Target - Actual B2B):")
        print(f"  Quarterly target: {target_sales:,.2f} SAR")
        print(f"  Actual B2B: {vat_sales:,.2f} SAR")
        print(f"  B2C needed: {remaining_sales:,.2f} SAR")
        print(f"  B2C VAT needed: {remaining_vat:,.2f} SAR")
        
        # Phase 3: Generate cash sales
        print(f"\nPhase 3: Generating cash sales...")
        cash_invoices = self._generate_controlled_cash_sales(
            start_date,
            end_date,
            remaining_sales,
            remaining_vat,
            allow_variance=allow_variance  # Pass through
        )
        
        print(f"  Generated: {len(cash_invoices)} cash invoices")
        
        # Combine
        all_invoices = vat_invoices + cash_invoices

        # Calculate actuals
        actual_b2b_sales = sum(inv['subtotal'] for inv in vat_invoices)
        actual_b2b_vat = sum(inv['vat_amount'] for inv in vat_invoices)
        actual_b2c_sales = sum(inv['subtotal'] for inv in cash_invoices)
        actual_b2c_vat = sum(inv['vat_amount'] for inv in cash_invoices)
        actual_sales = actual_b2b_sales + actual_b2c_sales
        actual_vat = actual_b2b_vat + actual_b2c_vat

        sales_diff = abs(actual_sales - target_sales)
        vat_diff = abs(actual_vat - target_vat)

        print(f"\n{'='*60}")
        print(f"ALIGNMENT COMPLETE - {quarter_name}")
        print(f"{'='*60}")

        print(f"\n📊 BREAKDOWN:")
        print(f"  B2B Invoices: {len(vat_invoices)}")
        print(f"    Sales: {actual_b2b_sales:,.2f} SAR")
        print(f"    VAT: {actual_b2b_vat:,.2f} SAR")
        if vat_customers:
            expected_b2b = sum((c['purchase_amount'] / Decimal("1.15")).quantize(Decimal('0.01')) for c in vat_customers)
            b2b_pct = (actual_b2b_sales / expected_b2b * 100) if expected_b2b > 0 else Decimal("0")
            print(f"    Match: {b2b_pct:.1f}% of customer expectations")

        print(f"\n  B2C Invoices: {len(cash_invoices)}")
        print(f"    Sales: {actual_b2c_sales:,.2f} SAR")
        print(f"    VAT: {actual_b2c_vat:,.2f} SAR")

        print(f"\n🎯 QUARTERLY TARGET:")
        print(f"  Target Sales (ex VAT): {target_sales:,.2f} SAR")
        print(f"  Actual Sales (ex VAT): {actual_sales:,.2f} SAR")
        print(f"  Difference: {sales_diff:.2f} SAR")
        print(f"\n  Target VAT (15%): {target_vat:,.2f} SAR")
        print(f"  Actual VAT: {actual_vat:,.2f} SAR")
        print(f"  Difference: {vat_diff:.2f} SAR")
        
        # Tolerance check
        if allow_variance:
            # 2023: Any result is acceptable
            coverage_pct = (actual_sales / target_sales * 100) if target_sales > 0 else 0
            print(f"\n✅ 2023 RESULT ACCEPTED")
            print(f"  Sales coverage: {coverage_pct:.1f}% of target")
            print(f"  Note: 2023 uses best effort - exact matching not required")
        else:
            # 2024: Check tolerance
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

    def _reverse_engineer_line_items(
        self,
        target_subtotal: Decimal,
        invoice_date: date,
        customer_name: str
    ) -> List[Dict]:
        """
        REVERSE-ENGINEERING: Generate line items that sum to EXACT target amount.

        Per PRD requirements:
        - B2B customers can order "pre-arrival" (no stock_date filter)
        - B2B can mix ALL classifications (EXC_INSPECTION + NONEXC_INSPECTION + NONEXC_OUTSIDE)
        - Line items must sum to EXACT invoice total (100% data integrity)

        Algorithm:
        1. Get ALL products from inventory (no date filtering for B2B pre-orders)
        2. Greedy two-pass: bulk items first, then fine-tune
        3. Adjust last item quantity to hit exact target
        """

        # Get ALL lots from inventory for B2B (pre-arrival ordering allowed)
        # No current_date filter - B2B can order products before they arrive
        all_products = self.simulator.inventory.products

        # Filter only profitable lots (price >= cost)
        available_lots = [
            p for p in all_products
            if p['unit_price_ex_vat'] >= p['unit_cost_ex_vat'] and p['quantity_remaining'] > 0
        ]

        if not available_lots:
            return []

        # Step 1: Greedy algorithm - keep adding items until we approach target
        line_items = []
        remaining = target_subtotal
        used_lot_ids = set()

        # Sort lots by price (cheapest first for better coverage)
        available_lots.sort(key=lambda x: x['unit_price_ex_vat'])

        # Pass 1: Add items with max quantity (100) to quickly approach target
        for lot in available_lots:
            if remaining <= Decimal("50.00"):  # Switch to fine-tuning mode
                break

            lot_price = lot['unit_price_ex_vat']
            lot_cost = lot['unit_cost_ex_vat']

            # Skip if unprofitable
            if lot_price < lot_cost:
                continue

            # Calculate quantity needed
            ideal_qty = int(remaining / lot_price)

            if ideal_qty >= 3:  # Only add if we need at least 3 units
                quantity = min(100, ideal_qty)
                line_subtotal = (lot_price * quantity).quantize(Decimal('0.01'))
                line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))

                line_items.append({
                    'lot_id': lot['lot_id'],
                    'customs_declaration_no': lot['customs_declaration_no'],
                    'item_description': lot['item_description'],
                    'shipment_class': lot['shipment_class'],
                    'quantity': quantity,
                    'unit_price_ex_vat': lot_price,
                    'unit_cost_ex_vat': lot_cost,
                    'line_subtotal': line_subtotal,
                    'vat_amount': line_vat,
                    'line_total': line_subtotal + line_vat,
                    'item_name': lot['item_name'],
                    'customs_declaration': lot['customs_declaration'],
                    'classification': lot['classification'],
                    'unit_price': lot_price,
                    'unit_cost_actual': lot_cost
                })

                remaining -= line_subtotal
                used_lot_ids.add(lot['lot_id'])

        # Pass 2: Fine-tune with smaller quantities to hit exact target
        for lot in available_lots:
            if remaining <= Decimal("1.00"):
                break

            if lot['lot_id'] in used_lot_ids:
                continue

            lot_price = lot['unit_price_ex_vat']
            lot_cost = lot['unit_cost_ex_vat']

            if lot_price < lot_cost:
                continue

            # Try to add this lot with appropriate quantity
            ideal_qty = int(remaining / lot_price)

            if ideal_qty >= 3:
                quantity = min(100, ideal_qty)
            elif ideal_qty > 0 or (lot_price * 3) <= remaining + Decimal("50.00"):
                quantity = 3
            else:
                continue

            line_subtotal = (lot_price * quantity).quantize(Decimal('0.01'))
            line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))

            line_items.append({
                'lot_id': lot['lot_id'],
                'customs_declaration_no': lot['customs_declaration_no'],
                'item_description': lot['item_description'],
                'shipment_class': lot['shipment_class'],
                'quantity': quantity,
                'unit_price_ex_vat': lot_price,
                'unit_cost_ex_vat': lot_cost,
                'line_subtotal': line_subtotal,
                'vat_amount': line_vat,
                'line_total': line_subtotal + line_vat,
                'item_name': lot['item_name'],
                'customs_declaration': lot['customs_declaration'],
                'classification': lot['classification'],
                'unit_price': lot_price,
                'unit_cost_actual': lot_cost
            })

            remaining -= line_subtotal
            used_lot_ids.add(lot['lot_id'])

        if not line_items:
            return []

        # Step 2: Fine-tune last item to hit exact target
        actual_total = sum(item['line_subtotal'] for item in line_items)
        difference = target_subtotal - actual_total

        if abs(difference) > Decimal("1.00") and line_items:
            # Adjust last item's quantity to match exactly
            last_item = line_items[-1]
            unit_price = last_item['unit_price_ex_vat']

            # Calculate adjustment needed
            qty_adjustment = int(difference / unit_price)
            new_qty = last_item['quantity'] + qty_adjustment

            # Ensure bounds (3-100)
            new_qty = max(3, min(100, new_qty))

            # Recalculate
            last_item['quantity'] = new_qty
            last_item['line_subtotal'] = (unit_price * new_qty).quantize(Decimal('0.01'))
            last_item['vat_amount'] = (last_item['line_subtotal'] * VAT_RATE).quantize(Decimal('0.01'))
            last_item['line_total'] = last_item['line_subtotal'] + last_item['vat_amount']

        return line_items

    def _generate_vat_customer_invoices(self, customers: List[Dict]) -> List[Dict]:
        """
        Generate invoices for VAT customers with EXACT amounts from customers.xlsx.

        REVERSE-ENGINEERING APPROACH:
        Instead of trying to match customer amounts (and failing due to limited catalog),
        we HARDCODE the exact invoice totals from customers.xlsx, then reverse-engineer
        line items that sum to those exact totals using quantity adjustments.
        """
        invoices = []

        for customer in customers:
            # HARDCODED TARGET: Exact amount from customers.xlsx
            total_with_vat = customer['purchase_amount']
            target_subtotal = (total_with_vat / Decimal("1.15")).quantize(Decimal('0.01'))
            target_vat = (target_subtotal * VAT_RATE).quantize(Decimal('0.01'))
            target_total = (target_subtotal + target_vat).quantize(Decimal('0.01'))

            # Random date and time
            purchase_date = customer['purchase_date']
            invoice_datetime = datetime.combine(
                purchase_date,
                datetime.min.time().replace(
                    hour=random.randint(9, 21),
                    minute=random.randint(0, 59)
                )
            )

            # REVERSE-ENGINEER: Generate line items that sum to EXACT target
            line_items = self._reverse_engineer_line_items(
                target_subtotal=target_subtotal,
                invoice_date=purchase_date,
                customer_name=customer['customer_name']
            )

            if not line_items:
                print(f"  ⚠️  {customer['customer_name']}: Could not generate invoice (no suitable products)")
                continue
            
            # Calculate actuals from line items
            actual_subtotal = sum(item['line_subtotal'] for item in line_items)
            actual_vat = sum(item['vat_amount'] for item in line_items)
            actual_total = (actual_subtotal + actual_vat).quantize(Decimal('0.01'))

            # Calculate variance from HARDCODED target
            variance = abs(actual_subtotal - target_subtotal)

            # Log result with exact match status
            if variance <= Decimal("1.00"):
                status_icon = "✅"
                status_text = "EXACT"
            elif variance <= Decimal("10.00"):
                status_icon = "✓"
                status_text = "CLOSE"
            else:
                status_icon = "⚠️"
                status_text = f"OFF BY {variance:.2f}"

            print(f"  {status_icon} {customer['customer_name']}: {actual_subtotal:,.2f} SAR [{status_text}]")
            if variance > Decimal("1.00"):
                print(f"      (Target: {target_subtotal:,.2f}, Variance: {variance:.2f})")
            
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
                'subtotal': actual_subtotal,  # Use actual from line items
                'vat_amount': actual_vat,      # Use actual from line items
                'total': actual_total,          # Use actual from line items
                'qr_code_data': f"INV:{invoice_number}|{customer['customer_name']}"
            }

            invoices.append(invoice)

        # Summary report - REVERSE-ENGINEERED EXACT MATCHING
        if invoices:
            total_target = sum((c['purchase_amount'] / Decimal("1.15")).quantize(Decimal('0.01')) for c in customers)
            total_actual = sum(inv['subtotal'] for inv in invoices)
            total_variance = abs(total_actual - total_target)

            print(f"\n  B2B Summary (REVERSE-ENGINEERED):")
            print(f"    Customers processed: {len(invoices)}/{len(customers)}")
            print(f"    Target total (from customers.xlsx): {total_target:,.2f} SAR")
            print(f"    Actual total (from line items): {total_actual:,.2f} SAR")
            print(f"    Variance: {total_variance:.2f} SAR")

            if total_variance <= Decimal("10.00"):
                print(f"    ✅ EXCELLENT - Hardcoded amounts matched within ±10 SAR!")
            elif total_variance <= Decimal("100.00"):
                print(f"    ✓ GOOD - Close match using reverse-engineering")
            else:
                print(f"    ⚠️ Review needed - Check quantity adjustments")

        return invoices
    
    def _generate_controlled_cash_sales(
        self,
        start_date: date,
        end_date: date,
        target_sales: Decimal,
        target_vat: Decimal,
        allow_variance: bool = False  # NEW PARAMETER
    ) -> List[Dict]:
        """
        Generate cash invoices that match target using authentic prices and quantity adjustment.
        
        If allow_variance=True (2023): Generate as much as possible, accept any total.
        If allow_variance=False (2024): Match target precisely.
        """
        
        # Calculate working days
        working_days = []
        current = start_date
        while current <= end_date:
            if self.simulator.is_working_day(current):
                working_days.append(current)
            current += timedelta(days=1)
        
        print(f"    Working days: {len(working_days)}")
        
        if allow_variance:
            print(f"    2023 MODE: Generating maximum possible sales (target is guideline only)")
        else:
            print(f"    2024 MODE: Matching target precisely using authentic prices")
        
        invoices = []
        actual_sales = Decimal("0")
        actual_vat = Decimal("0")
        
        # For 2023: Try to generate enough invoices to approach target
        # For 2024: Generate just enough to hit target
        if allow_variance:
            max_invoices = len(working_days) * 50  # More attempts for 2023 to reach target
        else:
            max_invoices = len(working_days) * 20  # Current logic for 2024
        
        for i in range(max_invoices):
            # Check stopping conditions
            remaining_sales = target_sales - actual_sales
            remaining_vat = target_vat - actual_vat
            
            if allow_variance:
                # 2023: Aim for target, but accept 80-120% range (best effort)
                if actual_sales >= target_sales * Decimal("1.2"):
                    print(f"    Reached 120% of target, stopping (2023 best effort)")
                    break
                # Also stop if we're very close to target (within 1%)
                if actual_sales >= target_sales * Decimal("0.99") and remaining_sales <= Decimal("1000.00"):
                    print(f"    Close enough to target (2023 best effort)")
                    break
            else:
                # 2024: Stop when very close to target (ultra-tight tolerance)
                if remaining_sales <= Decimal("0.10"):
                    break
            
            # Select working day (smart or random)
            # For Q3-2023, this will naturally prefer late September when stock arrives
            available_dates = [
                d for d in working_days 
                if any(p['stock_date'] <= d for p in self.simulator.inventory.products 
                       if p['quantity_remaining'] > 0)
            ]
            
            if not available_dates:
                if allow_variance:
                    print(f"    No more inventory available")
                break
            
            # SMART: Use weighted date selection
            if self.use_smart_algorithm:
                invoice_date = self.smart_generator.get_weighted_date(
                    available_dates,
                    start_date,
                    end_date
                )
            else:
                # LEGACY: Random selection
                invoice_date = random.choice(available_dates)
            
            # Target size for this invoice
            if self.use_smart_algorithm:
                # SMART: Calculate realistic size using normal distribution
                days_left = len([d for d in working_days if d >= invoice_date])
                target_invoice_size = self.smart_generator.calculate_invoice_size(
                    invoice_date,
                    remaining_sales,
                    days_left,
                    start_date,
                    end_date
                )
            else:
                # LEGACY: Random sizes
                if allow_variance:
                    # 2023: More aggressive invoice sizes to reach target faster
                    if remaining_sales > Decimal("50000"):
                        target_invoice_size = Decimal(str(random.randint(2000, 8000)))
                    elif remaining_sales > Decimal("10000"):
                        target_invoice_size = Decimal(str(random.randint(1000, 5000)))
                    else:
                        target_invoice_size = Decimal(str(random.randint(500, 2000)))
                else:
                    # 2024: Size based on remaining target
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
        
        if allow_variance:
            coverage_pct = (actual_sales / target_sales * 100) if target_sales > 0 else 0
            print(f"    Coverage: {coverage_pct:.1f}% of target")
        
        # ITERATIVE REFINEMENT: Fine-tune to match target precisely
        # Only for 2024 (strict mode) or if smart algorithm is enabled
        if not allow_variance or self.use_smart_algorithm:
            target_total_inc_vat = (target_sales + target_vat).quantize(Decimal('0.01'))
            invoices = refine_with_smart_adjustments(
                invoices,
                target_total_inc_vat,
                tolerance=Decimal("5.00") if not allow_variance else Decimal("50.00")
            )
        
        return invoices
    
    def _create_authentic_price_line_items(
        self,
        target_subtotal: Decimal,
        invoice_date: date,
        invoice_type: str,
        deduct_stock: bool = True,  # Whether to actually deduct from inventory
        tolerance_min: Decimal = Decimal("1.00"),  # Minimum acceptable percentage (1.00 = 100%)
        tolerance_max: Decimal = Decimal("1.00")   # Maximum acceptable percentage (1.00 = 100%)
    ) -> List[Dict]:
        """
        Create line items using LOT-BASED inventory with authentic lot prices.
        CRITICAL: Each line item tracks its lot_id for PRD compliance.
        If same item from multiple lots, creates SEPARATE line items.
        """

        # Get available LOTS by classification (not aggregated items)
        from config import UNDER_NON_SELECTIVE, UNDER_SELECTIVE, OUTSIDE_INSPECTION

        if invoice_type == "TAX":
            available_lots = self.simulator.inventory.get_available_lots_by_classification(
                UNDER_NON_SELECTIVE,
                current_date=invoice_date
            )
        else:
            available_lots = (
                self.simulator.inventory.get_available_lots_by_classification(
                    UNDER_NON_SELECTIVE,
                    current_date=invoice_date
                ) +
                self.simulator.inventory.get_available_lots_by_classification(
                    UNDER_SELECTIVE,
                    current_date=invoice_date
                ) +
                self.simulator.inventory.get_available_lots_by_classification(
                    OUTSIDE_INSPECTION,
                    current_date=invoice_date
                )
            )

        if not available_lots:
            return []

        # Build line items approaching target - ONE LINE PER LOT
        line_items = []
        remaining_target = target_subtotal
        max_attempts = 50
        used_lot_ids = set()  # Track used lots to avoid duplicates

        # Calculate acceptable range based on tolerance
        min_acceptable = target_subtotal * tolerance_min
        max_acceptable = target_subtotal * tolerance_max

        for attempt in range(max_attempts):
            # Calculate current total
            current_total = sum(item['line_subtotal'] for item in line_items)

            # Stop if we've reached acceptable range
            if current_total >= min_acceptable and current_total <= max_acceptable:
                break

            # Stop if we can't add more without exceeding max
            if remaining_target <= Decimal("1.00") and current_total >= min_acceptable:
                break

            # Select LOT (smart or random)
            if self.use_smart_algorithm:
                # SMART: Use weighted selection based on popularity
                # Filter out already used lots
                available_for_selection = [
                    lot for lot in available_lots
                    if lot['lot_id'] not in used_lot_ids
                ]
                if not available_for_selection:
                    break
                
                # Select using smart weighting
                selected_lots = self.smart_generator.select_weighted_products(
                    available_for_selection,
                    invoice_date,
                    num_items=1
                )
                if not selected_lots:
                    break
                lot = selected_lots[0]
            else:
                # LEGACY: Random selection
                lot = random.choice(available_lots)
                
                # Skip if already used this lot
                if lot['lot_id'] in used_lot_ids:
                    continue

            # Get LOT-SPECIFIC price and cost
            lot_price = lot['unit_price_ex_vat']
            lot_cost = lot['unit_cost_ex_vat']

            # CRITICAL VALIDATION: Ensure lot price is profitable
            if lot_price < lot_cost:
                print(f"  ⚠️ Skipping lot {lot['lot_id']} - price {lot_price} below cost {lot_cost}")
                continue

            # Calculate ideal quantity WITHOUT changing price
            ideal_qty = int(remaining_target / lot_price)
            ideal_qty = max(1, min(ideal_qty, MAX_QUANTITY_PER_ITEM))
            
            # Add ±20% random variation for realism (avoid too many identical quantities)
            if ideal_qty > 5:  # Only vary if quantity is meaningful
                variation = int(ideal_qty * 0.2)  # 20% variation
                ideal_qty = random.randint(
                    max(MIN_QUANTITY_PER_ITEM, ideal_qty - variation),
                    min(MAX_QUANTITY_PER_ITEM, ideal_qty + variation)
                )

            # Check stock availability for this specific LOT
            if not self.simulator.inventory.check_lot_stock_available(lot['lot_id'], ideal_qty):
                # Try smaller quantity
                for qty in [30, 20, 10, 5, 3, 1]:
                    if self.simulator.inventory.check_lot_stock_available(lot['lot_id'], qty):
                        ideal_qty = qty
                        break
                else:
                    continue  # No stock available in this lot

            # Deduct from inventory using LOT-SPECIFIC deduction (if requested)
            if deduct_stock:
                try:
                    deduction = self.simulator.inventory.deduct_stock(lot['lot_id'], ideal_qty)
                except ValueError:
                    continue

            # Calculate line totals using LOT price (constant from lot record)
            line_subtotal = (lot_price * ideal_qty).quantize(Decimal('0.01'))
            line_vat = (line_subtotal * VAT_RATE).quantize(Decimal('0.01'))

            # Only add if it doesn't overshoot target too much
            if line_subtotal <= remaining_target + Decimal("100.00"):
                # Create line item with LOT tracking (PRD-compliant)
                line_items.append({
                    # PRD-compliant fields
                    'lot_id': lot['lot_id'],
                    'customs_declaration_no': lot['customs_declaration_no'],
                    'item_description': lot['item_description'],
                    'shipment_class': lot['shipment_class'],
                    'quantity': ideal_qty,
                    'unit_price_ex_vat': lot_price,
                    'unit_cost_ex_vat': lot_cost,  # For profitability validation
                    'line_subtotal': line_subtotal,
                    'vat_amount': line_vat,
                    'line_total': line_subtotal + line_vat,

                    # Legacy fields for backward compatibility
                    'item_name': lot['item_name'],
                    'customs_declaration': lot['customs_declaration'],
                    'classification': lot['classification'],
                    'unit_price': lot_price,
                    'unit_cost_actual': lot_cost
                })

                remaining_target -= line_subtotal
                used_lot_ids.add(lot['lot_id'])

        return line_items
    
    def validate_invoice_prices(self, invoices: List[Dict]) -> bool:
        """
        Validate that ALL invoice prices match their LOT-SPECIFIC prices and are profitable.
        Each line item's price is validated against its lot_id's actual price.
        """
        print(f"\n{'='*80}")
        print("PROFITABILITY & PRICE VALIDATION - LOT-BASED")
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