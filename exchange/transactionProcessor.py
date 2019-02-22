from time import sleep
def processTransactions(db, rpc, logger, delay):
    while True:
        txs = db.getUnsetTransactions()
        sent = []
        for tx in txs:
            try:
                daktxid = rpc.send(tx['user_name'], tx['toAddress'], tx['amount'], tx['message'])
                sent.append((daktxid, tx['txid']))
            except Exception as _:
                ts = strftime('[%Y-%b-%d %H:%M]')
                tb = traceback.format_exc()
                logger.error('%s %s %s %s DAKRPC ERROR IN SENDING\n%s',
                    ts,
                    tx['txid'],
                    tx['toAddress'],
                    tx['user_name'],
                    tb)
        if any(sent):
            db.markTransactionsAsSent(sent)
        sleep(delay)