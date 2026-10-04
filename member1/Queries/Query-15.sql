SELECT
    product_id,
    product_name,
    price
FROM product
WHERE price BETWEEN 50 AND 200
ORDER BY price;