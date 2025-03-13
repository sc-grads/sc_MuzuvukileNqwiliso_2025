USE BikeStores
SELECT * FROM sales.customers

SELECT COUNT(*) AS customers_that_have_phones
FROM (
    SELECT first_name
    FROM sales.customers
    WHERE phone IS NOT NULL
) 
AS subquery;


SELECT  list_price
FROM sales.order_items
WHERE list_price > (SELECT AVG(list_price) FROM sales.order_items);
