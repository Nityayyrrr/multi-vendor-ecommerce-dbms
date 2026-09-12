/*Find the minimum and maximum product prices*/

SELECT 
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price
FROM product;