USE BikeStores

-- RETRIEVE TABLES
-- SALES
SELECT * FROM sales.customers
SELECT * FROM sales.orders
SELECT * FROM sales.order_items
SELECT *FROM sales.stores
SELECT * FROM sales.staffs

-- PRODUCTS
SELECT * FROM production.brands
SELECT * FROM production.categories
SELECT * FROM production.products
SELECT * FROM production.stocks

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
ON stf.store_id = [str].store_id

-- 3: Tables - orders, products, item_orders,
-- THE * MEANS I WANT TO RETURN EVERYTHING FROM THE ORDERS TABLE
SELECT ord.*,  p.product_name, ord_i.quantity ,ord_i.discount
FROM sales.order_items ord_i 
INNER JOIN production.products p
ON p.product_id = ord_i.product_id
-- THE ABOVE IS RESULT WILL BE TREATED AS THE FIRST TABLE 
INNER JOIN sales.orders ord 
ON ord.order_id = ord_i.order_id
-- THE ABOVE WILL BE TREATED AS THE SECOND ATBLE

-- 4: Tables - orders,customers,stores,staffs
-- THE ORDER TABLE HAS ID FOR : CUSTOMER,STAFF,STORE
-- I WILL USE THE FOREIGN KEYS IN THE ORDERS TABLES IN ORDER TO RETRIEVE ALL THE INFORMATION NEEDED
SELECT ord.order_id as [order id], 
c.first_name as [customer name], 
s.store_name as [store name], 
stf.first_name as [staff name]
-- THE ABOVE WILL RETURN THE COLUMNS NEEDED 
FROM sales.orders ord 
INNER JOIN sales.customers c
ON ord.customer_id = c.customer_id
INNER JOIN sales.stores s
ON ord.store_id = s.store_id
INNER JOIN sales.staffs stf
ON ord.staff_id = stf.staff_id
-- THE ABOVE WILL RETURN THE NEEDED INFORMATION
ORDER BY [customer name]
OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY -- THIS LINE WILL RETURN ONLY 20 RECORDS
