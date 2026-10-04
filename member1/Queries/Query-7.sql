SELECT vendor_id, vendor_name, rating
FROM vendor
WHERE rating > ALL (
    SELECT rating
    FROM vendor
    WHERE rating < 3.0
);