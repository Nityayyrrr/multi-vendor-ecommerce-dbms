USE multivendor_ecommerce_db;

-- Query 2: Payments greater than average payment amount
SELECT *
FROM payment
WHERE amount > (
    SELECT AVG(amount)
    FROM payment
);
