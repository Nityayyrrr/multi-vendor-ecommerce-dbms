USE multivendor_ecommerce_db;

SELECT
    p.product_id,
    p.product_name,
    c.category_name
FROM product p
JOIN category c
    ON p.category_id = c.category_id;