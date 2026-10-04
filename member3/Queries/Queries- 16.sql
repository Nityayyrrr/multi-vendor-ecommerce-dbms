SELECT category_id, AVG(price) AS avg_price
FROM PRODUCT
GROUP BY category_id
ORDER BY avg_price DESC
LIMIT 1;
