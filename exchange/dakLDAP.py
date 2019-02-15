from ldap3 import Server, Connection, ALL, NTLM, MODIFY_REPLACE

class dakLdap():
    def __init__(self, host, SAUsername, SAPassword, DNBase, domain):
        self.host = host
        self.SAUsername = SAUsername
        self.SAPassword = SAPassword
        self.DNBase = DNBase
        self.domain = domain
        self.server = Server(self.host, use_ssl=True)
        self.conn = Connection(self.server, user=self.SAUsername, password=self.SAPassword, authentication=NTLM)
        self.conn.bind()
        self.conn.start_tls() 
        self.conn.unbind()

    def checkUserCreds(self, username, password):

        username = "%s@%s" % (username, self.domain)
        conn = Connection(self.server, user = username, password = password)
        # conn.bind will return true or false depending on if the
        # user logs in correctly.
        userStatus = conn.bind()
        conn.unbind()
        return userStatus
    
    def changePassword(self, username, password):
        DN = 'cn=%s,%s' % (username, self.DNBase)
        print(DN)
        self.conn.bind()
        self.conn.start_tls()  
        self.conn.extend.microsoft.unlock_account(user=DN)
        print(self.conn.extend.microsoft.modify_password(DN, password, None))
        self.conn.unbind()

    def createUser(self, username, password):
        # 'memberOf':'CN=Web App Users,CN=Builtin,DC=ccdc,DC=local'
        self.conn.bind()
        self.conn.start_tls()
        DN = 'cn=%s,%s' % (username, self.DNBase)
        principalName = '%s@%s' % (username, self.domain)
        self.conn.add(DN, ['user', 'top'], {'sAMAccountName':username, 'userPassword':password, 'userPrincipalName':principalName})
        self.conn.extend.microsoft.unlock_account(user=DN)
        print(self.conn.extend.microsoft.modify_password(DN, password, None))
        # changeUACattribute = {"userAccountControl": (MODIFY_REPLACE, [512])}
        # self.conn.modify(DN, changes=changeUACattribute)
        # self.conn.extend.microsoft.add_members_to_groups([DN], ['CN=Web App Users,CN=Users,DC=ccdc,DC=local'])
        self.conn.unbind()