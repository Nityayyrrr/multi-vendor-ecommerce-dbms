SELECT p.product_id, p.product_name
FROM product p
WHERE EXISTS (
    SELECT 1
    FROM order_item oi
    WHERE oi.product_id = p.product_id
);