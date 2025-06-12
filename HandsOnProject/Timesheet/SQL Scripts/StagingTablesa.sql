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





