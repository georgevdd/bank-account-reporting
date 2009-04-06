import Schema
import MsMoney
from datetime import datetime
import sqlalchemy
import sqlalchemy.orm as orm
sqlfunc = sqlalchemy.func
# For Python 2.3, decimal is available from
# http://sourceforge.net/projects/sigefi
from decimal import Decimal

class Event(object):
    '''Object representing an update to the database. All eventstamped
    objects that were created in the same event will have a reference
    to the same eventstamp.'''
    def __init__(self, eventTimestamp):
        self.eventTimestamp = eventTimestamp

    currentEvent = None

def makeEventstampedClass(cls):
    class EventStamped(cls):
        '''Base class for all types where we need to know exactly when
        each instance was created.'''
        def __init__(self, *args, **kwargs):
            cls.__init__(self, *args, **kwargs)
            if Event.currentEvent is None:
                Event.currentEvent = Event(datetime.utcnow())
            self.creationEvent = Event.currentEvent

    return EventStamped

MAXIMUM_LIKELY_PAYMENT = Decimal('1000.00')

Transaction = makeEventstampedClass(MsMoney.Transaction)

class ImportedStatement(object):
    def __init__(self, beginDate, endDate):
        self.beginDate = beginDate
        self.endDate = endDate

ImportedStatement = makeEventstampedClass(ImportedStatement)

def initMappings():
    a = sqlalchemy    
    s = Schema
    
    def eventstampedMapper(class_, local_table, **kwargs):
        kwargs.setdefault('properties', {})['creationEvent'] = orm.relation(Event)
        return orm.mapper(class_, local_table, **kwargs)
    
    orm.mapper(Event, s.event, properties={
        'eventTimestamp' : s.event.c.event_timestamp,
        })
    
    eventstampedMapper(Transaction, s.statementItem, properties={
        'date' : s.statementItem.c.dtposted,
        'amount' : s.statementItem.c.trnamt
        })

    eventstampedMapper(ImportedStatement, s.importedStatement, properties={
        'beginDate' : s.importedStatement.c.begin_date,
        'endDate' : s.importedStatement.c.end_date,
        })

initMappings()
