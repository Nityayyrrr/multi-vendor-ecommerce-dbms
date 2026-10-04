SELECT 
    warehouse_id,
    SUM(stock_quantity) AS total_quantity
FROM inventory
GROUP BY warehouse_id;
