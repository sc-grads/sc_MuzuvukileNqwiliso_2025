USE ShopDB
GO

CREATE TABLE #TempOrders (
    OrderID INT PRIMARY KEY,
    CustomerID INT,
    TotalPrice DECIMAL(10,2),
    PaymentMethod NVARCHAR(50),
    CHECK (TotalPrice > 0),
    FOREIGN KEY (CustomerID) REFERENCES store.Customers(CustomerID)
);

INSERT INTO #TempOrders (OrderID, CustomerID, TotalPrice, PaymentMethod)
VALUES (1, 100, 250.00, 'Card'),
       (2, 101, 150.00, 'Cash');

SELECT * FROM #TempOrders;

-- drop the table after use or if you don't it will automatically drop
DROP TABLE #TempOrders;
