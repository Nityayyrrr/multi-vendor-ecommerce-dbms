"""
Transform Orders and Order Items Entities.
Canonical Target Tables:
- ORDERS (PK: order_id, FK -> customer(customer_id = customer_unique_id))
- ORDER_ITEM (Composite PK: order_id, product_id, FKs -> ORDERS, PRODUCT)
"""
import csv
from collections import defaultdict
from typing import Dict, List, Tuple, Any

STATUS_NORMALIZATION_MAP = {
    "delivered": "DELIVERED",
    "shipped": "SHIPPED",
    "canceled": "CANCELLED",
    "unavailable": "UNAVAILABLE",
    "invoiced": "INVOICED",
    "processing": "PROCESSING",
    "created": "CREATED",
    "approved": "APPROVED",
}

def transform_orders_and_items(
    raw_orders_path: str,
    raw_customers_path: str,
    raw_items_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transforms ORDERS and ORDER_ITEM.
    Returns:
        (order_records, order_item_records)
    """
    # 1. Map raw customer_id (order token) -> customer_unique_id (master customer entity)
    cust_token_to_unique: Dict[str, str] = {}
    with open(raw_customers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            cust_token_to_unique[r["customer_id"].strip()] = r["customer_unique_id"].strip()

    # 2. Read and transform ORDERS
    order_records: List[Dict[str, Any]] = []
    valid_order_ids = set()

    with open(raw_orders_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            oid = r["order_id"].strip()
            cid_token = r["customer_id"].strip()
            uid = cust_token_to_unique.get(cid_token)
            
            raw_status = r["order_status"].strip().lower()
            normalized_status = STATUS_NORMALIZATION_MAP.get(raw_status, raw_status.upper())
            order_date = r["order_purchase_timestamp"].strip()

            order_records.append({
                "order_id": oid,
                "customer_id": uid,
                "order_date": order_date,
                "status": normalized_status
            })
            valid_order_ids.add(oid)

    # 3. Read and aggregate ORDER_ITEM
    # Group by (order_id, product_id)
    # quantity = COUNT(*)
    # price_at_purchase = MIN(price)
    grouped_items: Dict[Tuple[str, str], Dict[str, Any]] = {}

    with open(raw_items_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            oid = r["order_id"].strip()
            pid = r["product_id"].strip()
            price = float(r["price"])

            key = (oid, pid)
            if key not in grouped_items:
                grouped_items[key] = {
                    "order_id": oid,
                    "product_id": pid,
                    "quantity": 1,
                    "price_at_purchase": price
                }
            else:
                grouped_items[key]["quantity"] += 1
                if price < grouped_items[key]["price_at_purchase"]:
                    grouped_items[key]["price_at_purchase"] = price

    order_item_records = list(grouped_items.values())

    return order_records, order_item_records
