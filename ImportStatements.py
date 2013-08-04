#!/usr/bin/env python

import sys
import Model
from Database import ensureSession, resetSession
from QifStatement import QifStatement as Statement
import StatementStore

genDownloadedStatementFilenames = StatementStore.genDownloadedStatementFilenames

def importAll():
    session = ensureSession()
    for filename in genDownloadedStatementFilenames('qif'):
        stmt = Statement(open(filename))
        print '%s - %s' % (stmt.beginDate, stmt.endDate),
        stmt_exists = (session.query(Model.ImportedStatement)
                  .filter_by(beginDate=stmt.beginDate, endDate=stmt.endDate)
                  .first() is not None)
        for trn in stmt.transactions:
            trn_exists = (session.query(Model.Transaction)
                  .filter_by(fitid=trn.fitid)
                  .first() is not None)
            if trn_exists ^ stmt_exists:
                raise Exception('Something very odd about fitid %s' % trn.fitid)
            if not trn_exists:
                # Create a Model.Transaction out of a
                # MsMoney.Transaction.
                trn = Model.Transaction(trn.date, trn.creditAmount,
                    trn.fitid, trn.description, trn.memo)
                session.add(trn)
        if stmt_exists:
            print 'already exists.'
        else:
            session.add(Model.ImportedStatement(
                *StatementStore.statementDateRangeFromFilename(filename)))
            print 'saved.'
            
        resetSession()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        StatementStore.STORE_PATH = sys.argv[1]
    print 'Looking for statements in', StatementStore.STORE_PATH
    importAll()
