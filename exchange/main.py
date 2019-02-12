import sys
import json
import sched
import ldap3
import logging
import argparse
import traceback
from multiprocessing import Process
from pprint import pprint
from time import strftime, sleep
from flask_simpleldap import LDAP
from logging.handlers import RotatingFileHandler
from flask import Flask, g, redirect, render_template, request, session, url_for

import dakDB
import dakRPC

app = Flask(__name__)

app.config['LDAP_HOST'] = 'dc01'
app.config['LDAP_USERNAME'] = 'cn=Administrator,CN=Users,DC=ccdc,DC=local'
app.config['LDAP_PASSWORD'] = 'Password1!'
app.config['LDAP_BASE_DN'] = 'CN=Users,DC=ccdc,DC=local'
app.config['LDAP_USER_OBJECT_FILTER'] = '(&(objectclass=person)(cn=%s))'

ldap = LDAP(app)

def processTransactions(db, rpc, logger, delay):
    while True:
        txs = db.getUnsetTransactions()
        sent = []
        # import code
        # code.interact(local=locals())
        for tx in txs:
            # try:
            rpc.send(tx['user_name'], tx['toAddress'], tx['amount'], tx['message'])
            sent.append(tx['txid'])
            # except Exception as e:
            #     ts = strftime('[%Y-%b-%d %H:%M]')
            #     tb = traceback.format_exc()
            #     logger.error('%s %s %s %s DAKRPC ERROR IN SENDING\n%s',
            #         ts,
            #         tx['txid'],
            #         tx['toAddress'],
            #         tx['user_name'],
            #         tb)
        if any(sent):
            db.markTransactionsAsSent(sent)
        sleep(delay)


def registerUser(username, password, email):
    db.createUser(username, password, email)
    rpc.addNewAccount(username)

def authenticate(username, password):
    # return ldap.bind_user(username, password)
    return db.checkUserCreds(username, password)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        form = request.form
        if 'username' in form and 'password' in form:
            if authenticate(form['username'], form['password']):
                session['logged_in'] = True
                session['username'] = form['username']
                g.user = form['username']
            else:
                error = 'Invalid Username or Password'
    else:
        if 'logged_in' in session:
            userInfo = db.getUserByName(session['username'])
            return render_template('index.html', **userInfo)
    return render_template('index.html', error=error)

@app.route('/account/<username>')
def account(username):
    pprint(rpc.getBalance(username))
    return username

# @app.route('/send', methods=['GET', 'POST'])
# def send():
#     if request.method == 'POST':
        

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
            session['userid'] = db.getUserByName(username)['userid']
            session['logged_in'] = True

            return redirect(url_for('account', username=session['username']))
        else:
            error = "Username already registerd"
    if 'username' in session:
        return redirect(url_for('index'))

    return render_template('register.html', error=error)

@app.route('/logout', methods=['GET'])
def logout():
    if 'logged_in' in session:
        del session['logged_in']
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser('Mt. CCDC Crypto exchange backend')
    parser.add_argument('ConfigFile', type=str, help='File containing inital configureation information')
    args = parser.parse_args()

    try:
        with open(args.ConfigFile) as fp:
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

    app.secret_key = config['webAppSessionSecretKey']
    app.run(debug=True)
