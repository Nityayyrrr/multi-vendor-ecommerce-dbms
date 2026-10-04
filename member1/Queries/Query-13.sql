SELECT
    c.category_name,
    p.product_name,
    p.price
FROM product p
JOIN category c
    ON p.category_id = c.category_id
JOIN (
    SELECT category_id, MAX(price) AS max_price
    FROM product
    GROUP BY category_id
) m
    ON m.category_id = p.category_id
   AND m.max_price = p.price;