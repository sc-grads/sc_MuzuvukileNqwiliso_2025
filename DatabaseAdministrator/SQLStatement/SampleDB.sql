
-- THIS COMMAND IS USED FOR CREATING DATABSE # DDL COMMAND 
-- THIS COMMAND IS ONLY USED WHEN CREATING TABLE OR DATABASE
-- AFTER CREATING ONE OF THOSE (TABLE OR DATABASE) RUN 'USE DATABSENAME'
CREATE DATABASE SampleDB;

-- THIS COMMAND IS USED FOR SPECIFYING WHICH DATABASE YOU WANT TO WORK WITH
USE SampleDB;

-- THIS COMMAND CREATES TABLE 
-- IT DEFINES THE DATABASE MEANING IT DEFINES DATA TYPES OF THE ATTRIBUTES AND 
-- CONTRAINTS THAT MUST BE MET BY THE ENTITY OR BY THE TABLE
CREATE TABLE Customers(
CustomerID INT IDENTITY(1,1),
FirstName VARCHAR(50) NOT NULL,
LastName VARCHAR(50) NOT NULL,
Email VARCHAR(50) NOT NULL,
City VARCHAR(50) NOT NULL
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
FOREIGN KEY(CustomerID) REFERENCES Customers(CustomerID),
-- THIS TABLE I DONT HAVE PRIMARY KEY 
-- I WILL USE ALTER TO INSERT IT
);

-- THIS IS A DML COMMAND MEANING IT INTERACT WITH THE DATA ITSELF, BY ADDING A RECORD TO THE TABLE
-- WHEN INSERTING OR ADDING A RECORD YOU CAN OMIT THE COLUMNS, IF YOU DO SO MAKE SURE THAT YOU SPECIFY ALL THE COLUMNS ON THE TABLE

INSERT INTO Customers(FirstName,LastName,Email,City) 
VALUES 
('Thabo', 'Mbeki', 'thabo.mbeki@example.com', 'Johannesburg'),
('Jan', 'Van der Merwe', 'jan.vdm@example.com', 'Pretoria'),
('Nomvula', 'Mokonyane', 'nomvula.mokonyane@example.com', 'Durban'),
('Lerato', 'Ndlovu', 'lerato.ndlovu@example.com', 'Cape Town'),
('Kagiso', 'Modise', 'kagiso.modise@example.com', 'Bloemfontein'),
('Zanele', 'Khumalo', 'zanele.khumalo@example.com', 'Port Elizabeth'),
('Mandla', 'Zulu', 'mandla.zulu@example.com', 'Polokwane'),
('Naledi', 'Molefe', 'naledi.molefe@example.com', 'Nelspruit'),
('Tumi', 'Botha', 'tumi.botha@example.com', 'Kimberley'),
('Refilwe', 'Van der Merwe', 'refilwe.vdm@example.com', 'Stellenbosch'),
('Ayanda', 'Dlamini', 'ayanda.dlamini@example.com', 'Johannesburg'),
('Bongani', 'Sithole', 'bongani.sithole@example.com', 'Pretoria'),
('Chris', 'Joubert', 'chris.joubert@example.com', 'Durban'),
('Dineo', 'Mahlangu', 'dineo.mahlangu@example.com', 'Cape Town'),
('Elvis', 'Mthembu', 'elvis.mthembu@example.com', 'Bloemfontein'),
('Fatima', 'Patel', 'fatima.patel@example.com', 'Port Elizabeth'),
('Gugu', 'Nxumalo', 'gugu.nxumalo@example.com', 'Polokwane'),
('Hendrik', 'Steyn', 'hendrik.steyn@example.com', 'Nelspruit'),
('Itumeleng', 'Sephiri', 'itumeleng.sephiri@example.com', 'Kimberley'),
('Jabulani', 'Nkosi', 'jabulani.nkosi@example.com', 'Stellenbosch');



INSERT INTO Orders (CustomerID, OrderDate, OrderPrice)
VALUES
(1, '2023-10-01', 100.50),
(2, '2023-10-02', 200.75),
(3, '2023-10-03', 150.00),
(1, '2023-10-04', 300.25),
(4, '2023-10-05', 50.00),
(5, '2023-10-06', 75.80),
(6, '2023-10-07', 120.00),
(7, '2023-10-08', 90.45),
(8, '2023-10-09', 250.60),
(9, '2023-10-10', 180.30);

-- THIS COMMAND SELECTS EVERY COLUMNS OR IT RETIREVES EVERY INFO IN THE TABLE
SELECT * FROM Customers;

-- THIS COMMAND IS USED AS FILTER, BECAUSE THE USER IS ABLE TO SPECIFY WHAT KIND OF INFORMATION IS H/SHE IS WILLING TO RETURN
SELECT * FROM Customers
WHERE City = 'Johannesburg';

-- YOU CAN USE SELECT TO RETURN SPECIF COLUMNS IN A TABLE 
SELECT FirstName, LastName 
FROM Customers;

-- THIS COMMAND IS USED RETURN SPECIFIC NUMBER OR RECORDS IN TABLE
SELECT TOP 10 *
FROM Customers;

-- THIS COMMAND IS SAME AS TOP BUT IT IS USED WITH ORDER BY COMMAND
SELECT * FROM Customers
ORDER BY FirstName 
OFFSET 17 ROWS FETCH NEXT 1 ROWS ONLY

-- THE FIRST COMMMAD 'OFFEST 17 ROWS' MEANS ROWS TO BE  SKIPPED
-- THE SECOND COMMAND 'FETCH NEXT 1 ROWS ONLY' MEANING RETURN 1 ROW TO BE RETURNED
;

-- ADD A PRIMARY KEY FOR ORDERS TABLE 
-- BUT FIRST MAKE SURE -- 
-- NO DUPLICATES 
-- NO NULLS

ALTER TABLE Orders
ADD CONSTRAINT PK_OrdersID PRIMARY KEY(OrdersID)