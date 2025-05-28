select E.EmployeeNumber as ENumber, E.EmployeeFirstName,
       E.EmployeeLastName, T.EmployeeNumber as TNumber, 
       sum(T.Amount) as TotalAmount -- this will use group by 
from tblEmployee as E
left join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
where T.EmployeeNumber IS NULL
group by E.EmployeeNumber, T.EmployeeNumber, E.EmployeeFirstName, -- if i omit one of the columns here the sql will generate an error
       E.EmployeeLastName -- this will group by 4 columns that are in the select statement
order by E.EmployeeNumber, T.EmployeeNumber, E.EmployeeFirstName, -- even if you can omit a column here there's going to be no error
       E.EmployeeLastName
-- derived table


select ENumber, EmployeeFirstName, EmployeeLastName -- the ENumber comes from the inner table - subquery
from (
select E.EmployeeNumber as ENumber, E.EmployeeFirstName,
       E.EmployeeLastName, T.EmployeeNumber as TNumber, 
       sum(T.Amount) as TotalAmount
from tblEmployee as E
left join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
--where T.EmployeeNumber is null -- the where clause can be here inside
group by E.EmployeeNumber, T.EmployeeNumber, E.EmployeeFirstName,
       E.EmployeeLastName)
	   as newTable -- alias of the inner table
where TNumber is null -- this reference to the  inner table
order by ENumber, TNumber, EmployeeFirstName,
       EmployeeLastName
-- RIGHT JOIN


select *
from (
select E.EmployeeNumber as ENumber, E.EmployeeFirstName,
       E.EmployeeLastName, T.EmployeeNumber as TNumber, 
       sum(T.Amount) as TotalAmount
from tblEmployee as E
right join tblTransaction as T
on E.EmployeeNumber = T.EmployeeNumber
group by E.EmployeeNumber, T.EmployeeNumber, E.EmployeeFirstName,
       E.EmployeeLastName) as newTable
where ENumber is null
order by ENumber, TNumber, EmployeeFirstName,
       EmployeeLastName



UPDATE T
SET T.Amount = -9999 -- or any placeholder value
FROM tblTransaction AS T
LEFT JOIN tblEmployee AS E
    ON T.EmployeeNumber = E.EmployeeNumber
WHERE E.EmployeeNumber IS NULL;


