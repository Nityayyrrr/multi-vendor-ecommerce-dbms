USE multivendor_ecommerce_db;

-- Query 12: Product count per category
SELECT 
    c.category_id,
    c.category_name,
    COUNT(p.product_id) AS product_count
FROM category c
LEFT JOIN product p
    ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_name;
