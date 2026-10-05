USE multivendor_ecommerce_db;

SELECT
    v.vendor_id,
    v.vendor_name,
    COUNT(p.product_id) AS product_count
FROM vendor v
LEFT JOIN product p
    ON v.vendor_id = p.vendor_id
GROUP BY
    v.vendor_id,
    v.vendor_name;