SELECT *
FROM PRODUCT
WHERE price > SOME (
    SELECT price
    FROM PRODUCT
    WHERE category_id = 5
);
