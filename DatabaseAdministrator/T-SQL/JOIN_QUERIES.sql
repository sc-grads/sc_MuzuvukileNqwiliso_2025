-- JOIN QUERY

-- TABLES 
SELECT * FROM [dbo].tblEmployee
SELECT * FROM [dbo].tblDepartment
SELECT * FROM [dbo].tblTransaction

SELECT E.EmployeeNumber,
E.EmployeeFirstName As [First Name],
E.EmployeeLastName As [Last Name], E.DateOfBirth As DOB ,
T.Amount, T.DateOfTransaction
FROM [dbo].tblEmployee E
JOIN [dbo].tblTransaction T
ON E.EmployeeNumber = T.EmployeeNumber


SELECT E.EmployeeNumber,
E.EmployeeFirstName As [First Name],
E.EmployeeLastName As [Last Name], E.DateOfBirth As DOB ,
T.Amount, T.DateOfTransaction
FROM [dbo].tblEmployee E
LEFT JOIN [dbo].tblTransaction T
ON E.EmployeeNumber = T.EmployeeNumber


SELECT E.EmployeeNumber,
E.EmployeeFirstName As [First Name],
E.EmployeeLastName As [Last Name], E.DateOfBirth As DOB ,
T.Amount, T.DateOfTransaction
FROM [dbo].tblEmployee E
RIGHT JOIN [dbo].tblTransaction T
ON E.EmployeeNumber = T.EmployeeNumber


SELECT EmployeeNumber 
FROM (SELECT E.EmployeeNumber,
E.EmployeeFirstName As [First Name],
E.EmployeeLastName As [Last Name], E.DateOfBirth As DOB ,
T.Amount, T.DateOfTransaction
FROM [dbo].tblEmployee E
LEFT JOIN [dbo].tblTransaction T
ON E.EmployeeNumber = T.EmployeeNumber
WHERE T.Amount IS NOT NULL)AS newTable
WHERE YEAR(DOB) >= YEAR('1980-01-01')

