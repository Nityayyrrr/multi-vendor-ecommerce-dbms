SELECT 
    o.order_id,
    c.customer_name,
    p.product_name,
    oi.quantity,
    oi.purchase_price
FROM ORDERS o
JOIN CUSTOMER c
    ON o.customer_id = c.customer_id
JOIN ORDER_ITEM oi
    ON o.order_id = oi.order_id
JOIN PRODUCT p
    ON oi.product_id = p.product_id;
