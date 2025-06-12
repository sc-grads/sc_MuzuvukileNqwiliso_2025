USE master;
GO

-- Drop and recreate the TimesheetDB
IF OBJECT_ID('dbo.ResetTimesheetDB', 'P') IS NOT NULL
    DROP PROCEDURE dbo.ResetTimesheetDB;
GO

CREATE PROCEDURE dbo.ResetTimesheetDB
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @DatabaseName NVARCHAR(128) = 'TimesheetDB';

    IF EXISTS (SELECT name FROM sys.databases WHERE name = @DatabaseName)
    BEGIN
        EXEC('ALTER DATABASE [' + @DatabaseName + '] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;');
        EXEC('DROP DATABASE [' + @DatabaseName + '];');
    END

    EXEC('CREATE DATABASE [' + @DatabaseName + '];');
END;
GO

-- Execute DB reset
EXEC dbo.ResetTimesheetDB;
GO

-- Switch to new DB
USE TimesheetDB;
GO

-- Create Timesheet schema if not exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Timesheet')
BEGIN
    EXEC('CREATE SCHEMA Timesheet');
END
GO

-- Drop procedure if exists
IF OBJECT_ID('Timesheet.CreateSqID', 'P') IS NOT NULL
    DROP PROCEDURE Timesheet.CreateSqID;
GO

-- Create dynamic procedure for assigning SEQUENCE in each table
CREATE OR ALTER PROCEDURE Timesheet.CreateSqID
    @SequenceName NVARCHAR(100),
    @StartValue INT = 1
AS
BEGIN
    DECLARE @FullName NVARCHAR(200) = 'Timesheet.' + @SequenceName

    IF NOT EXISTS (
        SELECT * FROM sys.sequences 
        WHERE name = @SequenceName AND SCHEMA_NAME(schema_id) = 'Timesheet'
    )
    BEGIN
        DECLARE @SQL NVARCHAR(MAX) = '
            CREATE SEQUENCE ' + @FullName + '
            AS INT
            START WITH ' + CAST(@StartValue AS NVARCHAR) + '
            INCREMENT BY 1
            MINVALUE 1
            NO MAXVALUE
            NO CYCLE;
        '
        EXEC sp_executesql @SQL
    END
END
GO

-- Creation of sequences
EXEC Timesheet.CreateSqID @SequenceName = 'EmployeeSeq', @StartValue = 1000;
EXEC Timesheet.CreateSqID @SequenceName = 'ClientSeq', @StartValue = 2000;
EXEC Timesheet.CreateSqID @SequenceName = 'ProjectSeq', @StartValue = 3000;
EXEC Timesheet.CreateSqID @SequenceName = 'LeaveTypeSeq', @StartValue = 4000;
EXEC Timesheet.CreateSqID @SequenceName = 'ActivitySeq', @StartValue = 5000;
EXEC Timesheet.CreateSqID @SequenceName = 'TimesheetSeq', @StartValue = 6000;
EXEC Timesheet.CreateSqID @SequenceName = 'ForecastSeq', @StartValue = 7000;
GO




-- Drop CreateTimesheetTables if exists
IF OBJECT_ID('Timesheet.CreateTimesheetTables', 'P') IS NOT NULL
    DROP PROCEDURE Timesheet.CreateTimesheetTables;
GO

-- Create All Tables
CREATE PROCEDURE Timesheet.CreateTimesheetTables
AS
BEGIN
    SET NOCOUNT ON;

    -- Employee Table
    IF OBJECT_ID('Timesheet.Employee', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Employee (
            EmployeeID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.EmployeeSeq,
            EmployeeName VARCHAR(100) NOT NULL,
            CONSTRAINT CHK_Employee_Name CHECK (EmployeeName <> '')
        );
        CREATE INDEX IX_Employee_Employee_ID ON Timesheet.Employee(EmployeeID);
        PRINT 'Employee table created.';
    END

    -- Client Table
    IF OBJECT_ID('Timesheet.Client', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Client (
            ClientID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ClientSeq, -- Fixed typo
            ClientName VARCHAR(100) NOT NULL,
            CONSTRAINT CHK_Client_Name CHECK (ClientName <> '')
        );
        CREATE INDEX IX_Client_Client_ID ON Timesheet.Client(ClientID);
        PRINT 'Client table created.';
    END

    -- ✅ Project Table
    IF OBJECT_ID('Timesheet.Project', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Project (
            ProjectID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ProjectSeq, -- Changed to use sequence
            ProjectName VARCHAR(100) NOT NULL,
            ClientID INT NOT NULL,
            FOREIGN KEY (ClientID) REFERENCES Timesheet.Client(ClientID),
            CONSTRAINT CHK_Project_Name CHECK (ProjectName <> '')
        );
        CREATE INDEX IX_Project_Client_ID ON Timesheet.Project(ClientID);
        PRINT 'Project table created.';
    END

    -- LeaveType Table
    IF OBJECT_ID('Timesheet.LeaveType', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.LeaveType (
            LeaveType INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.LeaveTypeSeq, -- Changed to use sequence
            LeaveTypeName VARCHAR(50) NOT NULL,
            CONSTRAINT CHK_LeaveType_Name CHECK (LeaveTypeName <> '')
        );
        CREATE INDEX IX_LeaveType_LeaveType_ID ON Timesheet.LeaveType(LeaveType);
        PRINT 'LeaveType table created.';
    END

    -- Activity Table
    IF OBJECT_ID('Timesheet.Activity', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Activity (
            ActivityID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ActivitySeq, -- Changed to use sequence
            ActivityName VARCHAR(50) NOT NULL,
            CONSTRAINT CHK_Activity_Name CHECK (ActivityName <> '')
        );
        CREATE INDEX IX_Activity_Activity_ID ON Timesheet.Activity(ActivityID);
        PRINT 'Activity table created.';
    END

    -- Timesheet Table
    IF OBJECT_ID('Timesheet.Timesheet', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Timesheet (
            Timesheet_ID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.TimesheetSeq, -- Changed to use sequence
            EmployeeID INT NOT NULL,
            Date DATE NOT NULL,
            [DayOfWeek] VARCHAR(10) NOT NULL,
            ClientID INT,
            ProjectID INT,
            ActivityID INT,
            LeaveType INT,
            BillableStatus VARCHAR(20) NOT NULL CHECK (BillableStatus IN ('Billable', 'Non-Billable')),
            Comments TEXT,
            TotalHours DECIMAL(5,2),
            StartTime TIME,
            EndTime TIME,
            FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
            FOREIGN KEY (ClientID) REFERENCES Timesheet.Client(ClientID),
            FOREIGN KEY (ProjectID) REFERENCES Timesheet.Project(ProjectID),
            FOREIGN KEY (ActivityID) REFERENCES Timesheet.Activity(ActivityID),
            FOREIGN KEY (LeaveType) REFERENCES Timesheet.LeaveType(LeaveType),
            CONSTRAINT CHK_Valid_Hours CHECK (TotalHours >= 0),
            CONSTRAINT CHK_Day_of_Week CHECK ([DayOfWeek] IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
            CONSTRAINT activity_or_leave CHECK (
                (ActivityID IS NOT NULL AND LeaveType IS NULL) OR 
                (ActivityID IS NULL AND LeaveType IS NOT NULL)
            )
        );
        CREATE INDEX IX_Timesheet_Employee_Date ON Timesheet.Timesheet(EmployeeID, Date);
        PRINT 'Timesheet table created.';
    END

	
    -- Leave Table
	IF OBJECT_ID('Timesheet.LeaveRequest','U') IS NULL 
	BEGIN
		  CREATE TABLE Timesheet.LeaveRequest (
			LeaveRequestID INT IDENTITY(1,1) PRIMARY KEY,
			EmployeeID INT NOT NULL,
			LeaveTypeID INT NOT NULL,  -- FK here instead of string
			StartDate DATE NOT NULL,
			EndDate DATE NOT NULL,
			Status VARCHAR(20) NOT NULL DEFAULT 'Pending'
				CHECK (Status IN ('Pending', 'Approved', 'Denied')),
			NumberOfDays AS DATEDIFF(DAY, StartDate, EndDate) + 1 PERSISTED,
			ApprovalObtained BIT NOT NULL DEFAULT 0,
			SickNoteSubmitted BIT NULL,

			CONSTRAINT FK_LeaveRequests_Employee FOREIGN KEY (EmployeeID)
				REFERENCES Timesheet.Employee(EmployeeID),

			CONSTRAINT FK_LeaveRequests_LeaveType FOREIGN KEY (LeaveTypeID)
				REFERENCES Timesheet.LeaveType(LeaveType),

			CONSTRAINT CHK_LeaveRequests_Dates CHECK (EndDate >= StartDate),

			CONSTRAINT CHK_Approval_Status CHECK (
				(Status = 'Approved' AND ApprovalObtained = 1) OR
				(Status IN ('Pending', 'Denied'))
			)
		);
     END

-- Drop the table if it exists (must be before procedure creation)
IF OBJECT_ID('Timesheet.Forecast', 'U') IS NOT NULL
    DROP TABLE Timesheet.Forecast;
  CREATE TABLE Timesheet.Forecast (
    ForecastID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ForecastSeq ,
    EmployeeID INT NOT NULL,
    ForecastMonth DATE NOT NULL,
    ForecastedHours DECIMAL(5,2) NOT NULL DEFAULT (168.00),
    ForecastedWorkDays INT NOT NULL DEFAULT (21),
    NonBillableHours DECIMAL(5,2) NOT NULL,
    BillableHours DECIMAL(5,2) NOT NULL,
    TotalHours DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
    CONSTRAINT UQ_Forecast_Employee_Month UNIQUE (EmployeeID, ForecastMonth),
    CONSTRAINT CK_Forecast_Total_vs_Planned CHECK (TotalHours >= ForecastedHours)
);


    -- ProcessedFiles Table
    IF OBJECT_ID('Timesheet.ProcessedFiles', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.ProcessedFiles (
            FileID INT PRIMARY KEY IDENTITY(1,1),
            FilePath VARCHAR(500) NOT NULL,
            FileName VARCHAR(255) NOT NULL,
            LastModifiedDate DATETIME NOT NULL,
            ProcessedDate DATETIME NOT NULL,
            FileHash VARCHAR(64)
        );
        CREATE INDEX IX_ProcessedFiles_FileName ON Timesheet.ProcessedFiles(FileName);
        PRINT 'ProcessedFiles table created.';
    END


 IF OBJECT_ID('Timesheet.AuditLog', 'U') IS NOT NULL
    DROP TABLE Timesheet.AuditLog;

CREATE TABLE Timesheet.AuditLog (
    AuditID INT PRIMARY KEY IDENTITY(1,1),
    EmployeeName NVARCHAR(255),          -- Added to identify the employee involved
    FileName VARCHAR(255),              -- File associated with the action
    TableName VARCHAR(50) NOT NULL,     -- Table affected by the action
    Action VARCHAR(20) NOT NULL CHECK (Action IN ('Insert', 'Update', 'Delete', 'Processed', 'Skipped')), -- Expanded actions
    RecordID INT,                       -- ID of the affected record
    TotalHours DECIMAL(5,2),            -- Hours related to the action (if applicable)
    Message NVARCHAR(1000),             -- Detailed context or reason
    ProcessedDate DATETIME NOT NULL DEFAULT GETDATE() -- Default to current time
);
CREATE INDEX IX_AuditLog_ProcessedDate ON Timesheet.AuditLog(ProcessedDate);
CREATE INDEX IX_AuditLog_EmployeeName ON Timesheet.AuditLog(EmployeeName);
PRINT 'AuditLog table updated with EmployeeName.';

IF OBJECT_ID('Timesheet.ErrorLog', 'U') IS NULL
BEGIN
    CREATE TABLE Timesheet.ErrorLog (
        ErrorID INT PRIMARY KEY IDENTITY(1,1),
        EmployeeName NVARCHAR(255),          -- Employee associated with the error
        FileName VARCHAR(255),              -- File causing the error
        TableName VARCHAR(50),              -- Table where error occurred
        ErrorType VARCHAR(50) NOT NULL CHECK (ErrorType IN ('Validation', 'SSIS', 'Data', 'System')), -- Error category
        ErrorMessage NVARCHAR(1000) NOT NULL, -- Detailed error description
        RecordID INT,                       -- Affected record (if applicable)
        StackTrace NVARCHAR(MAX),           -- Technical details (e.g., SSIS error stack)
        ProcessedDate DATETIME NOT NULL DEFAULT GETDATE() -- When the error occurred
    );
    CREATE INDEX IX_ErrorLog_ProcessedDate ON Timesheet.ErrorLog(ProcessedDate);
    CREATE INDEX IX_ErrorLog_EmployeeName ON Timesheet.ErrorLog(EmployeeName);
    PRINT 'ErrorLog table created.';
END


    -- Timesheet_Staging Table
IF OBJECT_ID('Timesheet.TimesheetStaging', 'U') IS NOT NULL
    DROP TABLE Timesheet.TimesheetStaging;

CREATE TABLE Timesheet.TimesheetStaging (
    StagingID INT IDENTITY(1,1) PRIMARY KEY,
    [Date] NVARCHAR(50),           -- Raw string to handle Excel date formats
    [DayOfWeek] VARCHAR(10),
    ClientName VARCHAR(100),
    ProjectName VARCHAR(100),
    ActivityName VARCHAR(50),
    BillableStatus VARCHAR(20),
    Comments NVARCHAR(MAX),         -- TEXT is deprecated, use NVARCHAR(MAX)
    TotalHours NVARCHAR(50),        -- Raw string to validate later
    StartTime NVARCHAR(50),         -- Raw string for time
    EndTime NVARCHAR(50),           -- Raw string for time
    EmployeeName NVARCHAR(255),     -- From User::EmployeeName
    FileName NVARCHAR(255),         -- From User::ExcelFilePath
    ProcessedDate DATETIME DEFAULT GETDATE(),
    IsValid BIT DEFAULT 0,          -- Flag for valid rows
    --ErrorMessage NVARCHAR(1000)     -- Validation errors
);

PRINT 'Timesheet.TimesheetStaging table created.';

    -- FileEmployeeMapping Table
    IF OBJECT_ID('Timesheet.FileEmployeeMapping', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.FileEmployeeMapping (
            FileNamePattern VARCHAR(255) PRIMARY KEY,
            EmployeeID INT NOT NULL,
            FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID)
        );
        PRINT 'FileEmployeeMapping table created.';
    END
END;
GO

-- Execute table creation
EXEC Timesheet.CreateTimesheetTables;
GO


--  Employee (uses SEQUENCE, start at 1000)
CREATE OR ALTER PROCEDURE Timesheet.ResetEmployee
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Employee;
    ALTER SEQUENCE Timesheet.EmployeeSeq RESTART WITH 1000;
END;
GO

--  Client (uses SEQUENCE, start at 2000)
CREATE OR ALTER PROCEDURE Timesheet.ResetClient
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Client;
    ALTER SEQUENCE Timesheet.ClientSeq RESTART WITH 2000;
END;
GO

--  Project (uses SEQUENCE, start at 3000)
CREATE OR ALTER PROCEDURE Timesheet.ResetProject
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Project;
    ALTER SEQUENCE Timesheet.ProjectSeq RESTART WITH 3000;
END;
GO

--  LeaveType (uses SEQUENCE, start at 4000)
CREATE OR ALTER PROCEDURE Timesheet.ResetLeaveType
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.LeaveType;
    ALTER SEQUENCE Timesheet.LeaveTypeSeq RESTART WITH 4000;
END;
GO

--  Activity (uses SEQUENCE, start at 5000)
CREATE OR ALTER PROCEDURE Timesheet.ResetActivity
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Activity;
    ALTER SEQUENCE Timesheet.ActivitySeq RESTART WITH 5000;
END;
GO

--  Timesheet (uses SEQUENCE, start at 6000)
CREATE OR ALTER PROCEDURE Timesheet.ResetTimesheet
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Timesheet;
    ALTER SEQUENCE Timesheet.TimesheetSeq RESTART WITH 6000;
END;
GO

--  Leave (uses IDENTITY, so reseed to 0 or desired base)
CREATE OR ALTER PROCEDURE Timesheet.ResetLeave
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.LeaveRequest;
    DBCC CHECKIDENT ('Timesheet.LeaveRequest', RESEED, 0);
END;
GO

-- Forecast (uses IDENTITY, reseed to 0 or relevant base)
CREATE OR ALTER PROCEDURE Timesheet.ResetForecast
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Forecast;
    DBCC CHECKIDENT ('Timesheet.Forecast', RESEED, 0);
END;
GO



CREATE OR ALTER PROCEDURE Timesheet.ResetAll
AS
BEGIN
    EXEC Timesheet.ResetForecast;
    EXEC Timesheet.ResetLeave;
    EXEC Timesheet.ResetTimesheet;
    EXEC Timesheet.ResetActivity;
    EXEC Timesheet.ResetLeaveType;
    EXEC Timesheet.ResetProject;
    EXEC Timesheet.ResetClient;
    EXEC Timesheet.ResetEmployee;
END;
GO


-- VIEWS 
CREATE VIEW Timesheet.vw_LeaveRequestDetails AS
SELECT
    lr.LeaveRequestID,
    e.EmployeeID,
    e.EmployeeName,
    lt.LeaveTypeName,
    lr.StartDate,
    lr.EndDate,
    lr.NumberOfDays,
    lr.Status,
    lr.ApprovalObtained,
    lr.SickNoteSubmitted
FROM Timesheet.LeaveRequest lr
JOIN Timesheet.Employee e ON lr.EmployeeID = e.EmployeeID
JOIN Timesheet.LeaveType lt ON lr.LeaveTypeID = lt.LeaveType;

--