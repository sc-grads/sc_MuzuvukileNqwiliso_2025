INSERT INTO store.Customers (Name, Email, Phone)
VALUES 
('Mampo Doe', 'mampo.doe@example.com', '078-456-7890'),
('Jane Smith', 'jane.smith@example.com', '063-567-8901'),
('Alizwa Hlatywayo', 'alizwa.hlatywayo@example.com', '078-678-9012');

GO
INSERT INTO store.Products (Name, Price, Stock)
VALUES 
('Dining Table', 800.00, 40),
('Recliner Chair', 1200.00, 25),
('Coffee Table', 350.00, 60),
('Bookshelf', 450.00, 80),
('Wardrobe', 1500.00, 15);
GO

INSERT INTO store.Orders (CustomerID, TotalPrice)
VALUES 
(1, 1200.00),
(2, 2200.00),
(3, 1450.00),
(4, 800.00),
(5, 1800.00);
GO

INSERT INTO store.Payments (OrderID, Amount, PaymentMethod)
VALUES 
(4, 1200.00, 'Online'),
(5, 2200.00, 'Card'),
(6, 1450.00, 'Cash'),
(7, 800.00, 'Card'),
(8, 1800.00, 'Online');
GO



INSERT INTO [ShopDB].[store].[Customers] ([Name], [Email], [Phone], [CreatedAt])
VALUES
('Thabo Mbeki', 'thabo.mbeki@email.com', '071-234-5678', GETDATE()),
('John van der Merwe', 'john.vdm@email.com', '082-345-6789', GETDATE()),
('Naledi Padi', 'naledi.padi@email.com', '076-5432-109', GETDATE()),
('Zanele Khoza', 'zanele.khoza@email.com', '073-876-5432', GETDATE()),
('Kgosi Moloi', 'kgosi.moloi@email.com', '071-987-6543', GETDATE()),
('Mpho Makgoba', 'mpho.makgoba@email.com', '071-2345-679', GETDATE()),
('Sarah de Villiers', 'sarah.devilliers@email.com', '083-456-7890', GETDATE()),
('Ayesha Khan', 'ayesha.khan@email.com', '072-345-6789', GETDATE()),
('Sipho Ndlovu', 'sipho.ndlovu@email.com', '076-543-2178', GETDATE()),
('Johan Botha', 'johan.botha@email.com', '079-876-5432', GETDATE())

