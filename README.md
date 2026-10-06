# Multi-Vendor E-Commerce & Inventory Management System

A relational database management system (DBMS) project modeling an online multi-vendor retail platform (similar to Amazon / Flipkart). Built with **MySQL 8.4**, populated via a Python ETL pipeline from the **Brazilian E-Commerce Public Dataset by Olist** (772,247 loaded records), and completed with an analytical SQL query suite (95 queries across 4 team members).

---

## 1. Project Overview

Large e-commerce platforms like Amazon or Flipkart deal with thousands of vendors, large product catalogs, dynamic inventory across multiple warehouses, customer delivery profiles, orders, and split-payment transactions all at once.

This project implements a normalized relational database in MySQL 8.4 to model that setup:
- Customer accounts with multiple phone numbers and delivery/billing addresses.
- Vendor profiles with review ratings and tax IDs.
- A product catalog structured as a two-level category tree (using a self-referencing foreign key).
- Product search tags normalized into 1NF.
- Regional warehouse hubs with inventory tracking and reorder levels.
- Order processing with line items (quantity and price preserved) and split payments.

Following database population, the project implements an analytical query suite of 95 SQL queries divided among four team members. These queries cover operational reporting, catalog search, warehouse logistics, and customer order analytics using multi-table joins, correlated subqueries, set comparisons, and recursive hierarchy navigation.

---

## 2. Objectives

1. **Relational Schema Design:** Design a normalized (up to 3NF / BCNF) schema with 12 tables in MySQL 8.4.
2. **Real-World Dataset:** Base the schema on real retail data using the Brazilian Olist dataset (9 raw CSVs, ~1.45M records total).
3. **Deterministic ETL Pipeline:** Build an ETL script in Python that cleans, transforms, and loads the data without touching the raw CSV files.
4. **Data Integrity:** Enforce primary and composite keys, foreign keys (with proper cascade/restrict rules), unique constraints, and check constraints.
5. **Automated Validation:** Verify everything with a 27-check test suite (runnable both against intermediate CSVs and the live MySQL database).
6. **Analytical Query Suite:** Implement an analytical SQL query suite across 4 team members covering joins, multi-level aggregations, subqueries, relational division, and self-referencing category tree traversals.

---

## 3. Technology Stack

- **Database Management System:** MySQL 8.4 LTS
- **Database Client:** MySQL Workbench / Command Line Client
- **Programming Language:** Python 3.10+
- **Database Driver:** PyMySQL
- **Environment Management:** python-dotenv
- **Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)
- **Query Capabilities:** Complex multi-table joins, correlated subqueries, set comparisons (ALL, SOME), relational division, and recursive hierarchy queries

---

## 4. Database Architecture (12 Tables)

The schema (`multivendor_ecommerce_db`) consists of 12 tables covering customers, vendors, catalog, inventory, and orders:

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

### Source Data vs. Generated Data

Since Olist is real transaction data from a single marketplace, a few fields needed for a full DBMS model (like warehouse stock levels or clean customer contact details) had to be derived or generated:

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

3. **Generated / Augmented Data:**
   - Customer names and emails (generated deterministically from customer hash).
   - Customer phone numbers (generated with standard Brazilian state area codes / DDD).
   - Street names (synthetically formatted; Olist provides city, state, and zip prefix).
   - Vendor commercial names and GST numbers.
   - Regional warehouse hubs (8 representative fulfillment centers across Brazil).
   - Inventory stock levels and reorder thresholds (calculated based on sales velocity).
   - Product search tags (generated from category keywords, price tier, and popularity).
   - Payment transaction references (unique deterministic hash strings).

---

## 6. ETL Pipeline & Loading Order

The pipeline transforms the raw Olist CSVs into normalized tables and loads them into MySQL in foreign-key order:

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

**Total Database Records Loaded:** **772,247**

---

## 7. Project Directory Structure

```
multi-vendor-ecommerce-dbms/
│
├── data/
│   ├── raw/                                 # Immutable source Olist CSV files (9 datasets, ~1.45M rows)
│   └── processed/                           # Staged intermediate CSV files (12 normalized tables, 772,247 rows)
│
├── database/
│   ├── 01_create_database.sql               # Database creation and character set setup (Phase 1 modular)
│   ├── 02_create_tables.sql                 # Table definitions for all 12 entities (Phase 1 modular)
│   ├── 03_constraints.sql                   # Primary keys, foreign keys, unique, and check constraints
│   ├── 04_validation_queries.sql            # Information schema queries verifying schema and constraints
│   ├── schema.sql                           # Complete monolithic schema definition script
│   ├── setup_database.sql                   # Safe database creation script (uses IF NOT EXISTS)
│   └── validate_schema.py                   # Static schema validation script
│
├── documentation/
│   ├── ER DIAGRAM.pdf                       # Relational Entity-Relationship diagram
│   └── final_schema_specification.md         # Phase 1: Conceptual ER modeling & relational schema specification
│
├── etl/
│   ├── load/
│   │   ├── __init__.py
│   │   ├── db_connection.py                 # PyMySQL connection manager and DDL executor
│   │   └── loader.py                        # 13-stage topological MySQL batch loader
│   ├── transform/
│   │   ├── __init__.py
│   │   ├── pipeline.py                      # Transformation pipeline orchestrator
│   │   ├── transform_catalog.py             # Transforms CATEGORY, PRODUCT, and PRODUCT_TAG
│   │   ├── transform_customers.py           # Transforms CUSTOMER, CUSTOMER_PHONE, and ADDRESS
│   │   ├── transform_inventory.py           # Transforms WAREHOUSE and INVENTORY
│   │   ├── transform_orders.py              # Transforms ORDERS and ORDER_ITEM
│   │   ├── transform_payments.py            # Transforms PAYMENT
│   │   └── transform_vendors.py             # Transforms VENDOR
│   ├── validate/
│   │   ├── __init__.py
│   │   └── validate_etl.py                  # 27-check validation suite (Dry-run & Live MySQL)
│   ├── config.py                            # Central path configurations and database credentials
│   ├── README.md                            # ETL pipeline documentation
│   └── run_etl.py                           # Main CLI pipeline runner
│
├── member1/
│   ├── Queries/                             # Member 1 analytical SQL queries (25 queries, Query-1 to Query-25)
│   └── Screenshots/                         # Execution output screenshots for Member 1 queries (25 captures)
│
├── member2/
│   ├── Queries/                             # Member 2 analytical SQL queries (20 queries, 01 to 20)
│   └── Screenshots/                         # Execution output screenshots for Member 2 queries (20 captures)
│
├── member3/
│   ├── Queries/                             # Member 3 analytical SQL queries (25 queries, Queries- 1 to Queries- 25)
│   └── Screenshots/                         # Execution output screenshots for Member 3 queries (25 captures)
│
├── member4/
│   ├── Queries/                             # Member 4 analytical SQL queries (25 queries, Query1 to Query25)
│   └── Screenshots/                         # Execution output screenshots for Member 4 queries (25 captures)
│
├── .env.example                             # Template environment configuration file
├── .gitignore                               # Git exclusion rules (credentials, cache, data artifacts)
├── requirements.txt                         # Required Python dependencies (pymysql, python-dotenv)
└── README.md                                # Root project documentation
```

---

## 8. Running Locally

Here is how to set up and populate the database from scratch:

### Prerequisites
- **MySQL Server 8.4** (or MySQL 8.0+) installed and running.
- **MySQL Workbench** (recommended GUI) or the MySQL Command Line Client.
- **Python 3.10+** installed.

---

### Step 1: Clone the Repository & Install Dependencies

Clone the project repository and install the minimal required Python libraries:

```powershell
# Windows PowerShell / Command Prompt
git clone https://github.com/Nityayyrrr/multi-vendor-ecommerce-dbms.git
cd multi-vendor-ecommerce-dbms

pip install -r requirements.txt
```

*(Only two external packages are needed: `pymysql` for MySQL connections and `python-dotenv` for reading `.env`.)*

---

### Step 2: Configure Database Credentials

Create a local `.env` configuration file from the provided template:

```powershell
# Windows PowerShell
Copy-Item .env.example .env

# Windows CMD
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` in any text editor and specify your local MySQL credentials:

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password
MYSQL_DATABASE=multivendor_ecommerce_db
```

> **Note on Security:** The `.env` file is listed in `.gitignore` and must never be committed to source control.

---

### Step 3: Create the Database Structure

You can create the database schema in one of two ways:

#### Method A: Using MySQL Workbench or MySQL CLI (Recommended)
Open `database/setup_database.sql` in MySQL Workbench and execute the script (or run via command line):

```powershell
mysql -u root -p < database/setup_database.sql
```

This creates `multivendor_ecommerce_db` and all 12 canonical tables with all primary keys, composite keys, foreign keys, unique constraints, check constraints, and indexes.

> **Safety Note:** `setup_database.sql` is non-destructive. It uses `CREATE DATABASE IF NOT EXISTS` and `CREATE TABLE IF NOT EXISTS` without `DROP TABLE` statements, making it safe to run without deleting existing data. Note that `IF NOT EXISTS` creates tables only if they are not already present; it does not alter or modify an already-existing table definition.

#### Method B: Automated Initialization via Python ETL
If you run the ETL pipeline (Step 4), the script automatically executes the schema creation step before loading data.

---

### Step 4: Load Data with the ETL Pipeline

Run the pipeline using `etl/run_etl.py`:

#### Option 1: Full Pipeline (Transform + Load + Validate)
Transforms the raw CSVs, runs dry-run checks, creates the schema, loads all 772,247 rows across the 13 stages, and validates the live database:

```powershell
python -m etl.run_etl
```

#### Option 2: Skip Transform (Use Existing CSVs)
If you already ran the transform step once, you can load directly from `data/processed/`:

```powershell
python -m etl.run_etl --skip-transform
```

---

### Step 5: Validate

Run the validation suite to make sure the data and schema loaded properly:

1. **Automated Live MySQL Validation (27 Integrity Checks):**
   ```powershell
   python -m etl.run_etl --validate-only
   ```
   *Verifies row counts across all 12 tables, zero orphan foreign keys, domain check constraints, and conserved unit counts.*

2. **Static Schema Validation:**
   ```powershell
   python database/validate_schema.py
   ```
   *Verifies all SQL scripts (`setup_database.sql`, `schema.sql`, and modular files) against the canonical ER architecture.*

3. **Manual Verification via MySQL Workbench:**
   Open and execute `database/04_validation_queries.sql` in MySQL Workbench to inspect table definitions, primary keys, foreign key cascade actions, unique indexes, and check constraints directly from MySQL's `information_schema`.

---

### Step 6: Run Analytical SQL Queries

Once the database is populated and validated, run the analytical queries using MySQL CLI or MySQL Workbench.

#### Running Individual Queries via MySQL CLI

Execute any individual query script against `multivendor_ecommerce_db`:

```powershell
# Windows PowerShell
mysql -u root -p multivendor_ecommerce_db < member1/Queries/Query-1.sql
mysql -u root -p multivendor_ecommerce_db < member2/Queries/01_product_category.sql
mysql -u root -p multivendor_ecommerce_db < "member3/Queries/Queries- 1.sql"
mysql -u root -p multivendor_ecommerce_db < member4/Queries/Query1.sql
```

#### Running an Entire Member Query Suite in PowerShell

To execute all queries for a team member in batch:

```powershell
# Run all Member 1 queries
Get-ChildItem -Path "member1/Queries/*.sql" | Sort-Object { [int]($_.BaseName -replace '\D') } | ForEach-Object {
    Write-Host "Running $($_.Name)..." -ForegroundColor Cyan
    Get-Content $_.FullName | mysql -u root -p multivendor_ecommerce_db
}
```

#### Running via MySQL Workbench
1. Open MySQL Workbench and connect to your local MySQL 8.4 instance.
2. Select **File > Open SQL Script...** and navigate to any file in `member1/Queries/`, `member2/Queries/`, `member3/Queries/`, or `member4/Queries/`.
3. Ensure `multivendor_ecommerce_db` is selected as the default schema (`USE multivendor_ecommerce_db;`).
4. Execute the query using `Ctrl + Shift + Enter`.
5. Compare the tabular result grid against the reference captures in the corresponding `Screenshots/` folder.

---

## 9. Automated Validation Suite (27 Checks)

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

## 10. Analytical SQL Query Suite

The analytical query phase is complete. The team implemented 95 SQL queries organized into 4 member directories, covering reporting, catalog exploration, inventory alerts, and customer behavior analysis:
- Multi-table joins (including self-joins on the category tree).
- Aggregations (sales by category, vendor volumes, customer spending).
- Subqueries and correlated subqueries.
- Window functions and ranking equivalents (running totals, percentiles, top-N filters).
- Inventory alerts (items below reorder level, warehouse utilization).

Each team member worked on an assigned query folder with accompanying execution screenshots:

| Directory | Member | Files | Numbering Range | Screenshots Folder |
| :--- | :--- | :---: | :--- | :--- |
| `member1/Queries/` | Member 1 (Aryan) | 25 | `Query-1.sql` to `Query-25.sql` | `member1/Screenshots/` (25 images) |
| `member2/Queries/` | Member 2 (Jahnavi Gautam) | 20 | `01_product_category.sql` to `20_products_using_exists.sql` | `member2/Screenshots/` (20 images) |
| `member3/Queries/` | Member 3 (Niyati Tyagi) | 25 | `Queries- 1.sql` to `Queries- 25.sql` | `member3/Screenshots/` (25 images) |
| `member4/Queries/` | Member 4 (Nityay Bhavsar) | 25 | `Query1.sql` to `Query25.sql` | `member4/Screenshots/` (25 images) |

---

## 11. Query Difficulty Tiers & Catalog

The query suite is structured across three difficulty tiers:
- **Tier 1 (Basic):** Single-table projections, basic filtering (`WHERE`, `BETWEEN`, `LIKE`), sorting (`ORDER BY`, `LIMIT`), and single-table aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).
- **Tier 2 (Intermediate):** Multi-table `INNER JOIN` and `LEFT JOIN` operations, `GROUP BY` with aggregate calculations, `HAVING` filters, date extractions (`YEAR`, `MONTH`), and scalar subqueries.
- **Tier 3 (Advanced):** Correlated subqueries (`EXISTS`, `NOT EXISTS`), set comparison predicates (`> ALL`, `> SOME`), relational division (finding entities associated with all items of a group), multi-level subqueries in `HAVING` and `FROM`, self-joins on the recursive category hierarchy, and multi-source financial reconciliation checks.

### Difficulty Tier Distribution

| Member | Directory | Total Queries | Tier 1 (Basic) | Tier 2 (Intermediate) | Tier 3 (Advanced) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Member 1 | `member1/Queries/` | 25 | 7 | 11 | 7 |
| Member 2 | `member2/Queries/` | 20 | 6 | 9 | 5 |
| Member 3 | `member3/Queries/` | 25 | 8 | 10 | 7 |
| Member 4 | `member4/Queries/` | 25 | 8 | 10 | 7 |
| **Total** | | **95** | **29** | **40** | **26** |

---

### Member 1 Query Catalog (Aryan)

| File | Business Question / Purpose | Tier | SQL Concepts Used | Tables Referenced |
| :--- | :--- | :---: | :--- | :--- |
| `Query-1.sql` | Products with their assigned vendor names | Tier 2 | INNER JOIN | `product`, `vendor` |
| `Query-2.sql` | Products priced above overall catalog average | Tier 2 | Scalar Subquery, AVG() | `product` |
| `Query-3.sql` | Full customer account profiles | Tier 1 | SELECT * | `customer` |
| `Query-4.sql` | Warehouse holding highest count of low-stock items | Tier 2 | INNER JOIN, GROUP BY, COUNT(), ORDER BY, LIMIT | `warehouse`, `inventory` |
| `Query-5.sql` | Order count per customer account | Tier 2 | LEFT JOIN, GROUP BY, COUNT() | `customer`, `orders` |
| `Query-6.sql` | Top 10 lowest-priced products | Tier 1 | ORDER BY price ASC, LIMIT 10 | `product` |
| `Query-7.sql` | Vendors with rating higher than all vendors rated below 3.0 | Tier 3 | > ALL (Subquery) | `vendor` |
| `Query-8.sql` | Warehouses and stock items including empty allocations | Tier 2 | LEFT JOIN | `warehouse`, `inventory` |
| `Query-9.sql` | Average vendor review rating across marketplace | Tier 1 | Aggregate AVG() | `vendor` |
| `Query-10.sql` | Relational division: customers buying every product in category 5 | Tier 3 | 4-table JOIN, GROUP BY, HAVING COUNT = Subquery | `customer`, `orders`, `order_item`, `product` |
| `Query-11.sql` | Gross revenue generated per vendor | Tier 2 | 3-table JOIN, GROUP BY, SUM(quantity * price) | `vendor`, `product`, `order_item` |
| `Query-12.sql` | Product search matching keyword 'bed' | Tier 1 | LIKE '%bed%' | `product` |
| `Query-13.sql` | Highest-priced product within each category | Tier 3 | JOIN with Subquery (GROUP BY MAX price) | `category`, `product` |
| `Query-14.sql` | Line items with quantity and historical purchase price | Tier 2 | INNER JOIN | `order_item`, `product` |
| `Query-15.sql` | Products in price range between 50 and 200 | Tier 1 | BETWEEN 50 AND 200, ORDER BY | `product` |
| `Query-16.sql` | Customers spending above the average customer spending | Tier 3 | 3-table JOIN, GROUP BY, HAVING > Subquery on Subquery | `customer`, `orders`, `payment` |
| `Query-17.sql` | Products distributed across more than one warehouse | Tier 2 | INNER JOIN, GROUP BY, HAVING COUNT > 1 | `product`, `inventory` |
| `Query-18.sql` | Product count per category including empty categories | Tier 2 | LEFT JOIN, GROUP BY, COUNT(), ORDER BY DESC | `category`, `product` |
| `Query-19.sql` | Products stocked in every single warehouse hub | Tier 3 | Correlated Subqueries (Double NOT EXISTS) | `product`, `warehouse`, `inventory` |
| `Query-20.sql` | Annual order volume trends | Tier 1 | YEAR(order_date), GROUP BY, COUNT() | `orders` |
| `Query-21.sql` | Total count of catalog products | Tier 1 | Aggregate COUNT(*) | `product` |
| `Query-22.sql` | Active vendors with no catalog items priced at or below 100 | Tier 3 | Correlated EXISTS and NOT EXISTS | `vendor`, `product` |
| `Query-23.sql` | Inactive customers who have never placed an order | Tier 2 | LEFT JOIN WHERE order_id IS NULL | `customer`, `orders` |
| `Query-24.sql` | Delivered orders filter | Tier 1 | WHERE status = 'delivered' | `orders` |
| `Query-25.sql` | Financial reconciliation: order item total vs payment total | Tier 3 | Multi-table LEFT JOIN Subqueries, COALESCE, ABS() | `orders`, `order_item`, `payment` |

---

### Member 2 Query Catalog (Jahnavi Gautam)

| File | Business Question / Purpose | Tier | SQL Concepts Used | Tables Referenced |
| :--- | :--- | :---: | :--- | :--- |
| `01_product_category.sql` | Product names mapped to category names | Tier 2 | INNER JOIN | `product`, `category` |
| `02_vendor_above_average_rating.sql` | Vendors with rating above marketplace average | Tier 2 | Scalar Subquery with AVG() | `vendor` |
| `03_customer_id_email.sql` | Customer profile identifiers and emails | Tier 1 | SELECT customer_id, email | `customer` |
| `04_customers_never_ordered.sql` | Customers with no purchase records | Tier 3 | Correlated Subquery (NOT EXISTS) | `customer`, `orders` |
| `05_payment_order_status.sql` | Payment identifiers and transaction statuses | Tier 1 | SELECT payment_id, order_id, status | `payment` |
| `06_vendors_rating_above_4.sql` | Vendors rated above 4.0 | Broken | Empty file (0 bytes) | None |
| `07_products_greater_than_all_category.sql` | Products priced above all products in Category 1 | Tier 3 | > ALL (Subquery) | `product` |
| `08_total_quantity_purchased_per_product.sql` | Total units ordered per product | Tier 2 | INNER JOIN, GROUP BY, SUM(quantity) | `product`, `order_item` |
| `09_products_ascending_price.sql` | Products ordered by price ascending | Tier 1 | ORDER BY price ASC | `product` |
| `10_category_with_largest_product_count.sql` | Category with the largest number of products | Tier 2 | INNER JOIN, GROUP BY, COUNT(), ORDER BY, LIMIT 1 | `category`, `product` |
| `11_vendors_with_product_count.sql` | Total products offered per vendor | Tier 2 | LEFT JOIN, GROUP BY, COUNT() | `vendor`, `product` |
| `12_distinct_customer_states.sql` | Unique customer states in address book | Tier 1 | SELECT DISTINCT state | `address` |
| `13_customers_with_orders_exists.sql` | Customers who placed at least one order | Tier 3 | Correlated Subquery (EXISTS) | `customer`, `orders` |
| `14_products_and_warehouses.sql` | Products mapped to fulfillment warehouses | Tier 2 | 3-table INNER JOIN | `product`, `inventory`, `warehouse` |
| `15_total_vendors.sql` | Total count of registered marketplace vendors | Tier 1 | Aggregate COUNT(*) | `vendor` |
| `16_vendor_highest_avg_product_price.sql` | Vendor with highest average item price | Tier 2 | INNER JOIN, GROUP BY, AVG(), ORDER BY, LIMIT 1 | `vendor`, `product` |
| `17_categories_no_products.sql` | Categories that contain zero products | Tier 2 | LEFT JOIN WHERE product_id IS NULL | `category`, `product` |
| `18_payments_by_payment_mode.sql` | Payment count grouped by payment method | Broken | Empty file (0 bytes) | None |
| `19_orders_date_range.sql` | Orders placed during calendar year 2024 | Tier 1 | BETWEEN '2024-01-01' AND '2024-12-31' *(0 rows)* | `orders` |
| `20_products_using_exists.sql` | Products that have been ordered at least once | Tier 3 | Correlated Subquery (EXISTS) | `product`, `order_item` |

---

### Member 3 Query Catalog (Niyati Tyagi)

| File | Business Question / Purpose | Tier | SQL Concepts Used | Tables Referenced |
| :--- | :--- | :---: | :--- | :--- |
| `Queries- 1.sql` | Order records with customer contact information | Tier 2 | INNER JOIN | `orders`, `customer` |
| `Queries- 2.sql` | Payments exceeding average transaction amount | Tier 2 | Scalar Subquery with AVG() | `payment` |
| `Queries- 3.sql` | Products priced above 100 | Tier 1 | WHERE price > 100 | `product` |
| `Queries- 4.sql` | Highest-priced product within its own category | Tier 3 | Correlated Subquery (MAX per category) | `product` |
| `Queries- 5.sql` | Product inventory stock and warehouse location | Tier 2 | 3-table INNER JOIN | `inventory`, `product`, `warehouse` |
| `Queries- 6.sql` | Total count of customer accounts | Tier 1 | Aggregate COUNT(*) | `customer` |
| `Queries- 7.sql` | Vendors selling strictly products priced over 100 | Tier 3 | Correlated Subquery (NOT EXISTS <= 100) | `vendor`, `product` |
| `Queries- 8.sql` | Aggregated inventory stock per warehouse | Tier 2 | GROUP BY, SUM(stock_quantity) | `inventory` |
| `Queries- 9.sql` | Warehouse locations and aggregated physical units | Tier 2 | INNER JOIN, GROUP BY, SUM() | `warehouse`, `inventory` |
| `Queries-10.sql` | Customer accounts sorted alphabetically by email | Tier 1 | ORDER BY email ASC | `customer` |
| `Queries- 11.sql` | Relational division: customers buying every product in category 3 | Tier 3 | Correlated Subqueries (Double NOT EXISTS) | `customer`, `product`, `orders`, `order_item` |
| `Queries- 12.sql` | Total products per category including empty groups | Tier 2 | LEFT JOIN, GROUP BY, COUNT() | `category`, `product` |
| `Queries- 13.sql` | All items classified under category 3 | Tier 1 | WHERE category_id = 3 | `product` |
| `Queries - 14.sql`| Monthly order distribution across the calendar year | Tier 2 | MONTH(order_date), GROUP BY, COUNT() | `orders` |
| `Queries- 15.sql` | Count of distinct Brazilian states represented | Tier 1 | COUNT(DISTINCT state) | `address` |
| `Queries- 16.sql` | Category with highest average product price | Tier 2 | GROUP BY, AVG(), ORDER BY DESC, LIMIT 1 | `product` |
| `Queries- 17.sql` | Catalog products currently unstocked in any warehouse | Tier 3 | Correlated Subquery (NOT EXISTS) | `product`, `inventory` |
| `Queries- 18.sql` | Top 10 most expensive items in product catalog | Tier 1 | ORDER BY price DESC, LIMIT 10 | `product` |
| `Queries- 19.sql` | Products priced higher than at least one item in category 5 | Tier 3 | > SOME (Subquery) | `product` |
| `Queries- 20.sql` | Line item order breakdown with customer and product names | Tier 2 | 4-table INNER JOIN | `orders`, `customer`, `order_item`, `product` |
| `Queries- 21.sql` | Total sum of payments received | Tier 1 | Aggregate SUM(amount) | `payment` |
| `Queries- 22.sql` | Customers ordering more frequently than customer average | Tier 3 | GROUP BY, HAVING > Subquery on Subquery | `orders` |
| `Queries- 23.sql` | Total customer spending across all orders | Tier 2 | 3-table INNER JOIN, GROUP BY, SUM(amount) | `customer`, `orders`, `payment` |
| `Queries- 24.sql` | Customers with domain filter `@vitbhopal.ac.in` | Tier 1 | LIKE '%@vitbhopal.ac.in' *(0 rows)* | `customer` |
| `Queries- 25.sql` | Top product by total sales volume | Tier 2 | INNER JOIN, GROUP BY, SUM(quantity), LIMIT 1 | `product`, `order_item` |

---

### Member 4 Query Catalog (Nityay Bhavsar)

| File | Business Question / Purpose | Tier | SQL Concepts Used | Tables Referenced |
| :--- | :--- | :---: | :--- | :--- |
| `Query1.sql` | Master list of all registered vendors | Tier 1 | SELECT * | `vendor` |
| `Query2.sql` | Products priced above 100 | Tier 1 | WHERE price > 100 | `product` |
| `Query3.sql` | Total count of registered customers | Tier 1 | Aggregate COUNT(*) | `customer` |
| `Query4.sql` | Catalog items ordered by price ascending | Tier 1 | ORDER BY price ASC | `product` |
| `Query5.sql` | Payments processed via credit card | Tier 1 | WHERE mode = 'Credit Card' *(0 rows)* | `payment` |
| `Query6.sql` | Minimum and maximum catalog product prices | Tier 1 | Aggregates MIN(), MAX() | `product` |
| `Query7.sql` | Orders with delivered status | Tier 1 | WHERE status = 'Delivered' | `orders` |
| `Query8.sql` | Product search matching name pattern | Tier 1 | LIKE '%Toys Product #009AF1%' | `product` |
| `Query9.sql` | Order line items with quantity and unit price | Tier 2 | INNER JOIN | `order_item`, `product` |
| `Query10.sql` | Warehouse hubs and distinct product counts | Tier 2 | LEFT JOIN, GROUP BY, COUNT() | `warehouse`, `inventory` |
| `Query11.sql` | Products linked with vendor name and category name | Tier 2 | 3-table INNER JOIN | `product`, `vendor`, `category` |
| `Query12.sql` | Total units ordered per product | Tier 2 | LEFT JOIN, GROUP BY, COALESCE(SUM(), 0) | `product`, `order_item` |
| `Query13.sql` | Total units ordered per product *(Duplicate of Q12)* | Tier 2 | Duplicate logic and text of Query12 | `product`, `order_item` |
| `Query14.sql` | Customer order volume including zero-order accounts | Tier 2 | LEFT JOIN, GROUP BY, COUNT() | `customer`, `orders` |
| `Query15.sql` | Products with warehouse locations and stock levels | Tier 2 | 3-table INNER JOIN | `product`, `inventory`, `warehouse` |
| `Query16.sql` | Customer order volume *(Duplicate logic of Q14)* | Tier 2 | Duplicate query without header comment | `customer`, `orders` |
| `Query17.sql` | Sales revenue generated per vendor | Tier 2 | 3-table INNER JOIN, GROUP BY, SUM() | `vendor`, `product`, `order_item` |
| `Query18.sql` | Customers ordering above average customer frequency | Tier 3 | LEFT JOIN, GROUP BY, HAVING > Subquery | `customer`, `orders` |
| `Query19.sql` | Products stocked across all warehouse locations | Tier 3 | INNER JOIN, GROUP BY, HAVING COUNT = Subquery | `product`, `inventory`, `warehouse` |
| `Query20.sql` | Vendors with rating higher than at least one vendor | Tier 3 | > SOME (Subquery) | `vendor` |
| `Query21.sql` | Customers who placed at least one order | Tier 3 | Correlated Subquery (EXISTS) | `customer`, `orders` |
| `Query22.sql` | Category containing the largest number of products | Tier 2 | INNER JOIN, GROUP BY, COUNT(), ORDER BY, LIMIT 1 | `category`, `product` |
| `Query23.sql` | Products priced above their own category average | Tier 3 | Correlated Subquery (AVG per category) | `product`, `category` |
| `Query24.sql` | Customers who have never placed an order | Tier 3 | Correlated Subquery (NOT EXISTS) | `customer`, `orders` |
| `Query25.sql` | Intermediate categories with both parent and child | Tier 3 | Self-Join on category tree | `category` |

---

## 12. Team Members & Contributions

The project was completed by a four-member team, with tasks divided across relational modeling, Python ETL engineering, constraint validation, and analytical SQL query formulation:

| Team Member | Registration No. | GitHub / Branch | Assigned Module | Deliverables |
| :--- | :--- | :--- | :--- | :--- |
| **Aryan** | *(Project Lead)* | `main` | Database Architecture, Python ETL, Member 1 Analysis | Relational schema design, 13-stage topological ETL pipeline, 27-check validation suite, Member 1 SQL queries (1–25) |
| **Jahnavi Gautam** | 25BCE10361 | `25BCE10361` | Member 2 Analysis | Member 2 analytical SQL queries (01–20) and query execution screenshots |
| **Niyati Tyagi** | 25BCE11103 | `member3` | Member 3 Analysis | Member 3 analytical SQL queries (1–25) and query execution screenshots |
| **Nityay Bhavsar** | 24BCG10064 | `SQL_QUERIES_24BCG10064` | Member 4 Analysis | Member 4 analytical SQL queries (1–25) and query execution screenshots |

---

## 13. Known Limitations & Technical Notes

1. **Member 2 Query Count:** Member 2 includes 20 query scripts (`01` through `20`). Queries 21 to 25 were not submitted to the repository.
2. **Empty Query Files:** Member 2 contains two 0-byte files (`06_vendors_rating_above_4.sql` and `18_payments_by_payment_mode.sql`).
3. **Duplicate Scripts in Member 4:** `Query12.sql` and `Query13.sql` share identical SQL text and comments. `Query14.sql` and `Query16.sql` share identical query logic.
4. **Order Status Casing:** The ETL normalizes order status strings to uppercase (`DELIVERED`, `SHIPPED`, `CANCELLED`). `Query-24.sql` (Member 1) uses lowercase `'delivered'`, and `Query7.sql` (Member 4) uses Title Case `'Delivered'`. On default case-insensitive collations these resolve, but explicit uppercase matching aligns directly with database constraints.
5. **Payment Mode Casing:** Payment modes in `payment.mode` are stored as lowercase strings (`credit_card`, `boleto`, `voucher`, `debit_card`). `Query5.sql` (Member 4) filters for `'Credit Card'`, which returns zero rows against the loaded database.
6. **Date Range Bounds:** The Olist dataset covers orders between 2016 and 2018. `19_orders_date_range.sql` (Member 2) specifies dates in 2024, returning zero rows on this historical dataset.
7. **Email Domain Filtering:** Synthetic customer emails generated during ETL use `@ecommerce-demo.com`. `Queries- 24.sql` (Member 3) queries for `@vitbhopal.ac.in`, returning zero records.
8. **Stored Routines:** The analytical suite consists entirely of SQL `SELECT` queries (DQL). Views, stored procedures, triggers, and transactions were not introduced into the repository.

---

## 14. Acknowledgements & References

- **Dataset:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle. Contains 100k real marketplace orders from 2016 to 2018.
- **Database System:** Oracle MySQL 8.4 LTS Reference Manual for relational storage engine specifications, indexing, and window function support.
- **Academic Context:** Course project for Relational Database Management Systems (DBMS), VIT Bhopal University.

