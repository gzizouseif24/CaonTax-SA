import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import random
from config import MIN_STOCK_DELAY, MAX_STOCK_DELAY


def read_products(file_path):
    """
    Read products Excel file with ENGLISH column names.
    """
    print(f"Reading products from {file_path}...")
    
    df = pd.read_excel(file_path)
    
    # Remove any unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Strip whitespace from column names (fix trailing spaces)
    df.columns = df.columns.str.strip()
    
    # Print columns to verify
    print(f"Found columns: {list(df.columns)}")
    
    products = []
    
    for idx, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['item_name']):
            continue
            
        # Extract values
        item_name = str(row['item_name']).strip()
        
        # Handle import date
        import_date = row['import_date']
        if pd.isna(import_date):
            print(f"  Warning: Skipping row {idx} - no import date")
            continue
            
        if isinstance(import_date, (int, float)):
            # Excel date serial
            import_date = datetime(1899, 12, 30) + timedelta(days=int(import_date))
        elif isinstance(import_date, str):
            # Parse string date
            try:
                import_date = datetime.strptime(import_date, '%d/%m/%Y')
            except:
                try:
                    import_date = datetime.strptime(import_date, '%Y-%m-%d')
                except:
                    print(f"  Warning: Could not parse date '{import_date}' at row {idx}")
                    continue
        
        import_date = import_date.date()
        
        # Calculate stock date (import + 7-12 random days)
        # SPECIAL: For 2023 Q3, ignore delays to enable sales
        stock_date = import_date + timedelta(days=0)  # Changed from 10 to 0
        
        # Get quantity
        quantity_val = row['quantity']
        if pd.isna(quantity_val):
            print(f"  Warning: Skipping row {idx} - no quantity")
            continue
        quantity = int(quantity_val)
        
        # Get total cost
        total_cost_val = row['total_cost']
        if pd.isna(total_cost_val):
            print(f"  Warning: Skipping row {idx} - no total cost")
            continue
        total_cost = Decimal(str(total_cost_val))
        
        # Get profit margin
        profit_margin_val = row['profit_margin_pct']
        if pd.isna(profit_margin_val):
            profit_margin_pct = Decimal("15")  # Default 15%
        else:
            profit_margin_pct = Decimal(str(profit_margin_val))
        
        # Calculate unit cost
        unit_cost = total_cost / quantity
        
        # READ unit price from Excel (don't calculate it!)
        unit_price_val = row['unit_price_before_vat']
        if pd.isna(unit_price_val):
            # Fallback: calculate if not in Excel
            unit_price_before_vat = unit_cost * (1 + profit_margin_pct / 100)
        else:
            # Use the EXACT price from Excel
            unit_price_before_vat = Decimal(str(unit_price_val))
        
        # Get classification
        classification = str(row['classification']).strip().replace('  ', ' ')  # Replace double spaces with single        
        product = {
            'item_name': item_name,
            'customs_declaration': str(row['customs_declaration']),
            'classification': classification,
            'import_date': import_date,
            'stock_date': stock_date,
            'quantity_imported': quantity,
            'quantity_remaining': quantity,
            'unit_cost': unit_cost,
            'unit_price_before_vat': unit_price_before_vat,
            'profit_margin_pct': profit_margin_pct
        }
        
        products.append(product)
    
    print(f"✓ Loaded {len(products)} products")
    return products


def read_customers(file_path):
    """
    Read VAT customers Excel file with ENGLISH column names.
    """
    print(f"Reading customers from {file_path}...")
    
    df = pd.read_excel(file_path)
    
    # Remove unnamed columns and strip whitespace from column names
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = df.columns.str.strip()
    
    print(f"Found columns: {list(df.columns)}")
    
    customers = []
    
    for idx, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['customer_name']):
            continue
            
        # Parse purchase date
        purchase_date = row['purchase_date']
        if pd.isna(purchase_date):
            continue
            
        if isinstance(purchase_date, str):
            try:
                purchase_date = datetime.strptime(purchase_date, '%d/%m/%Y').date()
            except:
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        elif isinstance(purchase_date, (int, float)):
            purchase_date = (datetime(1899, 12, 30) + timedelta(days=int(purchase_date))).date()
        else:
            purchase_date = purchase_date.date()
        
        # Handle both 'tax_number' and 'tax_id' column names
        tax_number_col = 'tax_number' if 'tax_number' in df.columns else 'tax_id'
        
        # Handle both 'address' and 'adress' (typo)
        address_col = 'address' if 'address' in df.columns else 'adress'
        
        customer = {
            'customer_name': str(row['customer_name']).strip(),
            'tax_number': str(row[tax_number_col]).strip(),
            'commercial_registration': str(row.get('commercial_registration', '')).strip(),
            'address': str(row.get(address_col, '')).strip(),
            'purchase_amount': Decimal(str(row['purchase_amount'])),
            'purchase_date': purchase_date
        }
        
        customers.append(customer)
    
    print(f"✓ Loaded {len(customers)} VAT customers")
    return customers


def read_holidays(file_path):
    """
    Read holidays Excel file.
    """
    print(f"Reading holidays from {file_path}...")
    
    df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
    
    holidays = []
    
    for sheet_name, sheet_df in df.items():
        print(f"  Reading sheet: {sheet_name}")
        
        # Strip whitespace from column names
        sheet_df.columns = sheet_df.columns.str.strip()
        
        print(f"    Columns: {list(sheet_df.columns)}")
        
        # Find date column
        date_col = 'Date'  # Your file uses 'Date'
        
        if date_col not in sheet_df.columns:
            print(f"    Warning: Could not find Date column")
            continue
        
        print(f"    Using date column: {date_col}")
        print(f"    Total rows: {len(sheet_df)}")
        
        for idx, row in sheet_df.iterrows():
            holiday_date = row[date_col]
            
            # Debug: print first few
            if idx < 3:
                print(f"      Row {idx}: {holiday_date} (type: {type(holiday_date)})")
            
            if pd.isna(holiday_date):
                continue
            
            # Try to convert to date
            try:
                if isinstance(holiday_date, str):
                    # Try multiple date formats
                    formats_to_try = [
                        '%d/%m/%Y',      # 22/02/2024
                        '%Y-%m-%d',      # 2024-02-22
                        '%b %d, %Y',     # Feb 22, 2024
                        '%B %d, %Y',     # February 22, 2024
                        '%m/%d/%Y',      # 02/22/2024
                    ]
                    
                    parsed = False
                    for fmt in formats_to_try:
                        try:
                            holiday_date = datetime.strptime(holiday_date, fmt).date()
                            parsed = True
                            break
                        except:
                            continue
                    
                    if not parsed:
                        if idx < 3:
                            print(f"      Could not parse date format: {holiday_date}")
                        continue
                elif isinstance(holiday_date, (int, float)):
                    holiday_date = (datetime(1899, 12, 30) + timedelta(days=int(holiday_date))).date()
                elif hasattr(holiday_date, 'date'):
                    # It's already a datetime object
                    holiday_date = holiday_date.date()
                else:
                    # Try direct conversion
                    holiday_date = pd.to_datetime(holiday_date).date()
                
                holidays.append(holiday_date)
            except Exception as e:
                if idx < 3:
                    print(f"      Error converting: {e}")
                continue
    
    print(f"✓ Loaded {len(holidays)} holidays")
    return holidays