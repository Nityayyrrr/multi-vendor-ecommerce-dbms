SELECT
    c.customer_id,
    c.name,
    SUM(p.amount) AS total_spending
FROM customer c
JOIN `orders` o
    ON c.customer_id = o.customer_id
JOIN payment p
    ON o.order_id = p.order_id
GROUP BY c.customer_id, c.name
HAVING SUM(p.amount) > (
    SELECT AVG(customer_spending)
    FROM (
        SELECT SUM(p2.amount) AS customer_spending
        FROM `orders` o2
        JOIN payment p2
            ON o2.order_id = p2.order_id
        GROUP BY o2.customer_id
    ) AS spending
);