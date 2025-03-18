USE msdb;
GO

-- Create the Job
EXEC sp_add_job 
    @job_name = 'BackupBikeStoresJob',
    @enabled = 1, -- Enable the job
    @notify_level_eventlog = 2, -- Log failures
    @owner_login_name = 'sa'; -- Ensure a valid owner

-- Add Job Step (Backup Database)
EXEC sp_add_jobstep 
    @job_name = 'BackupBikeStoresJob',
    @step_name = 'Backup Step',
    @subsystem = 'TSQL',
    @command = 'BACKUP DATABASE BikeStores 
                TO DISK = ''C:\SQLBackups\BikeStores.bak'' 
                WITH FORMAT, INIT, NAME = ''BikeStores Full Backup'';',
    @on_success_action = 1, -- Quit with success
    @on_fail_action = 2; -- Quit with failure

-- Create a Daily Schedule at 10 PM
EXEC sp_add_schedule 
    @schedule_name = 'DailyBackupSchedule',
    @freq_type = 4, -- Daily
    @freq_interval = 1, -- Every day
    @active_start_time = 220000; -- Runs at 10:00 PM

-- Attach Schedule to Job
EXEC sp_attach_schedule 
    @job_name = 'BackupBikeStoresJob',
    @schedule_name = 'DailyBackupSchedule';

-- Assign Job to SQL Server Agent
EXEC sp_add_jobserver 
    @job_name = 'BackupBikeStoresJob',
    @server_name = @@SERVERNAME;
GO

SELECT * FROM msdb.dbo.sysjobs WHERE name = 'BackupBikeStoresJob'; -- these two scripts are used to display the jobs
SELECT * FROM msdb.dbo.sysjobsteps WHERE job_id IN (SELECT job_id FROM msdb.dbo.sysjobs WHERE name = 'BackupBikeStoresJob');

EXEC msdb.dbo.sp_start_job @job_name = 'BackupBikeStoresJob'; -- this is used to run the job manually 

EXEC msdb.dbo.sp_delete_job @job_name = 'BackupBikeStoresJob'; -- this is used to delete the Job 
