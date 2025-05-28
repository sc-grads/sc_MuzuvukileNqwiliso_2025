use [70-461];
go
if OBJECT_ID('GetUserFullName',N'FN') is not null
   DROP FUNCTION GetUserFullName
go

CREATE FUNCTION [dbo].GetUserFullName  -- this must return one value - scalar function
(
    @employeeNumber int
)
RETURNS VARCHAR(50)
AS
BEGIN
    DECLARE @Name Varchar(50);
    SELECT @Name =  EmployeeFirstName + ' '+ EmployeeLastName  FROM tblEmployee WHERE EmployeeNumber = @employeeNumber
	RETURN @Name

END
GO
DECLARE @FullName VARCHAR(50) = [dbo].GetUserFullName(123)
SELECT @FullName AS FullName -- this only return a single value
SELECT name,type_desc
from sys.objects
Where type_desc like '%FUNCTION%'


GO
IF OBJECT_ID('GetUserInformation', N'IF') IS NOT NULL
    DROP FUNCTION GetUserInformation;
GO

CREATE FUNCTION [dbo].GetUserInformation
(
    @employeeNumber INT
)
RETURNS TABLE
AS
RETURN
(
    SELECT 
        E.*,
        D.DepartmentHead
    FROM tblEmployee AS E
    INNER JOIN tblDepartment AS D
        ON E.Department = D.Department
    WHERE E.EmployeeNumber = @employeeNumber
);

GO
SELECT * from [dbo].GetUserInformation(123)
SELECT name, type_desc 
FROM sys.objects
WHERE type_desc LIKE '%FUNCTION%'
GO 

CREATE FUNCTION [dbo].[FunctionName] -- i don't know it yet here.
(
    @param1 int,
    @param2 char(5)
)
RETURNS @returntable TABLE 
(
	[c1] int,
	[c2] char(5)
)
AS
BEGIN
    INSERT @returntable
    SELECT @param1, @param2
    RETURN 
END



