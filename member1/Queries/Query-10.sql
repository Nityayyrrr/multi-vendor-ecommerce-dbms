SELECT c.customer_id
FROM customer c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_item oi ON o.order_id = oi.order_id
JOIN product p ON oi.product_id = p.product_id
WHERE p.category_id = 5
GROUP BY c.customer_id
HAVING COUNT(DISTINCT p.product_id) = (
    SELECT COUNT(*) FROM product WHERE category_id = 5
);