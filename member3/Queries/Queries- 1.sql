SELECT 
    o.order_id,
    c.customer_id,
    c.email,
    o.order_date,
    o.status
FROM Orders o
JOIN Customers c
    ON o.customer_id = c.customer_id;
