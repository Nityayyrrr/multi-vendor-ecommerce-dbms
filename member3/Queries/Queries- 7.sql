USE multivendor_ecommerce_db;

-- Query 7: Vendors with no products priced under or equal to 100
SELECT v.vendor_id, v.vendor_name
FROM vendor v
WHERE NOT EXISTS (
    SELECT 1
    FROM product p
    WHERE p.vendor_id = v.vendor_id
      AND p.price <= 100
);
