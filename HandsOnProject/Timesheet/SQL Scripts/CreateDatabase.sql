
USE master;
GO

-- Drop and recreate TimesheetDB
IF OBJECT_ID('dbo.ResetTimesheetDB', 'P') IS NOT NULL
    DROP PROCEDURE dbo.ResetTimesheetDB;
GO
CREATE PROCEDURE dbo.ResetTimesheetDB
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @DatabaseName NVARCHAR(128) = 'TimesheetDB';

    IF EXISTS (SELECT 1 FROM sys.databases WHERE name = @DatabaseName)
   

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

-- Switch to TimesheetDB
USE TimesheetDB;
GO

-- Create Timesheet schema
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'Timesheet')
BEGIN
    EXEC('CREATE SCHEMA Timesheet');
END;
GO

-- Create sequence creation procedure
IF OBJECT_ID('Timesheet.CreateSqID', 'P') IS NOT NULL
    DROP PROCEDURE Timesheet.CreateSqID;
GO
CREATE PROCEDURE Timesheet.CreateSqID
    @SequenceName NVARCHAR(100),
    @StartValue INT = 1
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @FullName NVARCHAR(200) = QUOTENAME('Timesheet') + '.' + QUOTENAME(@SequenceName);
    DECLARE @SQL NVARCHAR(MAX);

    IF NOT EXISTS (
        SELECT 1 FROM sys.sequences 
        WHERE name = @SequenceName AND SCHEMA_NAME(schema_id) = 'Timesheet'
    )
    BEGIN
        SET @SQL = N'
            CREATE SEQUENCE ' + @FullName + N'
            AS INT
            START WITH ' + CAST(@StartValue AS NVARCHAR(10)) + N'
            INCREMENT BY 1
            MINVALUE 1
            NO MAXVALUE
            NO CYCLE;
        ';
        EXEC sp_executesql @SQL;
    END;
END;
GO

-- Create all sequences
EXEC Timesheet.CreateSqID @SequenceName = 'EmployeeSeq', @StartValue = 1000;
EXEC Timesheet.CreateSqID @SequenceName = 'ClientSeq', @StartValue = 2000;
EXEC Timesheet.CreateSqID @SequenceName = 'ProjectSeq', @StartValue = 3000;
EXEC Timesheet.CreateSqID @SequenceName = 'LeaveTypeSeq', @StartValue = 4000;
EXEC Timesheet.CreateSqID @SequenceName = 'ActivitySeq', @StartValue = 5000;
EXEC Timesheet.CreateSqID @SequenceName = 'TimesheetSeq', @StartValue = 6000;
EXEC Timesheet.CreateSqID @SequenceName = 'ForecastSeq', @StartValue = 7000;
EXEC Timesheet.CreateSqID @SequenceName = 'DescriptionSeq', @StartValue = 8000;
GO

-- Create tables procedure
IF OBJECT_ID('Timesheet.CreateTimesheetTables', 'P') IS NOT NULL
    DROP PROCEDURE Timesheet.CreateTimesheetTables;
GO
CREATE PROCEDURE Timesheet.CreateTimesheetTables
AS
BEGIN
    SET NOCOUNT ON;

    -- Drop dependent tables first to avoid FK violations
    IF OBJECT_ID('Timesheet.Timesheet', 'U') IS NOT NULL
        DROP TABLE Timesheet.Timesheet;
    IF OBJECT_ID('Timesheet.Forecast', 'U') IS NOT NULL
        DROP TABLE Timesheet.Forecast;
    IF OBJECT_ID('Timesheet.LeaveRequest', 'U') IS NOT NULL
        DROP TABLE Timesheet.LeaveRequest;
    IF OBJECT_ID('Timesheet.Project', 'U') IS NOT NULL
        DROP TABLE Timesheet.Project;
    IF OBJECT_ID('Timesheet.Description', 'U') IS NOT NULL
        DROP TABLE Timesheet.Description;
    IF OBJECT_ID('Timesheet.Client', 'U') IS NOT NULL
        DROP TABLE Timesheet.Client;
    IF OBJECT_ID('Timesheet.Employee', 'U') IS NOT NULL
        DROP TABLE Timesheet.Employee;
    IF OBJECT_ID('Timesheet.LeaveType', 'U') IS NOT NULL
        DROP TABLE Timesheet.LeaveType;
    IF OBJECT_ID('Timesheet.Activity', 'U') IS NOT NULL
        DROP TABLE Timesheet.Activity;
    IF OBJECT_ID('Timesheet.TimesheetStaging', 'U') IS NOT NULL
        DROP TABLE Timesheet.TimesheetStaging;
    IF OBJECT_ID('Timesheet.StagingForecast', 'U') IS NOT NULL
        DROP TABLE Timesheet.StagingForecast;
    IF OBJECT_ID('Timesheet.ProjectStaging', 'U') IS NOT NULL
        DROP TABLE Timesheet.ProjectStaging;
    IF OBJECT_ID('Timesheet.ActivityLeaveStaging', 'U') IS NOT NULL
        DROP TABLE Timesheet.ActivityLeaveStaging;
    IF OBJECT_ID('Timesheet.AuditLog', 'U') IS NOT NULL
        DROP TABLE Timesheet.AuditLog;

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
    END;

    -- Client Table
    IF OBJECT_ID('Timesheet.Client', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Client (
            ClientID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ClientSeq,
            ClientName VARCHAR(100) NOT NULL,
            CONSTRAINT CHK_Client_Name CHECK (ClientName <> '')
        );
        CREATE INDEX IX_Client_Client_ID ON Timesheet.Client(ClientID);
        PRINT 'Client table created.';
    END;

    -- Project Table
    IF OBJECT_ID('Timesheet.Project', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Project (
            ProjectID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ProjectSeq,
            ProjectName VARCHAR(100) NOT NULL,
            ClientID INT NOT NULL,
            FOREIGN KEY (ClientID) REFERENCES Timesheet.Client(ClientID),
            CONSTRAINT CHK_Project_Name CHECK (ProjectName <> '')
        );
        CREATE INDEX IX_Project_Client_ID ON Timesheet.Project(ClientID);
        PRINT 'Project table created.';
    END;

    -- LeaveType Table
    IF OBJECT_ID('Timesheet.LeaveType', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.LeaveType (
            LeaveType INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.LeaveTypeSeq,
            LeaveTypeName VARCHAR(50) NOT NULL,
            CONSTRAINT CHK_LeaveType_Name CHECK (LeaveTypeName <> '')
        );
        CREATE INDEX IX_LeaveType_LeaveType_ID ON Timesheet.LeaveType(LeaveType);
        PRINT 'LeaveType table created.';
    END;

    -- Activity Table
    IF OBJECT_ID('Timesheet.Activity', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Activity (
            ActivityID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ActivitySeq,
            ActivityName VARCHAR(50) NOT NULL,
            CONSTRAINT CHK_Activity_Name CHECK (ActivityName <> '')
        );
        CREATE INDEX IX_Activity_Activity_ID ON Timesheet.Activity(ActivityID);
        PRINT 'Activity table created.';
    END;

    -- Description Table (Fixed typo: removed 'compagnon')
    IF OBJECT_ID('Timesheet.Description', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.Description (
            DescriptionID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.DescriptionSeq,
            DescriptionType VARCHAR(10) CHECK (DescriptionType IN ('Activity', 'Leave')),
            SourceID INT NOT NULL,
            DescriptionName VARCHAR(100) NOT NULL
        );
        PRINT 'Description table created.';
    END;

    -- Timesheet Table
    CREATE TABLE Timesheet.Timesheet (
        Timesheet_ID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.TimesheetSeq,
        EmployeeID INT NOT NULL,
        [Date] DATE NOT NULL,
        [DayOfWeek] VARCHAR(10) NOT NULL CHECK ([DayOfWeek] IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
        ClientID INT,
        ProjectID INT,
        DescriptionID INT NOT NULL,
        BillableStatus VARCHAR(20) NOT NULL CHECK (BillableStatus IN ('Billable', 'Non-Billable')),
        Comments TEXT,
        TotalHours DECIMAL(5,2) CHECK (TotalHours >= 0),
        StartTime TIME,
        EndTime TIME,
        FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
        FOREIGN KEY (ClientID) REFERENCES Timesheet.Client(ClientID),
        FOREIGN KEY (ProjectID) REFERENCES Timesheet.Project(ProjectID),
        FOREIGN KEY (DescriptionID) REFERENCES Timesheet.Description(DescriptionID)
    );
    CREATE INDEX IX_Timesheet_Employee_Date ON Timesheet.Timesheet(EmployeeID, [Date]);
    PRINT 'Timesheet table created successfully with unified DescriptionID.';

    -- Forecast Table
    CREATE TABLE Timesheet.Forecast (
        ForecastID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ForecastSeq,
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
    PRINT 'Forecast table created.';

    -- ProcessedFiles Table
    IF OBJECT_ID('Timesheet.ProcessedFiles', 'U') IS NOT NULL
	    DROP TABLE Timesheet.ProcessedFiles
    BEGIN
        CREATE TABLE Timesheet.ProcessedFiles (
            FileID INT PRIMARY KEY IDENTITY(1,1),
            FilePath VARCHAR(500) NOT NULL,
            FileName VARCHAR(255) NOT NULL,
            LastModifiedDate DATETIME NOT NULL,
            ProcessedDate DATETIME NOT NULL,
            FileHash VARCHAR(64),
			[RowCount] INT NOT NULL,
			ColumnHash VARCHAR(64) NOT NULL,
			ProcessedDataHash VARCHAR(64) NULL
        );
        CREATE INDEX IX_ProcessedFiles_FileName ON Timesheet.ProcessedFiles(FileName);
        PRINT 'ProcessedFiles table created.';
    END;

    -- AuditLog Table
 IF OBJECT_ID('Timesheet.AuditLog') IS NOT NULL
    DROP TABLE Timesheet.AuditLog;

CREATE TABLE Timesheet.AuditLog (
    AuditID INT PRIMARY KEY IDENTITY(1,1),
    EmployeeName NVARCHAR(255),
    FileName VARCHAR(255),
    TableName VARCHAR(50) NOT NULL,
    Action VARCHAR(20) NOT NULL CHECK (Action IN ('Insert', 'Update', 'Delete')),
    Message NVARCHAR(1000),
    ProcessedDate DATETIME NOT NULL DEFAULT GETDATE()
);
CREATE INDEX IX_AuditLog_ProcessedDate ON Timesheet.AuditLog(ProcessedDate);
CREATE INDEX IX_AuditLog_EmployeeName ON Timesheet.AuditLog(EmployeeName);
PRINT 'AuditLog table created or altered.';

    -- ErrorLog Table
    IF OBJECT_ID('Timesheet.ErrorLog', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.ErrorLog (
            ErrorLogID INT IDENTITY(1,1) PRIMARY KEY,
            ErrorDate DATETIME NOT NULL DEFAULT GETDATE(),
            ErrorTask NVARCHAR(255) NOT NULL,
            ErrorDescription NVARCHAR(MAX) NOT NULL,
            SourceComponent NVARCHAR(255) NULL,
            UserName NVARCHAR(100) NULL
        );
        PRINT 'ErrorLog table created.';
    END;

    -- TimesheetStaging Table
    CREATE TABLE Timesheet.TimesheetStaging (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        [Date] NVARCHAR(50),
        [DayOfWeek] VARCHAR(10),
        ClientName VARCHAR(100),
        ProjectName VARCHAR(100),
        ActivityName VARCHAR(50),
        BillableStatus VARCHAR(20),
        Comments NVARCHAR(MAX),
        TotalHours NVARCHAR(50),
        StartTime NVARCHAR(50),
        EndTime NVARCHAR(50),
        EmployeeName NVARCHAR(255),
        FileName NVARCHAR(255),
        ProcessedDate DATETIME DEFAULT GETDATE(),
        IsValid BIT DEFAULT 0
    );
    PRINT 'TimesheetStaging table created.';

    -- StagingLeaveRequest Table
    IF OBJECT_ID('Timesheet.StagingLeaveRequest', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.StagingLeaveRequest (
            StagingID INT IDENTITY(1,1) PRIMARY KEY,
            LeaveTypeName NVARCHAR(255),
            StartDate NVARCHAR(50),
            EndDate NVARCHAR(50),
            NumberOfDays NVARCHAR(50),
            ApprovalObtained NVARCHAR(50),
            SickNote NVARCHAR(50),
            EmployeeName NVARCHAR(255),
            FileName NVARCHAR(255),
            ProcessedDate DATETIME DEFAULT GETDATE(),
            IsValid BIT DEFAULT 0
        );
        PRINT 'StagingLeaveRequest table created.';
    END;

    -- StagingForecast Table
    CREATE TABLE Timesheet.StagingForecast (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        ForecastedHours NVARCHAR(50),
        ForecastedWorkDays NVARCHAR(50),
        BillableHours NVARCHAR(50),
        NonBillableHours NVARCHAR(50),
        TotalHours NVARCHAR(50),
        EmployeeName NVARCHAR(255),
        FileName NVARCHAR(255),
        ProcessedDate DATETIME DEFAULT GETDATE()
    );
    PRINT 'StagingForecast table created.';

    -- ProjectStaging Table
    CREATE TABLE Timesheet.ProjectStaging (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectName NVARCHAR(255) NOT NULL,
        ClientName NVARCHAR(255) NOT NULL,
        FileName VARCHAR(255) NOT NULL,
        ProcessedDate DATETIME DEFAULT GETDATE(),
        IsProcessed BIT DEFAULT 0
    );
    CREATE INDEX IX_ProjectStaging_ProjectName ON Timesheet.ProjectStaging(ProjectName);
    CREATE INDEX IX_ProjectStaging_ClientName ON Timesheet.ProjectStaging(ClientName);
    CREATE INDEX IX_ProjectStaging_FileName ON Timesheet.ProjectStaging(FileName);
    PRINT 'ProjectStaging table created.';

    -- ActivityLeaveStaging Table
    CREATE TABLE Timesheet.ActivityLeaveStaging (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        ActivityOrLeaveType NVARCHAR(255) NOT NULL,
        FileName VARCHAR(255) NOT NULL,
        EmployeeName NVARCHAR(255),
        ProcessedDate DATETIME DEFAULT GETDATE(),
        IsProcessed BIT DEFAULT 0
    );
    CREATE INDEX IX_ActivityLeaveStaging_ActivityOrLeaveType ON Timesheet.ActivityLeaveStaging(ActivityOrLeaveType);
    CREATE INDEX IX_ActivityLeaveStaging_FileName ON Timesheet.ActivityLeaveStaging(FileName);
    PRINT 'ActivityLeaveStaging table created.';

    -- LeaveRequest Table
    CREATE TABLE Timesheet.LeaveRequest (
        LeaveRequestID INT IDENTITY(1,1) PRIMARY KEY,
        EmployeeID INT NOT NULL,
        LeaveTypeID INT NOT NULL,
        StartDate DATE NOT NULL,
        EndDate DATE NOT NULL,
        Status NVARCHAR(20) NOT NULL CHECK (Status IN ('Pending', 'Approved', 'Rejected')),
        ApprovalObtained BIT NOT NULL DEFAULT 0,
        SickNoteSubmitted BIT NULL,
        CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_LeaveRequest_Employee FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
        CONSTRAINT FK_LeaveRequest_LeaveType FOREIGN KEY (LeaveTypeID) REFERENCES Timesheet.LeaveType(LeaveType)
    );
    PRINT 'LeaveRequest table created.';

    -- FileEmployeeMapping Table
    IF OBJECT_ID('Timesheet.FileEmployeeMapping', 'U') IS NULL
    BEGIN
        CREATE TABLE Timesheet.FileEmployeeMapping (
            FileNamePattern VARCHAR(255) PRIMARY KEY,
            EmployeeID INT NOT NULL,
            FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID)
        );
        PRINT 'FileEmployeeMapping table created.';
    END;
END;
GO

-- Execute table creation
EXEC Timesheet.CreateTimesheetTables;
GO

-- Reset procedures
CREATE OR ALTER PROCEDURE Timesheet.ResetEmployee
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Employee;
    ALTER SEQUENCE Timesheet.EmployeeSeq RESTART WITH 1000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetClient
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Client;
    ALTER SEQUENCE Timesheet.ClientSeq RESTART WITH 2000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetProject
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Project;
    ALTER SEQUENCE Timesheet.ProjectSeq RESTART WITH 3000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetLeaveType
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.LeaveType;
    ALTER SEQUENCE Timesheet.LeaveTypeSeq RESTART WITH 4000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetActivity
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Activity;
    ALTER SEQUENCE Timesheet.ActivitySeq RESTART WITH 5000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetTimesheet
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Timesheet;
    ALTER SEQUENCE Timesheet.TimesheetSeq RESTART WITH 6000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetLeave
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.LeaveRequest;
    DBCC CHECKIDENT ('Timesheet.LeaveRequest', RESEED, 0);
END;
GO

CREATE OR ALTER PROCEDURE [Timesheet].[ResetForecast]
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Timesheet.Forecast;
    ALTER SEQUENCE Timesheet.ForecastSeq RESTART WITH 7000;
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetDescription
AS
BEGIN
	SET NOCOUNT ON;
	DELETE FROM Timesheet.Description;
    ALTER SEQUENCE Timesheet.DescriptionSeq RESTART WITH 8000;
END
GO

CREATE OR ALTER PROCEDURE Timesheet.ResetAll
AS
BEGIN
    SET NOCOUNT ON;
    EXEC Timesheet.ResetForecast;
    EXEC Timesheet.ResetLeave;
    EXEC Timesheet.ResetTimesheet;
    EXEC Timesheet.ResetActivity;
    EXEC Timesheet.ResetLeaveType;
    EXEC Timesheet.ResetProject;
    EXEC Timesheet.ResetClient;
	EXEC Timesheet.ResetDescription
    EXEC Timesheet.ResetEmployee;
END;
GO

-- Timesheet processing procedure to prevent DescriptionID 8020
IF OBJECT_ID('Timesheet.ProcessTimesheetStaging', 'P') IS NOT NULL
    DROP PROCEDURE Timesheet.ProcessTimesheetStaging;
GO
CREATE PROCEDURE Timesheet.ProcessTimesheetStaging
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        -- Step 0: Log records with missing or invalid mappings, including DescriptionID 8020
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'TimesheetStaging' AS TableName,
            'Skipped' AS Action,
            'Data error(s): ' +
                CASE WHEN e.EmployeeID IS NULL THEN 'Missing EmployeeID; ' ELSE '' END +
                CASE WHEN c.ClientID IS NULL AND s.ClientName IS NOT NULL THEN 'Missing ClientID; ' ELSE '' END +
                CASE WHEN p.ProjectID IS NULL AND s.ProjectName IS NOT NULL THEN 'Missing ProjectID; ' ELSE '' END +
                CASE WHEN d.DescriptionID IS NULL THEN 'Missing Description; ' 
                     WHEN d.DescriptionID = 8020 THEN 'Public Holiday (DescriptionID 8020); ' 
                     ELSE '' END +
                CASE WHEN TRY_CONVERT(DATE, s.[Date]) IS NULL THEN 'Invalid Date; ' ELSE '' END +
                CASE WHEN TRY_CONVERT(TIME, s.StartTime) IS NULL THEN 'Invalid StartTime; ' ELSE '' END +
                CASE WHEN TRY_CONVERT(TIME, s.EndTime) IS NULL THEN 'Invalid EndTime; ' ELSE '' END,
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        LEFT JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        LEFT JOIN Timesheet.Client c ON s.ClientName = c.ClientName
        LEFT JOIN Timesheet.Project p ON s.ProjectName = p.ProjectName AND p.ClientID = c.ClientID
        LEFT JOIN Timesheet.Description d ON s.ActivityName = d.DescriptionName
        WHERE s.IsValid = 1 AND (
            e.EmployeeID IS NULL OR
            (s.ClientName IS NOT NULL AND c.ClientID IS NULL) OR
            (s.ProjectName IS NOT NULL AND p.ProjectID IS NULL) OR
            d.DescriptionID IS NULL OR
            d.DescriptionID = 8020 OR
            TRY_CONVERT(DATE, s.[Date]) IS NULL OR
            TRY_CONVERT(TIME, s.StartTime) IS NULL OR
            TRY_CONVERT(TIME, s.EndTime) IS NULL
        );

        -- Step 1: Log skipped/duplicate records
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'TimesheetStaging' AS TableName,
            'Skipped' AS Action,
            'Duplicate timesheet entry found for project: ' + 
                COALESCE(s.ProjectName, 'Unknown') + 
                ', Hours: ' + COALESCE(CAST(s.TotalHours AS NVARCHAR(10)), '0') AS Message,
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        LEFT JOIN Timesheet.Client c ON s.ClientName = c.ClientName
        LEFT JOIN Timesheet.Project p ON s.ProjectName = p.ProjectName AND p.ClientID = c.ClientID
        JOIN Timesheet.Timesheet t ON 
            e.EmployeeID = t.EmployeeID
            AND TRY_CONVERT(DATE, s.[Date]) = t.[Date]
            AND TRY_CONVERT(TIME, s.StartTime) = t.StartTime
            AND TRY_CONVERT(TIME, s.EndTime) = t.EndTime
            AND COALESCE(c.ClientID, -1) = COALESCE(t.ClientID, -1)
            AND COALESCE(p.ProjectID, -1) = COALESCE(t.ProjectID, -1)
        WHERE s.IsValid = 1;

        -- Step 2: Insert valid, non-duplicate records, excluding DescriptionID 8020
        INSERT INTO Timesheet.Timesheet (
            EmployeeID, [Date], [DayOfWeek], ClientID, ProjectID, DescriptionID,
            BillableStatus, Comments, TotalHours, StartTime, EndTime
        )
        SELECT 
            e.EmployeeID,
            TRY_CONVERT(DATE, s.[Date]),
            s.[DayOfWeek],
            c.ClientID,
            p.ProjectID,
            d.DescriptionID,
            s.BillableStatus,
            s.Comments,
            TRY_CONVERT(DECIMAL(5,2), s.TotalHours),
            TRY_CONVERT(TIME, s.StartTime),
            TRY_CONVERT(TIME, s.EndTime)
        FROM Timesheet.TimesheetStaging s
        LEFT JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        LEFT JOIN Timesheet.Client c ON s.ClientName = c.ClientName
        LEFT JOIN Timesheet.Project p ON s.ProjectName = p.ProjectName AND p.ClientID = c.ClientID
        LEFT JOIN Timesheet.Description d ON s.ActivityName = d.DescriptionName
        WHERE s.IsValid = 1
          AND e.EmployeeID IS NOT NULL
          AND d.DescriptionID IS NOT NULL AND d.DescriptionID <> 8020
          AND NOT EXISTS (
                SELECT 1
                FROM Timesheet.Timesheet t
                WHERE t.EmployeeID = e.EmployeeID
                  AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
                  AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
                  AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
                  AND COALESCE(t.ClientID, -1) = COALESCE(c.ClientID, -1)
                  AND COALESCE(t.ProjectID, -1) = COALESCE(p.ProjectID, -1)
            );

        -- Step 3: Log inserted records
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet' AS TableName,
            'Insert' AS Action,
            'New timesheet inserted: ' + COALESCE(s.ProjectName, 'Unknown') + ', Hours: ' + COALESCE(CAST(s.TotalHours AS NVARCHAR(10)), '0'),
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        JOIN Timesheet.Timesheet t ON t.EmployeeID = e.EmployeeID
            AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
            AND t.TotalHours = TRY_CONVERT(DECIMAL(5,2), s.TotalHours)
        WHERE s.IsValid = 1;

        -- Step 4: Log updates
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet' AS TableName,
            'Update' AS Action,
            'Timesheet updated for project: ' + COALESCE(s.ProjectName, 'Unknown') + ', New Hours: ' + COALESCE(CAST(s.TotalHours AS NVARCHAR(10)), '0'),
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        JOIN Timesheet.Timesheet t ON t.EmployeeID = e.EmployeeID
            AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
            AND t.TotalHours = TRY_CONVERT(DECIMAL(5,2), s.TotalHours)
        WHERE s.IsValid = 1;

        -- Step 5: Delete records with -1 hours
        DELETE t
        FROM Timesheet.Timesheet t
        JOIN Timesheet.Employee e ON e.EmployeeID = t.EmployeeID
        JOIN Timesheet.TimesheetStaging s ON s.EmployeeName = e.EmployeeName
            AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
            AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
            AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
        WHERE s.IsValid = 1
          AND TRY_CONVERT(DECIMAL(5,2), s.TotalHours) = -1;

        -- Step 6: Log deleted records
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet' AS TableName,
            'Delete' AS Action,
            'Timesheet deleted for project: ' + COALESCE(s.ProjectName, 'Unknown'),
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        JOIN Timesheet.Timesheet t ON t.EmployeeID = e.EmployeeID
            AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
            AND t.TotalHours = TRY_CONVERT(DECIMAL(5,2), s.TotalHours)
        WHERE s.IsValid = 1
          AND TRY_CONVERT(DECIMAL(5,2), s.TotalHours) = -1
          AND NOT EXISTS (SELECT 1 FROM Timesheet.Timesheet t2 WHERE t2.Timesheet_ID = t.Timesheet_ID);
    END TRY
    BEGIN CATCH
        INSERT INTO Timesheet.ErrorLog (
            ErrorDate,
            ErrorTask,
            ErrorDescription,
            SourceComponent,
            UserName
        )
        VALUES (
            GETDATE(),
            'Timesheet Import Process',
            ERROR_MESSAGE(),
            'TimesheetETL',
            SYSTEM_USER
        );
        THROW;
    END CATCH;
END;
GO
