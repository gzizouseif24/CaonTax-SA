# 🚀 E-Invoicing System: Complete Implementation Plan

## 📋 PROJECT OVERVIEW

**Objective:** Build a sales simulation system that generates realistic invoices matching exact quarterly tax targets

**Duration:** 4 days

**Tech Stack:** Python + FastAPI + PostgreSQL + ReportLab

**Complexity Level:** 8/10 (High)

---

## 🎯 CORE TECHNICAL REQUIREMENTS

### Must-Have Features
1. ✅ Import 3 Excel files with configurable column mapping
2. ✅ FIFO inventory management system
3. ✅ Automated sales generation engine with seasonal/salary boosts
4. ✅ Quarterly alignment algorithm (exact match to ±0.01 SAR)
5. ✅ Two invoice types: Simplified (thermal) + Tax (A4)
6. ✅ QR code generation with seller/invoice data
7. ✅ Arabic RTL support in PDFs
8. ✅ Detailed & summary reports (PDF/Excel export)

### Constraints
- 203 products across 3 classifications
- 70 VAT customers (2024 only, 4.68M SAR purchases)
- 6 quarterly targets (5.55M SAR total sales)
- No sales on Fridays or holidays
- Strict classification mixing rules
- Cannot exceed inventory (FIFO depletion)

---

## 🛠️ TECHNOLOGY STACK & LIBRARIES

### Core Framework
```bash
# Backend Framework
fastapi==0.110.0          # Modern async web framework
uvicorn==0.29.0           # ASGI server
pydantic==2.6.4           # Data validation
python-dotenv==1.0.1      # Environment variables
```

### Database
```bash
# Database ORM
sqlalchemy==2.0.27        # ORM for PostgreSQL
psycopg2-binary==2.9.9    # PostgreSQL adapter
alembic==1.13.1           # Database migrations
```

### Excel Processing
```bash
# Excel Import/Export
openpyxl==3.1.2           # Read/write Excel files
pandas==2.2.1             # Data manipulation
xlsxwriter==3.2.0         # Excel export with formatting
```

### PDF Generation
```bash
# PDF Libraries
reportlab==4.1.0          # PDF generation (Arabic support in 4.4+)
arabic-reshaper==3.0.0    # Reshape Arabic text for PDF
python-bidi==0.4.2        # BiDirectional text support
pillow==10.2.0            # Image processing for PDFs
```

### QR Code Generation
```bash
# QR Code/Barcode
qrcode[pil]==7.4.2        # QR code generation
python-barcode==0.15.1    # Barcode generation (if needed)
```

### Date/Time Handling
```bash
# Islamic Calendar
hijri-converter==2.3.1    # Convert Gregorian ↔ Hijri dates
```

### Testing & Development
```bash
# Development Tools
pytest==8.0.2             # Testing framework
pytest-asyncio==0.23.5    # Async testing
faker==24.0.0             # Generate fake data for testing
black==24.2.0             # Code formatting
flake8==7.0.0             # Linting
```

---

## 📁 PROJECT STRUCTURE

```
e-invoicing-system/
│
├── app/                          # Main application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Settings & environment vars
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── item.py               # Items/Products
│   │   ├── batch.py              # Inventory batches
│   │   ├── customer.py           # VAT customers
│   │   ├── invoice.py            # Invoice headers
│   │   ├── invoice_line.py       # Invoice line items
│   │   └── holiday.py            # Official holidays
│   │
│   ├── schemas/                  # Pydantic models
│   │   ├── __init__.py
│   │   ├── item.py
│   │   ├── customer.py
│   │   ├── invoice.py
│   │   └── report.py
│   │
│   ├── api/                      # API routes
│   │   ├── __init__.py
│   │   ├── import_routes.py      # Excel import endpoints
│   │   ├── simulation_routes.py  # Run simulation
│   │   ├── invoice_routes.py     # Invoice CRUD
│   │   └── report_routes.py      # Generate reports
│   │
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── import_service.py     # Excel import with column mapping
│   │   ├── inventory_service.py  # FIFO stock management
│   │   ├── simulation_engine.py  # Sales generation logic
│   │   ├── alignment_engine.py   # Quarterly matching algorithm
│   │   ├── invoice_service.py    # Invoice generation
│   │   └── report_service.py     # Report generation
│   │
│   ├── pdf_generators/           # PDF creation
│   │   ├── __init__.py
│   │   ├── base_generator.py     # Base PDF class
│   │   ├── simplified_invoice.py # Thermal receipt
│   │   ├── tax_invoice.py        # A4 tax invoice
│   │   └── arabic_utils.py       # RTL text handling
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── date_utils.py         # Hijri/Gregorian conversion
│   │   ├── qr_generator.py       # QR code creation
│   │   ├── validators.py         # Data validation
│   │   └── constants.py          # Constants & enums
│   │
│   ├── database/                 # Database
│   │   ├── __init__.py
│   │   ├── session.py            # DB connection
│   │   └── base.py               # Base model
│   │
│   └── templates/                # PDF templates (HTML/CSS if using HTML→PDF)
│       ├── simplified_invoice.html
│       └── tax_invoice.html
│
├── migrations/                   # Alembic migrations
│   └── versions/
│
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_import.py
│   ├── test_inventory.py
│   ├── test_simulation.py
│   ├── test_alignment.py
│   └── test_invoice_generation.py
│
├── data/                         # Input data folder
│   ├── uploads/                  # Excel uploads
│   ├── column_mappings/          # Saved mappings
│   └── sample_data/              # Test data
│
├── output/                       # Generated files
│   ├── invoices/                 # PDF invoices
│   └── reports/                  # Excel/PDF reports
│
├── fonts/                        # Arabic fonts
│   ├── Amiri-Regular.ttf
│   └── NotoNaskhArabic-Regular.ttf
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore
├── README.md
└── run.py                        # Run development server
```

---

## 🗄️ DATABASE SCHEMA

### Items Table
```python
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    customs_declaration = Column(String(50))
    classification = Column(Enum(ItemClassification))
    # Relations
    batches = relationship("Batch", back_populates="item")
```

**ItemClassification Enum:**
- `OUTSIDE_INSPECTION_NON_SELECTIVE`
- `UNDER_INSPECTION_NON_SELECTIVE`
- `UNDER_INSPECTION_SELECTIVE`

### Batches Table (Inventory)
```python
class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    import_date = Column(Date, nullable=False)
    stock_date = Column(Date, nullable=False)  # import_date + 7-12 days
    quantity_imported = Column(Integer, nullable=False)
    quantity_remaining = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    unit_price_before_vat = Column(Numeric(10, 2), nullable=False)
    profit_margin_pct = Column(Numeric(5, 2))
    # Relations
    item = relationship("Item", back_populates="batches")
```

### Customers Table
```python
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tax_number = Column(String(50), unique=True)
    commercial_registration = Column(String(50))
    customer_type = Column(Enum(CustomerType))  # CASH or VAT
    # Relations
    invoices = relationship("Invoice", back_populates="customer")
```

### Invoices Table
```python
class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_type = Column(Enum(InvoiceType))  # SIMPLIFIED or TAX
    customer_id = Column(Integer, ForeignKey("customers.id"))
    invoice_date = Column(DateTime, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    vat_amount = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    qr_code_data = Column(Text)
    # Relations
    customer = relationship("Customer", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice")
```

### Invoice Lines Table
```python
class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    batch_id = Column(Integer, ForeignKey("batches.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_subtotal = Column(Numeric(10, 2), nullable=False)
    vat_amount = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    # Relations
    invoice = relationship("Invoice", back_populates="lines")
```

### Holidays Table
```python
class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
```

---

## 🔧 MODULE IMPLEMENTATION DETAILS

### Module 1: Excel Import Service

**File:** `app/services/import_service.py`

**Responsibilities:**
- Read Excel files (Products, Customers, Holidays)
- Apply configurable column mapping
- Validate data
- Insert into database

**Key Functions:**
```python
class ImportService:
    def import_products(self, file_path: str, mapping: dict) -> int:
        """Import products from Excel with column mapping"""
        # Read Excel with pandas
        # Apply column mapping
        # Validate classifications
        # Calculate unit prices
        # Insert into Items & Batches tables
        # Return count of imported items
        
    def import_customers(self, file_path: str, mapping: dict) -> int:
        """Import VAT customers with purchase data"""
        
    def import_holidays(self, file_path: str) -> int:
        """Import holiday calendar"""
        
    def save_column_mapping(self, name: str, mapping: dict):
        """Save mapping config for reuse"""
```

**Column Mapping Example:**
```python
product_mapping = {
    "الصنف": "item_name",
    "تاريخ الاستيراد": "import_date",
    "البيان الجمركي للشحنة": "customs_declaration",
    "الكمية ": "quantity",
    " اجمالي التكاليف ": "total_cost",
    "نسبة هامش الربح ": "profit_margin_pct",
    "النوع ": "classification"
}
```

---

### Module 2: Inventory Management Service

**File:** `app/services/inventory_service.py`

**Responsibilities:**
- Track inventory with FIFO
- Deduct stock on sales
- Check availability before sales

**Key Functions:**
```python
class InventoryService:
    def get_available_quantity(self, item_id: int) -> int:
        """Get total available quantity for an item"""
        
    def get_available_items_by_classification(
        self, 
        classification: ItemClassification
    ) -> List[Item]:
        """Get all items with available stock by classification"""
        
    def deduct_stock_fifo(
        self, 
        item_id: int, 
        quantity: int
    ) -> List[Tuple[int, int]]:  # Returns [(batch_id, qty_deducted), ...]
        """Deduct quantity using FIFO, returns list of batches used"""
        # Query batches ordered by stock_date ASC
        # Deduct from oldest first
        # Update quantity_remaining
        # Raise exception if insufficient stock
        
    def get_unit_price_fifo(self, item_id: int) -> Decimal:
        """Get unit price from oldest available batch (FIFO)"""
```

---

### Module 3: Simulation Engine

**File:** `app/services/simulation_engine.py`

**Responsibilities:**
- Generate daily sales based on rules
- Apply seasonal & salary day boosts
- Respect working hours & holidays
- Handle classification mixing rules

**Key Functions:**
```python
class SimulationEngine:
    def __init__(self, config: SimulationConfig):
        self.config = config  # VAT rate, boosts, working hours
        
    def generate_quarterly_sales(
        self,
        quarter_start: date,
        quarter_end: date,
        target_sales: Decimal,
        target_vat: Decimal
    ) -> List[Invoice]:
        """Main simulation loop - generates invoices for a quarter"""
        
    def generate_daily_sales(self, date: date) -> List[Invoice]:
        """Generate all invoices for a specific day"""
        # Check if working day
        # Calculate boost factor (seasonal + salary day)
        # Generate N invoices (5-20 × boost)
        # For each invoice: choose type, select items, create
        
    def select_invoice_type(self) -> InvoiceType:
        """Randomly choose SIMPLIFIED or TAX invoice"""
        # If VAT customer available and needs purchase → TAX
        # Otherwise → SIMPLIFIED
        
    def build_invoice_basket(
        self,
        invoice_type: InvoiceType,
        margin_multiplier: float = 1.0
    ) -> List[Tuple[Item, int]]:  # Returns [(item, quantity), ...]
        """Select 2-10 items respecting classification rules"""
        # If SIMPLIFIED → can mix SELECTIVE + NON_SELECTIVE (under inspection)
        # If TAX → only NON_SELECTIVE (under inspection)
        # OUTSIDE_INSPECTION → must be alone
        
    def calculate_boost_factor(self, date: date) -> float:
        """Calculate multiplier for date"""
        boost = 1.0
        # Check if Ramadan/Sha'ban → ×2.0
        # Check if day 27 → ×1.5
        # Check if day 1 → ×1.2
        # Check if day 10 → ×1.1
        return boost
        
    def is_working_day(self, date: date) -> bool:
        """Check if sales should occur on this date"""
        # False if Friday
        # False if in holidays table
        # True otherwise
```

**Simulation Config:**
```python
@dataclass
class SimulationConfig:
    vat_rate: Decimal = Decimal("0.15")
    working_hours: Tuple[int, int] = (9, 22)
    working_days: List[int] = [0, 1, 2, 3, 4, 5]  # Mon-Sat (Friday = 4)
    ramadan_boost: float = 2.0
    salary_day_27_boost: float = 1.5
    salary_day_1_boost: float = 1.2
    salary_day_10_boost: float = 1.1
    min_items_per_invoice: int = 2
    max_items_per_invoice: int = 10
    min_quantity_per_item: int = 3
    max_quantity_per_item: int = 40
```

---

### Module 4: Quarterly Alignment Engine

**File:** `app/services/alignment_engine.py`

**Responsibilities:**
- Adjust simulation to match exact quarterly targets
- Iterative convergence algorithm
- Handle customer purchase constraints

**Core Algorithm:**
```python
class AlignmentEngine:
    def __init__(self, simulation_engine: SimulationEngine):
        self.simulation = simulation_engine
        self.max_iterations = 1000
        self.tolerance = Decimal("0.01")
        
    def align_quarter(
        self,
        quarter: QuarterlyTarget,
        customer_purchases: List[CustomerPurchase]
    ) -> List[Invoice]:
        """Main alignment function"""
        
        # Phase 1: Generate VAT customer invoices (fixed amounts)
        vat_invoices = self._generate_customer_invoices(customer_purchases)
        vat_sales = sum(inv.subtotal for inv in vat_invoices)
        vat_vat = sum(inv.vat_amount for inv in vat_invoices)
        
        # Phase 2: Calculate gap to fill with cash sales
        remaining_sales = quarter.target_sales - vat_sales
        remaining_vat = quarter.target_vat - vat_vat
        
        # Phase 3: Iterative cash sales generation
        cash_invoices = self._align_cash_sales(
            quarter.start_date,
            quarter.end_date,
            remaining_sales,
            remaining_vat
        )
        
        return vat_invoices + cash_invoices
        
    def _align_cash_sales(
        self,
        start_date: date,
        end_date: date,
        target_sales: Decimal,
        target_vat: Decimal
    ) -> List[Invoice]:
        """Iteratively adjust cash sales to hit target"""
        
        adjustment_factor = 1.0
        
        for iteration in range(self.max_iterations):
            # Generate all cash invoices for the period
            invoices = []
            current_date = start_date
            
            while current_date <= end_date:
                if self.simulation.is_working_day(current_date):
                    daily_invoices = self.simulation.generate_daily_sales(
                        current_date,
                        margin_multiplier=adjustment_factor,
                        invoice_type_filter=InvoiceType.SIMPLIFIED
                    )
                    invoices.extend(daily_invoices)
                current_date += timedelta(days=1)
            
            # Calculate actual totals
            actual_sales = sum(inv.subtotal for inv in invoices)
            actual_vat = sum(inv.vat_amount for inv in invoices)
            
            # Check convergence
            sales_diff = abs(actual_sales - target_sales)
            vat_diff = abs(actual_vat - target_vat)
            
            if sales_diff < self.tolerance and vat_diff < self.tolerance:
                logger.info(f"✅ Converged in {iteration} iterations")
                return invoices
            
            # Adjust strategy
            if actual_sales < target_sales:
                # Need MORE sales
                adjustment_factor *= 1.05  # Increase margins by 5%
            else:
                # Need LESS sales
                adjustment_factor *= 0.95  # Decrease margins by 5%
            
            logger.debug(
                f"Iteration {iteration}: "
                f"Target={target_sales:.2f}, "
                f"Actual={actual_sales:.2f}, "
                f"Diff={sales_diff:.2f}"
            )
        
        # Convergence failed - create final adjustment invoice
        logger.warning("Failed to converge, creating balancing invoice")
        return self._create_balancing_invoice(
            invoices,
            target_sales - actual_sales
        )
        
    def _create_balancing_invoice(
        self,
        existing_invoices: List[Invoice],
        adjustment_amount: Decimal
    ) -> List[Invoice]:
        """Create one final invoice to hit exact target"""
        # Pick random available item
        # Calculate quantity/price to hit exact amount
        # Return updated invoice list
```

---

### Module 5: Invoice Generation Service

**File:** `app/services/invoice_service.py`

**Responsibilities:**
- Create invoice records
- Generate invoice numbers
- Calculate totals & VAT
- Trigger PDF generation

**Key Functions:**
```python
class InvoiceService:
    def create_invoice(
        self,
        invoice_type: InvoiceType,
        customer_id: Optional[int],
        items: List[Tuple[Item, int, Decimal]],  # (item, qty, unit_price)
        invoice_date: datetime
    ) -> Invoice:
        """Create invoice with all calculations"""
        # Generate invoice number
        # Calculate line items
        # Calculate totals
        # Generate QR code data
        # Save to database
        # Return invoice object
        
    def generate_invoice_number(self, invoice_type: InvoiceType) -> str:
        """Generate sequential invoice number"""
        # Format: INV-SIMPLIFIED-000001 or INV-TAX-000001
        
    def generate_qr_data(self, invoice: Invoice) -> str:
        """Generate QR code content"""
        # Include: Invoice #, Seller name, Address, Tax number
        return f"INV:{invoice.invoice_number}|{SELLER_NAME}|{SELLER_ADDRESS}|{SELLER_TAX_NUMBER}"
```

---

### Module 6: PDF Generation

**File:** `app/pdf_generators/simplified_invoice.py`

**Arabic RTL Setup:**
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display

class ArabicPDFGenerator:
    def __init__(self):
        # Register Arabic font
        pdfmetrics.registerFont(
            TTFont('Arabic', 'fonts/Amiri-Regular.ttf')
        )
        
    def reshape_arabic(self, text: str) -> str:
        """Prepare Arabic text for PDF"""
        reshaped = reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
```

**Simplified Invoice (Thermal):**
```python
class SimplifiedInvoiceGenerator(ArabicPDFGenerator):
    def generate(self, invoice: Invoice) -> bytes:
        """Generate thermal receipt PDF"""
        # Size: 80mm width (thermal paper)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(80*mm, 297*mm))
        
        # Header
        c.setFont('Arabic', 14)
        y = 280*mm
        c.drawString(10*mm, y, self.reshape_arabic("مؤسسة رائد الإنجاز"))
        
        # Invoice details
        # Line items
        # Totals
        # QR code
        
        c.save()
        return buffer.getvalue()
```

**Tax Invoice (A4):**
```python
class TaxInvoiceGenerator(ArabicPDFGenerator):
    def generate(self, invoice: Invoice) -> bytes:
        """Generate A4 tax invoice PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Professional header with logo
        # Seller details (right-aligned Arabic)
        # Customer details
        # Table of items
        # Totals section
        # QR code
        # Footer
        
        c.save()
        return buffer.getvalue()
```

**QR Code Generation:**
```python
# app/utils/qr_generator.py
import qrcode
from PIL import Image

def generate_qr_code(data: str, size: int = 200) -> Image:
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img
```

---

### Module 7: Report Generation

**File:** `app/services/report_service.py`

**Detailed Sales Report:**
```python
def generate_detailed_report(
    start_date: date,
    end_date: date,
    filters: Optional[dict] = None
) -> pd.DataFrame:
    """Generate detailed line-by-line sales report"""
    # Query: invoice_lines JOIN invoices JOIN items
    # Columns: Invoice #, Date, Item, Unit Price, Qty, Subtotal, VAT, Total
    # Apply filters (date range, classification, customs declaration)
    # Return DataFrame for export
```

**Summary Report:**
```python
def generate_summary_report(
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """Generate invoice-level summary"""
    # Query: invoices table
    # Columns: Invoice #, Date, Subtotal, VAT, Total
    # Return DataFrame
```

**Quarterly Tax Report:**
```python
def generate_quarterly_tax_report(year: int, quarter: int) -> dict:
    """Generate tax return summary"""
    # Calculate Q1/Q2/Q3/Q4 totals
    # Return: {sales_before_vat, vat_amount, total_sales}
```

---

## 📅 4-DAY DEVELOPMENT PLAN

### **DAY 1: Foundation & Data Layer** (8-10 hours)

**Morning (4 hours):**
- [x] ✅ Project setup (virtual environment, dependencies)
- [x] ✅ Database schema design
- [x] ✅ Create all SQLAlchemy models
- [x] ✅ Setup FastAPI project structure
- [ ] 🔲 Configure environment variables
- [ ] 🔲 Setup Alembic migrations

**Afternoon (4-6 hours):**
- [ ] 🔲 Implement `ImportService`
- [ ] 🔲 Build Excel import API endpoints
- [ ] 🔲 Test with actual data files
- [ ] 🔲 Implement column mapping UI/API
- [ ] 🔲 Validate all 3 Excel files can be imported

**Evening (Optional 2 hours):**
- [ ] 🔲 Write unit tests for import service
- [ ] 🔲 Document API endpoints

**Deliverables:**
- ✅ Working database with all tables
- ✅ All 3 Excel files imported successfully
- ✅ API to upload & map Excel files

---

### **DAY 2: Business Logic Core** (8-10 hours)

**Morning (4 hours):**
- [ ] 🔲 Implement `InventoryService` (FIFO logic)
- [ ] 🔲 Write unit tests for FIFO deduction
- [ ] 🔲 Implement date utilities (Hijri conversion, holiday checker)
- [ ] 🔲 Create `SimulationConfig` dataclass

**Afternoon (4-6 hours):**
- [ ] 🔲 Implement `SimulationEngine` core functions:
  - `is_working_day()`
  - `calculate_boost_factor()`
  - `build_invoice_basket()`
  - `generate_daily_sales()`
- [ ] 🔲 Test simulation engine with small date range
- [ ] 🔲 Validate classification mixing rules work correctly

**Evening (Optional 2 hours):**
- [ ] 🔲 Write integration tests
- [ ] 🔲 Test boost calculations (Ramadan, salary days)

**Deliverables:**
- ✅ FIFO inventory system working
- ✅ Basic sales generation engine functional
- ✅ Classification rules enforced

---

### **DAY 3: Alignment Algorithm & PDF Generation** (8-10 hours)

**Morning (5 hours):**
- [ ] 🔲 Implement `AlignmentEngine`
- [ ] 🔲 Build iterative convergence algorithm
- [ ] 🔲 Test with Q3 2023 target (smallest quarter)
- [ ] 🔲 Iterate until convergence works reliably

**Afternoon (3-5 hours):**
- [ ] 🔲 Setup Arabic font in ReportLab
- [ ] 🔲 Implement `SimplifiedInvoiceGenerator` (thermal)
- [ ] 🔲 Implement `TaxInvoiceGenerator` (A4)
- [ ] 🔲 Integrate QR code generation
- [ ] 🔲 Generate 5 sample PDFs of each type

**Evening (Optional 2 hours):**
- [ ] 🔲 Test full alignment for all 6 quarters
- [ ] 🔲 Verify exact matches (±0.01 SAR)

**Deliverables:**
- ✅ Alignment algorithm converging for all quarters
- ✅ PDF generation working with Arabic RTL
- ✅ 10 sample invoices (5 simplified + 5 tax)

---

### **DAY 4: Reports, Testing & Polish** (8-10 hours)

**Morning (4 hours):**
- [ ] 🔲 Implement `ReportService`
- [ ] 🔲 Build detailed sales report (Excel/PDF export)
- [ ] 🔲 Build summary report
- [ ] 🔲 Build quarterly tax report
- [ ] 🔲 Test all report exports

**Afternoon (4 hours):**
- [ ] 🔲 Run full simulation for all 6 quarters
- [ ] 🔲 Verify exact quarterly matches
- [ ] 🔲 Generate complete documentation:
  - User manual (Arabic & English)
  - API documentation (Swagger)
  - Database schema diagram
  - Architecture diagram
- [ ] 🔲 Create 10+ sample invoice PDFs for demo

**Evening (2 hours):**
- [ ] 🔲 Bug fixes & edge cases
- [ ] 🔲 Performance testing (handle 10K+ invoices)
- [ ] 🔲 Final testing checklist
- [ ] 🔲 Prepare delivery package

**Deliverables:**
- ✅ All reports working (PDF/Excel export)
- ✅ Complete documentation
- ✅ 10+ sample invoice PDFs
- ✅ Verified exact quarterly matching
- ✅ Ready for deployment

---

## 🧪 TESTING STRATEGY

### Unit Tests (pytest)

```python
# tests/test_inventory.py
def test_fifo_deduction_single_batch():
    """Test FIFO deduction from single batch"""
    assert inventory.deduct_stock_fifo(item_id=1, quantity=10) == [(1, 10)]

def test_fifo_deduction_multiple_batches():
    """Test FIFO spanning multiple batches"""
    result = inventory.deduct_stock_fifo(item_id=1, quantity=150)
    assert len(result) == 2  # Used 2 batches
    
def test_insufficient_stock_raises_error():
    """Test error when stock insufficient"""
    with pytest.raises(InsufficientStockError):
        inventory.deduct_stock_fifo(item_id=1, quantity=10000)
```

```python
# tests/test_simulation.py
def test_friday_no_sales():
    """No sales should be generated on Friday"""
    friday = date(2023, 9, 29)  # A Friday
    invoices = simulation.generate_daily_sales(friday)
    assert len(invoices) == 0

def test_ramadan_boost():
    """Ramadan should have 2x boost"""
    ramadan_day = date(2024, 3, 15)  # During Ramadan 2024
    boost = simulation.calculate_boost_factor(ramadan_day)
    assert boost >= 2.0

def test_classification_mixing_outside_inspection():
    """Outside Inspection items must be alone"""
    basket = simulation.build_invoice_basket(
        invoice_type=InvoiceType.SIMPLIFIED
    )
    classifications = [item.classification for item, qty in basket]
    
    if ItemClassification.OUTSIDE_INSPECTION_NON_SELECTIVE in classifications:
        assert len(classifications) == 1  # Must be alone
```

```python
# tests/test_alignment.py
def test_quarter_alignment_q3_2023():
    """Test alignment for Q3 2023"""
    target = QuarterlyTarget(
        quarter="Q3-2023",
        start_date=date(2023, 7, 1),
        end_date=date(2023, 9, 30),
        target_sales=Decimal("341130.43"),
        target_vat=Decimal("51169.56")
    )
    
    invoices = alignment.align_quarter(target, customer_purchases=[])
    
    actual_sales = sum(inv.subtotal for inv in invoices)
    actual_vat = sum(inv.vat_amount for inv in invoices)
    
    assert abs(actual_sales - target.target_sales) < Decimal("0.01")
    assert abs(actual_vat - target.target_vat) < Decimal("0.01")
```

### Integration Tests

```python
# tests/test_full_workflow.py
def test_complete_workflow():
    """Test full workflow from import to invoice generation"""
    # Import Excel files
    import_service.import_products("data/products.xlsx", mapping)
    import_service.import_customers("data/customers.xlsx", mapping)
    import_service.import_holidays("data/holidays.xlsx")
    
    # Run simulation
    invoices = simulation_service.run_full_simulation(
        start_date=date(2023, 7, 1),
        end_date=date(2024, 12, 31)
    )
    
    # Verify quarterly targets
    q3_2023 = [inv for inv in invoices if inv.quarter == "Q3-2023"]
    assert sum(inv.subtotal for inv in q3_2023) == Decimal("341130.43")
    
    # Generate PDFs
    pdf_data = pdf_generator.generate(invoices[0])
    assert len(pdf_data) > 0  # PDF generated
    
    # Generate reports
    report = report_service.generate_detailed_report(
        date(2023, 7, 1), 
        date(2024, 12, 31)
    )
    assert len(report) > 0
```

---

## ⚠️ CRITICAL IMPLEMENTATION NOTES

### 1. Arabic RTL in PDFs

**Problem:** ReportLab doesn't natively support Arabic RTL

**Solution:**
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# Setup
pdfmetrics.registerFont(TTFont('Arabic', 'fonts/Amiri-Regular.ttf'))

# For every Arabic text:
arabic_text = "مؤسسة رائد الإنجاز للخدمات التجارية"
reshaped = reshape(arabic_text)
bidi_text = get_display(reshaped)

# Then use in PDF
canvas.setFont('Arabic', 12)
canvas.drawRightString(200*mm, y, bidi_text)  # Right-aligned
```

**Note:** As of ReportLab 4.4.0 (April 2025), experimental RTL support is included. Check if you can use native support.

### 2. Hijri Calendar Conversion

**For Ramadan detection:**
```python
from hijri_converter import Hijri, Gregorian

def is_ramadan(date: date) -> bool:
    """Check if Gregorian date falls in Ramadan"""
    hijri = Gregorian(date.year, date.month, date.day).to_hijri()
    return hijri.month == 9  # Ramadan is 9th month

def is_shaaban(date: date) -> bool:
    """Check if Gregorian date falls in Sha'ban"""
    hijri = Gregorian(date.year, date.month, date.day).to_hijri()
    return hijri.month == 8  # Sha'ban is 8th month
```

### 3. Convergence Algorithm Tuning

**If convergence is slow:**

```python
# Adaptive step size
def calculate_adjustment(iteration: int, diff: Decimal) -> float:
    """Calculate adaptive adjustment factor"""
    if iteration < 100:
        step = 0.05  # 5% steps early on
    elif iteration < 500:
        step = 0.02  # 2% steps mid-way
    else:
        step = 0.01  # 1% steps late
    
    # Increase/decrease based on diff magnitude
    if abs(diff) > 10000:
        step *= 2  # Larger steps for big gaps
    elif abs(diff) < 100:
        step *= 0.5  # Smaller steps when close
    
    return step
```

**Fallback strategy:**
```python
# If convergence fails after 1000 iterations
if iteration >= max_iterations:
    # Create ONE final balancing invoice
    adjustment_needed = target - actual
    
    # Pick a random available item
    item = random.choice(available_items)
    
    # Calculate exact quantity/price to hit target
    quantity = 10  # Fixed quantity
    unit_price = adjustment_needed / quantity / 1.15  # Reverse VAT calc
    
    # Create invoice with this exact pricing
    balancing_invoice = create_manual_invoice(item, quantity, unit_price)
    invoices.append(balancing_invoice)
```

### 4. Customer Purchase Allocation

**Problem:** 70 customers with specific purchase amounts must match quarterly targets

**Solution:**
```python
def allocate_customer_purchases(quarter: str) -> List[Invoice]:
    """Generate invoices for customers in this quarter"""
    customers = get_customers_for_quarter(quarter)
    invoices = []
    
    for customer in customers:
        # Create invoice on their purchase date
        items = select_non_selective_items()  # Only allowed type
        
        # IMPORTANT: Adjust margins to hit exact purchase amount
        target_subtotal = customer.purchase_amount / 1.15  # Remove VAT
        
        # Calculate how many items needed
        estimated_subtotal = sum(item.unit_price * random.randint(3, 40) 
                                 for item in items)
        
        # Adjust prices proportionally
        adjustment = target_subtotal / estimated_subtotal
        
        for item in items:
            item.adjusted_price = item.unit_price * adjustment
        
        invoice = create_invoice(customer, items)
        invoices.append(invoice)
    
    return invoices
```

### 5. Performance Optimization

**For handling 10K+ invoices:**

```python
# Batch inserts
from sqlalchemy.orm import Session

def bulk_create_invoices(invoices: List[Invoice], batch_size: int = 500):
    """Insert invoices in batches for performance"""
    session = get_db_session()
    
    for i in range(0, len(invoices), batch_size):
        batch = invoices[i:i+batch_size]
        session.bulk_save_objects(batch)
        session.commit()
        logger.info(f"Inserted batch {i//batch_size + 1}")
```

**Index optimization:**
```sql
-- Add indexes for frequently queried fields
CREATE INDEX idx_invoices_date ON invoices(invoice_date);
CREATE INDEX idx_batches_stock_date ON batches(stock_date);
CREATE INDEX idx_invoice_lines_invoice_id ON invoice_lines(invoice_id);
```

### 6. QR Code Specifications

**Saudi E-Invoicing QR Code Format:**
```python
def generate_saudi_einvoice_qr(invoice: Invoice) -> str:
    """Generate QR code per Saudi ZATCA standards"""
    # Base64 TLV (Tag-Length-Value) encoding
    
    def tlv_encode(tag: int, value: str) -> bytes:
        value_bytes = value.encode('utf-8')
        length = len(value_bytes)
        return bytes([tag, length]) + value_bytes
    
    # Required fields
    seller_name = tlv_encode(1, "مؤسسة رائد الإنجاز للخدمات التجارية")
    vat_number = tlv_encode(2, "302167780700003")
    timestamp = tlv_encode(3, invoice.invoice_date.isoformat())
    total_vat = tlv_encode(4, str(invoice.vat_amount))
    total = tlv_encode(5, str(invoice.total))
    
    # Concatenate all TLV values
    qr_data = seller_name + vat_number + timestamp + total_vat + total
    
    # Base64 encode
    import base64
    qr_string = base64.b64encode(qr_data).decode('utf-8')
    
    return qr_string
```

---

## 🚀 API ENDPOINTS REFERENCE

### Import Endpoints

```python
POST /api/import/products
Content-Type: multipart/form-data
Body: {
    file: products.xlsx,
    mapping: {...}  # Column mapping JSON
}

POST /api/import/customers
POST /api/import/holidays
```

### Simulation Endpoints

```python
POST /api/simulation/run
Body: {
    start_date: "2023-07-01",
    end_date: "2024-12-31",
    config: {
        ramadan_boost: 2.0,
        salary_day_27_boost: 1.5,
        ...
    }
}
Response: {
    status: "success",
    invoices_generated: 4523,
    quarterly_results: [
        {quarter: "Q3-2023", sales: 341130.43, vat: 51169.56, match: true},
        ...
    ]
}

GET /api/simulation/status
# Check progress of running simulation
```

### Invoice Endpoints

```python
GET /api/invoices?start_date=2023-07-01&end_date=2023-09-30
# List invoices with filters

GET /api/invoices/{invoice_id}
# Get single invoice details

GET /api/invoices/{invoice_id}/pdf
# Download invoice PDF

POST /api/invoices/bulk-generate-pdfs
Body: {invoice_ids: [1, 2, 3, ...]}
# Generate PDFs for multiple invoices
```

### Report Endpoints

```python
GET /api/reports/detailed?start_date=2023-07-01&end_date=2024-12-31&format=excel
# Download detailed sales report

GET /api/reports/summary?quarter=Q3-2023&format=pdf
# Download summary report

GET /api/reports/quarterly-tax?year=2024
# Get quarterly tax report
```

---

## 📦 DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] All tests passing (unit + integration)
- [ ] Database migrations prepared
- [ ] Environment variables documented
- [ ] Arabic fonts included in fonts/
- [ ] Sample data files provided
- [ ] API documentation complete (Swagger UI)

### Deliverables Package

```
delivery_package/
├── README.md                    # Installation & usage guide
├── ARCHITECTURE.md              # System architecture
├── API_DOCUMENTATION.md         # API reference
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── app/                         # Source code
├── fonts/                       # Arabic fonts
├── migrations/                  # Database migrations
├── sample_data/                 # Example Excel files
├── sample_output/
│   ├── invoices/                # 10 sample PDF invoices
│   ├── detailed_report.xlsx     # Sample detailed report
│   └── summary_report.pdf       # Sample summary report
└── tests/                       # Test suite
```

### Documentation to Include

**1. User Manual (English & Arabic)**
- How to import Excel files
- How to configure column mappings
- How to run simulation
- How to generate reports
- How to export invoices

**2. Technical Documentation**
- Architecture diagram
- Database schema
- API endpoints reference
- Configuration options
- Troubleshooting guide

**3. Sample Outputs**
- 5 simplified invoices (PDF)
- 5 tax invoices (PDF)
- Detailed sales report (Excel)
- Summary report (PDF)
- Quarterly tax report (JSON)

---

## 🔍 TROUBLESHOOTING GUIDE

### Issue: Convergence Not Working

**Symptoms:** Algorithm doesn't reach target after 1000 iterations

**Solutions:**
1. Reduce step size in adjustment factor
2. Check if inventory is sufficient
3. Verify classification rules aren't too restrictive
4. Use fallback balancing invoice

### Issue: Arabic Text Not Displaying

**Symptoms:** Arabic shows as black squares or reversed

**Solutions:**
1. Verify font is registered: `pdfmetrics.getFontNames()`
2. Check font file exists in fonts/ folder
3. Ensure using `reshape()` and `get_display()`
4. Use `drawRightString()` for right alignment

### Issue: FIFO Deduction Failing

**Symptoms:** "Insufficient stock" errors

**Solutions:**
1. Check batch dates are correct (import_date + 7-12 days)
2. Verify stock isn't being double-counted
3. Check for negative quantities in database
4. Review deduction logic in `deduct_stock_fifo()`

### Issue: Performance Slow with Large Datasets

**Symptoms:** Simulation takes >10 minutes

**Solutions:**
1. Add database indexes on date columns
2. Use bulk inserts (batch_size=500)
3. Reduce logging verbosity
4. Consider caching available items list

---

## 💰 PRICING JUSTIFICATION

**Recommended Quote: $2,500 - $3,000**

**Breakdown:**
- Day 1 (Foundation): $625 @ ~10 hours
- Day 2 (Business Logic): $625 @ ~10 hours
- Day 3 (Alignment & PDF): $750 @ ~10 hours (most complex)
- Day 4 (Reports & Polish): $625 @ ~10 hours

**Why This Price:**
- 40 hours × $62-75/hour
- Complex algorithmic challenge (alignment)
- Multiple specialized domains (inventory, tax, PDF, Arabic)
- Production-ready system with tests
- Complete documentation package

**Value Proposition:**
- Saves client from manual invoice generation
- Ensures 100% tax compliance
- Automated quarterly matching
- Professional Arabic PDF generation
- Scalable architecture for future enhancements

---

## 🎯 SUCCESS CRITERIA

### Functional Requirements ✅
- [x] Import 3 Excel files with column mapping
- [x] FIFO inventory system
- [x] Automated sales generation (seasonal/salary boosts)
- [x] Exact quarterly matching (±0.01 SAR)
- [x] Two invoice types (simplified + tax)
- [x] Arabic RTL support
- [x] QR code generation
- [x] Reports (detailed + summary)

### Non-Functional Requirements ✅
- [x] Handle 10K+ invoices without performance issues
- [x] All configurations editable without code changes
- [x] Comprehensive logging
- [x] Error handling & validation
- [x] Unit test coverage >70%
- [x] Complete documentation

### Acceptance Criteria ✅
- [x] All 6 quarterly targets matched exactly
- [x] VAT customers restricted to correct items
- [x] Selective items only in cash invoices
- [x] No sales on Fridays/holidays
- [x] 10 sample PDF invoices generated
- [x] Reports export to Excel/PDF

---

## 📚 ADDITIONAL RESOURCES

### Python Libraries Documentation
- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **ReportLab:** https://www.reportlab.com/docs/reportlab-userguide.pdf
- **arabic-reshaper:** https://github.com/mpcabd/python-arabic-reshaper
- **python-bidi:** https://github.com/MeirKriheli/python-bidi
- **qrcode:** https://pypi.org/project/qrcode/
- **pandas:** https://pandas.pydata.org/docs/

### Saudi E-Invoicing
- ZATCA E-Invoicing Portal: https://zatca.gov.sa/en/E-Invoicing/Pages/default.aspx
- E-Invoicing Technical Specifications (if available)

### Islamic Calendar
- **hijri-converter:** https://github.com/dralshehri/hijri-converter

---

## 🏁 FINAL NOTES

This implementation plan provides a **complete roadmap** for building the e-invoicing system in 4 days. The architecture is modular, scalable, and maintainable.

**Key Success Factors:**
1. Start with data layer (Day 1) - solid foundation
2. Build business logic incrementally (Day 2)
3. Focus on alignment algorithm early (Day 3) - hardest part
4. Leave buffer time for polish (Day 4)

**Risk Mitigation:**
- Alignment algorithm is the biggest risk - allocate extra time
- Arabic RTL can be tricky - test early with sample PDFs
- Customer purchase allocation needs careful handling

**Next Steps:**
1. Review this plan with the client
2. Confirm access to all 3 Excel files
3. Clarify any ambiguous requirements
4. Set up development environment
5. Start Day 1 implementation!

**Good luck! 🚀**