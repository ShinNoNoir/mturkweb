import sys
import mechanize
from bs4 import BeautifulSoup
from urllib import urlencode

DEBUG = False

BATCH_STATUSES = '''
batches_in_progress
batches_reviewable
batches_reviewed
'''.split()

LOGIN_URL = 'https://requester.mturk.com/begin_signin'
LOGIN_SUCCESS_URL = 'https://requester.mturk.com'
LOGIN_NOT_A_REQUESTER_URL_PREFIX = 'https://requester.mturk.com/mturk/register'
COOKIE_DOMAIN = 'requester.mturk.com'
MANAGE_URL = 'https://requester.mturk.com/batches.js'
MANAGE_PARAMS = {
    'direction': 'DESC',
    'order': 'Creation Date',
    'page': None,
    'status': None
}
TRANSACTION_URL = 'https://requester.mturk.com/mturk/transactionhistory'
TRANSACTION_PARAMS = {'fromMonth': 1,
                      'fromDay': 1,
                      'fromYear': None,
                      'toMonth': 1,
                      'toDay': 1,
                      'toYear': None,
                      'transactionDownload.x': 1,
                      'transactionDownload.y': 1,
                      'sortType': 'DATE_DESCENDING'}
UA_STRING = 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'

def login(email, password):
    """Login to Mechanical Turk with an Amazon account.
    
    Args:
        email: The e-mail address (str) associated with the Amazon account.
        password: The password (str) of the Amazon account.
    
    Returns:
        An MTurkWebSession instance if login was successful.
    
    Raises:
        ValueError: Wrong email/password.
        ValueError: Not an MTurk Requester account.
    """
    br = mechanize.Browser()
    cj = mechanize.CookieJar()
    br.addheaders = [('User-agent', UA_STRING)]
    br.set_cookiejar(cj)
    br.set_handle_robots(False)
    br.open(LOGIN_URL)
    br.select_form(nr = 0)
    br.form['email'] = email
    br.form['password'] = password
    response = br.submit()
    
    response_url = response.geturl()
    if response_url.rstrip('/') == LOGIN_SUCCESS_URL:
        assert cookiejar_has_requester_state(cj), \
            'A successful login should set requester_state cookie'
        return MTurkWebSession(br, cj)
    elif response_url.startswith(LOGIN_NOT_A_REQUESTER_URL_PREFIX):
        raise ValueError('Not an MTurk Requester account')
    else:
        msg = 'Wrong email/password'
        if DEBUG:
            msg += ': ' + response_url
        raise ValueError(msg)


def cookiejar_has_requester_state(cookiejar):
    """Returns True iff a non-empty requester_state cookie has been set.
    
    Args:
        cookiejar: A CookieJar that will be searched.
    Returns:
        True iff the given cookie jar contains a non-empty requeste_state cookie.
    """
    for cookie in cookiejar:
        if cookie.name == 'requester_state' and cookie.domain == COOKIE_DOMAIN:
            return cookie.value != ''
    return False


class MTurkWebSession:
    """Represents a session on the Mechanical Turk website.
    
    Do not create instances of this class yourself,
    but use the `login()` function instead.
    """
    def __init__(self, browser, cookiejar):
        """Constructs an MTurkWebSession instance."""
        self.browser = browser
        self.cookiejar = cookiejar    
        
        assert browser._ua_handlers['_cookies'].cookiejar == cookiejar, \
            'Given CookieJar should be used by the given Browser instance'
        assert cookiejar_has_requester_state(cookiejar), \
            'Given CookieJar should contain a non-empty request_state cookie'
    
    def _retrieve_batch_page(self, batch_status, page=1):
        """Retrieves batches with the given status from a given page.
        
        Args:
            batch_status: One of BATCH_STATUSES.
            page: The Mechanical Turk batch page (int) to scrape from.
        
        Returns:
            A tuple consisting of a list of batches and the next page from 
            which scraping could resume. If there are no more pages to scrape
            from, the next page is None.
        """
        br = self.browser
        params = dict(MANAGE_PARAMS, status=batch_status, page=page)
        url = '%s?%s' % (MANAGE_URL, urlencode(params))
        
        if DEBUG:
            print >>sys.stderr, '*** _retrieve_batch_page(%s, %s)' % (batch_status, page)
        
        response = br.open(url)
        soup = BeautifulSoup(response.read())
        pagination = soup.find(attrs={'class': 'pagination'})
        page_links = set( int(a.string) for a in pagination.find_all('a') if a.string.isdigit() ) \
                     if pagination is not None else set()
        
        next_page = page+1 if (page+1) in page_links else None
        
        DIV_ID_PREFIX = 'batch_capsule_'
        batches = []
        for batch_capsule in soup.find_all(id=lambda x: x and x.startswith(DIV_ID_PREFIX)):
            batch_id = int(batch_capsule.attrs['id'][len(DIV_ID_PREFIX):])
            batch_link_tag = batch_capsule.find('a', id='batch_status_%s' % batch_id)
            batch_name = batch_link_tag.string
            tbl = batch_capsule.find(id="batch_%s" % batch_id)
            metadata = [line for line in tbl.text.splitlines() if line.strip()]
            
            batches.append( Batch(batch_id, batch_name, metadata) )
        
        return batches, next_page
    
    def get_batches(self):
        """
        Retrieves all the batches available for this session.
        
        Returns:
            A dict mapping batch statuses to the corresponding batches with 
            that status.
        """
        res = {}
        for status in BATCH_STATUSES:
            all_batches = []
            res[status] = all_batches
            
            page = 1
            while page is not None:
                batches, page = self._retrieve_batch_page(status, page)
                all_batches.extend(batches)
        
        return res
    
    def get_transaction_history_csv(self, year):
        """
        Retrieves the transaction history for a specific year.
        
        Args:
            year: The year for which to get the transaction history.
            
        Returns:
            A string containing the transaction history in CSV format
        """
        
        br = self.browser
        params = dict(TRANSACTION_PARAMS, fromYear=year, toYear=year+1)
        url = '%s?%s' % (TRANSACTION_URL, urlencode(params))
        response = br.open(url).read()
        
        soup = BeautifulSoup(response)
        error = soup.find(attrs={'class': 'message error'})
        if error:
            error_msgs = [msg for msg in error.find(id='alertboxMessage')]
            raise ValueError(error_msgs[0].strip())
        return response

class Batch:
    """Represents a Mechanical Turk Batch.
    
    Attributes:
        id: The identifier (int) of this batch.
        name: The name (str) of this batch.
    """
    
    def __init__(self, id, name, metadata=None):
        """Constructs a Batch instance.
        
        Args:
            id: The identifier (id) of this batch.
            name: The name of this batch.
            metadata: Any metadata (exact format is TBD).
        """
        self.id = id
        self.name = name
        self.metadata = metadata
    
    def geturl(self):
        """Returns a URL corresponding to this batch."""
        return 'https://requester.mturk.com/batches/%s/' % self.id
