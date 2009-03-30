from mechanize import urlopen, Request
from urllib import urlencode
from ClientForm import ParseResponse, ParseFile
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup
from sys import stdin, stderr
from getpass import getpass
from urlparse import urljoin

loggedIn = False
docsListHit = False

HOMEPAGE_URL = 'http://www.halifax-online.co.uk'
HOMEPAGE_TITLE = 'Halifax - Welcome to Online'
DOCS_LIST_URL = ('https://online-documents.halifax-online.co.uk' +
    '/onlinedocuments/app/oddocuments.asp')
DOC_URL = ('https://online-documents.halifax-online.co.uk'+
        '/onlinedocuments/app/odviewdocument.asp')
LOGOUT_URL = 'https://www.halifax-online.co.uk/_mem_bin/SignOff.asp'

class LoginInfo(object):
    def __init__(self, username, password, securityAnswer):
        self.username = username
        self.password = password
        self.securityAnswer = securityAnswer


def getLoginInfo(question):
    return LoginInfo(getpass('Username: '), getpass(), getpass(question + ' '))

def checkPageTitle(soup, expectedTitle):
    title = soup.title.contents[0]
    if expectedTitle != title:
        raise Exception('Title was "%s", not "%s"' % (title, expectedTitle))

def doWithRetries(func, retries = 4, **kwargs):
    while (retries > 0):
        try:
            return func(**kwargs)
        except Exception, e:
            print "Exception %s - retrying %s" % (e, func.__name__)
        retries -= 1
    return func(**kwargs)

def getLoginForm():
    response = urlopen(HOMEPAGE_URL)
    responseText = response.read()
    
    soup = BeautifulSoup(responseText)
    checkPageTitle(soup, HOMEPAGE_TITLE)
    
    prompts = soup.findAll(name='td', attrs={'class':'bwLoginMCUser'})
    formSoup = soup.find("form", {"id" : "frmFormsLogin"})
    question = formSoup.find("input", {"name" : "answer", "class" : "LoginAnswer"})["alt"]
    if not question.endswith('?'):
        raise Exception('Found "%s" while trying to find question.')
    
    forms = ParseFile(StringIO(responseText), response.geturl(), 
            backwards_compat=False)
    form = forms[1]
    
    return form, question

def postLoginForm(form):
    homepageText = urlopen(form.click('btnContinue')).read()
    soup = BeautifulSoup(homepageText)
    errors = soup.findAll(attrs={'color':'red'})
    if errors:
        raise Exception(errors)

def logIn():
    form, question = doWithRetries(getLoginForm)
    
    loginInfo = getLoginInfo(question)

    form.find_control('JSEnabled').readonly = False
    form['JSEnabled'] = 'true'
    form['Username'] = loginInfo.username
    form['password'] = loginInfo.password
    form['answer'] = loginInfo.securityAnswer

    postLoginForm(form)
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

