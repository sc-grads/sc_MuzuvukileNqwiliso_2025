select * 
from tblTransaction T
join tblEmployee E
on T.EmployeeNumber = E.EmployeeNumber -- this tables returns everything from 'transaction table' and 'employee table'
where E.EmployeeFirstName like 'y%' -- in like the case sensetive doesn't matter
order by T.EmployeeNumber

  select *
  from tblTransaction AS T
  where T.EmployeeNumber  in ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName not like 'y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber



  
  select * 
  from tblTransaction AS T
  where T.EmployeeNumber  not in ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName like 'y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber




  select * 
  from tblTransaction AS T
  where T.EmployeeNumber <> any ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName like 'y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber

    select * 
  from tblTransaction AS T
  where T.EmployeeNumber = any ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName like 'y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber


    select * -- all = and
  from tblTransaction AS T
  where T.EmployeeNumber <> all ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName like 'y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber


  select *  -- some / any = or
  from tblTransaction AS T
  where T.EmployeeNumber = some ( -- this in will return the employees first name that have the same EmployeeNumber that is similar EmployeeNumber
  select E.EmployeeNumber
  from  tblEmployee AS E
  where E.EmployeeFirstName like 'Y%' -- this subquery return employees that their first name don't start with y
  )
  order by T.EmployeeNumber


  -- number of transactions

select E.[Full Name],  E.[Number of Trans]
from (select left(E.EmployeeFirstName,1)as [Initialise], E.EmployeeFirstName +' '+E.EmployeeLastName as [Full Name], (select count(T.EmployeeNumber)
				from tblTransaction as T
				where T.EmployeeNumber = E.EmployeeNumber
				)as [Number of Trans]
from tblEmployee as E 
where E.EmployeeFirstName like 'y%') as E
where E.[Number of Trans] >=2