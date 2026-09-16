SELECT *
FROM Products p
WHERE p.price = (
    SELECT MAX(p2.price)
    FROM Products p2
    WHERE p2.category_id = p.category_id
);
