/* Display all payments made using credit card. */
SELECT *
FROM payment
WHERE mode = 'Credit Card';