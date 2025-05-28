-- Enable IDENTITY_INSERT for the Occupation table
SET IDENTITY_INSERT AdventureWorks2022.dbo.Occupation ON;

-- Insert occupation data
INSERT INTO AdventureWorks2022.dbo.Occupation (OccupationID, OccupationTitle)
VALUES
    (101, 'Manager'),
    (102, 'Engineer'),
    (103, 'Technician'),
    (104, 'Supervisor'),
    (105, 'Consultant'),
    (106, 'Administrator');

-- Disable IDENTITY_INSERT after inserting the data
SET IDENTITY_INSERT AdventureWorks2022.dbo.Occupation OFF;

SELECT *FROM AdventureWorks2022.dbo.Occupation

TRUNCATE TABLE AdventureWorks2022.dbo.Occupation