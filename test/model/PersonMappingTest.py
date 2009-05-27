import TestSetup
import Model as M
from TestSetup import resetSession, DatabaseTestCase

class PersonTest(DatabaseTestCase):
    def testPersonPersists(self):
        p = M.Person('Joe', 'Bloggs')
        self.session.add(p)
        resetSession()
        p = self.session.query(M.Person).first()
        self.assertEqual('Joe', p.givenName)
        self.assertEqual('Bloggs', p.familyName)
