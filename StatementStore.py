#!/usr/bin/env python

import Halifax
import QifStatement
import CsvStatement
from os.path import join as pjoin, splitext, exists
from StringIO import StringIO
from datetime import date
import os
import re

STORE_PATH = "/Users/georgevdd/Google Drive/bills"

FORMATS = {
    'qif': QifStatement.parseQif,
    'csv': CsvStatement.CsvStatement,
    }

def statementFilename(month, format):
    return '%s.%s' % (month.strftime('%Y-%m'), format)

def statementFilenamePattern(format):
    return re.compile(r'(XXXX)-(XX)\.'.replace('X','\d') + format)

def statementDateRangeFromFilename(filename):
    format = splitext(filename)[1][1:]
    match = statementFilenamePattern(format).match(filename)
    numbers = match and [int(x) for x in match.groups()] or None
    if numbers is None:
        raise Exception('\"%s\" is not a valid statement filename.' % filename)
    try:
        start = date(numbers[0], numbers[1], 1)
        end = date + relativedelta(months=1, days=-1)
        return start, end
    except ValueError:
        raise ValueError('\"%s\" is not a valid statement filename.' % filename)

def genDownloadedStatementFilenames(format='qif'):
    for path, dirs, files in os.walk(STORE_PATH):
        for filename in files:
            if statementFilenamePattern(format).match(filename):
                yield pjoin(path, filename)

def fetchNewStatements(forceFetchAll=False, format='qif'):
    Halifax.logIn()
    print 'Logged in.'
    try:
        consecutiveParseFailures = 0
        existingFiles = 0
        for month, response in Halifax.genAllStatements(format):
            try:
                text = response.read()
                statement = FORMATS[format](StringIO(text))
                consecutiveParseFailures = 0
            except Exception, e:
                consecutiveParseFailures += 1
                if consecutiveParseFailures == 4:
                    print 'Too many consecutive parse failures - giving up.'
                    raise e
                else:
                    print 'Skipping document; it could not be understood.'
                    continue
            filename = statementFilename(month, format)
            print filename
            filename = pjoin(STORE_PATH, filename)
            if exists(filename):
                if existingFiles > 0 and not forceFetchAll:
                    print ('File exists (and is not the most '
                           'recent existing). Stopping.')
                    break
                else:
                    existingFiles += 1
            print >> open(filename, 'w'), text
    finally:
        Halifax.logOut()
        print 'Logged out.'

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        STORE_PATH = sys.argv[1]
    print 'Fetching statements to', STORE_PATH
    fetchNewStatements()
