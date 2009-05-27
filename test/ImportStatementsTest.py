from unittest import TestCase
from datetime import date
from decimal import Decimal
from TestSetup import testDbs, resetSession, DatabaseTestCase
from StringIO import StringIO
import MsMoney, Mapping
from Mapping import ImportedStatement

import ImportStatements as IS
import Database as DB

class ImportStatementsTest(DatabaseTestCase):
    def mockGenDownloadedStatementFilenames(self):
        return ['DUMMY_FILENAME']

    def mockOpen(self, filename):
        self.assertEqual('DUMMY_FILENAME', filename)
        return StringIO('DUMMY_CONTENT')

    def mockStatement(thisTest):
        class MockStatement:
            def __init__(self, file):
                thisTest.assertEqual(['DUMMY_CONTENT'], file.readlines())
                self.beginDate = date(1000, 01, 06)
                self.endDate = date(1000, 02, 07)
                self.transactions = [
                     MsMoney.Transaction(date(1000, 01, 06), Decimal('123.45'), 'FITID1', 'Example Transaction 1', 'Memo 1'),
                     MsMoney.Transaction(date(1000, 01, 26), Decimal('456.78'), 'FITID2', 'Example Transaction 2', 'Memo 2')
                 ]
        return MockStatement
    
    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.mockAttr(IS, 'genDownloadedStatementFilenames', self.mockGenDownloadedStatementFilenames)
        self.mockAttr(IS, 'open', self.mockOpen)
        self.mockAttr(IS, 'Statement', self.mockStatement())

    def testImportAllCreatesImportedStatements(self):
        IS.importAll()
        resetSession()
        importedStatements = self.session.query(ImportedStatement).select()
        self.assertNotEqual(None, importedStatements)
        self.assertEqual(1, len(importedStatements))
        record = importedStatements[0]
        self.assertEqual(date(1000, 01, 06), record.beginDate)
        self.assertEqual(date(1000, 02, 07), record.endDate)

    def testImportAllCreatesTransactions(self):
        IS.importAll()
        resetSession()
        transactions = self.session.query(Mapping.Transaction).select()
        self.assertNotEqual(None, transactions)
        self.assertEqual(2, len(transactions))
        