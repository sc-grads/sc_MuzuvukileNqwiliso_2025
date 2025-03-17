USE BikeStores;
GO

SELECT name, type_desc FROM sys.database_principals WHERE name = 'mzuUser'; -- this is used to check if the mzuLogin has the access to bikestores database

SELECT * FROM sales.customers; -- Allowed

INSERT INTO sales.customers (first_name, last_name, phone, email, street, city, state, zip_code)
VALUES ('John', 'Doe', '123-456-7890', 'john.doe@example.com', '123 Main St', 'New York', 'NY', '10001');

SELECT * FROM sales.customers
WHERE sales.customers.first_name = 'John'

DELETE FROM sales.customers
WHERE customer_id = 1446

SELECT * FROM fn_my_permissions('sales.customers', 'OBJECT');

