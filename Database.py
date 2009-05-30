#!/usr/bin/env python

import sqlalchemy as sqla
import sqlalchemy.orm as orm
from getpass import getpass
from urllib import quote_plus
import Model

HOST = 'localhost'
DATABASE = 'bills'

def getBillsDbs(user, password):
    host = HOST
    database = DATABASE
    dbs = 'postgres://%s:%s@%s/%s' % tuple(map(quote_plus,
        (user, password, host, database)))
    return dbs

def getDbs():
    user = raw_input('User name: ')
    password = getpass()
    return getBillsDbs(user, password)

db = None

def connect():
    global db
    db = sqla.create_engine(getDbs(), encoding='utf-8')
    try:
        db.connect()
    except:
        db = None
        raise
    
def ensureConnected():
    global db
    if db is None:
        connect()

def _doDropSchema(someDb):
    import Schema
    Schema.metadata.drop_all(someDb)

def _doCreateSchema(someDb):
    import Schema
    Schema.metadata.create_all(someDb)

def rebuildSchema():
    ensureConnected()
    _doDropSchema(db)
    _doCreateSchema(db)

def dropAllSchemaTables():
    ensureConnected()
    _doDropSchema(db)

def addNewSchemaTables():
    import Schema
    ensureConnected()
    _doCreateSchema(db)

__session__ = None

def ensureSession():
    global __session__
    ensureConnected()
    if __session__ is None:
        __session__ = orm.create_session(bind=db)
    if __session__ is None:
        raise Exception('Failed to create session (db=%s)' % db)
    return __session__

def getSession():
    return __session__

def flushSession():
    session = getSession()
    session.flush()
    # A new Event will be created lazily if necessary.
    Model.Event.currentEvent = None

def resetSession():
    session = getSession()
    session.flush()
    session.expunge_all()
    # A new Event will be created lazily if necessary.
    Model.Event.currentEvent = None

def main():
    import sys
    argv = sys.argv
    action = argv[1]
    if action == 'add_new':
        addNewSchemaTables()
    elif action == 'rebuild':
        rebuildSchema()
    else:
        print 'Unknown action', action

if __name__ == '__main__':
    main()
