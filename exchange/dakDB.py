import pyodbc as dbc
import time

class DakDb(object):
    def __init__(self, host, database, username, password):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        # test to ensure we have a connection.
        self._getDatabaseConnection()
    
    def _getDatabaseConnection(self, retries=10):
        for _ in range(retries):
            try:
                # dbConn = dbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=MSI;DATABASE=exchange;UID=webApp;PWD=Password1!')
                dbConn = dbc.connect(driver='ODBC Driver 17 for SQL Server'
                                    ,server=self.host
                                    ,database=self.database
                                    ,uid=self.username
                                    ,pwd=self.password  
                                    )

                break
            except dbc.InterfaceError:
                time.sleep(1)
        else:
            raise dbc.InterfaceError()
        return dbConn

    def createUser(self, username, email):
        insertionQuery = "INSERT INTO users  VALUES (?, ?)"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(insertionQuery, (username, email))
        dbConn.commit()
        cur.close()
        dbConn.close()

    def getCurentConfig(self):
        selectQuery = "SELECT * FROM current_config"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery)
        rows = [{column[0]:rowElement for column, rowElement in zip (cur.description, row)} for row in cur]
        cur.close()
        dbConn.close()
        return rows[0]

    def getHistoricalConfigs(self):
        selectQuery = "SELECT * FROM configs ORDER BY id DESC"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery)
        rows = [row for row in cur]
        cur.close()
        dbConn.close()
        return rows

    def checkUserCreds(self, username, password):
        selectQuery = "SELECT TOP 1 id FROM users WHERE user_name = ? AND user_password = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery, (username, password))
        rows = [row for row in cur]
        cur.close()
        dbConn.close()
        return rows

    def checkForExistingUser(self, username):
        selectQuery = "SELECT id FROM users WHERE user_name = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery, username)
        rows = [row for row in cur]
        cur.close()
        dbConn.close()
        return rows
    
    def getUserByName(self, username):
        selectQuery = "SELECT TOP 1 * FROM users WHERE user_name = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery, username)
        rows = [{column[0]:rowElement for column, rowElement in zip (cur.description, row)} for row in cur]
        cur.close()
        dbConn.close()
        return rows[0]
    
    def getUserById(self, id):
        selectQuery = "SELECT TOP 1 * FROM users WHERE id = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery, id)
        rows = [{column[0]:rowElement for column, rowElement in zip (cur.description, row)} for row in cur]
        cur.close()
        dbConn.close()
        return rows[0]

    def getUnsetTransactions(self):
        selectQuery = "SELECT * FROM unsent_transactions"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery)
        rows = [{column[0]:rowElement for column, rowElement in zip (cur.description, row)} for row in cur]
        cur.close()
        dbConn.close()
        return rows

    def markTransactionsAsSent(self, txids):
        updateQuery = "UPDATE transactions SET daktxid=?, sent=1, timeSent=GETDATE() WHERE txid = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.executemany(updateQuery, txids)
        dbConn.commit()
        cur.close()
        dbConn.close()
    
    def getTransactions(self, userid):
        selectQuery = "SELECT * FROM transactions WHERE userid = ?"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(selectQuery, userid)
        rows = [row for row in cur]
        cur.close()
        dbConn.close()
        return rows

    def createTransaction(self, userId, toAddress, amount, message):
        insertionQuery = "INSERT INTO transactions VALUES (?, ?, ?, ?, NULL, 0, 0, 0)"
        dbConn = self._getDatabaseConnection()
        cur = dbConn.cursor()
        cur.execute(insertionQuery, (userId, toAddress, amount, message))
        dbConn.commit()
        cur.close()
        dbConn.close()