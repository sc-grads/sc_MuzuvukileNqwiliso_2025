-- FIRST_VALUE: returns the first occurrence of A.AttendanceMonth within the defined window frame.
-- OVER (PARTITION BY A.EmployeeNumber): resets the window for each EmployeeNumber.
-- For example, if the EmployeeNumbers are 1,1,1,2,2,2, the window starts over when the EmployeeNumber changes.
-- ORDER BY A.AttendanceMonth: defines how the AttendanceMonth values are sorted to determine "first".
-- NOTE: Using ORDER BY (SELECT NULL) would ignore order, which is not helpful for FIRST_VALUE or LAST_VALUE.

-- LAST_VALUE requires both ORDER BY and ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
-- to make sure it considers the full partition (i.e., all rows for each employee).
-- UNBOUNDED PRECEDING: starts from the very first row in the partition.
-- UNBOUNDED FOLLOWING: goes all the way to the last row in the partition (ensures true "last" value).

SELECT 
    A.EmployeeNumber, 
    A.AttendanceMonth, 
    A.NumberAttendance,

    FIRST_VALUE(A.AttendanceMonth) OVER (
        PARTITION BY A.EmployeeNumber 
        ORDER BY A.AttendanceMonth
    ) AS FirstAttendanceMonth,

    LAST_VALUE(A.AttendanceMonth) OVER (
        PARTITION BY A.EmployeeNumber 
        ORDER BY A.AttendanceMonth 
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS LastAttendanceMonth

FROM tblEmployee E
JOIN tblAttendance A
    ON E.EmployeeNumber = A.EmployeeNumber;


	LEAD(AttendanceMonth) OVER (PARTITION BY EmployeeNumber ORDER BY AttendanceMonth)
-- Output: Feb (for Jan row), Mar (for Feb row), NULL (for Mar row)

LAG(AttendanceMonth) OVER (PARTITION BY EmployeeNumber ORDER BY AttendanceMonth)
-- Output: NULL (for Jan row), Jan (for Feb row), Feb (for Mar row)


SELECT 
    A.EmployeeNumber, 
    A.AttendanceMonth, 
    A.NumberAttendance, 
    ROW_NUMBER() OVER (ORDER BY E.EmployeeNumber, A.AttendanceMonth) AS TheRowNumber
FROM 
    tblEmployee AS E
JOIN 
    (
        SELECT * FROM tblAttendance
        UNION ALL
        SELECT * FROM tblAttendance
    ) AS A
ON 
    E.EmployeeNumber = A.EmployeeNumber;


	SELECT 
    A.EmployeeNumber, 
    A.AttendanceMonth, 
    A.NumberAttendance, 
    RANK() OVER (ORDER BY E.EmployeeNumber, A.AttendanceMonth) AS TheRank
FROM 
    tblEmployee AS E
JOIN 
    (
        SELECT * FROM tblAttendance
        UNION ALL
        SELECT * FROM tblAttendance
    ) AS A
ON 
    E.EmployeeNumber = A.EmployeeNumber;

	SELECT 
    A.EmployeeNumber, 
    A.AttendanceMonth, 
    A.NumberAttendance, 
    DENSE_RANK() OVER (ORDER BY E.EmployeeNumber, A.AttendanceMonth) AS TheDenseRank
FROM 
    tblEmployee AS E
JOIN 
    (
        SELECT * FROM tblAttendance
        UNION ALL
        SELECT * FROM tblAttendance
    ) AS A
ON 
    E.EmployeeNumber = A.EmployeeNumber;
