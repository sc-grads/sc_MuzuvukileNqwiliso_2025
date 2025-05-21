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



SELECT 
    e.EmployeeNumber, 
    e.EmployeeFirstName, 
    e.EmployeeLastName, 
    SUM(t.Amount) AS SumOfAmount
FROM 
    [dbo].tblEmployee e
LEFT JOIN 
    tblTransaction t ON e.EmployeeNumber = t.EmployeeNumber
GROUP BY 
    e.EmployeeNumber, 
    e.EmployeeFirstName, 
    e.EmployeeLastName
ORDER BY 
    e.EmployeeNumber;


select * from tblEmployee 

select * from tblTransaction where EmployeeNumber = 1046


select Department as NumberOfDepartments
into tblDepartment2
from
(select Department, count(*) as NumberPerDepartment
from tblEmployee
GROUP BY Department) as newTable

--derived table

select distinct Department, convert(varchar(20), N'') as DepartmentHead
into tblDepartment3
from tblEmployee

drop table tblDepartment3

select * from tblDepartment3

alter table tblDepartment
alter column DepartmentHead varchar(30) null
