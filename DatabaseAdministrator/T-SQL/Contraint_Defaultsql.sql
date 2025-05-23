 -- CONSTRAINTS
 SELECT * 
INTO newEmployees
FROM [dbo].[tblEmployee];

ALTER TABLE [dbo].[tblEmployee]
ADD CONSTRAINT DF_EmployeeDateOfBirth 
DEFAULT (YEAR(GETDATE())) 
FOR EmployeeDateOfBirth;

alter table [dbo].[tblEmployee]
add unique (EmployeeFirstName) -- this does not need index

BEGIN TRAN;

ALTER TABLE [dbo].[tblEmployee]
ADD CONSTRAINT uc_EmployeeFullName UNIQUE (EmployeeFirstName, EmployeeLastName);

ROLLBACK TRAN;
 -- the uc_EmployeeFullName is the name of the constraint