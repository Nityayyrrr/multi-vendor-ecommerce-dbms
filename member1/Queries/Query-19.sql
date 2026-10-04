SELECT
    p.product_id,
    p.product_name
FROM product p
WHERE NOT EXISTS (
    SELECT 1
    FROM warehouse w
    WHERE NOT EXISTS (
        SELECT 1
        FROM inventory i
        WHERE i.product_id = p.product_id
          AND i.warehouse_id = w.warehouse_id
    )
);