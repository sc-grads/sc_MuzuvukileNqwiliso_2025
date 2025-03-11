INSERT INTO store.Customers (Name, Email, Phone)
VALUES 
('Mampo Doe', 'mampo.doe@example.com', '078-456-7890'),
('Jane Smith', 'jane.smith@example.com', '063-567-8901'),
('Alizwa Hlatywayo', 'alizwa.hlatywayo@example.com', '078-678-9012');

GO

INSERT INTO store.Products (Name, Price, Stock)
VALUES 
('Chair', 150.00, 100),
('Table', 250.00, 50),
('Sofa', 500.00, 30),
('Lamp', 75.00, 200);

GO

INSERT INTO store.Orders (CustomerID, TotalPrice)
VALUES 
(1, 150.00),
(2, 500.00), 
(3, 325.00); 

GO 

INSERT INTO store.Payments (OrderID, Amount, PaymentMethod)
VALUES 
(1, 150.00, 'Card'),
(2, 500.00, 'Cash'),
(3, 325.00, 'Online');
