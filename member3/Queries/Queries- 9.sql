SELECT 
    w.warehouse_id,
    w.location,
    SUM(i.quantity) AS total_quantity
FROM Warehouses w
JOIN Inventory i
    ON w.warehouse_id = i.warehouse_id
GROUP BY w.warehouse_id, w.location;
