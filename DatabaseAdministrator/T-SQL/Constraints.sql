-- constraint 
create table tblConstraint(
   tblPrimary int unique primary key, -- this will generate error you cann't use primary key and unique
  [first name] varchar(20) NOT NULL UNIQUE,
  [date of birth] date default getdate()
)

create table tblConstraint2(
   tblPrimary int primary key, -- this will generate error you cann't use primary key and unique
  [first name] varchar(20) NOT NULL UNIQUE,
  [date of birth] date default getdate(),
  [id number] char(13) default 123456789123 unique,
  [salary] decimal(10,2) check(salary >= 100)
)

-- use alter to insert constraint
alter table tblEmployee
ADD CONSTRAINT unqGovernmentID UNIQUE (EmployeeGovernmentID);

select EmployeeGovernmentID, count(EmployeeGovernmentID) as MyCount from tblEmployee
group by EmployeeGovernmentID
having count(EmployeeGovernmentID)>1

select * from tblEmployee where EmployeeGovernmentID IN ('HN513777D', 'TX593671R')

begin tran
delete from tblEmployee
where EmployeeNumber < 3

delete top(2) from tblEmployee
where EmployeeNumber in (131, 132)

select * from tblEmployee where EmployeeGovernmentID IN ('HN513777D', 'TX593671R')

commit tran

alter table tblTransaction
add constraint unqTransaction UNIQUE (Amount, DateOfTransaction, EmployeeNumber)

delete from tblTransaction
where EmployeeNumber = 131

insert into tblTransaction
VALUES (1,'2015-01-01', 131)
insert into tblTransaction
VALUES (1,'2015-01-01', 131)

alter table tblTransaction
Drop constraint unqTransaction

create table tblTransaction2
(Amount smallmoney not null,
DateOfTransaction smalldatetime not null,
EmployeeNumber int not null,
CONSTRAINT unqTransaction2 UNIQUE (Amount,DateOfTransaction,EmployeeNumber))

drop table tblTransaction2
alter table tblTransaction
add DateOfEntry datetime

alter table tblTransaction
add constraint defDateOfEntry DEFAULT GETDATE() for DateOfEntry;

delete from tblTransaction where EmployeeNumber < 3

insert into tblTransaction(Amount, DateOfTransaction, EmployeeNumber)
values (1, '2014-01-01', 1)
insert into tblTransaction(Amount, DateOfTransaction, EmployeeNumber, DateOfEntry)
values (2, '2014-01-02', 1, '2013-01-01')

select * from tblTransaction where EmployeeNumber < 3

create table tblTransaction2
(Amount smallmoney not null,
DateOfTransaction smalldatetime not null,
EmployeeNumber int not null,
DateOfEntry datetime null CONSTRAINT tblTransaction2_defDateOfEntry DEFAULT GETDATE())

insert into tblTransaction2(Amount, DateOfTransaction, EmployeeNumber)
values (1, '2014-01-01', 1)
insert into tblTransaction2(Amount, DateOfTransaction, EmployeeNumber, DateOfEntry)
values (2, '2014-01-02', 1, '2013-01-01')

select * from tblTransaction2 where EmployeeNumber < 3

drop table tblTransaction2

alter table tblTransaction
drop column DateOfEntry

alter table tblTransaction
drop constraint defDateOfEntry

BEGIN TRAN

ALTER TABLE tblTransaction
ADD DateOfEntry datetime
DEFAULT GETDATE() WITH VALUES

SELECT * FROM tblTransaction

ROLLBACK TRAN
