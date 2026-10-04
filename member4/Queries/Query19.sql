SELECT
    p.product_id,
    p.product_name
FROM product p
JOIN inventory i
    ON p.product_id = i.product_id
GROUP BY p.product_id, p.product_name
HAVING COUNT(DISTINCT i.warehouse_id) = (
    SELECT COUNT(*)
    FROM warehouse
);