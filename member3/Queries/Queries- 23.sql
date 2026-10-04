SELECT 
    c.customer_id,
    c.name,
    SUM(p.amount) AS total_spending
FROM customer c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN payment p
    ON o.order_id = p.order_id
GROUP BY c.customer_id, c.name;
