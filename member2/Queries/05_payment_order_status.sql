USE multivendor_ecommerce_db;

SELECT
    p.payment_id,
    p.order_id,
    p.status
FROM payment p;