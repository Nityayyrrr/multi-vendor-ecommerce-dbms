USE multivendor_ecommerce_db;

SELECT
    c.customer_id,
    c.email
FROM customer c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.customer_id
);