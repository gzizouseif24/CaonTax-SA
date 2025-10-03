import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict
import os


class ReportGenerator:
    """
    Generates Excel reports from invoice data.
    
    Per BRD Section 4:
    1. Detailed Sales Report - All line items
    2. Invoice Summary Report - One row per invoice
    3. Quarterly Summary Report - Targets vs Actuals
    """
    
    def __init__(self, output_dir: str = "output/reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _save_excel_with_error_handling(self, df: pd.DataFrame, filename: str) -> str:
        """Save DataFrame to Excel with error handling for file locks."""
        output_path = os.path.join(self.output_dir, filename)
        try:
            df.to_excel(output_path, index=False, engine='openpyxl')
            return output_path
        except PermissionError:
            print(f"⚠️  Cannot write to {output_path} - file may be open in Excel")
            print(f"   Please close Excel and try again")
            # Try alternative filename
            alt_filename = filename.replace('.xlsx', f'_new.xlsx')
            alt_path = os.path.join(self.output_dir, alt_filename)
            df.to_excel(alt_path, index=False, engine='openpyxl')
            print(f"   Saved as alternative: {alt_path}")
            return alt_path
    
    def generate_detailed_sales_report(
        self,
        invoices: List[Dict],
        output_filename: str
    ) -> str:
        """
        Generate detailed sales report (one row per line item).
        
        Per BRD: Columns should be:
        - Invoice Number
        - Invoice Date
        - Item Name
        - Unit Price (before VAT)
        - Quantity
        - Subtotal (before VAT)
        - VAT Amount
        - Total (with VAT)
        
        Args:
            invoices: List of invoice dictionaries
            output_filename: Filename for the report
            
        Returns:
            Path to generated file
        """
        rows = []
        
        for invoice in invoices:
            invoice_number = invoice['invoice_number']
            invoice_date = invoice['invoice_date']
            
            # Format date
            if isinstance(invoice_date, datetime):
                formatted_date = invoice_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_date = str(invoice_date)
            
            # Add row for each line item
            for item in invoice['line_items']:
                row = {
                    'رقم الفاتورة': invoice_number,
                    'تاريخ الفاتورة': formatted_date,
                    'اسم الصنف': item['item_name'],
                    'سعر الوحدة (قبل الضريبة)': float(item['unit_price']),
                    'الكمية': item['quantity'],
                    'المجموع قبل الضريبة': float(item['line_subtotal']),
                    'مبلغ الضريبة': float(item['vat_amount']),
                    'الإجمالي شامل الضريبة': float(item['line_total'])
                }
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Save to Excel
        output_path = self._save_excel_with_error_handling(df, output_filename)
        
        print(f"✓ Detailed sales report: {output_path}")
        print(f"  Total line items: {len(rows)}")
        
        return output_path
    
    def generate_invoice_summary_report(
        self,
        invoices: List[Dict],
        output_filename: str
    ) -> str:
        """
        Generate invoice summary report (one row per invoice).
        
        Per BRD: Columns should be:
        - Invoice Number
        - Invoice Date
        - Subtotal (before VAT)
        - VAT Amount
        - Total (with VAT)
        
        Args:
            invoices: List of invoice dictionaries
            output_filename: Filename for the report
            
        Returns:
            Path to generated file
        """
        rows = []
        
        for invoice in invoices:
            # Format date
            invoice_date = invoice['invoice_date']
            if isinstance(invoice_date, datetime):
                formatted_date = invoice_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_date = str(invoice_date)
            
            row = {
                'رقم الفاتورة': invoice['invoice_number'],
                'تاريخ الفاتورة': formatted_date,
                'نوع الفاتورة': invoice['invoice_type'],
                'اسم العميل': invoice['customer_name'],
                'المجموع قبل الضريبة': float(invoice['subtotal']),
                'مبلغ الضريبة': float(invoice['vat_amount']),
                'الإجمالي شامل الضريبة': float(invoice['total'])
            }
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Save to Excel
        output_path = self._save_excel_with_error_handling(df, output_filename)
        
        print(f"✓ Invoice summary report: {output_path}")
        print(f"  Total invoices: {len(rows)}")
        
        return output_path
    
    def generate_quarterly_summary_report(
        self,
        quarter_name: str,
        target_sales: Decimal,
        target_vat: Decimal,
        actual_sales: Decimal,
        actual_vat: Decimal,
        invoices: List[Dict],
        output_filename: str
    ) -> str:
        """
        Generate quarterly summary report comparing targets vs actuals.
        
        Args:
            quarter_name: Name of quarter (e.g. "Q3-2023")
            target_sales: Target sales before VAT
            target_vat: Target VAT amount
            actual_sales: Actual sales before VAT
            actual_vat: Actual VAT amount
            invoices: List of invoice dictionaries
            output_filename: Filename for the report
            
        Returns:
            Path to generated file
        """
        # Count invoice types
        tax_count = len([inv for inv in invoices if inv['invoice_type'] == 'TAX'])
        simplified_count = len([inv for inv in invoices if inv['invoice_type'] == 'SIMPLIFIED'])
        
        # Calculate differences
        sales_diff = actual_sales - target_sales
        vat_diff = actual_vat - target_vat
        total_target = target_sales + target_vat
        total_actual = actual_sales + actual_vat
        total_diff = total_actual - total_target
        
        # Create summary data
        data = {
            'البيان': [
                'الربع',
                'عدد الفواتير الإجمالي',
                'فواتير ضريبية',
                'فواتير مبسطة',
                '',
                'المبيعات المستهدفة (قبل الضريبة)',
                'المبيعات الفعلية (قبل الضريبة)',
                'الفرق',
                '',
                'الضريبة المستهدفة',
                'الضريبة الفعلية',
                'الفرق',
                '',
                'الإجمالي المستهدف (شامل الضريبة)',
                'الإجمالي الفعلي (شامل الضريبة)',
                'الفرق'
            ],
            'القيمة': [
                quarter_name,
                len(invoices),
                tax_count,
                simplified_count,
                '',
                f'{float(target_sales):,.2f}',
                f'{float(actual_sales):,.2f}',
                f'{float(sales_diff):,.2f}',
                '',
                f'{float(target_vat):,.2f}',
                f'{float(actual_vat):,.2f}',
                f'{float(vat_diff):,.2f}',
                '',
                f'{float(total_target):,.2f}',
                f'{float(total_actual):,.2f}',
                f'{float(total_diff):,.2f}'
            ]
        }
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to Excel
        output_path = self._save_excel_with_error_handling(df, output_filename)
        
        print(f"✓ Quarterly summary report: {output_path}")
        print(f"  Quarter: {quarter_name}")
        print(f"  Sales difference: {float(sales_diff):.2f} SAR")
        print(f"  VAT difference: {float(vat_diff):.2f} SAR")
        
        return output_path
    
    def generate_all_reports(
        self,
        quarter_name: str,
        invoices: List[Dict],
        target_sales: Decimal,
        target_vat: Decimal
    ) -> Dict[str, str]:
        """
        Generate all 3 reports for a quarter.
        
        Args:
            quarter_name: Name of quarter
            invoices: List of invoice dictionaries
            target_sales: Target sales before VAT
            target_vat: Target VAT amount
            
        Returns:
            Dictionary with paths to all generated reports
        """
        print(f"\n{'='*60}")
        print(f"GENERATING REPORTS FOR {quarter_name}")
        print(f"{'='*60}\n")
        
        # Calculate actuals
        actual_sales = sum(inv['subtotal'] for inv in invoices)
        actual_vat = sum(inv['vat_amount'] for inv in invoices)
        
        # Generate reports
        detailed_path = self.generate_detailed_sales_report(
            invoices,
            f"{quarter_name}_detailed_sales.xlsx"
        )
        
        summary_path = self.generate_invoice_summary_report(
            invoices,
            f"{quarter_name}_invoice_summary.xlsx"
        )
        
        quarterly_path = self.generate_quarterly_summary_report(
            quarter_name,
            target_sales,
            target_vat,
            actual_sales,
            actual_vat,
            invoices,
            f"{quarter_name}_quarterly_summary.xlsx"
        )
        
        print(f"\n{'='*60}")
        print(f"ALL REPORTS GENERATED FOR {quarter_name}")
        print(f"{'='*60}\n")
        
        return {
            'detailed': detailed_path,
            'summary': summary_path,
            'quarterly': quarterly_path
        }