

CREATE PROCEDURE GetCustomerDetails
@CustomerID INT -- this acts as a parameter in a function
AS
BEGIN
-- this is saying retrieve the customer with this @Customer id 
	SELECT * FROM sales.customers 
	WHERE sales.customers.customer_id = @CustomerID
END

EXEC GetCustomerDetails @CustomerID = 3 -- the exec is used to trigger the procedure
										-- sntax (exec procedure_name parameter)

							
SELECT * FROM sales.customers

CREATE PROCEDURE getUserswithSameCity
@City VARCHAR(50)
AS 
BEGIN
	SELECT * FROM sales.customers
	WHERE sales.customers.city = @City
END

EXEC getUserswithSameCity @City = 'Uniondale'