import TestSetup
from unittest import TestCase
from datetime import date
from decimal import Decimal
from TestSetup import testDbs, resetSession, DatabaseTestCase
from StringIO import StringIO
import MsMoney, Model
from Model import ImportedStatement
import QifStatement

import ImportStatements as IS
import Database as DB

class ImportStatementsTest(DatabaseTestCase):
    def mockGenDownloadedStatementFilenames(self, format):
        return ['1000-01.qif']

    def mockOpen(self, filename):
        self.assertEqual('1000-01.qif', filename)
        return StringIO('DUMMY_CONTENT')

    def mockStatement(thisTest):
        class MockStatement:
            def __init__(self, file):
                thisTest.assertEqual(['DUMMY_CONTENT'], file.readlines())
                self.beginDate = date(1000, 01, 01)
                self.endDate = date(1000, 01, 31)

                qifItems = QifStatement.parseQif(StringIO('''D31/01/1000
PMemo 1
T-123.45
^
D30/01/1000
PMemo 2
T-456.78
^
'''))

                self.transactions = [QifStatement.Transaction(item, i) for i, item in enumerate(qifItems)]
        return MockStatement
    
    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.mockAttr(IS, 'genDownloadedStatementFilenames', self.mockGenDownloadedStatementFilenames)
        self.mockAttr(IS, 'open', self.mockOpen)
        self.mockAttr(IS, 'Statement', self.mockStatement())

    def testImportAllCreatesImportedStatements(self):
        IS.importAll()

        importedStatements = list(self.session.query(ImportedStatement))
        self.assertNotEqual(None, importedStatements)
        self.assertEqual(1, len(importedStatements))
        record = importedStatements[0]
        self.assertEqual(date(1000, 01, 01), record.beginDate)
        self.assertEqual(date(1000, 01, 31), record.endDate)

    def testImportAllCreatesTransactions(self):
        IS.importAll()

        transactions = list(self.session.query(Model.Transaction))
        self.assertNotEqual(None, transactions)
        self.assertEqual(2, len(transactions))
        
