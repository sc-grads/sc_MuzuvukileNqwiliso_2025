
-- row window function
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

	-- rank 

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

	-- desnse rank

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
