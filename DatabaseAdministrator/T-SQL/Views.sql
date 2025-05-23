select 1
go
create view ViewByDepartment as 
select D.Department, T.EmployeeNumber, T.DateOfTransaction, T.Amount as TotalAmount
from tblDepartment as D
left join tblEmployee as E
on D.Department = E.Department
left join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
where T.EmployeeNumber between 120 and 139
--order by D.Department, T.EmployeeNumber
go

create view ViewSummary as 
select D.Department, T.EmployeeNumber as EmpNum, sum(T.Amount) as TotalAmount
from tblDepartment as D
left join tblEmployee as E
on D.Department = E.Department
left join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
group by D.Department, T.EmployeeNumber
--order by D.Department, T.EmployeeNumber
go
select * from ViewByDepartment where TotalAmount >1  order by  EmployeeNumber asc
select Department, EmployeeNumber, TotalAmount
from ViewByDepartment
update ViewByDepartment set TotalAmount = 2.77 where EmployeeNumber = 132
select * from ViewSummary

delete from ViewByDepartment where EmployeeNumber = 123
go

CREATE OR  REPLACE VIEW cust_view as 
SELECT * FROM [dbo].tblEmployee
go
-- Drop the view if it exists
IF OBJECT_ID('vwEmployeeDepartment', 'V') IS NOT NULL
    DROP VIEW vwEmployeeDepartment;
GO
-- Create the view
CREATE VIEW vwEmployeeDepartment
AS
SELECT 
    e.EmployeeNumber,
    e.EmployeeFirstName,
    e.EmployeeLastName,
    d.Department
FROM tblEmployee e
JOIN tblDepartment d
    ON e.Department = d.Department;


	-- Drop the view if it exists
IF OBJECT_ID('vwEmployeeDepartment', 'V') IS NOT NULL
    DROP VIEW vwEmployeeDepartment;

-- Create the view
CREATE VIEW vwEmployeeDepartment
AS
SELECT 
    e.EmployeeNumber,
    e.EmployeeFirstName,
    e.EmployeeLastName,
    d.DepartmentName
FROM tblEmployee e
JOIN tblDepartment d
    ON e.DepartmentID = d.DepartmentID;

