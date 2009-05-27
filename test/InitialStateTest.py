from TestSetup import resetSession, DatabaseTestCase
import Mapping as M
import InitialState

class InitialStateTest(DatabaseTestCase):
    def mockImportAll(self):
        self.wasImportAllCalled = True
    
    def mockRebuildSchema(self):
        pass

    def setUp(self):
        DatabaseTestCase.setUp(self)
        self.mockAttr(InitialState, 'rebuildSchema', self.mockRebuildSchema)
        self.mockAttr(InitialState, 'importAll', self.mockImportAll)
        self.wasImportAllCalled = False

    def testCreateInitialStateCreatesPersons(self):
        InitialState.createInitialState()
        george = self.session.query(M.Person).get_by(givenName='George')
        self.assertNotEqual(None, george)

    def testCreateInitialStateCreatesTenancies(self):
        InitialState.createInitialState()
        george = self.session.query(M.Person).get_by(givenName='George')
        self.assertNotEquals(0, len(george.tenancies))

    def testCreateInitialStateDestroysPreviousState(self):
        InitialState.createInitialState()
        InitialState.createInitialState()
        georges = self.session.query(M.Person).select_by(givenName='George')
        self.assertEqual(1, len(georges))

    def testCreateInitialStateCallsImportAll(self):
        InitialState.createInitialState()
        self.assertEqual(True, self.wasImportAllCalled)
