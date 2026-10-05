USE multivendor_ecommerce_db;

SELECT
    c.category_id,
    c.category_name,
    COUNT(p.product_id) AS product_count
FROM category c
JOIN product p
    ON c.category_id = p.category_id
GROUP BY
    c.category_id,
    c.category_name
ORDER BY product_count DESC
LIMIT 1;