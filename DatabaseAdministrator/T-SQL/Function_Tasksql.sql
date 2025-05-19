DECLARE @result_2 AS DECIMAL(10,2) = FLOOR(PI()) 
PRINT @result_2

DECLARE @result_3 AS DECIMAL(7,1) = CEILING(PI())
SET @result_3 = 123456.67
PRINT @result_3