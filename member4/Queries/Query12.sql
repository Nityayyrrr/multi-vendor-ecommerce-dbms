/* Calculate the total quantity purchased for every product. */
SELECT 
    p.product_id,
    p.product_name,
    COALESCE(SUM(oi.quantity), 0) AS total_quantity
FROM product p
LEFT JOIN order_item oi
    ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name;