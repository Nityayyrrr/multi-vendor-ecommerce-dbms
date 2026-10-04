SELECT 
    MONTH(order_date) AS month,
    COUNT(*) AS total_orders
FROM ORDERS
GROUP BY MONTH(order_date)
ORDER BY month;
