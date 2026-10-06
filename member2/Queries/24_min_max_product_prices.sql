USE multivendor_ecommerce_db;

SELECT
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price
FROM product;