from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from datetime import date


class InventoryManager:
    """
    Manages inventory with LOT-BASED FIFO (First In, First Out) logic.
    Each lot (customs_declaration_no:item_description) is tracked separately.
    PRD-compliant: Supports lot_id-based pricing and deduction.
    """

    def __init__(self, products: List[Dict]):
        """
        Initialize inventory with products from Excel.
        Each product is a unique LOT with its own pricing.

        Args:
            products: List of product lot dictionaries from read_products()
        """
        self.products = products

        # Build lot_id index for fast lookup
        self.lot_index = {p['lot_id']: p for p in products}

        unique_lots = len(set(p['lot_id'] for p in products))
        unique_items = len(set(p['item_description'] for p in products))

        print(f"Inventory initialized with {len(products)} product lots")
        print(f"  Unique lot_ids: {unique_lots}")
        print(f"  Unique items: {unique_items}")

    def get_available_lots_by_classification(self, classification: str, current_date: date = None) -> List[Dict]:
        """
        Get ALL available lots for a specific classification.
        Returns LOTS (not deduplicated items) - each lot is separate.

        Args:
            classification: One of the three shipment_class types
            current_date: Optional date filter (only lots with stock_date <= current_date)

        Returns:
            List of lot dictionaries (one per lot, NOT aggregated)
        """
        available = [
            p for p in self.products
            if p['shipment_class'] == classification and p['qty_remaining'] > 0
        ]

        # Filter by stock date if provided
        if current_date:
            available = [p for p in available if p['stock_date'] <= current_date]

        return available

    def get_all_available_lots(self, current_date: date = None) -> List[Dict]:
        """
        Get ALL available lots (any classification).
        Returns LOTS (not deduplicated items) - each lot is separate.

        Args:
            current_date: Optional date filter (only lots with stock_date <= current_date)

        Returns:
            List of lot dictionaries (one per lot, NOT aggregated)
        """
        available = [p for p in self.products if p['qty_remaining'] > 0]

        # Filter by stock date if provided
        if current_date:
            available = [p for p in available if p['stock_date'] <= current_date]

        return available

    def get_lots_for_item(self, item_description: str) -> List[Dict]:
        """
        Get ALL lots for a given item_description, sorted by FIFO order.

        Args:
            item_description: The item name/description

        Returns:
            List of lots sorted by stock_date (oldest first)
        """
        lots = [
            p for p in self.products
            if p['item_description'] == item_description and p['qty_remaining'] > 0
        ]

        # Sort by stock_date (FIFO - oldest first)
        lots.sort(key=lambda x: (x['stock_date'], x['import_date']))

        return lots

    def get_available_quantity_for_item(self, item_description: str) -> int:
        """
        Get total available quantity for an item across ALL lots.

        Args:
            item_description: The item name/description

        Returns:
            Total quantity available across all lots
        """
        total = sum(
            p['qty_remaining']
            for p in self.products
            if p['item_description'] == item_description
        )
        return total

    def get_lot_by_id(self, lot_id: str) -> Optional[Dict]:
        """
        Get a specific lot by lot_id.

        Args:
            lot_id: The lot identifier (customs_declaration_no:item_description)

        Returns:
            Lot dictionary or None if not found
        """
        return self.lot_index.get(lot_id)

    def get_lot_price(self, lot_id: str) -> Decimal:
        """
        Get unit price for a specific lot.

        Args:
            lot_id: The lot identifier

        Returns:
            Unit price (ex VAT) for this lot

        Raises:
            ValueError: If lot not found or has no stock
        """
        lot = self.lot_index.get(lot_id)

        if not lot:
            raise ValueError(f"Lot not found: {lot_id}")

        if lot['qty_remaining'] <= 0:
            raise ValueError(f"Lot has no stock: {lot_id}")

        return lot['unit_price_ex_vat']

    def get_lot_cost(self, lot_id: str) -> Decimal:
        """
        Get unit cost for a specific lot.

        Args:
            lot_id: The lot identifier

        Returns:
            Unit cost (ex VAT) for this lot

        Raises:
            ValueError: If lot not found
        """
        lot = self.lot_index.get(lot_id)

        if not lot:
            raise ValueError(f"Lot not found: {lot_id}")

        return lot['unit_cost_ex_vat']

    def deduct_stock(self, lot_id: str, quantity: int) -> Dict:
        """
        Deduct quantity from a SPECIFIC lot.

        Args:
            lot_id: The lot identifier
            quantity: Quantity to deduct

        Returns:
            Dictionary with deduction details:
            {
                'lot_id': str,
                'qty_deducted': int,
                'unit_price_ex_vat': Decimal,
                'unit_cost_ex_vat': Decimal,
                'customs_declaration_no': str,
                'item_description': str
            }

        Raises:
            ValueError: If lot not found or insufficient stock
        """
        lot = self.lot_index.get(lot_id)

        if not lot:
            raise ValueError(f"Lot not found: {lot_id}")

        if lot['qty_remaining'] < quantity:
            raise ValueError(
                f"Insufficient stock in lot {lot_id}. "
                f"Requested: {quantity}, Available: {lot['qty_remaining']}"
            )

        # Deduct the quantity
        lot['qty_remaining'] -= quantity

        # Return deduction details
        return {
            'lot_id': lot_id,
            'qty_deducted': quantity,
            'unit_price_ex_vat': lot['unit_price_ex_vat'],
            'unit_cost_ex_vat': lot['unit_cost_ex_vat'],
            'customs_declaration_no': lot['customs_declaration_no'],
            'item_description': lot['item_description']
        }

    def deduct_stock_fifo(self, item_description: str, quantity: int) -> List[Dict]:
        """
        Deduct quantity from item using FIFO across lots.
        Returns multiple deductions if quantity spans multiple lots.

        Args:
            item_description: The item name
            quantity: Total quantity to deduct

        Returns:
            List of deduction dictionaries (one per lot used)

        Raises:
            ValueError: If insufficient total stock
        """
        # Check total availability
        total_available = self.get_available_quantity_for_item(item_description)
        if total_available < quantity:
            raise ValueError(
                f"Insufficient total stock for {item_description}. "
                f"Requested: {quantity}, Available: {total_available}"
            )

        # Get lots in FIFO order
        lots = self.get_lots_for_item(item_description)

        deductions = []
        remaining_to_deduct = quantity

        for lot in lots:
            if remaining_to_deduct <= 0:
                break

            # How much to take from this lot?
            qty_from_lot = min(remaining_to_deduct, lot['qty_remaining'])

            # Deduct from this lot
            deduction = self.deduct_stock(lot['lot_id'], qty_from_lot)
            deductions.append(deduction)

            remaining_to_deduct -= qty_from_lot

        return deductions

    def check_lot_stock_available(self, lot_id: str, quantity: int) -> bool:
        """
        Check if sufficient stock is available in a specific lot.

        Args:
            lot_id: The lot identifier
            quantity: Quantity needed

        Returns:
            True if stock is available, False otherwise
        """
        lot = self.lot_index.get(lot_id)

        if not lot:
            return False

        return lot['qty_remaining'] >= quantity

    def check_item_stock_available(self, item_description: str, quantity: int) -> bool:
        """
        Check if sufficient stock is available for an item across all lots.

        Args:
            item_description: The item name
            quantity: Quantity needed

        Returns:
            True if stock is available, False otherwise
        """
        available = self.get_available_quantity_for_item(item_description)
        return available >= quantity

    def get_inventory_summary(self) -> Dict:
        """
        Get summary statistics about current inventory.

        Returns:
            Dictionary with inventory stats
        """
        total_lots = len(self.products)
        lots_with_stock = len([p for p in self.products if p['qty_remaining'] > 0])
        lots_depleted = total_lots - lots_with_stock
        total_quantity = sum(p['qty_remaining'] for p in self.products)

        # Count unique items
        unique_items_all = len(set(p['item_description'] for p in self.products))
        unique_items_available = len(set(
            p['item_description'] for p in self.products if p['qty_remaining'] > 0
        ))

        return {
            'total_lots': total_lots,
            'lots_with_stock': lots_with_stock,
            'lots_depleted': lots_depleted,
            'total_quantity_remaining': total_quantity,
            'unique_items_all': unique_items_all,
            'unique_items_available': unique_items_available
        }

    def get_lots_by_classification_count(self) -> Dict[str, int]:
        """
        Count available LOTS by classification (not deduplicated items).

        Returns:
            Dictionary: {classification: count_of_lots_with_stock}
        """
        from collections import defaultdict
        counts = defaultdict(int)

        for p in self.products:
            if p['qty_remaining'] > 0:
                counts[p['shipment_class']] += 1

        return dict(counts)

    # ============================================================
    # LEGACY COMPATIBILITY METHODS
    # Keep these for backward compatibility with existing code
    # ============================================================

    def get_available_items_by_classification(self, classification: str) -> List[Dict]:
        """
        LEGACY: Returns available lots (not deduplicated).
        For backward compatibility.
        """
        return self.get_available_lots_by_classification(classification)

    def get_all_available_items(self) -> List[Dict]:
        """
        LEGACY: Returns available lots (not deduplicated).
        For backward compatibility.
        """
        return self.get_all_available_lots()

    def get_available_quantity(self, item_name: str) -> int:
        """
        LEGACY: Get available quantity by item_name.
        For backward compatibility.
        """
        return self.get_available_quantity_for_item(item_name)

    def get_unit_price(self, item_name: str) -> Decimal:
        """
        LEGACY: Get price from oldest lot for item.
        For backward compatibility.
        """
        lots = self.get_lots_for_item(item_name)

        if not lots:
            raise ValueError(f"No stock available for item: {item_name}")

        # Return price from oldest lot (FIFO)
        return lots[0]['unit_price_ex_vat']

    def get_items_by_classification_count(self) -> Dict[str, int]:
        """
        LEGACY: Count lots by classification.
        For backward compatibility.
        """
        return self.get_lots_by_classification_count()
