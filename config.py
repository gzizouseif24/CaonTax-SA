from decimal import Decimal
from datetime import date

# ============================================================
# QUARTERLY TARGETS (Sales Inc VAT - from tax returns)
# ============================================================
# NOTE: "sales" field now represents TOTAL sales INCLUDING VAT
# This matches the PRD requirement for sales_inc_vat
# Legacy code may expect separate sales/vat fields - use compatibility layer
QUARTERLY_TARGETS = {
    "Q3-2023": {
        "sales_inc_vat": Decimal("392299.99"),  # PRD-compliant name
        "sales": Decimal("392299.99"),          # Legacy compatibility
        "period_start": date(2023, 7, 1),       # PRD-compliant name
        "period_end": date(2023, 9, 30),        # PRD-compliant name
        "start": date(2023, 7, 1),              # Legacy compatibility
        "end": date(2023, 9, 30),               # Legacy compatibility
        "allow_variance": True                   # 2023: Best effort (Q3 has minimal inventory)
    },
    "Q4-2023": {
        "sales_inc_vat": Decimal("319600.00"),
        "sales": Decimal("319600.00"),
        "period_start": date(2023, 10, 1),
        "period_end": date(2023, 12, 31),
        "start": date(2023, 10, 1),
        "end": date(2023, 12, 31),
        "allow_variance": True                   # 2023: Best effort
    },
    "Q1-2024": {
        "sales_inc_vat": Decimal("1053833.24"),
        "sales": Decimal("1053833.24"),
        "period_start": date(2024, 1, 1),
        "period_end": date(2024, 3, 31),
        "start": date(2024, 1, 1),
        "end": date(2024, 3, 31),
        "allow_variance": False                  # 2024: Strict matching
    },
    "Q2-2024": {
        "sales_inc_vat": Decimal("1393727.32"),
        "sales": Decimal("1393727.32"),
        "period_start": date(2024, 4, 1),
        "period_end": date(2024, 6, 30),
        "start": date(2024, 4, 1),
        "end": date(2024, 6, 30),
        "allow_variance": False                  # 2024: Strict matching
    },
    "Q3-2024": {
        "sales_inc_vat": Decimal("2333442.00"),
        "sales": Decimal("2333442.00"),
        "period_start": date(2024, 7, 1),
        "period_end": date(2024, 9, 30),
        "start": date(2024, 7, 1),
        "end": date(2024, 9, 30),
        "allow_variance": False                  # 2024: Strict matching
    },
    "Q4-2024": {
        "sales_inc_vat": Decimal("892647.25"),
        "sales": Decimal("892647.25"),
        "period_start": date(2024, 10, 1),
        "period_end": date(2024, 12, 31),
        "start": date(2024, 10, 1),
        "end": date(2024, 12, 31),
        "allow_variance": False                  # 2024: Strict matching
    }
}

# ============================================================
# SELLER INFORMATION (Fixed for all invoices)
# ============================================================
SELLER_NAME = "مؤسسة رائد الإنجاز للخدمات التجارية"
SELLER_ADDRESS = "الرياض، السلي 14322"
SELLER_PHONE = "0555866344"
SELLER_EMAIL = "M.ALSHAIKHI1993@GMAIL.COM"
SELLER_TAX_NUMBER = "302167780700003"

# ============================================================
# TAX & PRICING
# ============================================================
VAT_RATE = Decimal("0.15")  # 15% VAT

# ============================================================
# ITEM CLASSIFICATIONS (shipment_class values)
# ============================================================
# PRD specifies: EXC_INSPECTION, NONEXC_INSPECTION, NONEXC_OUTSIDE
# Our Arabic equivalents:
OUTSIDE_INSPECTION = "خارج حالة الفحص غير انتقائية"     # NONEXC_OUTSIDE in PRD
UNDER_NON_SELECTIVE = "محل الفحص سلع غير انتقائية"     # NONEXC_INSPECTION in PRD
UNDER_SELECTIVE = "محل الفحص سلع انتقائية"             # EXC_INSPECTION in PRD

# PRD-compliant names (for reference)
EXC_INSPECTION = UNDER_SELECTIVE          # Excise/selective goods
NONEXC_INSPECTION = UNDER_NON_SELECTIVE   # Non-excise under inspection
NONEXC_OUTSIDE = OUTSIDE_INSPECTION       # Non-excise outside inspection

# Classification mapping
CLASSIFICATION_MAP = {
    OUTSIDE_INSPECTION: "NONEXC_OUTSIDE",
    UNDER_NON_SELECTIVE: "NONEXC_INSPECTION",
    UNDER_SELECTIVE: "EXC_INSPECTION"
}

# ============================================================
# SIMULATION SETTINGS
# ============================================================
# Seasonal boosts
RAMADAN_BOOST = 2.0
SHAABAN_BOOST = 2.0

# Salary day boosts
SALARY_DAY_27_BOOST = 1.5  # Highest
SALARY_DAY_1_BOOST = 1.2   # Medium
SALARY_DAY_10_BOOST = 1.1  # Lower

# Working days (0=Monday, 4=Friday, 6=Sunday)
WORKING_DAYS = [0, 1, 2, 3, 5, 6]  # Saturday-Thursday (no Friday)
WORKING_HOURS = (9, 22)  # 9 AM to 10 PM

# Invoice basket settings
MIN_ITEMS_PER_INVOICE = 2
MAX_ITEMS_PER_INVOICE = 10
MIN_QUANTITY_PER_ITEM = 3
MAX_QUANTITY_PER_ITEM = 40

# ============================================================
# INVENTORY SETTINGS
# ============================================================
# Days to add to import_date to get stock_date
MIN_STOCK_DELAY = 7
MAX_STOCK_DELAY = 12

# ============================================================
# ALIGNMENT ALGORITHM SETTINGS
# ============================================================
MAX_ITERATIONS = 1000
TOLERANCE = Decimal("0.10")  # Match within ±0.01 SAR
ADJUSTMENT_STEP = 0.05  # 5% price adjustments per iteration

# ============================================================
# INVOICE SETTINGS
# ============================================================
CASH_CUSTOMER_NAME = "عميل نقدي"