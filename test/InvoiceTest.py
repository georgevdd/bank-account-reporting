from TestSetup import resetSession, DatabaseTestCase
import Mapping as M
import Invoice
from datetime import date

class GetTenantsTest(DatabaseTestCase):
    def testGetTenantsIsEmptyWhenNoPersonsExist(self):
        self.assertEqual([], Invoice.getTenants(date(2006, 1, 1)))

    def testGetTenantsIncludesCurrentTenant(self):
        p = M.Person('Joe', 'Bloggs')
        p.tenancies.append(M.Tenancy(date(2006, 1, 1), date(2006, 2, 2)))
        self.session.save(p)
        resetSession()
        self.session.update(p)
        
        ts = Invoice.getTenants(date(2006, 1, 20))
        self.assertEqual(p, ts[0])

    def testGetTenantsExcludesPreviousTenant(self):
        p = M.Person('Joe', 'Bloggs')
        p.tenancies.append(M.Tenancy(date(2005, 1, 1), date(2005, 2, 2)))
        self.session.save(p)
        resetSession()
        
        ts = Invoice.getTenants(date(2006, 1, 20))
        self.assertEqual([], ts)

    def testGetTenantsExcludesFutureTenant(self):
        p = M.Person('Joe', 'Bloggs')
        p.tenancies.append(M.Tenancy(date(2007, 1, 1), date(2007, 2, 2)))
        self.session.save(p)
        resetSession()
        
        ts = Invoice.getTenants(date(2006, 1, 20))
        self.assertEqual([], ts)

    def testCountTenantsCountsCurrentTenants(self):
        ps = [M.Person('Joe', 'Bloggs'), M.Person('John', 'Doe')]
        for p in ps:
            p.tenancies.append(M.Tenancy(date(2006, 1, 1), date(2006, 2, 2)))
            self.session.save(p)
        resetSession()
        for p in ps:
            self.session.update(p)
        
        numTs = Invoice.countTenants(date(2006, 1, 20))
        self.assertEqual(len(ps), numTs)
