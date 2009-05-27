import TestSetup
import Model as M
from datetime import datetime
from TestSetup import resetSession, DatabaseTestCase

class EventTest(DatabaseTestCase):
    def testEventPersists(self):
        dt = datetime.utcnow()
        e = M.Event(dt)
        self.session.add(e)
        resetSession()
        e = self.session.query(M.Event).first()
        self.assertEqual(dt.replace(tzinfo=e.eventTimestamp.tzinfo), e.eventTimestamp)

class EventstampedObjectTest(DatabaseTestCase):        
    def testEventstampedObjectsShareEvent(self):
        eso1 = M.EventStamped()
        eso2 = M.EventStamped()
        self.assert_(eso1.creationEvent is eso2.creationEvent)
    
    def testResetSessionBeginsNewEvent(self):
        eso1 = M.EventStamped()
        resetSession()
        eso2 = M.EventStamped()
        self.assert_(eso1.creationEvent is not eso2.creationEvent)
