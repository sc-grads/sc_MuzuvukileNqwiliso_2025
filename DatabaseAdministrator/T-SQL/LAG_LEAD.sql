SELECT 
LEAD(AttendanceMonth) OVER (PARTITION BY EmployeeNumber ORDER BY AttendanceMonth) As [output]
-- Output: Feb (for Jan row), Mar (for Feb row), NULL (for Mar row)
FROM tblAttendance
SELECT 
LAG(AttendanceMonth) OVER (PARTITION BY EmployeeNumber ORDER BY AttendanceMonth)
-- Output: NULL (for Jan row), Jan (for Feb row), Feb (for Mar row)
FROM tblAttendance


select A.EmployeeNumber, A.AttendanceMonth, 
A.NumberAttendance, 
lag(NumberAttendance, 1)  over(partition by E.EmployeeNumber 
                            order by A.AttendanceMonth) as MyLag,
lead(NumberAttendance, 1) over(partition by E.EmployeeNumber 
                            order by A.AttendanceMonth) as MyLead,
NumberAttendance - lag(NumberAttendance, 1)  over(partition by E.EmployeeNumber 
                            order by A.AttendanceMonth) as MyDiff
--first_value(NumberAttendance)  over(partition by E.EmployeeNumber 
--                                    order by A.AttendanceMonth
--							        rows between 1 preceding and current row) as MyFirstValue,
--last_value(NumberAttendance) over(partition by E.EmployeeNumber 
--                                  order by A.AttendanceMonth
--								  rows between current row and 1 following) as MyLastValue
from tblEmployee as E join tblAttendance as A
on E.EmployeeNumber = A.EmployeeNumber
