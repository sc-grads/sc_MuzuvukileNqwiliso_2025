-- New user information
DECLARE @first_name2 AS VARCHAR(50);
SET @first_name2 = 'Nomsa';

DECLARE @last_name2 AS VARCHAR(50);
SET @last_name2 = 'Dlamini';

DECLARE @job2 AS VARCHAR(100);
SET @job2 = 'Data Analyst';

DECLARE @salary2 AS DECIMAL(10,2);
SET @salary2 = 18999.50;

DECLARE @VAT2 AS DECIMAL(10,2);
SET @VAT2 = (@salary2 * 15) / 100;

-- Print details
PRINT 'My name is ' + @first_name2 + ' ' + @last_name2 +
      '. I work as a ' + @job2 +
      ', my salary is R' + CAST(@salary2 AS VARCHAR(20)) +
      ' and I pay a VAT of R' + CAST(@VAT2 AS VARCHAR(20));

-- Insert new employee and assign department 101 directly
INSERT INTO tbEmployees (first_name, last_name, department)
VALUES (@first_name2, @last_name2, 101);

-- Show updated table
SELECT * FROM tbEmployees;
