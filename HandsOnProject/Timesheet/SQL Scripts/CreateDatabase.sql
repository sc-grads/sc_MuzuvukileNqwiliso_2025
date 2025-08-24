SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO
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
            LeaveTypeID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.LeaveTypeSeq,
            LeaveTypeName VARCHAR(50) NOT NULL,
            CONSTRAINT CHK_LeaveType_Name CHECK (LeaveTypeName <> '')
        );
        CREATE INDEX IX_LeaveType_LeaveType_ID ON Timesheet.LeaveType(LeaveTypeID);
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
		DescriptionType VARCHAR(10) NOT NULL CHECK (DescriptionType IN ('Activity', 'Leave')),
		DescriptionName VARCHAR(100) NOT NULL
		);
        PRINT 'Description table created.';
    END;

	IF OBJECT_ID('Timesheet.DescriptionActivity', 'U') IS NULL
	-- Bridge to Activity
	BEGIN
	CREATE TABLE Timesheet.DescriptionActivity (
		DescriptionID INT PRIMARY KEY,
		ActivityID INT NOT NULL,
		FOREIGN KEY (DescriptionID) REFERENCES Timesheet.Description(DescriptionID),
		FOREIGN KEY (ActivityID) REFERENCES Timesheet.Activity(ActivityID)
	);
	 PRINT 'DescriptionActivity table created.';
	END;

	IF OBJECT_ID('Timesheet.DescriptionLeave', 'U') IS NULL
	BEGIN
	-- Bridge to LeaveType
	CREATE TABLE Timesheet.DescriptionLeave (
		DescriptionID INT PRIMARY KEY,
		LeaveTypeID INT NOT NULL,
		FOREIGN KEY (DescriptionID) REFERENCES Timesheet.Description(DescriptionID),
		FOREIGN KEY (LeaveTypeID) REFERENCES Timesheet.LeaveType(LeaveTypeID)
	);
	 PRINT 'DescriptionLeave table created.';
	END;

    -- Timesheet Table
    CREATE TABLE Timesheet.Timesheet (
        TimesheetID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.TimesheetSeq,
        EmployeeID INT NOT NULL,
        [Date] DATE NOT NULL,
        [DayOfWeek] VARCHAR(10) NOT NULL CHECK ([DayOfWeek] IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
        ClientID INT,
        ProjectID INT,
        DescriptionID INT NOT NULL,
        BillableStatus VARCHAR(20) NOT NULL CHECK (BillableStatus IN ('Billable', 'Non-Billable')),
        Comments  NVARCHAR(MAX),
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
    PRINT 'Timesheet table created successfully.';

    -- Forecast Table
    CREATE TABLE Timesheet.Forecast (
        ForecastID INT PRIMARY KEY DEFAULT NEXT VALUE FOR Timesheet.ForecastSeq,
        EmployeeID INT NOT NULL,
        ForecastMonth DATE NOT NULL,
        ForecastedHours DECIMAL(10,2) NOT NULL DEFAULT (168.00),
        ForecastedWorkDays INT NOT NULL DEFAULT (21),
        NonBillableHours DECIMAL(10,2) NOT NULL,
        BillableHours DECIMAL(10,2) NOT NULL,
        TotalHours DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
        CONSTRAINT UQ_Forecast_Employee_Month UNIQUE (EmployeeID, ForecastMonth)
       -- CONSTRAINT CK_Forecast_Total_vs_Planned CHECK (TotalHours >= ForecastedHours)
    );
    PRINT 'Forecast table created.';

	 -- ProcessedFiles Table
	IF OBJECT_ID('Timesheet.ProcessedFiles', 'U') IS NOT NULL
		DROP TABLE Timesheet.ProcessedFiles;

	CREATE TABLE Timesheet.ProcessedFiles (
		FileID INT PRIMARY KEY IDENTITY(1,1),
		FilePath VARCHAR(500) NOT NULL,
		FileName VARCHAR(255) NOT NULL,
		EmployeeID INT NOT NULL,  
		[RowCount] INT NOT NULL,
		DataHash VARCHAR(64),
		LastModifiedDate DATETIME NOT NULL,
		ProcessedDate DATETIME NOT NULL DEFAULT GETDATE(),
		CONSTRAINT FK_ProcessedFiles_Employee
		FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID)
	);


CREATE INDEX IX_ProcessedFiles_FileName ON Timesheet.ProcessedFiles(FileName);

PRINT 'ProcessedFiles table created.';

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
		RunID NVARCHAR(40) NULL,
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

	-- Index for performance
	CREATE INDEX IX_TimesheetStaging_RunID 
	ON Timesheet.TimesheetStaging(RunID, FileName, EmployeeName);

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
		NumberOfDays AS DATEDIFF(DAY, StartDate, EndDate) + 1 PERSISTED,
		Status NVARCHAR(20) NOT NULL CHECK (Status IN ('Pending', 'Approved', 'Rejected')),
		ApprovalObtained BIT NOT NULL DEFAULT 0,
		SickNoteSubmitted BIT NULL,
		CreatedDate DATETIME NOT NULL DEFAULT GETDATE(),
		CONSTRAINT CK_LeaveRequest_MaxDays 
			CHECK (DATEDIFF(DAY, StartDate, EndDate) + 1 BETWEEN 1 AND 10),
		CONSTRAINT FK_LeaveRequest_Employee 
			FOREIGN KEY (EmployeeID) REFERENCES Timesheet.Employee(EmployeeID),
		CONSTRAINT FK_LeaveRequest_LeaveType 
			FOREIGN KEY (LeaveTypeID) REFERENCES Timesheet.LeaveType(LeaveTypeID)
	);
    PRINT 'LeaveRequest table created.';

END;
GO

CREATE OR ALTER PROCEDURE Timesheet.CreateView
AS
BEGIN
    SET NOCOUNT ON;

    IF OBJECT_ID('Timesheet.vw_TimesheetDisplay', 'V') IS NOT NULL
        DROP VIEW Timesheet.vw_TimesheetDisplay;

    DECLARE @sql NVARCHAR(MAX);
    SET @sql = '
        
        CREATE VIEW Timesheet.vw_TimesheetDisplay AS
        SELECT 
            e.EmployeeName,
            t.[Date],
            t.[DayOfWeek],
            c.ClientName,
            p.ProjectName,
            d.DescriptionName AS [Description],
            t.BillableStatus,
            t.Comments,
            t.TotalHours,
            COALESCE(LEFT(CONVERT(VARCHAR(5), t.StartTime, 108), 5), ''N/A'') AS StartTime,
            COALESCE(LEFT(CONVERT(VARCHAR(5), t.EndTime, 108), 5), ''N/A'') AS EndTime
        FROM Timesheet.Timesheet t
        INNER JOIN Timesheet.Employee e ON t.EmployeeID = e.EmployeeID
        LEFT JOIN Timesheet.Client c ON t.ClientID = c.ClientID
        LEFT JOIN Timesheet.Project p ON t.ProjectID = p.ProjectID
        INNER JOIN Timesheet.Description d ON t.DescriptionID = d.DescriptionID;
    ';

    EXEC sp_executesql @sql;

    PRINT 'View vw_TimesheetDisplay created.';
END;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    -- Step 3: Run the table creation procedure
    EXEC Timesheet.CreateTimesheetTables;

    -- Step 4: Now the view procedure can be safely executed
    EXEC Timesheet.CreateView;

    COMMIT TRANSACTION;
    PRINT 'Database setup completed successfully.';
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    PRINT 'Error occurred: ' + @ErrorMessage;
END CATCH;
GO


CREATE OR ALTER PROCEDURE Timesheet.usp_UpsertEmployee
    @EmployeeName NVARCHAR(255),
    @FileName NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        DECLARE @IsNewEmployee BIT = 0;

        -- Step 1: Insert employee if they don't exist
        IF NOT EXISTS (SELECT 1 FROM Timesheet.Employee WHERE EmployeeName = @EmployeeName)
        BEGIN
            INSERT INTO Timesheet.Employee (EmployeeName)
            VALUES (@EmployeeName);

            SET @IsNewEmployee = 1;
        END

        -- Step 2: Always audit per file, only if it hasn’t been audited already for that file
        IF NOT EXISTS (
            SELECT 1 
            FROM Timesheet.AuditLog 
            WHERE EmployeeName = @EmployeeName 
              AND FileName = @FileName 
              AND TableName = 'Employee' 
              AND Action = 'Insert'
        )
        BEGIN
            INSERT INTO Timesheet.AuditLog (
                EmployeeName,
                FileName,
                [Month],
                TableName,
                Action,
                Message,
                ProcessedDate
            )
            VALUES (
                @EmployeeName,
                @FileName,
                'Not Applicable',
                'Employee',
                'Insert',
                CASE 
                    WHEN @IsNewEmployee = 1 THEN 'New employee added to the system'
                    ELSE 'Employee already existed; associated with a new file'
                END,
                GETDATE()
            );
        END
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
            'usp_UpsertEmployee',
            ERROR_MESSAGE(),
            'Employee_Upsert',
            SYSTEM_USER
        );
    END CATCH
END;
GO


-- Insert Activity and Leave
CREATE OR ALTER PROCEDURE  Timesheet.usp_InsertActivityLeaveData
    @TimesheetMonth NVARCHAR(20)  -- Passed from Script Task
AS
BEGIN
    BEGIN TRY
        DECLARE @ActivityRows INT = 0;
        DECLARE @LeaveTypeRows INT = 0;
        DECLARE @AuditMessage NVARCHAR(1000);

        -- Create temp table for employee-file-activity/leave records
        CREATE TABLE #EmployeeActivityFiles (
            EmployeeName NVARCHAR(255),
            FileName NVARCHAR(255),
            ActivityOrLeaveType NVARCHAR(255),
            IsLeaveType BIT
        );

        -- Extract employee names and classify as activity/leave
        WITH MonthPositions AS (
            SELECT 
                als.FileName,
                als.ActivityOrLeaveType,
                NULLIF(
                    (SELECT MIN(pos) 
                     FROM (VALUES
                         (NULLIF(CHARINDEX('January', als.FileName), 0)),
                         (NULLIF(CHARINDEX('February', als.FileName), 0)),
                         (NULLIF(CHARINDEX('March', als.FileName), 0)),
                         (NULLIF(CHARINDEX('April', als.FileName), 0)),
                         (NULLIF(CHARINDEX('May', als.FileName), 0)),
                         (NULLIF(CHARINDEX('June', als.FileName), 0)),
                         (NULLIF(CHARINDEX('July', als.FileName), 0)),
                         (NULLIF(CHARINDEX('August', als.FileName), 0)),
                         (NULLIF(CHARINDEX('September', als.FileName), 0)),
                         (NULLIF(CHARINDEX('October', als.FileName), 0)),
                         (NULLIF(CHARINDEX('November', als.FileName), 0)),
                         (NULLIF(CHARINDEX('December', als.FileName), 0))
                     ) AS positions(pos)
                     WHERE pos IS NOT NULL)
                , 0) AS MonthPosition
            FROM Timesheet.ActivityLeaveStaging als
        )
        INSERT INTO #EmployeeActivityFiles (EmployeeName, FileName, ActivityOrLeaveType, IsLeaveType)
        SELECT DISTINCT
            CASE
                WHEN MonthPosition = 0 THEN 'Unknown'
                ELSE 
                    LTRIM(RTRIM(
                        REPLACE(
                            CASE
                                WHEN SUBSTRING(FileName, MonthPosition-1, 1) IN ('_', ' ') 
                                THEN LEFT(FileName, MonthPosition-2)
                                ELSE LEFT(FileName, MonthPosition-1)
                            END,
                            '_', ' '
                        )
                    ))
            END AS EmployeeName,
            FileName,
            ActivityOrLeaveType,
            CASE WHEN LOWER(ActivityOrLeaveType) LIKE '%leave%' THEN 1 ELSE 0 END AS IsLeaveType
        FROM MonthPositions;

        -- Step 1: Insert Activities
        INSERT INTO Timesheet.Activity (ActivityName)
        SELECT DISTINCT eaf.ActivityOrLeaveType
        FROM #EmployeeActivityFiles eaf
        WHERE eaf.IsLeaveType = 0
          AND NOT EXISTS (
              SELECT 1 FROM Timesheet.Activity a
              WHERE a.ActivityName = eaf.ActivityOrLeaveType
          );
        
        SET @ActivityRows = @@ROWCOUNT;

        -- Step 2: Insert LeaveTypes (if the table exists)
        IF OBJECT_ID('Timesheet.LeaveType', 'U') IS NOT NULL
        BEGIN
            INSERT INTO Timesheet.LeaveType (LeaveTypeName)
            SELECT DISTINCT eaf.ActivityOrLeaveType
            FROM #EmployeeActivityFiles eaf
            WHERE eaf.IsLeaveType = 1
              AND NOT EXISTS (
                  SELECT 1 FROM Timesheet.LeaveType lt
                  WHERE lt.LeaveTypeName = eaf.ActivityOrLeaveType
              );
            
            SET @LeaveTypeRows = @@ROWCOUNT;
        END;

        -- Step 3: Insert AuditLog entries (if the table exists)
        IF OBJECT_ID('Timesheet.AuditLog', 'U') IS NOT NULL
        BEGIN
            INSERT INTO Timesheet.AuditLog (
                EmployeeName,
                FileName,
                [Month],
                TableName,
                Action,
                Message,
                ProcessedDate
            )
            SELECT 
                eaf.EmployeeName,
                eaf.FileName,
                @TimesheetMonth,
                CASE WHEN eaf.IsLeaveType = 1 THEN 'LeaveType' ELSE 'Activity' END AS TableName,
                'Insert' AS Action,
                CASE 
                    WHEN eaf.IsLeaveType = 1 THEN 'New leave type inserted: ' + eaf.ActivityOrLeaveType
                    ELSE 'New activity inserted: ' + eaf.ActivityOrLeaveType
                END AS Message,
                GETDATE()
            FROM #EmployeeActivityFiles eaf
            WHERE (eaf.IsLeaveType = 0 AND @ActivityRows > 0)
               OR (eaf.IsLeaveType = 1 AND @LeaveTypeRows > 0);
        END;

        -- Clean up
        DROP TABLE #EmployeeActivityFiles;

        -- Audit summary message
        SET @AuditMessage = CONCAT('Inserted ', @ActivityRows, ' new activity(ies)');
        IF OBJECT_ID('Timesheet.LeaveType', 'U') IS NOT NULL
        BEGIN
            SET @AuditMessage = CONCAT(@AuditMessage, ' and ', @LeaveTypeRows, ' new leave type(s)');
        END;

        -- Output result summary
        SELECT 
            @ActivityRows AS ActivitiesInserted,
            @LeaveTypeRows AS LeaveTypesInserted,
            @AuditMessage AS AuditMessage;

    END TRY
    BEGIN CATCH
        -- Clean up temp table on error
        IF OBJECT_ID('tempdb..#EmployeeActivityFiles') IS NOT NULL
            DROP TABLE #EmployeeActivityFiles;
        
        -- Error logging
        INSERT INTO Timesheet.ErrorLog (
            ErrorDate,
            ErrorTask,
            ErrorDescription,
            SourceComponent,
            UserName
        )
        VALUES (
            GETDATE(),
            'Activity/LeaveType Import Process',
            ERROR_MESSAGE(),
            'ActivityLeaveETL',
            SYSTEM_USER
        );

        -- Rethrow the error
        THROW;
    END CATCH
END
GO

-- ProcessFiles Stored Procedure
CREATE OR ALTER PROCEDURE Timesheet.usp_ProcessTimesheetFile
(
    @IsNewFile BIT,
    @EmployeeID INT,
    @FileName NVARCHAR(255),
    @FilePath NVARCHAR(500),
    @RowCount INT,
    @TimesheetMonth NVARCHAR(50),
    @LastModified NVARCHAR(10),
    @PreviousRowCount INT,
    @PreviousDataHash NVARCHAR(64),
    @CurrentDataHash NVARCHAR(64)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @CountDifference INT;
    DECLARE @Message NVARCHAR(1000);

	 DECLARE @EmployeeName NVARCHAR(255);

    SELECT @EmployeeName = EmployeeName
    FROM Timesheet.Employee
    WHERE EmployeeID = @EmployeeID;

    IF @IsNewFile = 1
    BEGIN
        SET @Message = 'New timesheet uploaded with ' + CAST(@RowCount AS NVARCHAR(10)) + 
                      CASE WHEN @RowCount = 1 THEN ' row.' ELSE ' rows.' END;

        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, [Month], TableName, Action, Message, ProcessedDate
        )
        VALUES (
            @EmployeeName, @FileName, @TimesheetMonth, 'TimesheetStaging', 
            'Insert', @Message, GETDATE()
        );

       INSERT INTO Timesheet.ProcessedFiles (
		FilePath, FileName, EmployeeID, [RowCount], LastModifiedDate, ProcessedDate, DataHash
		)
		VALUES (
			@FilePath, @FileName, @EmployeeID, @RowCount,
			CAST(@LastModified AS DATETIME), GETDATE(), @CurrentDataHash
		);

    END
    ELSE
    BEGIN
        IF @PreviousRowCount > @RowCount
        BEGIN
            SET @CountDifference = @PreviousRowCount - @RowCount;
            SET @Message = 'Timesheet reduced by ' + CAST(@CountDifference AS NVARCHAR(10)) + 
                           CASE WHEN @CountDifference = 1 THEN ' row removed.' ELSE ' rows removed.' END;

            INSERT INTO Timesheet.AuditLog (
                EmployeeName, FileName, [Month], TableName, Action, Message, ProcessedDate
            )
            VALUES (
                @EmployeeName, @FileName, @TimesheetMonth, 'Timesheet', 
                'Delete', @Message, GETDATE()
            );
        END
        ELSE IF @PreviousRowCount < @RowCount
        BEGIN
            SET @CountDifference = @RowCount - @PreviousRowCount;
            SET @Message = 'Timesheet increased by ' + CAST(@CountDifference AS NVARCHAR(10)) + 
                           CASE WHEN @CountDifference = 1 THEN ' new row added.' ELSE ' new rows added.' END;

            INSERT INTO Timesheet.AuditLog (
                EmployeeName, FileName, [Month], TableName, Action, Message, ProcessedDate
            )
            VALUES (
                @EmployeeName, @FileName, @TimesheetMonth, 'Timesheet', 
                'Insert', @Message, GETDATE()
            );
        END
        ELSE IF @RowCount = @PreviousRowCount 
            AND (@CurrentDataHash != @PreviousDataHash 
                 OR (@PreviousDataHash IS NULL AND @CurrentDataHash IS NOT NULL)
                 OR (@PreviousDataHash IS NOT NULL AND @CurrentDataHash IS NULL))
        BEGIN
            SET @Message = 'Timesheet file was modified (content changed, row count remains the same).';

            INSERT INTO Timesheet.AuditLog (
                EmployeeName, FileName, [Month], TableName, Action, Message, ProcessedDate
            )
            VALUES (
                @EmployeeName, @FileName, @TimesheetMonth, 'Timesheet', 
                'Update', @Message, GETDATE()
            );
        END

        -- Update latest snapshot
        UPDATE Timesheet.ProcessedFiles
        SET 
            [RowCount] = @RowCount,
            LastModifiedDate = CAST(@LastModified AS DATETIME),
            ProcessedDate = GETDATE(),
            DataHash = @CurrentDataHash
        WHERE FilePath = @FilePath;
    END
END;
GO

-- Insert LeaveRequest
CREATE OR ALTER PROCEDURE Timesheet.usp_UpsertLeaveRequests
    @Month VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- Step 1: MERGE existing records
        MERGE INTO Timesheet.LeaveRequest AS target
        USING (
            SELECT 
                e.EmployeeID,
                lt.LeaveTypeID,
                MIN(TRY_CONVERT(DATE, slr.StartDate)) AS StartDate,
                MAX(TRY_CONVERT(DATE, slr.EndDate)) AS EndDate,
                CASE 
                    WHEN MAX(slr.ApprovalObtained) = 1 THEN 'Approved'
                    ELSE 'Pending'
                END AS Status,
                MAX(slr.ApprovalObtained) AS ApprovalObtained,
                COALESCE(MAX(slr.SickNote),0) AS SickNote,
                e.EmployeeName
            FROM Timesheet.StagingLeaveRequest slr
            JOIN Timesheet.Employee e ON slr.EmployeeName = e.EmployeeName
            JOIN Timesheet.LeaveType lt ON slr.LeaveTypeName = lt.LeaveTypeName
            WHERE slr.IsValid = 1
              AND slr.ProcessedDate >= DATEADD(DAY, -1, GETDATE())
            GROUP BY e.EmployeeID, lt.LeaveTypeID, e.EmployeeName
        ) AS source
        ON target.EmployeeID = source.EmployeeID
           AND target.LeaveTypeID = source.LeaveTypeID
           AND target.StartDate = source.StartDate
           AND target.EndDate = source.EndDate
        WHEN MATCHED THEN
            UPDATE SET 
                target.Status = source.Status,
                target.ApprovalObtained = source.ApprovalObtained,
                target.SickNoteSubmitted = source.SickNote;

        -- Step 2: Audit log for updates
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            [Month],
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            COALESCE(slr.EmployeeName, 'Unknown'),
            COALESCE(slr.FileName, 'Unknown'),
            @Month,
            'LeaveRequest',
            'Update',
            'Leave request updated successfully',
            GETDATE()
        FROM Timesheet.StagingLeaveRequest slr
        JOIN Timesheet.Employee e ON slr.EmployeeName = e.EmployeeName
        WHERE slr.IsValid = 1
          AND slr.ProcessedDate >= DATEADD(DAY, -1, GETDATE())
        GROUP BY slr.EmployeeName, slr.FileName;

        -- Step 3: Insert new leave requests
        INSERT INTO Timesheet.LeaveRequest (
            EmployeeID,
            LeaveTypeID,
            StartDate,
            EndDate,
            Status,
            ApprovalObtained,
            SickNoteSubmitted
        )
        SELECT 
            e.EmployeeID,
            lt.LeaveTypeID,
            MIN(TRY_CONVERT(DATE, slr.StartDate)),
            MAX(TRY_CONVERT(DATE, slr.EndDate)),
            CASE 
                WHEN MAX(slr.ApprovalObtained) = 1 THEN 'Approved'
                ELSE 'Pending'
            END,
            MAX(slr.ApprovalObtained),
            COALESCE(MAX(slr.SickNote),0)
        FROM Timesheet.StagingLeaveRequest slr
        JOIN Timesheet.Employee e ON slr.EmployeeName = e.EmployeeName
        JOIN Timesheet.LeaveType lt ON slr.LeaveTypeName = lt.LeaveTypeName
        WHERE slr.IsValid = 1
          AND slr.ProcessedDate >= DATEADD(DAY, -1, GETDATE())
          AND NOT EXISTS (
              SELECT 1
              FROM Timesheet.LeaveRequest lr
              WHERE lr.EmployeeID = e.EmployeeID
                AND lr.LeaveTypeID = lt.LeaveTypeID
                AND lr.StartDate = TRY_CONVERT(DATE, slr.StartDate)
                AND lr.EndDate = TRY_CONVERT(DATE, slr.EndDate)
          )
        GROUP BY e.EmployeeID, lt.LeaveTypeID;

        -- Step 4: Audit log for inserts
        INSERT INTO Timesheet.AuditLog (
            EmployeeName,
            FileName,
            [Month],
            TableName,
            Action,
            Message,
            ProcessedDate
        )
        SELECT 
            COALESCE(slr.EmployeeName, 'Unknown'),
            COALESCE(slr.FileName, 'Unknown'),
            @Month,
            'LeaveRequest',
            'Insert',
            'Leave request inserted successfully',
            GETDATE()
        FROM Timesheet.StagingLeaveRequest slr
        JOIN Timesheet.Employee e ON slr.EmployeeName = e.EmployeeName
        WHERE slr.IsValid = 1
          AND slr.ProcessedDate >= DATEADD(DAY, -1, GETDATE())
        GROUP BY slr.EmployeeName, slr.FileName;

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
            'usp_UpsertLeaveRequests',
            ERROR_MESSAGE(),
            'LeaveRequest_Processing',
            SYSTEM_USER
        );
    END CATCH
END;
GO

-- Insert Projects
CREATE OR ALTER PROCEDURE Timesheet.usp_InsertProjects
    @TimesheetMonth NVARCHAR(20)
AS
BEGIN
    BEGIN TRY
        DECLARE @RowsAffected INT = 0;
        DECLARE @AuditMessage NVARCHAR(1000);

        -- Step 1: Insert new projects from staging
        INSERT INTO Timesheet.Project (ProjectName, ClientID)
        SELECT DISTINCT ps.ProjectName, c.ClientID
        FROM Timesheet.ProjectStaging ps
        JOIN Timesheet.Client c ON ps.ClientName = c.ClientName
        WHERE NOT EXISTS (
            SELECT 1 FROM Timesheet.Project p
            WHERE p.ProjectName = ps.ProjectName AND p.ClientID = c.ClientID
        );

        -- Step 2: Capture number of rows inserted
        SET @RowsAffected = @@ROWCOUNT;

        -- Only proceed with auditing if rows were actually inserted
        IF @RowsAffected > 0
        BEGIN
            SET @AuditMessage = CONCAT(
                'Inserted ', @RowsAffected, 
                CASE WHEN @RowsAffected = 1 THEN ' new project' ELSE ' new projects' END
            );

            -- Step 3: Create temp table
            CREATE TABLE #EmployeeFiles (
                EmployeeName NVARCHAR(255),
                FileName NVARCHAR(255)
            );

            -- Step 4: Extract distinct employee-file pairs
            WITH MonthPositions AS (
                SELECT 
                    FileName,
                    NULLIF((
                        SELECT MIN(pos)
                        FROM (VALUES
                            (NULLIF(CHARINDEX('January', FileName), 0)),
                            (NULLIF(CHARINDEX('February', FileName), 0)),
                            (NULLIF(CHARINDEX('March', FileName), 0)),
                            (NULLIF(CHARINDEX('April', FileName), 0)),
                            (NULLIF(CHARINDEX('May', FileName), 0)),
                            (NULLIF(CHARINDEX('June', FileName), 0)),
                            (NULLIF(CHARINDEX('July', FileName), 0)),
                            (NULLIF(CHARINDEX('August', FileName), 0)),
                            (NULLIF(CHARINDEX('September', FileName), 0)),
                            (NULLIF(CHARINDEX('October', FileName), 0)),
                            (NULLIF(CHARINDEX('November', FileName), 0)),
                            (NULLIF(CHARINDEX('December', FileName), 0))
                        ) AS positions(pos)
                        WHERE pos IS NOT NULL
                    ), 0) AS MonthPosition
                FROM Timesheet.ProjectStaging
                GROUP BY FileName
            )
            INSERT INTO #EmployeeFiles (EmployeeName, FileName)
            SELECT DISTINCT
                CASE
                    WHEN MonthPosition = 0 THEN 'Unknown'
                    ELSE 
                        LTRIM(RTRIM(
                            REPLACE(
                                CASE
                                    WHEN SUBSTRING(FileName, MonthPosition-1, 1) IN ('_', ' ') 
                                    THEN LEFT(FileName, MonthPosition-2)
                                    ELSE LEFT(FileName, MonthPosition-1)
                                END,
                                '_', ' '
                            )
                        ))
                END AS EmployeeName,
                FileName
            FROM MonthPositions;

            -- Step 5: Insert into audit log only if EmployeeName/FileName exists
            IF EXISTS (SELECT 1 FROM #EmployeeFiles)
            BEGIN
                INSERT INTO Timesheet.AuditLog (
                    EmployeeName,
                    FileName,
                    [Month],
                    TableName,
                    Action,
                    Message,
                    ProcessedDate
                )
                SELECT 
                    ef.EmployeeName,
                    ef.FileName,
                    @TimesheetMonth,
                    'Project',
                    'Insert',
                    @AuditMessage,
                    GETDATE()
                FROM #EmployeeFiles ef;
            END

            DROP TABLE #EmployeeFiles;
        END

        -- Step 6: Return rows affected
        SELECT @RowsAffected AS RowsAffected;

    END TRY
    BEGIN CATCH
        -- Error logging
        INSERT INTO Timesheet.ErrorLog (
            ErrorDate,
            ErrorTask,
            ErrorDescription,
            SourceComponent,
            UserName
        )
        VALUES (
            GETDATE(),
            'Project Import Process',
            ERROR_MESSAGE(),
            'ProjectETL',
            SYSTEM_USER
        );

        IF OBJECT_ID('tempdb..#EmployeeFiles') IS NOT NULL
            DROP TABLE #EmployeeFiles;

        THROW;
    END CATCH
END;
GO

CREATE OR ALTER PROCEDURE Timesheet.usp_SkippedRecords 
    @ThisMonth VARCHAR(20)
AS
BEGIN 
    BEGIN TRY
        -- Step 1: Insert valid, non-holiday records from staging
        INSERT INTO Timesheet.Timesheet (
            EmployeeID, [Date], [DayOfWeek], ClientID, ProjectID, DescriptionID,
            BillableStatus, Comments, TotalHours, StartTime, EndTime, FileName
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
            TRY_CONVERT(TIME, s.EndTime),
            s.FileName
        FROM Timesheet.TimesheetStaging s
        JOIN Timesheet.Employee e ON s.EmployeeName = e.EmployeeName
        LEFT JOIN Timesheet.Client c ON s.ClientName = c.ClientName
        LEFT JOIN Timesheet.Project p ON s.ProjectName = p.ProjectName AND p.ClientID = c.ClientID
        JOIN Timesheet.Description d ON s.ActivityName = d.DescriptionName
        WHERE s.IsValid = 1
          AND d.DescriptionID <> 8020 -- Skip public holidays
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

        -- Step 2: Clean up hours that are -1 (but not holidays)
        DELETE t
        FROM Timesheet.Timesheet t
        JOIN Timesheet.Employee e ON e.EmployeeID = t.EmployeeID
        JOIN Timesheet.TimesheetStaging s ON s.EmployeeName = e.EmployeeName
            AND t.[Date] = TRY_CONVERT(DATE, s.[Date])
            AND t.StartTime = TRY_CONVERT(TIME, s.StartTime)
            AND t.EndTime = TRY_CONVERT(TIME, s.EndTime)
        JOIN Timesheet.Description d ON s.ActivityName = d.DescriptionName
        WHERE s.IsValid = 1
          AND TRY_CONVERT(DECIMAL(5,2), s.TotalHours) = -1
          AND d.DescriptionID <> 8020;

        -- No logging for skipped holidays (NoChange)
        -- Clean and quiet run
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
            'Timesheet Validation',
            ERROR_MESSAGE(),
            'ValidationTask',
            SYSTEM_USER
        );
    END CATCH;
END;
GO

-- Sync Data
CREATE OR ALTER PROCEDURE [Timesheet].[usp_SyncTimesheetDataFromStaging]
    @RunID NVARCHAR(40)
AS
BEGIN
    SET NOCOUNT ON;

    MERGE Timesheet.Timesheet AS Target
    USING (
        SELECT 
            e.EmployeeID,
            TRY_CAST(s.[Date] AS DATE) AS WorkDate,
            s.DayOfWeek,
            c.ClientID,
            p.ProjectID,
            d.DescriptionID,
            s.BillableStatus,
            s.Comments,
            TRY_CAST(s.TotalHours AS DECIMAL(5,2)) AS TotalHours,
            TRY_CAST(s.StartTime AS TIME) AS StartTime,
            TRY_CAST(s.EndTime AS TIME) AS EndTime,
            s.FileName
        FROM Timesheet.TimesheetStaging s
        LEFT JOIN Timesheet.Employee e ON e.EmployeeName = s.EmployeeName
        LEFT JOIN Timesheet.Client c ON c.ClientName = s.ClientName
        LEFT JOIN Timesheet.Project p ON p.ProjectName = s.ProjectName
        LEFT JOIN Timesheet.Description d ON d.DescriptionName = TRIM(s.ActivityName)
        WHERE 
            s.RunID = @RunID
            AND d.DescriptionID IS NOT NULL
            AND TRY_CAST(s.TotalHours AS DECIMAL(5,2)) IS NOT NULL
            AND TRY_CAST(s.StartTime AS TIME) IS NOT NULL
            AND TRY_CAST(s.EndTime AS TIME) IS NOT NULL
            AND TRY_CAST(s.[Date] AS DATE) IS NOT NULL
    ) AS Source
    ON Target.EmployeeID = Source.EmployeeID
       AND Target.[Date] = Source.WorkDate
       AND Target.FileName = Source.FileName

    -- UPDATE existing records where content changed
    WHEN MATCHED AND (
        ISNULL(Target.TotalHours, 0) <> ISNULL(Source.TotalHours, 0)
        OR ISNULL(Target.ProjectID, 0) <> ISNULL(Source.ProjectID, 0)
        OR ISNULL(Target.ClientID, 0) <> ISNULL(Source.ClientID, 0)
        OR ISNULL(Target.DescriptionID, 0) <> ISNULL(Source.DescriptionID, 0)
        OR ISNULL(Target.Comments, '') <> ISNULL(Source.Comments, '')
        OR ISNULL(Target.BillableStatus, '') <> ISNULL(Source.BillableStatus, '')
        OR ISNULL(Target.StartTime, '') <> ISNULL(Source.StartTime, '')
        OR ISNULL(Target.EndTime, '') <> ISNULL(Source.EndTime, '')
    ) THEN
        UPDATE SET
            Target.TotalHours = Source.TotalHours,
            Target.ProjectID = Source.ProjectID,
            Target.ClientID = Source.ClientID,
            Target.DescriptionID = Source.DescriptionID,
            Target.Comments = Source.Comments,
            Target.BillableStatus = Source.BillableStatus,
            Target.StartTime = Source.StartTime,
            Target.EndTime = Source.EndTime

    -- INSERT new rows
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            EmployeeID, [Date], DayOfWeek, ClientID, ProjectID,
            DescriptionID, BillableStatus, Comments,
            TotalHours, StartTime, EndTime, FileName
        )
        VALUES (
            Source.EmployeeID, Source.WorkDate, Source.DayOfWeek, Source.ClientID,
            Source.ProjectID, Source.DescriptionID, Source.BillableStatus,
            Source.Comments, Source.TotalHours, Source.StartTime, Source.EndTime, Source.FileName
        )

    -- DELETE rows from Timesheet if they are not in the current RunID (same file)
    WHEN NOT MATCHED BY SOURCE
    AND Target.FileName = (
        SELECT TOP 1 FileName FROM Timesheet.TimesheetStaging WHERE RunID = @RunID
    ) THEN
        DELETE;
END;
GO

-- INSERT THE Description Table

CREATE OR ALTER PROCEDURE Timesheet.SyncDescriptions
AS
BEGIN
    SET NOCOUNT ON;

    -------------------------------------------------
    -- Insert new Activities into Description
    -------------------------------------------------
    INSERT INTO Timesheet.Description (DescriptionType, DescriptionName)
    SELECT 'Activity', A.ActivityName
    FROM Timesheet.Activity A
    WHERE NOT EXISTS (
        SELECT 1 
        FROM Timesheet.DescriptionActivity DA
        JOIN Timesheet.Description D ON DA.DescriptionID = D.DescriptionID
        WHERE D.DescriptionType = 'Activity'
          AND DA.ActivityID = A.ActivityID
    );

    -------------------------------------------------
    -- Insert bridge entries for Activities
    -------------------------------------------------
    INSERT INTO Timesheet.DescriptionActivity (DescriptionID, ActivityID)
    SELECT D.DescriptionID, A.ActivityID
    FROM Timesheet.Activity A
    JOIN Timesheet.Description D 
        ON D.DescriptionType = 'Activity'
       AND D.DescriptionName = A.ActivityName
    WHERE NOT EXISTS (
        SELECT 1 
        FROM Timesheet.DescriptionActivity DA
        WHERE DA.ActivityID = A.ActivityID
    );

    -------------------------------------------------
    -- Insert new LeaveTypes into Description
    -------------------------------------------------
    INSERT INTO Timesheet.Description (DescriptionType, DescriptionName)
    SELECT 'Leave', L.LeaveTypeName
    FROM Timesheet.LeaveType L
    WHERE NOT EXISTS (
        SELECT 1 
        FROM Timesheet.DescriptionLeave DL
        JOIN Timesheet.Description D ON DL.DescriptionID = D.DescriptionID
        WHERE D.DescriptionType = 'Leave'
          AND DL.LeaveTypeID = L.LeaveTypeID
    );

    -------------------------------------------------
    -- Insert bridge entries for LeaveTypes
    -------------------------------------------------
    INSERT INTO Timesheet.DescriptionLeave (DescriptionID, LeaveTypeID)
    SELECT D.DescriptionID, L.LeaveTypeID
    FROM Timesheet.LeaveType L
    JOIN Timesheet.Description D 
        ON D.DescriptionType = 'Leave'
       AND D.DescriptionName = L.LeaveTypeName
    WHERE NOT EXISTS (
        SELECT 1 
        FROM Timesheet.DescriptionLeave DL
        WHERE DL.LeaveTypeID = L.LeaveTypeID
    );

END;
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