# Phase 3 ETL Pipeline Documentation
## Multi-Vendor E-Commerce & Inventory Management System

### 1. Overview
This directory contains the production-grade ETL (Extract, Transform, Load) and validation pipeline for Phase 3 of the Multi-Vendor E-Commerce DBMS project. The pipeline transforms the 9 raw immutable Olist CSV datasets located in `data/raw/` into the canonical 12-table relational schema for MySQL 8.4 (`multivendor_ecommerce_db`).

---

### 2. Pipeline Architecture & Directory Structure

```
etl/
├── README.md                      # Comprehensive ETL pipeline documentation
├── config.py                      # Database credentials and filesystem paths configuration
├── run_etl.py                     # Master CLI entry point (Extract, Dry-Run, Load, Validate)
├── transform/
│   ├── __init__.py
│   ├── transform_customers.py     # Transforms CUSTOMER, CUSTOMER_PHONE, ADDRESS
│   ├── transform_vendors.py       # Transforms VENDOR (review ratings & GST synthesis)
│   ├── transform_catalog.py       # Transforms CATEGORY (13-stage hierarchy), PRODUCT, PRODUCT_TAG
│   ├── transform_inventory.py     # Transforms WAREHOUSE (8 regional hubs), INVENTORY
│   ├── transform_orders.py        # Transforms ORDERS (canonical unique_id), ORDER_ITEM (deduped & aggregated)
│   ├── transform_payments.py      # Transforms PAYMENT (sanitized zero-amounts, sequential PK)
│   └── pipeline.py                # Master transformation orchestrator
├── load/
│   ├── __init__.py
│   ├── db_connection.py           # PyMySQL connection manager (transactions & DDL execution)
│   └── loader.py                  # 13-stage topological MySQL batch loader (Zero INSERT IGNORE)
└── validate/
    ├── __init__.py
    └── validate_etl.py            # Automated 27-check validation suite (Dry-run & Live MySQL)
```

---

### 3. Canonical Transformation & Lineage Rules

| Target Table | Target PK | Source Feeder | Lineage Classification | Transformation Rule Summary | Target Row Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CUSTOMER`** | `customer_id` | `olist_customers_dataset.csv` | **DIRECT / MAPPED** | Mapped from `customer_unique_id` (human customer accounts). Deterministic name, email, and earliest order `join_date`. | **96,096** |
| **`CUSTOMER_PHONE`** | `(customer_id, phone_number)` | State DDD + customer hash | **SYNTHETIC / AUGMENTED** | Deterministic Brazilian formatted mobile numbers (`+55<DDD>9...`). Type `'Mobile'`. | **96,096** |
| **`ADDRESS`** | `(customer_id, address_type)` | `olist_customers_dataset.csv` | **DIRECT / SYNTHETIC STREET** | Mapped from most recent order address for repeat buyers. Type `'Shipping'`, synthetic street, source city/state, pincode prefix formatted `CONCAT(zip, '-000')`. | **96,096** |
| **`VENDOR`** | `vendor_id` | `olist_sellers_dataset.csv` | **DIRECT / DERIVED** | Mapped from `seller_id` (3,095). Rating derived from review score average (`ROUND(AVG(review_score), 2)`). Deterministic unique `GST-<STATE>-<HEX8>`. | **3,095** |
| **`CATEGORY`** | `category_id` | `product_category_name_translation.csv` | **DERIVED** | 9 L1 parent categories (`parent_category_id IS NULL`) + 73 L2 child subcategories + 1 Uncategorized fallback (ID 83). | **83** |
| **`PRODUCT`** | `product_id` | `olist_products_dataset.csv` | **DIRECT / DERIVED** | 32,951 products. 3-tier vendor resolution: 1. Sales Volume DESC, 2. Earliest Order Date ASC, 3. Min `seller_id` ASC. Representative catalog price = median historical price. | **32,951** |
| **`PRODUCT_TAG`** | `(product_id, tag)` | Product attributes | **SYNTHETIC / AUGMENTED** | 2–4 deterministic keyword tags per product based on category tokens, price tier, and popularity. | **98,853** |
| **`WAREHOUSE`** | `warehouse_id` | Regional Hub synthesis | **SYNTHETIC / AUGMENTED** | 8 regional fulfillment centers in key Brazilian logistics hubs (SP Central, Campinas, RJ, BH, Curitiba, Porto Alegre, Salvador, Brasília). Capacities 250k–1M. | **8** |
| **`INVENTORY`** | `(product_id, warehouse_id)` | Product & Vendor hub mapping | **SYNTHETIC / AUGMENTED** | Multi-warehouse stock model (1–3 warehouses per product). `stock_quantity = GREATEST(ROUND(sales*1.5), 50)`, `reorder_level = GREATEST(ROUND(stock*0.2), 10)`. | **43,217** |
| **`ORDERS`** | `order_id` | `olist_orders_dataset.csv` | **DIRECT / MAPPED** | 99,441 orders. `customer_id` mapped to `customer_unique_id`. Status normalized to uppercase (`'DELIVERED'`, `'SHIPPED'`, `'CANCELLED'`, etc.). | **99,441** |
| **`ORDER_ITEM`** | `(order_id, product_id)` | `olist_order_items_dataset.csv` | **DERIVED / AGGREGATED** | Grouped by `(order_id, product_id)` with `quantity = COUNT(*)` and `price_at_purchase = MIN(price)`. Collapses 112,650 raw rows into 102,425 composite PK pairs while conserving 100% quantity. | **102,425** |
| **`PAYMENT`** | `(order_id, payment_id)` | `olist_order_payments_dataset.csv` | **DIRECT / DERIVED** | `payment_id = payment_sequential`. Sanitizes 9 zero-value payments to `0.01` to comply with `chk_payment_amount: amount > 0.00`. Deterministic unique `transaction_reference`. | **103,886** |

---

### 4. 13-Stage Topological Population Sequence

To respect foreign-key dependencies without disabling foreign key checks during loading, data is populated across 13 stages:

```
Stage 1:   CUSTOMER
Stage 2:   CUSTOMER_PHONE
Stage 3:   ADDRESS
Stage 4:   VENDOR
Stage 5:   CATEGORY (L1 Root Categories: parent_category_id IS NULL)
Stage 6:   CATEGORY (L2 Child Subcategories: parent_category_id -> L1 ID)
Stage 7:   WAREHOUSE
Stage 8:   PRODUCT (FKs -> VENDOR, CATEGORY)
Stage 9:   PRODUCT_TAG (FK -> PRODUCT)
Stage 10:  INVENTORY (FKs -> PRODUCT, WAREHOUSE)
Stage 11:  ORDERS (FK -> CUSTOMER)
Stage 12:  ORDER_ITEM (FKs -> ORDERS, PRODUCT)
Stage 13:  PAYMENT (FK -> ORDERS)
```

---

### 5. Running the Pipeline

#### Full Pipeline (Extract, Dry-Run, Schema Init, Load, Validate)
```bash
python -m etl.run_etl
```

#### Pre-Load Dry Run Only (No DB connection needed)
```bash
python -m etl.run_etl --dry-run-only
```

#### Live MySQL Validation Only (Runs 27-check validation suite against loaded DB)
```bash
python -m etl.run_etl --validate-only
```

#### Skip Transformation (Use existing files in `data/processed/`)
```bash
python -m etl.run_etl --skip-transform
```
