from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import date


class InventoryManager:
    """
    Manages inventory with FIFO (First In, First Out) logic.
    All inventory is stored in memory as a list of product dictionaries.
    """
    
    def __init__(self, products: List[Dict]):
        """
        Initialize inventory with products from Excel.
        
        Args:
            products: List of product dictionaries from read_products()
        """
        self.products = products
        print(f"Inventory initialized with {len(products)} product batches")
    
    def get_available_items_by_classification(self, classification: str) -> List[Dict]:
        """
        Get all items with available stock for a specific classification.
        Returns ONE record per unique item (not per batch).
        
        Args:
            classification: One of the three classification types
            
        Returns:
            List of product dictionaries (one per unique item name)
        """
        available = [
            p for p in self.products 
            if p['classification'] == classification and p['quantity_remaining'] > 0
        ]
        
        # Group by item_name and return only ONE record per item
        # Use the first available batch as the representative
        seen_items = {}
        unique_items = []
        
        for product in available:
            item_name = product['item_name']
            if item_name not in seen_items:
                seen_items[item_name] = True
                unique_items.append(product)
        
        return unique_items
    
    def get_all_available_items(self) -> List[Dict]:
        """
        Get all items with available stock (any classification).
        Returns ONE record per unique item (not per batch).
        
        Returns:
            List of product dictionaries (one per unique item name)
        """
        available = [p for p in self.products if p['quantity_remaining'] > 0]
        
        # Group by item_name and return only ONE record per item
        seen_items = {}
        unique_items = []
        
        for product in available:
            item_name = product['item_name']
            if item_name not in seen_items:
                seen_items[item_name] = True
                unique_items.append(product)
        
        return unique_items
    
    def get_available_quantity(self, item_name: str) -> int:
        """
        Get total available quantity for an item across all batches.
        
        Args:
            item_name: Name of the item
            
        Returns:
            Total quantity available
        """
        total = sum(
            p['quantity_remaining'] 
            for p in self.products 
            if p['item_name'] == item_name
        )
        return total
    
    def get_unit_price(self, item_name: str) -> Decimal:
        """
        Get unit price from the oldest available batch (FIFO).
        
        Args:
            item_name: Name of the item
            
        Returns:
            Unit price before VAT from oldest batch
        """
        # Find all batches for this item with stock
        available_batches = [
            p for p in self.products 
            if p['item_name'] == item_name and p['quantity_remaining'] > 0
        ]
        
        if not available_batches:
            raise ValueError(f"No stock available for item: {item_name}")
        
        # Sort by stock_date (oldest first = FIFO)
        available_batches.sort(key=lambda x: x['stock_date'])
        
        # Return price from oldest batch
        return available_batches[0]['unit_price_before_vat']
    
    def deduct_stock(self, item_name: str, quantity: int) -> List[Tuple[str, int, Decimal]]:
        """
        Deduct quantity from inventory using FIFO.
        
        Args:
            item_name: Name of the item
            quantity: Quantity to deduct
            
        Returns:
            List of tuples: (customs_declaration, qty_deducted, unit_price)
            
        Raises:
            ValueError: If insufficient stock
        """
        # Check if enough stock available
        available = self.get_available_quantity(item_name)
        if available < quantity:
            raise ValueError(
                f"Insufficient stock for {item_name}. "
                f"Requested: {quantity}, Available: {available}"
            )
        
        # Find all batches for this item with stock
        available_batches = [
            p for p in self.products 
            if p['item_name'] == item_name and p['quantity_remaining'] > 0
        ]
        
        # Sort by stock_date (oldest first = FIFO)
        available_batches.sort(key=lambda x: x['stock_date'])
        
        # Deduct from oldest batches first
        remaining_to_deduct = quantity
        deductions = []
        
        for batch in available_batches:
            if remaining_to_deduct <= 0:
                break
            
            # How much can we take from this batch?
            qty_from_batch = min(remaining_to_deduct, batch['quantity_remaining'])
            
            # Deduct it
            batch['quantity_remaining'] -= qty_from_batch
            remaining_to_deduct -= qty_from_batch
            
            # Record the deduction
            deductions.append((
                batch['customs_declaration'],
                qty_from_batch,
                batch['unit_price_before_vat']
            ))
        
        return deductions
    
    def check_stock_available(self, item_name: str, quantity: int) -> bool:
        """
        Check if sufficient stock is available without deducting.
        
        Args:
            item_name: Name of the item
            quantity: Quantity needed
            
        Returns:
            True if stock is available, False otherwise
        """
        available = self.get_available_quantity(item_name)
        return available >= quantity
    
    def get_inventory_summary(self) -> Dict:
        """
        Get summary statistics about current inventory.
        
        Returns:
            Dictionary with inventory stats
        """
        total_items = len(self.products)
        items_with_stock = len([p for p in self.products if p['quantity_remaining'] > 0])
        items_depleted = total_items - items_with_stock
        total_quantity = sum(p['quantity_remaining'] for p in self.products)
        
        return {
            'total_batches': total_items,
            'batches_with_stock': items_with_stock,
            'batches_depleted': items_depleted,
            'total_quantity_remaining': total_quantity
        }
    
    def get_items_by_classification_count(self) -> Dict[str, int]:
        """
        Count available items by classification.
        
        Returns:
            Dictionary: {classification: count_of_items_with_stock}
        """
        from collections import defaultdict
        counts = defaultdict(int)
        
        for p in self.products:
            if p['quantity_remaining'] > 0:
                counts[p['classification']] += 1
        
        return dict(counts)