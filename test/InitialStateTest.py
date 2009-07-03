import TestSetup
from TestSetup import resetSession, DatabaseTestCase, getSession
import Model as M
from decimal import Decimal
import InitialState

class InitialStateTest(DatabaseTestCase):
    def mockImportAll(self):
        self.wasImportAllCalled = True
    
    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.mockAttr(InitialState, 'importAll', self.mockImportAll)
        self.wasImportAllCalled = False

    def testCreateInitialStateCreatesPersons(self):
        InitialState.createInitialState()
        george = self.session.query(M.Person) \
            .filter_by(givenName='George') \
            .first()
        self.assertNotEqual(None, george)

    def testCreateInitialStateCreatesTenancies(self):
        InitialState.createInitialState()
        george = self.session.query(M.Person) \
            .filter_by(givenName='George') \
            .first()
        self.assertNotEquals(0, len(george.tenancies))

    def testCreateInitialStateDestroysPreviousState(self):
        InitialState.createInitialState()
        InitialState.createInitialState()
        georges = list(self.session.query(M.Person) \
            .filter_by(givenName='George'))
        self.assertEqual(1, len(georges))

    def testCreateInitialStateCallsImportAll(self):
        InitialState.createInitialState()
        self.assertEqual(True, self.wasImportAllCalled)
