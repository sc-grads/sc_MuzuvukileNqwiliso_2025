create trigger trigger_tblTransaction
on tblTransaction
after delete,insert, update
as
begin
select * from inserted
select * from Deleted
end
go


begin tran
update tblTransaction set Amount = FLOOR(Amount) where EmployeeNumber = 804
rollback tran
go

begin tran
delete from tblTransaction where EmployeeNumber = 804
rollback tran
go

select * from tblTransaction where EmployeeNumber = 804

alter TRIGGER tr_ViewByDepartment
ON dbo.ViewByDepartment
INSTEAD OF DELETE
AS
BEGIN
    declare @EmployeeNumber as int
	declare @DateOfTransaction as smalldatetime
	declare @Amount as smallmoney
select @EmployeeNumber = EmployeeNumber, @DateOfTransaction = DateOfTransaction,  @Amount = TotalAmount
	from deleted
	--SELECT * FROM deleted
	delete tblTransaction
	from tblTransaction as T
	where T.EmployeeNumber = @EmployeeNumber
	and T.DateOfTransaction = @DateOfTransaction
	and T.Amount = @Amount
END

begin tran
--SELECT * FROM ViewByDepartment where TotalAmount = -2.77 and EmployeeNumber = 132
delete from ViewByDepartment
where TotalAmount = -2.77 and EmployeeNumber = 132
SELECT * FROM ViewByDepartment where TotalAmount = -2.77 and EmployeeNumber = 132
rollback tran

GO

ALTER TRIGGER trigger_tblTransaction
ON tblTransaction
AFTER DELETE, INSERT, UPDATE
AS
BEGIN
    if @@NESTLEVEL = 1
	begin
		select *,'TABLEINSERT' AS  inserted_Column  from Inserted
		select *, 'TABLEDELETE' AS  deleted_Column from Deleted
	end
END
GO

BEGIN TRAN
insert into tblTransaction(Amount, DateOfTransaction, EmployeeNumber)
VALUES (123,'2015-07-10', 123)
ROLLBACK TRAN

begin tran
--SELECT * FROM ViewByDepartment where TotalAmount = -2.77 and EmployeeNumber = 132
delete from ViewByDepartment
where TotalAmount = -2.77 and EmployeeNumber = 132
--SELECT * FROM ViewByDepartment where TotalAmount = -2.77 and EmployeeNumber = 132
rollback tran

EXEC sp_configure 'nested triggers';

EXEC sp_configure 'nested triggers',0;
RECONFIGURE
GO

