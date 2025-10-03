from jinja2 import Environment, FileSystemLoader
import pdfkit
import qrcode
import io
import base64
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
from config import SELLER_NAME, SELLER_ADDRESS, SELLER_PHONE, SELLER_EMAIL, SELLER_TAX_NUMBER
import os


class PDFGenerator:
    """
    Generates PDF invoices from HTML templates using Jinja2 and pdfkit.
    """
    
    def __init__(self, template_dir: str = "templates", wkhtmltopdf_path: str = None):
        """
        Initialize PDF generator.
        
        Args:
            template_dir: Directory containing HTML templates
            wkhtmltopdf_path: Path to wkhtmltopdf executable (auto-detect if None)
        """
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Configure pdfkit
        if wkhtmltopdf_path:
            self.pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        else:
            # Try default Windows installation path
            default_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            if os.path.exists(default_path):
                self.pdfkit_config = pdfkit.configuration(wkhtmltopdf=default_path)
            else:
                self.pdfkit_config = None
        
    def generate_qr_code(self, invoice_data: Dict) -> str:
        """
        Generate QR code containing invoice information.
        
        Per BRD: QR must show invoice number, seller name, address, tax number
        
        Args:
            invoice_data: Invoice dictionary
            
        Returns:
            Base64 encoded QR code image
        """
        # Build QR content
        qr_content = (
            f"Invoice: {invoice_data['invoice_number']}\n"
            f"Seller: {SELLER_NAME}\n"
            f"Address: {SELLER_ADDRESS}\n"
            f"Tax Number: {SELLER_TAX_NUMBER}\n"
            f"Total: {invoice_data['total']} SAR"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def format_invoice_data(self, invoice: Dict) -> Dict:
        """
        Format invoice data for template rendering.
        
        Args:
            invoice: Raw invoice dictionary from alignment
            
        Returns:
            Formatted dictionary for Jinja2 template
        """
        # Format date
        invoice_date = invoice['invoice_date']
        if isinstance(invoice_date, datetime):
            formatted_date = invoice_date.strftime('%d/%m/%Y %H:%M')
        else:
            formatted_date = str(invoice_date)
        
        # Generate QR code
        qr_code = self.generate_qr_code(invoice)
        
        # Build template data
        template_data = {
            'company': {
                'name': SELLER_NAME,
                'address': SELLER_ADDRESS,
                'phone': SELLER_PHONE,
                'email': SELLER_EMAIL,
                'tax_number': SELLER_TAX_NUMBER
            },
            'invoice': {
                'number': invoice['invoice_number'],
                'date': formatted_date
            },
            'customer': {
                'name': invoice['customer_name'],
                'address': invoice.get('customer_address', ''),
                'tax_number': invoice.get('customer_tax_number', '')
            },
            'items': [],
            'totals': {
                'subtotal': float(invoice['subtotal']),
                'vat': float(invoice['vat_amount']),
                'total': float(invoice['total'])
            },
            'qr_code': qr_code
        }
        
        # Format line items
        for item in invoice['line_items']:
            template_data['items'].append({
                'name': item['item_name'],
                'quantity': item['quantity'],
                'unit_price': float(item['unit_price']),
                'line_subtotal': float(item['line_subtotal']),
                'line_vat': float(item['vat_amount']),
                'total': float(item['line_total'])
            })
        
        return template_data
    
    def generate_pdf(
        self,
        invoice: Dict,
        output_path: str,
        template_name: str = None
    ) -> str:
        """
        Generate PDF invoice from data.
        
        Args:
            invoice: Invoice dictionary
            output_path: Path to save PDF
            template_name: Optional template override
            
        Returns:
            Path to generated PDF
        """
        # Determine template based on invoice type
        if template_name is None:
            if invoice['invoice_type'] == 'TAX':
                template_name = 'invoice_tax.html'
            else:
                template_name = 'invoice_simplified.html'
        
        # Format data for template
        template_data = self.format_invoice_data(invoice)
        
        # Render HTML
        template = self.env.get_template(template_name)
        html_content = template.render(**template_data)
        
        # PDF options for better rendering
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'print-media-type': None,
            'no-outline': None,
            'quiet': None
        }
        
        # Add page size based on invoice type
        options['page-size'] = 'A4'
        
        # Generate PDF
        pdfkit.from_string(
            html_content,
            output_path,
            configuration=self.pdfkit_config,
            options=options
        )
        
        return output_path
    
    def generate_invoice_batch(
        self,
        invoices: List[Dict],
        output_dir: str = "output/invoices"
    ) -> List[str]:
        """
        Generate multiple invoice PDFs.
        
        Args:
            invoices: List of invoice dictionaries
            output_dir: Directory to save PDFs
            
        Returns:
            List of generated PDF paths
        """
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        
        for i, invoice in enumerate(invoices):
            # Generate filename
            invoice_number = invoice['invoice_number'].replace('/', '-')
            output_path = os.path.join(output_dir, f"{invoice_number}.pdf")
            
            try:
                self.generate_pdf(invoice, output_path)
                generated_files.append(output_path)
                
                if (i + 1) % 50 == 0:
                    print(f"  Generated {i + 1}/{len(invoices)} invoices...")
                    
            except Exception as e:
                print(f"  Error generating {invoice['invoice_number']}: {e}")
                continue
        
        print(f"\n✓ Generated {len(generated_files)}/{len(invoices)} PDF invoices")
        return generated_files