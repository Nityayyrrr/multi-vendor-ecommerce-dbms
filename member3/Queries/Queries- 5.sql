USE multivendor_ecommerce_db;

-- Query 5: Inventory details with product name, warehouse location, and stock quantity
SELECT 
    p.product_id,
    p.product_name,
    w.location,
    i.stock_quantity
FROM inventory i
JOIN product p
    ON i.product_id = p.product_id
JOIN warehouse w
    ON i.warehouse_id = w.warehouse_id;
