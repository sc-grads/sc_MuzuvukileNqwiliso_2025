-- STRING TYPE
DECLARE @code CHAR(5) = 'A'
PRINT @code -- Outputs: 'A    ' (padded with spaces)
-- USEFULL WHEN YOU WORK WITH IDs, COUNTRY CODES, ZIP CODES

DECLARE @name VARCHAR(50)
SET @name = 'Mzu'
SELECT @name -- Outputs: 'Mzu'
PRINT LEN(@name)

-- ⚠️ -- Don't ever use TEXT data type

DECLARE @longText VARCHAR(MAX);
SET @longText = REPLICATE('A', 12); -- 1 million A's
SELECT @longText -- Only use it if I need long text , documents, logs, articles

-- UNICODE VERSIONS ---

DECLARE @lang NVARCHAR(20) = N'你好'; -- Chinese for Hello
SELECT @lang

DECLARE @idNumber VARCHAR(13) = '9501215009087';

SELECT 
  LEFT(@idNumber, 6) AS BirthDatePart,  -- e.g. YYMMDD
  RIGHT(@idNumber, 4) AS LastDigits;    -- could be used for checks or grouping

DECLARE @full_name VARCHAR(50) = TRIM(' Mzuvu  kile');
SELECT @full_name

SELECT REPLACE(@full_name, ' ', '') AS NoSpaces