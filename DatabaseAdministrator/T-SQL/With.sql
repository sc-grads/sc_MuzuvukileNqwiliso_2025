WITH tblWithRanking AS (
    SELECT 
        D.Department, 
        E.EmployeeNumber, 
        E.EmployeeFirstName, 
        E.EmployeeLastName,
        RANK() OVER(PARTITION BY D.Department ORDER BY E.EmployeeNumber) AS TheRank
    FROM tblDepartment AS D 
    JOIN tblEmployee AS E 
        ON D.Department = E.Department
), Transaction2014 as (Select * from tblTransaction where DateOfTransaction between '20131231' and '20150101' and Amount is not null and DateOfTransaction is not null and EmployeeNumber is not null)

SELECT * 
FROM tblWithRanking AS R
LEFT JOIN Transaction2014 AS T
ON T.EmployeeNumber = R.EmployeeNumber
WHERE TheRank <= 5
ORDER BY Department, R.EmployeeNumber;
