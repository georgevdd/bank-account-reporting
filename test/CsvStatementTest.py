#!/usr/bin/env python

import sys
sys.path.append('..')

import unittest
import CsvStatement

class CsvStatementTest(unittest.TestCase):
    MONTH_TEXT = '''Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,Debit Amount,Credit Amount,Balance,
25/11/2011,BGC,00-11-22,12345678,SOMEONEWHOPAYSME,,6543.21,6655.55
01/11/2011,DEB,00-11-22,12345678,SOMEONEWHOMIPAY ,12.34,,112.34'''

    def testCsvStatement(self):
        stmt = CsvStatement.CsvStatement(CsvStatementTest.MONTH_TEXT)
        self.assertEquals(2, len(stmt.transactions))
        
        t = stmt.transactions[0]
        self.assertEquals(date(2011, 11, 25), t.date)
        self.assertEquals('BCG', t.type)
        self.assertEquals('SOMEONEWHOPAYSME', t.description)
        self.assertEquals(Decimal(6543.21), t.creditAmount)

        t = stmt.transactions[1]
        self.assertEquals(date(2011, 11, 01), t.date)
        self.assertEquals('DEB', t.type)
        self.assertEquals('SOMEONEWHOMIPAY', t.description)
        self.assertEquals(Decimal(12.34), t.creditAmount)
