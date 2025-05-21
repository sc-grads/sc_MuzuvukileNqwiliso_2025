 -- CONSTRAINTS
 SELECT * 
INTO newEmployees
FROM [dbo].[tblEmployee];

ALTER TABLE [dbo].[tblEmployee]
ADD CONSTRAINT DF_EmployeeDateOfBirth 
DEFAULT (YEAR(GETDATE())) 
FOR EmployeeDateOfBirth;
