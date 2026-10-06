USE multivendor_ecommerce_db;

SELECT
    c.customer_id,
    c.email,
    COUNT(o.order_id) AS order_count
FROM customer c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.email;