SELECT *
FROM Payments
WHERE amount > (
    SELECT AVG(amount)
    FROM Payments
);
