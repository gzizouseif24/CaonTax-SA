from decimal import Decimal
from datetime import date

# ============================================================
# QUARTERLY TARGETS (Exact amounts from tax returns)
# ============================================================
QUARTERLY_TARGETS = {
    "Q3-2023": {
        "sales": Decimal("392299.99"),
        "start": date(2023, 7, 1),
        "end": date(2023, 9, 30)
    },
    "Q4-2023": {
        "sales": Decimal("319600.00"),
        "start": date(2023, 10, 1),
        "end": date(2023, 12, 31)
    },
    "Q1-2024": {
        "sales": Decimal("1053833.24"),
        "start": date(2024, 1, 1),
        "end": date(2024, 3, 31)
    },
    "Q2-2024": {
        "sales": Decimal("1393727.32"),
        "start": date(2024, 4, 1),
        "end": date(2024, 6, 30)
    },
    "Q3-2024": {
        "sales": Decimal("2333442.00"),
        "start": date(2024, 7, 1),
        "end": date(2024, 9, 30)
    },
    "Q4-2024": {
        "sales": Decimal("892647.25"),
        "start": date(2024, 10, 1),
        "end": date(2024, 12, 31)
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
# ITEM CLASSIFICATIONS (Arabic names from Excel)
# ============================================================
OUTSIDE_INSPECTION = "خارج حالة الفحص غير انتقائية"
UNDER_NON_SELECTIVE = "محل الفحص سلع غير انتقائية"
UNDER_SELECTIVE = "محل الفحص سلع انتقائية"

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