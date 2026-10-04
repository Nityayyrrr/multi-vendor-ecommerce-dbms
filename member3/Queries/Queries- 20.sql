SELECT 
    o.order_id,
    c.name,
    p.product_name,
    oi.quantity,
    oi.price_at_purchase
FROM orders o
JOIN customer c
    ON o.customer_id = c.customer_id
JOIN order_item oi
    ON o.order_id = oi.order_id
JOIN product p
    ON oi.product_id = p.product_id;
