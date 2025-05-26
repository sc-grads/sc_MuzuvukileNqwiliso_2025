CREATE CLUSTERED INDEX idx_tblEmployee ON [dbo].[tblEmployee]([EmployeeNumber]);

DROP INDEX idx_tblEmployee ON [dbo].[tblEmployee];

SELECT * FROM [dbo].[tblEmployee2] WHERE [EmployeeNumber] = 127;
SELECT * FROM [dbo].[tblEmployee2];

SELECT *
INTO [dbo].[tblEmployee2]
FROM [dbo].[tblEmployee]
WHERE EmployeeNumber <> 131;

ALTER TABLE [dbo].[tblEmployee2]
ADD CONSTRAINT pk_tblEmployee2 PRIMARY KEY(EmployeeNumber);

CREATE TABLE myTable (Field1 INT PRIMARY KEY);

SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    user_seeks,
    user_scans,
    user_lookups,
    user_updates
FROM sys.indexes i
INNER JOIN sys.dm_db_index_usage_stats s ON i.object_id = s.object_id AND i.index_id = s.index_id
WHERE OBJECT_NAME(i.object_id) IN ('tblEmployee', 'tblEmployee2', 'myTable');

create nonclustered index idx_tblEmployee_DateOfBirth on [dbo].[tblEmployee]([DateOfBirth])
create nonclustered index idx_tblEmployee_DateOfBirth_Department on [dbo].[tblEmployee]([DateOfBirth],Department)

drop index idx_tblEmployee on [dbo].[tblEmployee]

select * from [dbo].[tblEmployee2] where [EmployeeNumber] = 127
select * from [dbo].[tblEmployee2]

select DateOfBirth, Department
from [dbo].[tblEmployee]
where DateOfBirth>='1992-01-01' and DateOfBirth<'1993-01-01'

--seek = few number of rows based on the index
--scan = going through the entire table

alter table [dbo].[tblDepartment]
add constraint unq_tblDepartment UNIQUE(Department)
