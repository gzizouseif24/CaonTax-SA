import pandas as pd
from datetime import datetime, timedelta
import random

print("="*60)
print("FIXING PRODUCT IMPORT DATES")
print("="*60)

# Read current products
df = pd.read_excel('input/products.xlsx')

print(f"\nLoaded {len(df)} products")

# Check current import dates
df['import_date'] = pd.to_datetime(df['import_date'])
print(f"Current date range: {df['import_date'].min()} to {df['import_date'].max()}")

# Define new date range
# Start from June 2023 (before Q3-2023 starts)
# End at September 2024 (covers all your quarters)
start_date = datetime(2023, 6, 1)
end_date = datetime(2024, 9, 30)
total_days = (end_date - start_date).days

print(f"\nNew date range: {start_date.date()} to {end_date.date()}")
print(f"Distributing {len(df)} products across {total_days} days")

# Distribute products evenly across the timeframe
# Group them in batches (like real import shipments)
num_batches = 15  # ~15 shipments over 16 months
products_per_batch = len(df) // num_batches

new_dates = []
current_batch = 0

for i in range(len(df)):
    # Determine which batch this product belongs to
    batch_num = i // products_per_batch
    
    if batch_num >= num_batches:
        batch_num = num_batches - 1
    
    # Calculate batch date (evenly spaced)
    days_per_batch = total_days // num_batches
    batch_date = start_date + timedelta(days=batch_num * days_per_batch)
    
    # Add random variance within batch (±7 days)
    variance = random.randint(-7, 7)
    product_date = batch_date + timedelta(days=variance)
    
    # Ensure date is within bounds
    if product_date < start_date:
        product_date = start_date
    if product_date > end_date:
        product_date = end_date
    
    new_dates.append(product_date)

# Update the dataframe
df['import_date'] = new_dates

# Convert to Excel-friendly date format
df['import_date'] = df['import_date'].dt.strftime('%d/%m/%Y')

# Verify distribution
df_temp = df.copy()
df_temp['import_date'] = pd.to_datetime(df_temp['import_date'], format='%d/%m/%Y')

print("\n" + "="*60)
print("DISTRIBUTION BY QUARTER")
print("="*60)

quarters = [
    ('Q3-2023', '2023-07-01', '2023-09-30'),
    ('Q4-2023', '2023-10-01', '2023-12-31'),
    ('Q1-2024', '2024-01-01', '2024-03-31'),
    ('Q2-2024', '2024-04-01', '2024-06-30'),
    ('Q3-2024', '2024-07-01', '2024-09-30'),
    ('Q4-2024', '2024-10-01', '2024-12-31'),
]

for quarter_name, start, end in quarters:
    count = len(df_temp[(df_temp['import_date'] >= start) & (df_temp['import_date'] <= end)])
    print(f"{quarter_name}: {count} products imported")

# Save to new file
output_file = 'input/products_fixed_dates.xlsx'
df.to_excel(output_file, index=False)

print("\n" + "="*60)
print(f"✓ Saved to: {output_file}")
print("="*60)

print("\nNext steps:")
print("1. Verify the new file looks correct")
print("2. Backup your original: mv products.xlsx products_original.xlsx")
print("3. Use new file: mv products_fixed_dates.xlsx products.xlsx")
print("4. Re-run test_alignment.py")