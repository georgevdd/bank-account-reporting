#!/usr/bin/env python

import sqlalchemy as sqla
import sqlalchemy.orm as orm
from getpass import getpass
from urllib import quote_plus
import sys
import Model

HOST = 'localhost'
DATABASE = 'bills'

def getBillsDbs(user, password):
    host = HOST
    database = DATABASE
    dbs = 'postgres://%s:%s@%s/%s' % tuple(map(quote_plus,
        (user, password, host, database)))
    return dbs
    
def collectLoginDetails():
    user = raw_input('User name: ')
    if sys.stdin.isatty():
        password = getpass()
    else:
        password = sys.stdin.readline().strip()
    return user, password

def getDbs():
    user, password = collectLoginDetails()
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

def createSession():
    return orm.create_session(bind=db)

def ensureSession():
    global __session__
    ensureConnected()
    if __session__ is None:
        __session__ = createSession()
    if __session__ is None:
        raise Exception('Failed to create session (db=%s)' % db)
    return __session__

def requireSession():
    if __session__ is None:
        raise Exception("No session.")
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

def withSession(f):
  ensureSession()
  result = f()
  resetSession()
  return result

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
