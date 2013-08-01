from mechanize import urlopen, Request, ParseResponse, ParseFile
from urllib import urlencode
from StringIO import StringIO
from BeautifulSoup import BeautifulSoup as RealBeautifulSoup
from sys import stdin, stderr
from getpass import getpass
from re import compile
from urlparse import parse_qs, urljoin, urlparse, urlunparse
from datetime import date
from dateutil.relativedelta import relativedelta

loggedIn = False
docsListHit = False

HOMEPAGE_URL = 'https://www.halifax-online.co.uk'
HOMEPAGE_TITLE = 'Welcome to Online Banking'
MEMORABLE_INFO_FORM_TITLE = 'Halifax - Enter Memorable Information'
EXPORT_FORM_URL = ('https://secure.halifax-online.co.uk'
                   '/personal/a/viewproductdetails'
                   '/m44_exportstatement.jsp')
EXPORT_FORM_TITLE = 'Halifax - Export Statement'
LOGOUT_URL = ('https://secure.halifax-online.co.uk'
              '/personal/a/viewaccount/accountoverviewpersonalbase.jsp'
              '?lnkcmd=lnkCustomerLogoff')

def customizeUserAgent():
    import mechanize
    cookies = mechanize.CookieJar()
    opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cookies))
    # Pretend to be Chrome to avoid getting the mobile site.
    opener.addheaders = [("User-agent", "Chrome/16.0.912.63")]
    mechanize.install_opener(opener)

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
    errors = (soup.findAll(id='AdditionalInfo') or
              soup.findAll(id='frmErrorPageLoggedIn'))
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
    memInfoFmt = ('frmentermemorableinformation1:'
                  'strEnterMemorableInformation_memInfo%d')

    def __init__(self, httpResponse):
        pageText = httpResponse.read()
        soup = BeautifulSoup(pageText)

        checkForErrors(soup)
        checkPageTitle(soup, MEMORABLE_INFO_FORM_TITLE)

        expr = compile('Character ([0-9]+).*')

        self.memorableInfoIndices = [
            int(expr.match(soup
                .find('label', attrs={ 'for': self.memInfoFmt % i })
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
            f = self.form.find_control(type='select', name=self.memInfoFmt % i)
            try:
                f.value = (['&nbsp;%s' %v])
            except:
                print f.possible_items()
                print f.value
                raise

    def submissionRequest(self):
        return self.form.click('frmentermemorableinformation1:btnContinue')

def chooseCurrentAccount(landingPageResponse):
    landingPageText = landingPageResponse.read()
    landingPage = BeautifulSoup(landingPageText)
    checkForErrors(landingPage)
    accountUrl = landingPage.form.find(text='Reward Current Account').parent['href']
    chooseAccountUrl = urljoin(landingPageResponse.geturl(), accountUrl)

    nextPage = BeautifulSoup(urlopen(chooseAccountUrl).read())
    checkForErrors(nextPage)

def logIn():
    customizeUserAgent()
    
    loginForm = LoginForm(urlopen(HOMEPAGE_URL))
    loginInfo = getLoginInfo()
    loginForm.populate(loginInfo)

    memorableInfoForm = MemorableInfoForm(urlopen(
        loginForm.submissionRequest()))
    memorableInfo = getMemorableInfo(memorableInfoForm.memorableInfoIndices)
    memorableInfoForm.populate(memorableInfo)

    chooseCurrentAccount(urlopen(memorableInfoForm.submissionRequest()))

    global loggedIn
    loggedIn = True

def exportMonth(exportDate, format='qif'):
    monthStart = date(exportDate.year, exportDate.month, 1)
    monthEnd = min(date.today(), monthStart + relativedelta(months=1, days=-1))
    
    httpResponse = urlopen(EXPORT_FORM_URL)
    responseText = httpResponse.read()
    soup = BeautifulSoup(responseText)
    checkForErrors(soup)

    form = ParseFile(StringIO(responseText),
                     httpResponse.geturl(),
                     backwards_compat=False)[0]
    
    form['frmTest:rdoDateRange'] = ['1']

    for (dn, d) in [('From', monthStart),
                    ('To', monthEnd)]:
        fn = 'frmTest:dtSearch%sDate' % dn
        form[fn           ] = ['%02d' % d.day]
        form[fn + '.month'] = ['%02d' % d.month]
        form[fn + '.year' ] = ['%04d' % d.year]

    formats = {
        'qif': 'Quicken 98 and 2000 and Money (.QIF)',
        'csv': 'Internet banking text/spreadsheet (.CSV)',
        }
    form['frmTest:strExportFormatSelected'] = [formats[format]]
    
    return form.click()

def genAllStatements(format='qif'):
    today = date.today()
    month = date(today.year, today.month, 1)
    while True:
        response = urlopen(exportMonth(month, format))
        yield month, response
        month = month + relativedelta(months=-1)

def logOut():
    global loggedIn
    loggedIn = False
    urlopen(LOGOUT_URL).read()

def test():
    logIn()
    try:
        print urlopen(exportMonth(date(2011,11,1))).read()
    finally:
        logOut()
