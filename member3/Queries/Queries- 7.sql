SELECT v.vendor_id, v.vendor_name
FROM Vendors v
WHERE NOT EXISTS (
    SELECT 1
    FROM Products p
    WHERE p.vendor_id = v.vendor_id
      AND p.price <= 100
);
