USE BikeStores

-- RETRIEVE TABLES
SELECT * FROM sales.customers
SELECT * FROM sales.orders
SELECT * FROM sales.staffs

-- THIS SQL QUERY RETRIEVES THE FIRST NAME, LAST NAME, EMAIL, AND PHONE NUMBER OF STAFF MEMBERS,  
-- ALONG WITH THE STORE THEY WORK FOR.  
SELECT stf.first_name, stf.last_name, stf.email, stf.phone, [str].store_name  
FROM sales.staffs stf  
-- SQUARE BRACKETS [] ARE USED AROUND "STR" BECAUSE "STR" IS A RESERVED KEYWORD IN SQL.  
-- ENCLOSING IT IN BRACKETS PREVENTS SYNTAX ERRORS.  
INNER JOIN sales.stores [str]  
ON [str].store_id = stf.store_id; 

-- ================================
-- 🔹 inner join practice questions
-- ================================

-- 1. retrieve a list of customers along with their orders (customer's first name, last name, and order id).
-- 2. list all staff members and the stores they work for (first name, last name, store name).
-- 3. retrieve all order details, including the product name, quantity ordered, and discount applied.
-- 4. get a list of products along with their category names and brand names.
-- 5. retrieve a report showing orders with their customer names, store names, and the staff who processed the order.

-- 1: Tables - customers, orders

SELECT c.first_name, c.last_name, o.order_id
FROM sales.orders o
INNER JOIN sales.customers c
ON c.customer_id = o.customer_id

-- 2: Tables - staffs, stores
SELECT stf.first_name, stf.last_name,[str].store_name
FROM sales.staffs stf 
INNER JOIN sales.stores [str]
ON stf.staff_id = [str].store_id
