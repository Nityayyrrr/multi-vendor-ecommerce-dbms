# Phase 2 — Olist Dataset Analysis and Source-to-Target Mapping Report
## Multi-Vendor E-Commerce & Inventory Management System

**Target Database:** MySQL 8.4 LTS (`multivendor_ecommerce_db`)  
**Dataset Analyzed:** Brazilian E-Commerce Public Dataset by Olist (9 Raw CSV Files in `data/raw/`)  
**Project Phase:** Phase 2 (Dataset Investigation, Field Mapping & Synthetic Augmentation Design)  

---

## 1. Dataset Presence & Source Inventory

All 9 source files of the Brazilian E-Commerce Public Dataset by Olist are present in the `data/raw/` directory. No source files were modified, moved, or cleaned in place; the raw data remains strictly immutable.

### Source Files Inventory Table

| # | Source CSV File Name | File Size (Bytes) | Row Count (Data Rows) | Column Count | Inferred Candidate Key | Target Schema Contribution |
| :- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `olist_customers_dataset.csv` | 9,033,957 | **99,441** | 5 | `customer_id` (Unique per order) | `CUSTOMER`, `ADDRESS`, `CUSTOMER_PHONE` |
| 2 | `olist_orders_dataset.csv` | 17,654,914 | **99,441** | 8 | `order_id` (100% Unique) | `ORDERS`, `PAYMENT` (dates), `CUSTOMER` (join_date) |
| 3 | `olist_order_items_dataset.csv` | 15,438,671 | **112,650** | 7 | Composite: `(order_id, order_item_id)` | `ORDER_ITEM`, `PRODUCT` (vendor & price derivation), `INVENTORY` |
| 4 | `olist_order_payments_dataset.csv` | 5,777,138 | **103,886** | 5 | Composite: `(order_id, payment_sequential)` | `PAYMENT` |
| 5 | `olist_products_dataset.csv` | 2,379,446 | **32,951** | 9 | `product_id` (100% Unique) | `PRODUCT`, `CATEGORY`, `PRODUCT_TAG`, `INVENTORY` |
| 6 | `olist_sellers_dataset.csv` | 174,703 | **3,095** | 4 | `seller_id` (100% Unique) | `VENDOR` |
| 7 | `product_category_name_translation.csv` | 2,613 | **71** | 2 | `product_category_name` (100% Unique) | `CATEGORY` (English taxonomy) |
| 8 | `olist_order_reviews_dataset.csv` | 14,451,670 | **99,224** | 7 | Composite: `(review_id, order_id)` | `VENDOR` (Derived merchant review ratings) |
| 9 | `olist_geolocation_dataset.csv` | 61,273,883 | **1,000,163** | 5 | None (spatial coordinate lookup) | `ADDRESS` (spatial lookup), `WAREHOUSE` (hub topology) |
| — | **TOTAL** | **126,186,995** | **1,450,922** | **47** | — | **Direct & Derived Feeder for 12 Target Tables** |

---

## 2. Detailed Inspection of Every Olist Source CSV

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                OLIST SOURCE DATA FLOW GRAPH                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   ┌──────────────────────────┐                    ┌───────────────────────────────┐    │
│   │ olist_customers_dataset  │◄────( 1 : 1 )──────┤      olist_orders_dataset     │    │
│   └────────────┬─────────────┘                    └───────┬───────────────┬───────┘    │
│                │ ( N : 1 )                                │ ( 1 : N )     │ ( 1 : N )  │
│                ▼                                          ▼               ▼            │
│   ┌──────────────────────────┐                    ┌───────────────┐ ┌──────────────┐   │
│   │ olist_geolocation_dataset│                    │olist_order_   │ │olist_order_  │   │
│   └────────────▲─────────────┘                    │payments       │ │reviews       │   │
│                │ ( N : 1 )                        └───────────────┘ └──────────────┘   │
│   ┌────────────┴─────────────┐                                                         │
│   │   olist_sellers_dataset  │◄───┐                                                    │
│   └──────────────────────────┘    │                                                    │
│                                   │ ( N : 1 )                                          │
│   ┌──────────────────────────┐    │          ┌────────────────────────────────┐        │
│   │  olist_products_dataset  │◄───┼──(N : 1)─┤   olist_order_items_dataset    │        │
│   └────────────┬─────────────┘    │          └────────────────────────────────┘        │
│                │ ( N : 1 )        │                                                    │
│                ▼                  │                                                    │
│   ┌──────────────────────────┐    │                                                    │
│   │  product_category_name_  │    │                                                    │
│   │  translation.csv         │    │                                                    │
│   └──────────────────────────┘    │                                                    │
│                                   │                                                    │
└───────────────────────────────────┴────────────────────────────────────────────────────┘
```

### 2.1 `olist_customers_dataset.csv`
* **Row Count:** 99,441
* **Columns & Inferred Types:**
  1. `customer_id` — `CHAR(32)` (Hexadecimal token; 99,441 unique values)
  2. `customer_unique_id` — `CHAR(32)` (Hexadecimal real-customer ID; 96,096 unique values)
  3. `customer_zip_code_prefix` — `CHAR(5)` (Postal code prefix; 14,994 unique values)
  4. `customer_city` — `VARCHAR(40)` (City name; 4,119 unique values)
  5. `customer_state` — `CHAR(2)` (Brazilian state abbreviation; 27 unique values)
* **Primary Key Candidate:** `customer_id` (100% unique per row).
* **Foreign Keys:** `customer_zip_code_prefix` $\rightarrow$ `olist_geolocation_dataset(geolocation_zip_code_prefix)`.
* **Missing Values:** 0 nulls across all 5 columns (0.00%).
* **Duplicates:** 0 duplicate rows; 2,997 `customer_unique_id` values appear 2 to 17 times.
* **Relationships:** Strict 1:1 match with `olist_orders_dataset.csv` on `customer_id`.
* **Contributes To:** `CUSTOMER`, `ADDRESS`, `CUSTOMER_PHONE`.

### 2.2 `olist_orders_dataset.csv`
* **Row Count:** 99,441
* **Columns & Inferred Types:**
  1. `order_id` — `CHAR(32)` (Hexadecimal UUID; 99,441 unique values)
  2. `customer_id` — `CHAR(32)` (Hexadecimal customer token; 99,441 unique values)
  3. `order_status` — `VARCHAR(20)` (Status string; 8 unique values: `delivered`: 96,478, `shipped`: 1,107, `canceled`: 625, `unavailable`: 609, `invoiced`: 314, `processing`: 301, `created`: 5, `approved`: 2)
  4. `order_purchase_timestamp` — `DATETIME` (Range: `2016-09-04 21:15:19` to `2018-10-17 17:30:18`)
  5. `order_approved_at` — `DATETIME` (160 nulls; 0.16%)
  6. `order_delivered_carrier_date` — `DATETIME` (1,783 nulls; 1.79%)
  7. `order_delivered_customer_date` — `DATETIME` (2,965 nulls; 2.98%)
  8. `order_estimated_delivery_date` — `DATETIME` (0 nulls)
* **Primary Key Candidate:** `order_id` (100% unique, 0 nulls).
* **Foreign Keys:** `customer_id` $\rightarrow$ `olist_customers_dataset(customer_id)`.
* **Missing Values:** 160 missing approvals, 1,783 missing carrier delivery dates, 2,965 missing customer delivery dates (consistent with undelivered/canceled order statuses).
* **Duplicates:** 0 duplicate rows.
* **Relationships:** 1:1 with `olist_customers_dataset.csv`; 1:N with `olist_order_items_dataset.csv` and `olist_order_payments_dataset.csv`.
* **Contributes To:** `ORDERS`, `CUSTOMER` (`join_date`), `PAYMENT` (`payment_date`).

### 2.3 `olist_order_items_dataset.csv`
* **Row Count:** 112,650
* **Columns & Inferred Types:**
  1. `order_id` — `CHAR(32)` (98,666 distinct orders)
  2. `order_item_id` — `INT` (Sequential item index: 1 to 21)
  3. `product_id` — `CHAR(32)` (32,951 distinct products)
  4. `seller_id` — `CHAR(32)` (3,095 distinct sellers)
  5. `shipping_limit_date` — `DATETIME`
  6. `price` — `DECIMAL(10,2)` (Range: 0.85 to 6,735.00)
  7. `freight_value` — `DECIMAL(10,2)` (Range: 0.00 to 409.68)
* **Primary Key Candidate:** Composite `(order_id, order_item_id)`.
* **Foreign Keys:**
  * `order_id` $\rightarrow$ `olist_orders_dataset(order_id)`
  * `product_id` $\rightarrow$ `olist_products_dataset(product_id)`
  * `seller_id` $\rightarrow$ `olist_sellers_dataset(seller_id)`
* **Missing Values:** 0 nulls across all columns (0.00%).
* **Composite Key Investigation `(order_id, product_id)`:**
  * Total composite pairs `(order_id, product_id)` = **102,425** unique pairs.
  * Exactly **7,088** pairs appear more than once (2 to 20 times), representing **10,225 redundant rows** that will be aggregated into a single row with `quantity = COUNT(*)`.
  * Unit prices for the same `(order_id, product_id)` in the raw data have **zero price discrepancies** (`price_discrepancy_count = 0`).
* **Contributes To:** `ORDER_ITEM`, `PRODUCT` (vendor & price linkage), `INVENTORY`.

### 2.4 `olist_order_payments_dataset.csv`
* **Row Count:** 103,886
* **Columns & Inferred Types:**
  1. `order_id` — `CHAR(32)` (99,440 distinct orders)
  2. `payment_sequential` — `INT` (Sequential payment index: 1 to 29; 0 duplicates per order)
  3. `payment_type` — `VARCHAR(20)` (`credit_card`: 76,795, `boleto`: 19,784, `voucher`: 5,775, `debit_card`: 1,529, `not_defined`: 3)
  4. `payment_installments` — `INT` (Range: 0 to 24)
  5. `payment_value` — `DECIMAL(10,2)` (Range: 0.00 to 13,664.08)
* **Primary Key Candidate:** Composite `(order_id, payment_sequential)`.
* **Foreign Keys:** `order_id` $\rightarrow$ `olist_orders_dataset(order_id)`.
* **Missing Values:** 0 nulls across all columns (0.00%).
* **Anomalies Identified:**
  * Exactly **9 rows** have `payment_value = 0.00` (6 vouchers, 3 not_defined). (Must be sanitized to satisfy target schema constraint `chk_payment_amount: amount > 0.00`).
  * Exactly 1 order in `orders` has 0 payment rows (`order_id = 'bfbd0f9bdef84302105ad712db648a6c'`).
* **Contributes To:** `PAYMENT`.

### 2.5 `olist_products_dataset.csv`
* **Row Count:** 32,951
* **Columns & Inferred Types:**
  1. `product_id` — `CHAR(32)` (32,951 unique values)
  2. `product_category_name` — `VARCHAR(50)` (73 distinct categories; 610 nulls = 1.85%)
  3. `product_name_lenght` — `INT` (610 nulls = 1.85%)
  4. `product_description_lenght` — `INT` (610 nulls = 1.85%)
  5. `product_photos_qty` — `INT` (610 nulls = 1.85%)
  6. `product_weight_g` — `DECIMAL(10,2)` (2 nulls = 0.01%)
  7. `product_length_cm` — `DECIMAL(10,2)` (2 nulls = 0.01%)
  8. `product_height_cm` — `DECIMAL(10,2)` (2 nulls = 0.01%)
  9. `product_width_cm` — `DECIMAL(10,2)` (2 nulls = 0.01%)
* **Primary Key Candidate:** `product_id` (100% unique).
* **Foreign Keys:** `product_category_name` $\rightarrow$ `product_category_name_translation(product_category_name)`.
* **Missing Values:** 610 products have missing category and metadata; 2 products have missing dimensions/weight.
* **Unused Source Columns:** Columns 3 through 9 (`product_name_lenght`, `product_description_lenght`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`) are raw physical dimensions not required by our target `PRODUCT` relational table.
* **Contributes To:** `PRODUCT`, `CATEGORY`, `PRODUCT_TAG`, `INVENTORY`.

### 2.6 `olist_sellers_dataset.csv`
* **Row Count:** 3,095
* **Columns & Inferred Types:**
  1. `seller_id` — `CHAR(32)` (3,095 unique values)
  2. `seller_zip_code_prefix` — `CHAR(5)` (2,246 distinct prefixes)
  3. `seller_city` — `VARCHAR(40)` (611 distinct cities)
  4. `seller_state` — `CHAR(2)` (23 distinct states; Top: SP=1,849, PR=349, MG=244, SC=190, RJ=171)
* **Primary Key Candidate:** `seller_id` (100% unique).
* **Foreign Keys:** `seller_zip_code_prefix` $\rightarrow$ `olist_geolocation_dataset(geolocation_zip_code_prefix)`.
* **Missing Values:** 0 nulls across all columns (0.00%).
* **Contributes To:** `VENDOR`.

### 2.7 `product_category_name_translation.csv`
* **Row Count:** 71
* **Columns & Inferred Types:**
  1. `product_category_name` — `VARCHAR(50)` (Portuguese category slug; 71 unique values)
  2. `product_category_name_english` — `VARCHAR(50)` (English translated name; 71 unique values)
* **Primary Key Candidate:** `product_category_name` (100% unique).
* **Source Anomaly:** UTF-8 Byte Order Mark (`\ufeff`) on column header (`\ufeffproduct_category_name`).
* **Coverage Gap:** 2 categories in `olist_products_dataset.csv` (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) are missing from this file and must be translated explicitly.
* **Contributes To:** `CATEGORY`.

### 2.8 `olist_order_reviews_dataset.csv`
* **Row Count:** 99,224 (unique review entries)
* **Columns:** `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`.
* **Utility in Target Schema:** The canonical schema does not contain an `ORDER_REVIEW` table. However, review scores (1 to 5) link via `order_id` $\rightarrow$ `order_items` $\rightarrow$ `seller_id` to compute realistic, data-driven average merchant ratings for the `VENDOR.rating` column (`rating = AVG(review_score)`).

### 2.9 `olist_geolocation_dataset.csv`
* **Row Count:** 1,000,163
* **Columns:** `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state`.
* **Utility in Target Schema:** Reference lookup table for geographic validation, synthesizing realistic addresses, and defining regional fulfillment distribution hubs for `WAREHOUSE`.

---

## 3. Comprehensive Source-to-Target Column Mapping

Below is the complete, exhaustive mapping for all 12 target tables and every single attribute.

### Table 1: `CUSTOMER`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `PRIMARY KEY` | `olist_customers_dataset.csv` (`customer_unique_id`) | **DIRECT SOURCE / MAPPED** | Mapped from distinct `customer_unique_id` (96,096 unique human customer accounts). |
| `name` | `VARCHAR(100)` | `NOT NULL` | `olist_customers_dataset.csv` (`customer_unique_id`) | **SYNTHETIC / AUGMENTED** | Deterministically synthesized realistic human full names generated via a seeded faker/algorithmic name dictionary keyed on `customer_unique_id`. |
| `email` | `VARCHAR(150)` | `NOT NULL, UNIQUE, CHECK` | `olist_customers_dataset.csv` (`customer_unique_id`) | **SYNTHETIC / AUGMENTED** | Deterministically synthesized email address in the format `customer_<customer_unique_id_prefix>@domain.com`, guaranteed unique across all 96,096 customers and satisfying check constraint `chk_customer_email_format`. |
| `join_date` | `DATETIME` | `NOT NULL, CHECK (>= 2016-01-01)` | `olist_orders_dataset.csv` (`order_purchase_timestamp`) | **DERIVED** | Derived as the earliest lifetime order purchase timestamp for that `customer_unique_id` (minimum date `2016-09-04`, fully satisfying `>= 2016-01-01`). |

---

### Table 2: `CUSTOMER_PHONE`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> customer` | `olist_customers_dataset.csv` (`customer_unique_id`) | **DIRECT SOURCE** | Foreign key linking to `CUSTOMER.customer_id` (`customer_unique_id`). |
| `phone_number` | `VARCHAR(20)` | `PRIMARY KEY, CHECK (len >= 8)` | `olist_customers_dataset.csv` (`customer_state`, `customer_unique_id`) | **SYNTHETIC / AUGMENTED** | Deterministically synthesized Brazilian E.164 phone number utilizing state area codes (DDD) (e.g. SP: `+55119...`, RJ: `+55219...`, MG: `+55319...`) and numeric hash of `customer_unique_id`. |
| `phone_type` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'Mobile', CHECK` | — (Static default) | **SYNTHETIC / AUGMENTED** | Defaulted to `'Mobile'` (satisfying check constraint `IN ('Mobile', 'Home', 'Work', 'Office', 'Other')`). |

---

### Table 3: `ADDRESS`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> customer` | `olist_customers_dataset.csv` (`customer_unique_id`) | **DIRECT SOURCE** | Foreign key linking to `CUSTOMER.customer_id` (`customer_unique_id`). For repeat customers, primary address is selected from their most recent order. |
| `address_type` | `VARCHAR(20)` | `PRIMARY KEY, DEFAULT 'Shipping', CHECK` | — (Static default) | **DERIVED** | Set to `'Shipping'` for primary delivery addresses (satisfying check constraint `IN ('Shipping', 'Billing', 'Home', 'Office', 'Work', 'Other')`). |
| `street` | `VARCHAR(150)` | `NOT NULL` | `olist_customers_dataset.csv` (`customer_zip_code_prefix`, `customer_unique_id`) | **SYNTHETIC / AUGMENTED** | Deterministically synthesized street address (e.g., `"Rua das Flores, 142"`, `"Avenida Paulista, 1020"`) generated from standard Brazilian street nomenclature and customer hash. |
| `city` | `VARCHAR(50)` | `NOT NULL` | `olist_customers_dataset.csv` (`customer_city`) | **DIRECT SOURCE** | Directly copied from `customer_city`, normalized with Title Case (e.g., `"Sao Paulo"`). |
| `state` | `CHAR(2)` | `NOT NULL, CHECK (len = 2)` | `olist_customers_dataset.csv` (`customer_state`) | **DIRECT SOURCE** | Directly copied from `customer_state` (2-character state code: `SP`, `RJ`, etc.). |
| `pincode` | `VARCHAR(10)` | `NOT NULL` | `olist_customers_dataset.csv` (`customer_zip_code_prefix`) | **DERIVED** | Formatted 8-digit Brazilian CEP string: `CONCAT(customer_zip_code_prefix, '-000')` (e.g., `"01153-000"`). |
| `is_default` | `BOOLEAN` | `NOT NULL, DEFAULT 1` | — (Static default) | **DERIVED** | Set to `1` (`TRUE`) as the customer's primary address. |

---

### Table 4: `VENDOR`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `vendor_id` | `VARCHAR(32)` | `PRIMARY KEY` | `olist_sellers_dataset.csv` (`seller_id`) | **DIRECT SOURCE** | Directly mapped 1:1 from `seller_id` (3,095 sellers). |
| `vendor_name` | `VARCHAR(100)` | `NOT NULL` | `olist_sellers_dataset.csv` (`seller_city`, `seller_state`, `seller_id`) | **SYNTHETIC / AUGMENTED** | Synthesized realistic commercial enterprise name (e.g., `"Paulista Commercial Distribuicao Ltda"`, `"Rio Sul Express #142"`), derived from city, state, and seller hash. |
| `rating` | `DECIMAL(3,2)` | `NOT NULL, CHECK (1.00 <= rating <= 5.00)` | `olist_order_reviews_dataset.csv` (`review_score`) joined via `order_items` | **DERIVED** | Computed as the exact mathematical average of all customer review scores on orders fulfilled by this seller: `ROUND(AVG(review_score), 2)`. For the 5 sellers with 0 reviews, defaulted to `5.00`. |
| `gst_number` | `VARCHAR(20)` | `NOT NULL, UNIQUE, CHECK (len >= 8)` | `olist_sellers_dataset.csv` (`seller_id`) | **SYNTHETIC / AUGMENTED** | Deterministically synthesized unique tax identification / GST number formatted as `GST-<STATE>-<HEX8>` (e.g., `"GST-SP-3442F890"`), guaranteed unique and `>= 8` characters. |

---

### Table 5: `CATEGORY`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `category_id` | `INT UNSIGNED` | `PRIMARY KEY, AUTO_INCREMENT` | Synthetic surrogate sequence | **SYNTHETIC / AUGMENTED** | Auto-incrementing integer identifier (IDs 1 to 9 for Level-1 parent categories; IDs 10 to 82 for Level-2 subcategories; ID 83 for Uncategorized). |
| `category_name` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | `product_category_name_translation.csv` (`product_category_name_english`) | **DERIVED** | Standardized English category title (e.g., `"Electronics & Appliances"`, `"Health & Beauty"`, `"Bed Bath Table"`). |
| `parent_category_id` | `INT UNSIGNED` | `NULL, FK -> category(category_id), CHECK` | Proposed hierarchical taxonomy rule | **DERIVED** | `NULL` for top-level L1 root categories (e.g., `"Electronics & Appliances"`). Set to corresponding L1 `category_id` for L2 subcategories (e.g., `"Computers & Accessories"` $\rightarrow$ L1 ID). Satisfies `parent_category_id <> category_id`. |

---

### Table 6: `PRODUCT`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `PRIMARY KEY` | `olist_products_dataset.csv` (`product_id`) | **DIRECT SOURCE** | Directly mapped 1:1 from `product_id` (32,951 products). |
| `product_name` | `VARCHAR(150)` | `NOT NULL` | `olist_products_dataset.csv` (`product_category_name`, `product_id`) | **SYNTHETIC / AUGMENTED** | Olist only provides name character length. Synthesize realistic descriptive titles combining English category name and product token (e.g., `"Premium Bed Bath Table Set #A489"`). |
| `description` | `TEXT` | `NULL` | `olist_products_dataset.csv` (`product_category_name`, `product_weight_g`, etc.) | **SYNTHETIC / AUGMENTED** | Synthesized product description detailing category, dimensions, weight, and specifications. |
| `price` | `DECIMAL(10,2)` | `NOT NULL, CHECK (price >= 0.00)` | `olist_order_items_dataset.csv` (`price`) | **DERIVED** | Derived as the base catalog list price (median/mode price for this product across historical order items). |
| `category_id` | `INT UNSIGNED` | `NOT NULL, FK -> category` | `olist_products_dataset.csv` (`product_category_name`) | **DERIVED** | Foreign key looked up from `CATEGORY` using translated category name. The 610 products with NULL category map to category ID 83 (`"General Merchandise / Uncategorized"`). |
| `vendor_id` | `VARCHAR(32)` | `NOT NULL, FK -> vendor` | `olist_order_items_dataset.csv` (`seller_id`) | **DERIVED** | Primary vendor assigned via 3-tier deterministic rule: 1. Highest historical sales volume, 2. If tied, earliest order date, 3. If still tied, minimum `seller_id`. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'Active', CHECK` | — (Static default) | **DERIVED** | Set to `'Active'` (satisfying check constraint `IN ('Active', 'Inactive', 'Out of Stock', 'Discontinued')`). |

---

### Table 7: `PRODUCT_TAG`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> product` | `olist_products_dataset.csv` (`product_id`) | **DIRECT SOURCE** | Foreign key linking to `PRODUCT.product_id`. |
| `tag` | `VARCHAR(50)` | `PRIMARY KEY, CHECK (len >= 2)` | Derived from category tokens, price tier, and sales volume | **SYNTHETIC / AUGMENTED** | Deterministically generated multi-valued keyword tags: e.g. tokenized category words (`"bedding"`, `"electronics"`, `"kitchen"`), price tier (`"budget"`, `"premium"`), and popularity (`"bestseller"`, `"featured"`). |

---

### Table 8: `WAREHOUSE`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `warehouse_id` | `INT UNSIGNED` | `PRIMARY KEY, AUTO_INCREMENT` | Synthetic surrogate sequence | **SYNTHETIC / AUGMENTED** | Auto-incrementing integer ID (1 to 8). |
| `location` | `VARCHAR(100)` | `NOT NULL` | Synthesized regional logistics hubs | **SYNTHETIC / AUGMENTED** | 8 regional fulfillment centers placed in top commercial states: `"São Paulo Central Distribution Hub (SP)"`, `"Campinas Logistics Park (SP)"`, `"Rio de Janeiro Distribution Center (RJ)"`, `"Belo Horizonte Hub (MG)"`, `"Curitiba Regional Hub (PR)"`, `"Porto Alegre Hub (RS)"`, `"Salvador Northeast Center (BA)"`, `"Brasília Central Hub (DF)"`. |
| `capacity` | `INT UNSIGNED` | `NOT NULL, CHECK (capacity > 0)` | Sized to accommodate catalog inventory | **SYNTHETIC / AUGMENTED** | Realistic storage capacities: 250,000 to 1,000,000 units per warehouse. |

---

### Table 9: `INVENTORY`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> product` | `olist_products_dataset.csv` (`product_id`) | **DIRECT SOURCE** | Foreign key linking to `PRODUCT.product_id`. |
| `warehouse_id` | `INT UNSIGNED` | `PRIMARY KEY, FK -> warehouse` | Assigned regional fulfillment hub | **DERIVED** | Deterministically assigned to 1 to 3 warehouses based on the product vendor's state location (primary regional hub) plus the national hub in SP. |
| `stock_quantity` | `INT` | `NOT NULL, DEFAULT 0, CHECK (>= 0)` | Historical order velocity | **DERIVED / SYNTHETIC** | Computed deterministically as `stock_quantity = GREATEST(ROUND(historical_units_sold * 1.5), 50)` ensuring stock is strictly positive and exceeds all past order volumes. |
| `reorder_level` | `INT` | `NOT NULL, DEFAULT 10, CHECK (>= 0)` | Safety stock threshold rule | **DERIVED / SYNTHETIC** | Set to `reorder_level = GREATEST(ROUND(stock_quantity * 0.20), 10)`. |
| `last_updated` | `DATETIME` | `NOT NULL` | Latest transaction timestamp | **DERIVED** | Derived as latest order timestamp or `CURRENT_TIMESTAMP`. |

---

### Table 10: `ORDERS`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `PRIMARY KEY` | `olist_orders_dataset.csv` (`order_id`) | **DIRECT SOURCE** | Directly mapped 1:1 from `order_id` (99,441 orders). |
| `customer_id` | `VARCHAR(32)` | `NOT NULL, FK -> customer` | `olist_orders_dataset.csv` (`customer_id`) joined to `olist_customers_dataset.csv` | **DERIVED / MAPPED** | Foreign key referencing `CUSTOMER.customer_id` (`customer_unique_id`). Resolved by joining `olist_orders_dataset.customer_id` to `olist_customers_dataset.customer_unique_id`. |
| `order_date` | `DATETIME` | `NOT NULL` | `olist_orders_dataset.csv` (`order_purchase_timestamp`) | **DIRECT SOURCE** | Directly mapped from `order_purchase_timestamp`. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'PLACED', CHECK` | `olist_orders_dataset.csv` (`order_status`) | **DERIVED** | Normalized to uppercase format matching `chk_orders_status` (e.g. `'delivered'` $\rightarrow$ `'DELIVERED'`, `'shipped'` $\rightarrow$ `'SHIPPED'`, `'canceled'` $\rightarrow$ `'CANCELLED'`). |

---

### Table 11: `ORDER_ITEM`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> orders` | `olist_order_items_dataset.csv` (`order_id`) | **DIRECT SOURCE** | Composite primary key component referencing `ORDERS.order_id`. |
| `product_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> product` | `olist_order_items_dataset.csv` (`product_id`) | **DIRECT SOURCE** | Composite primary key component referencing `PRODUCT.product_id`. |
| `quantity` | `INT` | `NOT NULL, DEFAULT 1, CHECK (quantity > 0)` | `olist_order_items_dataset.csv` aggregated rows | **DERIVED** | Reconstructed via `quantity = COUNT(*)` per `(order_id, product_id)` group. Collapses 112,650 raw item rows into 102,425 unique composite pairs with quantity 1 to 20. |
| `price_at_purchase` | `DECIMAL(10,2)` | `NOT NULL, CHECK (price >= 0.00)` | `olist_order_items_dataset.csv` (`price`) | **DERIVED** | Derived as unit purchase price: `price_at_purchase = MIN(price)` per `(order_id, product_id)` (verified 0 price variance across all repeated units). |

---

### Table 12: `PAYMENT`
| Target Column | Target Data Type | Constraints | Source File & Column | Classification | ETL Transformation & Population Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `PRIMARY KEY, FK -> orders` | `olist_order_payments_dataset.csv` (`order_id`) | **DIRECT SOURCE** | Composite primary key component referencing `ORDERS.order_id`. |
| `payment_id` | `INT UNSIGNED` | `PRIMARY KEY` | `olist_order_payments_dataset.csv` (`payment_sequential`) | **DIRECT SOURCE** | Mapped from `payment_sequential` (values 1 to 29; 0 duplicates per order). |
| `amount` | `DECIMAL(10,2)` | `NOT NULL, CHECK (amount > 0.00)` | `olist_order_payments_dataset.csv` (`payment_value`) | **DERIVED** | Direct `payment_value`. The 9 raw rows with `0.00` value are sanitized to `0.01` (or filtered if redundant voucher token) to satisfy `chk_payment_amount: amount > 0.00`. |
| `mode` | `VARCHAR(20)` | `NOT NULL, CHECK` | `olist_order_payments_dataset.csv` (`payment_type`) | **DERIVED** | Mapped to allowed check constraint values: `credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`. |
| `status` | `VARCHAR(20)` | `NOT NULL, DEFAULT 'Success', CHECK` | Derived from order status | **DERIVED** | Set to `'Success'` for delivered/shipped/approved orders; `'Refunded'` for canceled orders with vouchers. |
| `payment_date` | `DATETIME` | `NOT NULL` | `olist_orders_dataset.csv` (`order_approved_at` / `order_purchase_timestamp`) | **DERIVED** | Derived from `order_approved_at` (or `order_purchase_timestamp` if approval timestamp is null). |
| `transaction_reference` | `VARCHAR(64)` | `NOT NULL, UNIQUE` | Deterministic transaction hash | **SYNTHETIC / AUGMENTED** | Deterministically synthesized unique reference: `CONCAT('TXN-', UPPER(SUBSTRING(MD5(CONCAT(order_id, payment_sequential)), 1, 16)))`, guaranteed 100% unique across all payment records. |

---

## 4. Deep-Dive on Critical Target-Schema Investigation Issues

### 4.1 CUSTOMER: `customer_id` vs `customer_unique_id`
* **Analysis:** In Olist, `customer_id` is an order-level transaction identifier (99,441 unique values), while `customer_unique_id` is the real-world individual account identifier (96,096 unique values; 2,997 repeat customers).
* **Referential Architecture:** The `olist_orders_dataset.csv` contains `customer_id`, which maps to `customer_unique_id` via `olist_customers_dataset.csv`.
* **Design Decision:** In our canonical relational schema, master customer entities are stored as `CUSTOMER.customer_id = customer_unique_id` (96,096 distinct records). In `ORDERS`, `ORDERS.customer_id` references `customer_unique_id` (resolved by joining `olist_orders_dataset` with `olist_customers_dataset` on `customer_id`). This preserves full historical transaction linkage so that repeat orders correctly roll up to the customer entity.

### 4.2 CUSTOMER_PHONE: Synthetic Multivalued Phone Numbers
* **Analysis:** Olist contains zero customer telephone numbers.
* **Strategy:** Model `CUSTOMER_PHONE` with composite PK `(customer_id, phone_number)`. Generate valid Brazilian formatted mobile numbers (`+55 <DDD> 9<8-digits>`) where `<DDD>` matches the customer's state area code (e.g. 11 for SP, 21 for RJ, 31 for MG) deterministically derived from `customer_unique_id` hash. All records satisfy `chk_phone_number_length: len >= 8`.

### 4.3 ADDRESS: Customer Address Synthesis & Pincode Prefix Analysis
* **Analysis:** Olist provides `customer_zip_code_prefix` (5-digit prefix), `customer_city`, and `customer_state`. It does not contain full 8-digit CEPs or street names.
* **Strategy:**
  * `street`: Synthesized realistic Brazilian street names (`"Rua..."`, `"Avenida..."`) deterministically generated from city/state and customer ID hash.
  * `pincode`: Standardized by appending suffix to the prefix: `CONCAT(customer_zip_code_prefix, '-000')`.
  * `address_type`: Defaulted to `'Shipping'`.
  * `is_default`: Set to `1`.
  * Composite PK `(customer_id, address_type)` is strictly unique.

### 4.4 VENDOR: Seller Mapping, Ratings, & GST Number
* **Analysis:** `olist_sellers_dataset.csv` contains `seller_id` (3,095 sellers), `seller_zip_code_prefix`, `seller_city`, `seller_state`.
* **Strategy:**
  * `vendor_id`: Mapped 1:1 from `seller_id`.
  * `vendor_name`: Generated realistic trade names based on seller city/state and seller ID.
  * `rating`: Mathematically calculated from `olist_order_reviews_dataset.csv` by averaging review scores of all orders fulfilled by the seller (`ROUND(AVG(review_score), 2)`). Range: 1.00 to 5.00 (Mean: 3.97), satisfying `chk_vendor_rating`.
  * `gst_number`: Formatted unique tax ID string `GST-<STATE>-<HEX8>` (e.g., `GST-SP-3442F890`), satisfying `uq_vendor_gst` and `chk_vendor_gst_len: len >= 8`.

### 4.5 CATEGORY: Recursive Taxonomy & Translation Coverage
* **Analysis:** `olist_products_dataset.csv` contains 73 Portuguese categories plus 610 products with NULL category. `product_category_name_translation.csv` contains 71 English translations.
* **Missing Translations Resolved:**
  1. `pc_gamer` $\rightarrow$ `"PC Gaming"`
  2. `portateis_cozinha_e_preparadores_de_alimentos` $\rightarrow$ `"Kitchen & Food Appliances"`
* **Recursive Hierarchy Structure:**
  * **9 Level-1 Root Categories (`parent_category_id IS NULL`):**
    1. `Electronics & Appliances`
    2. `Home & Furniture`
    3. `Fashion & Accessories`
    4. `Health & Beauty`
    5. `Sports, Hobbies & Leisure`
    6. `Automotive & Industry`
    7. `Food & Beverages`
    8. `Pet Care`
    9. `Stationery, Gifts & Misc`
  * **73 Level-2 Subcategories (`parent_category_id = Level-1 ID`):** All 73 translated Olist categories mapped deterministically to their respective parent.
  * **Fallback Category:** Category ID 83 (`"General Merchandise / Uncategorized"`, under parent `Stationery, Gifts & Misc`) for the 610 products with NULL category.

### 4.6 PRODUCT: Catalog Pricing, Primary Vendor Assignment, & Dimension Filtering
* **Analysis:** Olist has 32,951 products. In Olist, `price` and `seller_id` are located in `order_items` rather than `products`.
  * 31,726 products are sold by exactly 1 seller.
  * 1,225 products are sold by 2 to 8 different sellers.
* **Strategy:**
  * `vendor_id`: Primary vendor is assigned via the canonical 3-tier deterministic rule: 1. Highest historical sales volume, 2. If tied, earliest order date, 3. If still tied, minimum `seller_id`.
  * `price`: Catalog price is derived as the median historical price from `order_items`.
  * `product_name` & `description`: Synthesized descriptive title and textual description from category and product token.
  * Unused source columns (`product_photos_qty`, `product_weight_g`, dimensions) are filtered out cleanly.

### 4.7 PRODUCT_TAG: Deterministic Tag Generation
* **Analysis:** Olist contains no product tags.
* **Strategy:** Populate `PRODUCT_TAG` (composite PK `(product_id, tag)`) with 2 to 4 deterministic keyword tags per product:
  1. Category keyword tokens (e.g., `"audio"`, `"kitchen"`, `"furniture"`).
  2. Price tier tag (`"budget"`, `"mid-range"`, `"premium"`).
  3. Regional tag (`"sudeste"`, `"sul"`, `"norte"`).

### 4.8 WAREHOUSE: Regional Logistics Topology
* **Analysis:** Olist is a decentralized seller-fulfillment network without physical warehouse entities.
* **Strategy:** Synthesize 8 regional fulfillment centers in key distribution hubs based on Olist seller concentration (SP, RJ, MG, PR, RS, BA, DF) with capacities from 250,000 to 1,000,000 units.

### 4.9 INVENTORY: Deterministic Warehouse Stock Allocation Rule
* **Strategy:** Multi-warehouse inventory stock model resolving M:N relationship between `PRODUCT` and `WAREHOUSE`:
  * Each product is stocked in 1 to 3 warehouses (primary regional warehouse of its vendor + central SP hub).
  * `stock_quantity = GREATEST(ROUND(historical_sales * 1.5), 50)`
  * `reorder_level = GREATEST(ROUND(stock_quantity * 0.20), 10)`
  * Guarantees stock is non-negative and satisfies `chk_inventory_stock` and `chk_inventory_reorder`.

### 4.10 ORDERS: Lifecycle & Status Normalization
* **Analysis:** 99,441 orders spanning 2016 to 2018.
* **Strategy:** Map `order_purchase_timestamp` $\rightarrow$ `order_date`. Normalize raw statuses (`delivered`, `shipped`, `canceled`, etc.) to uppercase strings matching check constraint `chk_orders_status`.

### 4.11 ORDER_ITEM: Composite Key Deduplication & Quantity Reconstruction
* **Analysis:** Raw `olist_order_items_dataset.csv` contains 112,650 rows across 98,666 distinct orders.
* **Canonical Aggregation Rule:**
  * Group by `(order_id, product_id)`:
    * `quantity = COUNT(*)` (values range from 1 to 20; exactly 7,088 multi-item groups).
    * `price_at_purchase = MIN(price)` (unit price is 100% uniform within all multi-item groups).
  * Target row count: **102,425 rows** with composite PK `(order_id, product_id)`, eliminating all duplicate key errors while preserving 100% of order value.

### 4.12 PAYMENT: Composite Key, Sequential Mapping, & Zero-Value Sanitization
* **Analysis:** 103,886 payment records across 99,440 orders.
* **Strategy:**
  * Composite PK `(order_id, payment_id)` where `payment_id = payment_sequential` (values 1 to 29; 0 duplicates per order).
  * `amount`: 9 raw rows with `0.00` value are sanitized to `0.01` (or filtered) to satisfy `chk_payment_amount: amount > 0.00`.
  * `transaction_reference`: Synthesized unique 16-character MD5 token `TXN-<HEX16>`.
  * `payment_date`: Derived from `orders.order_approved_at` or `order_purchase_timestamp`.

---

## 5. Comprehensive Data Quality & Anomaly Analysis

The table below summarizes every data quality finding, exact row count, and the corresponding mitigation rule:

| Quality Dimension | Source Location | Exact Metric / Count | Impact on Target DBMS Schema | Mitigation / Transformation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Missing Product Categories** | `olist_products_dataset.csv` | **610 products** (1.85%) | `PRODUCT.category_id` has `NOT NULL` foreign key constraint. | Assign to dedicated fallback category ID 83 (`"General Merchandise / Uncategorized"`). |
| **Unlisted Category Translations** | `product_category_name_translation.csv` | **2 categories** (`pc_gamer`, `portateis_cozinha...`) | Translation lookup would return NULL for 18 products. | Add explicit manual translation mapping in ETL script. |
| **UTF-8 BOM in Translation Header** | `product_category_name_translation.csv` | **1 file** (`\ufeff`) | Python standard CSV reader misinterprets column 0 header. | Read file using `utf-8-sig` encoding in ETL pipeline. |
| **Multi-Item Order Rows** | `olist_order_items_dataset.csv` | **10,225 redundant rows** across 7,088 pairs | Violates composite PK `(order_id, product_id)` in `ORDER_ITEM`. | Aggregate by `(order_id, product_id)` with `quantity = COUNT(*)` and `price_at_purchase = MIN(price)`. |
| **Multi-Vendor Products** | `olist_order_items_dataset.csv` | **1,225 products** sold by >1 seller | `PRODUCT.vendor_id` allows only a single vendor FK. | Assign primary vendor via 3-tier rule: 1. Highest sales volume, 2. Earliest order date, 3. Minimum `seller_id`. |
| **Zero-Value Payments** | `olist_order_payments_dataset.csv` | **9 payment rows** with `0.00` value | Violates check constraint `chk_payment_amount: amount > 0.00`. | Sanitize value to `0.01` or filter dummy token rows during ETL. |
| **Orders Without Items** | `olist_orders_dataset.csv` | **775 orders** (603 unavailable, 164 canceled, 8 other) | Orders exist with no child rows in `ORDER_ITEM`. | Relational model is parent-child (`ORDER_ITEM -> ORDERS`); 0 FK violations occur. |
| **Orders Without Payments** | `olist_orders_dataset.csv` | **1 order** (`bfbd0f9bdef...`) | Order exists with no payment record. | Relational model is parent-child (`PAYMENT -> ORDERS`); 0 FK violations occur. |
| **Review ID Duplications** | `olist_order_reviews_dataset.csv` | **789 duplicate review IDs** | Not an issue for target schema as reviews are used only for vendor rating aggregation. | Aggregate by `seller_id` to compute average rating; table is not loaded directly. |
| **Missing Geolocation Zips** | `olist_customers_dataset.csv` | **157 customer zip prefixes** | Geolocation lookup cannot find spatial coordinates for 157 zips. | Fall back to customer state/city centroid for spatial enrichment. |

---

## 6. ETL Readiness Validation & Core Mismatch Resolutions

This section provides the mathematical, empirical, and academic validation of the three core source-to-target mapping decisions before proceeding to Phase 3 (ETL & MySQL Population).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             CORE SOURCE-TO-TARGET CONFLICT RESOLUTIONS                           │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  1. ORDER_ITEM Line-Item Expansion (112,650 rows) ──► Aggregated (102,425 composite pairs)      │
│     • Rule: quantity = COUNT(*), price_at_purchase = MIN(price)                                  │
│     • Validation: 7,088 multi-item pairs, 0.00% price variance, 100% value conserved             │
│                                                                                                  │
│  2. PRODUCT N:1 VENDOR Assignment (1,225 multi-seller products)                                   │
│     • Rule: Rank 1 by Volume (DESC) ──► Earliest Order Date (ASC) ──► Min Seller ID (ASC)        │
│     • Validation: 916 volume dominant (74.78%), 309 resolved by timestamp (100%), 0 date ties    │
│                                                                                                  │
│  3. Master CUSTOMER Identity Resolution (96,096 unique individuals)                              │
│     • Rule: CUSTOMER.customer_id = customer_unique_id (Master BCNF Entity)                       │
│     • Validation: 2,997 repeat customers (6,342 orders, max 17 orders/customer)                  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 6.1 Conflict 1: `ORDER_ITEM` Composite Primary Key & Quantity Derivation

#### Empirical Audit of Raw `olist_order_items_dataset.csv`
* **Total Raw Rows:** `112,650`
* **Distinct `(order_id, product_id)` Composite Pairs:** `102,425`
* **Repeated `(order_id, product_id)` Pairs (Count > 1):** `7,088` (representing `10,225` redundant rows to be collapsed).
* **Distribution of Units (Quantities) in Repeated Combinations:**
  * **2 units:** 5,382 combinations (10,764 raw rows)
  * **3 units:** 953 combinations (2,859 raw rows)
  * **4 units:** 390 combinations (1,560 raw rows)
  * **5 units:** 168 combinations (840 raw rows)
  * **6 units:** 172 combinations (1,032 raw rows)
  * **7 units:** 4 combinations (28 raw rows)
  * **8 units:** 2 combinations (16 raw rows)
  * **9 units:** 2 combinations (18 raw rows)
  * **10 units:** 5 combinations (50 raw rows)
  * **11 to 20 units:** 10 combinations (146 raw rows; Maximum quantity = 20 units)

#### Data Structure & Semantic Reality
1. **Absence of Explicit Quantity Field:** The Olist schema does **not** contain an explicit `quantity` column. Instead, when a buyer orders $N$ units of the same product, the system expands the purchase into $N$ distinct records with an incrementing `order_item_id` (1, 2, 3, ...).
2. **Order Item ID Sequencing:** In 264 multi-product orders, identical products appear with non-consecutive IDs (e.g., item IDs 1, 2, 3, and 8 because items 4–7 were different catalog items in the same cart).
3. **Price & Freight Uniformity:** Across all 7,088 repeated combinations, there is **EXACTLY 0.00% price variance** (`0` discrepancies) and **0.00% freight variance** (`0` discrepancies). Every repeated unit within an order was charged the identical unit price.
4. **Fulfillment Seller Uniformity:** In 100% of repeated combinations, all units of the same product in a given order were fulfilled by the **same seller** (`0` multi-seller splits for a single product within an order).

#### Recommended Single Deterministic Transformation Rule
$$\text{quantity} = \text{COUNT}(*)$$
$$\text{price\_at\_purchase} = \text{MIN}(\text{price})$$

```sql
-- Deterministic SQL ETL Aggregation Rule
SELECT 
    order_id,
    product_id,
    COUNT(*) AS quantity,
    MIN(price) AS price_at_purchase
FROM olist_order_items_dataset
GROUP BY order_id, product_id;
```

* **Academic & Relational Justification:** Because unit prices within any order-product pair are 100% uniform, `MIN(price) = MAX(price) = AVG(price)`. Using `MIN(price)` is computationally efficient, deterministic, preserves all 112,650 purchased units, maintains 100% of historical GMV (Gross Merchandise Value), and strictly complies with `PRIMARY KEY (order_id, product_id)`.

---

### 6.2 Conflict 2: `PRODUCT -> VENDOR` Canonical Relationship Resolution

#### Empirical Audit of Product-Seller Distribution
* **Total Products in Catalog:** `32,951`
* **Single-Seller Products:** `31,726` products (**96.28%** of catalog — 1:1 vendor mapping is trivially direct).
* **Multi-Seller Products:** `1,225` products (**3.72%** of catalog).
* **Sellers per Multi-Seller Product:**
  * **2 sellers:** 1,030 products (84.08%)
  * **3 sellers:** 147 products (12.00%)
  * **4 sellers:** 32 products (2.61%)
  * **5 sellers:** 10 products (0.82%)
  * **6 to 8 sellers:** 6 products (0.49%; Maximum = 8 distinct sellers for 2 products)

#### Dominance & Tie-Break Analysis for the 1,225 Multi-Seller Products
1. **Volume Dominance (Primary Tier):** In **916 products (74.78%)**, a single seller sold strictly more historical units than any competing seller.
2. **Volume Ties (Secondary Tier):** In **309 products (25.22%)**, multiple top sellers are tied in total units sold (e.g., 2 sellers each selling 1 unit).
3. **Chronological Resolution:** Across all 309 tied products, the tie is **100.00% resolved** by selecting the seller with the earliest chronological transaction timestamp (`MIN(order_purchase_timestamp)`).
4. **Exact Timestamp Ties:** Exactly **0** products have identical earliest timestamps among tied sellers.

#### Recommended Single Deterministic Vendor-Resolution Rule
For every `product_id`, evaluate all candidate sellers from historical order items using the following multi-tiered ranking function:

$$\text{Rank}(S) = \operatorname{ROW\_NUMBER}() \text{ OVER} \Big(\text{PARTITION BY } \text{product\_id } \text{ORDER BY } \text{COUNT}(*) \text{ DESC}, \min(\text{order\_purchase\_timestamp}) \text{ ASC}, \text{seller\_id } \text{ASC}\Big)$$

The vendor with $\text{Rank} = 1$ is assigned as `PRODUCT.vendor_id`.

* **Academic & Relational Justification:** 
  * **Economic Principle:** Attributing a product to its primary volume distributor reflects commercial catalog ownership.
  * **First-to-Market Principle:** Breaking volume ties via chronological precedence honors the original merchant who first listed and sold the product.
  * **Mathematical Determinism:** The tertiary lexicographical tie-breaker (`seller_id ASC`) guarantees 100% reproducible execution across any database engine.

---

### 6.3 Master `CUSTOMER` Identity Resolution

#### Empirical Audit of Customer Identifiers
* **Total Raw `customer_id` Tokens (Order-Level Sessions):** `99,441`
* **Total Unique `customer_unique_id` Entities (Human Accounts):** `96,096`
* **Total Repeat Customers (Placed $> 1$ Order):** `2,997` customers (**3.12%** of user base).
* **Total Orders Placed by Repeat Customers:** `6,342` orders.
* **Customer Lifetime Order Frequency Distribution:**
  * **1 order:** 93,099 customers (96.88%)
  * **2 orders:** 2,745 customers (2.86%)
  * **3 orders:** 203 customers (0.21%)
  * **4 orders:** 30 customers (0.03%)
  * **5 to 17 orders:** 20 customers (Max = 17 lifetime orders by a single customer)
* **Address Mobility among Repeat Customers:**
  * 250 repeat customers used multiple postal code prefixes across different orders.
  * 122 repeat customers ordered from multiple cities.
  * 39 repeat customers ordered from multiple states.

#### Master Customer Identity Mapping Strategy
In relational database design (BCNF / 3NF), an entity table must represent distinct real-world entities (individual customers), not ephemeral transaction tokens.

1. **`CUSTOMER` Table:** Populated with the **96,096 distinct `customer_unique_id`** records. `customer_id = customer_unique_id`.
2. **`ORDERS` Table:** `ORDERS.customer_id` references `customer_unique_id` (obtained by joining `olist_orders_dataset` with `olist_customers_dataset` on `customer_id`). This preserves full historical transaction linkage so that repeat orders correctly roll up to the customer entity.
3. **`ADDRESS` Table:** Composite PK `(customer_id, address_type)`. For the 250 repeat customers with multiple historical shipping addresses, their primary address is deterministically selected as their most recent delivery address (`MAX(order_purchase_timestamp)`).
4. **`CUSTOMER_PHONE` Table:** Composite PK `(customer_id, phone_number)` referencing `customer_unique_id`.

* **Academic & Relational Justification:** Using `customer_unique_id` prevents creating 3,345 duplicate customer accounts, enables customer lifetime value (LTV) and cohort analytics queries, and avoids violating 2NF/3NF constraints on customer contact information.

---

### 6.4 Summary of Selected Deterministic Rules

| Domain Target | Raw Mismatch | Final Deterministic Rule | Validation Status |
| :--- | :--- | :--- | :--- |
| **`ORDER_ITEM` PK** | Expanded line items ($N$ rows per $N$ units) | `GROUP BY order_id, product_id` with `quantity = COUNT(*)` and `price_at_purchase = MIN(price)` | **100% Valid (102,425 rows, 0 price discrepancies)** |
| **`PRODUCT.vendor_id`** | 1,225 products sold by multiple sellers | Rank sellers by `Volume DESC`, then `Earliest Date ASC`, then `seller_id ASC` (Select Rank 1) | **100% Deterministic (916 volume wins, 309 date wins, 0 unresolved ties)** |
| **`CUSTOMER.customer_id`** | Order token vs Human entity | Store `customer_unique_id` in `CUSTOMER` (96,096 rows) and join `ORDERS` on `customer_unique_id` | **100% Relational (Clean BCNF modeling, 2,997 repeat buyers preserved)** |
| **`CATEGORY.parent_id`** | Flat category list | 9 L1 parent categories + 73 L2 subcategories + 1 Uncategorized fallback category | **100% Taxonomy Coverage (73/73 categories mapped)** |
| **`PAYMENT.amount`** | 9 rows with `payment_value = 0.00` | Adjust `0.00` values to `0.01` to comply with `chk_payment_amount: amount > 0.00` | **100% Constraint Compliant** |

---

### 6.5 Remaining Pre-ETL Checklist

1. [x] Raw Olist CSV files verified and immutable in `data/raw/`.
2. [x] Composite primary keys and foreign key hierarchies mathematically validated.
3. [x] All 73 product categories mapped to English and structured into recursive 2-level hierarchy.
4. [x] Multi-vendor product conflict fully resolved with 3-tier deterministic ranking.
5. [x] Order item multi-unit expansion resolved with zero price variance.
6. [x] Zero-value payment adjustment strategy confirmed.
7. [ ] Ready for User Approval to begin Phase 3 (Python ETL Pipeline & MySQL Loading).

---

## 7. Status Statement

**ETL READINESS VALIDATION COMPLETE — WAITING FOR APPROVAL.**
