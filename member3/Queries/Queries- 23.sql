SELECT 
    c.customer_id,
    c.customer_name,
    SUM(p.amount) AS total_spending
FROM CUSTOMER c
JOIN ORDERS o
    ON c.customer_id = o.customer_id
JOIN PAYMENT p
    ON o.order_id = p.order_id
GROUP BY c.customer_id, c.customer_name;
