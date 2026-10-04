USE multivendor_ecommerce_db;

SELECT
    v.vendor_id,
    v.vendor_name,
    AVG(p.price) AS average_product_price
FROM vendor v
JOIN product p
    ON v.vendor_id = p.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY average_product_price DESC
LIMIT 1;