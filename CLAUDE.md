# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Saudi Arabian invoice generation system that creates realistic, tax-compliant invoices with quarterly financial targets. The system generates 751 invoices across 6 quarters (Q3-2023 through Q4-2024) totaling 5.29M SAR in sales with 793K SAR in VAT.

## Essential Commands

### Generate Invoices and Validate System
```bash
python testing.py
```
Generates all invoices, validates price accuracy (100%), profitability (100%), and target matching. Creates invoice JSON files in `output/` and `debug_results.json` with metrics.

### Generate All Reports
```bash
python generate_complete_reports.py
```
Generates 25 Excel reports: 18 standard reports (3 per quarter) + 6 enhanced analytics (1 per quarter) + 1 consolidated summary. All saved to `output/reports/`.

### List Available Reports
```bash
python list_reports.py
```
Shows all generated reports with sizes and modification dates.

### Analyze System Performance
```bash
python analyze_debug_results.py
```
Detailed analysis of invoice generation metrics and validation results.

### Alternative Report Commands
```bash
python generate_all_reports.py         # Standard reports only
python generate_enhanced_reports.py    # Analytics only
```

## Architecture

### Data Flow
1. **Input** → Excel files in `input/`: `products.xlsx`, `customers.xlsx`, `holidays.xlsx`
2. **Processing** → Core modules process data with FIFO inventory and alignment algorithms
3. **Output** → JSON invoices in `output/`, Excel reports in `output/reports/`

### Core Module Structure

**excel_reader.py** - Reads Excel input files with English column names (`item_name`, `import_date`, `quantity`, `total_cost`, `profit_margin_pct`, `unit_price_before_vat`, `classification`, `customs_declaration`)

**inventory.py** - `InventoryManager` manages FIFO inventory logic. Returns ONE record per unique item name (not per batch). Tracks `quantity_remaining` across batches.

**simulation.py** - `SalesSimulator` generates realistic sales based on:
- Working days (Saturday-Thursday, no Fridays)
- Seasonal boosts (Ramadan/Shaaban: 2.0x)
- Salary day boosts (Day 27: 1.5x, Day 1: 1.2x, Day 10: 1.1x)
- Stock dates (items only available after `stock_date`)
- Classification rules (OUTSIDE_INSPECTION must be alone in basket, UNDER_NON_SELECTIVE and UNDER_SELECTIVE can mix)

**alignment.py** - `QuarterlyAligner` aligns simulated sales to exact quarterly targets:
- **2024 mode** (strict): Must match targets within TOLERANCE (±0.10 SAR)
- **2023 mode** (flexible): Best effort, accepts any total
- Two-phase: VAT customer invoices first, then cash sales to fill gap
- NEVER sells below cost - tracks actual FIFO costs for profitability

**report_generator.py** - `ReportGenerator` creates three types of Excel reports per quarter:
1. Detailed Sales - All line items
2. Invoice Summary - One row per invoice
3. Quarterly Summary - Target vs Actual comparison

**pdf_generator.py** - `PDFGenerator` generates PDF invoices using Jinja2 templates and pdfkit (requires wkhtmltopdf at `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`)

**config.py** - Central configuration with:
- `QUARTERLY_TARGETS` - Exact sales/VAT targets with date ranges
- Seller information (name, address, phone, email, tax number)
- VAT rate (15%)
- Classification constants
- Simulation settings (boosts, working days, basket sizes)
- Alignment settings (max iterations, tolerance, adjustment step)

### Key Data Structures

**Product Dictionary** (from Excel):
```python
{
    'item_name': str,
    'classification': str,  # One of: OUTSIDE_INSPECTION, UNDER_NON_SELECTIVE, UNDER_SELECTIVE
    'import_date': date,
    'stock_date': date,     # import_date + 0 days (special for Q3-2023)
    'quantity': int,
    'quantity_remaining': int,
    'unit_cost': Decimal,
    'unit_price_before_vat': Decimal,  # Read from Excel, not calculated
    'profit_margin_pct': Decimal,
    'customs_declaration': str
}
```

**Invoice Dictionary**:
```python
{
    'invoice_number': str,
    'invoice_type': str,    # 'simplified' or 'tax'
    'invoice_date': datetime,
    'customer_name': str,
    'customer_tax_number': str or None,
    'items': List[Dict],
    'subtotal': Decimal,
    'vat_amount': Decimal,
    'total': Decimal
}
```

### Critical Implementation Rules

**Price Accuracy**: Unit prices come directly from `products.xlsx` column `unit_price_before_vat` - never recalculate during alignment. The system achieves 100% price accuracy by respecting Excel prices.

**FIFO Inventory**: Items are consumed from oldest batches first (earliest `import_date`). Multiple batches of the same item may have different prices. Always use `InventoryManager.get_unit_price()` which returns price from oldest available batch.

**Stock Date Filtering**: When generating invoices, only use items where `stock_date <= current_date`. Special handling for Q3-2023: stock_date = import_date + 0 days.

**Profitability Guarantee**: NEVER sell below cost. Alignment algorithm tracks actual FIFO costs per item and adjusts quantities to maintain profitability on every sale.

**Classification Mixing**:
- OUTSIDE_INSPECTION items must be ALONE in basket
- UNDER_NON_SELECTIVE and UNDER_SELECTIVE can mix together
- 20% of baskets use OUTSIDE_INSPECTION

**Date Handling**: Use `decimal.Decimal` for all money values. Use `datetime.date` for dates. JSON serialization requires custom encoder for these types.

**2023 vs 2024 Alignment**:
- 2023 quarters: `allow_variance=True` (best effort, minor variances acceptable)
- 2024 quarters: `allow_variance=False` (strict matching within TOLERANCE)

## Testing

Run from project root:
```bash
python testing.py  # Full system validation
```

Individual test files in `tests/`:
- `test_inventory.py` - Inventory FIFO logic
- `test_simulation.py` - Sales simulation
- `test_alignement.py` - Alignment algorithm
- `final_test.py` - Full integration test

## Expected Output

**After `python testing.py`**:
- 751 invoices across 6 quarters
- 5,291,467.54 SAR total sales
- 793,720.17 SAR total VAT
- 100% price accuracy (matches Excel)
- 100% profitability (no loss sales)
- Minor variance in 2023 quarters (<0.01%)

**After `python generate_complete_reports.py`**:
- 25 Excel files in `output/reports/`
- Start with `consolidated_summary.xlsx` for overview
- Quarter analytics files for detailed insights

## File Organization

```
input/                          # Excel source data
  products.xlsx                 # Product catalog with prices
  customers.xlsx                # VAT registered customers
  holidays.xlsx                 # Saudi holidays
output/                         # Generated invoices (JSON)
  invoices_Q3_2023.json
  invoices_Q4_2023.json
  ...
output/reports/                 # Generated Excel reports
  Q*_detailed_sales.xlsx
  Q*_invoice_summary.xlsx
  Q*_analytics.xlsx
  consolidated_summary.xlsx
templates/                      # Jinja2 templates for PDFs
tests/                          # Test files
```

## Dependencies

Install via: `pip install -r requirements.txt`

Key packages:
- pandas, openpyxl - Excel I/O
- reportlab, weasyprint, pdfkit - PDF generation
- arabic-reshaper, python-bidi - Arabic text support
- hijri-converter - Islamic calendar for seasonal boosts
- xlsxwriter - Enhanced Excel writing
- qrcode, pillow - QR code generation

## Notes

- System is production-ready with validated accuracy
- All monetary values use `Decimal` to avoid floating-point errors
- Invoice numbering: Simplified invoices start at 1, tax invoices start at 1 (separate sequences)
- Working hours: 9 AM to 10 PM (config: `WORKING_HOURS`)
- Basket sizes: 2-10 items, 3-40 quantity per item (configurable in `config.py`)
