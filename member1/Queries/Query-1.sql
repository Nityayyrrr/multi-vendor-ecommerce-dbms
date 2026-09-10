-- USE multivendor_ecommerce_db;
-- SHOW TABLES;
SELECT
    p.product_id,
    p.product_name,
    v.vendor_name
FROM product p
INNER JOIN vendor v
    ON p.vendor_id = v.vendor_id;