-- Reset the table for demonstration
UPDATE [dbo].[tblEmployee] SET EmployeeNumber = 123 WHERE EmployeeNumber = 122

-- Display initial data
SELECT * FROM [dbo].[tblEmployee]

-- Transaction demonstration with error handling
BEGIN TRY
    SELECT 'Initial TRANCOUNT:' AS Message, @@TRANCOUNT AS TranCount
    
    BEGIN TRANSACTION MainTran
        SELECT 'After MainTran begin:' AS Message, @@TRANCOUNT AS TranCount
        
        BEGIN TRANSACTION NestedTran
            SELECT 'After NestedTran begin:' AS Message, @@TRANCOUNT AS TranCount
            
            -- Perform update
            UPDATE [dbo].[tblEmployee] 
            SET EmployeeNumber = 122 
            WHERE EmployeeNumber = 123
            
            -- Simulate an error condition (uncomment to test)
            -- DECLARE @test INT = 1/0
            
            SELECT 'Before NestedTran commit:' AS Message, @@TRANCOUNT AS TranCount
        COMMIT TRANSACTION NestedTran
        SELECT 'After NestedTran commit:' AS Message, @@TRANCOUNT AS TranCount
        
        -- Additional operations could go here
        IF @@TRANCOUNT > 0
        BEGIN
           


-- Simple Transaction Demo with Error Handling

-- 1. Reset demo data
UPDATE [dbo].[tblEmployee] 
SET EmployeeNumber = 123 
WHERE EmployeeNumber = 122;

-- 2. Display initial data
SELECT 'Before Transaction' AS Status, * FROM [dbo].[tblEmployee];

-- 3. Transaction with error handling
BEGIN TRY
    BEGIN TRANSACTION;
    
    -- Update existing employee
    UPDATE [dbo].[tblEmployee] 
    SET EmployeeNumber = 122 
    WHERE EmployeeNumber = 123;
    
    -- Insert new employee
    INSERT INTO [dbo].[tblEmployee](
        EmployeeNumber,
        EmployeeFirstName,
        EmployeeMiddleName,
        EmployeeLastName,
        EmployeeGovernmentID,
        DateOfBirth,
        Department)
    VALUES (
        124,
        'John',
        'A',
        'Smith',
        'JS123',
        '1990-05-15',
        'IT');
    
    -- Uncomment to test rollback
    -- RAISERROR('Test error', 16, 1);
    
    COMMIT TRANSACTION;
    PRINT 'Transaction committed successfully';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;
    
    PRINT 'Transaction rolled back due to error:';
    PRINT ERROR_MESSAGE();
END CATCH

-- 4. Display final data
SELECT 'After Transaction' AS Status, * FROM [dbo].[tblEmployee];