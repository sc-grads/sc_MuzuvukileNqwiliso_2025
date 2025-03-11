CREATE VIEW ExpensiveOrders AS
SELECT OrderID, CustomerID, TotalPrice
FROM store.Orders
WHERE TotalPrice > 100
