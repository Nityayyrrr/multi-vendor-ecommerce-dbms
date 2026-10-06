USE multivendor_ecommerce_db;

SELECT
    p.product_id,
    p.product_name,
    SUM(oi.quantity) AS total_quantity_purchased
FROM product p
JOIN order_item oi
    ON p.product_id = oi.product_id
GROUP BY
    p.product_id,
    p.product_name
ORDER BY total_quantity_purchased DESC
LIMIT 1;