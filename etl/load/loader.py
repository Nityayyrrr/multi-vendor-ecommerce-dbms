"""
Loads the 12 processed CSVs into MySQL across 13 ordered stages.
Uses plain INSERT (no INSERT IGNORE) so any PK violation fails loudly.
"""
import csv
import time
from typing import Dict, List, Tuple, Any, Optional

from etl.config import PROCESSED_FILES, BATCH_SIZE
from etl.load.db_connection import get_connection

def load_table_in_batches(
    conn,
    table_name: str,
    columns: List[str],
    rows: List[Tuple[Any, ...]],
    stage_num: int,
    stage_desc: str
) -> int:
    """Batch-insert rows into a single table. Rolls back on any error."""
    if not rows:
        print(f"  [Stage {stage_num}] {stage_desc}: 0 rows to load.")
        return 0

    cols_str = ", ".join([f"`{c}`" for c in columns])
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO `{table_name}` ({cols_str}) VALUES ({placeholders});"

    total_inserted = 0
    start_time = time.time()

    with conn.cursor() as cur:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            try:
                cur.executemany(sql, batch)
                total_inserted += len(batch)
            except Exception as e:
                conn.rollback()
                print(f"\n  [ERROR in Stage {stage_num} ({table_name}) at batch {i}-{i+len(batch)}]: {e}")
                print(f"  Sample failed row: {batch[0] if batch else 'None'}")
                raise RuntimeError(f"Batch insert failure in `{table_name}`: {e}")

    conn.commit()
    elapsed = round(time.time() - start_time, 2)
    print(f"  Loaded {total_inserted:,} rows into {table_name} ({stage_desc}) in {elapsed}s")
    return total_inserted

def execute_13_stage_load() -> Dict[str, int]:
    """Run all 13 load stages in FK-safe order and return the per-table row counts."""
    print("Loading data into MySQL tables...")
    total_start = time.time()

    conn = get_connection(autocommit=False)
    loaded_counts: Dict[str, int] = {}

    try:
        # read processed csv files
        tables_data: Dict[str, List[Dict[str, str]]] = {}
        for tbl, fpath in PROCESSED_FILES.items():
            with open(fpath, "r", encoding="utf-8") as f:
                tables_data[tbl] = list(csv.DictReader(f))

        # customer
        cust_rows = [
            (r["customer_id"], r["name"], r["email"], r["join_date"])
            for r in tables_data["customer"]
        ]
        loaded_counts["customer"] = load_table_in_batches(
            conn, "customer", ["customer_id", "name", "email", "join_date"],
            cust_rows, 1, "customer accounts"
        )

        # customer phone
        phone_rows = [
            (r["customer_id"], r["phone_number"], r["phone_type"])
            for r in tables_data["customer_phone"]
        ]
        loaded_counts["customer_phone"] = load_table_in_batches(
            conn, "customer_phone", ["customer_id", "phone_number", "phone_type"],
            phone_rows, 2, "customer phone numbers"
        )

        # address
        addr_rows = [
            (r["customer_id"], r["address_type"], r["street"], r["city"], r["state"], r["pincode"], int(r["is_default"]))
            for r in tables_data["address"]
        ]
        loaded_counts["address"] = load_table_in_batches(
            conn, "address", ["customer_id", "address_type", "street", "city", "state", "pincode", "is_default"],
            addr_rows, 3, "customer addresses"
        )

        # vendor
        vendor_rows = [
            (r["vendor_id"], r["vendor_name"], float(r["rating"]), r["gst_number"])
            for r in tables_data["vendor"]
        ]
        loaded_counts["vendor"] = load_table_in_batches(
            conn, "vendor", ["vendor_id", "vendor_name", "rating", "gst_number"],
            vendor_rows, 4, "vendors"
        )

        # category roots
        l1_cat_rows = [
            (int(r["category_id"]), r["category_name"], None)
            for r in tables_data["category"]
            if not r["parent_category_id"] or r["parent_category_id"] == "None" or r["parent_category_id"] == ""
        ]
        load_table_in_batches(
            conn, "category", ["category_id", "category_name", "parent_category_id"],
            l1_cat_rows, 5, "root categories"
        )

        # category subcategories
        l2_cat_rows = [
            (int(r["category_id"]), r["category_name"], int(r["parent_category_id"]))
            for r in tables_data["category"]
            if r["parent_category_id"] and r["parent_category_id"] != "None" and r["parent_category_id"] != ""
        ]
        load_table_in_batches(
            conn, "category", ["category_id", "category_name", "parent_category_id"],
            l2_cat_rows, 6, "subcategories"
        )
        loaded_counts["category"] = len(l1_cat_rows) + len(l2_cat_rows)

        # warehouse
        wh_rows = [
            (int(r["warehouse_id"]), r["location"], int(r["capacity"]))
            for r in tables_data["warehouse"]
        ]
        loaded_counts["warehouse"] = load_table_in_batches(
            conn, "warehouse", ["warehouse_id", "location", "capacity"],
            wh_rows, 7, "warehouses"
        )

        # product
        prod_rows = [
            (r["product_id"], r["product_name"], r["description"], float(r["price"]), int(r["category_id"]), r["vendor_id"], r["status"])
            for r in tables_data["product"]
        ]
        loaded_counts["product"] = load_table_in_batches(
            conn, "product", ["product_id", "product_name", "description", "price", "category_id", "vendor_id", "status"],
            prod_rows, 8, "product catalog"
        )

        # product tag
        tag_rows = [
            (r["product_id"], r["tag"])
            for r in tables_data["product_tag"]
        ]
        loaded_counts["product_tag"] = load_table_in_batches(
            conn, "product_tag", ["product_id", "tag"],
            tag_rows, 9, "product tags"
        )

        # inventory
        inv_rows = [
            (r["product_id"], int(r["warehouse_id"]), int(r["stock_quantity"]), int(r["reorder_level"]), r["last_updated"])
            for r in tables_data["inventory"]
        ]
        loaded_counts["inventory"] = load_table_in_batches(
            conn, "inventory", ["product_id", "warehouse_id", "stock_quantity", "reorder_level", "last_updated"],
            inv_rows, 10, "inventory levels"
        )

        # orders
        order_rows = [
            (r["order_id"], r["customer_id"], r["order_date"], r["status"])
            for r in tables_data["orders"]
        ]
        loaded_counts["orders"] = load_table_in_batches(
            conn, "orders", ["order_id", "customer_id", "order_date", "status"],
            order_rows, 11, "orders"
        )

        # order item
        item_rows = [
            (r["order_id"], r["product_id"], int(r["quantity"]), float(r["price_at_purchase"]))
            for r in tables_data["order_item"]
        ]
        loaded_counts["order_item"] = load_table_in_batches(
            conn, "order_item", ["order_id", "product_id", "quantity", "price_at_purchase"],
            item_rows, 12, "order items"
        )

        # payment
        pay_rows = [
            (r["order_id"], int(r["payment_id"]), float(r["amount"]), r["mode"], r["status"], r["payment_date"], r["transaction_reference"])
            for r in tables_data["payment"]
        ]
        loaded_counts["payment"] = load_table_in_batches(
            conn, "payment", ["order_id", "payment_id", "amount", "mode", "status", "payment_date", "transaction_reference"],
            pay_rows, 13, "payments"
        )

        total_elapsed = round(time.time() - total_start, 2)
        print(f"\nLoaded all 12 tables in {total_elapsed}s ({sum(loaded_counts.values()):,} total rows).\n")
        return loaded_counts

    finally:
        conn.close()

if __name__ == "__main__":
    execute_13_stage_load()
