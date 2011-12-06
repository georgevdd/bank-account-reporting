from mechanize import urlopen, Request, ParseResponse, ParseFile
from urllib import urlencode
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup as RealBeautifulSoup
from sys import stdin, stderr
from getpass import getpass
from re import compile
from urlparse import urljoin

loggedIn = False
docsListHit = False

HOMEPAGE_URL = 'http://www.halifax-online.co.uk'
HOMEPAGE_TITLE = 'Welcome to Online Banking'
MEMORABLE_INFO_FORM_TITLE = 'Halifax - Enter Memorable Information'
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

def checkPageText(soup, element, expectedText):
    text = element.contents[0].strip()
    if expectedText != text:
        global errorSoup
        errorSoup = soup
        raise Exception('Text was "%s", not "%s"' % (text, expectedText))

def checkPageTitle(soup, expectedTitle):
    checkPageText(soup, soup.title, expectedTitle)

def checkPageH1(soup, expectedHeading):
    checkPageText(soup, soup.h1, expectedHeading)

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

def BeautifulSoup(html, *args, **kwargs):
    '''See http://mail.python.org/pipermail/python-bugs-list/2007-February/037082.html'''
    return RealBeautifulSoup(html.replace('&#', 'xx'), *args, **kwargs)

class LoginForm(object):
    def __init__(self, httpResponse):
        responseText = httpResponse.read()
        soup = BeautifulSoup(responseText)

        checkPageH1(soup, HOMEPAGE_TITLE)

        forms = ParseFile(StringIO(responseText),
                          httpResponse.geturl(),
                          backwards_compat=False)
        self.form = forms[0]

    def populate(self, loginInfo):
        self.form['frmLogin:strCustomerLogin_userID'] = loginInfo.username
        self.form['frmLogin:strCustomerLogin_pwd'] = loginInfo.password

    def submissionRequest(self):
        return self.form.click('frmLogin:btnLogin1')

class MemorableInfoForm(object):
    def __init__(self, httpResponse):
        pageText = httpResponse.read()
        soup = BeautifulSoup(pageText)

        checkForErrors(soup)
        checkPageTitle(soup, MEMORABLE_INFO_FORM_TITLE)

        expr = compile('Character ([0-9]+).*')

        self.memorableInfoIndices = [
            int(expr.match(soup
                .find('label', attrs={ 'for': 'frmentermemorableinformation1:strEnterMemorableInformation_memInfo%d' % i })
                .contents[0]).group(1))
            for i in range(1, 4)]

        forms = ParseFile(StringIO(pageText),
                          httpResponse.geturl(),
                          backwards_compat=False)
        self.form = forms[0]

    def populate(self, memorableInfoCharacters):
        if len(memorableInfoCharacters) != 3:
            raise ValueError('Expected three memorable info characters.')

        for i, v in zip(range(1, 4), memorableInfoCharacters.lower()):
            f = self.form.find_control(
                type='select',
                name='frmentermemorableinformation1:strEnterMemorableInformation_memInfo%d' % i)
            try:
                f.value = (['&nbsp;%s' %v])
            except:
                print f.possible_items()
                print f.value
                raise

    def submissionRequest(self):
        return self.form.click('frmentermemorableinformation1:btnContinue')

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

