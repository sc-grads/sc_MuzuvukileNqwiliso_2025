
-- CURRENT_TIMESTAMP FUNCTION

SELECT  YEAR(CURRENT_TIMESTAMP) AS [Year] -- this will return a year of the current system
SELECT DAY(CURRENT_TIMESTAMP) AS [Day] -- this will return a day of the current sysystem
SELECT MONTH(CURRENT_TIMESTAMP) AS [Month] -- this will return month of the current system

-- DATE
declare @myDate as date = '2025-05-24'
declare @myDateTime as datetime = '2025-05-24 12:34:56.124'
SELECT @myDateTime AS [Date Time]
SELECT @myDate AS [Full Date]
declare @timeDate as date
declare @time as time = SYSDATETIME()
SELECT @time AS [System Time]
declare @date as datetime = SYSDATETIME()
SELECT @date AS [System Date]
declare @smalldate as smalldatetime = SYSDATETIME()
SELECT @smalldate AS [Small date time]
SELECT GETDATE() AS [DateTimeFunction] 

-- DIFFERENCE DATE FUNCTIONS
SELECT DATEDIFF(YEAR, '2022-10-11', CURRENT_TIMESTAMP) AS YearsPassed;
SELECT DATEDIFF(YEAR, '2002-03-11', SYSDATETIME()) AS DOB;

-- MODIFY
SELECT IIF(Month(DATEADD(MONTH, 1,CURRENT_TIMESTAMP)) = 6, 'June','Not June')  AS NextMonth
SELECT 
  DATENAME(MONTH, DATEADD(MONTH, 1, CURRENT_TIMESTAMP)) AS ActualNextMonth,
  IIF(MONTH(DATEADD(MONTH, 1, CURRENT_TIMESTAMP)) = 6, 'June', 'Not June') AS IsJune;
