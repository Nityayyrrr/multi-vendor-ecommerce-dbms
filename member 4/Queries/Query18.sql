/*Display customers who have placed more orders than the average number of orders placed by all customers.*/
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS total_orders
FROM customer c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) > (
    SELECT AVG(order_count)
    FROM (
        SELECT COUNT(o2.order_id) AS order_count
        FROM customer c2
        LEFT JOIN orders o2
            ON c2.customer_id = o2.customer_id
        GROUP BY c2.customer_id
    ) AS customer_orders
);