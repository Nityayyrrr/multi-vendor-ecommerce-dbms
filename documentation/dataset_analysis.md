# Multi-Vendor E-Commerce Database Management System (DBMS)
# Comprehensive Raw Dataset Analysis Report (HISTORICAL EXPLORATORY DOCUMENT)

> [!NOTE]
> **DOCUMENT CLASSIFICATION: HISTORICAL EXPLORATORY ARTIFACT**  
> This file is a historical exploratory document created during Phase 1 / early Phase 2 scoping.
> * **Authoritative Phase 2 ETL Mapping Specification:** [phase2_dataset_analysis_and_mapping.md](phase2_dataset_analysis_and_mapping.md)
> * **Authoritative MySQL 8.4 Database Specification:** [final_schema_specification.md](final_schema_specification.md)

**Target File Location:** `documentation/dataset_analysis.md`  
**Dataset Analyzed:** Brazilian E-Commerce Public Dataset by Olist (9 Raw CSV Files in `data/raw/`)  
**Analysis Date:** 2026-09-01  
**Status:** Historical Dataset Inspection (Superseded by `phase2_dataset_analysis_and_mapping.md` for ETL)

---

## Executive Summary

This report delivers an exhaustive, column-by-column, and file-by-file statistical and relational inspection of all 9 raw CSV files located in `data/raw/`. The raw dataset captures 100,000 real-world e-commerce orders placed between 2016 and 2018 across multiple marketplaces in Brazil.

### High-Level Dataset Inventory Summary

| File Name | Row Count | File Size (Bytes) | Column Count | Natural Primary Key / Candidate Key | Referential Integrity Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `olist_customers_dataset.csv` | **99,441** | 9,033,957 | 5 | `customer_id` (Unique per order) | Clean; 157 zip codes missing in Geolocation |
| `olist_geolocation_dataset.csv` | **1,000,163** | 61,273,883 | 5 | None (No unique key; 261,831 exact dupes) | Reference lookup table with multiple coordinates per zip |
| `olist_orders_dataset.csv` | **99,441** | 17,654,914 | 8 | `order_id` (100% Unique) | 100% valid `customer_id` references (0 orphans) |
| `olist_order_items_dataset.csv` | **112,650** | 15,438,671 | 7 | Composite: `(order_id, order_item_id)` | 100% valid references to Orders, Products, Sellers (0 orphans) |
| `olist_order_payments_dataset.csv` | **103,886** | 5,777,138 | 5 | Composite: `(order_id, payment_sequential)` | 100% valid references to Orders (0 orphans; 1 order unpaid) |
| `olist_order_reviews_dataset.csv` | **99,224** | 14,451,670 | 7 | Composite: `(review_id, order_id)` / Surrogate | 100% valid references to Orders (789 non-unique `review_id`s) |
| `olist_products_dataset.csv` | **32,951** | 2,379,446 | 9 | `product_id` (100% Unique) | 610 missing categories; 2 categories unlisted in translation |
| `olist_sellers_dataset.csv` | **3,095** | 174,703 | 4 | `seller_id` (100% Unique) | Clean; 7 zip codes missing in Geolocation |
| `product_category_name_translation.csv` | **71** | 2,613 | 2 | `product_category_name` (100% Unique) | UTF-8 BOM present in raw header; 71 bilingual mappings |
| **TOTAL** | **1,450,922** | **106,186,995** | **47** | — | **High cross-file relational consistency** |

---

## Detailed Inspection Per CSV File

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA FLOW ARCHITECTURE                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────┐                   ┌──────────────────────────────┐     │
│   │   olist_customers   │◄───(1:1)──────────│         olist_orders         │     │
│   └──────────┬──────────┘                   └───────┬───────────────┬──────┘     │
│              │ (N:1)                                │ (1:N)         │ (1:N)      │
│              ▼                                      ▼               ▼            │
│   ┌─────────────────────┐               ┌───────────────┐   ┌────────────────┐   │
│   │  olist_geolocation  │               │ olist_payments│   │  olist_reviews │   │
│   └──────────▲──────────┘               └───────────────┘   └────────────────┘   │
│              │ (N:1)                                                             │
│   ┌──────────┴──────────┐                                                        │
│   │    olist_sellers    │◄───┐                                                   │
│   └─────────────────────┘    │                                                   │
│                              │ (N:1)                                             │
│   ┌─────────────────────┐    │          ┌───────────────────────────┐            │
│   │    olist_products   │◄───┼──(N:1)───┤     olist_order_items     │            │
│   └──────────┬──────────┘    │          └───────────────────────────┘            │
│              │ (N:1)         │                                                   │
│              ▼               │                                                   │
│   ┌─────────────────────┐    │                                                   │
│   │ product_category_   │    │                                                   │
│   │ name_translation    │    │                                                   │
│   └─────────────────────┘    │                                                   │
│                              │                                                   │
└──────────────────────────────┴───────────────────────────────────────────────────┘
```

---

### 1. `olist_customers_dataset.csv`

#### 1.1 Number of Rows
* **Exact Row Count:** `99,441` rows (plus 1 header row).

#### 1.2 Columns
1. `customer_id` (Index 0)
2. `customer_unique_id` (Index 1)
3. `customer_zip_code_prefix` (Index 2)
4. `customer_city` (Index 3)
5. `customer_state` (Index 4)

#### 1.3 Appropriate Data Types
* `customer_id`: `CHAR(32)` (Fixed-length 32-character hexadecimal MD5 hash string).
* `customer_unique_id`: `CHAR(32)` (Fixed-length 32-character hexadecimal MD5 hash string).
* `customer_zip_code_prefix`: `VARCHAR(5)` / `CHAR(5)` (5-character numeric string; storing as string preserves leading zeros such as `01037`).
* `customer_city`: `VARCHAR(40)` (Actual max length in data: 32 characters; e.g., `"sao bernardo do campo"`).
* `customer_state`: `CHAR(2)` (2-character standard Brazilian state abbreviation; e.g., `"SP"`, `"RJ"`, `"MG"`).

#### 1.4 Candidate Primary Keys
* **Candidate Primary Key (in this file):** `customer_id` (99,441 unique values across 99,441 rows; 0 duplicates, 0 nulls).
* *Note on Domain Architecture:* `customer_id` acts as an order-level transaction token (alias). The true customer entity is represented by `customer_unique_id` (96,096 distinct values).

#### 1.5 Candidate Foreign Keys
* `customer_zip_code_prefix` $\rightarrow$ `olist_geolocation_dataset(geolocation_zip_code_prefix)` (Referential check: 14,837 zip codes match; 157 unique zip codes are unrepresented in the geolocation file).

#### 1.6 Relationships with Other Source Files
* **With `olist_orders_dataset.csv`:** Strict **1:1 relationship** on `customer_id` (each record in `olist_customers_dataset` corresponds to exactly 1 order in `olist_orders_dataset`).
* **Within `olist_customers_dataset.csv`:** **N:1 relationship** between `customer_id` and `customer_unique_id`. Exactly 2,997 repeat customers placed between 2 and 17 orders.
* **With `olist_geolocation_dataset.csv`:** **N:1 relationship** on `customer_zip_code_prefix`.

#### 1.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `0` | `0.00%` | 32 | 32 |
| `customer_unique_id` | `0` | `0.00%` | 32 | 32 |
| `customer_zip_code_prefix` | `0` | `0.00%` | 5 | 5 |
| `customer_city` | `0` | `0.00%` | 3 | 32 |
| `customer_state` | `0` | `0.00%` | 2 | 2 |

#### 1.8 Duplicate-Key Issues
* `customer_id`: **0 duplicates** (100% unique).
* `customer_unique_id`: **3,345 duplicate rows** (representing returning customers making repeat purchases).

#### 1.9 Mapping to Proposed 12-Table ER Model
* In the proposed normalized ER model, this raw file splits into two distinct entities:
  1. `customers` (Master Customer Entity): Keyed by `customer_unique_id` (96,096 distinct records).
  2. `customer_addresses` / `orders.customer_id`: Keyed by `customer_id` linking the specific order to the customer's delivery location at the time of purchase.

#### 1.10 Absent Required Attributes / Entities from ER Model
* Real customer first and last name.
* Customer email address.
* Customer phone number / mobile number.
* Authentication credentials (password hash, salt, OAuth tokens).
* Customer tax identification number (CPF - *Cadastro de Pessoas Físicas*).
* Detailed street address (logradouro), building number, complement/apartment number, neighborhood (bairro).
* Account registration timestamp, account status, email verification status.

---

### 2. `olist_geolocation_dataset.csv`

#### 2.1 Number of Rows
* **Exact Row Count:** `1,000,163` rows (plus 1 header row).

#### 2.2 Columns
1. `geolocation_zip_code_prefix` (Index 0)
2. `geolocation_lat` (Index 1)
3. `geolocation_lng` (Index 2)
4. `geolocation_city` (Index 3)
5. `geolocation_state` (Index 4)

#### 2.3 Appropriate Data Types
* `geolocation_zip_code_prefix`: `VARCHAR(5)` / `CHAR(5)` (Preserves leading zeros; e.g. `'01037'`).
* `geolocation_lat`: `DECIMAL(10, 8)` / `DOUBLE PRECISION` (Floating point coordinates ranging from `-36.60537441` to `45.06593318`).
* `geolocation_lng`: `DECIMAL(11, 8)` / `DOUBLE PRECISION` (Floating point coordinates ranging from `-101.46676645` to `121.10539381`).
* `geolocation_city`: `VARCHAR(40)` (Actual max length in data: 38 characters).
* `geolocation_state`: `CHAR(2)` (2-character state code; 27 unique states/federal districts).

#### 2.4 Candidate Primary Keys
* **Single Column:** **None** (Only 19,015 unique zip code prefixes across 1,000,163 rows).
* **Composite Key from Existing Columns:** **None** (Combining all 5 columns `(geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)` yields only 738,332 unique rows, leaving 261,831 exact duplicate rows).
* **Required Implementation:** A synthetic surrogate key `geolocation_id` (`BIGINT AUTO_INCREMENT`) or an aggregated/deduplicated postal code dimension table keyed by `zip_code_prefix`.

#### 2.5 Candidate Foreign Keys
* None within this dataset. This table serves as a reference/lookup dimension.

#### 2.6 Relationships with Other Source Files
* **With `olist_customers_dataset.csv`:** **1:N relationship** via `geolocation_zip_code_prefix` $\rightarrow$ `customer_zip_code_prefix`.
* **With `olist_sellers_dataset.csv`:** **1:N relationship** via `geolocation_zip_code_prefix` $\rightarrow$ `seller_zip_code_prefix`.

#### 2.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length |
| :--- | :--- | :--- | :--- | :--- |
| `geolocation_zip_code_prefix` | `0` | `0.00%` | 5 | 5 |
| `geolocation_lat` | `0` | `0.00%` | 7 | 23 |
| `geolocation_lng` | `0` | `0.00%` | 7 | 19 |
| `geolocation_city` | `0` | `0.00%` | 2 | 38 |
| `geolocation_state` | `0` | `0.00%` | 2 | 2 |

#### 2.8 Duplicate-Key Issues
* **Severe Data Redundancy:** 261,831 completely identical rows across all 5 fields.
* **Zip Code Collision:** Individual zip code prefixes appear up to 1,146 times (e.g. zip code `24220` has 1,146 coordinate observations with minor GPS jitter and alternative city spelling conventions).
* **Geographical Outliers:** Latitude/longitude values include GPS points situated outside Brazil's territorial boundaries (e.g., positive latitudes corresponding to European/North American coordinates due to sensor errors).

#### 2.9 Mapping to Proposed 12-Table ER Model
* Maps to `geolocation_reference` / `zip_codes` table.
* **Transformation Requirement:** Group by `zip_code_prefix` and aggregate mean latitude/longitude, standardizing city names (removing accent discrepancies) to produce a 1:1 zip code dimension table.

#### 2.10 Absent Required Attributes / Entities from ER Model
* Street address / avenue name ranges (logradouro).
* Neighborhood name (bairro).
* Standardized IBGE municipality code (*Código de Município IBGE*).
* Timezone / daylight saving time zone indicators.
* Country code (ISO 3166-1 alpha-2).

---

### 3. `olist_orders_dataset.csv`

#### 3.1 Number of Rows
* **Exact Row Count:** `99,441` rows (plus 1 header row).

#### 3.2 Columns
1. `order_id` (Index 0)
2. `customer_id` (Index 1)
3. `order_status` (Index 2)
4. `order_purchase_timestamp` (Index 3)
5. `order_approved_at` (Index 4)
6. `order_delivered_carrier_date` (Index 5)
7. `order_delivered_customer_date` (Index 6)
8. `order_estimated_delivery_date` (Index 7)

#### 3.3 Appropriate Data Types
* `order_id`: `CHAR(32)` (Fixed-length 32-character hexadecimal MD5 hash string).
* `customer_id`: `CHAR(32)` (Fixed-length 32-character hexadecimal MD5 hash string).
* `order_status`: `VARCHAR(20)` / `ENUM('delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved')`.
* `order_purchase_timestamp`: `DATETIME` / `TIMESTAMP` (`YYYY-MM-DD HH:MM:SS`).
* `order_approved_at`: `DATETIME` / `TIMESTAMP` (Nullable).
* `order_delivered_carrier_date`: `DATETIME` / `TIMESTAMP` (Nullable).
* `order_delivered_customer_date`: `DATETIME` / `TIMESTAMP` (Nullable).
* `order_estimated_delivery_date`: `DATETIME` / `TIMESTAMP` (`YYYY-MM-DD HH:MM:SS`).

#### 3.4 Candidate Primary Keys
* **Candidate Primary Key:** `order_id` (99,441 unique values across 99,441 rows; 0 duplicates, 0 nulls).

#### 3.5 Candidate Foreign Keys
* `customer_id` $\rightarrow$ `olist_customers_dataset(customer_id)` (100% referential match; 0 orphan orders).

#### 3.6 Relationships with Other Source Files
* **With `olist_customers_dataset.csv`:** **1:1 relationship** on `customer_id`.
* **With `olist_order_items_dataset.csv`:** **1:N relationship** on `order_id` (98,666 orders have associated line items; 775 orders have 0 items due to status cancellations or item unavailability).
* **With `olist_order_payments_dataset.csv`:** **1:N relationship** on `order_id` (99,440 orders have payment records; exactly 1 order `bfbd0f9bdef84302105ad712db648a6c` has 0 payment records).
* **With `olist_order_reviews_dataset.csv`:** **1:N relationship** on `order_id` (98,673 orders have reviews; 768 orders have 0 reviews; 547 orders have multiple review entries).

#### 3.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Status Alignment Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `0` | `0.00%` | 32 | 32 | Complete |
| `customer_id` | `0` | `0.00%` | 32 | 32 | Complete |
| `order_status` | `0` | `0.00%` | 7 | 11 | Complete (8 distinct states) |
| `order_purchase_timestamp` | `0` | `0.00%` | 19 | 19 | Complete (2016-09-04 to 2018-10-17) |
| `order_approved_at` | `160` | `0.16%` | 0 | 19 | Null for unapproved/canceled orders |
| `order_delivered_carrier_date` | `1,783` | `1.79%` | 0 | 19 | Null for undelivered/in-transit orders |
| `order_delivered_customer_date` | `2,965` | `2.98%` | 0 | 19 | Null for non-completed deliveries |
| `order_estimated_delivery_date` | `0` | `0.00%` | 19 | 19 | Complete baseline SLA |

```
Order Status Breakdown across 99,441 records:
  - delivered:   96,478 (97.02%)
  - shipped:      1,107  (1.11%)
  - canceled:       625  (0.63%)
  - unavailable:    609  (0.61%)
  - invoiced:       314  (0.32%)
  - processing:     301  (0.30%)
  - created:          5  (0.01%)
  - approved:         2  (0.00%)
```

#### 3.8 Duplicate-Key Issues
* `order_id`: **0 duplicates** (100% unique).
* `customer_id`: **0 duplicates** (1:1 with customer token).

#### 3.9 Mapping to Proposed 12-Table ER Model
* Maps directly to the core `orders` entity table.
* The shipping milestone timestamps (`order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`) map to the `shipments` / `deliveries` entity.

#### 3.10 Absent Required Attributes / Entities from ER Model
* Order financial summaries (pre-computed `subtotal_amount`, `freight_total_amount`, `discount_total_amount`, `tax_total_amount`, `grand_total_amount`).
* Order currency code (e.g., `'BRL'`).
* Explicit foreign key linking to a dedicated `shipping_address_id` / `billing_address_id`.
* Customer IP address, user agent, referral channel, or session tracking ID.
* Cancellation reason codes, cancellation request timestamp, and cancellation initiator (customer vs seller vs platform).

---

### 4. `olist_order_items_dataset.csv`

#### 4.1 Number of Rows
* **Exact Row Count:** `112,650` rows (plus 1 header row).

#### 4.2 Columns
1. `order_id` (Index 0)
2. `order_item_id` (Index 1)
3. `product_id` (Index 2)
4. `seller_id` (Index 3)
5. `shipping_limit_date` (Index 4)
6. `price` (Index 5)
7. `freight_value` (Index 6)

#### 4.3 Appropriate Data Types
* `order_id`: `CHAR(32)` (MD5 hash).
* `order_item_id`: `SMALLINT` / `INTEGER` (Sequential item counter per order, values `1` through `21`).
* `product_id`: `CHAR(32)` (MD5 hash).
* `seller_id`: `CHAR(32)` (MD5 hash).
* `shipping_limit_date`: `DATETIME` / `TIMESTAMP` (`YYYY-MM-DD HH:MM:SS`).
* `price`: `DECIMAL(10, 2)` (Item unit price in BRL; min: `0.85`, max: `6735.00`, mean: `120.65`).
* `freight_value`: `DECIMAL(10, 2)` (Item shipping freight cost in BRL; min: `0.00`, max: `409.68`, mean: `19.99`).

#### 4.4 Candidate Primary Keys
* **Candidate Primary Key (Composite):** `(order_id, order_item_id)` (112,650 unique pairs across 112,650 rows; 0 duplicates, 0 nulls).
* **Surrogate Key Alternative:** `order_item_pk` (`BIGINT AUTO_INCREMENT`).

#### 4.5 Candidate Foreign Keys
* `order_id` $\rightarrow$ `olist_orders_dataset(order_id)` (100% match; 0 orphans).
* `product_id` $\rightarrow$ `olist_products_dataset(product_id)` (100% match; 0 orphans; all 32,951 products are referenced).
* `seller_id` $\rightarrow$ `olist_sellers_dataset(seller_id)` (100% match; 0 orphans; all 3,095 sellers are referenced).

#### 4.6 Relationships with Other Source Files
* **With `olist_orders_dataset.csv`:** **N:1 relationship** (an order contains 1 to 21 line items).
* **With `olist_products_dataset.csv`:** **N:1 relationship** (products are purchased across multiple order line items).
* **With `olist_sellers_dataset.csv`:** **N:1 relationship** (sellers fulfill specific order line items).

#### 4.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Min Value | Max Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `0` | `0.00%` | 32 | 32 | — | — |
| `order_item_id` | `0` | `0.00%` | 1 | 2 | 1 | 21 |
| `product_id` | `0` | `0.00%` | 32 | 32 | — | — |
| `seller_id` | `0` | `0.00%` | 32 | 32 | — | — |
| `shipping_limit_date` | `0` | `0.00%` | 19 | 19 | 2016-09-19 | 2020-04-09 |
| `price` | `0` | `0.00%` | 4 | 7 | 0.85 | 6,735.00 |
| `freight_value` | `0` | `0.00%` | 4 | 6 | 0.00 | 409.68 |

#### 4.8 Duplicate-Key Issues
* Composite `(order_id, order_item_id)`: **0 duplicates** (100% unique).
* Individual foreign key columns have expected duplicates representing repeated purchases and multi-item vendor orders.

#### 4.9 Mapping to Proposed 12-Table ER Model
* Maps directly to `order_items` junction/associative table linking Orders, Products, and Sellers.
* Implicitly informs `seller_inventory` / `product_sellers` regarding seller-product catalog offerings.

#### 4.10 Absent Required Attributes / Entities from ER Model
* `quantity` attribute: In Olist, purchasing 3 identical units generates 3 distinct rows with `order_item_id = 1, 2, 3` rather than a single row with `quantity = 3`.
* Line-item discount amount / promotional code applied at item level.
* Line-item tax amount (ICMS, PIS, COFINS).
* Individual item fulfillment status (e.g., `PENDING`, `PICKED`, `PACKED`, `SHIPPED`, `RETURNED`, `REFUNDED`).
* Seller SKU code / product variation identifiers (color, size, storage capacity).
* Platform commission cut percentage / marketplace fee amount charged to the vendor for that line item.

---

### 5. `olist_order_payments_dataset.csv`

#### 5.1 Number of Rows
* **Exact Row Count:** `103,886` rows (plus 1 header row).

#### 5.2 Columns
1. `order_id` (Index 0)
2. `payment_sequential` (Index 1)
3. `payment_type` (Index 2)
4. `payment_installments` (Index 3)
5. `payment_value` (Index 4)

#### 5.3 Appropriate Data Types
* `order_id`: `CHAR(32)` (MD5 hash).
* `payment_sequential`: `SMALLINT` / `INTEGER` (Sequential split counter, values `1` through `29`).
* `payment_type`: `VARCHAR(20)` / `ENUM('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined')`.
* `payment_installments`: `SMALLINT` / `INTEGER` (Number of monthly installments, values `0` through `24`).
* `payment_value`: `DECIMAL(10, 2)` (Transaction amount in BRL; min: `0.00`, max: `13664.08`, mean: `154.10`).

#### 5.4 Candidate Primary Keys
* **Candidate Primary Key (Composite):** `(order_id, payment_sequential)` (103,886 unique pairs across 103,886 rows; 0 duplicates, 0 nulls).
* **Surrogate Key Alternative:** `payment_id` (`BIGINT AUTO_INCREMENT`).

#### 5.5 Candidate Foreign Keys
* `order_id` $\rightarrow$ `olist_orders_dataset(order_id)` (100% match; 0 orphans).

#### 5.6 Relationships with Other Source Files
* **With `olist_orders_dataset.csv`:** **N:1 relationship** (an order can have multiple payment methods/split payments; 99,440 orders have payments).

#### 5.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Distinct Count | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `0` | `0.00%` | 32 | 32 | 99,440 | `'b81ef226f3fe1789b1e8b2acac839d17'` |
| `payment_sequential` | `0` | `0.00%` | 1 | 2 | 29 | `1`, `2`, `3` |
| `payment_type` | `0` | `0.00%` | 6 | 11 | 5 | `'credit_card'`, `'boleto'`, `'voucher'` |
| `payment_installments`| `0` | `0.00%` | 1 | 2 | 24 | `1`, `8`, `10` |
| `payment_value` | `0` | `0.00%` | 4 | 8 | 29,077 | `99.33`, `24.39`, `65.71` |

```
Payment Types Distribution across 103,886 records:
  - credit_card:  76,795 (73.92%)
  - boleto:       19,784 (19.04%)
  - voucher:       5,775  (5.56%)
  - debit_card:    1,529  (1.47%)
  - not_defined:       3  (0.00%)
```

#### 5.8 Duplicate-Key Issues
* Composite `(order_id, payment_sequential)`: **0 duplicates** (100% unique).
* **Data Domain Anomalies:**
  * 3 records exhibit `payment_type = 'not_defined'` with `payment_value = 0.00`.
  * 2 records exhibit `payment_installments = 0` with non-zero payment values.
  * 9 records exhibit `payment_value = 0.00` (predominantly voucher reconciliation placeholders).

#### 5.9 Mapping to Proposed 12-Table ER Model
* Maps directly to `payments` / `order_payments` entity table.

#### 5.10 Absent Required Attributes / Entities from ER Model
* Payment gateway transaction ID / Authorization Code (e.g., Stripe, Adyen, PagSeguro reference).
* Payment status lifecycle (`PENDING`, `AUTHORIZED`, `SETTLED`, `FAILED`, `DECLINED`, `REFUNDED`, `CHARGEBACK`).
* Payment gateway provider / acquirer name (Cielo, Rede, Stone).
* Credit card brand / scheme (Visa, MasterCard, Elo, Hipercard, Amex).
* Masked card number (last 4 digits) and cardholder name.
* Payment authorization timestamp and settlement timestamp.
* Currency code (ISO 4217).

---

### 6. `olist_order_reviews_dataset.csv`

#### 6.1 Number of Rows
* **Exact Row Count:** `99,224` rows (plus 1 header row).

#### 6.2 Columns
1. `review_id` (Index 0)
2. `order_id` (Index 1)
3. `review_score` (Index 2)
4. `review_comment_title` (Index 3)
5. `review_comment_message` (Index 4)
6. `review_creation_date` (Index 5)
7. `review_answer_timestamp` (Index 6)

#### 6.3 Appropriate Data Types
* `review_id`: `CHAR(32)` (MD5 hash).
* `order_id`: `CHAR(32)` (MD5 hash).
* `review_score`: `TINYINT` / `SMALLINT` (Integer rating scale `1` through `5`).
* `review_comment_title`: `VARCHAR(100)` (Max observed text length: 26 characters).
* `review_comment_message`: `TEXT` / `VARCHAR(500)` (Max length: 208 characters; contains multilingual Portuguese text and embedded newline characters).
* `review_creation_date`: `DATETIME` / `TIMESTAMP` (`YYYY-MM-DD 00:00:00` survey trigger date).
* `review_answer_timestamp`: `DATETIME` / `TIMESTAMP` (`YYYY-MM-DD HH:MM:SS` customer response time).

#### 6.4 Candidate Primary Keys
* **Single Column `review_id`:** **NOT Unique** (98,410 distinct IDs for 99,224 rows; 789 duplicate review IDs exist).
* **Composite Key:** `(review_id, order_id)` (99,224 unique pairs across 99,224 rows; 0 duplicates, 0 nulls).
* **Surrogate Key Recommendation:** `review_pk` (`BIGINT AUTO_INCREMENT`).

#### 6.5 Candidate Foreign Keys
* `order_id` $\rightarrow$ `olist_orders_dataset(order_id)` (100% match; 0 orphans).

#### 6.6 Relationships with Other Source Files
* **With `olist_orders_dataset.csv`:** **N:1 relationship** (98,673 unique orders; 547 orders have multiple review entries).

#### 6.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Remarks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `review_id` | `0` | `0.00%` | 32 | 32 | Complete |
| `order_id` | `0` | `0.00%` | 32 | 32 | Complete |
| `review_score` | `0` | `0.00%` | 1 | 1 | Complete (Scores 1 to 5) |
| `review_comment_title` | **`87,658`** | **`88.34%`** | 0 | 26 | Optional survey title |
| `review_comment_message`| **`58,274`** | **`58.73%`** | 0 | 208 | Optional feedback text |
| `review_creation_date` | `0` | `0.00%` | 19 | 19 | Complete |
| `review_answer_timestamp`| `0` | `0.00%` | 19 | 19 | Complete |

```
Review Score Rating Distribution:
  - 5 Stars: 57,328 (57.78%)
  - 4 Stars: 19,142 (19.29%)
  - 1 Star:  11,424 (11.51%)
  - 3 Stars:  8,179  (8.24%)
  - 2 Stars:  3,151  (3.18%)
```

#### 6.8 Duplicate-Key Issues
* `review_id`: **789 duplicate key occurrences**. The same `review_id` is linked to multiple orders when a customer places several orders simultaneously and receives a single unified survey ID.
* Composite `(review_id, order_id)`: **0 duplicates** (100% unique).

#### 6.9 Mapping to Proposed 12-Table ER Model
* Maps directly to `reviews` / `order_reviews` entity.

#### 6.10 Absent Required Attributes / Entities from ER Model
* `product_id`: The raw dataset records reviews strictly at the **order level**; there is no direct attribute indicating which specific product in a multi-product order the comment refers to.
* `seller_id`: No separate seller rating score (customer evaluates overall fulfillment).
* Review verification badge (e.g. `is_verified_buyer`).
* Moderation / approval status (`APPROVED`, `FLAGGED`, `REJECTED`).
* Review helpfulness count / upvote tally.
* Review multimedia attachments (photos/videos uploaded by customer).

---

### 7. `olist_products_dataset.csv`

#### 7.1 Number of Rows
* **Exact Row Count:** `32,951` rows (plus 1 header row).

#### 7.2 Columns
1. `product_id` (Index 0)
2. `product_category_name` (Index 1)
3. `product_name_lenght` (Index 2 - *note original Portuguese spelling with 'ght'*)
4. `product_description_lenght` (Index 3 - *note original Portuguese spelling with 'ght'*)
5. `product_photos_qty` (Index 4)
6. `product_weight_g` (Index 5)
7. `product_length_cm` (Index 6)
8. `product_height_cm` (Index 7)
9. `product_width_cm` (Index 8)

#### 7.3 Appropriate Data Types
* `product_id`: `CHAR(32)` (MD5 hash).
* `product_category_name`: `VARCHAR(50)` (Portuguese category slug; max length: 46 characters).
* `product_name_length`: `SMALLINT` / `INTEGER` (Nullable character length of product name).
* `product_description_length`: `INTEGER` (Nullable character length of product description).
* `product_photos_qty`: `SMALLINT` / `INTEGER` (Nullable count of photos, values `1` through `20`).
* `product_weight_g`: `INTEGER` / `DECIMAL(10, 2)` (Nullable product weight in grams; range: `0` to `40,425` g).
* `product_length_cm`: `INTEGER` / `DECIMAL(10, 2)` (Nullable product package length in cm; range: `7` to `105` cm).
* `product_height_cm`: `INTEGER` / `DECIMAL(10, 2)` (Nullable product package height in cm; range: `2` to `105` cm).
* `product_width_cm`: `INTEGER` / `DECIMAL(10, 2)` (Nullable product package width in cm; range: `6` to `118` cm).

#### 7.4 Candidate Primary Keys
* **Candidate Primary Key:** `product_id` (32,951 unique values across 32,951 rows; 0 duplicates, 0 nulls).

#### 7.5 Candidate Foreign Keys
* `product_category_name` $\rightarrow$ `product_category_name_translation(product_category_name)`.
  * *Referential check:* 71 categories match; **2 categories** (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) containing 18 products are missing from the translation file.

#### 7.6 Relationships with Other Source Files
* **With `olist_order_items_dataset.csv`:** **1:N relationship** (all 32,951 products in the catalog have been ordered at least once).
* **With `product_category_name_translation.csv`:** **N:1 relationship** on category name.

#### 7.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Min Value | Max Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | `0` | `0.00%` | 32 | 32 | — | — |
| `product_category_name` | **`610`** | **`1.85%`** | 0 | 46 | — | — |
| `product_name_lenght` | **`610`** | **`1.85%`** | 0 | 2 | 5 | 76 |
| `product_description_lenght`| **`610`** | **`1.85%`** | 0 | 4 | 4 | 3,992 |
| `product_photos_qty` | **`610`** | **`1.85%`** | 0 | 2 | 1 | 20 |
| `product_weight_g` | **`2`** | **`0.01%`** | 0 | 5 | 0 | 40,425 |
| `product_length_cm` | **`2`** | **`0.01%`** | 0 | 3 | 7 | 105 |
| `product_height_cm` | **`2`** | **`0.01%`** | 0 | 3 | 2 | 105 |
| `product_width_cm` | **`2`** | **`0.01%`** | 0 | 3 | 6 | 118 |

#### 7.8 Duplicate-Key Issues
* `product_id`: **0 duplicates** (100% unique).

#### 7.9 Mapping to Proposed 12-Table ER Model
* Maps directly to `products` catalog master entity.

#### 7.10 Absent Required Attributes / Entities from ER Model
* Actual product title / name text (only string character count is available).
* Full product description text / marketing bullet points (only character length is provided).
* Product brand name / manufacturer entity.
* Universal Product Code (UPC / EAN / Barcode / ISBN).
* Product stock level / inventory quantity on hand.
* Product listing status (`ACTIVE`, `INACTIVE`, `DRAFT`, `ARCHIVED`).
* Product images / media gallery URLs (only photo count is provided).
* Standard product MSRP / base price (pricing is set dynamically per seller in order items).

---

### 8. `olist_sellers_dataset.csv`

#### 8.1 Number of Rows
* **Exact Row Count:** `3,095` rows (plus 1 header row).

#### 8.2 Columns
1. `seller_id` (Index 0)
2. `seller_zip_code_prefix` (Index 1)
3. `seller_city` (Index 2)
4. `seller_state` (Index 3)

#### 8.3 Appropriate Data Types
* `seller_id`: `CHAR(32)` (Fixed-length 32-character hexadecimal MD5 hash string).
* `seller_zip_code_prefix`: `VARCHAR(5)` / `CHAR(5)` (Preserves leading zeros; e.g. `'13023'`).
* `seller_city`: `VARCHAR(40)` (Actual max length: 40 characters).
* `seller_state`: `CHAR(2)` (2-character state code; 23 unique states).

#### 8.4 Candidate Primary Keys
* **Candidate Primary Key:** `seller_id` (3,095 unique values across 3,095 rows; 0 duplicates, 0 nulls).

#### 8.5 Candidate Foreign Keys
* `seller_zip_code_prefix` $\rightarrow$ `olist_geolocation_dataset(geolocation_zip_code_prefix)`.
  * *Referential check:* 2,239 seller zip prefixes match; **7 seller zip prefixes** are unrepresented in the geolocation file.

#### 8.6 Relationships with Other Source Files
* **With `olist_order_items_dataset.csv`:** **1:N relationship** (all 3,095 sellers have fulfilled at least one order line item).
* **With `olist_geolocation_dataset.csv`:** **N:1 relationship** on zip code prefix.

#### 8.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length | Unique Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seller_id` | `0` | `0.00%` | 32 | 32 | 3,095 |
| `seller_zip_code_prefix` | `0` | `0.00%` | 5 | 5 | 2,246 |
| `seller_city` | `0` | `0.00%` | 2 | 40 | 611 |
| `seller_state` | `0` | `0.00%` | 2 | 2 | 23 |

#### 8.8 Duplicate-Key Issues
* `seller_id`: **0 duplicates** (100% unique).

#### 8.9 Mapping to Proposed 12-Table ER Model
* Maps directly to `sellers` / `vendors` entity table.

#### 8.10 Absent Required Attributes / Entities from ER Model
* Merchant store trade name / brand display name.
* Legal corporate entity name (Razão Social).
* Corporate Brazilian Tax Registration Number (CNPJ - *Cadastro Nacional da Pessoa Jurídica*).
* Seller business contact email address and phone number.
* Seller account registration timestamp and verification status (`PENDING_KYC`, `VERIFIED`, `SUSPENDED`).
* Seller commission agreement tier / platform fee schedule.
* Bank account / payout settlement routing details (Bank code, agency, account number, PIX key).
* Seller rating score summary / tier badge.

---

### 9. `product_category_name_translation.csv`

#### 9.1 Number of Rows
* **Exact Row Count:** `71` rows (plus 1 header row).

#### 9.2 Columns
1. `product_category_name` (Index 0 - *Note: raw file begins with UTF-8 BOM `\ufeff`*)
2. `product_category_name_english` (Index 1)

#### 9.3 Appropriate Data Types
* `product_category_name`: `VARCHAR(50)` (Portuguese category slug; max length: 46 characters).
* `product_category_name_english`: `VARCHAR(50)` (English translated name; max length: 39 characters).

#### 9.4 Candidate Primary Keys
* **Candidate Primary Key:** `product_category_name` (71 unique values across 71 rows; 0 duplicates, 0 nulls).
* **Alternate Candidate Key:** `product_category_name_english` (71 unique values; 0 duplicates, 0 nulls).

#### 9.5 Candidate Foreign Keys
* None. Serves as master translation dimension.

#### 9.6 Relationships with Other Source Files
* **With `olist_products_dataset.csv`:** **1:N relationship** on `product_category_name`.

#### 9.7 Missing-Value Statistics
| Column Name | Missing Count | Missing Percentage | Min Length | Max Length |
| :--- | :--- | :--- | :--- | :--- |
| `product_category_name` | `0` | `0.00%` | 3 | 46 |
| `product_category_name_english` | `0` | `0.00%` | 3 | 39 |

#### 9.8 Duplicate-Key Issues
* `product_category_name`: **0 duplicates** (100% unique).
* `product_category_name_english`: **0 duplicates** (100% unique).
* **Source Anomaly:** UTF-8 Byte Order Mark (`\ufeff`) is present at the start of column 0 (`\ufeffproduct_category_name`), requiring `utf-8-sig` encoding decoding in ETL pipelines.
* **Coverage Gap:** 2 categories present in `olist_products_dataset` (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) are absent from this file.

#### 9.9 Mapping to Proposed 12-Table ER Model
* Maps to `product_categories` entity table.

#### 9.10 Absent Required Attributes / Entities from ER Model
* Category hierarchy (Parent category ID `parent_category_id` for multi-level category trees).
* Category description text.
* Category display image / icon URL.
* Category display order / sort weight.
* Active status flag (`is_active`).

---

## Cross-Dataset Referential Integrity & Consistency Matrix

The following matrix documents the exact referential integrity checks performed across all candidate primary-to-foreign key relationships across the 9 raw files:

| Source (Child) Column | Target (Parent) Column | Total Child Keys | Distinct Keys | Unmatched / Orphan Keys | Integrity Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `orders.customer_id` | `customers.customer_id` | 99,441 | 99,441 | **`0`** | **100% Valid (Perfect 1:1 Match)** |
| `order_items.order_id` | `orders.order_id` | 112,650 | 98,666 | **`0`** | **100% Valid (775 orders have 0 items due to cancellation)** |
| `order_items.product_id` | `products.product_id` | 112,650 | 32,951 | **`0`** | **100% Valid (All 32,951 products ordered)** |
| `order_items.seller_id` | `sellers.seller_id` | 112,650 | 3,095 | **`0`** | **100% Valid (All 3,095 sellers active)** |
| `order_payments.order_id` | `orders.order_id` | 103,886 | 99,440 | **`0`** | **100% Valid (1 order missing payment record)** |
| `order_reviews.order_id` | `orders.order_id` | 99,224 | 98,673 | **`0`** | **100% Valid (768 orders unreviewed; 547 have >1 review)** |
| `products.product_category_name` | `translations.product_category_name` | 32,341 | 73 | **`2` Categories (18 products)** | **Missing `pc_gamer` & `portateis_cozinha...`** |
| `customers.customer_zip_code_prefix` | `geolocation.geolocation_zip_code_prefix` | 99,441 | 14,994 | **`157` Zip Codes** | **Incomplete geolocation spatial coverage** |
| `sellers.seller_zip_code_prefix` | `geolocation.geolocation_zip_code_prefix` | 3,095 | 2,246 | **`7` Zip Codes** | **Incomplete geolocation spatial coverage** |

---

## Proposed 12-Table ER Model Mapping & Gap Analysis

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PROPOSED 12-TABLE ER SCHEMA                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [1. customers] ────────(1:N)───────► [2. customer_addresses]                                    │
│        │                                     ▲                                                   │
│        │ (1:N)                               │ (N:1)                                             │
│        ▼                                     │                                                   │
│  [7. orders] ────────────────────────────────┘                                                   │
│        │                                                                                         │
│        ├───(1:N)───► [8. order_items] ◄───(N:1)─── [5. products] ◄───(N:1)─── [4. categories]    │
│        │                   ▲                             ▲                                       │
│        │                   │ (N:1)                       │ (1:N)                                 │
│        │             [3. sellers] ◄───(1:N)─── [6. seller_inventory]                             │
│        │                                                                                         │
│        ├───(1:N)───► [9. order_payments]                                                         │
│        │                                                                                         │
│        ├───(1:N)───► [10. order_reviews]                                                         │
│        │                                                                                         │
│        └───(1:N)───► [11. shipments]                                                            │
│                                                                                                  │
│  [12. geolocation_reference]  (Master Spatial Reference Table)                                   │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

The table below provides a full mapping from the 9 raw CSV files to a canonical 12-table Normalized Multi-Vendor E-Commerce ER Schema, specifying source column lineages, necessary data transformations, and all domain attributes that are completely absent from the source dataset:

| # | ER Model Table | Source CSV File(s) | Primary Key Strategy | Mapped Attributes from Source | Critical Absent Attributes in Source Dataset |
| :- | :--- | :--- | :--- | :--- | :--- |
| **1** | **`customers`** | `olist_customers_dataset.csv` | `customer_unique_id` (`CHAR(32)`) | `customer_unique_id` | Real customer name, email, phone number, password hash, CPF tax ID, account creation timestamp, account status. |
| **2** | **`customer_addresses`** | `olist_customers_dataset.csv` | `address_id` (Surrogate `BIGINT` / `customer_id`) | `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` | Street address (logradouro), building number, complement/apartment number, neighborhood (bairro), default address flag. |
| **3** | **`sellers`** | `olist_sellers_dataset.csv` | `seller_id` (`CHAR(32)`) | `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state` | Store trade name, legal business name, CNPJ tax registration, contact email, phone number, bank payout details, commission rate. |
| **4** | **`product_categories`** | `product_category_name_translation.csv` + `olist_products_dataset.csv` | `category_id` (Surrogate `INT`) | `product_category_name` (Portuguese), `product_category_name_english` | Hierarchy (`parent_category_id`), category description, category icon/banner image, display order, active status. |
| **5** | **`products`** | `olist_products_dataset.csv` | `product_id` (`CHAR(32)`) | `product_id`, `product_category_name`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | Actual product title, full product description, brand/manufacturer, barcode/EAN/UPC, base MSRP price, active status. |
| **6** | **`seller_inventory`** | `olist_order_items_dataset.csv` (Derived listing) | `listing_id` (Surrogate `BIGINT`) / Composite `(seller_id, product_id)` | `seller_id`, `product_id`, `price` (historical listed price) | Real-time stock quantity on hand, seller custom SKU, reorder threshold, minimum order quantity, listing creation date. |
| **7** | **`orders`** | `olist_orders_dataset.csv` | `order_id` (`CHAR(32)`) | `order_id`, `customer_id` (FK to addresses), `order_status`, `order_purchase_timestamp`, `order_approved_at` | Order subtotal, total discount, tax total, order grand total, currency code, coupon code applied, cancellation reason. |
| **8** | **`order_items`** | `olist_order_items_dataset.csv` | Composite `(order_id, order_item_id)` / Surrogate `item_id` | `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value` | Item quantity (currently expanded into separate rows), item tax, item discount, line-item status, seller commission cut. |
| **9** | **`order_payments`** | `olist_order_payments_dataset.csv` | Composite `(order_id, payment_sequential)` / Surrogate `payment_id` | `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value` | Gateway transaction ID, payment status (`AUTHORIZED`, `SETTLED`), card brand/scheme, card last 4 digits, currency, settlement date. |
| **10**| **`order_reviews`** | `olist_order_reviews_dataset.csv` | Composite `(review_id, order_id)` / Surrogate `review_pk` | `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp` | Direct line-item `product_id` link, seller rating score, verified buyer badge, review moderation status, upvote count, media attachments. |
| **11**| **`shipments`** | `olist_orders_dataset.csv` (+ `olist_order_items_dataset.csv`) | `shipment_id` (Surrogate `BIGINT` / `order_id`) | `order_id`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date` | Carrier company name (Correios, Loggi), carrier tracking number, delivery attempt count, shipping method (SEDEX, PAC), proof of delivery. |
| **12**| **`geolocation_reference`** | `olist_geolocation_dataset.csv` | `zip_code_prefix` (`VARCHAR(5)`) (after aggregation) | `geolocation_zip_code_prefix`, `geolocation_lat` (mean), `geolocation_lng` (mean), `geolocation_city`, `geolocation_state` | Standardized IBGE municipality code, street range, neighborhood name, timezone offset, ISO country code. |

---

## Key Data Transformation & Quality Considerations

1. **Customer Identity Normalization:**
   * `olist_customers_dataset.csv` provides `customer_id` (an order-specific token) and `customer_unique_id` (the true customer identifier). The database design must normalize `customer_unique_id` into the `customers` table and `customer_id` into the `customer_addresses` / `orders` table to properly model repeat customer behavior.

2. **Geolocation Deduplication:**
   * `olist_geolocation_dataset.csv` cannot be imported directly as a 1:1 table without prior deduplication. It contains 261,831 exact duplicate rows and multiple coordinate entries per zip code. An ETL aggregation step (averaging latitude and longitude per `geolocation_zip_code_prefix`) is required before creating a unique primary key constraint.

3. **Category Translation Gaps & UTF-8 BOM Handling:**
   * `product_category_name_translation.csv` contains a UTF-8 BOM header on the first column.
   * Two product categories (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) are missing from the translation table and must either be preserved in Portuguese or supplemented during ETL without inventing unverified source categories.

4. **Review ID Duplication:**
   * `review_id` in `olist_order_reviews_dataset.csv` has 789 duplicate instances across multiple orders. The relational schema should either use a composite key `(review_id, order_id)` or generate a synthetic auto-increment primary key (`review_pk`).

5. **Order Items Quantity Expansion:**
   * Orders with multiple quantities of the same product are represented in the raw data as multiple distinct rows with sequential `order_item_id` rather than a single row with a `quantity` attribute. The target schema must decide whether to retain line-item sequential modeling or aggregate into `(order_id, product_id, seller_id)` tuples with a `quantity` attribute.

---

*Report concluded. No SQL tables were created, no raw CSV files were modified, and no missing source information was invented.*
