-- Properly check if the table exists
IF OBJECT_ID('newTable', 'U') IS NOT NULL
    DROP TABLE newTable;
GO

-- Begin transaction (any changes can be rolled back)
BEGIN TRAN;

-- Create a new table with a uniqueidentifier column and default newsequentialid()
CREATE TABLE newTable (
    userID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
    userName CHAR(2)
);

-- Insert values into the table
INSERT INTO newTable (userName) VALUES ('u1'), ('u2'), ('u3');

-- View the data
SELECT * FROM newTable;

delete from newTable

-- Rollback the transaction (undo table creation and insertions)
ROLLBACK TRAN;



begin tran
create sequence firstsq as bigint
start with 1
increment by 1
minvalue 1
maxvalue 99999 --- must change thsi to the bigint - so i will comment it.
cycle
cache 50
CREATE SEQUENCE secondSeq AS INT
SELECT * FROM sys.sequences
ROLLBACK TRAN

--- second sequence
begin tran
create sequence secondsq as bigint
start with 1
increment by 1
minvalue 1
cycle
cache 50
select next value for secondsq as nextvalue -- this is the stepping to next value from start value 1,2,3,4
rollback tran

CREATE SEQUENCE newSeq AS BIGINT
START WITH 1
INCREMENT BY 1
MINVALUE 1
--MAXVALUE 999999
--CYCLE
CACHE 50

alter table tblTransaction
ADD NextNumber int CONSTRAINT DF_Transaction DEFAULT NEXT VALUE FOR newSeq

alter table tblTransaction
drop DF_Transaction
alter table tblTransaction
drop column NextNumber

alter table tblTransaction
add NextNumber int
alter table tblTransaction
add CONSTRAINT DF_Transaction DEFAULT NEXT VALUE FOR newSeq for NextNumber

begin tran
select * from tblTransaction
INSERT INTO tblTransaction(Amount, DateOfTransaction, EmployeeNumber)
VALUES (1,'2017-01-01',123)
select * from tblTransaction WHERE EmployeeNumber = 123;

update tblTransaction
set NextNumber = NEXT VALUE FOR newSeq
where NextNumber is null
select * from tblTransaction --WHERE EmployeeNumber = 123
ROLLBACK TRAN

--SET IDENTITY_INSERT tablename ON
--DBCC CHECKIDENT(tablename,RESEED)

alter sequence newSeq
restart with 1

alter table tblTransaction
drop DF_Transaction
alter table tblTransaction
drop column NextNumber
DROP SEQUENCE newSeq


