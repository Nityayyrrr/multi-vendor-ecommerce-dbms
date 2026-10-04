SELECT p.*
FROM PRODUCT p
WHERE NOT EXISTS (
    SELECT 1
    FROM INVENTORY i
    WHERE i.product_id = p.product_id
);
