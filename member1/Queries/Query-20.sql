SELECT
    YEAR(order_date) AS order_year,
    COUNT(*) AS total_orders
FROM `orders`
GROUP BY YEAR(order_date)
ORDER BY order_year;