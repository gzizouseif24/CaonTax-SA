"""
Generate sample PDF invoices from Q2-2024.
This will show how invoices look with multiple line items.
"""

import sys
import os
import pickle

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from excel_reader import read_products, read_customers, read_holidays
from inventory import InventoryManager
from simulation import SalesSimulator
from alignment import QuarterlyAligner
from pdf_generator import PDFGenerator
from config import QUARTERLY_TARGETS


def generate_sample_invoices():
    """Generate sample PDFs from Q2-2024."""
    
    print("\n" + "="*80)
    print("📄 GENERATING SAMPLE PDF INVOICES FROM Q2-2024")
    print("="*80)
    print("\nThis will show how invoices look with multiple line items.\n")
    
    # Check if we have cached invoices
    cache_file = "output/q2_2024_invoices.pkl"
    
    if os.path.exists(cache_file):
        print("📂 Loading cached Q2-2024 invoices...")
        with open(cache_file, 'rb') as f:
            invoices = pickle.load(f)
        print(f"   ✓ Loaded {len(invoices)} invoices from cache")
    else:
        print("📂 Generating Q2-2024 invoices...")
        
        # Load data
        products = read_products('input/products.xlsx')
        customers = read_customers('input/customers.xlsx')
        holidays = read_holidays('input/holidays.xlsx')
        
        # Initialize system
        inventory = InventoryManager(products)
        simulator = SalesSimulator(inventory, holidays)
        aligner = QuarterlyAligner(simulator, use_smart_algorithm=True)
        
        # Get Q2-2024 config
        config = QUARTERLY_TARGETS["Q2-2024"]
        
        # Filter customers
        quarter_customers = [
            c for c in customers
            if config['period_start'] <= c['purchase_date'] <= config['period_end']
        ]
        
        # Generate invoices
        invoices = aligner.align_quarter(
            quarter_name="Q2-2024",
            start_date=config['period_start'],
            end_date=config['period_end'],
            target_total_inc_vat=config['sales_inc_vat'],
            vat_customers=quarter_customers,
            allow_variance=config['allow_variance']
        )
        
        # Cache for future use
        os.makedirs("output", exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump(invoices, f)
        
        print(f"   ✓ Generated and cached {len(invoices)} invoices")
    
    # Analyze invoices
    print(f"\n📊 Invoice Analysis:")
    
    # Find interesting invoices
    b2b_invoices = [inv for inv in invoices if inv['invoice_type'] == 'TAX']
    b2c_invoices = [inv for inv in invoices if inv['invoice_type'] == 'SIMPLIFIED']
    
    # Find invoice with most line items
    max_lines_invoice = max(invoices, key=lambda x: len(x['line_items']))
    
    # Find multi-lot invoice (same item from different lots)
    multi_lot_invoice = None
    for inv in invoices:
        items = [line['item_description'] for line in inv['line_items']]
        if len(items) != len(set(items)):  # Has duplicates
            multi_lot_invoice = inv
            break
    
    print(f"   Total invoices: {len(invoices)}")
    print(f"   B2B (Tax): {len(b2b_invoices)}")
    print(f"   B2C (Simplified): {len(b2c_invoices)}")
    print(f"   Max line items: {len(max_lines_invoice['line_items'])} (Invoice: {max_lines_invoice['invoice_number']})")
    
    # Select samples
    samples = []
    
    # Sample 1: B2B invoice with most line items
    if b2b_invoices:
        b2b_max = max(b2b_invoices, key=lambda x: len(x['line_items']))
        samples.append(('B2B_multi_items', b2b_max))
        print(f"\n   Sample 1: B2B invoice {b2b_max['invoice_number']}")
        print(f"      Customer: {b2b_max['customer_name']}")
        print(f"      Line items: {len(b2b_max['line_items'])}")
        print(f"      Total: {b2b_max['total']:,.2f} SAR")
    
    # Sample 2: B2C invoice with many items
    if b2c_invoices:
        b2c_large = max(b2c_invoices, key=lambda x: len(x['line_items']))
        samples.append(('B2C_multi_items', b2c_large))
        print(f"\n   Sample 2: B2C invoice {b2c_large['invoice_number']}")
        print(f"      Customer: {b2c_large['customer_name']}")
        print(f"      Line items: {len(b2c_large['line_items'])}")
        print(f"      Total: {b2c_large['total']:,.2f} SAR")
    
    # Sample 3: Multi-lot invoice (if found)
    if multi_lot_invoice:
        samples.append(('Multi_lot', multi_lot_invoice))
        print(f"\n   Sample 3: Multi-lot invoice {multi_lot_invoice['invoice_number']}")
        print(f"      Line items: {len(multi_lot_invoice['line_items'])}")
        print(f"      Total: {multi_lot_invoice['total']:,.2f} SAR")
    
    # Sample 4: Simple B2C invoice
    simple_b2c = min(b2c_invoices, key=lambda x: len(x['line_items']))
    samples.append(('B2C_simple', simple_b2c))
    print(f"\n   Sample 4: Simple B2C invoice {simple_b2c['invoice_number']}")
    print(f"      Line items: {len(simple_b2c['line_items'])}")
    print(f"      Total: {simple_b2c['total']:,.2f} SAR")
    
    # Generate PDFs
    print(f"\n📄 Generating PDF samples...")
    print(f"   Output directory: output/sample_invoices/")
    
    os.makedirs("output/sample_invoices", exist_ok=True)
    
    # Initialize PDF generator
    try:
        pdf_gen = PDFGenerator()
        
        for name, invoice in samples:
            output_path = f"output/sample_invoices/{name}_{invoice['invoice_number'].replace('/', '-')}.pdf"
            
            try:
                pdf_gen.generate_pdf(invoice, output_path)
                print(f"   ✓ Generated: {output_path}")
                
                # Show line items
                print(f"      Line items in this invoice:")
                for i, line in enumerate(invoice['line_items'][:5], 1):  # Show first 5
                    print(f"         {i}. {line['item_description']}: {line['quantity']} × {line['unit_price_ex_vat']:.2f} = {line['line_subtotal']:.2f} SAR")
                if len(invoice['line_items']) > 5:
                    print(f"         ... and {len(invoice['line_items']) - 5} more items")
                
            except Exception as e:
                print(f"   ❌ Error generating {name}: {e}")
                print(f"      Note: Make sure wkhtmltopdf is installed!")
                print(f"      Download from: https://wkhtmltopdf.org/downloads.html")
        
        print(f"\n{'='*80}")
        print("✅ SAMPLE PDFs GENERATED")
        print(f"{'='*80}")
        print(f"\n📁 Check output/sample_invoices/ folder")
        print(f"\n💡 Each PDF shows:")
        print(f"   - Invoice header (number, date, seller info)")
        print(f"   - Customer info (for B2B)")
        print(f"   - Line items table (ALL items in one invoice)")
        print(f"   - Totals (subtotal, VAT, total)")
        print(f"   - QR code (for B2C)")
        
    except Exception as e:
        print(f"\n❌ PDF generation failed: {e}")
        print(f"\n💡 To fix:")
        print(f"   1. Install wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
        print(f"   2. Add to PATH or update pdf_generator.py with correct path")
        print(f"   3. Re-run this script")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    generate_sample_invoices()
