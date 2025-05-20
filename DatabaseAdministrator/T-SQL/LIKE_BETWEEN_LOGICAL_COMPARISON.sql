SELECT * FROM tbEmployees
GO
SELECT EmployeeFirstName , EmployeeLastName 
FROM tbEmployees
where EmployeeNumber BETWEEN 123 AND  128

GO

SELECT * 
FROM tbEmployees
where EmployeeNumber > 534
GO

SELECT * 
FROM tbEmployees
where EmployeeNumber < 534

GO

SELECT * 
FROM tbEmployees
where EmployeeNumber = 534

GO

SELECT * 
FROM tbEmployees
where EmployeeNumber >= 534

GO

SELECT * 
FROM tbEmployees
where EmployeeFirstName LIKE 'C%' AND EmployeeFirstName LIKE '%e' -- THIS RETRIEVES EMPLOYEES  THAT HAVE FRST NAME THAT START WITH  C AND  ENDS  WITH  E

GO

SELECT * 
FROM tbEmployees
WHERE EmployeeFirstName LIKE '[A-F]%';

GO

SELECT * 
FROM tbEmployees
WHERE EmployeeFirstName LIKE '%[^A-F]%';

GO

SELECT * 
FROM tbEmployees
WHERE EmployeeFirstName LIKE '__C%';


GO 


SELECT * 
FROM tbEmployees
WHERE DateOfBirth IN ('1990-01-01', '2000-01-01')

GO


SELECT TOP 10 
    Department, 
    COUNT(*) AS EmployeeCount
FROM tbEmployees
WHERE DateOfBirth <> '1990-01-01' OR DateOfBirth >= '1990-01-01'
GROUP BY Department
HAVING COUNT(*) > 0;


