CREATE DATABASE IF NOT EXISTS CS411;
USE CS411;
CREATE TABLE IF NOT EXISTS Users
(
    email    VARCHAR(30) PRIMARY KEY,
    password VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS History
(
    hid         INTEGER PRIMARY KEY AUTO_INCREMENT,
    email       VARCHAR(30),
    quote       VARCHAR(255),
    imgname     VARCHAR(255),
    description VARCHAR(255),
    FOREIGN KEY (email) references Users (email)
);
SELECT *
FROM HISTORY;
SELECT *
FROM Users;
INSERT INTO Users(email)
VALUES ("zhuceyezi@gmail.com");
INSERT INTO Users(email)
VALUES ("lianghan@bu.edu");
INSERT INTO Users(email)
VALUES ("maxgspan@bu.edu");
INSERT INTO Users(email)
VALUES ("stefanjacobp@gmail.com");
INSERT INTO Users(email)
VALUES ("jmsrng.trash@gmail.com");
INSERT INTO Users(email)
VALUES ("mgreenspan42@gmail.com");

INSERT INTO History(imgname)
VALUES ('maxine.png')