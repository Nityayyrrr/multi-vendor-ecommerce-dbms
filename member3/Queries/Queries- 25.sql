SELECT 
    p.product_id,
    p.product_name,
    SUM(oi.quantity) AS total_quantity
FROM PRODUCT p
JOIN ORDER_ITEM oi
    ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
ORDER BY total_quantity DESC
LIMIT 1;
