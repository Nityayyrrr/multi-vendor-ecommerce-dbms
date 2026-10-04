SELECT customer_id, COUNT(*) AS order_count
FROM ORDERS
GROUP BY customer_id
HAVING COUNT(*) > (
    SELECT AVG(order_count)
    FROM (
        SELECT customer_id, COUNT(*) AS order_count
        FROM ORDERS
        GROUP BY customer_id
    ) AS temp
);
