/* Display each product together with both its vendor and category information.*/

SELECT
    p.product_id,
    p.product_name,
    v.vendor_id,
    v.vendor_name,
    c.category_id,
    c.category_name
FROM product p
JOIN vendor v
    ON p.vendor_id = v.vendor_id
JOIN category c
    ON p.category_id = c.category_id;