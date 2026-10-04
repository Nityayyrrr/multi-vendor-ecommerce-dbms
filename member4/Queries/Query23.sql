/* Display products whose price is greater than the average price of products in the same category */
SELECT
    p.product_id,
    p.product_name,
    p.category_id,
    p.price
FROM product p
WHERE p.price > (
    SELECT AVG(p2.price)
    FROM product p2
    WHERE p2.category_id = p.category_id
);
