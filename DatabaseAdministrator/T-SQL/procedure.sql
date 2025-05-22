create proc NameEmployees as
begin
	select EmployeeNumber, EmployeeFirstName, EmployeeLastName
	from tblEmployee
end
go
NameEmployees
execute NameEmployees
exec NameEmployees
GO
IF OBJECT_ID('proc_Employee', 'P') IS NOT NULL
    DROP PROCEDURE proc_Employee;
GO

CREATE PROCEDURE proc_Employee 
AS
BEGIN 
    DECLARE @looper INT = 1;

    WHILE @looper <= 5
    BEGIN
        SELECT 
            e.EmployeeFirstName + ' ' + e.EmployeeLastName AS [FullName],
            SUM(t.Amount) AS TotalAmount,
            d.Department,
            d.DepartmentHead
        FROM tblEmployee e
        LEFT JOIN tblTransaction t 
            ON e.EmployeeNumber = t.EmployeeNumber
        JOIN tblDepartment d
            ON e.Department = d.Department
        WHERE t.Amount IS NOT NULL
        GROUP BY 
            e.EmployeeFirstName + ' ' + e.EmployeeLastName, 
            d.Department, 
            d.DepartmentHead;

        SET @looper = @looper + 1;
    END
END
GO

EXEC proc_Employee;

go
-- Drop the procedure if it exists
IF OBJECT_ID('UserProcedure', 'P') IS NOT NULL
    DROP PROC UserProcedure;
GO

-- Create the procedure
CREATE PROC UserProcedure (@firstname VARCHAR(50), @dob int)
AS 
BEGIN 
    IF EXISTS (
        SELECT * 
        FROM tblEmployee 
        WHERE EmployeeFirstName = @firstname 
        AND YEAR(DateOfBirth) = @dob
    )
    BEGIN
        SELECT 
            e.EmployeeFirstName + ' ' + e.EmployeeLastName AS [FullName],
            SUM(t.Amount) AS TotalAmount,
            d.Department,
            d.DepartmentHead
        FROM tblEmployee e
        LEFT JOIN tblTransaction t 
            ON e.EmployeeNumber = t.EmployeeNumber
        JOIN tblDepartment d
            ON e.Department = d.Department
        WHERE e.EmployeeFirstName = @firstname 
        AND YEAR(e.DateOfBirth) = @dob
        GROUP BY 
            e.EmployeeFirstName + ' ' + e.EmployeeLastName, 
            d.Department, 
            d.DepartmentHead;
    END
    ELSE
    BEGIN
        PRINT 'No matching employee found with the given name and birth year.';
    END
END

GO 
EXEC UserProcedure @firstname = 'Ashvini', @dob = 1989;
GO
if object_ID('NameEmployees','P') IS NOT NULL
drop proc NameEmployees
go
create proc NameEmployees(@EmployeeNumberFrom int, @EmployeeNumberTo int) as
begin
	if exists (Select * from tblEmployee where EmployeeNumber between @EmployeeNumberFrom and @EmployeeNumberTo)
begin
		declare @EmployeeNumber int = @EmployeeNumberFrom
		while @EmployeeNumber <= @EmployeeNumberTo
		BEGIN
			if exists (Select * from tblEmployee where EmployeeNumber = @EmployeeNumber)
			select EmployeeNumber, EmployeeFirstName, EmployeeLastName
			from tblEmployee
			where EmployeeNumber = @EmployeeNumber
			SET @EmployeeNumber = @EmployeeNumber + 1
		END
	end
end
go
NameEmployees 4, 5
execute NameEmployees 223, 227
exec NameEmployees @EmployeeNumberFrom = 323, @EmployeeNumberTo = 1327


 select * from tblEmployee where EmployeeFirstName = 'Ashvini'
 select * from tblDepartment
 select * from tblTransaction