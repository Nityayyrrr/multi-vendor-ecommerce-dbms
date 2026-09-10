-- USE multivendor_ecommerce_db;
SELECT
    product_id,
    product_name,
    price
FROM product
WHERE price > (
    SELECT AVG(price)
    FROM product
);