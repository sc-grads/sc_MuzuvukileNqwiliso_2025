CREATE PROCEDURE Timesheet.usp_ProcessTimesheetFile
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
        -- New file processing: insert audit log and processed files record
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
            @FilePath, @FileName, @EmployeeName, @RowCount, CAST(@LastModified AS DATETIME), GETDATE()
        );
    END
    ELSE
    BEGIN
        -- Modified file processing

        -- Detect deleted rows
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
                CONVERT(NVARCHAR(10), Date, 120) + ', ' +
                FORMAT(StartTime, 'hh\:mm') + ' - ' +
                FORMAT(EndTime, 'hh\:mm'),
            @TimesheetMonth,
            GETDATE()
        FROM DeletedRows;

        -- Detect updated rows
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet',
            'Update',
            'Updated row: ' + CONVERT(NVARCHAR(10), s.Date, 120) + ', ' +
            FORMAT(TRY_CAST(s.StartTime AS TIME), 'hh\:mm') + ' - ' + 
            FORMAT(TRY_CAST(s.EndTime AS TIME), 'hh\:mm'),
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

        -- Insert detection (new rows that exist in staging but not in main Timesheet table)
        INSERT INTO Timesheet.AuditLog (
            EmployeeName, FileName, TableName, Action, Message, [Month], ProcessedDate
        )
        SELECT 
            s.EmployeeName,
            s.FileName,
            'Timesheet',
            'Insert',
            'Inserted new row: ' + CONVERT(NVARCHAR(10), s.Date, 120) + ', ' +
            FORMAT(TRY_CAST(s.StartTime AS TIME), 'hh\:mm') + ' - ' + 
            FORMAT(TRY_CAST(s.EndTime AS TIME), 'hh\:mm'),
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

        -- If no changes detected, insert 'NoChange' audit log
        IF NOT EXISTS (
            -- Deleted rows
            SELECT 1
            FROM Timesheet.Timesheet t
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
            -- Updated rows
            SELECT 1
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
              )
            UNION
            -- Inserted rows
            SELECT 1
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
END;
GO
