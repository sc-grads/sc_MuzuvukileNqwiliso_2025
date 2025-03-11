UPDATE store.Payments
SET PaymentMethod = 'Cash'
WHERE Amount < 500;

SELECT * FROM store.Payments