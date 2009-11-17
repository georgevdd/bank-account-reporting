#!/usr/bin/env python

import Halifax
import MsMoney
from os.path import join as pjoin, splitext, exists
from StringIO import StringIO
from datetime import date
import os
import re

STORE_PATH = "/home/georgevdd/bills/bank-statements/"

def statementFilename(stmt):
    return '%s_%s' % (stmt.beginDate.isoformat(), stmt.endDate.isoformat())

statementFilenamePattern = re.compile('(XXXX)-(XX)-(XX)_(XXXX)-(XX)-(XX)'.replace('X','\d'))

def statementDateRangeFromFilename(filename):
    match = statementFilenamePattern.match(filename)
    numbers = match and [int(x) for x in match.groups()] or None
    if numbers is None:
        raise Exception('\"%s\" is not a valid statement filename.' % filename)
    try:
        return (date(*numbers[0:3]), date(*numbers[3:6]))
    except ValueError:
        raise ValueError('\"%s\" is not a valid statement filename.' % filename)

def genDownloadedStatementFilenames():
    for path, dirs, files in os.walk(STORE_PATH):
        for filename in files:
            if statementFilenamePattern.match(filename):
                yield pjoin(path, filename)

def fetchNewStatements(forceFetchAll=False):
    Halifax.logIn()
    print 'Logged in.'
    try:
        consecutiveParseFailures = 0
        for text in Halifax.genAllStatements():
            try:
                stmt = MsMoney.Statement(StringIO(text))
                consecutiveParseFailures = 0
            except Exception, e:
                consecutiveParseFailures += 1
                if consecutiveParseFailures == 4:
                    print 'Too many consecutive parse failures - giving up.'
                    raise e
                else:
                    print 'Skipping document; it could not be understood.'
                    continue
            filename = statementFilename(stmt)
            print filename
            filename = pjoin(STORE_PATH, filename)
            if exists(filename) and not forceFetchAll:
                print 'File exists. Stopping.'
                break
            file = open(filename, 'w')
            print >> file, text
            file.close()
    finally:
        Halifax.logOut()
        print 'Logged out.'

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        STORE_PATH = sys.argv[1]
    print 'Fetching statements to', STORE_PATH
    fetchNewStatements()
