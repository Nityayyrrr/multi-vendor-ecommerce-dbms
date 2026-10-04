USE multivendor_ecommerce_db;

SELECT
    p.product_id,
    p.product_name,
    w.warehouse_id,
    w.location
FROM product p
JOIN inventory i
    ON p.product_id = i.product_id
JOIN warehouse w
    ON i.warehouse_id = w.warehouse_id;