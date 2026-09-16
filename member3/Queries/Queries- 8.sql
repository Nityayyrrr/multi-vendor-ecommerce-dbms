USE multivendor_ecommerce_db;

-- Query 8: Total inventory quantity grouped by warehouse
SELECT 
    warehouse_id,
    SUM(stock_quantity) AS total_quantity
FROM inventory
GROUP BY warehouse_id;
