SELECT 
    warehouse_id,
    SUM(quantity) AS total_quantity
FROM Inventory
GROUP BY warehouse_id;
