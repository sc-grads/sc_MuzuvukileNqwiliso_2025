SELECT [Status], Count(*) As NumberOfStatus
FROM (SELECT  

    e.EmployeeFirstName AS Firstname,
    e.EmployeeLastName AS LastName,
    t.Amount,
    t.DateOfTransaction,
    CASE 
        WHEN t.Amount < 0 THEN 'Negative'
        ELSE 'Positive'
    END AS [Status]
FROM 
    [dbo].tblEmployee AS e
JOIN 
    [dbo].tblTransaction AS t
    ON e.EmployeeNumber = t.EmployeeNumber) as EmployeeInfo
GROUP BY [Status]

SELECT  

    e.EmployeeFirstName AS Firstname,
    e.EmployeeLastName AS LastName,
    t.Amount,
    t.DateOfTransaction,
    CASE 
        WHEN YEAR(t.DateOfTransaction) = 2015 THEN 'Year- 2015'
		WHEN YEAR(t.DateOfTransaction) = 2014 THEN 'Year- 2014'
        ELSE 'Random year'
    END AS [Years]
FROM 
    [dbo].tblEmployee AS e
JOIN 
    [dbo].tblTransaction AS t
    ON e.EmployeeNumber = t.EmployeeNumber
    