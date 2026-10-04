SELECT 
    o.order_id,
    c.customer_id,
    c.email,
    o.order_date,
    o.status
FROM orders o
JOIN customer c
    ON o.customer_id = c.customer_id;
