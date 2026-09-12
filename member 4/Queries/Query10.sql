/*Display all warehouses along with the number of products stored there.*/
SELECT
    w.warehouse_id,
    w.location,
    COUNT(i.product_id) AS number_of_products
FROM warehouse w
LEFT JOIN inventory i
    ON w.warehouse_id = i.warehouse_id
GROUP BY
    w.warehouse_id,
    w.location;