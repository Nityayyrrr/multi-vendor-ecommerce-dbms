SELECT w.warehouse_id, w.location, i.product_id, i.stock_quantity
FROM warehouse w
LEFT JOIN inventory i
ON w.warehouse_id = i.warehouse_id;