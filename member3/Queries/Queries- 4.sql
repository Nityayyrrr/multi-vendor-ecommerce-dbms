SELECT *
FROM product p
WHERE p.price = (
    SELECT MAX(p2.price)
    FROM product p2
    WHERE p2.category_id = p.category_id
);
