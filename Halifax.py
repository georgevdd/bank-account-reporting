from mechanize import urlopen, Request, ParseResponse, ParseFile
from urllib import urlencode
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup
from sys import stdin, stderr
from getpass import getpass
from urlparse import urljoin

loggedIn = False
docsListHit = False

HOMEPAGE_URL = 'http://www.halifax-online.co.uk'
HOMEPAGE_TITLE = 'Halifax - Welcome to Online'
MEMORABLE_INFO_FORM_TITLE = 'Enter memorable information'
DOCS_LIST_URL = ('https://online-documents.halifax-online.co.uk' +
    '/onlinedocuments/app/oddocuments.asp')
DOC_URL = ('https://online-documents.halifax-online.co.uk'+
        '/onlinedocuments/app/odviewdocument.asp')
LOGOUT_URL = 'https://www.halifax-online.co.uk/_mem_bin/SignOff.asp'

class LoginInfo(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

def getLoginInfo():
    return LoginInfo(getpass('Username: '), getpass())

def getMemorableInfo(indices):
    return getpass('Memorable info characters %d, %d and %d: ' % tuple(indices))

def checkPageTitle(soup, expectedTitle):
    title = soup.title.contents[0].strip()
    if expectedTitle != title:
        global errorSoup
        errorSoup = soup
        raise Exception('Title was "%s", not "%s"' % (title, expectedTitle))

def checkForErrors(soup):
    errors = soup.findAll(id='AdditionalInfo')
    if errors:
        global errorSoup
        errorSoup = soup
        raise Exception(errors)

def doWithRetries(func, retries = 4, **kwargs):
    while (retries > 0):
        try:
            return func(**kwargs)
        except Exception, e:
            print "Exception %s - retrying %s" % (e, func.__name__)
        retries -= 1
    return func(**kwargs)

class LoginForm(object):
    def __init__(self, httpResponse):
        responseText = httpResponse.read()
        soup = BeautifulSoup(responseText)

        checkPageTitle(soup, HOMEPAGE_TITLE)

        forms = ParseFile(StringIO(responseText),
                          httpResponse.geturl(),
                          backwards_compat=False)
        self.form = forms[1]

    def populate(self, loginInfo):
        self.form['Username'] = loginInfo.username
        self.form['password'] = loginInfo.password
        self.form.find_control('JSEnabled').readonly = False
        self.form['JSEnabled'] = 'true'

    def submissionRequest(self):
        return self.form.click('btnContinue')

class MemorableInfoForm(object):
    def __init__(self, httpResponse):
        pageText = httpResponse.read()
        soup = BeautifulSoup(pageText)

        checkForErrors(soup)
        checkPageTitle(soup, MEMORABLE_INFO_FORM_TITLE)

        self.memorableInfoIndices = [
            int(soup
                .find('span', id='ctl00_MainPageContent_labelChar%d' % i)
                .string[-1])
            for i in range(1, 4)]

        forms = ParseFile(StringIO(pageText),
                          httpResponse.geturl(),
                          backwards_compat=False)
        self.form = forms[0]

    def populate(self, memorableInfoCharacters):
        if len(memorableInfoCharacters) != 3:
            raise ValueError('Expected three memorable info characters.')

        for i, v in zip(range(1, 4), memorableInfoCharacters.lower()):
            self.form.set_value_by_label(
                ['\xa0%s\xa0' % v],
                ('ctl00$MainPageContent$char%d$DropDownList' % i))
        self.form.find_control('ctl00$javascriptEnabled1').readonly = False
        self.form['ctl00$javascriptEnabled1'] = 'true'

    def submissionRequest(self):
        return self.form.click('ctl00$MainPageContent$_signin')

def logIn():
    loginForm = LoginForm(urlopen(HOMEPAGE_URL))
    loginInfo = getLoginInfo()
    loginForm.populate(loginInfo)

    memorableInfoForm = MemorableInfoForm(urlopen(
        loginForm.submissionRequest()))
    memorableInfo = getMemorableInfo(memorableInfoForm.memorableInfoIndices)
    memorableInfoForm.populate(memorableInfo)

    pageText = urlopen(memorableInfoForm.submissionRequest()).read()
    checkForErrors(BeautifulSoup(pageText))

    global loggedIn, docsListHit
    loggedIn = True
    docsListHit = False

def ensureDocsListHit():
    global docsListHit
    if not docsListHit:
        urlopen(DOCS_LIST_URL).read()
        docsListHit = True

def getDoc(nthMostRecent):
    ensureDocsListHit()

    docData = {
        'DLFormats':'ofx',
        'btnDownload':'Go',
        'doc':('A%d' % nthMostRecent)
        }
    response = urlopen(DOC_URL , data=urlencode(docData))
    docText = response.read()
    return docText

def isServiceInterruption(doc):
    soup = BeautifulSoup(doc)
    return ((soup.title is not None) and
            (len(soup.title.contents) > 0) and
            (soup.title.contents[0] == 'Service Interruption'))

def genAllStatements(maxFailures=4):
    gotAnyDoc = False
    nextDocIndex = 1
    while True:
        try:
            doc = getDoc(nextDocIndex)
            if isServiceInterruption(doc):
                raise Exception('Document %d could not be retrieved.' %
                        nextDocIndex)
            gotAnyDoc = True
            yield doc
        except Exception, e:
            print >> stderr, str(e)
            if gotAnyDoc or (maxFailures == 0):
                break
            maxFailures -= 1
        nextDocIndex += 1

def logOut():
    global loggedIn, docsListHit
    loggedIn = False
    docsListHit = False
    urlopen(LOGOUT_URL).read()

