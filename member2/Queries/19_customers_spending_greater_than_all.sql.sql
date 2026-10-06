USE multivendor_ecommerce_db;

SELECT
    c.customer_id,
    SUM(oi.quantity * oi.price_at_purchase) AS total_spending
FROM customer c
JOIN orders o
    ON c.customer_id = o.customer_id
JOIN order_item oi
    ON o.order_id = oi.order_id
GROUP BY c.customer_id
HAVING total_spending > ALL (
    SELECT spending
    FROM (
        SELECT
            o2.customer_id,
            SUM(oi2.quantity * oi2.price_at_purchase) AS spending
        FROM orders o2
        JOIN order_item oi2
            ON o2.order_id = oi2.order_id
        GROUP BY o2.customer_id
        HAVING COUNT(DISTINCT o2.order_id) < 3
    ) AS fewer_order_customers
);