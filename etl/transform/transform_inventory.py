"""
Transform Logistics Entities: WAREHOUSE and INVENTORY.
Canonical Target Tables:
- WAREHOUSE (Surrogate PK: warehouse_id) [100% SYNTHETIC/AUGMENTED]
- INVENTORY (Composite PK: product_id, warehouse_id) [100% SYNTHETIC/AUGMENTED]
"""
import csv
from collections import defaultdict
from typing import Dict, List, Tuple, Any

# 8 Canonical Regional Logistics Hubs
WAREHOUSES = [
    {"warehouse_id": 1, "location": "São Paulo Central Hub (SP)", "capacity": 1000000},
    {"warehouse_id": 2, "location": "Campinas Logistics Park (SP)", "capacity": 750000},
    {"warehouse_id": 3, "location": "Rio de Janeiro Distribution Center (RJ)", "capacity": 600000},
    {"warehouse_id": 4, "location": "Belo Horizonte Hub (MG)", "capacity": 500000},
    {"warehouse_id": 5, "location": "Curitiba Regional Hub (PR)", "capacity": 500000},
    {"warehouse_id": 6, "location": "Porto Alegre Hub (RS)", "capacity": 400000},
    {"warehouse_id": 7, "location": "Salvador Northeast Center (BA)", "capacity": 350000},
    {"warehouse_id": 8, "location": "Brasília Central Hub (DF)", "capacity": 300000},
]

# Mapping Brazilian state to regional warehouse ID
STATE_TO_WAREHOUSE_MAP = {
    "SP": 1,
    "RJ": 3,
    "MG": 4,
    "PR": 5, "SC": 5,
    "RS": 6,
    "BA": 7, "PE": 7, "CE": 7, "RN": 7, "PB": 7, "AL": 7, "SE": 7, "MA": 7, "PI": 7,
    "DF": 8, "GO": 8, "MT": 8, "MS": 8, "TO": 8, "RO": 8, "AC": 8, "AM": 8, "PA": 8, "AP": 8, "RR": 8,
    "ES": 3
}

def transform_warehouses_and_inventory(
    product_records: List[Dict[str, Any]],
    raw_sellers_path: str,
    raw_items_path: str,
    raw_orders_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transforms WAREHOUSE and INVENTORY.
    Returns:
        (warehouse_records, inventory_records)
    """
    # 1. Warehouse records
    warehouse_records = list(WAREHOUSES)

    # 2. Seller ID -> State
    seller_states: Dict[str, str] = {}
    with open(raw_sellers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            seller_states[r["seller_id"].strip()] = r["seller_state"].strip().upper()

    # 3. Product sales volume and latest date from items/orders
    order_dates: Dict[str, str] = {}
    with open(raw_orders_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            order_dates[r["order_id"]] = r["order_purchase_timestamp"]

    product_sales: Dict[str, int] = defaultdict(int)
    product_latest_date: Dict[str, str] = {}

    with open(raw_items_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["product_id"].strip()
            oid = r["order_id"].strip()
            product_sales[pid] += 1
            dt = order_dates.get(oid, "2018-01-01 00:00:00")
            if pid not in product_latest_date or dt > product_latest_date[pid]:
                product_latest_date[pid] = dt

    # 4. Generate INVENTORY records
    inventory_records: List[Dict[str, Any]] = []
    seen_inventory_pks = set()

    for p in product_records:
        pid = p["product_id"]
        vid = p["vendor_id"]
        v_state = seller_states.get(vid, "SP")
        
        # Primary warehouse is the state regional hub
        primary_wh = STATE_TO_WAREHOUSE_MAP.get(v_state, 1)
        warehouses_for_product = [primary_wh]
        
        # If vendor is outside SP, also stock in SP Central Hub (WH 1) for national reach
        if primary_wh != 1:
            warehouses_for_product.append(1)

        total_sales = product_sales.get(pid, 1)
        latest_dt = product_latest_date.get(pid, "2018-10-17 17:30:18")

        for wh_id in warehouses_for_product:
            pk = (pid, wh_id)
            if pk in seen_inventory_pks:
                continue
            seen_inventory_pks.add(pk)

            # Deterministic Stock and Reorder Level calculations
            stock_qty = max(int(round(total_sales * 1.5)), 50)
            reorder_lvl = max(int(round(stock_qty * 0.20)), 10)

            inventory_records.append({
                "product_id": pid,
                "warehouse_id": wh_id,
                "stock_quantity": stock_qty,
                "reorder_level": reorder_lvl,
                "last_updated": latest_dt
            })

    return warehouse_records, inventory_records
