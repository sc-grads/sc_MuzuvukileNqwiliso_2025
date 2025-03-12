USE BikeStores

-- sales schema
SELECT * FROM sales.customers
SELECT * FROM sales.orders
SELECT * FROM sales.order_items
SELECT *FROM sales.stores
SELECT * FROM sales.staffs

-- product schema
SELECT * FROM production.brands
SELECT * FROM production.categories
SELECT * FROM production.products
SELECT * FROM production.stocks

GO
 
SELECT stf.first_name, stf.last_name, stf.email, stf.phone, [str].store_name  
FROM sales.staffs stf  
INNER JOIN sales.stores [str]  
ON [str].store_id = stf.store_id; 

GO

SELECT c.first_name, c.last_name, o.order_id
FROM sales.orders o
INNER JOIN sales.customers c
ON c.customer_id = o.customer_id

GO 

SELECT stf.first_name, stf.last_name,[str].store_name
FROM sales.staffs stf 
INNER JOIN sales.stores [str]
ON stf.store_id = [str].store_id

GO 

SELECT ord.*,  p.product_name, ord_i.quantity ,ord_i.discount
FROM sales.order_items ord_i 
INNER JOIN production.products p
ON p.product_id = ord_i.product_id
INNER JOIN sales.orders ord 
ON ord.order_id = ord_i.order_id

GO 

SELECT ord.order_id as [order id], 
c.first_name as [customer name], 
s.store_name as [store name], 
stf.first_name as [staff name]
FROM sales.orders ord 
INNER JOIN sales.customers c
ON ord.customer_id = c.customer_id
INNER JOIN sales.stores s
ON ord.store_id = s.store_id
INNER JOIN sales.staffs stf
ON ord.staff_id = stf.staff_id
ORDER BY [customer name]
OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY 
