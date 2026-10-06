USE multivendor_ecommerce_db;

SELECT
    c.category_id,
    c.category_name,
    AVG(p.price) AS average_product_price
FROM category c
JOIN product p
    ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_name;