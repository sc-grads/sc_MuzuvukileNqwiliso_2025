-- DELETE column

begin transaction -- this stores the deleted coluumn in a temp memory

select count(*) from tblTransaction

delete tblTransaction -- delete from table - this is the right table that we are deleting to
from tblEmployee as E
right join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
where E.EmployeeNumber is null

select count(*) from tblTransaction

rollback transaction -- this undoes the delete

begin transaction
select count(*) from tblTransaction

delete tblTransaction
from tblTransaction
where EmployeeNumber IN
(select TNumber
from (
select E.EmployeeNumber as ENumber, E.EmployeeFirstName,
       E.EmployeeLastName, T.EmployeeNumber as TNumber, 
       sum(T.Amount) as TotalAmount
from tblEmployee as E
right join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
group by E.EmployeeNumber, T.EmployeeNumber, E.EmployeeFirstName,
       E.EmployeeLastName) as newTable
where ENumber is null)
select count(*) from tblTransaction
rollback tran
select count(*) from tblTransaction


select * from tblEmployee where EmployeeNumber = 194
select * from tblTransaction where EmployeeNumber = 3
select * from tblTransaction where EmployeeNumber = 194

begin tran
-- select * from tblTransaction where EmployeeNumber = 194

update tblTransaction
set EmployeeNumber = 194
output inserted.EmployeeNumber, deleted.EmployeeNumber
from tblTransaction
where EmployeeNumber in (3, 5, 7, 9)

insert into tblTransaction
go
delete tblTransaction
from tblTransaction
where EmployeeNumber = 3

-- select * from tblTransaction where EmployeeNumber = 194
rollback tran
