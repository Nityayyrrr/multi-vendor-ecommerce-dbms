SELECT c.customer_id, c.email
FROM Customers c
WHERE NOT EXISTS (
    SELECT 1
    FROM Products p
    WHERE p.category_id = 3
      AND NOT EXISTS (
          SELECT 1
          FROM Orders o
          JOIN Order_Items oi
              ON o.order_id = oi.order_id
          WHERE o.customer_id = c.customer_id
            AND oi.product_id = p.product_id
      )
);
