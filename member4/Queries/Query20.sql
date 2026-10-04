/* Display vendors whose rating is greater than at least one other vendor using SOME */
SELECT
    vendor_id,
    vendor_name,
    rating
FROM vendor
WHERE rating > SOME (
    SELECT rating
    FROM vendor
);
