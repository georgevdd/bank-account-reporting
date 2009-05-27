import TestSetup
import Model as M
from datetime import date
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal
from TestSetup import resetSession, DatabaseTestCase

class TenancyTest(DatabaseTestCase):
    def testPersonInitiallyHasNoTenancies(self):
        p = M.Person('Joe', 'Bloggs')
        self.assert_(hasattr(p, 'tenancies'))
        self.assertEqual(0, len(p.tenancies))
        
    def testTenancyCanBeAssignedToPerson(self):
        p = M.Person('Joe', 'Bloggs')
        t = M.Tenancy(date(2000, 1, 1))
        p.tenancies.append(t)
        self.assert_(t in p.tenancies)
        self.assertEqual(p, t.person)

    def testTenancyPersists(self):
        p = M.Person('Joe', 'Bloggs')
        t = M.Tenancy(date(2000, 1, 1))
        p.tenancies.append(t)
        self.session.add(p)
        resetSession()
        self.session.add(p)
        t = self.session.query(M.Tenancy).first()
        self.assertNotEqual(None, t)
        self.assertEqual(p, t.person)
        self.assertEqual(date(2000, 1, 1), t.dateMovedIn)
