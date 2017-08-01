#!/usr/bin/env python
"""
The Requester module is in charge of simplifying HTTP requests and
automatically log HTTP transactions by calling the DB module.
"""
import sys
import httplib
import logging
import urllib

from urllib3.poolmanager import PoolManager

from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import RequesterInterface
from framework.http import transaction
from framework.lib.general import *

# Intercept raw request trick from:
# http://stackoverflow.com/questions/6085709/get-headers-sent-in-urllib2-http-request
class MyHTTPConnection(httplib.HTTPConnection):
    def send(self, s):
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
        httplib.HTTPConnection.send(self, s)


class MyHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        try:
            return self.do_open(MyHTTPConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception:
            # Can't have OWTF crash due to a library exception -i.e. raise BadStatusLine(line)-
            return ''


class MyHTTPSConnection(httplib.HTTPSConnection):
    def send(self, s):
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
        httplib.HTTPSConnection.send(self, s)


class MyHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        try:
            return self.do_open(MyHTTPSConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception:
            # Can't have OWTF crash due to a library exception -i.e. raise BadStatusLine(line)-.
            return ''


# SmartRedirectHandler is courtesy of:
# http://www.diveintopython.net/http_web_services/redirects.html
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result


class Requester(BaseComponent, RequesterInterface):
    COMPONENT_NAME = "requester"

    def __init__(self, proxy):
        self.register_in_service_locator()
        self.db_config = self.get_component("db_config")
        self.target = self.get_component("target")
        self.transaction = self.get_component("transaction")
        self.url_manager = self.get_component("url_manager")
        self.error_handler = self.get_component("error_handler")
        self.plugin_handler = self.get_component("plugin_handler")
        self.timer = self.get_component("timer")
        self.http_transaction = None
        self.Headers = {'User-Agent': self.db_config.Get('USER_AGENT')}
        self.request_count_refused = 0
        self.request_count_total = 0
        self.log_transactions = False
        self.proxy = proxy
        if proxy is None:
            logging.debug(
                "WARNING: No outbound proxy selected. It is recommended to "
                "use an outbound proxy for tactical fuzzing later")
            # FIXME: "Smart" redirect handler not really working.
            self.Opener = urllib2.build_opener(MyHTTPHandler, MyHTTPSHandler, SmartRedirectHandler)
        else:  # All requests must use the outbound proxy.
            logging.debug("Setting up proxy(inbound) for OWTF requests..")
            ip, port = proxy
            proxy_conf = {'http': 'http://%s:%s' % (ip, port), 'https': 'http://%s:%s' % (ip, port)}
            proxy_handler = urllib2.ProxyHandler(proxy_conf)
            # FIXME: Works except no raw request on https.
            self.Opener = urllib2.build_opener(proxy_handler, MyHTTPHandler, MyHTTPSHandler, SmartRedirectHandler)
        urllib2.install_opener(self.Opener)

    def log_transactions(self, log_transactions=True):
        backup = self.log_transactions
        self.log_transactions = log_transactions
        return backup

    def ask_before_request(self):
        return not self.plugin_handler.NormalRequestsAllowed()

    def is_transaction_added(self, url):
        return self.transaction.is_transaction_added({'url': url.strip()})

    def is_request_possible(self):
        return self.plugin_handler.RequestsPossible()

    def proxy_check(self):
        # Verify proxy works! www.google.com might not work in a restricted network, try target URL :)
        if self.proxy is not None and self.is_request_possible():
            url = self.db_config.Get('PROXY_CHECK_URL')
            refused_before = self.request_count_refused
            cprint("Proxy Check: Avoid logging request again if already in DB..")
            log_setting_backup = False
            if self.is_transaction_added(url):
                log_setting_backup = self.log_transactions(False)
            if log_setting_backup:
                self.log_transactions(log_setting_backup)
            refused_after = self.request_count_refused
            if refused_before < refused_after:  # Proxy is refusing connections.
                return [False, "ERROR: Proxy Check error: The proxy is not listening or is refusing connections"]
            else:
                return [True, "Proxy Check OK: The proxy appears to be working"]
        return [True, "Proxy Check OK: No proxy is setup or no HTTP requests will be made"]

    def get_headers(self):
        return self.Headers

    def set_headers(self, headers):
        self.Headers = headers

    def set_header(self, header, value):
        self.Headers[header] = value

    def str_to_dict(self, string):
        dict = defaultdict(list)
        count = 0
        prev_item = ''
        for item in string.strip().split('='):
            if count % 2 == 1:  # Key.
                dict[prev_item] = item
            else:  # Value.
                dict[item] = ''
                prev_item = item
            count += 1
        return dict

    def post_to_str(self, post=None):
        post = self.derive_post(post)
        if post is None:
            return ''
        return post

    def derive_post(self, post=None):
        if '' == post:
            post = None
        if post is not None:
            if isinstance(post, str) or isinstance(post, unicode):
                # Must be a dictionary prior to urlencode.
                post = self.str_to_dict(post)
            post = urllib.urlencode(post)
        return post

    def perform_request(self, request):
        return urllib2.urlopen(request)

    def set_succesful_transaction(self, raw_request, response):
        return self.http_transaction.set_transaction(True, raw_request[0], response)

    def log_transaction(self):
        self.transaction.LogTransaction(self.http_transaction)

    def request(self, url, method=None, post=None):
        # kludge: necessary to get around urllib2 limitations: Need this to get the exact request that was sent.
        global raw_request
        url = str(url)

        raw_request = []  # Init Raw Request to blank list.
        post = self.derive_post(post)
        method = derive_http_method(method, post)
        url = url.strip()  # Clean up URL.
        request = urllib2.request(url, post, self.Headers)  # GET request.
        if method is not None:
            # kludge: necessary to do anything other that GET or POST with urllib2
            request.get_method = lambda: method
        # MUST create a new Transaction object each time so that lists of
        # transactions can be created and process at plugin-level
        # Pass the timer object to avoid instantiating each time.
        self.http_transaction = transaction.HTTPTransaction(self.timer)
        self.http_transaction.start(url, post, method, self.target.IsInScopeURL(url))
        self.request_count_total += 1
        try:
            response = self.perform_request(request)
            self.set_succesful_transaction(raw_request, response)
        except urllib2.HTTPError as Error:  # page NOT found.
            # Error is really a response for anything other than 200 OK in urllib2 :)
            self.http_transaction.set_transaction(False, raw_request[0], Error)
        except urllib2.URLError as Error:  # Connection refused?
            err_message = self.process_http_err_code(Error, url)
            self.http_transaction.set_error(err_message)
        except IOError:
            err_message = "ERROR: Requester Object -> Unknown HTTP Request error: %s\n%s" % (url, str(sys.exc_info()))
            self.http_transaction.set_error(err_message)
        if self.log_transactions:
            # Log transaction in DB for analysis later and return modified Transaction with ID.
            self.log_transaction()
        return self.http_transaction

    def process_http_err_code(self, error, url):
        message = ""
        if str(error.reason).startswith("[Errno 111]"):
            message = "ERROR: The connection was refused!: %s" % str(error)
            self.request_count_refused += 1
        elif str(error.reason).startswith("[Errno -2]"):
            self.error_handler.FrameworkAbort("ERROR: cannot resolve hostname!: %s" % str(error))
        else:
            message = "ERROR: The connection was not refused, unknown error!"
        log = logging.getLogger('general')
        log.info(message)
        return "%s (Requester Object): %s\n%s" % (message, url, str(sys.exc_info()))

    def get(self, url):
        return self.request(url)

    def post(self, url, data):
        return self.request(url, 'POST', data)

    def trace(self, url):
        return self.request(url, 'TRACE', None)

    def options(self, url):
        return self.request(url, 'OPTIONS', None)

    def head(self, url):
        return self.request(url, 'HEAD', None)

    def debug(self, url):
        self.backup_headers()
        self.Headers['Command'] = 'start-debug'
        result = self.request(url, 'DEBUG', None)
        self.restore_headers()
        return result

    def put(self, url, content_type='text/plain'):
        self.backup_headers()
        self.Headers['Content-Type'] = content_type
        self.Headers['Content-Length'] = "0"
        result = self.request(url, 'PUT', None)
        self.restore_headers()
        return result

    def backup_headers(self):
        self.HeadersBackup = dict.copy(self.Headers)

    def restore_headers(self):
        self.Headers = dict.copy(self.HeadersBackup)

    def get_transaction(self, use_cache, url, method=None, data=None):
        criteria = {'url': url.strip()}
        if method is not None:
            criteria['method'] = method
        # Must clean-up data to ensure match is found.
        if data is not None:
            criteria['data'] = self.post_to_str(data)
        # Visit URL if not already visited.
        if (not use_cache or not self.transaction.is_transaction_added(criteria)):
            if method in ['', 'GET', 'POST', 'HEAD', 'TRACE', 'OPTIONS']:
                return self.request(url, method, data)
            elif method == 'DEBUG':
                return self.debug(url)
            elif method == 'PUT':
                return self.put(url, data)
        else:  # Retrieve from DB = faster.
            # Important since there is no transaction ID with transactions objects created by Requester.
            return self.transaction.GetFirst(criteria)

    def get_transactions(self, use_cache, url_list, method=None, data=None, unique=True):
        transactions = []
        if unique:
            url_list = set(url_list)
        for url in url_list:
            url = url.strip()  # Clean up the URL first.
            if not url:
                continue  # Skip blank lines.
            if not self.url_manager.IsURL(url):
                self.error_handler.Add("Minor issue: %s is not a valid URL and has been ignored, processing continues" %
                                       str(url))
                continue  # Skip garbage URLs.
            transaction = self.get_transaction(use_cache, url, method=method, data=data)
            if transaction is not None:
                transactions.append(transaction)
        return transactions
