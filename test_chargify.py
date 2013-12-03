import unittest
from chargify import Chargify

class ChargifyHttpClientStub(object):
    
    def make_request(self, url, method, data, api_key):
        return url, method, data
        
class ChargifyTestCase(unittest.TestCase):
    
    def setUp(self):
        subdomain = 'subdomain'
        self.chargify = Chargify('api_key', subdomain, client=ChargifyHttpClientStub())
        self.host = 'https://%s.chargify.com' % subdomain
        
    def assertResult(self, result, expected_url, expected_method, expected_data):
        """
        A little helper method to help verify that the correct URL, HTTP method, and POST data are
        being constructed from the Chargify API.
        """
        url, method, data = result
        self.assertEqual(url, '%s%s' % (self.host, expected_url))
        self.assertEqual(method, expected_method)
        self.assertEqual(data, expected_data)
        
class TestCustomers(ChargifyTestCase):
    
    def test_construct_request(self):
        # List
        result = self.chargify.customers()
        self.assertResult(result, '/customers.json', 'GET', None)

        # Read/show (via chargify id)
        result = self.chargify.customers(customer_id=123)
        self.assertResult(result, '/customers/123.json', 'GET', None)
        
        # Read/show (via reference value)
        result = self.chargify.customers.lookup(reference=123)
        self.assertResult(result, '/customers/lookup.json?reference=123', 'GET', None)
        
        # Create
        result = self.chargify.customers.create(data={
            'customer':{
                'first_name':'Joe',
                'last_name':'Blow',
                'email':'joe@example.com'
            }
        })
        self.assertResult(result, '/customers.json', 'POST',
            '{"customer": {"first_name": "Joe", "last_name": "Blow", "email": "joe@example.com"}}')
            
        # Edit/update
        result = self.chargify.customers.update(customer_id=123, data={
            'customer':{
                'email':'joe@example.com'
            }
        })
        self.assertResult(result, '/customers/123.json', 'PUT',
            '{"customer": {"email": "joe@example.com"}}')
        
        # Delete
        result = self.chargify.customers.delete(customer_id=123)
        self.assertResult(result, '/customers/123.json', 'DELETE', None)

class TestManagementURL(ChargifyTestCase):

    def test_construct_request(self):
        # Get customer specific management link for billing portal
        result = self.chargify.customers.management_link.read(customer_id=123)
        self.assertResult(result, '/portal/customers/123/management_link', 'GET', None)

class TestProducts(ChargifyTestCase):
    
    def test_construct_request(self):
        # List
        result = self.chargify.products()
        self.assertResult(result, '/products.json', 'GET', None)
        
        # Read/show (via chargify id)
        result = self.chargify.products(product_id=123)
        self.assertResult(result, '/products/123.json', 'GET', None)
        
        # Read/show (via api handle)
        result = self.chargify.products.handle(handle='myhandle')
        self.assertResult(result, '/products/handle/myhandle.json', 'GET', None)

class TestSubscriptions(ChargifyTestCase):
    
    def test_construct_request(self):
        # List
        result = self.chargify.customers.subscriptions(customer_id=123)
        self.assertResult(result, '/customers/123/subscriptions.json', 'GET', None)
        
        # Read
        result = self.chargify.subscriptions(subscription_id=123)
        self.assertResult(result, '/subscriptions/123.json', 'GET', None)
        
        # Create
        result = self.chargify.subscriptions.create(data={
            'subscription':{
                'product_handle':'my_product',
                'customer_attributes':{
                    'first_name':'Joe',
                    'last_name':'Blow',
                    'email':'joe@example.com'
                },
                'credit_card_attributes':{
                    'full_number':'1',
                    'expiration_month':'10',
                    'expiration_year':'2020'
                }
            }
        })
        self.assertResult(result, '/subscriptions.json', 'POST',
            '{"subscription": {"product_handle": "my_product", "credit_card_attributes": {"expiration_month": "10", "full_number": "1", "expiration_year": "2020"}, "customer_attributes": {"first_name": "Joe", "last_name": "Blow", "email": "joe@example.com"}}}')
            
        # Update
        result = self.chargify.subscriptions.update(subscription_id=123, data={
            'subscription':{
                'credit_card_attributes':{
                    'full_number':'2',
                    'expiration_month':'10',
                    'expiration_year':'2030'
                }
            }
        })
        self.assertResult(result, '/subscriptions/123.json', 'PUT',
            '{"subscription": {"credit_card_attributes": {"expiration_month": "10", "full_number": "2", "expiration_year": "2030"}}}')
        
        # Delete
        result = self.chargify.subscriptions.delete(subscription_id=123, data={
            'subscription':{
                'cancellation_message':'Goodbye!'
            }
        })
        self.assertResult(result, '/subscriptions/123.json', 'DELETE',
            '{"subscription": {"cancellation_message": "Goodbye!"}}')

class TestCharges(ChargifyTestCase):
    
    def test_construct_request(self):
        # Create
        result = self.chargify.subscriptions.charges.create(subscription_id=123, data={
            'charge':{
                'amount':'1.00',
                'memo':'This is the description of the one time charge.'
            }
        })
        self.assertResult(result, '/subscriptions/123/charges.json', 'POST',
            '{"charge": {"amount": "1.00", "memo": "This is the description of the one time charge."}}')

class TestComponents(ChargifyTestCase):
    
    def test_construct_request(self):
        # List
        result = self.chargify.subscriptions.components.usages(subscription_id=123, component_id=456)
        self.assertResult(result, '/subscriptions/123/components/456/usages.json', 'GET', None)
   
        # Create
        result = self.chargify.subscriptions.components.usages.create(subscription_id=123, component_id=456, data={
            'usage':{
                'quantity':5,
                'memo':'My memo'
            }
        })
        self.assertResult(result, '/subscriptions/123/components/456/usages.json', 'POST',
            '{"usage": {"memo": "My memo", "quantity": 5}}')

class TestMigrations(ChargifyTestCase):
    
    def test_construct_request(self):
        # Create
        result = self.chargify.subscriptions.migrations.create(subscription_id=123, data={
            'product_id':1234
        })
        self.assertResult(result, '/subscriptions/123/migrations.json', 'POST',
            '{"product_id": 1234}')

class TestReactivate(ChargifyTestCase):
    
    def test_construct_request(self):
        # Reactivate
        result = self.chargify.subscriptions.reactivate.update(subscription_id=123)
        self.assertResult(result, '/subscriptions/123/reactivate.json', 'PUT', None)

class TestTransactions(ChargifyTestCase):
    
    def test_construct_request(self):
        # List transactions for a site
        result = self.chargify.transactions()
        self.assertResult(result, '/transactions.json', 'GET', None)
        
        # List transactions for a subscription
        result = self.chargify.subscriptions.transactions(subscription_id=123)
        self.assertResult(result, '/subscriptions/123/transactions.json', 'GET', None)


def suite():
    """Creates a unittest TestSuite for use with setuptools"""
    test_suite = unittest.TestSuite()
    for test_case in (TestCustomers, TestProducts, TestSubscriptions, \
                      TestCharges, TestComponents, TestMigrations, \
                      TestReactivate, TestTransactions):
        test_suite.addTest(unittest.makeSuite(test_case))
    return test_suite
        
            
if __name__ == "__main__":
    unittest.main(defaultTest='suite')