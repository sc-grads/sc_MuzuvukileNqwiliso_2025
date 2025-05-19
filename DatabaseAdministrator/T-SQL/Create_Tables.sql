CREATE TABLE tbDepartments (
  depart_id INTEGER PRIMARY KEY, 
  DepartmentName VARCHAR(200)
);
GO

CREATE TABLE tbEmployees (
  empl_id INTEGER IDENTITY(0,1) PRIMARY KEY,
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  department INTEGER,
  FOREIGN KEY (department) REFERENCES tbDepartments(depart_id)
);
GO

INSERT INTO tbDepartments (depart_id, DepartmentName)
VALUES (101, 'Data Analytics');

INSERT INTO tbEmployees(first_name,last_name,department)
VALUES ('Mzu','Nqwiliso',101)

SELECT * FROM tbEmployees