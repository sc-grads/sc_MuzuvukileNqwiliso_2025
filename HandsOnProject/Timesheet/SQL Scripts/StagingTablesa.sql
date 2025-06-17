-- Staging Tables
IF OBJECT_ID('Timesheet.StagingLeaveRequest', 'U') IS NULL 
BEGIN
    CREATE TABLE Timesheet.StagingLeaveRequest (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        LeaveTypeName NVARCHAR(255), -- Maps to Type of Leave
        StartDate NVARCHAR(50),      -- Maps to Start Date
        EndDate NVARCHAR(50),        -- Maps to End Date
        NumberOfDays NVARCHAR(50),   -- Maps to Number of days
        ApprovalObtained NVARCHAR(50), -- Maps to Approval Obtained
        SickNote NVARCHAR(50),       -- Maps to Sick Note
        EmployeeName NVARCHAR(255),  -- From EmployeeName variable
        FileName NVARCHAR(255),      -- From ExcelFilePath variable
        ProcessedDate DATETIME DEFAULT GETDATE(),
        IsValid BIT DEFAULT 0,       -- Marks valid rows
    );
END
GO
IF OBJECT_ID('Timesheet.StagingForecast', 'U') IS NOT NULL
    DROP TABLE Timesheet.StagingForecast;

CREATE TABLE Timesheet.StagingForecast (
    StagingID INT IDENTITY(1,1) PRIMARY KEY,
    ForecastedHours NVARCHAR(50),
    ForecastedWorkDays NVARCHAR(50),
    BillableHours NVARCHAR(50),
    NonBillableHours NVARCHAR(50),
    TotalHours NVARCHAR(50),
    EmployeeName NVARCHAR(255),
    FileName NVARCHAR(255),
    ProcessedDate DATETIME DEFAULT GETDATE(),
);

PRINT 'Timesheet.StagingForecast table created.';


IF OBJECT_ID('Timesheet.ProjectStaging', 'U') IS NOT NULL
    DROP TABLE Timesheet.ProjectStaging;

CREATE TABLE Timesheet.ProjectStaging (
    StagingID INT IDENTITY(1,1) PRIMARY KEY,         -- Unique identifier for each row
    ProjectName NVARCHAR(255) NOT NULL,              -- Project name to be inserted
    ClientName NVARCHAR(255) NOT NULL,               -- Client name to join with Timesheet.Client
    FileName VARCHAR(255) NOT NULL,                  -- Source file name for tracking
    ProcessedDate DATETIME DEFAULT GETDATE(),        -- Optional, for tracking when data was staged
    IsProcessed BIT DEFAULT 0                        -- Flag to mark rows as processed (optional)
);

CREATE INDEX IX_ProjectStaging_ProjectName ON Timesheet.ProjectStaging(ProjectName);
CREATE INDEX IX_ProjectStaging_ClientName ON Timesheet.ProjectStaging(ClientName);
CREATE INDEX IX_ProjectStaging_FileName ON Timesheet.ProjectStaging(FileName);
PRINT 'Timesheet.ProjectStaging table created.';


IF OBJECT_ID('Timesheet.ActivityLeaveStaging', 'U') IS NOT NULL
    DROP TABLE Timesheet.ActivityLeaveStaging;

CREATE TABLE Timesheet.ActivityLeaveStaging (
    StagingID INT IDENTITY(1,1) PRIMARY KEY,         -- Unique identifier for each row
    ActivityOrLeaveType NVARCHAR(255) NOT NULL,      -- Column to determine activity or leave type
    FileName VARCHAR(255) NOT NULL,                  -- Source file name for tracking
    EmployeeName NVARCHAR(255),                      -- Optional, if employee-specific data is included
    ProcessedDate DATETIME DEFAULT GETDATE(),        -- Optional, for tracking when data was staged
    IsProcessed BIT DEFAULT 0                        -- Flag to mark rows as processed (optional)
);

CREATE INDEX IX_ActivityLeaveStaging_ActivityOrLeaveType ON Timesheet.ActivityLeaveStaging(ActivityOrLeaveType);
CREATE INDEX IX_ActivityLeaveStaging_FileName ON Timesheet.ActivityLeaveStaging(FileName);
PRINT 'Timesheet.ActivityLeaveStaging table created.';




 IF OBJECT_ID('Timesheet.LeaveRequest','U') IS NOT NULL
    DROP TABLE Timesheet.LeaveRequest
-- Create the LeaveRequest table with constraints defined inline
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

    -- Foreign Key Constraints
    CONSTRAINT FK_LeaveRequest_Employee FOREIGN KEY (EmployeeID)
        REFERENCES Timesheet.Employee(EmployeeID),

    CONSTRAINT FK_LeaveRequest_LeaveType FOREIGN KEY (LeaveTypeID)
        REFERENCES Timesheet.LeaveType(LeaveType)
);
