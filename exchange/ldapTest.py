# from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, NTLM

# config = {}

# config['LDAP_HOST'] = 'dc01'
# config['LDAP_USERNAME'] = 'cn=Administrator,CN=Users,DC=ccdc,DC=local'
# config['LDAP_PASSWORD'] = 'Password1!'
# config['LDAP_BASE_DN'] = 'CN=Users,DC=ccdc,DC=local'
# config['LDAP_USER_OBJECT_FILTER'] = '(&(objectclass=person)(cn=%s))'

# server = Server('dc01.ccdc.local')
# conn = Connection(server)
# conn.bind()
# print(conn)
# CN=Administrator,CN=Users,DC=ccdc,DC=local

# class fromconfig:
#     def __init__(self):
#         Config = configparser.ConfigParser()
#         Config.read("config.ini")
#         self.serverip = Config.get('serverinfo', 'ip')
#         self.basepath = Config.get('serverinfo', 'base')
#         self.container = Config.get('serverinfo', 'container')
#         self.dc1 = Config.get('serverinfo', 'dc1')
#         self.dc2 = Config.get('serverinfo', 'dc2')
#         self.ou = Config.get('serverinfo', 'ou')

# def add_user(username, givenname, surname, userPrincipalName, SAMAccountName, userPassword):

#     ad_server = Server(config.serverip, use_ssl=True, get_info=ALL) 

#     ad_c = Connection(ad_server, user='domain\\user', password='password', authentication=NTLM)

#     if ad_c.bind():
#         ad_c.add('cn={},cn={},dc={},dc={}'.format(username, config.ou, config.dc1, config.dc2), ['person', 'user'], {'givenName': givenname, 'sn': surname, 'userPrincipalName': userPrincipalName, 'sAMAccountName': SAMAccountName, 'userPassword': userPassword})

#         ad_c.extend.microsoft.unlock_account(user='cn={},cn={},dc={},dc={}'.format(username, config.container, config.dc1, config.dc2))      
        
#         ad_c.extend.microsoft.modify_password(user='cn={},cn={},dc={},dc={}'.format(username, config.container, config.dc1, config.dc2), new_password=userpassword, old_password=None)
        
#         changeUACattribute = {"userAccountControl": (MODIFY_REPLACE, [512])}
        
#         ad_c.modify('cn={},cn={},dc={},dc={}'.format(username, config.container, config.dc1, config.dc2), changes=changeUACattribute)

#     ad_c.unbind()


from dakLDAP import dakLdap

ldapAuth = dakLdap('dc02','ccdc\\Administrator', 'Password1!', 'CN=Users,DC=ccdc,DC=local', 'ccdc.local','Web App Admins')

print(ldapAuth.checkUserCreds('Goat', 'Password1!'))

ldapAuth.createUser('test3', 'Password1!')

print(ldapAuth.checkUserCreds('test3', 'Password1!'))
print(ldapAuth.isAdmin('*'))