CREATE DATABASE IF NOT EXISTS CS411;
USE CS411;
CREATE TABLE IF NOT EXISTS Users(
	email VARCHAR(30) PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255)
);
INSERT INTO Users(email) VALUES("zhuceyezi@gmail.com");
INSERT INTO Users(email) VALUES("lianghan@bu.edu");
INSERT INTO Users(email) VALUES("maxgspan@bu.edu");
INSERT INTO Users(email) VALUES("stefanjacobp@gmail.com");
INSERT INTO Users(email) VALUES("jmsrng.trash@gmail.com");
