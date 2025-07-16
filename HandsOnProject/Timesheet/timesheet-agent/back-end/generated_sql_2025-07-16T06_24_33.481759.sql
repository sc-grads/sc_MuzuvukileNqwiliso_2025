SELECT [Timesheet].[Project].[ProjectName]
FROM [Timesheet].[Project]
INNER JOIN [Timesheet].[Employee] ON [Timesheet].[Employee].[EmployeeID] = [Timesheet].[Project].[EmployeeID]
INNER JOIN [Timesheet].[Timesheet] ON [Timesheet].[Employee].[EmployeeID] = [Timesheet].[Timesheet].[EmployeeID]
WHERE [Timesheet].[Employee].[EmployeeName] = 'Siyakhanya Mjikeliso' AND [Timesheet].[Timesheet].[Date] BETWEEN '2025-03-01' AND '2025-04-01'
GO
