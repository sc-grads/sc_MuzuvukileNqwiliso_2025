USE msdb;
GO

-- Delete the job if it exists
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = 'Run_MasterPackage')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = 'Run_MasterPackage';
END
GO

-- Optional: Create a Mail Operator (only once)
IF NOT EXISTS (SELECT 1 FROM msdb.dbo.sysoperators WHERE name = 'TimesheetOperator')
BEGIN
    EXEC msdb.dbo.sp_add_operator  
        @name = N'TimesheetOperator',  
        @enabled = 1,  
        @email_address = N'mzu.nqwiliso@gmail.com';  -- replace with yours
END
GO

-- Add the job
EXEC msdb.dbo.sp_add_job
    @job_name = 'Run_MasterPackage',
    @enabled = 1,
    @description = 'Executes the SSIS MasterPackage every 1 minute from SSISDB',
    @start_step_id = 1,
    @notify_level_eventlog = 2,  -- log failures
    @notify_level_email = 2,     -- 1 = success, 2 = failure, 3 = both
    @notify_email_operator_name = 'TimesheetOperator',
    @owner_login_name = 'LAPTOP-62JJ49T4\MuzuvukileNqwiliso';

-- Step 1: Run MasterPackage
EXEC msdb.dbo.sp_add_jobstep
    @job_name = 'Run_MasterPackage',
    @step_name = 'Run MasterPackage from SSISDB',
    @subsystem = 'TSQL',
    @command = N'
DECLARE @execution_id BIGINT;

EXEC SSISDB.catalog.create_execution
    @package_name = N''MasterPackage.dtsx'',
    @execution_id = @execution_id OUTPUT,
    @folder_name = N''TimesheetDeploy'',
    @project_name = N''MigratingTimesheet'',
    @use32bitruntime = False,
    @reference_id = NULL;

EXEC SSISDB.catalog.start_execution @execution_id;
',
    @database_name = 'SSISDB',
    @on_success_action = 3,
    @on_fail_action = 2;

-- Step 2: Clean Audit + Error Logs
EXEC msdb.dbo.sp_add_jobstep
    @job_name = 'Run_MasterPackage',
    @step_name = 'Clean Audit and Error Tables',
    @subsystem = 'TSQL',
    @command = N'
DELETE FROM [TimesheetDB].[Timesheet].[AuditLog]
WHERE [ProcessedDate] < DATEADD(MINUTE, -20, GETDATE());

DELETE FROM [TimesheetDB].[Timesheet].[ErrorLog]
WHERE [ProcessedDate] < DATEADD(MINUTE, -20, GETDATE());
',
    @database_name = 'TimesheetDB',
    @on_success_action = 1,
    @on_fail_action = 2;

-- Schedule: every 1 minute
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = 'Timesheet_Schedule',
    @freq_type = 4, -- daily
    @freq_interval = 1,
    @freq_subday_type = 4, -- minutes
    @freq_subday_interval = 1,
    @active_start_time = 0000;

-- Attach schedule
EXEC msdb.dbo.sp_attach_schedule
    @job_name = 'Run_MasterPackage',
    @schedule_name = 'Timesheet_Schedule';

-- Attach job to server
EXEC msdb.dbo.sp_add_jobserver
    @job_name = 'Run_MasterPackage';
