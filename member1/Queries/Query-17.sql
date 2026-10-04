SELECT
    p.product_id,
    p.product_name,
    COUNT(i.warehouse_id) AS warehouse_count
FROM product p
JOIN inventory i
    ON p.product_id = i.product_id
GROUP BY p.product_id, p.product_name
HAVING COUNT(i.warehouse_id) > 1;