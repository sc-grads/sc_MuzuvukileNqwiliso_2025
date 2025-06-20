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

    -- Description Table
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
	    [FileName] NVARCHAR(255) NULL,
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
        DROP TABLE Timesheet.ProcessedFiles;
   CREATE TABLE Timesheet.ProcessedFiles (
    FileID INT PRIMARY KEY IDENTITY(1,1),
    FilePath VARCHAR(500) NOT NULL,
    FileName VARCHAR(255) NOT NULL,
    EmployeeName NVARCHAR(255) NOT NULL,
    [RowCount] INT NOT NULL,
    LastModifiedDate DATETIME NOT NULL,
    ProcessedDate DATETIME NOT NULL DEFAULT GETDATE()
);

CREATE INDEX IX_ProcessedFiles_FileName ON Timesheet.ProcessedFiles(FileName);

PRINT 'ProcessedFiles table created with columns matching the script.';

    -- AuditLog Table
    IF OBJECT_ID('Timesheet.AuditLog', 'U') IS NOT NULL
        DROP TABLE Timesheet.AuditLog;
    CREATE TABLE Timesheet.AuditLog (
        AuditID INT PRIMARY KEY IDENTITY(1,1),
        EmployeeName NVARCHAR(255) NOT NULL,
        FileName VARCHAR(255) NOT NULL,
		[Month] NVARCHAR(20) NOT NULL,
        TableName VARCHAR(50) NOT NULL,
        Action VARCHAR(20) NOT NULL CHECK (Action IN ('Insert', 'Update', 'Delete','NoChange')),
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
            UserName NVARCHAR(100) NULL,
            ProcessedDate DATETIME NOT NULL DEFAULT GETDATE()
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

BEGIN TRY
    BEGIN TRANSACTION;
    EXEC Timesheet.CreateTimesheetTables;
    -- View creation code here
    COMMIT TRANSACTION;
    PRINT 'Database setup completed successfully.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    PRINT 'Error occurred: ' + @ErrorMessage;
END CATCH;
GO

-- Create view for clean Timesheet display without IDs
IF OBJECT_ID('Timesheet.vw_TimesheetDisplay', 'V') IS NOT NULL
    DROP VIEW Timesheet.vw_TimesheetDisplay;
GO
CREATE VIEW Timesheet.vw_TimesheetDisplay
AS
SELECT 
    e.EmployeeName,
    t.[Date],
    t.[DayOfWeek],
    c.ClientName,
    p.ProjectName,
    d.DescriptionName AS ActivityOrLeave,
    t.BillableStatus,
    t.Comments,
    t.TotalHours,
    t.StartTime,
    t.EndTime
FROM Timesheet.Timesheet t
INNER JOIN Timesheet.Employee e ON t.EmployeeID = e.EmployeeID
LEFT JOIN Timesheet.Client c ON t.ClientID = c.ClientID
LEFT JOIN Timesheet.Project p ON t.ProjectID = p.ProjectID
INNER JOIN Timesheet.Description d ON t.DescriptionID = d.DescriptionID;
GO
PRINT 'View vw_TimesheetDisplay created.';
GO

-- ProcessFiles Stored Procedure
CREATE OR ALTER PROCEDURE Timesheet.usp_ProcessTimesheetFile
(
    @IsNewFile BIT,
    @EmployeeName NVARCHAR(255),
    @FileName NVARCHAR(255),
    @FilePath NVARCHAR(500),
    @RowCount INT,
    @TimesheetMonth NVARCHAR(50),
    @LastModified NVARCHAR(10)
)
AS
BEGIN
    SET NOCOUNT ON;

    IF @IsNewFile = 1
    BEGIN
        -- New file processing
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        VALUES (
            @EmployeeName, @FileName, 'TimesheetStaging', 'Insert', 
            'New timesheet processed - ' + CAST(@RowCount AS NVARCHAR(10)) + ' rows',
            @TimesheetMonth, GETDATE()
        );

        INSERT INTO Timesheet.ProcessedFiles (
            FilePath, FileName, EmployeeName, [RowCount], LastModifiedDate, ProcessedDate
        )
        VALUES (
            @FilePath, @FileName, @EmployeeName, @RowCount,
            CAST(@LastModified AS DATETIME), GETDATE()
        );
    END
    ELSE
    BEGIN
        -- MODIFIED file logic

        -- Deleted rows
        WITH DeletedRows AS (
            SELECT 
                e.EmployeeName,
                t.FileName,
                t.Date,
                t.StartTime,
                t.EndTime,
                ROW_NUMBER() OVER (
                    PARTITION BY e.EmployeeName, t.FileName
                    ORDER BY t.Date, t.StartTime, t.EndTime
                ) AS RowNum
            FROM Timesheet.Timesheet t
            JOIN Timesheet.Employee e ON t.EmployeeID = e.EmployeeID
            WHERE e.EmployeeName = @EmployeeName
              AND t.FileName = @FileName
              AND NOT EXISTS (
                  SELECT 1
                  FROM Timesheet.TimesheetStaging s
                  WHERE s.EmployeeName = e.EmployeeName
                    AND s.Date = t.Date
                    AND s.StartTime = t.StartTime
                    AND s.EndTime = t.EndTime
                    AND s.FileName = t.FileName
              )
        )
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        SELECT 
            EmployeeName,
            FileName,
            'Timesheet',
            'Delete',
            'Row ' + CAST(RowNum AS NVARCHAR(10)) + ' deleted: ' +
                ISNULL(CONVERT(NVARCHAR(10), Date, 120), '??') + ', ' +
                ISNULL(FORMAT(StartTime, 'hh\:mm'), '??') + ' - ' +
                ISNULL(FORMAT(EndTime, 'hh\:mm'), '??'),
            @TimesheetMonth,
            GETDATE()
        FROM DeletedRows;

        -- Updated rows
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet',
            'Update',
            'Updated row: ' +
                ISNULL(CONVERT(NVARCHAR(10), s.Date, 120), '??') + ', ' +
                ISNULL(FORMAT(TRY_CAST(s.StartTime AS TIME), 'hh\:mm'), '??') + ' - ' +
                ISNULL(FORMAT(TRY_CAST(s.EndTime AS TIME), 'hh\:mm'), '??'),
            @TimesheetMonth,
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        JOIN Timesheet.Timesheet t ON t.EmployeeID = e.EmployeeID
            AND t.Date = s.Date
            AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
            AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
            AND t.FileName = s.FileName
        WHERE s.EmployeeName = @EmployeeName
          AND s.FileName = @FileName
          AND (
              TRY_CONVERT(DECIMAL(5,2), s.TotalHours) != t.TotalHours OR
              ISNULL(CAST(s.Comments AS NVARCHAR(MAX)), '') != ISNULL(CAST(t.Comments AS NVARCHAR(MAX)), '')
          );

        -- Inserted rows
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet',
            'Insert',
            'Inserted new row: ' +
                ISNULL(CONVERT(NVARCHAR(10), s.Date, 120), '??') + ', ' +
                ISNULL(FORMAT(TRY_CAST(s.StartTime AS TIME), 'hh\:mm'), '??') + ' - ' +
                ISNULL(FORMAT(TRY_CAST(s.EndTime AS TIME), 'hh\:mm'), '??'),
            @TimesheetMonth,
            GETDATE()
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        WHERE s.EmployeeName = @EmployeeName
          AND s.FileName = @FileName
          AND NOT EXISTS (
              SELECT 1 FROM Timesheet.Timesheet t
              WHERE t.EmployeeID = e.EmployeeID
                AND t.Date = s.Date
                AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
                AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
                AND t.FileName = s.FileName
          );

        -- If no changes
        IF NOT EXISTS (
            SELECT 1 FROM Timesheet.Timesheet t
            JOIN Timesheet.Employee e ON t.EmployeeID = e.EmployeeID
            WHERE e.EmployeeName = @EmployeeName
              AND t.FileName = @FileName
              AND NOT EXISTS (
                  SELECT 1 FROM Timesheet.TimesheetStaging s
                  WHERE s.EmployeeName = e.EmployeeName
                    AND s.Date = t.Date
                    AND s.StartTime = t.StartTime
                    AND s.EndTime = t.EndTime
                    AND s.FileName = t.FileName
              )
            UNION
            SELECT 1 FROM Timesheet.TimesheetStaging s
            JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
            JOIN Timesheet.Timesheet t ON t.EmployeeID = e.EmployeeID
                AND t.Date = s.Date
                AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
                AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
                AND t.FileName = s.FileName
            WHERE s.EmployeeName = @EmployeeName
              AND s.FileName = @FileName
              AND (
                  TRY_CONVERT(DECIMAL(5,2), s.TotalHours) != t.TotalHours OR
                  ISNULL(CAST(s.Comments AS NVARCHAR(MAX)), '') != ISNULL(CAST(t.Comments AS NVARCHAR(MAX)), '')
              )
            UNION
            SELECT 1 FROM Timesheet.TimesheetStaging s
            JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
            WHERE s.EmployeeName = @EmployeeName
              AND s.FileName = @FileName
              AND NOT EXISTS (
                  SELECT 1 FROM Timesheet.Timesheet t
                  WHERE t.EmployeeID = e.EmployeeID
                    AND t.Date = s.Date
                    AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
                    AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
                    AND t.FileName = s.FileName
              )
        )
        BEGIN
            INSERT INTO Timesheet.AuditLog (
                EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
            )
            VALUES (
                @EmployeeName, @FileName, 'Timesheet', 'NoChange',
                'Modified file processed but no changes detected.',
                @TimesheetMonth, GETDATE()
            );
        END

        -- Update ProcessedFiles table
        UPDATE Timesheet.ProcessedFiles
        SET [RowCount] = @RowCount,
            LastModifiedDate = CAST(@LastModified AS DATETIME),
            ProcessedDate = GETDATE()
        WHERE FilePath = @FilePath;
    END
END
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
END;
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
    EXEC Timesheet.ResetDescription;
    EXEC Timesheet.ResetEmployee;
END;
GO