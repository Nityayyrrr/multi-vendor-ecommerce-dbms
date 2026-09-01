"""
Master Transformation Pipeline Orchestrator.
Extracts raw data from `data/raw/`, applies canonical transformation rules,
and stages normalized intermediate CSVs in `data/processed/`.
"""
import csv
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

from etl.config import RAW_FILES, PROCESSED_FILES, PROCESSED_DATA_DIR
from etl.transform.transform_customers import transform_customers_and_addresses
from etl.transform.transform_vendors import transform_vendors
from etl.transform.transform_catalog import transform_catalog
from etl.transform.transform_inventory import transform_warehouses_and_inventory
from etl.transform.transform_orders import transform_orders_and_items
from etl.transform.transform_payments import transform_payments

def save_to_csv(data: List[Dict[str, Any]], filepath: Path, fieldnames: List[str]) -> int:
    """Saves a list of dictionaries to a CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return len(data)

def run_transformation_pipeline() -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """
    Executes all transformation stages, exports CSVs to `data/processed/`, and returns dataset dict + metrics.
    """
    start_time = time.time()
    print("=================================================================")
    print("PHASE 3 ETL: EXTRACT & TRANSFORM PIPELINE")
    print("=================================================================")
    
    # 1. Transform Customers, Customer Phone, Address
    print("[Stage 1-3] Transforming CUSTOMER, CUSTOMER_PHONE, and ADDRESS...")
    cust_records, phone_records, address_records = transform_customers_and_addresses(
        raw_customers_path=str(RAW_FILES["customers"]),
        raw_orders_path=str(RAW_FILES["orders"])
    )
    save_to_csv(cust_records, PROCESSED_FILES["customer"], ["customer_id", "name", "email", "join_date"])
    save_to_csv(phone_records, PROCESSED_FILES["customer_phone"], ["customer_id", "phone_number", "phone_type"])
    save_to_csv(address_records, PROCESSED_FILES["address"], ["customer_id", "address_type", "street", "city", "state", "pincode", "is_default"])
    print(f"  -> CUSTOMER: {len(cust_records):,} rows")
    print(f"  -> CUSTOMER_PHONE: {len(phone_records):,} rows")
    print(f"  -> ADDRESS: {len(address_records):,} rows")

    # 2. Transform Vendors
    print("\n[Stage 4] Transforming VENDOR...")
    vendor_records = transform_vendors(
        raw_sellers_path=str(RAW_FILES["sellers"]),
        raw_items_path=str(RAW_FILES["order_items"]),
        raw_reviews_path=str(RAW_FILES["order_reviews"])
    )
    save_to_csv(vendor_records, PROCESSED_FILES["vendor"], ["vendor_id", "vendor_name", "rating", "gst_number"])
    print(f"  -> VENDOR: {len(vendor_records):,} rows")

    # 3. Transform Catalog (Category, Product, Product Tag)
    print("\n[Stage 5-7] Transforming CATEGORY, PRODUCT, and PRODUCT_TAG...")
    cat_records, product_records, tag_records = transform_catalog(
        raw_products_path=str(RAW_FILES["products"]),
        raw_items_path=str(RAW_FILES["order_items"]),
        raw_orders_path=str(RAW_FILES["orders"]),
        raw_translations_path=str(RAW_FILES["category_translations"])
    )
    save_to_csv(cat_records, PROCESSED_FILES["category"], ["category_id", "category_name", "parent_category_id"])
    save_to_csv(product_records, PROCESSED_FILES["product"], ["product_id", "product_name", "description", "price", "category_id", "vendor_id", "status"])
    save_to_csv(tag_records, PROCESSED_FILES["product_tag"], ["product_id", "tag"])
    print(f"  -> CATEGORY: {len(cat_records):,} rows")
    print(f"  -> PRODUCT: {len(product_records):,} rows")
    print(f"  -> PRODUCT_TAG: {len(tag_records):,} rows")

    # 4. Transform Logistics (Warehouse, Inventory)
    print("\n[Stage 8-9] Transforming WAREHOUSE and INVENTORY...")
    warehouse_records, inventory_records = transform_warehouses_and_inventory(
        product_records=product_records,
        raw_sellers_path=str(RAW_FILES["sellers"]),
        raw_items_path=str(RAW_FILES["order_items"]),
        raw_orders_path=str(RAW_FILES["orders"])
    )
    save_to_csv(warehouse_records, PROCESSED_FILES["warehouse"], ["warehouse_id", "location", "capacity"])
    save_to_csv(inventory_records, PROCESSED_FILES["inventory"], ["product_id", "warehouse_id", "stock_quantity", "reorder_level", "last_updated"])
    print(f"  -> WAREHOUSE: {len(warehouse_records):,} rows")
    print(f"  -> INVENTORY: {len(inventory_records):,} rows")

    # 5. Transform Orders & Order Items
    print("\n[Stage 10-11] Transforming ORDERS and ORDER_ITEM...")
    order_records, item_records = transform_orders_and_items(
        raw_orders_path=str(RAW_FILES["orders"]),
        raw_customers_path=str(RAW_FILES["customers"]),
        raw_items_path=str(RAW_FILES["order_items"])
    )
    save_to_csv(order_records, PROCESSED_FILES["orders"], ["order_id", "customer_id", "order_date", "status"])
    save_to_csv(item_records, PROCESSED_FILES["order_item"], ["order_id", "product_id", "quantity", "price_at_purchase"])
    print(f"  -> ORDERS: {len(order_records):,} rows")
    print(f"  -> ORDER_ITEM: {len(item_records):,} rows")

    # 6. Transform Payments
    print("\n[Stage 12] Transforming PAYMENT...")
    payment_records, sanitized_zero_payments = transform_payments(
        raw_payments_path=str(RAW_FILES["order_payments"]),
        raw_orders_path=str(RAW_FILES["orders"])
    )
    save_to_csv(payment_records, PROCESSED_FILES["payment"], ["order_id", "payment_id", "amount", "mode", "status", "payment_date", "transaction_reference"])
    print(f"  -> PAYMENT: {len(payment_records):,} rows (Sanitized zero-values: {len(sanitized_zero_payments)})")

    elapsed = round(time.time() - start_time, 2)
    print(f"\n[OK] Complete transformation finished in {elapsed}s.")
    print("=================================================================\n")

    datasets = {
        "customer": cust_records,
        "customer_phone": phone_records,
        "address": address_records,
        "vendor": vendor_records,
        "category": cat_records,
        "warehouse": warehouse_records,
        "product": product_records,
        "product_tag": tag_records,
        "inventory": inventory_records,
        "orders": order_records,
        "order_item": item_records,
        "payment": payment_records,
    }

    metrics = {
        "elapsed_seconds": elapsed,
        "row_counts": {k: len(v) for k, v in datasets.items()},
        "sanitized_zero_payments": sanitized_zero_payments,
        "total_order_item_units": sum(it["quantity"] for it in item_records)
    }

    return datasets, metrics

if __name__ == "__main__":
    run_transformation_pipeline()
