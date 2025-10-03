from excel_reader import read_products
from inventory import InventoryManager
from collections import defaultdict

# Load products
products = read_products('input/products.xlsx')

# Group by item name to see if there are multiple batches with different prices
item_groups = defaultdict(list)
for product in products:
    item_groups[product['item_name']].append(product)

print("CHECKING FOR MULTIPLE BATCHES WITH DIFFERENT PRICES")
print("="*60)

items_with_multiple_prices = []

for item_name, batches in item_groups.items():
    if len(batches) > 1:
        # Check if prices are different
        prices = [batch['unit_price_before_vat'] for batch in batches]
        unique_prices = set(prices)
        
        if len(unique_prices) > 1:
            items_with_multiple_prices.append({
                'item_name': item_name,
                'batch_count': len(batches),
                'prices': prices,
                'stock_dates': [batch['stock_date'] for batch in batches]
            })

print(f"Found {len(items_with_multiple_prices)} items with multiple prices:")
print()

for item in items_with_multiple_prices[:10]:  # Show first 10
    print(f"Item: {item['item_name']}")
    print(f"  Batches: {item['batch_count']}")
    print(f"  Prices: {[float(p) for p in item['prices']]}")
    print(f"  Stock Dates: {item['stock_dates']}")
    print()

if items_with_multiple_prices:
    print(f"\n🔍 FOUND THE ISSUE!")
    print(f"There are {len(items_with_multiple_prices)} items with multiple batches having different prices.")
    print(f"The FIFO system is using the oldest batch price, which may differ from the expected price.")
    print(f"This explains the price mismatches in validation!")
else:
    print("✅ All items have consistent prices across batches.")