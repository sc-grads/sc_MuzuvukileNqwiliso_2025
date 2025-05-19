-- Can you create a variable of the data type that allows values up to 32,767, but no further.
DECLARE  @number_1 SMALLINT
SET @number_1 = 20000
PRINT @number_1

--Create version 2: Change your code so that it tries to assign the value of 200,000. If it doesn't run properly, then you got it right.
DECLARE  @number_2 SMALLINT
SET @number_2 = 200000
PRINT @number_2

-- Create version 3: Correct the problem by changing your variable to a data type that allows the value of 200,000, and see if the code now works.
DECLARE  @number_3 INT
SET @number_3 = 200000
PRINT @number_3