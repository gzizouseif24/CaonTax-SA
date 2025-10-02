from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import qrcode
from io import BytesIO
import base64

def generate_simple_qr(data):
    """Generate a simple QR code as base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader('templates/'))

# Test SIMPLIFIED invoice
print("Testing SIMPLIFIED invoice template...")
template = env.get_template('invoice_simplified.html')

sample_data = {
    'company': {
        'name': 'مؤسسة رائد الإنجاز للخدمات التجارية',
        'address': 'الرياض، السلي 14322',
        'phone': '0555866344',
        'tax_number': '302167780700003',
        'email': 'M.ALSHAIKHI1993@GMAIL.COM'
    },
    'invoice': {
        'number': 'INV-SIMP-0001',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    },
    'customer': {
        'name': 'عميل نقدي'
    },
    'items': [
        {'name': 'شيبس بطاطس', 'quantity': 10, 'unit_price': 6.47, 'total': 64.70},
        {'name': 'عصير برتقال', 'quantity': 5, 'unit_price': 3.25, 'total': 16.25},
        {'name': 'شوكولاتة', 'quantity': 3, 'unit_price': 4.50, 'total': 13.50}
    ],
    'totals': {
        'subtotal': 94.45,
        'vat': 14.17,
        'total': 108.62
    },
    'qr_code': generate_simple_qr('INV-SIMP-0001|مؤسسة رائد الإنجاز|302167780700003')
}

# Render SIMPLIFIED
html = template.render(**sample_data)
with open('test_simplified.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("✓ Simplified invoice rendered! Open test_simplified.html in browser")

# Test TAX invoice
print("\nTesting TAX invoice template...")
template_tax = env.get_template('invoice_tax.html')

sample_data_tax = {
    'company': {
        'name': 'مؤسسة رائد الإنجاز للخدمات التجارية',
        'address': 'الرياض، السلي 14322',
        'phone': '0555866344',
        'tax_number': '302167780700003',
        'email': 'M.ALSHAIKHI1993@GMAIL.COM'
    },
    'invoice': {
        'number': 'INV-TAX-0001',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    },
    'customer': {
        'name': 'شركة المثال التجارية',
        'address': 'الرياض، حي النخيل',
        'tax_number': '300000000000003'
    },
    'items': [
        {
            'name': 'شيبس بطاطس - عبوة كبيرة',
            'quantity': 100,
            'unit_price': 6.47,
            'line_subtotal': 647.00,
            'line_vat': 97.05
        },
        {
            'name': 'عصير برتقال - كرتون 24 حبة',
            'quantity': 50,
            'unit_price': 78.00,
            'line_subtotal': 3900.00,
            'line_vat': 585.00
        },
        {
            'name': 'بسكويت محلى - كرتون',
            'quantity': 30,
            'unit_price': 45.50,
            'line_subtotal': 1365.00,
            'line_vat': 204.75
        }
    ],
    'totals': {
        'subtotal': 5912.00,
        'vat': 886.80,
        'total': 6798.80
    },
    'qr_code': generate_simple_qr('INV-TAX-0001|مؤسسة رائد الإنجاز|302167780700003')
}

# Render TAX
html_tax = template_tax.render(**sample_data_tax)
with open('test_tax.html', 'w', encoding='utf-8') as f:
    f.write(html_tax)
print("✓ Tax invoice rendered! Open test_tax.html in browser")

print("\n" + "="*60)
print("TEMPLATES TESTED SUCCESSFULLY!")
print("="*60)
print("\nNext steps:")
print("1. Open test_simplified.html in your browser")
print("2. Open test_tax.html in your browser")
print("3. Check if the layout looks good")
print("4. Adjust CSS in the template files if needed")
print("5. Then integrate with WeasyPrint for PDF generation")