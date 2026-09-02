"""
Static Schema Validation Script for Multi-Vendor E-Commerce DBMS
Validates SQL files against the canonical 12-table ER architecture.
"""
import re
import os
import sys

def validate_sql_files(database_dir):
    print("=================================================================")
    print("STATIC SCHEMA VALIDATION SUITE: MULTI-VENDOR E-COMMERCE DBMS")
    print("=================================================================")
    
    files = [
        "01_create_database.sql",
        "02_create_tables.sql",
        "03_constraints.sql",
        "schema.sql",
        "setup_database.sql",
        "04_validation_queries.sql"
    ]
    
    for f in files:
        path = os.path.join(database_dir, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  [OK] Found SQL script: {f} ({size} bytes)")
        else:
            print(f"  [FAIL] Missing script: {f}")
            return False

    # Read unified schema.sql, setup_database.sql, and component scripts
    with open(os.path.join(database_dir, "schema.sql"), "r", encoding="utf-8") as sf:
        schema_sql = sf.read()

    with open(os.path.join(database_dir, "setup_database.sql"), "r", encoding="utf-8") as sdbf:
        setup_db_sql = sdbf.read()

    with open(os.path.join(database_dir, "02_create_tables.sql"), "r", encoding="utf-8") as tf:
        tables_sql = tf.read()

    with open(os.path.join(database_dir, "03_constraints.sql"), "r", encoding="utf-8") as cf:
        constraints_sql = cf.read()

    expected_tables = [
        "customer", "vendor", "category", "warehouse", "product",
        "customer_phone", "address", "product_tag", "inventory",
        "orders", "order_item", "payment"
    ]
    
    print("\n--- 1. Validating Table Entities ---")
    created_tables = re.findall(r"CREATE\s+TABLE\s+[`]?([a-zA-Z0-9_]+)[`]?", tables_sql, re.IGNORECASE)
    print(f"Discovered {len(created_tables)} tables in 02_create_tables.sql:")
    for t in created_tables:
        print(f"  - {t}")
    
    if sorted(created_tables) != sorted(expected_tables):
        print(f"  [FAIL] Created tables do not match expected 12 canonical tables.")
        print(f"  Missing: {set(expected_tables) - set(created_tables)}")
        print(f"  Unexpected: {set(created_tables) - set(expected_tables)}")
        return False
    print("  [PASS] Exactly 12 canonical tables defined with zero unauthorized entities.")

    print("\n--- 2. Validating Primary Keys & Composite Keys ---")
    expected_pks = {
        "customer": ["customer_id"],
        "vendor": ["vendor_id"],
        "category": ["category_id"],
        "warehouse": ["warehouse_id"],
        "product": ["product_id"],
        "customer_phone": ["customer_id", "phone_number"],
        "address": ["customer_id", "address_type"],
        "product_tag": ["product_id", "tag"],
        "inventory": ["product_id", "warehouse_id"],
        "orders": ["order_id"],
        "order_item": ["order_id", "product_id"],
        "payment": ["order_id", "payment_id"]
    }
    
    for tbl, cols in expected_pks.items():
        pattern = rf"CREATE\s+TABLE\s+[`]?{tbl}[`]?\s*\((.*?)\)\s*ENGINE"
        match = re.search(pattern, tables_sql, re.DOTALL | re.IGNORECASE)
        if match:
            tbl_def = match.group(1)
            pk_match = re.search(r"PRIMARY\s+KEY\s*\((.*?)\)", tbl_def, re.IGNORECASE)
            if pk_match:
                pk_cols = [c.strip().strip("`") for c in pk_match.group(1).split(",")]
                if pk_cols == cols:
                    is_comp = "Composite PK" if len(cols) > 1 else "Single PK"
                    print(f"  [PASS] Table '{tbl}': PRIMARY KEY ({', '.join(cols)}) [{is_comp}]")
                else:
                    print(f"  [FAIL] Table '{tbl}': Expected PK {cols}, got {pk_cols}")
                    return False
            else:
                print(f"  [FAIL] Table '{tbl}': No PRIMARY KEY found in definition.")
                return False
        else:
            print(f"  [FAIL] Table '{tbl}': Could not parse table definition.")
            return False

    print("\n--- 3. Validating Foreign Key Relationships ---")
    expected_fks = [
        ("category", "parent_category_id", "category", "category_id"),
        ("product", "category_id", "category", "category_id"),
        ("product", "vendor_id", "vendor", "vendor_id"),
        ("customer_phone", "customer_id", "customer", "customer_id"),
        ("address", "customer_id", "customer", "customer_id"),
        ("product_tag", "product_id", "product", "product_id"),
        ("inventory", "product_id", "product", "product_id"),
        ("inventory", "warehouse_id", "warehouse", "warehouse_id"),
        ("orders", "customer_id", "customer", "customer_id"),
        ("order_item", "order_id", "orders", "order_id"),
        ("order_item", "product_id", "product", "product_id"),
        ("payment", "order_id", "orders", "order_id")
    ]
    
    for c_tbl, c_col, p_tbl, p_col in expected_fks:
        fk_pat = rf"FOREIGN\s+KEY\s*\([`]?{c_col}[`]?\)\s*REFERENCES\s*[`]?{p_tbl}[`]?\s*\([`]?{p_col}[`]?\)"
        if (re.search(fk_pat, constraints_sql, re.IGNORECASE) or re.search(fk_pat, schema_sql, re.IGNORECASE)) and re.search(fk_pat, setup_db_sql, re.IGNORECASE):
            print(f"  [PASS] FK: {c_tbl}({c_col}) -> {p_tbl}({p_col})")
        else:
            print(f"  [FAIL] Missing FK: {c_tbl}({c_col}) -> {p_tbl}({p_col})")
            return False

    print("\n--- 4. Validating UNIQUE Constraints ---")
    expected_uniques = [
        ("customer", "email"),
        ("vendor", "gst_number"),
        ("category", "category_name"),
        ("payment", "transaction_reference")
    ]
    for tbl, col in expected_uniques:
        uq_pat = rf"UNIQUE\s*\([`]?{col}[`]?\)"
        if (re.search(uq_pat, constraints_sql, re.IGNORECASE) or re.search(uq_pat, schema_sql, re.IGNORECASE)) and re.search(uq_pat, setup_db_sql, re.IGNORECASE):
            print(f"  [PASS] UNIQUE constraint on {tbl}.{col}")
        else:
            print(f"  [FAIL] Missing UNIQUE constraint on {tbl}.{col}")
            return False

    print("\n--- 5. Validating CHECK Constraints ---")
    check_constraints = [
        "chk_customer_email_format",
        "chk_customer_join_date",
        "chk_vendor_rating",
        "chk_vendor_gst_len",
        "chk_warehouse_capacity",
        "chk_product_price",
        "chk_product_status",
        "chk_phone_number_length",
        "chk_phone_type",
        "chk_address_type",
        "chk_address_state_len",
        "chk_tag_length",
        "chk_inventory_stock",
        "chk_inventory_reorder",
        "chk_orders_status",
        "chk_order_item_quantity",
        "chk_order_item_price",
        "chk_payment_amount",
        "chk_payment_mode",
        "chk_payment_status"
    ]
    for chk in check_constraints:
        if chk in constraints_sql and chk in schema_sql and chk in setup_db_sql:
            print(f"  [PASS] CHECK constraint verified: {chk}")
        else:
            print(f"  [FAIL] Missing CHECK constraint: {chk}")
            return False

    print("\n=================================================================")
    print("ALL STATIC CHECKS PASSED: 100% RELATIONAL & DOMAIN INTEGRITY")
    print("=================================================================")
    return True

if __name__ == "__main__":
    db_dir = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\katwa\OneDrive\Desktop\multi-vendor-ecommerce-dbms\database"
    success = validate_sql_files(db_dir)
    sys.exit(0 if success else 1)
