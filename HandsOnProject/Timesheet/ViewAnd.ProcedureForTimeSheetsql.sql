
ALTER TABLE Timesheet.Timesheet DROP COLUMN SartTime;
ALTER TABLE Timesheet.Timesheet ADD StartTime TIME;
GO
CREATE OR ALTER PROCEDURE Timesheet.InsertTimesheet
    @EmployeeID INT,
    @Date DATE,
    @DayOfWeek VARCHAR(10),
    @ClientID INT,
    @ProjectID INT,
    @ActivityOrLeave VARCHAR(50),
    @BillableStatus VARCHAR(20),
    @Comments TEXT,
    @TotalHours DECIMAL(5,2),
    @StartTime TIME,
    @EndTime TIME,
    @FileName VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @ActivityID INT, @LeaveType INT;

    -- Map ActivityOrLeave to ActivityID or LeaveType
    IF LOWER(@ActivityOrLeave) LIKE '%leave%'
        SELECT @LeaveType = LeaveType FROM Timesheet.LeaveType WHERE LeaveTypeName = @ActivityOrLeave;
    ELSE
        SELECT @ActivityID = ActivityID FROM Timesheet.Activity WHERE ActivityName = @ActivityOrLeave;

    -- Insert if not exists
    IF NOT EXISTS (
        SELECT 1 FROM Timesheet.Timesheet
        WHERE EmployeeID = @EmployeeID
          AND [Date] = @Date
          AND ISNULL(ProjectID, 0) = ISNULL(@ProjectID, 0)
          AND ISNULL(ActivityID, 0) = ISNULL(@ActivityID, 0)
          AND ISNULL(LeaveType, 0) = ISNULL(@LeaveType, 0)
    )
    BEGIN
        INSERT INTO Timesheet.Timesheet (
            EmployeeID, [Date], [DayOfWeek], ClientID, ProjectID, ActivityID, LeaveType,
            BillableStatus, Comments, TotalHours, StartTime, EndTime
        )
        VALUES (
            @EmployeeID, @Date, @DayOfWeek, @ClientID, @ProjectID, @ActivityID, @LeaveType,
            @BillableStatus, @Comments, @TotalHours, @StartTime, @EndTime
        );

        -- Log to AuditLog
        INSERT INTO Timesheet.AuditLog (FileName, TableName, Action, RecordID, ProcessedDate)
        VALUES (@FileName, 'Timesheet', 'Insert', NEXT VALUE FOR Timesheet.TimesheetSeq - 1, GETDATE());
    END
END;

Go

CREATE OR ALTER VIEW Timesheet.vw_TimesheetDisplay
AS
SELECT 
    t.Timesheet_ID,
    e.EmployeeName,
    t.[Date],
    t.[DayOfWeek],
    c.ClientName,
    p.ProjectName,
    COALESCE(a.ActivityName, lt.LeaveTypeName) AS ActivityOrLeave,
    t.BillableStatus,
    t.Comments,
    t.TotalHours,
    t.StartTime,
    t.EndTime
FROM Timesheet.Timesheet t
JOIN Timesheet.Employee e ON t.EmployeeID = e.EmployeeID
LEFT JOIN Timesheet.Client c ON t.ClientID = c.ClientID
LEFT JOIN Timesheet.Project p ON t.ProjectID = p.ProjectID
LEFT JOIN Timesheet.Activity a ON t.ActivityID = a.ActivityID
LEFT JOIN Timesheet.LeaveType lt ON t.LeaveType = lt.LeaveType;