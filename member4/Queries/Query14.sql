/*Display all customers along with the number of orders they have placed, including customers with zero orders.*/
SELECT 
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS total_orders
FROM customer c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name;
