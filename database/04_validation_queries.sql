-- Schema verification queries for Multi-Vendor E-Commerce database

USE `multivendor_ecommerce_db`;

-- Check 1: Verify all 12 tables exist
SELECT 
    table_name,
    engine,
    table_collation,
    table_comment
FROM information_schema.tables
WHERE table_schema = 'multivendor_ecommerce_db'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Count verification (should be exactly 12)
SELECT 
    CASE 
        WHEN COUNT(*) = 12 THEN 'PASS: Exactly 12 canonical tables exist.'
        ELSE CONCAT('FAIL: Found ', COUNT(*), ' tables. Expected exactly 12.')
    END AS table_count_validation
FROM information_schema.tables
WHERE table_schema = 'multivendor_ecommerce_db'
  AND table_type = 'BASE TABLE';


-- Check 2: Verify primary keys and composite primary keys
SELECT 
    table_name,
    GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ', ') AS primary_key_columns,
    COUNT(*) AS key_column_count,
    CASE 
        WHEN table_name = 'customer' AND GROUP_CONCAT(column_name) = 'customer_id' THEN 'PASS'
        WHEN table_name = 'vendor' AND GROUP_CONCAT(column_name) = 'vendor_id' THEN 'PASS'
        WHEN table_name = 'category' AND GROUP_CONCAT(column_name) = 'category_id' THEN 'PASS'
        WHEN table_name = 'warehouse' AND GROUP_CONCAT(column_name) = 'warehouse_id' THEN 'PASS'
        WHEN table_name = 'product' AND GROUP_CONCAT(column_name) = 'product_id' THEN 'PASS'
        WHEN table_name = 'orders' AND GROUP_CONCAT(column_name) = 'order_id' THEN 'PASS'
        WHEN table_name = 'customer_phone' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'customer_id, phone_number' THEN 'PASS (Composite)'
        WHEN table_name = 'address' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'customer_id, address_type' THEN 'PASS (Composite)'
        WHEN table_name = 'product_tag' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'product_id, tag' THEN 'PASS (Composite)'
        WHEN table_name = 'inventory' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'product_id, warehouse_id' THEN 'PASS (Composite)'
        WHEN table_name = 'order_item' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'order_id, product_id' THEN 'PASS (Composite)'
        WHEN table_name = 'payment' AND GROUP_CONCAT(column_name ORDER BY seq_in_index) = 'order_id, payment_id' THEN 'PASS (Composite)'
        ELSE 'FAIL: Unexpected PK configuration'
    END AS pk_verification_status
FROM information_schema.statistics
WHERE table_schema = 'multivendor_ecommerce_db'
  AND index_name = 'PRIMARY'
GROUP BY table_name
ORDER BY table_name;


-- Check 3: Verify foreign keys and ON DELETE / UPDATE rules
SELECT 
    kcu.table_name AS child_table,
    kcu.column_name AS fk_column,
    kcu.constraint_name,
    kcu.referenced_table_name AS parent_table,
    kcu.referenced_column_name AS parent_column,
    rc.delete_rule,
    rc.update_rule
FROM information_schema.key_column_usage kcu
JOIN information_schema.referential_constraints rc
  ON kcu.constraint_name = rc.constraint_name
 AND kcu.constraint_schema = rc.constraint_schema
WHERE kcu.constraint_schema = 'multivendor_ecommerce_db'
  AND kcu.referenced_table_name IS NOT NULL
ORDER BY kcu.table_name, kcu.column_name;


-- Check 4: Verify unique constraints
SELECT 
    table_name,
    index_name AS unique_constraint_name,
    GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ', ') AS unique_columns
FROM information_schema.statistics
WHERE table_schema = 'multivendor_ecommerce_db'
  AND non_unique = 0
  AND index_name != 'PRIMARY'
GROUP BY table_name, index_name
ORDER BY table_name;


-- Check 5: Verify check constraints
SELECT 
    tc.table_name,
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints tc
JOIN information_schema.check_constraints cc
  ON tc.constraint_name = cc.constraint_name
 AND tc.constraint_schema = cc.constraint_schema
WHERE tc.constraint_schema = 'multivendor_ecommerce_db'
  AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;


-- Check 6: Inspect columns and data types
SELECT 
    table_name,
    ordinal_position,
    column_name,
    column_type,
    is_nullable,
    column_default,
    extra
FROM information_schema.columns
WHERE table_schema = 'multivendor_ecommerce_db'
ORDER BY table_name, ordinal_position;
