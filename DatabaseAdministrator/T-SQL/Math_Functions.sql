-- MATHS FUNCTIONS
DECLARE @num AS int  =  -3
DECLARE @num_2 As decimal(10,2) = 123.67
PRINT ABS(@num) -- This returns a non negative number

PRINT SIGN(@num) -- This returns -1 for negative number and returns 0 for positive number
SET @num = 2 -- Assign a new number to the previous one
PRINT SIGN(@num) -- returns 1 for a positive

PRINT  'num 2 : '+CAST( ROUND(@num_2 * 3.5,2) As VARCHAR(50))
PRINT 'this is a power function : '+ CAST( POWER(@num_2,3) AS VARCHAR(50))
PRINT 'this is the sqrt for number 2 : '+ CAST( FLOOR(SQRT(@num_2))AS VARCHAR(50))
PRINT 'this is a pi function : '+ CAST(PI() AS VARCHAR(50))