USE [70-461];

-- Create a copy of tblEmployee called tblEmpoyee2
SELECT * 
INTO tblEmpoyee2 
FROM [dbo].tblEmployee;

-- View data (optional)
SELECT * FROM [dbo].tblTransaction;
SELECT * FROM [dbo].tblDepartment;

SELECT EmployeeFirstName FROM [dbo].tblEmployee
UNION 
SELECT EmployeeFirstName FROM [dbo].tblEmpoyee2;

-- Unique values only

SELECT EmployeeFirstName FROM [dbo].tblEmployee
UNION ALL
SELECT EmployeeFirstName FROM [dbo].tblEmpoyee2;

-- Includes duplicates

SELECT EmployeeFirstName FROM [dbo].tblEmployee
INTERSECT
SELECT EmployeeFirstName FROM [dbo].tblEmpoyee2;

-- Common distinct values

SELECT EmployeeFirstName FROM [dbo].tblEmployee
EXCEPT
SELECT EmployeeFirstName FROM [dbo].tblEmpoyee2;

-- Values only in the first query
select *, Row_Number() over(order by (select null)) % 3 as ShouldIDelete
--into tblTransactionNew
from tblTransaction

delete from tblTransactionNew
where ShouldIDelete = 1

update tblTransactionNew
set DateOfTransaction = dateadd(day,1,DateOfTransaction)
Where ShouldIDelete = 2

alter table tblTransactionNew
drop column ShouldIDelete

select * from tblTransaction -- 2486 rows
intersect--except--union--union all
select * from tblTransactionNew -- 1657 rows, 829 changed rows, 828 unchanged
order by EmployeeNumber


SELECT DISTINCT EmployeeFirstName from [dbo].[tblEmployee] where [EmployeeFirstName] like 'Y%'
EXCEPT
SELECT DISTINCT EmployeeFirstName from [dbo].[tblEmployee] where [EmployeeFirstName] like 'YA%'

select  Row_Number() over(order by (select null)) % 3  from tblTransaction