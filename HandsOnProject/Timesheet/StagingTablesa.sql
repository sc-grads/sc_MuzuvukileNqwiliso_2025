-- Staging Tables
IF OBJECT_ID('Timesheet.Staging_LeaveRequest', 'U') IS NULL 
BEGIN
    CREATE TABLE Timesheet.Staging_LeaveRequest (
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