/* Display products together with their warehouse locations and stock quantities*/
SELECT
    p.product_id,
    p.product_name,
    w.location,
    i.stock_quantity
FROM product p
JOIN inventory i
    ON p.product_id = i.product_id
JOIN warehouse w
    ON i.warehouse_id = w.warehouse_id;