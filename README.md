# Multi-Vendor E-Commerce & Inventory Management System

A relational database management system (DBMS) project modeling an online multi-vendor retail platform (similar to Amazon / Flipkart). Built with **MySQL 8.4** and populated using a deterministic Python ETL pipeline that processes the real-world **Brazilian E-Commerce Public Dataset by Olist**.

---

## 1. Project Overview

Modern e-commerce platforms host thousands of independent vendors, millions of catalog products, dynamic inventory across regional fulfillment centers, customer delivery profiles, order transactions, and multi-mode payment settlements.

This project designs and implements a normalized, relational database architecture to manage:
- Master customer accounts, multiple phone numbers, and addresses.
- Marketplace seller/vendor profiles with review ratings and tax registration.
- A multi-tier product catalog structured as a self-referencing category tree.
- Multivalued search keywords/tags normalized in First Normal Form (1NF).
- Multi-warehouse regional logistics hubs and real-time inventory tracking.
- Order processing, line-item quantity/price preservation, and split-payment transactions.

---

## 2. Objectives

1. **Relational Schema Design:** Implement a normalized (1NF $\rightarrow$ 2NF $\rightarrow$ 3NF / BCNF) relational schema consisting of 12 canonical tables in MySQL 8.4.
2. **Real-World Source Grounding:** Ground the schema in real-world retail transactions using the Olist dataset (9 raw CSV files, ~1.45M total records).
3. **Reproducible Python ETL Pipeline:** Implement an Extract, Transform, and Load (ETL) pipeline to clean, derive, augment, and stage data without modifying the raw source files.
4. **Data Integrity & Consistency:** Enforce primary keys, composite keys, foreign keys with appropriate cascade/restrict actions, unique constraints, and domain check constraints.
5. **Comprehensive Validation:** Validate the staged CSVs and live database using a 27-check automated test suite.

---

## 3. Technology Stack

- **Database Management System:** MySQL 8.4 LTS
- **Database Client:** MySQL Workbench / Command Line Client
- **Programming Language:** Python 3.10+
- **Database Driver:** PyMySQL
- **Environment Management:** python-dotenv
- **Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)

---

## 4. Database Architecture (12 Canonical Tables)

The database schema (`multivendor_ecommerce_db`) consists of 12 canonical tables organized across five logical domains:

```
                               ┌──────────────────────────┐
                               │         category         │◄─────────┐ (Recursive 1:N)
                               └─────────────┬────────────┘          │ (parent_category_id)
                                             │ (1:N)                 │
                                             ▼                       │
┌─────────────────────────┐            ┌───────────┐                 │
│       product_tag       │◄───(1:N)───┤  product  │                 │
└─────────────────────────┘            └─────┬─────┘                 │
                                             │                       │
     ┌─────────────────────────┐             │ (N:1)                 │
     │         vendor          │◄────────────┤                       │
     └─────────────────────────┘             │                       │
                                             │                       │
     ┌─────────────────────────┐             │ (1:N)                 │
     │        inventory        │◄────────────┤                       │
     └────────────▲────────────┘             │                       │
                  │ (N:1)                    │                       │
     ┌────────────┴────────────┐             │                       │
     │        warehouse        │             │                       │
     └─────────────────────────┘             │                       │
                                             │                       │
┌─────────────────────────┐                  │                       │
│     customer_phone      │                  │                       │
└────────────▲────────────┘                  │                       │
             │ (N:1)                         │                       │
┌────────────┴────────────┐                  ▼                       │
│        customer         │◄──(N:1)───┌─────────────┐                │
└────────────┬────────────┘           │ order_item  │                │
             │ (1:N)                  └──────▲──────┘                │
             ▼                               │ (N:1)                 │
┌─────────────────────────┐           ┌──────┴──────┐                │
│         address         │           │   orders    │────────────────┘
└─────────────────────────┘           └──────┬──────┘                 
                                             │ (1:N Identifying)
                                             ▼
                                      ┌─────────────┐
                                      │   payment   │ (Weak Entity)
                                      └─────────────┘
```

### Table Summary & Primary Keys

| # | Table Name | Key Type | Primary Key Columns | Description |
| :- | :--- | :--- | :--- | :--- |
| 1 | `customer` | Single PK | `customer_id` | Master customer account profiles (mapped from `customer_unique_id`). |
| 2 | `customer_phone` | Composite PK | `(customer_id, phone_number)` | Multivalued customer contact numbers (1NF normalization). |
| 3 | `address` | Composite PK | `(customer_id, address_type)` | Customer delivery/billing addresses (weak entity). |
| 4 | `vendor` | Single PK | `vendor_id` | Marketplace sellers with review ratings and tax GST numbers. |
| 5 | `category` | Single PK | `category_id` | Hierarchical product taxonomy with self-referencing `parent_category_id`. |
| 6 | `warehouse` | Single PK | `warehouse_id` | Regional logistics hubs and fulfillment center capacities. |
| 7 | `product` | Single PK | `product_id` | Master catalog items linked to a primary vendor and category. |
| 8 | `product_tag` | Composite PK | `(product_id, tag)` | Multivalued descriptive search keywords in 1NF. |
| 9 | `inventory` | Composite PK | `(product_id, warehouse_id)` | Stock quantities and reorder levels per warehouse (M:N resolution). |
| 10 | `orders` | Single PK | `order_id` | Customer transaction orders and lifecycle status. |
| 11 | `order_item` | Composite PK | `(order_id, product_id)` | Order line-items with aggregated quantity and purchase price (M:N resolution). |
| 12 | `payment` | Composite PK | `(order_id, payment_id)` | Identifying weak entity recording payment amounts, modes, and statuses. |

---

## 5. Dataset & Lineage Breakdown

The project uses the **Olist Brazilian E-Commerce Dataset** stored in `data/raw/` (immutable source files).

### Source Data vs. Synthetic Augmentation

Because the raw Olist dataset represents a real-world snapshot, certain attributes required for a complete relational DBMS demonstration were either derived or synthetically generated:

1. **Direct Source Data:**
   - Real order UUIDs, purchase timestamps, delivery statuses (`orders.csv`).
   - Real product IDs, dimensions, weights (`products.csv`).
   - Real seller IDs, locations (`sellers.csv`).
   - Real payment amounts, installments, payment types (`order_payments.csv`).
   - Real item prices, freight values (`order_items.csv`).
   - Real customer geographical distribution across Brazilian cities and states.

2. **Derived Data (Relational Computation):**
   - `customer.customer_id`: Mapped to `customer_unique_id` to unify repeat purchasers into single master accounts (96,096 distinct customers).
   - `customer.join_date`: Earliest recorded order timestamp for that customer.
   - `vendor.rating`: Arithmetic average of review scores associated with that seller's orders.
   - `category`: Bilingual mapping into a 2-tier tree (9 Root Categories + 73 Subcategories + 1 Uncategorized fallback).
   - `product.price`: Median historical sale price across order items.
   - `product.vendor_id`: Assigned via a 3-tier deterministic ranking (Highest Sales Volume $\rightarrow$ Earliest Order Date $\rightarrow$ Lowest Seller ID).
   - `order_item`: Grouped by `(order_id, product_id)` to satisfy composite primary key uniqueness, conserving 100% of physical units (112,650 units across 102,425 pairs).
   - `payment.amount`: Sanitized 9 zero-value payments to 0.01 to meet domain check constraints (`amount > 0.00`).

3. **Synthetic / Augmented Data (Clearly Declared for Demonstration):**
   - Customer names and emails (generated deterministically from customer hash).
   - Customer phone numbers (generated with standard Brazilian state area codes / DDD).
   - Street names (synthetically formatted; Olist provides city, state, and zip prefix).
   - Vendor commercial names and GST numbers.
   - Regional warehouse hubs (8 representative fulfillment centers across Brazil).
   - Inventory stock levels and reorder thresholds (calculated based on sales velocity).
   - Product search tags (generated from category keywords, price tier, and popularity).
   - Payment transaction references (unique deterministic hash strings).

---

## 6. ETL Pipeline & Loading Workflow

The ETL pipeline converts raw immutable CSVs into normalized, dependency-safe relational data:

```
  data/raw/ (9 Olist CSVs)
             ↓
     etl/transform/ (Python Transformation Modules)
             ↓
  data/processed/ (12 Clean Intermediate CSVs)
             ↓
   Pre-Load Dry Run (27 Integrity Checks)
             ↓
     database/schema.sql (MySQL DDL Execution)
             ↓
     etl/load/ (13-Stage Topological Batch Loader)
             ↓
  multivendor_ecommerce_db (Live MySQL 8.4 Database)
             ↓
   Post-Load Validation (27 Live SQL Checks)
```

### 13-Stage Topological Loading Order

To satisfy all foreign key constraints without disabling integrity checks:

1. `CUSTOMER`
2. `CUSTOMER_PHONE`
3. `ADDRESS`
4. `VENDOR`
5. `CATEGORY` (Stage 1: Root categories where `parent_category_id IS NULL`)
6. `CATEGORY` (Stage 2: Child subcategories referencing root category IDs)
7. `WAREHOUSE`
8. `PRODUCT`
9. `PRODUCT_TAG`
10. `INVENTORY`
11. `ORDERS`
12. `ORDER_ITEM`
13. `PAYMENT`

**Total Database Records Loaded:** **778,244**

---

## 7. Project Directory Structure

```
multi-vendor-ecommerce-dbms/
│
├── data/
│   ├── raw/                       # Immutable source Olist CSV files (9 datasets)
│   └── processed/                 # Staged intermediate CSV files (12 clean datasets)
│
├── database/
│   ├── 01_create_database.sql     # Database creation and character set setup
│   ├── 02_create_tables.sql       # Table definitions for all 12 entities
│   ├── 03_constraints.sql         # Primary keys, foreign keys, unique, and check constraints
│   ├── 04_validation_queries.sql  # SQL queries to verify schema and constraints
│   ├── schema.sql                 # Unified master schema DDL
│   └── validate_schema.py         # Static schema validation script
│
├── documentation/
│   ├── final_schema_specification.md           # Phase 1: ER modeling & schema specification
│   ├── phase2_dataset_analysis_and_mapping.md  # Phase 2: Source data analysis & mapping
│   └── phase3_etl_reconciliation_report.md     # Phase 3: ETL reconciliation audit report
│
├── etl/
│   ├── load/
│   │   ├── __init__.py
│   │   ├── db_connection.py       # PyMySQL connection manager and DDL executor
│   │   └── loader.py              # 13-stage topological MySQL batch loader
│   ├── transform/
│   │   ├── __init__.py
│   │   ├── pipeline.py            # Master transformation pipeline orchestrator
│   │   ├── transform_catalog.py   # Transforms CATEGORY, PRODUCT, and PRODUCT_TAG
│   │   ├── transform_customers.py # Transforms CUSTOMER, CUSTOMER_PHONE, and ADDRESS
│   │   ├── transform_inventory.py # Transforms WAREHOUSE and INVENTORY
│   │   ├── transform_orders.py    # Transforms ORDERS and ORDER_ITEM
│   │   ├── transform_payments.py  # Transforms PAYMENT
│   │   └── transform_vendors.py   # Transforms VENDOR
│   ├── validate/
│   │   ├── __init__.py
│   │   └── validate_etl.py        # 27-check validation suite (Dry-run & Live MySQL)
│   ├── config.py                  # Configuration, directory paths, and database settings
│   ├── README.md                  # ETL pipeline documentation
│   └── run_etl.py                 # Master CLI runner
│
├── .env.example                   # Template environment configuration
├── .gitignore                     # Git exclusion rules (credentials, cache, virtual environments)
└── README.md                      # Project root documentation
```

---

## 8. Setup & Installation

### Prerequisites
- Python 3.10 or higher
- MySQL Server 8.4 (or 8.0+)
- MySQL Workbench (recommended for viewing schemas and running queries)

### 1. Configure Environment Variables
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Edit `.env` with your local MySQL credentials:
```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password
MYSQL_DATABASE=multivendor_ecommerce_db
```

### 2. Install Python Dependencies
```bash
pip install pymysql python-dotenv
```

---

## 9. Running the ETL Pipeline

The ETL pipeline can be executed using the master runner `etl/run_etl.py`:

### Option A: Complete End-to-End Pipeline
Extracts raw data, transforms CSVs, performs dry-run validation, initializes the MySQL schema, loads all 12 tables in 13 stages, and runs live database validation:
```bash
python -m etl.run_etl
```

### Option B: Dry-Run Validation Only (No Database Connection Required)
Runs extraction, transformation, and verifies the 27 integrity checks on `data/processed/` without modifying MySQL:
```bash
python -m etl.run_etl --dry-run-only
```

### Option C: Live MySQL Validation Only
Executes the 27 SQL integrity checks directly against the populated MySQL database:
```bash
python -m etl.run_etl --validate-only
```

### Option D: Skip Transformation (Fast Reload)
Loads directly from existing files in `data/processed/`:
```bash
python -m etl.run_etl --skip-transform
```

---

## 10. Automated Validation Suite (27 Checks)

The validation suite (`etl/validate/validate_etl.py`) enforces 27 relational and domain integrity checks across both staged CSVs and the live MySQL database:

| Check Group | Checks | Description | Result |
| :--- | :--- | :--- | :--- |
| **Row Count Integrity** | Checks 01–02 | Verifies exact row counts across all 12 tables and 96,096 unique customer accounts. | **PASS** |
| **Customer Integrity** | Checks 03–07 | Verifies customer email uniqueness, email formats, join dates ($\ge 2016$), phone composite PKs, FK integrity, and phone formats. | **PASS** |
| **Address Integrity** | Checks 08–10 | Verifies address composite PKs, FK references to customer, state code lengths (2 chars), and allowed address types. | **PASS** |
| **Vendor Integrity** | Checks 11–12 | Verifies vendor PK uniqueness, unique GST numbers, rating bounds ($1.00 \le r \le 5.00$), and GST string length. | **PASS** |
| **Category Hierarchy** | Checks 13–15 | Verifies 83 total categories (9 roots, 73 subcategories, 1 fallback), recursive FK validity, and zero self-references. | **PASS** |
| **Warehouse & Inventory** | Checks 16, 21–22 | Verifies warehouse capacities ($>0$), inventory composite PKs, FK integrity, and non-negative stock/reorder levels. | **PASS** |
| **Product & Tags** | Checks 17–20 | Verifies product single-vendor assignment, FK integrity to category and vendor, price validity ($\ge 0.00$), tag composite PKs, and tag lengths. | **PASS** |
| **Orders & Order Items** | Checks 23–26 | Verifies order FK references to customer, uppercase status normalization, order-item composite PKs, FK integrity, and conservation of all 112,650 physical units. | **PASS** |
| **Payment Integrity** | Check 27 | Verifies payment composite PKs, strictly positive amounts ($>0.00$), and unique transaction references. | **PASS** |

---

## 11. SQL Query Analysis Phase (Upcoming)

The SQL analysis phase will focus on executing comprehensive analytical queries against the populated `multivendor_ecommerce_db` database, demonstrating:
- Multi-table joins (inner, left, self-joins on recursive category hierarchy).
- Aggregate analysis (GMV by category, vendor sales volume, customer lifetime value).
- Nested subqueries and correlated subqueries.
- Window functions and ranking (top-selling products per category, vendor performance percentiles).
- Inventory reorder alerting and warehouse capacity utilization.
- Business performance questions.

*(Phase 4 query files and contributions will be added during the upcoming project phase.)*
