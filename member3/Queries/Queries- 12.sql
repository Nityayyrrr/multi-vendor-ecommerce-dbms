SELECT 
    c.category_id,
    c.category_name,
    COUNT(p.product_id) AS product_count
FROM Categories c
LEFT JOIN Products p
    ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_name;
