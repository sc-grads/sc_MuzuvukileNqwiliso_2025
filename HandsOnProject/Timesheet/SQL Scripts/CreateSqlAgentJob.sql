USE msdb;
GO

-- 1. Drop the job if it already exists
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = 'Run_MasterPackage')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = 'Run_MasterPackage';
END
GO

-- 2. Create the job
EXEC msdb.dbo.sp_add_job
    @job_name = 'Run_MasterPackage',
    @enabled = 1,
    @description = 'Executes the SSIS MasterPackage every 1 minute from SSISDB',
    @start_step_id = 1,
    @owner_login_name = 'LAPTOP-62JJ49T4\MuzuvukileNqwiliso'; -- change this if needed

-- 3. Add a job step to run the SSIS package
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
    @on_success_action = 1, -- Go to next step (or quit)
    @on_fail_action = 2; -- Quit with failure

-- 4. Create a schedule that runs every 1 minute
EXEC msdb.dbo.sp_add_schedule
    @schedule_name = 'Timesheet_Schedule',
    @freq_type = 4,  -- Daily
    @freq_interval = 1,
    @freq_subday_type = 4,  -- Minutes
    @freq_subday_interval = 1,
    @active_start_time = 0000;

-- 5. Attach the schedule to the job
EXEC msdb.dbo.sp_attach_schedule
    @job_name = 'Run_MasterPackage',
    @schedule_name = 'Timesheet_Schedule';

-- 6. Add the job to SQL Server Agent
EXEC msdb.dbo.sp_add_jobserver
    @job_name = 'Run_MasterPackage';
