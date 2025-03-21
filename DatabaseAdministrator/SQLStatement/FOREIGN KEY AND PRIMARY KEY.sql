CREATE DATABASE Store;

USE Store

-- THIS COMMAND CREATES TABLE 
-- IT DEFINES THE DATABASE MEANING IT DEFINES DATA TYPES OF THE ATTRIBUTES AND 
-- CONTRAINTS THAT MUST BE MET BY THE ENTITY OR BY THE TABLE
CREATE TABLE Customers(
CustomerID INT IDENTITY(1,1),
FirstName VARCHAR(50) NOT NULL,
LastName VARCHAR(50) NOT NULL,
Email VARCHAR(50) NOT NULL UNIQUE,
City VARCHAR(50) NOT NULL
-- THE BOLOW LINE IS A PRIMARY KEY OF THE TABLE, EACH ROW OR RECORD WILL BE DETERMINE BY IT'S OWN
-- KEY THAT IS DEFFERENT FROM THE OTHER RECORD
-- RECORD 1: CustomerID = 1 | FirstName = 'Anele'| LastName = 'Nzimakhwe' | Email ='exampl1@gmail.com'| City = 'Bizana'
-- RECORD 2 : CustomerID = 2 | FirstName = 'James'| LastName = 'Rogrigez' | Email ='example2@gmail.com'| City = 'Johannesburg'
-- IF YOU SEE ABOVE THE TWO RECORDS ID'S ARE DIFFERENT OR UNIQUE FROM THE OTHER
-- IT'S NOT A MUST FOR THE PRIMARY KEY TO BE A NUMBER YOU CAN USE ANYTHING THAT UNIQUETLY DEFINES A RECORD FROM THE OTHER
-- YOU CAN USE AN EMAIL, EMAIL ARE UNIQUE IN EACH PERSON
PRIMARY KEY(CustomerID)
);

-- THIS IS THE SECOND TABLE WHICH IS THE CHILD OF THE CUSTOMER TABLE
-- THIS TABLE IS GOING HAVE A NEW KEY TYPE WHICH IS FOREIGN KEY THAT REFERENCES TO CUSTOMER TABLE, 
-- REFERENCING USING CUSTOMERID THAT IS IN THE CUSTOMER TABLE 
-- THIS TABLE MUST HAVE A ATTRIBUTE THAT IS GOING TO STORE THE PRIMARY KEY ITS PARENT WHICH IS THE CUSTOMER ID
CREATE TABLE Orders(
OrdersID INT IDENTITY(1,1),
CustomerID INT NOT NULL,
OrderDate DATE NOT NULL,
OrderPrice DECIMAL(10,2)
-- THE BELOW IS THE FOREIGN KEY IT DEFINES THE RELATIONSHIP BETWEEN THE TWO TABLES THE ABOVE ONE AND THIS ONE. 
FOREIGN KEY(CustomerID) REFERENCES Customers(CustomerID),
-- THIS TABLE I DON'T HAVE PRIMARY KEY 
-- I WILL USE ALTER TO INSERT IT
);

ALTER TABLE Orders ADD PRIMARY KEY(OrdersID)

CREATE TABLE Orders_Items(
order_item_id INT IDENTITY(1,1) PRIMARY KEY,
order_id INT NOT NULL,
order_date DATE NOT NULL
FOREIGN KEY(order_id) REFERENCES Orders(OrdersID)
);

ALTER TABLE orders_Items ADD  item_id INT NOT NULL;
