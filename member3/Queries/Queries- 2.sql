SELECT *
FROM payment
WHERE amount > (
    SELECT AVG(amount)
    FROM payment
);
