USE [70-461]
select first_name + ' A' as [FIRST NAME]
from tbEmployees


select first_name + N'Ⱥ' as [FIRST NAME]
from tbEmployees


select Concat(substring(first_name,2,LEN(first_name)), 'A') as [FIRST NAME]
from tbEmployees
