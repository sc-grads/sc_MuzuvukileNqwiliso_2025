BEGIN TRAN
DELETE T
FROM tblTransaction AS T
LEFT JOIN tblEmployee AS E
    ON T.EmployeeNumber = E.EmployeeNumber
WHERE E.EmployeeNumber IS NULL;
ROLLBACK TRAN



SELECT T.*
FROM tblTransaction T
LEFT JOIN tblEmployee E
  ON T.EmployeeNumber = E.EmployeeNumber
WHERE E.EmployeeNumber IS NULL
ORDER BY T.EmployeeNumber

SELECT * FROM tblEmployee WHERE EmployeeNumber BETWEEN 3 and 15

BEGIN TRAN
UPDATE T
SET T.Amount = -9999 -- or any placeholder value
FROM tblTransaction AS T
LEFT JOIN tblEmployee AS E
    ON T.EmployeeNumber = E.EmployeeNumber
WHERE E.EmployeeNumber IS NULL;
ROLLBACK TRAN
