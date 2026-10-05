USE multivendor_ecommerce_db;

SELECT
    product_id,
    product_name,
    price,
    category_id
FROM product
WHERE price > ALL (
    SELECT price
    FROM product
    WHERE category_id = 1
);