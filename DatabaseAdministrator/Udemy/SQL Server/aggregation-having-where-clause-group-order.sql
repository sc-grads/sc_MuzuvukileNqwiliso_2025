
SELECT CustomerID, COUNT(OrderID) AS TotalOrders, SUM(TotalPrice) AS TotalSpent
FROM store.Orders
WHERE TotalPrice > 100
GROUP BY CustomerID
ORDER BY TotalSpent DESC;


SELECT ProductID, SUM(Stock) AS TotalStock
FROM store.Products
GROUP BY ProductID
HAVING SUM(Stock) > 50
ORDER BY TotalStock ASC;


SELECT CustomerID, AVG(TotalPrice) AS AvgOrderPrice
FROM store.Orders
WHERE OrderDate >= '2025-01-01'
GROUP BY CustomerID
HAVING AVG(TotalPrice) > 500
ORDER BY AvgOrderPrice DESC;
