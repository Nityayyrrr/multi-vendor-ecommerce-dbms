SELECT 
    w.warehouse_id,
    w.location,
    SUM(i.stock_quantity) AS total_quantity
FROM warehouse w
JOIN inventory i
    ON w.warehouse_id = i.warehouse_id
GROUP BY w.warehouse_id, w.location;
