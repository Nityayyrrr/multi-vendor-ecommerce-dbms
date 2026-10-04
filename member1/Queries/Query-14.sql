SELECT
    oi.order_id,
    p.product_name,
    oi.quantity,
    oi.price_at_purchase
FROM order_item oi
JOIN product p
    ON oi.product_id = p.product_id;