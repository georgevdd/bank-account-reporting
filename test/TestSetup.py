#!/usr/bin/env python

import sys
sys.path.append('..')

import Schema
import Database
import sqlalchemy as sqla
import unittest

testDbs = 'postgres://test:test@localhost/bills_test'

db = sqla.create_engine(testDbs)

def clearTables():
    c = getSession().connection(None)
    for t in Schema.metadata.sorted_tables.__reversed__():
        c.execute(t.delete())

getSession = Database.getSession
resetSession = Database.resetSession


def runOneTest(testMethod):
    '''Creates and runs a test case instance for a single method of a
    TestCase subclass.'''
    testClass = testMethod.im_class
    testInstance = testClass(testMethod.__name__)
    testInstance.debug()

class MockingTestCase(unittest.TestCase):
    '''A test case that provides support for plugging in mock objects during
    setup and unplugs them automatically during teardown.'''
    # Unique object for identifying mocks that should be deleted instead of reset.
    delenda = object()

    def __init__(self, name):
        unittest.TestCase.__init__(self, name)
        self.__mocks__ = {}

    def mockAttr(self, object, name, mock):
        if hasattr(object, name):
            self.__mocks__[(object, name)] = getattr(object, name)
        else:
            self.__mocks__[(object, name)] = MockingTestCase.delenda
        setattr(object, name, mock)

    def unmockAttrs(self):
        for k, v in self.__mocks__.iteritems():
            object, name = k
            original = v
            if original is MockingTestCase.delenda:
                delattr(object, name)
            else:
                setattr(object, name, original)

    def tearDown(self):
        self.unmockAttrs()
        unittest.TestCase.tearDown(self)

class DatabaseTestCase(MockingTestCase):
    def setUp(self):
        MockingTestCase.setUp(self)
        self.mockAttr(Database, 'getDbs', lambda: testDbs)
        self.session = Database.ensureSession()
        clearTables()

    def _get_engine(self):
        return self.session.connection(None).engine

    engine = property(_get_engine)

    def tearDown(self):
        if getSession() is not None:
            getSession().expunge_all()
            resetSession()
        self.session = None
        MockingTestCase.tearDown(self)

if __name__ == '__main__':
    oldGetDbs = Database.getDbs
    try:
        setattr(Database, 'getDbs', lambda: testDbs)
        Database.main()
    finally:
        setattr(Database, 'getDbs', oldGetDbs)
