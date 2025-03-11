-- section 4

-- this script creates a database
CREATE DATABASE our_first_db
GO 

-- this selects a table to use
USE our_first_db

-- this script creates a table 
CREATE TABLE users(
    [user_id] INT IDENTITY(1,1) PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL
);
GO 

-- this script insert data to the table
INSERT INTO users (first_name, last_name, date_of_birth) 
VALUES
    ('John', 'Doe', '1990-05-15'),
    ('Sarah', 'Smith', '1985-08-22'),
    ('Michael', 'Johnson', '1995-02-10'),
    ('Emily', 'Brown', '1992-11-30'),
    ('David', 'Wilson', '1988-03-25');

GO 

-- this script retrieves all the data in the table
SELECT * FROM users
