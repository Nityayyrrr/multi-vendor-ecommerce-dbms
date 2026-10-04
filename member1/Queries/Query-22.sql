SELECT
    v.vendor_id,
    v.vendor_name
FROM vendor v
WHERE EXISTS (
    SELECT 1
    FROM product p
    WHERE p.vendor_id = v.vendor_id
)
AND NOT EXISTS (
    SELECT 1
    FROM product p
    WHERE p.vendor_id = v.vendor_id
      AND p.price <= 100
);