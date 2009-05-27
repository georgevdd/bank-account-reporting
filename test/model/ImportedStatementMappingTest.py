import TestSetup
import Model as M
from datetime import date
from TestSetup import resetSession, DatabaseTestCase

class ImportedStatementTest(DatabaseTestCase):
    def testImportedStatementPersists(self):
        i = M.ImportedStatement(date(2000, 1, 1), date(2000, 2, 2))
        self.session.add(i)
        resetSession()
        i = self.session.query(M.ImportedStatement).first()
        self.assertEqual(date(2000, 1, 1), i.beginDate)
        self.assertEqual(date(2000, 2, 2), i.endDate)
