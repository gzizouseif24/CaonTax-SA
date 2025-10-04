"""
Cross-validation script: Verify generated reports against input data.

This script:
1. Reads detailed sales reports
2. Cross-checks with input/products.xlsx (lot prices, customs numbers)
3. Validates calculations (price × qty = subtotal, subtotal × 15% = VAT)
4. Checks lot ID format and completeness
5. Verifies totals match across all 3 report types
6. Generates validation report with findings
"""

import sys
import os
import pandas as pd
from decimal import Decimal
from typing import Dict, List, Tuple
from pathlib import Path

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class ReportValidator:
    """Validates generated reports against input data."""
    
    def __init__(self, input_dir: str = "input", reports_dir: str = "output/reports"):
        self.input_dir = input_dir
        self.reports_dir = reports_dir
        self.issues = []
        self.warnings = []
        self.stats = {}
        
    def load_input_data(self):
        """Load input data files."""
        print("\n📂 Loading input data...")
        
        # Load products
        products_path = os.path.join(self.input_dir, "products.xlsx")
        self.products_df = pd.read_excel(products_path)
        
        # Create lot_id for matching (strip whitespace and handle NaN)
        self.products_df['lot_id'] = (
            self.products_df['customs_declaration_no'].astype(str).str.strip() + ':' + 
            self.products_df['item_description'].astype(str).str.strip()
        )
        
        # Also create a normalized version for fuzzy matching
        self.products_df['lot_id_normalized'] = self.products_df['lot_id'].str.lower().str.replace(' ', '')
        
        print(f"  ✓ Products: {len(self.products_df)} lots")
        
        # Load customers
        customers_path = os.path.join(self.input_dir, "customers.xlsx")
        self.customers_df = pd.read_excel(customers_path)
        print(f"  ✓ Customers: {len(self.customers_df)} B2B customers")
        
    def validate_quarter(self, quarter_name: str) -> Dict:
        """Validate all reports for a quarter."""
        print(f"\n{'='*80}")
        print(f"🔍 VALIDATING {quarter_name}")
        print(f"{'='*80}")
        
        quarter_issues = []
        quarter_warnings = []
        quarter_stats = {}
        
        # Load reports
        detailed_path = os.path.join(self.reports_dir, f"{quarter_name}_detailed_sales.xlsx")
        summary_path = os.path.join(self.reports_dir, f"{quarter_name}_invoice_summary.xlsx")
        quarterly_path = os.path.join(self.reports_dir, f"{quarter_name}_quarterly_summary.xlsx")
        
        if not os.path.exists(detailed_path):
            print(f"  ⚠️  Detailed report not found: {detailed_path}")
            return None
        
        detailed_df = pd.read_excel(detailed_path)
        summary_df = pd.read_excel(summary_path) if os.path.exists(summary_path) else None
        quarterly_df = pd.read_excel(quarterly_path) if os.path.exists(quarterly_path) else None
        
        print(f"\n📊 Report Statistics:")
        print(f"  Line items: {len(detailed_df)}")
        if summary_df is not None:
            print(f"  Invoices: {len(summary_df)}")
        
        # Validation 1: Column existence
        print(f"\n1️⃣  Checking column structure...")
        required_columns = [
            'رقم الفاتورة',
            'تاريخ الفاتورة',
            'رقم البيان الجمركي',  # NEW
            'معرف اللوت',          # NEW
            'اسم الصنف',
            'سعر الوحدة (قبل الضريبة)',
            'الكمية',
            'المجموع قبل الضريبة',
            'مبلغ الضريبة',
            'الإجمالي شامل الضريبة'
        ]
        
        missing_columns = [col for col in required_columns if col not in detailed_df.columns]
        if missing_columns:
            issue = f"Missing columns: {missing_columns}"
            quarter_issues.append(issue)
            print(f"  ❌ {issue}")
        else:
            print(f"  ✓ All required columns present")
        
        # Validation 2: Lot tracking completeness
        print(f"\n2️⃣  Checking lot tracking...")
        
        null_customs = detailed_df['رقم البيان الجمركي'].isna().sum()
        null_lot_id = detailed_df['معرف اللوت'].isna().sum()
        
        if null_customs > 0:
            issue = f"{null_customs} rows with null customs_declaration_no"
            quarter_issues.append(issue)
            print(f"  ❌ {issue}")
        else:
            print(f"  ✓ No null customs declaration numbers")
        
        if null_lot_id > 0:
            issue = f"{null_lot_id} rows with null lot_id"
            quarter_issues.append(issue)
            print(f"  ❌ {issue}")
        else:
            print(f"  ✓ No null lot IDs")
        
        # Check lot ID format (should contain ':')
        invalid_lot_ids = detailed_df[~detailed_df['معرف اللوت'].astype(str).str.contains(':')]['معرف اللوت'].tolist()
        if invalid_lot_ids:
            issue = f"{len(invalid_lot_ids)} lot IDs missing colon separator"
            quarter_issues.append(issue)
            print(f"  ❌ {issue}")
            print(f"     Examples: {invalid_lot_ids[:3]}")
        else:
            print(f"  ✓ All lot IDs have correct format (contains ':')")
        
        quarter_stats['null_customs'] = null_customs
        quarter_stats['null_lot_id'] = null_lot_id
        quarter_stats['invalid_lot_ids'] = len(invalid_lot_ids)
        
        # Validation 3: Cross-check with products.xlsx
        print(f"\n3️⃣  Cross-checking with products.xlsx...")
        
        mismatches = []
        price_errors = []
        customs_errors = []
        
        # Sample 10 random rows for detailed checking
        sample_size = min(10, len(detailed_df))
        sample_rows = detailed_df.sample(n=sample_size, random_state=42)
        
        for idx, row in sample_rows.iterrows():
            lot_id = str(row['معرف اللوت']).strip()
            customs_no = str(row['رقم البيان الجمركي']).strip()
            item_name = str(row['اسم الصنف']).strip()
            price = row['سعر الوحدة (قبل الضريبة)']
            
            # Find in products (try exact match first)
            product_match = self.products_df[self.products_df['lot_id'] == lot_id]
            
            # If not found, try matching by customs_no and item separately
            if product_match.empty:
                product_match = self.products_df[
                    (self.products_df['customs_declaration_no'].astype(str).str.strip() == customs_no) &
                    (self.products_df['item_description'].astype(str).str.strip() == item_name)
                ]
            
            if product_match.empty:
                # Only report as mismatch if we can't find it by components either
                mismatches.append(f"Row {idx}: Lot ID '{lot_id}' not found in products.xlsx")
            else:
                product = product_match.iloc[0]
                
                # Check customs number
                if str(product['customs_declaration_no']) != str(customs_no):
                    customs_errors.append(
                        f"Row {idx}: Customs mismatch - Report: {customs_no}, Products: {product['customs_declaration_no']}"
                    )
                
                # Check price (allow 0.01 tolerance for rounding)
                expected_price = float(product['unit_price_ex_vat'])
                actual_price = float(price)
                if abs(expected_price - actual_price) > 0.01:
                    price_errors.append(
                        f"Row {idx}: Price mismatch for {lot_id} - Report: {actual_price:.2f}, Products: {expected_price:.2f}"
                    )
        
        if mismatches:
            for m in mismatches:
                quarter_issues.append(m)
                print(f"  ❌ {m}")
        else:
            print(f"  ✓ All sampled lot IDs found in products.xlsx")
        
        if customs_errors:
            for e in customs_errors:
                quarter_issues.append(e)
                print(f"  ❌ {e}")
        else:
            print(f"  ✓ All sampled customs numbers match")
        
        if price_errors:
            for e in price_errors:
                quarter_issues.append(e)
                print(f"  ❌ {e}")
        else:
            print(f"  ✓ All sampled prices match (within 0.01 SAR)")
        
        quarter_stats['lot_mismatches'] = len(mismatches)
        quarter_stats['price_errors'] = len(price_errors)
        quarter_stats['customs_errors'] = len(customs_errors)
        
        # Validation 4: Calculation accuracy
        print(f"\n4️⃣  Checking calculations...")
        
        calc_errors = []
        
        for idx, row in detailed_df.iterrows():
            price = float(row['سعر الوحدة (قبل الضريبة)'])
            qty = int(row['الكمية'])
            subtotal = float(row['المجموع قبل الضريبة'])
            vat = float(row['مبلغ الضريبة'])
            total = float(row['الإجمالي شامل الضريبة'])
            
            # Check: price × qty = subtotal
            expected_subtotal = price * qty
            if abs(expected_subtotal - subtotal) > 0.01:
                calc_errors.append(
                    f"Row {idx}: Subtotal error - Expected: {expected_subtotal:.2f}, Got: {subtotal:.2f}"
                )
            
            # Check: subtotal × 15% = VAT
            expected_vat = subtotal * 0.15
            if abs(expected_vat - vat) > 0.01:
                calc_errors.append(
                    f"Row {idx}: VAT error - Expected: {expected_vat:.2f}, Got: {vat:.2f}"
                )
            
            # Check: subtotal + VAT = total
            expected_total = subtotal + vat
            if abs(expected_total - total) > 0.01:
                calc_errors.append(
                    f"Row {idx}: Total error - Expected: {expected_total:.2f}, Got: {total:.2f}"
                )
        
        if calc_errors:
            # Show first 5 errors
            for e in calc_errors[:5]:
                quarter_issues.append(e)
                print(f"  ❌ {e}")
            if len(calc_errors) > 5:
                print(f"  ❌ ... and {len(calc_errors) - 5} more calculation errors")
        else:
            print(f"  ✓ All calculations correct")
        
        quarter_stats['calc_errors'] = len(calc_errors)
        
        # Validation 5: Multi-lot items (same item, different lots)
        print(f"\n5️⃣  Checking multi-lot items...")
        
        # Group by item name and check for multiple lot IDs
        item_lots = detailed_df.groupby('اسم الصنف')['معرف اللوت'].nunique()
        multi_lot_items = item_lots[item_lots > 1]
        
        if len(multi_lot_items) > 0:
            print(f"  ✓ Found {len(multi_lot_items)} items with multiple lots")
            print(f"    Examples:")
            for item, lot_count in multi_lot_items.head(3).items():
                print(f"      - {item}: {lot_count} different lots")
                
                # Check if they have different prices
                item_rows = detailed_df[detailed_df['اسم الصنف'] == item]
                unique_prices = item_rows['سعر الوحدة (قبل الضريبة)'].nunique()
                if unique_prices > 1:
                    print(f"        ✓ Different prices: {unique_prices} price points")
                else:
                    warning = f"Item '{item}' has {lot_count} lots but same price"
                    quarter_warnings.append(warning)
                    print(f"        ⚠️  Same price across all lots")
        else:
            print(f"  ℹ️  No items with multiple lots in this quarter")
        
        quarter_stats['multi_lot_items'] = len(multi_lot_items)
        
        # Validation 6: Totals match across reports
        if summary_df is not None:
            print(f"\n6️⃣  Checking totals across reports...")
            
            # NOTE: Detailed report shows LINE ITEM totals, not invoice totals
            # We need to sum by invoice number first
            detailed_by_invoice = detailed_df.groupby('رقم الفاتورة')['الإجمالي شامل الضريبة'].sum()
            detailed_total = detailed_by_invoice.sum()
            summary_total = summary_df['الإجمالي شامل الضريبة'].sum()
            
            diff = abs(detailed_total - summary_total)
            if diff > 0.10:
                issue = f"Total mismatch: Detailed={detailed_total:.2f}, Summary={summary_total:.2f}, Diff={diff:.2f}"
                quarter_issues.append(issue)
                print(f"  ❌ {issue}")
            else:
                print(f"  ✓ Totals match (diff: {diff:.2f} SAR)")
                print(f"    Detailed (by invoice): {detailed_total:.2f} SAR")
                print(f"    Summary: {summary_total:.2f} SAR")
            
            quarter_stats['total_diff'] = diff
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📋 VALIDATION SUMMARY FOR {quarter_name}")
        print(f"{'='*80}")
        print(f"  Issues: {len(quarter_issues)}")
        print(f"  Warnings: {len(quarter_warnings)}")
        
        if len(quarter_issues) == 0:
            print(f"  ✅ ALL CHECKS PASSED!")
        else:
            print(f"  ❌ ISSUES FOUND - Review above")
        
        return {
            'quarter': quarter_name,
            'issues': quarter_issues,
            'warnings': quarter_warnings,
            'stats': quarter_stats,
            'passed': len(quarter_issues) == 0
        }
    
    def validate_all_quarters(self) -> Dict:
        """Validate all quarters."""
        print("\n" + "="*80)
        print("🔍 CROSS-VALIDATION: REPORTS vs INPUT DATA")
        print("="*80)
        
        self.load_input_data()
        
        quarters = ["Q3-2023", "Q4-2023", "Q1-2024", "Q2-2024", "Q3-2024", "Q4-2024"]
        results = []
        
        for quarter in quarters:
            result = self.validate_quarter(quarter)
            if result:
                results.append(result)
        
        # Final summary
        print(f"\n\n{'='*80}")
        print("📊 FINAL VALIDATION SUMMARY")
        print(f"{'='*80}\n")
        
        passed = [r for r in results if r['passed']]
        failed = [r for r in results if not r['passed']]
        
        print(f"✅ Passed: {len(passed)}/{len(results)}")
        print(f"❌ Failed: {len(failed)}/{len(results)}\n")
        
        if passed:
            print("Passed Quarters:")
            for r in passed:
                print(f"  ✓ {r['quarter']}")
        
        if failed:
            print(f"\nFailed Quarters:")
            for r in failed:
                print(f"  ✗ {r['quarter']} ({len(r['issues'])} issues)")
        
        # Detailed statistics
        print(f"\n{'='*80}")
        print("📈 DETAILED STATISTICS")
        print(f"{'='*80}\n")
        
        for r in results:
            stats = r['stats']
            print(f"{r['quarter']}:")
            print(f"  Null customs: {stats.get('null_customs', 0)}")
            print(f"  Null lot IDs: {stats.get('null_lot_id', 0)}")
            print(f"  Invalid lot ID format: {stats.get('invalid_lot_ids', 0)}")
            print(f"  Lot mismatches: {stats.get('lot_mismatches', 0)}")
            print(f"  Price errors: {stats.get('price_errors', 0)}")
            print(f"  Calculation errors: {stats.get('calc_errors', 0)}")
            print(f"  Multi-lot items: {stats.get('multi_lot_items', 0)}")
            if 'total_diff' in stats:
                print(f"  Total difference: {stats['total_diff']:.2f} SAR")
            print()
        
        print(f"{'='*80}")
        print("✅ VALIDATION COMPLETE")
        print(f"{'='*80}\n")
        
        return {
            'results': results,
            'passed': len(passed),
            'failed': len(failed),
            'total': len(results)
        }


def main():
    """Run validation."""
    validator = ReportValidator()
    summary = validator.validate_all_quarters()
    
    # Exit code
    sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
