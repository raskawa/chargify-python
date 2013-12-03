try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        raise EnvironmentError("You must have a JSON module installed such as simplejson")
import urllib
import urllib2
import base64

# Define all exceptions
# Corresponds to HTTP response codes specified here:
# http://support.chargify.com/faqs/api/api-user-guide
class ChargifyError(Exception):
    def __init__(self, error_data=None, *a, **kw):
        self.error_data = error_data or {}
        super(ChargifyError, self).__init__(*a, **kw)

class ChargifyConnectionError(ChargifyError):pass
class ChargifyUnauthorizedError(ChargifyError):pass
class ChargifyForbiddenError(ChargifyError):pass
class ChargifyNotFoundError(ChargifyError):pass
class ChargifyUnprocessableEntityError(ChargifyError):pass
class ChargifyServerError(ChargifyError):pass

ERROR_CODES = {
    201: False,
    401: ChargifyUnauthorizedError,
    403: ChargifyForbiddenError,
    404: ChargifyNotFoundError,
    422: ChargifyUnprocessableEntityError,
    500: ChargifyServerError,
}

# Maps certain function names to HTTP verbs
VERBS = {
    'create':'POST',
    'read':'GET',
    'update':'PUT',
    'delete':'DELETE'
}

# A list of identifiers that should be extracted and placed into the url string if they are
# passed into the kwargs.
IDENTIFIERS = {
    'customer_id':'management_link',
    'customer_id':'customers',
    'product_id':'products',
    'subscription_id':'subscriptions',
    'component_id':'components',
    'handle':'handle',
    'statement_id':'statements',
    'product_family_id':'product_families',
    'coupon_id':'coupons',
    'transaction_id':'transactions',
    'usage_id':'usages',
    'migration_id':'migrations',
}

class ChargifyHttpClient(object):
    """
    Extracted from the main Chargify class so it can be stubbed out during testing.
    """

    def make_request(self, url, method, data, api_key):
        """
        Actually responsible for making the HTTP request.
        :param url: The URL to load.
        :param method: The HTTP method to use.
        :param data: Any POST data that should be included with the request.
        """
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url=url, data=data)

        # Build header
        request.get_method = lambda: method
        request.add_header('Authorization', 'Basic %s' % base64.encodestring('%s:%s' % (api_key, 'x'))[:-1])
        request.add_header('User-Agent', 'Chargify Python Client')
        request.add_header('Accept', 'application/json')
        request.add_header('Content-Type', 'application/json')
        if data is None:
            request.add_header('Content-Length','0')

        # Make request and trap for HTTP errors
        try:
            response = opener.open(request)
        except urllib2.HTTPError, e:
            response = e
        except urllib2.URLError, e:
            raise ChargifyConnectionError(e)

        result = response.read()

        try:
            data = json.loads(result)
        except ValueError:
            data = {'body': result} #Is not JSON

        if response.code in ERROR_CODES and ERROR_CODES[response.code] is not False:
            error_class = ERROR_CODES[e.code]
            raise error_class(data)

        return data

class Chargify(object):
    """
    A client for the Chargify API.
    """
    api_key = ''
    sub_domain = ''
    path = []
    domain = 'https://%s.chargify.com/'
    client = None

    def __init__(self, api_key, sub_domain, path=None, client=None):
        """
        :param api_key: The API key for your Chargify account.
        :param sub_domain: The sub domain of your Chargify account.
        :param path: The current path constructed for this request.
        :param client: The HTTP client to use to make the request.
        """
        self.api_key = api_key
        self.sub_domain = sub_domain
        self.path = path or []
        self.client = client or ChargifyHttpClient()

    def __getattr__(self, attr):
        """
        Uses attribute chaining to help construct the url path of the request.
        """
        try:
            return object.__getattr__(self, attr)
        except AttributeError:
            return Chargify(self.api_key, self.sub_domain, self.path + [attr], self.client)

    def construct_request(self, **kwargs):
        """
        :param kwargs: The arguments passed into the request. Valid values are:
            'customer_id', 'product_id', 'subscription_id', 'component_id', 'handle' will be extracted
            and placed into the url. 'data' will be serialized into a JSON string and POSTed with
            the request.
        """
        path = self.path[:]

        # Find the HTTP method if we were called with create(), update(), read(), or delete()
        if path[-1] in VERBS.keys():
            action = path.pop()
            method = VERBS[action]
        else:
            method = 'GET'

        # Extract certain kwargs and place them in the url instead
        for identifier, name in IDENTIFIERS.items():
            value = kwargs.pop(identifier, None)
            if value:

                path.insert(path.index(name)+1, str(value))

        # Convert the data to a JSON string
        data = kwargs.pop('data', None)
        if data:
            data = json.dumps(data)

        # Build query string
        get_params = kwargs.pop("get_params", {})
        if method == 'GET' and (kwargs or get_params):
            get_params.update(kwargs)
            args = "?%s" % (urllib.urlencode(get_params, True))
        else:
            args = ''

        # Build url
        url = self.domain % self.sub_domain
        url = url + '/'.join(path) + '.json' + args
        if "management_link" in url:
            url = url.replace("customers","portal/customers").replace(".json","")
        return url, method, data

    def __call__(self, **kwargs):
        url, method, data = self.construct_request(**kwargs)
        return self.client.make_request(url, method, data, self.api_key)
