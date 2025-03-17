USE master;
GO
CREATE LOGIN mzuLogin WITH PASSWORD = 'Strong@Password123'; -- Creates login at server level
GO

USE BikeStores;
GO
CREATE USER mzuUser FOR LOGIN mzuLogin; -- Creates user at database level
GO

GRANT SELECT, UPDATE, INSERT ON customers TO mzuUser; -- Grants permissions to the user
GO
