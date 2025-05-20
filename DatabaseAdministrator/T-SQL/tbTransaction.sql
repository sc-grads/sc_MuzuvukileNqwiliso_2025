USE [70-461]
GO
CREATE TABLE tbTransactions(
TransactionID int Primary Key Not NUll IDENTITY(0,1),
Amount	smallmoney NOT NULL,
DateOfTransaction	smalldatetime,
EmployeeNumber int 
FOREIGN KEY(EmployeeNumber) REFERENCES tbEmployees(EmployeeNumber)
)
