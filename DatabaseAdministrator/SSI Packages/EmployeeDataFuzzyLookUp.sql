CREATE TABLE [dbo].[Employees](
	[EmployeeID] [int] NOT NULL identity(1,1),
	[LastName] [varchar](50) NULL,
	[FirstName] [varchar](50) NULL,
	[OccupationID] [int] NULL,
	[OccupationTitle] [varchar](50) NULL
)
-- Inserting 22 employees with 6 unique occupation titles
INSERT INTO Employees (LastName, FirstName, OccupationID, OccupationTitle)
VALUES
    ('Doe', 'John', 101, 'Manager'),
    ('Smith', 'Jane', 102, 'Engineer'),
    ('Brown', 'Sam', 103, 'Technician'),
    ('Johnson', 'Alex', 104, 'Supervisor'),
    ('Davis', 'Emily', 105, 'Consultant'),
    ('Wilson', 'Chris', 106, 'Administrator'),
    ('Moore', 'Ryan', 101, 'Manager'),
    ('Taylor', 'Sara', 102, 'Engineer'),
    ('Anderson', 'Daniel', 103, 'Technician'),
    ('Thomas', 'Sophia', 104, 'Supervisor'),
    ('Jackson', 'Michael', 105, 'Consultant'),
    ('Martinez', 'Jessica', 106, 'Administrator'),
    ('Harris', 'Ethan', 101, 'Manager'),
    ('Clark', 'Olivia', 102, 'Engineer'),
    ('Lewis', 'Benjamin', 103, 'Technician'),
    ('Walker', 'Mia', 104, 'Supervisor'),
    ('Hall', 'Lucas', 105, 'Consultant'),
    ('Allen', 'Charlotte', 106, 'Administrator'),
    ('Young', 'Nathan', 101, 'Manager'),
    ('King', 'Emma', 102, 'Engineer'),
    ('Scott', 'William', 103, 'Technician'),
    ('White', 'Ava', 104, 'Supervisor');

-- Query to retrieve employee data
SELECT TOP (1000) 
    EmployeeID, 
    LastName, 
    FirstName, 
    OccupationID, 
    OccuTitle
FROM AdventureWorks2022.dbo.Employees;


-- Updating some occupation titles with spelling errors
UPDATE AdventureWorks2022.dbo.Employees
SET OccupationTitle = 
    CASE 
        WHEN OccupationTitle = 'Manager' THEN 'Mang'
        WHEN OccupationTitle = 'Engineer' THEN 'Engneer'
        WHEN OccupationTitle = 'Technician' THEN 'Tech'
        WHEN OccupationTitle = 'Supervisor' THEN 'Suprvsr'
        WHEN OccupationTitle = 'Consultant' THEN 'Consltnt'
        WHEN OccupationTitle = 'Administrator' THEN 'Adminstrtr'
        ELSE OccupationTitle
    END;


-- Rename OccupationTitle to OccuTitle in the Employees table
EXEC sp_rename 'AdventureWorks2022.dbo.Employees.OccupationTitle', 'OccuTitle', 'COLUMN';

Truncate Table AdventureWorks2022.dbo.Employees


SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Employees';

BEGIN TRAN

INSERT INTO AdventureWorks2022.dbo.Employees (LastName, FirstName, OccupationID, OccuTitle)
VALUES 
    ('Doe', 'John', 101, 'Mang.'),
    ('Smith', 'Jane', 102, 'Engneer.'),
    ('Brown', 'Sam', 103, 'Tech.'),
    ('Johnson', 'Alex', 104, 'Supervisor'),
    ('Davis', 'Emily', 105, 'Consultant');


	-- Query to retrieve employee data
SELECT TOP (1000) 
    EmployeeID, 
    LastName, 
    FirstName, 
    OccupationID, 
    OccuTitle
FROM AdventureWorks2022.dbo.Employees;
ROLLBACK TRAN

ALTER TABLE dbo.Employees
ADD EmployeeID INT IDENTITY(1,1) PRIMARY KEY;

DROP TABLE AdventureWorks2022.dbo.Employees