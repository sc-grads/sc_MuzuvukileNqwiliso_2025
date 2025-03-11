-- section 6 

-- this script creates database 
CREATE DATABASE ShopDB
GO

-- this script specifies which data to use
USE ShopDB
GO

-- this script create schema 
CREATE SCHEMA store;
GO

CREATE TABLE store.Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Email NVARCHAR(100) UNIQUE NOT NULL,
    Phone NVARCHAR(15) NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

GO 

CREATE TABLE store.Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Stock INT NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE store.Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL,
    OrderDate DATETIME DEFAULT GETDATE(),
    TotalPrice DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES store.Customers(CustomerID)
);
GO 

CREATE TABLE store.Payments (
    PaymentID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL,
    PaymentDate DATETIME DEFAULT GETDATE(),
	-- the in hear prevents the user for paying using other thing than cash,card or online
    PaymentMethod NVARCHAR(50) NOT NULL CHECK (PaymentMethod IN ('Cash', 'Card', 'Online')),
    FOREIGN KEY (OrderID) REFERENCES store.Orders(OrderID)
);
