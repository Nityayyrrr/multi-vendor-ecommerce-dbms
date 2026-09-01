# Canonical 12-Table Relational Schema Architecture Specification
## Multi-Vendor E-Commerce Database Management System (DBMS)

> [!IMPORTANT]
> **DOCUMENT CLASSIFICATION: ACTIVE AUTHORITATIVE SCHEMA SPECIFICATION**  
> This document is the single active, approved canonical database architecture specification defining the 12 MySQL 8.4 tables, constraints, keys, and loading dependencies.

**Target File Location:** `documentation/final_schema_specification.md`  
**Target RDBMS:** MySQL 8.4 LTS (InnoDB Storage Engine, UTF8MB4 Character Set)  
**Specification Date:** 2026-09-01  
**Status:** Approved Canonical Schema Architecture (Design & Transformation Specification)

---

## 1. Executive Summary & Design Principles

This document defines the definitive **12-table canonical relational database schema** and its corresponding **13-stage data-loading process** for the Multi-Vendor E-Commerce Database Management System.

### Core Architectural Decisions:

1. **Strict 12-Table Entity Model:**  
   The relational schema strictly consists of the 12 prescribed tables: `customer`, `customer_phone`, `address`, `vendor`, `category`, `product`, `product_tag`, `warehouse`, `inventory`, `orders`, `order_item`, and `payment`. No alternative table names or unprescribed core entities (such as reviews, shipments, or raw geolocation tables) are introduced.

2. **12-Table Schema, 13-Stage Data-Loading Process:**  
   Although the schema has exactly 12 tables, data loading follows a **13-stage sequence**. Table 5 (`category`) models a recursive self-referencing hierarchy and is populated across two distinct topological stages (Stage 1: Root parent categories with `parent_category_id IS NULL`; Stage 2: Child subcategories referencing parent category IDs).

3. **Weak / Dependent Entity Modeling for `payment`:**  
   In classical relational database theory, `payment` is modeled as an **identifying weak entity** dependent on `orders`. A payment transaction is identified within the scope of its parent order using the composite primary key `(order_id, payment_id)`. Here, `order_id` is both a foreign key and part of the primary key, while `payment_id` serves as the partial key / discriminator (mapped from Olist's `payment_sequential`). This enforces strict existence dependency: a payment cannot exist independently of an order.

4. **Honest Source vs. Augmented Data Lineage:**  
   The Brazilian E-Commerce Olist dataset serves as the empirical backbone for real-world transaction topologies, pricing, order timelines, categories, and geographic locations. Missing enterprise attributes (such as customer names, authentication credentials, vendor tax IDs, warehouse hubs, product tags, and inventory stock levels) are cleanly modeled with explicit synthetic/augmented data generation pipelines. Source data boundaries are preserved without pretending missing attributes existed in the raw CSVs.

5. **Academic Normalization Standard (Designed to satisfy 3NF, with BCNF satisfied where applicable):**  
   The schema focuses on clear, academically defensible normalization progression ($1\text{NF} \rightarrow 2\text{NF} \rightarrow 3\text{NF}$):
   - **1NF Compliance:** Multivalued customer phone numbers are decomposed into `customer_phone`, and multivalued product tags are decomposed into `product_tag`. All attributes contain strictly atomic scalar values.
   - **2NF Compliance:** Partial key dependencies are eliminated in composite-key entities (`address`, `customer_phone`, `product_tag`, `inventory`, `order_item`, `payment`). Every non-prime attribute is fully functionally dependent on the entire candidate/primary key.
   - **3NF Compliance:** Transitive dependencies are eliminated across all entities (e.g., categories reference parent categories via recursive self-reference; vendor profile attributes are isolated from product catalog items; customer delivery addresses are isolated from customer profiles).
   - **BCNF Alignment:** For relations with strictly independent candidate key determinants, Boyce-Codd Normal Form is satisfied where applicable without risking functional dependency loss.

6. **Referential Integrity & Cardinality Rules:**
   - `orders` (1) $\rightarrow$ (N) `payment` (resolving Olist split payments: credit card, voucher, etc. under composite key `(order_id, payment_id)`).
   - `orders` (M) $\leftrightarrow$ (N) `product` resolved via `order_item` with composite PK `(order_id, product_id)`.
   - `product` (M) $\leftrightarrow$ (N) `warehouse` resolved via `inventory` with composite PK `(product_id, warehouse_id)`.
   - `category` models a hierarchical tree using recursive self-referencing `parent_category_id FK`.
   - `product` belongs to **exactly one** `vendor` and **exactly one** `category`.

---

## 2. Global Entity-Relationship (ER) Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       CANONICAL 12-TABLE ER ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                             │
│                                  ┌──────────────────────────┐                                               │
│                                  │         category         │◄─────────┐ (Recursive 1:N)                    │
│                                  └─────────────┬────────────┘          │ (parent_category_id)               │
│                                                │ (1:N)                 │                                    │
│                                                ▼                       │                                    │
│   ┌─────────────────────────┐            ┌───────────┐                 │                                    │
│   │       product_tag       │◄───(1:N)───┤  product  │                 │                                    │
│   └─────────────────────────┘            └─────┬─────┘                 │                                    │
│                                                │                       │                                    │
│        ┌─────────────────────────┐             │ (N:1)                 │                                    │
│        │         vendor          │◄────────────┤                       │                                    │
│        └─────────────────────────┘             │                       │                                    │
│                                                │                       │                                    │
│        ┌─────────────────────────┐             │ (1:N)                 │                                    │
│        │        inventory        │◄────────────┤                       │                                    │
│        └────────────▲────────────┘             │                       │                                    │
│                     │ (N:1)                    │                       │                                    │
│        ┌────────────┴────────────┐             │                       │                                    │
│        │        warehouse        │             │                       │                                    │
│        └─────────────────────────┘             │                       │                                    │
│                                                │                       │                                    │
│   ┌─────────────────────────┐                  │                       │                                    │
│   │     customer_phone      │                  │                       │                                    │
│   └────────────▲────────────┘                  │                       │                                    │
│                │ (N:1)                         │                       │                                    │
│   ┌────────────┴────────────┐                  ▼                       │                                    │
│   │        customer         │◄──(N:1)───┌─────────────┐                │                                    │
│   └────────────┬────────────┘           │ order_item  │                │                                    │
│                │ (1:N)                  └──────▲──────┘                │                                    │
│                ▼                               │ (N:1)                 │                                    │
│   ┌─────────────────────────┐           ┌──────┴──────┐                │                                    │
│   │         address         │           │   orders    │────────────────┘                                    │
│   └─────────────────────────┘           └──────┬──────┘                                                     │
│                                                │ (1:N Identifying Relationship)                             │
│                                                ▼                                                            │
│                                         ┌─────────────┐                                                     │
│                                         │   payment   │ (Weak Entity: PK (order_id, payment_id))            │
│                                         └─────────────┘                                                     │
│                                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Comprehensive Table-by-Table Specifications

---

### Table 1: `customer`
* **Purpose:** Stores the unique identity profile of real-world retail customers across all orders.
* **Source Entity:** Derived from `olist_customers_dataset.csv` grouped by `customer_unique_id`.

#### 3.1.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `PRIMARY KEY`, `NOT NULL` | None | Unique customer hex hash (mapped from `customer_unique_id`). |
| `name` | `VARCHAR(100)` | `NOT NULL` | None | Full legal customer name (Synthetic/Augmented). |
| `email` | `VARCHAR(150)` | `NOT NULL`, `UNIQUE` | None | Unique customer email address (Synthetic/Augmented). |
| `join_date` | `DATETIME` | `NOT NULL` | `CURRENT_TIMESTAMP` | Date and time customer registered/first transacted. |

#### 3.1.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (customer_id)`
* **Unique Constraints:** `UNIQUE KEY uq_customer_email (email)`
* **Check Constraints:**
  - `CONSTRAINT chk_customer_email_format CHECK (email LIKE '%_@__%.__%')`
  - `CONSTRAINT chk_customer_join_date CHECK (join_date >= '2016-01-01 00:00:00')`

#### 3.1.3 Relationships & Normalization
* **Cardinalities:**
  - `customer` (1) $\rightarrow$ (0..N) `orders` (Mandatory in source data, optional in business lifecycle).
  - `customer` (1) $\rightarrow$ (1..N) `customer_phone` (Mandatory total participation; weak entity).
  - `customer` (1) $\rightarrow$ (1..N) `address` (Mandatory total participation; weak entity).
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.**  
  - *1NF:* All attributes are atomic.
  - *2NF:* No partial key dependencies (primary key is single-column `customer_id`).
  - *3NF:* No transitive dependencies ($customer\_id \rightarrow \{name, email, join_date\}$).

---

### Table 2: `customer_phone`
* **Purpose:** Resolves the multivalued customer phone-number attribute into first normal form (1NF).
* **Source Entity:** Synthetic augmentation linked to `customer.customer_id`.

#### 3.2.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `NOT NULL` | None | Identifying foreign key referencing `customer.customer_id`. |
| `phone_number` | `VARCHAR(20)` | `NOT NULL` | None | E.164 formatted telephone/mobile number (Synthetic). |
| `phone_type` | `VARCHAR(20)` | `NOT NULL` | `'Mobile'` | Phone classification (`'Mobile'`, `'Home'`, `'Work'`, `'Office'`, `'Other'`). |

#### 3.2.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (customer_id, phone_number)`
* **Foreign Key:** `FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE`
* **Check Constraints:**
  - `CONSTRAINT chk_phone_number_length CHECK (CHAR_LENGTH(phone_number) >= 8)`
  - `CONSTRAINT chk_phone_type CHECK (phone_type IN ('Mobile', 'Home', 'Work', 'Office', 'Other'))`

#### 3.2.3 Relationships & Normalization
* **Cardinalities:** `customer` (1) $\rightarrow$ (1..N) `customer_phone`.
* **Referential Action:** `ON DELETE CASCADE` ensures customer phone records are purged upon parent customer account deletion.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** As an identifying entity keyed by `(customer_id, phone_number)`, `phone_type` is fully dependent on the composite key, satisfying 3NF/BCNF.

---

### Table 3: `address`
* **Purpose:** Stores structured shipping, billing, and home delivery addresses dependent on individual customers.
* **Source Entity:** Normalized from `olist_customers_dataset.csv` + synthetic street logradouro.

#### 3.3.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `VARCHAR(32)` | `NOT NULL` | None | Identifying foreign key referencing `customer.customer_id`. |
| `address_type` | `VARCHAR(20)` | `NOT NULL` | `'Shipping'` | Discriminator type (`'Shipping'`, `'Billing'`, `'Home'`, `'Office'`). |
| `street` | `VARCHAR(150)` | `NOT NULL` | None | Street name, house/building number, and apartment/suite (Synthetic). |
| `city` | `VARCHAR(50)` | `NOT NULL` | None | Municipality / city name (Source: `customer_city`). |
| `state` | `CHAR(2)` | `NOT NULL` | None | 2-character administrative state code (Source: `customer_state`). |
| `pincode` | `VARCHAR(10)` | `NOT NULL` | None | 5-digit postal-code prefix (Source: `customer_zip_code_prefix`). |
| `is_default` | `BOOLEAN` | `NOT NULL` | `0` | Flag indicating default address for the type (0=No, 1=Yes). |

#### 3.3.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (customer_id, address_type)`
* **Foreign Key:** `FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE`
* **Check Constraints:**
  - `CONSTRAINT chk_address_type CHECK (address_type IN ('Shipping', 'Billing', 'Home', 'Office'))`
  - `CONSTRAINT chk_address_state_len CHECK (CHAR_LENGTH(state) = 2)`

#### 3.3.3 Relationships & Normalization
* **Cardinalities:** `customer` (1) $\rightarrow$ (1..N) `address`.
* **Referential Action:** `ON DELETE CASCADE` ensures addresses are removed with customer deletion.
* **Normalization Analysis:** **Designed to satisfy 3NF.** The composite key `(customer_id, address_type)` functionally determines all non-key address attributes. In relational modeling for e-commerce, capturing city, state, and pincode prefix together preserves the immutable delivery location entered by the customer without introducing update anomalies.

---

### Table 4: `vendor`
* **Purpose:** Stores merchant and vendor profiles operating on the multi-vendor marketplace platform.
* **Source Entity:** Derived from `olist_sellers_dataset.csv` with synthetic business profile augmentation.

#### 3.4.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `vendor_id` | `VARCHAR(32)` | `PRIMARY KEY`, `NOT NULL` | None | Unique vendor identifier (Source: `seller_id`). |
| `vendor_name` | `VARCHAR(100)` | `NOT NULL` | None | Commercial merchant trade name (Synthetic/Augmented). |
| `rating` | `DECIMAL(3, 2)` | `NOT NULL` | `5.00` | Merchant reputation rating score from 1.00 to 5.00 (Derived/Augmented). |
| `gst_number` | `VARCHAR(20)` | `NOT NULL`, `UNIQUE` | None | Standardized Tax Identification / GST Number (Synthetic). |

#### 3.4.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (vendor_id)`
* **Unique Constraints:** `UNIQUE KEY uq_vendor_gst (gst_number)`
* **Check Constraints:**
  - `CONSTRAINT chk_vendor_rating CHECK (rating >= 1.00 AND rating <= 5.00)`
  - `CONSTRAINT chk_vendor_gst_len CHECK (CHAR_LENGTH(gst_number) >= 8)`

#### 3.4.3 Relationships & Normalization
* **Cardinalities:** `vendor` (1) $\rightarrow$ (1..N) `product` (Mandatory: each vendor manages at least one product catalog item).
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** Both `vendor_id` and `gst_number` are candidate keys that uniquely determine all non-key attributes ($vendor\_id \rightarrow \{vendor\_name, rating, gst\_number\}$).

---

### Table 5: `category`
* **Purpose:** Implements a bilingual, self-referencing hierarchical taxonomy for product classification.
* **Source Entity:** Derived from `product_category_name_translation.csv` and `olist_products_dataset.csv`.

#### 3.5.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `category_id` | `INT UNSIGNED` | `PRIMARY KEY`, `AUTO_INCREMENT`, `NOT NULL` | None | Synthetic integer surrogate category identifier. |
| `category_name` | `VARCHAR(100)` | `NOT NULL`, `UNIQUE` | None | Category name in English (Source/Standardized). |
| `parent_category_id`| `INT UNSIGNED` | `NULL` | `NULL` | Recursive FK to `category.category_id`. Null for root categories. |

#### 3.5.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (category_id)`
* **Foreign Key:** `FOREIGN KEY (parent_category_id) REFERENCES category(category_id) ON DELETE RESTRICT ON UPDATE CASCADE`
* **Unique Constraints:** `UNIQUE KEY uq_category_name (category_name)`
* **Check Constraints:**
  - `CONSTRAINT chk_category_no_self_parent CHECK (parent_category_id IS NULL OR parent_category_id <> category_id)`

#### 3.5.3 Relationships & Normalization
* **Cardinalities:**
  - `category` (parent: 0..1) $\rightarrow$ (children: 0..N) `category` (Recursive Adjacency Tree).
  - `category` (1) $\rightarrow$ (0..N) `product`.
* **Referential Action:** `ON DELETE RESTRICT` prevents accidental orphan cascades of entire product classification trees.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** Hierarchical self-referencing structure eliminates redundant category repetition across tables.

---

### Table 6: `product`
* **Purpose:** Central product catalog master containing specifications, catalog pricing, category, and vendor ownership.
* **Source Entity:** Derived from `olist_products_dataset.csv`, `olist_order_items_dataset.csv`, and translation tables.

#### 3.6.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `PRIMARY KEY`, `NOT NULL` | None | Unique product identifier (Source: `product_id`). |
| `product_name` | `VARCHAR(150)` | `NOT NULL` | None | Human-readable product title (Synthetic/Augmented). |
| `description` | `TEXT` | `NULL` | `NULL` | Marketing & technical product overview (Synthetic/Augmented). |
| `price` | `DECIMAL(10, 2)` | `NOT NULL` | None | Base catalog retail price in BRL (Derived from `order_items.price`). |
| `category_id` | `INT UNSIGNED` | `NOT NULL` | None | Foreign key referencing `category.category_id`. |
| `vendor_id` | `VARCHAR(32)` | `NOT NULL` | None | Foreign key referencing `vendor.vendor_id`. |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'Active'` | Catalog lifecycle status (`'Active'`, `'Inactive'`, `'Out of Stock'`, `'Discontinued'`). |

#### 3.6.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (product_id)`
* **Foreign Keys:**
  - `FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE RESTRICT ON UPDATE CASCADE`
  - `FOREIGN KEY (vendor_id) REFERENCES vendor(vendor_id) ON DELETE RESTRICT ON UPDATE CASCADE`
* **Indexes:**
  - `KEY idx_product_category (category_id)`
  - `KEY idx_product_vendor (vendor_id)`
* **Check Constraints:**
  - `CONSTRAINT chk_product_price CHECK (price >= 0.00)`
  - `CONSTRAINT chk_product_status CHECK (status IN ('Active', 'Inactive', 'Out of Stock', 'Discontinued', 'ACTIVE', 'INACTIVE', 'OUT_OF_STOCK', 'DISCONTINUED'))`

#### 3.6.3 Relationships & Normalization
* **Cardinalities:**
  - `category` (1) $\rightarrow$ (N) `product` (Each product belongs to exactly 1 category).
  - `vendor` (1) $\rightarrow$ (N) `product` (Each product belongs to exactly 1 vendor).
  - `product` (1) $\rightarrow$ (0..N) `product_tag`.
  - `product` (1) $\rightarrow$ (1..N) `inventory`.
  - `product` (1) $\rightarrow$ (0..N) `order_item`.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** `product_id` is the primary key and sole determinant for descriptive fields (`product_name`, `description`, `price`), while category and vendor relationships are cleanly isolated as foreign keys.

---

### Table 7: `product_tag`
* **Purpose:** Stores searchable descriptive tags and keyword attributes for products in first normal form (1NF).
* **Source Entity:** Synthetic keyword extraction and category tag augmentation.

#### 3.7.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `NOT NULL` | None | Identifying foreign key referencing `product.product_id`. |
| `tag` | `VARCHAR(50)` | `NOT NULL` | None | Keyword tag (e.g., `'premium'`, `'wireless'`, `'clearance'`). |

#### 3.7.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (product_id, tag)`
* **Foreign Key:** `FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE`
* **Indexes:**
  - `KEY idx_product_tag_name (tag)`
* **Check Constraints:**
  - `CONSTRAINT chk_tag_length CHECK (CHAR_LENGTH(tag) >= 2)`

#### 3.7.3 Relationships & Normalization
* **Cardinalities:** `product` (1) $\rightarrow$ (1..N) `product_tag`.
* **Referential Action:** `ON DELETE CASCADE` removes tags when the product is deleted.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** Multivalued tag attribute is decomposed into an all-key relation `(product_id, tag)` in 1NF, satisfying 3NF/BCNF.

---

### Table 8: `warehouse`
* **Purpose:** Stores geographical logistics hubs, regional fulfillment centers, and overall storage capacity limits.
* **Source Entity:** Synthetic logistics distribution network definition.

#### 3.8.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `warehouse_id` | `INT UNSIGNED` | `PRIMARY KEY`, `AUTO_INCREMENT`, `NOT NULL` | None | Unique warehouse identifier. |
| `location` | `VARCHAR(100)` | `NOT NULL` | None | City and region name of the logistics hub (Synthetic). |
| `capacity` | `INT UNSIGNED` | `NOT NULL` | None | Maximum physical storage unit capacity (Synthetic). |

#### 3.8.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (warehouse_id)`
* **Check Constraints:**
  - `CONSTRAINT chk_warehouse_capacity CHECK (capacity > 0)`

#### 3.8.3 Relationships & Normalization
* **Cardinalities:** `warehouse` (1) $\rightarrow$ (0..N) `inventory`.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** `warehouse_id` is the primary key determining location and capacity ($warehouse\_id \rightarrow \{location, capacity\}$).

---

### Table 9: `inventory`
* **Purpose:** Resolves the M:N relationship between Products and Warehouses, tracking localized stock levels and replenishment triggers.
* **Source Entity:** Synthetic stock generation parameterized by product popularity and category.

#### 3.9.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `VARCHAR(32)` | `NOT NULL` | None | Foreign key referencing `product.product_id`. |
| `warehouse_id` | `INT UNSIGNED` | `NOT NULL` | None | Foreign key referencing `warehouse.warehouse_id`. |
| `stock_quantity` | `INT` | `NOT NULL` | `0` | Quantity currently available on hand (Synthetic). |
| `reorder_level` | `INT` | `NOT NULL` | `10` | Minimum threshold triggering replenishment orders (Synthetic). |
| `last_updated` | `DATETIME` | `NOT NULL` | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Timestamp of last stock modification. |

#### 3.9.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (product_id, warehouse_id)`
* **Foreign Keys:**
  - `FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE`
  - `FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id) ON DELETE RESTRICT ON UPDATE CASCADE`
* **Indexes:**
  - `KEY idx_inventory_warehouse (warehouse_id)`
* **Check Constraints:**
  - `CONSTRAINT chk_inventory_stock CHECK (stock_quantity >= 0)`
  - `CONSTRAINT chk_inventory_reorder CHECK (reorder_level >= 0)`

#### 3.9.3 Relationships & Normalization
* **Cardinalities:** `product` (M) $\leftrightarrow$ (N) `warehouse` resolved via `inventory`.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** The composite primary key `(product_id, warehouse_id)` determines `stock_quantity` and `reorder_level` with zero partial key dependencies.

---

### Table 10: `orders`
* **Purpose:** Records high-level customer order transactions and lifecycle statuses.
* **Source Entity:** Derived from `olist_orders_dataset.csv` with customer linkage mapped to `customer_unique_id`.

#### 3.10.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `PRIMARY KEY`, `NOT NULL` | None | Unique order transaction hash (Source: `order_id`). |
| `order_date` | `DATETIME` | `NOT NULL` | `CURRENT_TIMESTAMP` | Timestamp of order placement (Source: `order_purchase_timestamp`). |
| `customer_id` | `VARCHAR(32)` | `NOT NULL` | None | Foreign key referencing `customer.customer_id`. |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'created'` | Order lifecycle status (`'delivered'`, `'shipped'`, `'canceled'`, etc.). |

#### 3.10.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (order_id)`
* **Foreign Key:** `FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE`
* **Indexes:**
  - `KEY idx_orders_customer (customer_id)`
  - `KEY idx_orders_date (order_date)`
  - `KEY idx_orders_status (status)`
* **Check Constraints:**
  - `CONSTRAINT chk_orders_status CHECK (status IN ('delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved'))`

#### 3.10.3 Relationships & Normalization
* **Cardinalities:**
  - `customer` (1) $\rightarrow$ (N) `orders`.
  - `orders` (1) $\rightarrow$ (1..N) `order_item`.
  - `orders` (1) $\rightarrow$ (1..N) `payment` (Identifying relationship).
* **Referential Action:** `ON DELETE RESTRICT` prevents accidental deletion of customer records that have historical transaction records.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** `order_id` is the primary key determining order timestamp, customer reference, and status ($order\_id \rightarrow \{order\_date, customer\_id, status\}$).

---

### Table 11: `order_item`
* **Purpose:** Resolves the M:N relationship between Orders and Products, capturing purchased quantities and historical transaction pricing.
* **Source Entity:** Derived from `olist_order_items_dataset.csv` aggregated by `(order_id, product_id)`.

#### 3.11.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `NOT NULL` | None | Foreign key referencing `orders.order_id`. |
| `product_id` | `VARCHAR(32)` | `NOT NULL` | None | Foreign key referencing `product.product_id`. |
| `quantity` | `INT` | `NOT NULL` | `1` | Number of units purchased (Reconstructed target attribute). |
| `price_at_purchase` | `DECIMAL(10, 2)` | `NOT NULL` | None | Actual unit price captured at time of sale in BRL (Source: `price`). |

#### 3.11.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (order_id, product_id)`
* **Foreign Keys:**
  - `FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE`
  - `FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE RESTRICT ON UPDATE CASCADE`
* **Indexes:**
  - `KEY idx_order_item_product (product_id)`
* **Check Constraints:**
  - `CONSTRAINT chk_order_item_quantity CHECK (quantity > 0)`
  - `CONSTRAINT chk_order_item_price CHECK (price_at_purchase >= 0.00)`

#### 3.11.3 Relationships & Normalization
* **Cardinalities:** `orders` (M) $\leftrightarrow$ (N) `product` resolved via `order_item`.
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** The composite key `(order_id, product_id)` determines `quantity` and `price_at_purchase`. `price_at_purchase` records historical transactional pricing at the time of purchase and is not partially dependent on `product_id` alone.

---

### Table 12: `payment` (Weak / Dependent Entity)
* **Purpose:** Records discrete financial payment transactions, split payments, voucher redemptions, and gateway settlement statuses.
* **Relational Nature:** **Weak Entity.** A payment record has no independent existence outside the context of its parent order. It is identified through the composite primary key `(order_id, payment_id)`.
* **Source Entity:** Derived from `olist_order_payments_dataset.csv` with synthetic status and reference augmentation.

#### 3.12.1 Column Definitions
| Column Name | MySQL 8.4 Data Type | Constraints & Modifiers | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `order_id` | `VARCHAR(32)` | `NOT NULL` | None | Identifying foreign key referencing `orders.order_id`. |
| `payment_id` | `INT UNSIGNED` | `NOT NULL` | None | Partial key / sequence discriminator within the order (Source: `payment_sequential`). |
| `amount` | `DECIMAL(10, 2)` | `NOT NULL` | None | Transaction payment amount in BRL (Source: `payment_value`). |
| `mode` | `VARCHAR(20)` | `NOT NULL` | None | Payment instrument method (Source: `payment_type`). |
| `status` | `VARCHAR(20)` | `NOT NULL` | `'Success'` | Transaction settlement status (`'Success'`, `'Pending'`, `'Failed'`, `'Refunded'`). |
| `payment_date` | `DATETIME` | `NOT NULL` | `CURRENT_TIMESTAMP` | Timestamp of payment processing (Derived/Augmented). |
| `transaction_reference` | `VARCHAR(64)` | `NOT NULL`, `UNIQUE` | None | Unique gateway transaction authorization reference (Synthetic). |

#### 3.12.2 Integrity Constraints & Indexes
* **Primary Key:** `PRIMARY KEY (order_id, payment_id)`
* **Foreign Key:** `FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE`
* **Unique Constraints:** `UNIQUE KEY uq_payment_txn_ref (transaction_reference)`
* **Indexes:**
  - `KEY idx_payment_order (order_id)`
  - `KEY idx_payment_mode (mode)`
  - `KEY idx_payment_status (status)`
* **Check Constraints:**
  - `CONSTRAINT chk_payment_amount CHECK (amount >= 0.00)`
  - `CONSTRAINT chk_payment_mode CHECK (mode IN ('credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined'))`
  - `CONSTRAINT chk_payment_status CHECK (status IN ('Success', 'Pending', 'Failed', 'Refunded'))`

#### 3.12.3 Relationships & Normalization
* **Cardinalities:** `orders` (1) $\rightarrow$ (1..N) `payment` (Identifying 1:N relationship). An order can be settled via multiple payments (e.g. split across gift vouchers and credit cards).
* **Referential Action:** `ON DELETE CASCADE` automatically purges associated payment records when an order is deleted.
* **Weak Entity Justification (Viva Defense):**  
  > *"Payment is an identifying weak entity because a payment does not exist independently of an Order. Its primary key `(order_id, payment_id)` incorporates the primary key of `orders`, establishing an identifying foreign-key relationship and total existence dependency on `orders`."*
* **Normalization Analysis:** **Designed to satisfy 3NF, with BCNF satisfied where applicable.** The composite key `(order_id, payment_id)` determines all payment attributes (`amount`, `mode`, `status`, `payment_date`, `transaction_reference`). The secondary candidate key `transaction_reference` is also a valid determinant.

---

## 4. Comprehensive Source-to-Target Data Lineage & Transformation Mapping

The following matrix documents the exact origin of every column in the 12-table canonical schema, distinguishing strictly between **SOURCE (Olist CSVs)** and **SYNTHETIC / AUGMENTED** data:

| Target Table | Target Column | Data Origin Classification | Source CSV File & Column | Transformation / Generation Logic |
| :--- | :--- | :--- | :--- | :--- |
| **`customer`** | `customer_id` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_unique_id` | Extract distinct 32-character hex hashes (96,096 unique real customers). |
| **`customer`** | `name` | **SYNTHETIC** | None (Empirically Absent) | Deterministic realistic Portuguese/English full names generated per `customer_id`. |
| **`customer`** | `email` | **SYNTHETIC** | None (Empirically Absent) | Unique standardized email generated: `<name_slug>.<hash_prefix>@example.com`. |
| **`customer`** | `join_date` | **DERIVED / SOURCE** | `olist_orders_dataset.csv` $\rightarrow$ `order_purchase_timestamp` | Earliest purchase timestamp per customer, or `2016-01-01` for pre-registered buyers. |
| **`customer_phone`** | `customer_id` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_unique_id` | Foreign key referencing `customer.customer_id`. |
| **`customer_phone`** | `phone_number` | **SYNTHETIC** | None (Empirically Absent) | E.164 Brazilian mobile/landline numbers (e.g., `+5511987654321`, 1-2 per customer). |
| **`customer_phone`** | `phone_type` | **SYNTHETIC** | None (Domain Constant) | Phone type classification (`'Mobile'`, `'Home'`, `'Work'`, `'Office'`, `'Other'`). |
| **`address`** | `customer_id` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_unique_id` | Foreign key referencing `customer.customer_id`. |
| **`address`** | `address_type` | **SYNTHETIC** | None (Domain Constant) | Primary address assigned as `'Shipping'`; secondary repeat addresses as `'Billing'` / `'Home'`. |
| **`address`** | `street` | **SYNTHETIC** | None (Empirically Absent) | Realistic Brazilian street name and building number (e.g., `'Av. Paulista, 1000'`). |
| **`address`** | `city` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_city` | Direct import with title casing and trimmed whitespace. |
| **`address`** | `state` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_state` | Direct import of 2-character Brazilian state code. |
| **`address`** | `pincode` | **SOURCE** | `olist_customers_dataset.csv` $\rightarrow$ `customer_zip_code_prefix` | Formatted 5-digit postal-code prefix (representing the first 5 digits of the Brazilian CEP). |
| **`address`** | `is_default` | **SYNTHETIC** | None (Business Rule) | Boolean default flag (1 for primary shipping address, 0 otherwise). |
| **`vendor`** | `vendor_id` | **SOURCE** | `olist_sellers_dataset.csv` $\rightarrow$ `seller_id` | Direct import of 32-character seller MD5 hash (3,095 sellers). |
| **`vendor`** | `vendor_name` | **SYNTHETIC** | None (Empirically Absent) | Realistic business trade name (e.g., `'EletroTech Comércio'`, `'Paulista Imports'`). |
| **`vendor`** | `rating` | **DERIVED / AUGMENTED**| `olist_order_reviews_dataset.csv` $\rightarrow$ `review_score` | Mean review score of fulfilled order items; default `5.00` for unreviewed vendors. |
| **`vendor`** | `gst_number` | **SYNTHETIC** | None (Empirically Absent) | Standardized 15-character alphanumeric Tax/GST/CNPJ number. |
| **`category`** | `category_id` | **SYNTHETIC SURROGATE**| None (Surrogate Key) | Auto-incrementing integer identifier starting at 1. |
| **`category`** | `category_name` | **SOURCE / STANDARDIZED**| `product_category_name_translation.csv` $\rightarrow$ `product_category_name_english` | Cleaned English category names (BOM stripped, `pc_gamer` & missing translations resolved). |
| **`category`** | `parent_category_id`| **SYNTHETIC HIERARCHY** | None (Domain Taxonomy) | Top-level cluster mapping (e.g., Electronics, Home & Living, Fashion, Sports, etc.). |
| **`product`** | `product_id` | **SOURCE** | `olist_products_dataset.csv` $\rightarrow$ `product_id` | Direct import of 32-character product MD5 hash (32,951 products). |
| **`product`** | `product_name` | **SYNTHETIC** | None (Empirically Absent) | Structured product title derived from English category + short ID (e.g. `'Pro Audio Headphones 3a07'`). |
| **`product`** | `description` | **SYNTHETIC** | None (Empirically Absent) | Rich product overview text generated based on category taxonomy. |
| **`product`** | `price` | **DERIVED / SOURCE** | `olist_order_items_dataset.csv` $\rightarrow$ `price` | Median / modal unit sale price from historical order items. |
| **`product`** | `category_id` | **SOURCE MAPPED** | `olist_products_dataset.csv` $\rightarrow$ `product_category_name` | Mapped foreign key to dynamically generated `category.category_id` (fallback dynamically generated `'General & Miscellaneous'` ID for 610 nulls). |
| **`product`** | `vendor_id` | **SOURCE MAPPED** | `olist_order_items_dataset.csv` $\rightarrow$ `seller_id` | Assigned via 3-tier rule: 1. Highest sales volume, 2. If tied, earliest order date, 3. If still tied, minimum `seller_id` (resolves 1,225 multi-seller products to 1 vendor). |
| **`product`** | `status` | **SYNTHETIC** | None (Catalog State) | Product lifecycle state (`'Active'`, `'Inactive'`, `'Out of Stock'`, `'Discontinued'`). |
| **`product_tag`** | `product_id` | **SOURCE** | `olist_products_dataset.csv` $\rightarrow$ `product_id` | Foreign key referencing `product.product_id`. |
| **`product_tag`** | `tag` | **SYNTHETIC** | None (Empirically Absent) | 2 to 4 keyword tags per product (e.g. `'electronics'`, `'bestseller'`, `'deals'`). |
| **`warehouse`** | `warehouse_id` | **SYNTHETIC SURROGATE**| None (Surrogate Key) | Auto-incrementing integer (e.g., 1 to 10 for major Brazilian logistics hubs). |
| **`warehouse`** | `location` | **SYNTHETIC** | None (Empirically Absent) | Major distribution hubs (e.g., `'São Paulo - Central Hub'`, `'Rio de Janeiro - DC'`). |
| **`warehouse`** | `capacity` | **SYNTHETIC** | None (Empirically Absent) | Storage capacity in units (e.g., 100,000 to 1,000,000). |
| **`inventory`** | `product_id` | **SOURCE** | `olist_products_dataset.csv` $\rightarrow$ `product_id` | Foreign key referencing `product.product_id`. |
| **`inventory`** | `warehouse_id` | **SYNTHETIC MAPPED** | `warehouse.warehouse_id` | Distributed across 1 to 3 regional warehouses based on vendor/location proximity. |
| **`inventory`** | `stock_quantity` | **SYNTHETIC** | None (Empirically Absent) | Realistic stock levels (e.g., 20 to 500 units per product-warehouse pair). |
| **`inventory`** | `reorder_level` | **SYNTHETIC** | None (Empirically Absent) | Reorder threshold (e.g., 10 to 50 units). |
| **`inventory`** | `last_updated` | **DERIVED / AUDIT** | System timestamp | Timestamp tracking stock modification (`CURRENT_TIMESTAMP`). |
| **`orders`** | `order_id` | **SOURCE** | `olist_orders_dataset.csv` $\rightarrow$ `order_id` | Direct import of 32-character order MD5 hash (99,441 orders). |
| **`orders`** | `order_date` | **SOURCE** | `olist_orders_dataset.csv` $\rightarrow$ `order_purchase_timestamp` | Direct timestamp conversion (`YYYY-MM-DD HH:MM:SS`). |
| **`orders`** | `customer_id` | **SOURCE MAPPED** | `olist_orders_dataset.customer_id` $\rightarrow$ `customers.customer_unique_id` | Mapped to true `customer.customer_id` (resolving order-level tokens). |
| **`orders`** | `status` | **SOURCE** | `olist_orders_dataset.csv` $\rightarrow$ `order_status` | Direct import of lifecycle status string (delivered, shipped, etc.). |
| **`order_item`** | `order_id` | **SOURCE** | `olist_order_items_dataset.csv` $\rightarrow$ `order_id` | Foreign key referencing `orders.order_id`. |
| **`order_item`** | `product_id` | **SOURCE** | `olist_order_items_dataset.csv` $\rightarrow$ `product_id` | Foreign key referencing `product.product_id`. |
| **`order_item`** | `quantity` | **RECONSTRUCTED TARGET ATTRIBUTE**| `olist_order_items_dataset.csv` $\rightarrow$ Repeated rows | Derived target-model attribute reconstructed during ETL from repeated product occurrences within an order, subject to the canonical model's single-vendor-per-product constraint. |
| **`order_item`** | `price_at_purchase`| **SOURCE** | `olist_order_items_dataset.csv` $\rightarrow$ `price` | Unit price captured at purchase in BRL. |
| **`payment`** | `order_id` | **SOURCE** | `olist_order_payments_dataset.csv` $\rightarrow$ `order_id` | Identifying foreign key referencing `orders.order_id`. |
| **`payment`** | `payment_id` | **SOURCE (DISCRIMINATOR)**| `olist_order_payments_dataset.csv` $\rightarrow$ `payment_sequential` | Partial key / sequence number within the order (`1, 2, 3...`). |
| **`payment`** | `amount` | **SOURCE** | `olist_order_payments_dataset.csv` $\rightarrow$ `payment_value` | Transaction amount in BRL. |
| **`payment`** | `mode` | **SOURCE** | `olist_order_payments_dataset.csv` $\rightarrow$ `payment_type` | Payment type string (`credit_card`, `boleto`, `voucher`, `debit_card`). |
| **`payment`** | `status` | **SYNTHETIC / DERIVED** | Derived from order status & amount | `'Success'` for delivered/shipped/settled orders; `'Pending'`/`'Refunded'` for canceled/unpaid. |
| **`payment`** | `payment_date` | **DERIVED / SOURCE** | `olist_orders_dataset.csv` $\rightarrow$ `order_purchase_timestamp` | Payment execution timestamp. |
| **`payment`** | `transaction_reference`| **SYNTHETIC** | None (Empirically Absent) | Formatted alphanumeric gateway settlement reference code (e.g. `TXN-2018-099440-01`). |

---

## 5. 12-Table Schema, 13-Stage Data-Loading Process & Dependency Order

To strictly enforce foreign key referential integrity constraints without disabling `FOREIGN_KEY_CHECKS`, the database populates the **12 canonical tables across 13 topological stages** (Table 5 `category` is populated across Stage 1 and Stage 2 to establish its hierarchical parent-child relationships):

```
                  ┌────────────────────────┐
                  │ Stage 1: category(Root)│
                  └───────────┬────────────┘
                              │
                              ▼
                  ┌────────────────────────┐
                  │Stage 2:category(Child) │
                  └───────────┬────────────┘
                              │
      ┌───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
┌───────────┐           ┌───────────┐           ┌───────────┐
│Stage 3:   │           │ Stage 4:  │           │Stage 5:   │
│customer   │           │ vendor    │           │warehouse  │
└─────┬─────┘           └─────┬─────┘           └─────┬─────┘
      │                       │                       │
      ├──────────────┐        │                       │
      ▼              ▼        ▼                       │
┌───────────┐  ┌──────────┐ ┌───────────┐             │
│Stage 6:   │  │Stage 7:  │ │Stage 8:   │             │
│cust_phone │  │address   │ │product    │             │
└───────────┘  └──────────┘ └─────┬─────┘             │
                                  │                   │
                     ┌────────────┼────────────┐      │
                     ▼            ▼            ▼      ▼
               ┌───────────┐┌───────────┐┌───────────────┐
               │Stage 9:   ││Stage 10:  ││ Stage 11:     │
               │product_tag││orders     ││ inventory     │
               └───────────┘└─────┬─────┘└───────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
               ┌───────────┐             ┌───────────┐
               │Stage 12:  │             │Stage 13:  │
               │order_item │             │payment    │
               └───────────┘             └───────────┘
```

### 13-Stage Topological Execution Sequence:
* **Stage 1 (`category` - Root Level):** Insert parent root categories (`parent_category_id IS NULL`), including the dynamic creation of `'General & Miscellaneous'` (whose dynamically generated `category_id` will serve as the fallback for unclassified products).
* **Stage 2 (`category` - Subcategory Level):** Insert child subcategories referencing parent `category_id`s.
* **Stage 3 (`customer`):** Insert normalized master customers (keyed by `customer_unique_id`).
* **Stage 4 (`vendor`):** Insert master merchant vendors (keyed by `seller_id`).
* **Stage 5 (`warehouse`):** Insert logistics fulfillment centers.
* **Stage 6 (`customer_phone`):** Insert customer phone records referencing `customer(customer_id)`.
* **Stage 7 (`address`):** Insert customer addresses referencing `customer(customer_id)`.
* **Stage 8 (`product`):** Insert product catalog master referencing `category(category_id)` and `vendor(vendor_id)`.
* **Stage 9 (`product_tag`):** Insert keyword tags referencing `product(product_id)`.
* **Stage 10 (`orders`):** Insert order headers referencing `customer(customer_id)`.
* **Stage 11 (`inventory`):** Insert inventory records referencing `product(product_id)` and `warehouse(warehouse_id)`.
* **Stage 12 (`order_item`):** Insert aggregated line items referencing `orders(order_id)` and `product(product_id)`.
* **Stage 13 (`payment`):** Insert payment weak entity transactions referencing `orders(order_id)` with composite key `(order_id, payment_id)`.

---

## 6. Potential Data-Integrity Risks & Mitigation Strategies

| Data Integrity Risk | Source Occurrence in Olist | Risk Description & Impact | Concrete ETL Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Order Items Multi-Row Duplication** | 7,088 instances of identical `(order_id, product_id)` pairs | Raw order items contain multi-unit purchases as separate rows with incrementing `order_item_id`. Inserting raw rows directly violates `PRIMARY KEY (order_id, product_id)`. | **Target Quantity Reconstruction:** Reconstruct `quantity = COUNT(*)` per `(order_id, product_id)`, setting `price_at_purchase = MIN(price)` without pretending raw Olist supplied a native quantity column. |
| **Multi-Seller Products Violation** | 1,225 products sold by $>1$ seller | Canonical model requires: *Product belongs to exactly one Vendor*. Multiple vendor IDs cannot be assigned to one `product_id`. | **Vendor Resolution:** For multi-seller products, assign the primary vendor using the 3-tier rule: 1. Highest historical sales volume, 2. If tied, earliest order date, 3. If still tied, minimum `seller_id`. |
| **Customer Token vs Real Customer Key** | `customer_id` is an order token; `customer_unique_id` is the real customer | If `customer_id` is loaded directly as `customer.customer_id`, 2,997 repeat buyers are treated as isolated single-purchase accounts. | **Identity Unification:** Map `customer.customer_id = customer_unique_id`. In `orders`, map `orders.customer_id = customer_unique_id`. |
| **Category UTF-8 BOM & Unmapped Slugs** | BOM on column header; 2 missing categories (`pc_gamer`, `portateis_cozinha...`) | Unmapped foreign keys will cause `FOREIGN KEY constraint fail` during product loading. | **ETL Sanitization:** Read translation file using `utf-8-sig`. Add explicit records for `pc_gamer` ('PC Gaming') and missing slugs to `category`. |
| **Null Product Categories & Dynamic Fallback** | 610 products have `product_category_name IS NULL` | Inserting NULL into `product.category_id` (`NOT NULL` FK) will abort execution. Hard-coding a static ID creates sequence collision risks. | **Dynamic Fallback:** Dynamically insert root category `'General & Miscellaneous'` during Stage 1, retrieve its generated `category_id`, and map all 610 unclassified products to this dynamic ID. |
| **Orders Without Order Items** | 775 orders have 0 line items (603 unavailable, 164 canceled, 5 created, etc.) | Orders exist in `orders` table without matching children in `order_item`. | **Business Rule:** Maintain `orders` records with appropriate status (`canceled`/`unavailable`). `order_item` participation is naturally $(0..N)$ for aborted orders. |
| **Orders Without Payments** | Exactly 1 delivered order (`bfbd0f9bdef84302105ad712db648a6c`) has no payment record | Violates total participation assumption if payments are required for every delivered order. | **Synthetic Reconciliation:** Generate a synthetic payment record under `(order_id, 1)` matching the order items total value with payment mode `'not_defined'`. |
| **Omission of Reviews & Shipments** | Raw Olist contains reviews & delivery milestones | Reviews and logistics tracking are omitted from the canonical 12 tables per assignment scope. | **Scope Isolation:** Reviews are utilized strictly to derive historical merchant aggregate `vendor.rating`; no unprescribed tables are created. |

---

## 7. Post-Loading Validation & Verification Test Plan

After executing the ETL pipeline into MySQL 8.4, the following automated assertion checks must be executed to certify 100% data integrity:

### 7.1 Row Count & Completeness Verification
```sql
-- 1. Verify exact expected table row counts
SELECT 'customer' AS tbl, COUNT(*) AS cnt FROM customer
UNION ALL SELECT 'customer_phone', COUNT(*) FROM customer_phone
UNION ALL SELECT 'address', COUNT(*) FROM address
UNION ALL SELECT 'vendor', COUNT(*) FROM vendor
UNION ALL SELECT 'category', COUNT(*) FROM category
UNION ALL SELECT 'product', COUNT(*) FROM product
UNION ALL SELECT 'product_tag', COUNT(*) FROM product_tag
UNION ALL SELECT 'warehouse', COUNT(*) FROM warehouse
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_item', COUNT(*) FROM order_item
UNION ALL SELECT 'payment', COUNT(*) FROM payment;
```

### 7.2 Referential Integrity & Orphan Record Assertions
```sql
-- 2. Assert zero orphan customer_phone records
SELECT COUNT(*) AS orphan_phones 
FROM customer_phone cp 
LEFT JOIN customer c ON cp.customer_id = c.customer_id 
WHERE c.customer_id IS NULL;

-- 3. Assert zero orphan address records
SELECT COUNT(*) AS orphan_addresses 
FROM address a 
LEFT JOIN customer c ON a.customer_id = c.customer_id 
WHERE c.customer_id IS NULL;

-- 4. Assert zero orphan products (Category & Vendor FK validation)
SELECT COUNT(*) AS orphan_products 
FROM product p 
LEFT JOIN category c ON p.category_id = c.category_id 
LEFT JOIN vendor v ON p.vendor_id = v.vendor_id 
WHERE c.category_id IS NULL OR v.vendor_id IS NULL;

-- 5. Assert zero orphan order items (Orders & Products FK validation)
SELECT COUNT(*) AS orphan_order_items 
FROM order_item oi 
LEFT JOIN orders o ON oi.order_id = o.order_id 
LEFT JOIN product p ON oi.product_id = p.product_id 
WHERE o.order_id IS NULL OR p.product_id IS NULL;

-- 6. Assert zero orphan payments (Weak entity identifying FK validation)
SELECT COUNT(*) AS orphan_payments 
FROM payment py 
LEFT JOIN orders o ON py.order_id = o.order_id 
WHERE o.order_id IS NULL;

-- 7. Assert zero orphan inventory records (Product & Warehouse FK validation)
SELECT COUNT(*) AS orphan_inventory 
FROM inventory inv 
LEFT JOIN product p ON inv.product_id = p.product_id 
LEFT JOIN warehouse w ON inv.warehouse_id = w.warehouse_id 
WHERE p.product_id IS NULL OR w.warehouse_id IS NULL;
```

### 7.3 Business Logic & Constraint Assertions
```sql
-- 8. Assert all vendor ratings are within [1.00, 5.00]
SELECT COUNT(*) AS invalid_ratings FROM vendor WHERE rating < 1.00 OR rating > 5.00;

-- 9. Assert all order item quantities are positive
SELECT COUNT(*) AS invalid_quantities FROM order_item WHERE quantity <= 0;

-- 10. Assert all product and order item prices are non-negative
SELECT COUNT(*) AS invalid_product_prices FROM product WHERE price < 0.00;
SELECT COUNT(*) AS invalid_purchase_prices FROM order_item WHERE price_at_purchase < 0.00;

-- 11. Assert all payment amounts are non-negative
SELECT COUNT(*) AS invalid_payment_amounts FROM payment WHERE amount < 0.00;

-- 12. Assert all inventory stock and reorder levels are non-negative
SELECT COUNT(*) AS invalid_stock FROM inventory WHERE stock_quantity < 0 OR reorder_level < 0;

-- 13. Assert category hierarchy contains no self-referencing loops
SELECT COUNT(*) AS invalid_category_loops FROM category WHERE parent_category_id = category_id;
```

---

*Specification successfully updated and finalized. All 12 tables, weak entity relationships, honest data lineages, dynamic category handling, and 3NF normalization standards are fully documented.*
