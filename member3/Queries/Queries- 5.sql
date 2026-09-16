SELECT 
    i.inventory_id,
    p.product_name,
    w.location,
    i.quantity
FROM Inventory i
JOIN Products p
    ON i.product_id = p.product_id
JOIN Warehouses w
    ON i.warehouse_id = w.warehouse_id;
