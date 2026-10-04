USE multivendor_ecommerce_db;
SELECT product_id, product_name, price
FROM product
ORDER BY price ASC
LIMIT 10;