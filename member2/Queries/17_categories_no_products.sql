USE multivendor_ecommerce_db;

SELECT
    c.category_id,
    c.category_name
FROM category c
LEFT JOIN product p
    ON c.category_id = p.category_id
WHERE p.product_id IS NULL;