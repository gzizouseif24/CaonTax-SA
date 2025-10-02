import pandas as pd
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Read existing customers
df = pd.read_excel('input/customers.xlsx')

# Q3-2023 Target: 392,300 SAR total (341,130.43 before VAT + 51,169.57 VAT)
# Q4-2023 Target: 319,600 SAR total (277,913.04 before VAT + 41,686.96 VAT)

# Strategy: Allocate ~30% of Q3 and ~25% of Q4 to VAT customers
# Remainder will be cash sales

Q3_TARGET_TOTAL = 392_300
Q4_TARGET_TOTAL = 319_600

Q3_CUSTOMER_ALLOCATION = 0.30  # 30% from VAT customers
Q4_CUSTOMER_ALLOCATION = 0.25  # 25% from VAT customers

q3_customer_total = Q3_TARGET_TOTAL * Q3_CUSTOMER_ALLOCATION  # ~117,690 SAR
q4_customer_total = Q4_TARGET_TOTAL * Q4_CUSTOMER_ALLOCATION  # ~79,900 SAR

print("="*60)
print("2023 CUSTOMER FABRICATION PLAN")
print("="*60)

print(f"\nQ3-2023 (Jul-Sep):")
print(f"  Total target: {Q3_TARGET_TOTAL:,.0f} SAR")
print(f"  VAT customers: {q3_customer_total:,.0f} SAR ({Q3_CUSTOMER_ALLOCATION*100:.0f}%)")
print(f"  Cash sales: {Q3_TARGET_TOTAL - q3_customer_total:,.0f} SAR ({(1-Q3_CUSTOMER_ALLOCATION)*100:.0f}%)")

print(f"\nQ4-2023 (Oct-Dec):")
print(f"  Total target: {Q4_TARGET_TOTAL:,.0f} SAR")
print(f"  VAT customers: {q4_customer_total:,.0f} SAR ({Q4_CUSTOMER_ALLOCATION*100:.0f}%)")
print(f"  Cash sales: {Q4_TARGET_TOTAL - q4_customer_total:,.0f} SAR ({(1-Q4_CUSTOMER_ALLOCATION)*100:.0f}%)")

# Select random customers for 2023
# Use first 15 customers for variety
num_q3_customers = 8
num_q4_customers = 6

q3_customers = df.head(num_q3_customers).copy()
q4_customers = df.iloc[num_q3_customers:num_q3_customers+num_q4_customers].copy()

print(f"\n\nAssigning customers:")
print(f"  Q3-2023: {num_q3_customers} customers")
print(f"  Q4-2023: {num_q4_customers} customers")

# Generate Q3 purchase amounts (distribute q3_customer_total among customers)
# Random amounts between 10k and 25k
q3_amounts = []
remaining = q3_customer_total
for i in range(num_q3_customers - 1):
    # Random amount between 10k and min(25k, remaining/2)
    max_amount = min(25000, remaining / 2)
    amount = random.uniform(10000, max_amount)
    q3_amounts.append(round(amount, 2))
    remaining -= amount

# Last customer gets the remainder
q3_amounts.append(round(remaining, 2))
random.shuffle(q3_amounts)

# Generate Q3 purchase dates (July-September 2023)
q3_dates = []
for _ in range(num_q3_customers):
    # Random date in Jul-Sep 2023, weighted towards salary days
    month = random.choice([7, 8, 9])
    if random.random() < 0.4:  # 40% chance of salary day
        day = random.choice([1, 10, 27])
    else:
        day = random.randint(1, 28)
    
    try:
        date = datetime(2023, month, day)
        q3_dates.append(date.strftime('%d/%m/%Y'))
    except:
        date = datetime(2023, month, 15)
        q3_dates.append(date.strftime('%d/%m/%Y'))

# Generate Q4 purchase amounts
q4_amounts = []
remaining = q4_customer_total
for i in range(num_q4_customers - 1):
    max_amount = min(20000, remaining / 2)
    amount = random.uniform(8000, max_amount)
    q4_amounts.append(round(amount, 2))
    remaining -= amount

q4_amounts.append(round(remaining, 2))
random.shuffle(q4_amounts)

# Generate Q4 purchase dates (October-December 2023)
q4_dates = []
for _ in range(num_q4_customers):
    month = random.choice([10, 11, 12])
    if random.random() < 0.4:
        day = random.choice([1, 10, 27])
    else:
        day = random.randint(1, 28)
    
    try:
        date = datetime(2023, month, day)
        q4_dates.append(date.strftime('%d/%m/%Y'))
    except:
        date = datetime(2023, month, 15)
        q4_dates.append(date.strftime('%d/%m/%Y'))

# Create 2023 customer dataframe
customers_2023 = []

# Add Q3 customers
for idx, (_, row) in enumerate(q3_customers.iterrows()):
    customer = {
        'customer_name': row['customer_name'],
        'tax_id': row['tax_id'],
        'commercial_registration': row['commercial_registration'],
        'adress ': row['adress '],  # Note the space in column name
        'purchase_amount': q3_amounts[idx],
        'purchase_date': q3_dates[idx]
    }
    customers_2023.append(customer)

# Add Q4 customers
for idx, (_, row) in enumerate(q4_customers.iterrows()):
    customer = {
        'customer_name': row['customer_name'],
        'tax_id': row['tax_id'],
        'commercial_registration': row['commercial_registration'],
        'adress ': row['adress '],
        'purchase_amount': q4_amounts[idx],
        'purchase_date': q4_dates[idx]
    }
    customers_2023.append(customer)

df_2023 = pd.DataFrame(customers_2023)

# Display summary
print("\n" + "="*60)
print("GENERATED 2023 CUSTOMERS")
print("="*60)
print(f"\nTotal customers: {len(df_2023)}")
print(f"Total amount: {df_2023['purchase_amount'].sum():,.2f} SAR")

print("\nQ3-2023 breakdown:")
q3_df = df_2023[pd.to_datetime(df_2023['purchase_date'], format='%d/%m/%Y') < '2023-10-01']
print(f"  Customers: {len(q3_df)}")
print(f"  Amount: {q3_df['purchase_amount'].sum():,.2f} SAR")

print("\nQ4-2023 breakdown:")
q4_df = df_2023[pd.to_datetime(df_2023['purchase_date'], format='%d/%m/%Y') >= '2023-10-01']
print(f"  Customers: {len(q4_df)}")
print(f"  Amount: {q4_df['purchase_amount'].sum():,.2f} SAR")

print("\nSample customers:")
print(df_2023[['customer_name', 'purchase_amount', 'purchase_date']].head(10))

# Save to new Excel file
output_file = 'input/customers_2023_fabricated.xlsx'
df_2023.to_excel(output_file, index=False)
print(f"\n✓ Saved to: {output_file}")

print("\n" + "="*60)
print("CASH SALES REQUIREMENTS")
print("="*60)
print(f"\nQ3-2023 cash sales needed: {Q3_TARGET_TOTAL - q3_df['purchase_amount'].sum():,.2f} SAR")
print(f"Q4-2023 cash sales needed: {Q4_TARGET_TOTAL - q4_df['purchase_amount'].sum():,.2f} SAR")