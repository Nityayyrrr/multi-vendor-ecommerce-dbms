SELECT
    w.warehouse_id,
    w.location,
    COUNT(*) AS low_stock_products
FROM warehouse w
JOIN inventory i
    ON w.warehouse_id = i.warehouse_id
WHERE i.stock_quantity < i.reorder_level
GROUP BY w.warehouse_id, w.location
ORDER BY low_stock_products DESC
LIMIT 1;