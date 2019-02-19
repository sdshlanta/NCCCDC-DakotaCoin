from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

class dakRpc():
    def __init__(self, RpcAddr, RpcPort, RcpUser, RpcPass):    
        self._rcpUser = RcpUser
        self._rcpPass = RpcPass
        self._rpcAddr = RpcAddr
        self._rpcPort = RpcPort
        self.rpc = AuthServiceProxy("http://%s:%s@%s:%d"%(self._rcpUser,self._rcpPass, self._rpcAddr, self._rpcPort))
    
    def getAllAccountAddresses(self, account):
        addresses = self.rpc.getaddressesbyaccount(account)
        return addresses

    def getPrivateKey(self, address):
        privateKey = self.rpc.dumpprivkey(address)
        return privateKey
    
    def addNewAccount(self, account):
        address = self.rpc.getnewaddress(account)
        return address
    
    def getBalance(self, account):
        balance = self.rpc.getbalance(account)
        return float(balance)

    def getTransactions(self, account, start=0, end=10000):
        transactions = self.rpc.listtransactions(account, start, end)
        return transactions

    def getAddress(self, account):
        address = self.rpc.getaccountaddress(account)
        return address

    def getAccountByAddress(self, address):
        try:
            return self.rpc.getaccount(address)
        except JSONRPCException as e:
            if '-5' in str(e):
                return ''
            else:
                raise e

    def send(self, fromAccount, toAddress, amount, message = ''):
        addrInfo = self.getAddressInfo(toAddress)

        if addrInfo['ismine']:
            self.rpc.move(fromAccount, addrInfo['account'], amount, 1, message)
            return 'internal'
        else:
            txid = self.rpc.sendfrom(fromAccount, toAddress, amount, 1, message)
            return txid

    def getAddressInfo(self, address):
        return self.rpc.validateaddress(address)

    def getAddressTransactionInfo(self, address):
        print(self.rpc.listreceivedbyaddress())
        try:
            return list(filter(lambda balance: balance['address'] == address, self.rpc.listreceivedbyaddress()))[0]
        except IndexError:
            return None

    def getTransactionInfo(self, txid):
        return self.rpc.gettransaction(txid)