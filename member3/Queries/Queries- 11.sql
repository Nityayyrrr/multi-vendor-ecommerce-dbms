USE multivendor_ecommerce_db;

-- Query 11: Customers who have purchased products across specified category
SELECT c.customer_id, c.email
FROM customer c
WHERE NOT EXISTS (
    SELECT 1
    FROM product p
    WHERE p.category_id = 3
      AND NOT EXISTS (
          SELECT 1
          FROM orders o
          JOIN order_item oi
              ON o.order_id = oi.order_id
          WHERE o.customer_id = c.customer_id
            AND oi.product_id = p.product_id
      )
);
