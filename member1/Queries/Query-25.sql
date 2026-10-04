SELECT
    o.order_id,
    COALESCE(i.item_total, 0) AS item_total,
    COALESCE(p.payment_total, 0) AS payment_total
FROM `orders` o
LEFT JOIN (
    SELECT order_id,
           SUM(quantity * price_at_purchase) AS item_total
    FROM order_item
    GROUP BY order_id
) i ON o.order_id = i.order_id
LEFT JOIN (
    SELECT order_id,
           SUM(amount) AS payment_total
    FROM payment
    GROUP BY order_id
) p ON o.order_id = p.order_id
WHERE ABS(
    COALESCE(i.item_total, 0) -
    COALESCE(p.payment_total, 0)
) > 0.01;