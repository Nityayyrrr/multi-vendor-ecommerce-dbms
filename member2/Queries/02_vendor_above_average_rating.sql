USE multivendor_ecommerce_db;

SELECT
    vendor_id,
    vendor_name,
    rating
FROM vendor
WHERE rating > (
    SELECT AVG(rating)
    FROM vendor
);