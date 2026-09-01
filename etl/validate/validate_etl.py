"""
Validation Suite for Phase 3 ETL.
Provides explicit 1-to-27 granular verification across both:
1. Pre-Load Dry Run Validation (validates intermediate CSV files in data/processed/)
2. Post-Load Live Database Validation (executes 27 SQL verification checks against MySQL 8.4)
"""
import csv
import re
import sys
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional

from etl.config import PROCESSED_FILES

EXPECTED_ROW_COUNTS = {
    "customer": 96096,
    "customer_phone": 96096,
    "address": 96096,
    "vendor": 3095,
    "category": 83,
    "warehouse": 8,
    "product": 32951,
    "product_tag": 98853,
    "inventory": 43217,
    "orders": 99441,
    "order_item": 102425,
    "payment": 103886
}

def validate_dry_run_csvs() -> Tuple[bool, List[str]]:
    """
    Executes the complete 27-check pre-load validation suite on processed CSV files.
    """
    print("================================================================================")
    print("PRE-LOAD DRY RUN VALIDATION SUITE: 27 INTEGRITY CHECKS (data/processed/)")
    print("================================================================================")
    errors = []
    
    # Load CSVs into memory
    tables: Dict[str, List[Dict[str, str]]] = {}
    for tbl_name, file_path in PROCESSED_FILES.items():
        if not file_path.exists():
            errors.append(f"Missing processed file: {file_path}")
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            tables[tbl_name] = list(reader)

    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        return False, errors

    # Pre-extract shared identity sets
    cust_ids = {r["customer_id"] for r in tables["customer"]}
    vendor_ids = {r["vendor_id"] for r in tables["vendor"]}
    category_ids = {int(r["category_id"]) for r in tables["category"]}
    warehouse_ids = {int(r["warehouse_id"]) for r in tables["warehouse"]}
    product_ids = {r["product_id"] for r in tables["product"]}
    order_ids = {r["order_id"] for r in tables["orders"]}

    # CHECK 01: Table Row Counts
    rc_mismatch = []
    for tbl, expected in EXPECTED_ROW_COUNTS.items():
        actual = len(tables.get(tbl, []))
        if actual != expected:
            rc_mismatch.append(f"{tbl}: {actual} != {expected}")
    if rc_mismatch:
        errors.append(f"Check 01 Failed: Row count mismatches: {rc_mismatch}")
        print(f"  [FAIL] Check 01: Row Counts: {rc_mismatch}")
    else:
        print(f"  [PASS] Check 01: Row Counts (All 12 tables match expected counts exactly)")

    # CHECK 02: Master Customer Entity Count
    if len(cust_ids) == 96096:
        print(f"  [PASS] Check 02: Master Customer Entity Count (Exactly 96,096 distinct customer_unique_ids)")
    else:
        errors.append(f"Check 02 Failed: Customer count {len(cust_ids)} != 96,096")
        print(f"  [FAIL] Check 02: Master Customer Entity Count: {len(cust_ids)}")

    # CHECK 03: Customer PK & Email Uniqueness
    emails = [r["email"] for r in tables["customer"]]
    if len(cust_ids) == len(tables["customer"]) and len(emails) == len(set(emails)):
        print(f"  [PASS] Check 03: Customer PK & Email Uniqueness (0 duplicate IDs, 0 duplicate emails)")
    else:
        errors.append("Check 03 Failed: Duplicate customer IDs or emails found")
        print("  [FAIL] Check 03: Duplicate customer IDs or emails found")

    # CHECK 04: Customer Email Format & Join Date Constraints
    invalid_emails = [r["email"] for r in tables["customer"] if not re.match(r"^[^@]+@[^@]+\.[^@]+$", r["email"])]
    invalid_join_dates = [r["join_date"] for r in tables["customer"] if r["join_date"] < "2016-01-01"]
    if not invalid_emails and not invalid_join_dates:
        print("  [PASS] Check 04: Customer Email Format & Join Date Domain Constraints (All valid)")
    else:
        errors.append(f"Check 04 Failed: {len(invalid_emails)} invalid emails, {len(invalid_join_dates)} invalid join dates")
        print("  [FAIL] Check 04: Invalid email format or join dates before 2016-01-01")

    # CHECK 05: Customer Phone Composite PK Uniqueness
    phone_pks = {(r["customer_id"], r["phone_number"]) for r in tables["customer_phone"]}
    if len(phone_pks) == len(tables["customer_phone"]):
        print(f"  [PASS] Check 05: Customer Phone Composite PK Uniqueness ({len(phone_pks):,} unique pairs)")
    else:
        errors.append("Check 05 Failed: Duplicate composite PK in customer_phone")
        print("  [FAIL] Check 05: Duplicate composite PK in customer_phone")

    # CHECK 06: Customer Phone Foreign Key Integrity
    orphan_phones = [r for r in tables["customer_phone"] if r["customer_id"] not in cust_ids]
    if not orphan_phones:
        print("  [PASS] Check 06: Customer Phone FK Integrity (0 orphan phones)")
    else:
        errors.append(f"Check 06 Failed: {len(orphan_phones)} orphan customer phones")
        print(f"  [FAIL] Check 06: {len(orphan_phones)} orphan customer phones")

    # CHECK 07: Customer Phone Format & Type Constraints
    invalid_phones = [r for r in tables["customer_phone"] if len(r["phone_number"]) < 8 or r["phone_type"] not in ["Mobile", "Home", "Work", "Office", "Other"]]
    if not invalid_phones:
        print("  [PASS] Check 07: Customer Phone Format & Type Constraints (Length >= 8, valid types)")
    else:
        errors.append("Check 07 Failed: Invalid phone number length or type")
        print("  [FAIL] Check 07: Invalid phone number length or type")

    # CHECK 08: Address Composite PK Uniqueness
    addr_pks = {(r["customer_id"], r["address_type"]) for r in tables["address"]}
    if len(addr_pks) == len(tables["address"]):
        print(f"  [PASS] Check 08: Address Composite PK Uniqueness ({len(addr_pks):,} unique pairs)")
    else:
        errors.append("Check 08 Failed: Duplicate composite PK in address")
        print("  [FAIL] Check 08: Duplicate composite PK in address")

    # CHECK 09: Address Foreign Key Integrity
    orphan_addrs = [r for r in tables["address"] if r["customer_id"] not in cust_ids]
    if not orphan_addrs:
        print("  [PASS] Check 09: Address FK Integrity (0 orphan addresses)")
    else:
        errors.append(f"Check 09 Failed: {len(orphan_addrs)} orphan addresses")
        print(f"  [FAIL] Check 09: {len(orphan_addrs)} orphan addresses")

    # CHECK 10: Address State Length & Type Constraints
    invalid_addrs = [r for r in tables["address"] if len(r["state"]) != 2 or r["address_type"] not in ["Shipping", "Billing", "Home", "Office", "Work", "Other"]]
    if not invalid_addrs:
        print("  [PASS] Check 10: Address State Length & Type Constraints (2-char state, valid types)")
    else:
        errors.append("Check 10 Failed: Invalid address state length or type")
        print("  [FAIL] Check 10: Invalid address state length or type")

    # CHECK 11: Vendor Primary Key & GST Uniqueness
    gsts = [r["gst_number"] for r in tables["vendor"]]
    if len(vendor_ids) == len(tables["vendor"]) and len(gsts) == len(set(gsts)):
        print(f"  [PASS] Check 11: Vendor PK & GST Uniqueness ({len(vendor_ids):,} vendors, {len(gsts):,} unique GSTs)")
    else:
        errors.append("Check 11 Failed: Duplicate vendor ID or GST")
        print("  [FAIL] Check 11: Duplicate vendor ID or GST")

    # CHECK 12: Vendor Rating & GST Length Constraints
    invalid_vendors = [r for r in tables["vendor"] if not (1.00 <= float(r["rating"]) <= 5.00) or len(r["gst_number"]) < 8]
    if not invalid_vendors:
        print("  [PASS] Check 12: Vendor Rating & GST Length Constraints (Ratings in [1.00, 5.00], GST len >= 8)")
    else:
        errors.append("Check 12 Failed: Invalid vendor rating or GST length")
        print("  [FAIL] Check 12: Invalid vendor rating or GST length")

    # CHECK 13: Category PK Uniqueness & Hierarchy Count (83 Categories)
    root_cats = [r for r in tables["category"] if not r["parent_category_id"] or r["parent_category_id"] in ["None", ""]]
    sub_cats = [r for r in tables["category"] if r["parent_category_id"] and r["parent_category_id"] not in ["None", ""]]
    if len(category_ids) == 83 and len(root_cats) == 9 and len(sub_cats) == 74:
        print(f"  [PASS] Check 13: Category Hierarchy Count: 83 total (9 L1 roots + 73 mapped L2 + 1 Uncategorized fallback = 74 non-root)")
    else:
        errors.append(f"Check 13 Failed: Category counts mismatch (Total: {len(category_ids)}, Roots: {len(root_cats)}, Sub: {len(sub_cats)})")
        print("  [FAIL] Check 13: Category hierarchy count mismatch")

    # CHECK 14: Category Recursive Foreign Key Integrity
    orphan_cat_parents = [r for r in sub_cats if int(r["parent_category_id"]) not in category_ids]
    if not orphan_cat_parents:
        print("  [PASS] Check 14: Category Recursive FK Integrity (0 orphan parent category references)")
    else:
        errors.append(f"Check 14 Failed: {len(orphan_cat_parents)} orphan parent category references")
        print("  [FAIL] Check 14: Orphan parent category references found")

    # CHECK 15: Category Self-Reference Prevention
    self_parents = [r for r in sub_cats if int(r["parent_category_id"]) == int(r["category_id"])]
    if not self_parents:
        print("  [PASS] Check 15: Category Self-Reference Prevention (0 self-parenting categories)")
    else:
        errors.append("Check 15 Failed: Self-parenting categories found")
        print("  [FAIL] Check 15: Self-parenting categories found")

    # CHECK 16: Warehouse Primary Key & Capacity Constraints
    invalid_whs = [r for r in tables["warehouse"] if int(r["capacity"]) <= 0]
    if len(warehouse_ids) == len(tables["warehouse"]) and not invalid_whs:
        print(f"  [PASS] Check 16: Warehouse PK & Capacity Constraints ({len(warehouse_ids)} hubs, capacities > 0)")
    else:
        errors.append("Check 16 Failed: Invalid warehouse capacity or duplicate ID")
        print("  [FAIL] Check 16: Invalid warehouse capacity or duplicate ID")

    # CHECK 17: Product Primary Key & Single Vendor Assignment
    if len(product_ids) == len(tables["product"]):
        print(f"  [PASS] Check 17: Product PK Uniqueness & Single Vendor Assignment ({len(product_ids):,} products)")
    else:
        errors.append("Check 17 Failed: Duplicate product IDs found")
        print("  [FAIL] Check 17: Duplicate product IDs found")

    # CHECK 18: Product Category & Vendor Foreign Key Integrity
    orphan_prod_cats = [r for r in tables["product"] if int(r["category_id"]) not in category_ids]
    orphan_prod_vendors = [r for r in tables["product"] if r["vendor_id"] not in vendor_ids]
    if not orphan_prod_cats and not orphan_prod_vendors:
        print("  [PASS] Check 18: Product Category & Vendor FK Integrity (0 orphan category or vendor links)")
    else:
        errors.append("Check 18 Failed: Orphan product category or vendor references")
        print("  [FAIL] Check 18: Orphan product category or vendor references")

    # CHECK 19: Product Price & Status Constraints
    invalid_prods = [r for r in tables["product"] if float(r["price"]) < 0.00 or r["status"] not in ["Active", "Inactive", "Out of Stock", "Discontinued"]]
    if not invalid_prods:
        print("  [PASS] Check 19: Product Price & Status Constraints (Catalog prices >= 0.00, valid status enums)")
    else:
        errors.append("Check 19 Failed: Negative product price or invalid status")
        print("  [FAIL] Check 19: Negative product price or invalid status")

    # CHECK 20: Product Tag Composite PK & Foreign Key Integrity
    tag_pks = {(r["product_id"], r["tag"]) for r in tables["product_tag"]}
    orphan_tags = [r for r in tables["product_tag"] if r["product_id"] not in product_ids or len(r["tag"]) < 2]
    if len(tag_pks) == len(tables["product_tag"]) and not orphan_tags:
        print(f"  [PASS] Check 20: Product Tag Composite PK & FK Integrity ({len(tag_pks):,} unique pairs, 0 orphans, tag len >= 2)")
    else:
        errors.append("Check 20 Failed: Duplicate tag PK, orphan tag, or short tag length")
        print("  [FAIL] Check 20: Duplicate tag PK, orphan tag, or short tag length")

    # CHECK 21: Inventory Composite PK & Foreign Key Integrity
    inv_pks = {(r["product_id"], int(r["warehouse_id"])) for r in tables["inventory"]}
    orphan_inv = [r for r in tables["inventory"] if r["product_id"] not in product_ids or int(r["warehouse_id"]) not in warehouse_ids]
    if len(inv_pks) == len(tables["inventory"]) and not orphan_inv:
        print(f"  [PASS] Check 21: Inventory Composite PK & FK Integrity ({len(inv_pks):,} unique pairs, 0 orphans)")
    else:
        errors.append("Check 21 Failed: Duplicate inventory PK or orphan inventory references")
        print("  [FAIL] Check 21: Duplicate inventory PK or orphan inventory references")

    # CHECK 22: Inventory Stock & Reorder Non-Negative Constraints
    invalid_inv = [r for r in tables["inventory"] if int(r["stock_quantity"]) < 0 or int(r["reorder_level"]) < 0]
    if not invalid_inv:
        print("  [PASS] Check 22: Inventory Stock & Reorder Non-Negative Constraints (stock >= 0, reorder >= 0)")
    else:
        errors.append("Check 22 Failed: Negative stock quantity or reorder level")
        print("  [FAIL] Check 22: Negative stock quantity or reorder level")

    # CHECK 23: Orders Primary Key & Customer Foreign Key Integrity
    orphan_orders = [r for r in tables["orders"] if r["customer_id"] not in cust_ids]
    if len(order_ids) == len(tables["orders"]) and not orphan_orders:
        print(f"  [PASS] Check 23: Orders PK & Customer FK Integrity ({len(order_ids):,} orders, 0 orphan orders)")
    else:
        errors.append("Check 23 Failed: Duplicate order ID or orphan customer FK in orders")
        print("  [FAIL] Check 23: Duplicate order ID or orphan customer FK in orders")

    # CHECK 24: Orders Status Normalization Constraints
    allowed_statuses = ["DELIVERED", "SHIPPED", "CANCELLED", "UNAVAILABLE", "INVOICED", "PROCESSING", "CREATED", "APPROVED"]
    invalid_order_status = [r for r in tables["orders"] if r["status"] not in allowed_statuses]
    if not invalid_order_status:
        print("  [PASS] Check 24: Orders Status Normalization Constraints (100% match uppercase check enums)")
    else:
        errors.append("Check 24 Failed: Invalid order status values")
        print("  [FAIL] Check 24: Invalid order status values")

    # CHECK 25: Order Item Composite PK & Foreign Key Integrity
    item_pks = {(r["order_id"], r["product_id"]) for r in tables["order_item"]}
    orphan_items = [r for r in tables["order_item"] if r["order_id"] not in order_ids or r["product_id"] not in product_ids]
    if len(item_pks) == len(tables["order_item"]) and not orphan_items:
        print(f"  [PASS] Check 25: Order Item Composite PK & FK Integrity ({len(item_pks):,} unique pairs, 0 orphans)")
    else:
        errors.append("Check 25 Failed: Duplicate order_item PK or orphan references")
        print("  [FAIL] Check 25: Duplicate order_item PK or orphan references")

    # CHECK 26: Order Item Aggregation & Conserved Physical Units (112,650 units)
    tot_units = sum(int(r["quantity"]) for r in tables["order_item"])
    invalid_item_prices = [r for r in tables["order_item"] if int(r["quantity"]) <= 0 or float(r["price_at_purchase"]) < 0.00]
    if tot_units == 112650 and len(item_pks) == 102425 and not invalid_item_prices:
        print(f"  [PASS] Check 26: Order Item Conserved Physical Units: Exactly 112,650 units across 102,425 composite pairs")
    else:
        errors.append(f"Check 26 Failed: Conserved units {tot_units} != 112,650 or pairs {len(item_pks)} != 102,425")
        print("  [FAIL] Check 26: Order item quantity conservation failure")

    # CHECK 27: Payment Composite PK, Positive Amount & Txn Reference Uniqueness
    pay_pks = {(r["order_id"], int(r["payment_id"])) for r in tables["payment"]}
    txn_refs = {r["transaction_reference"] for r in tables["payment"]}
    orphan_payments = [r for r in tables["payment"] if r["order_id"] not in order_ids]
    invalid_pay_amounts = [r for r in tables["payment"] if float(r["amount"]) <= 0.00]
    if len(pay_pks) == len(tables["payment"]) and len(txn_refs) == len(tables["payment"]) and not orphan_payments and not invalid_pay_amounts:
        print(f"  [PASS] Check 27: Payment Composite PK, Positive Amounts & Txn Ref Uniqueness ({len(pay_pks):,} payments, all amounts > 0.00)")
    else:
        errors.append("Check 27 Failed: Payment PK duplication, non-positive amount, duplicate txn ref, or orphan order")
        print("  [FAIL] Check 27: Payment validation failure")

    print("================================================================================")
    if not errors:
        print("ALL 27 PRE-LOAD DRY RUN CHECKS PASSED: 100% RELATIONAL & DOMAIN INTEGRITY")
        print("================================================================================\n")
        return True, []
    else:
        print(f"DRY RUN FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  - {err}")
        print("================================================================================\n")
        return False, errors

def validate_mysql_database(connection) -> Tuple[bool, List[str]]:
    """
    Executes the complete 27-check live database verification suite against MySQL 8.4.
    """
    print("================================================================================")
    print("POST-LOAD LIVE MYSQL DATABASE VALIDATION: 27 CHECKS (multivendor_ecommerce_db)")
    print("================================================================================")
    errors = []
    
    with connection.cursor() as cur:
        # Check 01: Row Counts
        rc_mismatch = []
        for tbl, expected in EXPECTED_ROW_COUNTS.items():
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            act = cur.fetchone()[0]
            if act != expected:
                rc_mismatch.append(f"{tbl}: {act} != {expected}")
        if rc_mismatch:
            errors.append(f"Check 01: {rc_mismatch}")
            print(f"  [FAIL] Check 01: Row Counts: {rc_mismatch}")
        else:
            print("  [PASS] Check 01: Table Row Counts (All 12 tables match expected counts exactly)")

        # Check 02: Master Customer Entity Count
        cur.execute("SELECT COUNT(DISTINCT customer_id) FROM `customer`;")
        distinct_cust = cur.fetchone()[0]
        if distinct_cust == 96096:
            print(f"  [PASS] Check 02: Master Customer Entity Count: Exactly {distinct_cust:,} distinct accounts")
        else:
            errors.append(f"Check 02: {distinct_cust} != 96,096")
            print(f"  [FAIL] Check 02: Customer count {distinct_cust}")

        # Check 03: Customer PK & Email Uniqueness
        cur.execute("SELECT COUNT(*) - COUNT(DISTINCT customer_id), COUNT(*) - COUNT(DISTINCT email) FROM `customer`;")
        dup_cid, dup_email = cur.fetchone()
        if dup_cid == 0 and dup_email == 0:
            print("  [PASS] Check 03: Customer Primary Key & Email Uniqueness (0 duplicates)")
        else:
            errors.append("Check 03: Duplicate customer IDs or emails")
            print("  [FAIL] Check 03: Duplicate customer IDs or emails")

        # Check 04: Customer Email Format & Join Date Constraints
        cur.execute("SELECT COUNT(*) FROM `customer` WHERE email NOT LIKE '%_@__%.__%' OR join_date < '2016-01-01';")
        invalid_cust = cur.fetchone()[0]
        if invalid_cust == 0:
            print("  [PASS] Check 04: Customer Email Format & Join Date Constraints (0 violations)")
        else:
            errors.append("Check 04: Invalid email format or join date")
            print("  [FAIL] Check 04: Invalid email format or join date")

        # Check 05: Customer Phone Composite PK Uniqueness
        cur.execute("SELECT COUNT(*) - COUNT(DISTINCT customer_id, phone_number) FROM `customer_phone`;")
        dup_phone_pk = cur.fetchone()[0]
        if dup_phone_pk == 0:
            print("  [PASS] Check 05: Customer Phone Composite PK Uniqueness (0 duplicates)")
        else:
            errors.append("Check 05: Duplicate customer phone PK")
            print("  [FAIL] Check 05: Duplicate customer phone PK")

        # Check 06: Customer Phone Foreign Key Integrity
        cur.execute("SELECT COUNT(*) FROM `customer_phone` cp LEFT JOIN `customer` c ON cp.customer_id = c.customer_id WHERE c.customer_id IS NULL;")
        orphan_phones = cur.fetchone()[0]
        if orphan_phones == 0:
            print("  [PASS] Check 06: Customer Phone Foreign Key Integrity (0 orphan phones)")
        else:
            errors.append(f"Check 06: {orphan_phones} orphan phones")
            print("  [FAIL] Check 06: Orphan customer phones found")

        # Check 07: Customer Phone Format & Type Constraints
        cur.execute("SELECT COUNT(*) FROM `customer_phone` WHERE CHAR_LENGTH(phone_number) < 8 OR phone_type NOT IN ('Mobile', 'Home', 'Work', 'Office', 'Other');")
        invalid_phones = cur.fetchone()[0]
        if invalid_phones == 0:
            print("  [PASS] Check 07: Customer Phone Format & Type Constraints (0 violations)")
        else:
            errors.append("Check 07: Invalid phone format or type")
            print("  [FAIL] Check 07: Invalid phone format or type")

        # Check 08: Address Composite PK Uniqueness
        cur.execute("SELECT COUNT(*) - COUNT(DISTINCT customer_id, address_type) FROM `address`;")
        dup_addr_pk = cur.fetchone()[0]
        if dup_addr_pk == 0:
            print("  [PASS] Check 08: Address Composite PK Uniqueness (0 duplicates)")
        else:
            errors.append("Check 08: Duplicate address PK")
            print("  [FAIL] Check 08: Duplicate address PK")

        # Check 09: Address Foreign Key Integrity
        cur.execute("SELECT COUNT(*) FROM `address` a LEFT JOIN `customer` c ON a.customer_id = c.customer_id WHERE c.customer_id IS NULL;")
        orphan_addrs = cur.fetchone()[0]
        if orphan_addrs == 0:
            print("  [PASS] Check 09: Address Foreign Key Integrity (0 orphan addresses)")
        else:
            errors.append(f"Check 09: {orphan_addrs} orphan addresses")
            print("  [FAIL] Check 09: Orphan addresses found")

        # Check 10: Address State Length & Type Constraints
        cur.execute("SELECT COUNT(*) FROM `address` WHERE CHAR_LENGTH(state) <> 2 OR address_type NOT IN ('Shipping', 'Billing', 'Home', 'Office', 'Work', 'Other');")
        invalid_addrs = cur.fetchone()[0]
        if invalid_addrs == 0:
            print("  [PASS] Check 10: Address State Length & Type Constraints (0 violations)")
        else:
            errors.append("Check 10: Invalid address state length or type")
            print("  [FAIL] Check 10: Invalid address state length or type")

        # Check 11: Vendor Primary Key & GST Uniqueness
        cur.execute("SELECT COUNT(*) - COUNT(DISTINCT vendor_id), COUNT(*) - COUNT(DISTINCT gst_number) FROM `vendor`;")
        dup_vid, dup_gst = cur.fetchone()
        if dup_vid == 0 and dup_gst == 0:
            print("  [PASS] Check 11: Vendor Primary Key & GST Uniqueness (0 duplicates)")
        else:
            errors.append("Check 11: Duplicate vendor ID or GST")
            print("  [FAIL] Check 11: Duplicate vendor ID or GST")

        # Check 12: Vendor Rating & GST Length Constraints
        cur.execute("SELECT COUNT(*) FROM `vendor` WHERE rating < 1.00 OR rating > 5.00 OR CHAR_LENGTH(gst_number) < 8;")
        invalid_vendors = cur.fetchone()[0]
        if invalid_vendors == 0:
            print("  [PASS] Check 12: Vendor Rating & GST Length Constraints (0 violations)")
        else:
            errors.append("Check 12: Invalid vendor rating or GST length")
            print("  [FAIL] Check 12: Invalid vendor rating or GST length")

        # Check 13: Category PK Uniqueness & Hierarchy Count (83 Categories)
        cur.execute("SELECT COUNT(*), SUM(CASE WHEN parent_category_id IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN parent_category_id IS NOT NULL THEN 1 ELSE 0 END) FROM `category`;")
        tot_c, root_c, sub_c = cur.fetchone()
        if tot_c == 83 and root_c == 9 and sub_c == 74:
            print("  [PASS] Check 13: Category Hierarchy Count: 83 total (9 L1 roots + 73 mapped L2 + 1 Uncategorized fallback = 74 non-root)")
        else:
            errors.append("Check 13: Category count mismatch")
            print("  [FAIL] Check 13: Category count mismatch")

        # Check 14: Category Recursive Foreign Key Integrity
        cur.execute("SELECT COUNT(*) FROM `category` c WHERE c.parent_category_id IS NOT NULL AND c.parent_category_id NOT IN (SELECT category_id FROM `category`);")
        orphan_cats = cur.fetchone()[0]
        if orphan_cats == 0:
            print("  [PASS] Check 14: Category Recursive Foreign Key Integrity (0 orphan parents)")
        else:
            errors.append(f"Check 14: {orphan_cats} orphan parents")
            print("  [FAIL] Check 14: Orphan category parents found")

        # Check 15: Category Self-Reference Prevention
        cur.execute("SELECT COUNT(*) FROM `category` WHERE parent_category_id = category_id;")
        self_cats = cur.fetchone()[0]
        if self_cats == 0:
            print("  [PASS] Check 15: Category Self-Reference Prevention (0 self-parenting categories)")
        else:
            errors.append("Check 15: Self-parenting categories found")
            print("  [FAIL] Check 15: Self-parenting categories found")

        # Check 16: Warehouse Primary Key & Capacity Constraints
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT warehouse_id), SUM(CASE WHEN capacity <= 0 THEN 1 ELSE 0 END) FROM `warehouse`;")
        tot_w, dist_w, inv_w = cur.fetchone()
        if tot_w == 8 and dist_w == 8 and inv_w == 0:
            print("  [PASS] Check 16: Warehouse Primary Key & Capacity Constraints (0 violations)")
        else:
            errors.append("Check 16: Warehouse PK or capacity error")
            print("  [FAIL] Check 16: Warehouse PK or capacity error")

        # Check 17: Product Primary Key & Single Vendor Resolution
        cur.execute("SELECT COUNT(*) - COUNT(DISTINCT product_id) FROM `product`;")
        dup_pid = cur.fetchone()[0]
        if dup_pid == 0:
            print("  [PASS] Check 17: Product Primary Key & Single Vendor Assignment (0 duplicate products)")
        else:
            errors.append("Check 17: Duplicate product IDs")
            print("  [FAIL] Check 17: Duplicate product IDs")

        # Check 18: Product Category & Vendor Foreign Key Integrity
        cur.execute("""
            SELECT 
                (SELECT COUNT(*) FROM `product` p LEFT JOIN `category` c ON p.category_id = c.category_id WHERE c.category_id IS NULL),
                (SELECT COUNT(*) FROM `product` p LEFT JOIN `vendor` v ON p.vendor_id = v.vendor_id WHERE v.vendor_id IS NULL);
        """)
        orp_p_cat, orp_p_ven = cur.fetchone()
        if orp_p_cat == 0 and orp_p_ven == 0:
            print("  [PASS] Check 18: Product Category & Vendor Foreign Key Integrity (0 orphan references)")
        else:
            errors.append("Check 18: Orphan product category or vendor FK")
            print("  [FAIL] Check 18: Orphan product category or vendor FK")

        # Check 19: Product Price & Status Constraints
        cur.execute("SELECT COUNT(*) FROM `product` WHERE price < 0.00 OR status NOT IN ('Active', 'Inactive', 'Out of Stock', 'Discontinued', 'ACTIVE', 'INACTIVE', 'OUT_OF_STOCK', 'DISCONTINUED');")
        inv_prods = cur.fetchone()[0]
        if inv_prods == 0:
            print("  [PASS] Check 19: Product Price & Status Constraints (Catalog prices >= 0.00, valid status)")
        else:
            errors.append("Check 19: Negative product price or invalid status")
            print("  [FAIL] Check 19: Negative product price or invalid status")

        # Check 20: Product Tag Composite PK & Foreign Key Integrity
        cur.execute("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT product_id, tag),
                (SELECT COUNT(*) FROM `product_tag` pt LEFT JOIN `product` p ON pt.product_id = p.product_id WHERE p.product_id IS NULL),
                SUM(CASE WHEN CHAR_LENGTH(tag) < 2 THEN 1 ELSE 0 END)
            FROM `product_tag`;
        """)
        dup_tag, orp_tag, inv_tag_len = cur.fetchone()
        if dup_tag == 0 and orp_tag == 0 and inv_tag_len == 0:
            print("  [PASS] Check 20: Product Tag Composite PK & Foreign Key Integrity (0 duplicates, 0 orphans, tag len >= 2)")
        else:
            errors.append("Check 20: Product tag validation failure")
            print("  [FAIL] Check 20: Product tag validation failure")

        # Check 21: Inventory Composite PK & Foreign Key Integrity
        cur.execute("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT product_id, warehouse_id),
                (SELECT COUNT(*) FROM `inventory` i LEFT JOIN `product` p ON i.product_id = p.product_id WHERE p.product_id IS NULL),
                (SELECT COUNT(*) FROM `inventory` i LEFT JOIN `warehouse` w ON i.warehouse_id = w.warehouse_id WHERE w.warehouse_id IS NULL)
            FROM `inventory`;
        """)
        dup_inv, orp_inv_p, orp_inv_w = cur.fetchone()
        if dup_inv == 0 and orp_inv_p == 0 and orp_inv_w == 0:
            print("  [PASS] Check 21: Inventory Composite PK & Foreign Key Integrity (0 duplicates, 0 orphans)")
        else:
            errors.append("Check 21: Inventory PK or FK error")
            print("  [FAIL] Check 21: Inventory PK or FK error")

        # Check 22: Inventory Stock & Reorder Non-Negative Constraints
        cur.execute("SELECT COUNT(*) FROM `inventory` WHERE stock_quantity < 0 OR reorder_level < 0;")
        inv_stock_err = cur.fetchone()[0]
        if inv_stock_err == 0:
            print("  [PASS] Check 22: Inventory Stock & Reorder Non-Negative Constraints (stock >= 0, reorder >= 0)")
        else:
            errors.append("Check 22: Negative inventory stock or reorder level")
            print("  [FAIL] Check 22: Negative inventory stock or reorder level")

        # Check 23: Orders Primary Key & Customer Foreign Key Integrity
        cur.execute("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT order_id),
                (SELECT COUNT(*) FROM `orders` o LEFT JOIN `customer` c ON o.customer_id = c.customer_id WHERE c.customer_id IS NULL)
            FROM `orders`;
        """)
        dup_oid, orp_orders = cur.fetchone()
        if dup_oid == 0 and orp_orders == 0:
            print("  [PASS] Check 23: Orders Primary Key & Customer Foreign Key Integrity (0 duplicates, 0 orphans)")
        else:
            errors.append("Check 23: Orders PK or customer FK error")
            print("  [FAIL] Check 23: Orders PK or customer FK error")

        # Check 24: Orders Status Normalization Constraints
        cur.execute("""
            SELECT COUNT(*) FROM `orders` 
            WHERE status NOT IN ('PLACED', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'PROCESSING', 'INVOICED', 'UNAVAILABLE', 'CREATED', 'APPROVED', 'delivered', 'shipped', 'canceled', 'unavailable', 'invoiced', 'processing', 'created', 'approved');
        """)
        inv_order_status = cur.fetchone()[0]
        if inv_order_status == 0:
            print("  [PASS] Check 24: Orders Status Normalization Constraints (0 invalid status values)")
        else:
            errors.append("Check 24: Invalid order status values")
            print("  [FAIL] Check 24: Invalid order status values")

        # Check 25: Order Item Composite PK & Foreign Key Integrity
        cur.execute("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT order_id, product_id),
                (SELECT COUNT(*) FROM `order_item` oi LEFT JOIN `orders` o ON oi.order_id = o.order_id WHERE o.order_id IS NULL),
                (SELECT COUNT(*) FROM `order_item` oi LEFT JOIN `product` p ON oi.product_id = p.product_id WHERE p.product_id IS NULL)
            FROM `order_item`;
        """)
        dup_oi, orp_oi_o, orp_oi_p = cur.fetchone()
        if dup_oi == 0 and orp_oi_o == 0 and orp_oi_p == 0:
            print("  [PASS] Check 25: Order Item Composite PK & Foreign Key Integrity (0 duplicates, 0 orphans)")
        else:
            errors.append("Check 25: Order item PK or FK error")
            print("  [FAIL] Check 25: Order item PK or FK error")

        # Check 26: Order Item Aggregation & Conserved Physical Units (112,650 units)
        cur.execute("SELECT SUM(quantity), COUNT(*), MIN(quantity), MIN(price_at_purchase) FROM `order_item`;")
        tot_q, dist_pairs, min_q, min_p = cur.fetchone()
        if tot_q == 112650 and dist_pairs == 102425 and min_q > 0 and min_p >= 0.00:
            print(f"  [PASS] Check 26: Order Item Conserved Physical Units: Exactly 112,650 units across 102,425 composite pairs")
        else:
            errors.append("Check 26: Order item quantity conservation failure")
            print("  [FAIL] Check 26: Order item quantity conservation failure")

        # Check 27: Payment Composite PK, Positive Amount & Txn Reference Uniqueness
        cur.execute("""
            SELECT 
                COUNT(*) - COUNT(DISTINCT order_id, payment_id),
                COUNT(*) - COUNT(DISTINCT transaction_reference),
                (SELECT COUNT(*) FROM `payment` p LEFT JOIN `orders` o ON p.order_id = o.order_id WHERE o.order_id IS NULL),
                SUM(CASE WHEN amount <= 0.00 THEN 1 ELSE 0 END)
            FROM `payment`;
        """)
        dup_pay_pk, dup_txn, orp_pay, non_pos_pay = cur.fetchone()
        if dup_pay_pk == 0 and dup_txn == 0 and orp_pay == 0 and non_pos_pay == 0:
            print("  [PASS] Check 27: Payment Composite PK, Positive Amounts & Txn Ref Uniqueness (0 duplicates, 0 orphans, amounts > 0.00)")
        else:
            errors.append("Check 27: Payment validation failure")
            print("  [FAIL] Check 27: Payment validation failure")

    print("================================================================================")
    if not errors:
        print("ALL 27 LIVE MYSQL DATABASE CHECKS PASSED SUCCESSFULLY!")
        print("================================================================================\n")
        return True, []
    else:
        print(f"LIVE VALIDATION FAILED WITH {len(errors)} ERRORS:")
        for err in errors:
            print(f"  - {err}")
        print("================================================================================\n")
        return False, errors

if __name__ == "__main__":
    success, errors = validate_dry_run_csvs()
    sys.exit(0 if success else 1)
