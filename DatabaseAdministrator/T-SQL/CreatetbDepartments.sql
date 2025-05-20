SELECT Department, '' as DepartmentHead
Into tbDepartments
FROM ( SELECT Department, count(*) as NumberOfDepartments FROM tbEmployees
GROUP BY Department) as newTable

ALTER TABLE tbDepartments
ALTER COLUMN DepartmentHead VARCHAR(20) NUll 

SELECT * FROM tbEmployees
SELECT * From tbDepartments