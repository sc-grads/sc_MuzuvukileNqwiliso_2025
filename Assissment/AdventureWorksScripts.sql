USE AdventureWorks2022

 -- 1. Write a query in SQL to retrieve all rows and columns from the employee table in the
 -- Adventureworks database. Sort the result set in ascending order on jobtitle.
SELECT * FROM HumanResources.Employee
ORDER BY JobTitle ASC

--  2. Write a query in SQL to retrieve all rows and columns from the employee table using table
--  aliasing in the Adventureworks database. Sort the output in ascending order on lastname
SELECT *
FROM Person.Person p
ORDER BY P.LastName ASC

--  3. Write a query in SQL to return all rows and a subset of the columns (FirstName, LastName,
--  businessentityid) from the person table in the AdventureWorks database. The third column
--  heading is renamed to Employee_id. Arranged the output in ascending order by lastname
SELECT P.FirstName, P.LastName,
P.BusinessEntityID AS Employee_id
FROM Person.Person P
ORDER BY P.LastName ASC

-- 4. Write a query in SQL to return only the rows for product that have a sellstartdate that is not
-- NULL and a productline of 'T'. Return productid, productnumber, and name. Arranged the
-- output in ascending order on name
SELECT P.ProductID, P.ProductNumber, P.[Name]
FROM Production.Product P
WHERE P.SellStartDate IS NOT NUll AND P.ProductLine = 'T'

 -- 5. Write a query in SQL to return all rows from the salesorderheader table in Adventureworks
 -- database and calculate the percentage of tax on the subtotal have decided. Return
 -- salesorderid, customerid, orderdate, subtotal, percentage of tax column. Arranged the result
 -- set in ascending order on subtotal
 SELECT 
    SalesOrderID,
    CustomerID,
    OrderDate,
    SubTotal,
    (TaxAmt / SubTotal) * 100 AS Tax_Percentage
FROM Sales.SalesOrderHeader
ORDER BY SubTotal ASC

-- 6. Write a query in SQL to create a list of unique jobtitles in the employee table in
-- Adventureworks database. Return jobtitle column and arranged the resultset in ascending
-- order.
SELECT
DISTINCT H.JobTitle
FROM  HumanResources.Employee H
ORDER BY H.JobTitle ASC

-- 7. Write a query in SQL to calculate the total freight paid by each customer. Return customerid
-- and total freight. Sort the output in ascending order on customerid.
SELECT
CustomerID,
SUM(Freight) AS Total_Freight
FROM Sales.SalesOrderHeader
GROUP BY CustomerID
ORDER BY CustomerID ASC
                 
 -- 8. Write a query in SQL to find the average and the sum of the subtotal for every customer.
 -- Return customerid, average and sum of the subtotal. Grouped the result on customerid and
 -- salespersonid. Sort the result on customerid column in descending order.
SELECT 
S.CustomerID,
S.SalesPersonID,
AVG(S.SubTotal) AS Avg_Subtotal,
SUM(S.SubTotal) AS Sum_SubTotal
FROM Sales.SalesOrderHeader  S
GROUP BY S.CustomerID, S.SalesPersonID
ORDER BY S.CustomerID DESC
                                       
-- 9. Write a query in SQL to retrieve total quantity of each productid which are in shelf of 'A' or 'C'
-- or 'H'. Filter the results for sum quantity is more than 500. Return productid and sum of the
-- quantity. Sort the results according to the productid in ascending order
SELECT 
P.ProductID,
SUM(P.Quantity) AS Total_Quantity
FROM Production.ProductInventory P
WHERE P.Shelf IN ('A', 'C', 'H')
GROUP BY P.ProductID
HAVING SUM(P.Quantity) > 500

-- 10. Write a query in SQL to find the total quentity for a group of locationid multiplied by 10.
SELECT 
SUM(P.Quantity) 
AS Total_Quantity
FROM Production.ProductInventory P
GROUP BY P.LocationID * 10

-- 11. Write a query in SQL to find the persons whose last name starts with letter 'L'. Return
-- BusinessEntityID, FirstName, LastName, and PhoneNumber. Sort the result on lastname and
-- firstname
SELECT 
P.BusinessEntityID,
P.FirstName,
P.LastName,
PP.PhoneNumber AS Person_Phone
FROM Person.Person P
JOIN Person.PersonPhone PP
ON PP.BusinessEntityID = P.BusinessEntityID
WHERE LEFT(P.LastName,1) = 'L'
ORDER BY P.LastName, P.FirstName

-- 12.  Write a query in SQL to find the sum of subtotal column. Group the sum on distinct
-- salespersonid and customerid. Rolls up the results into subtotal and running total. Return
-- salespersonid, customerid and sum of subtotal column i.e. sum_subtotal.
SELECT 
S.SalesPersonID,
S.CustomerID,
SUM(S.SubTotal) AS Sum_Subtotal
FROM Sales.SalesOrderHeader S
WHERE S.SalesPersonID IS NOT NULL 
GROUP BY ROLLUP(S.SalesPersonID, S.CustomerID)
ORDER BY S.SalesPersonID, S.CustomerID

-- 13. Write a query in SQL to find the sum of the quantity of all combination of group of distinct
-- locationid and shelf column. Return locationid, shelf and sum of quantity as TotalQuantity.
SELECT 
P.LocationID, 
P.Shelf,
SUM(P.Quantity) AS TotalQuantity
FROM Production.ProductInventory P
GROUP BY ROLLUP(P.LocationID, P.Shelf)
ORDER BY P.LocationID, P.Shelf

-- 14. Write a query in SQL to find the sum of the quantity with subtotal for each locationid. Group
-- the results for all combination of distinct locationid and shelf column. Rolls up the results into
-- subtotal and running total. Return locationid, shelf and sum of quantity as TotalQuantity.
SELECT 
P.LocationID, 
P.Shelf,
SUM(P.Quantity) AS TotalQuantity
FROM Production.ProductInventory P
GROUP BY ROLLUP(P.LocationID, P.Shelf)
ORDER BY P.LocationID, P.Shelf;


-- 15. Write a query in SQL to find the total quantity for each locationid and calculate the grand
-- total for all locations. Return locationid and total quantity. Group the results on locationid
SELECT 
P.LocationID,
SUM(P.Quantity) AS TotalQuantity
FROM Production.ProductInventory P
GROUP BY ROLLUP(P.LocationID)
ORDER BY P.LocationID;


 -- 16. Write a query in SQL to retrieve the number of employees for each City. Return city and
 -- number of employees. Sort the result in ascending order on city
SELECT 
A.City, 
COUNT(A.City) AS NoOfEmployee
FROM Person.Address A
GROUP BY A.City
ORDER BY A.City ASC

-- 17. Write a query in SQL to retrieve the total sales for each year. Return the year part of order
-- date and total due amount. Sort the result in ascending order on year part of order date
SELECT 
DATEPART(YEAR,S.OrderDate) AS Year,
SUM(S.TotalDue) AS [Order Amount]
FROM Sales.SalesOrderHeader S
GROUP BY DATEPART(YEAR,S.OrderDate)
ORDER BY DATEPART(YEAR,S.OrderDate) ASC

-- 18. Write a query in SQL to retrieve the total sales for each year. Filter the result set for those
-- orders where order year is on or before 2016. Return the year part of orderdate and total due
-- amount. Sort the result in ascending order on year part of order date
SELECT 
DATEPART(YEAR,S.OrderDate) AS Year,
SUM(S.TotalDue) AS [Order Amount]
FROM Sales.SalesOrderHeader S
WHERE TRY_CONVERT(INT,DATEPART(YEAR,S.OrderDate)) < 2016
GROUP BY DATEPART(YEAR,S.OrderDate)
ORDER BY DATEPART(YEAR,S.OrderDate) ASC

-- 19. Write a query in SQL to find the contacts who are designated as a manager in various
-- departments. Returns ContactTypeID, name. Sort the result set in descending order
SELECT C.ContactTypeID, C.Name
FROM Person.ContactType C
WHERE C.Name LIKE '%Manager'
ORDER BY C.Name DESC

-- 20. From the following tables write a query in SQL to make a list of contacts who are designated
-- as 'Purchasing Manager'. Return BusinessEntityID, LastName, and FirstName columns. Sort
-- the result set in ascending order of LastName, and FirstName
SELECT P.BusinessEntityID, P.LastName, P.FirstName
FROM Person.Person P
INNER JOIN Person.BusinessEntityContact BC
ON P.BusinessEntityID = BC.BusinessEntityID
INNER JOIN Person.ContactType C
ON BC.ContactTypeID = C.ContactTypeID
WHERE C.Name = 'Purchasing Manager'
ORDER BY P.LastName, P.FirstName;

-- 21. Write a query in SQL to retrieve the salesperson for each PostalCode who belongs to a
-- territory and SalesYTD is not zero. Return row numbers of each group of PostalCode, last
-- name, salesytd, postalcode column. Sort the salesytd of each postalcode group in
-- descending order. Shorts the postalcode in ascending order
SELECT
ROW_NUMBER() OVER (
PARTITION BY A.PostalCode
ORDER BY SP.SalesYTD DESC) AS RowNumber,
P.LastName,
SP.SalesYTD,
A.PostalCode
FROM Sales.SalesPerson SP
INNER JOIN Person.Person P
ON P.BusinessEntityID = SP.BusinessEntityID
INNER JOIN Person.BusinessEntityAddress BEA
ON BEA.BusinessEntityID = SP.BusinessEntityID
INNER JOIN Person.Address A
ON A.AddressID = BEA.AddressID
WHERE SP.SalesYTD > 0
ORDER BY A.PostalCode ASC, SP.SalesYTD DESC;

-- 22.Write a query in SQL to count the number of contacts for combination of each type and
-- name. Filter the output for those who have 100 or more contacts. Return ContactTypeID and
-- ContactTypeName and BusinessEntityContact. Sort the result set in descending order on
-- number of contacts

SELECT
C.ContactTypeID,
C.Name AS ContactTypeName,
COUNT(*) AS NoContacts
FROM Person.BusinessEntityContact BC
INNER JOIN Person.ContactType C
ON C.ContactTypeID = BC.ContactTypeID
GROUP BY C.ContactTypeID, C.Name
HAVING COUNT(*) >= 100
ORDER BY NoContacts DESC;

-- 23. Write a query in SQL to retrieve the RateChangeDate, full name (first name, middle name and
-- last name) and weekly salary (40 hours in a week) of employees. In the output the
-- RateChangeDate should appears in date format. Sort the output in ascending order on
-- NameInFull
SELECT
CONVERT(date, ER.RateChangeDate) AS FromDate,
P.LastName + ', ' +
P.FirstName + 
ISNULL(' ' + P.MiddleName, '') AS NameInFull,
ER.Rate * 40 AS SalaryInAWeek
FROM HumanResources.EmployeePayHistory ER
INNER JOIN Person.Person P
ON P.BusinessEntityID = ER.BusinessEntityID
ORDER BY NameInFull ASC;


-- 24. Write a query in SQL to calculate and display the latest weekly salary of each employee.
-- Return RateChangeDate, full name (first name, middle name and last name) and weekly
-- salary (40 hours in a week) of employees Sort the output in ascending order on NameInFull
SELECT
    CONVERT(date, ER.RateChangeDate) AS RateChangeDate,
    P.LastName + ', ' + P.FirstName + 
        ISNULL(' ' + P.MiddleName, '') AS NameInFull,
    ER.Rate * 40 AS SalaryInAWeek
FROM HumanResources.EmployeePayHistory ER
INNER JOIN Person.Person P
    ON P.BusinessEntityID = ER.BusinessEntityID
ORDER BY NameInFull ASC;



-- 25 Write a query in SQL to find the sum, average, count, minimum, and maximum order quentity
-- for those orders whose id are 43659 and 43664. Return SalesOrderID, ProductID, OrderQty,
-- sum, average, count, max, and min order quantity.
SELECT
SalesOrderID,
ProductID,
OrderQty,
SUM(OrderQty) AS SumQty,
AVG(OrderQty) AS AvgQty,
COUNT(*)    AS CntQty,
MAX(OrderQty) AS MaxQty,
MIN(OrderQty) AS MinQty
FROM Sales.SalesOrderDetail
WHERE SalesOrderID = 99999
;
