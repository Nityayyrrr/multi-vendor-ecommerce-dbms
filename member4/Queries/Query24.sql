/* Display customers who have never placed an order using NOT EXISTS */
SELECT
    c.customer_id,
    c.name
FROM customer c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);
