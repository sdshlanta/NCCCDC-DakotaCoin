import os
import sys
import json
import sched
import logging
import argparse
import traceback
from pprint import pprint
from time import strftime, sleep
from multiprocessing import Process
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, render_template, request, session, url_for, send_from_directory

import dakDB
import dakRPC
import dakLDAP
from transactionProcessor import processTransactions

app = Flask(__name__)


app.config['LDAP_HOST'] = 'dc01'
app.config['LDAP_USERNAME'] = 'cn=Administrator,CN=Users,DC=ccdc,DC=local'
app.config['LDAP_PASSWORD'] = 'Password1!'
app.config['LDAP_BASE_DN'] = 'CN=Users,DC=ccdc,DC=local'

def registerUser(username, password, email):
    db.createUser(username, email)
    rpc.addNewAccount(username)
    ldapAuth.createUser(username, password)

def authenticate(username, password):
    if db.checkForExistingUser(username):
        return ldapAuth.checkUserCreds(username, password)
    return False

@app.before_request
def before():
    if 'logged_in' not in session:
        session['logged_in'] = False

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        form = request.form
        if 'username' in form and 'password' in form:
            if authenticate(form['username'], form['password']):
                session['logged_in'] = True
                session['username'] = form['username']
                session['userid'] = db.getUserByName(form['username'])['id']
            else:
                error = 'Invalid Username or Password'
    
    if session['logged_in']:
        userInfo = db.getUserByName(session['username'])
        userInfo['balance'] = rpc.getBalance(session['username'])
        userInfo['error'] = error
        return render_template('index.html', **userInfo)
    return render_template('index.html', loginError=error)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if not session['logged_in'] or not ldapAuth.isAdmin(session['username']):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        form = request.form
        db.createNewConfig(form['RPC_user'], form['RPC_password'], form['RPC_address'], form['RPC_port'], form['transact_interval'])

    info = db.getUserByName(session['username'])
    currentConfig = db.getCurentConfig()
    print(currentConfig)
    info.update(currentConfig)
    info['historicalConfigs'] = db.getHistoricalConfigs()
    print(info['historicalConfigs'])
    print(info)
    try:
        info['balance'] = rpc.getBalance(session['username'])
    except ConnectionRefusedError:
        balance = "Unable to contact RPC server"
    info['error'] = error
    return render_template('admin.html', **info)


@app.route('/account', methods=['GET', 'POST'])
def accountSearch():
    error = None
    if request.method == 'POST':
        form = request.form
        return redirect(url_for('accountInfo', username=form['accountName']))
    
    userInfo = {}
    if session['logged_in']:
        userInfo = db.getUserByName(session['username'])
        userInfo['balance'] = rpc.getBalance(session['username'])
    userInfo['error'] = error
    return render_template('accountSearch.html', **userInfo)

@app.route('/account/<username>')
def accountInfo(username = None):
    error = None
    
    try:
        userInfo = db.getUserByName(username)
        userInfo['pathUsername'] = username
        userInfo['addresses'] = rpc.getAllAccountAddresses(username)
    except IndexError:
        error = 'The user "%s" does not exist' % username
        userInfo = {'addresses':[None]}
    if session['logged_in']:
        userInfo['balance'] = rpc.getBalance(session['username'])
    try:
        userInfo['transactions'] = db.getTransactions(userInfo['id'])
    except KeyError:
        error = 'The user "%s" does not exist' % username
        userInfo['transactions'] = []
    userInfo['error'] = error

    return render_template('account.html', **userInfo)

@app.route('/account/<username>/resetpassword', methods=['GET', 'POST'])
def resetPassword(username):
    if session['logged_in']:
        error = None
        if request.method == 'POST':
            form = request.form
            if form['newPassword']:
                ldapAuth.changePassword(username, form['newPassword'])
            else:
                error = "Please provide a new password."
        userInfo = db.getUserByName(session['username'])
        userInfo['balance'] = rpc.getBalance(session['username'])
        userInfo['error'] = error
        return render_template('resetPassword.html', **userInfo)
    return redirect(url_for('index'))

@app.route('/addressinfo/<address>')
def addressInfo(address):
    error = None
    addrInfo = rpc.getAddressInfo(address)   
    addrInfo['address'] = address
    if addrInfo['isvalid']:
        addrTXInfo = rpc.getAddressTransactionInfo(address)
        if addrTXInfo is not None:
            addrInfo['amountRecv'] = float(addrTXInfo['amount'])
            addrInfo['txids'] = addrTXInfo['txids']
        else:
            addrInfo['amountRecv'] = 0.0
    if session['logged_in']:
        userInfo = db.getUserByName(session['username'])
        userInfo['balance'] = rpc.getBalance(session['username'])
        userInfo['error'] = error
        addrInfo.update(userInfo)
    return render_template('addressInfo.html', **addrInfo)

@app.route('/transactionInfo/<txid>')
def transactionInfo(txid):
    error = None
    transactInfo = rpc.getTransactionInfo(txid)
    if transactionInfo:
        pass    
    
    if session['logged_in']:
        userInfo = db.getUserByName(session['username'])
        userInfo['balance'] = rpc.getBalance(session['username'])
        userInfo['error'] = error
        transactInfo.update(userInfo)
    return render_template('addressInfo.html', **transactInfo)


@app.route('/send', methods=['GET', 'POST'])
def send():
    if not session['logged_in']:
        redirect(url_for('index'))

    ballance = rpc.getBalance(session['username'])
    error = None
    
    if request.method == 'POST':
        toAddress = request.form['toAddress']
        amount = float(request.form['amount'])
        message = request.form['message']
        unit = float(request.form['unit'])
        amount *= unit
        addrInfo = rpc.getAddressInfo(toAddress)
        if addrInfo['isvalid']:
            if addrInfo['ismine']:
                if ballance >= amount:
                    db.createTransaction(session['userid'], toAddress, amount, message)
                else:
                    error = "Insufficient Funds to send %f DAK" % amount
            else:
                if ballance >= amount + 0.02:
                    db.createTransaction(session['userid'], toAddress, amount, message)                   
                else:
                    error = "Insufficient Funds to send %f DAK.  Please keep in mind the 0.02 DAK network fee to transfer out of MT. CCDC" % amount
        elif db.checkForExistingUser(toAddress):
            toAddress = rpc.getAddress(toAddress)
            if ballance >= amount:
                db.createTransaction(session['userid'], toAddress, amount, message)
            else:
                error = "Insufficient Funds to send %f DAK" % amount
        else:
            error = "%s is an invalid DakotaCoin address"

    userInfo = db.getUserByName(session['username'])
    userInfo['balance'] = ballance
    userInfo['error'] = error
    return render_template('send.html', **userInfo)
        

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST' and 'email' in request.form:
        username = request.form['NewUsername']
        password = request.form['NewPassword']
        if not any(db.checkForExistingUser(password)):
            registerUser(username
                        ,password
                        ,request.form['email']
            )

            session['username'] = username
            session['userid'] = db.getUserByName(username)['id']
            session['logged_in'] = True

            return redirect(url_for('accountInfo', username=session['username']))
        else:
            error = "Username already registerd"
    if session['logged_in']:
        return redirect(url_for('index'))

    return render_template('register.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    if 'logged_in' in session:
        session['logged_in'] = False
    if 'username' in session:
        del session['username']
    return redirect(url_for('index'))

@app.after_request
def afterRequest(response):
    if response.status_code != 500:
        if request.form:
            data = request.form
        else:
            data = ''
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.info('%s %s %s %s %s %s %s',
            ts,
            request.remote_addr,
            request.method,
            request.scheme,
            request.url,
            response.status,
            data)
    return response

@app.errorhandler(Exception)
def logExceptions(e):
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
        ts,
        request.remote_addr,
        request.method,
        request.scheme,
        request.url,
        tb)
    return "Internal Server Error", 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')



try:
    with open('config.json') as fp:
        config = json.load(fp)
except FileNotFoundError:
    print('Could not find configuration file at %s' % args.ConfigFile)
    sys.exit(-2)
except PermissionError:
    print('Could not read configuration file at %s' % args.ConfigFile)
    sys.exit(-3)
except IOError as e:
    print('Error accessing configuration file at %s')
    print(str(e))
    sys.exit(-4)

db = dakDB.DakDb(
    config['dbHost']
    ,config['dbDatabase']
    ,config['dbUser']
    ,config['dbPassword']
)
handler = RotatingFileHandler(config['logFile'], maxBytes=config['logMaxBytes'], backupCount=config['logBackups'])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

config.update(db.getCurentConfig())

rpc = dakRPC.dakRpc(
    config['RPC_address'].strip()
    ,config['RPC_port']
    ,config['RPC_user']
    ,config['RPC_password']
)
p = Process(target=processTransactions, args=(db, rpc, logger, config['transact_interval']))
p.start()
# processTransactions(db, rpc, logger, s)
# import code
# code.interact(local=locals())
ldapAuth = dakLDAP.dakLdap(config['ldapHost'],config['ldapUser'], config['ldapPassword'], config['ldapBaseDN'], config['domain'], config['adminGroup'])

app.secret_key = config['webAppSessionSecretKey']

if __name__ == "__main__":
    app.run(debug=True)
