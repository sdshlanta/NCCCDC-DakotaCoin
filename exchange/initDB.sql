USE exchange;
GO
DROP TABLE IF EXISTS [dbo].[dakotacoinAccounts];
GO
DROP TABLE IF EXISTS configs;
GO
DROP TABLE IF EXISTS transaction_failures;
GO
DROP TABLE IF EXISTS transactions;
GO
DROP TABLE IF EXISTS users;
GO
DROP VIEW IF EXISTS current_config;
GO
DROP VIEW IF EXISTS unsent_transactions;
GO
DROP VIEW IF EXISTS cancled_transactions;
GO

EXEC sp_configure 'remote admin connections', 1;
GO
RECONFIGURE;
GO 

CREATE TABLE users (
	id int NOT NULL IDENTITY PRIMARY KEY
	,user_name varchar(100) NOT NULL
	,user_password varchar(100) NOT NULL
	,user_email varchar(100) NOT NULL
	,softDAK float NOT NULL
);

CREATE TABLE transactions (
	txid int NOT NULL IDENTITY PRIMARY KEY
	,userid int NOT NULL FOREIGN KEY REFERENCES users(id)
	,toAddress char(34) NOT NULL
	,amount float NOT NULL
	,message varchar(1024) NOT NULL
	,sent bit NOT NULL DEFAULT 0
	,cancled bit NOT NULL DEFAULT 0
	,failed bit NOT NULL DEFAULT 0
);

CREATE TABLE transaction_failures (
	fxid int NOT NULL IDENTITY PRIMARY KEY
	,txid int NOT NULL FOREIGN KEY REFERENCES transactions(txid)
	,errorMessage varchar(1024) NOT NULL
);

CREATE TABLE configs (
	id int NOT NULL IDENTITY PRIMARY KEY
	,LDAP_user varchar(100) NOT NULL
	,LDAP_password varchar(100) NOT NULL
	,RPC_user varchar(100) NOT NULL
	,RPC_password varchar(100) NOT NULL
	,RPC_address char(20) NOT NULL
	,RPC_port smallint NOT NULL
	,transact_interval float NOT NULL
);
GO

CREATE VIEW current_config AS
	SELECT TOP 1 *
	FROM configs 
	ORDER BY configs.id DESC;
GO

CREATE VIEW unsent_transactions AS
	SELECT txid, users.user_name, toAddress, amount, message
	FROM transactions
	INNER JOIN users 
	ON transactions.userid = users.id
	WHERE sent = 0 AND cancled = 0;
GO

CREATE VIEW cancled_transactions AS
	SELECT txid, transactions.userid, toAddress, amount, message, users.user_name
	FROM transactions
	INNER JOIN users 
	ON transactions.userid = users.id
	WHERE cancled = 1;
GO

INSERT users VALUES ('mike', 'test', 'A', 0),
					('eric', 'fish_are_hot', 'B', 0),
					('andrew', 'Password1!', 'C' ,0),
					('dyl_up', 'r00M#Gb4p%ur', 'myspamcondom@gmail.com', 0),
					('test2', 'UvT$yRs8PfO8', 'myspamcondom2@gmail.com', 0);

INSERT configs VALUES ('admin', 'password1!', 'username', 'password', '192.168.80.160', 9332, 60),
					  ('admin', 'Password1!', 'username', 'password', '192.168.80.160', 9332, 5);

INSERT INTO transactions VALUES (5, 'tAGRGCq7jEzkgAi4B2vJam4T5q8yHNczvX', 0.1, '', 0, 0, 0),
								(5, 'tGTAR2yw5jRWTcdv26s4MqsR55c85T51GV', 0.1, '', 0, 0, 0);

SELECT * FROM users;
SELECT * FROM configs;
SELECT * FROM current_config;
SELECT * FROM configs ORDER BY id DESC;
SELECT * FROM transactions;
SELECT * FROM unsent_transactions;
SELECT * FROM cancled_transactions;
