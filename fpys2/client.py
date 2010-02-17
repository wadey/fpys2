import base64
import hmac
import hashlib
import urllib, urllib2
import logging
import time
from datetime import datetime, tzinfo

try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

_log = logging.getLogger("fpys")

def _attr_name_from_tag(tag_name):
    # some tag names have an XML namespace that we
    # aren't really concerned with.  This strips them:
    tag_name = tag_name[tag_name.find("}")+1:]
    # Then we lowercase the first letter
    return tag_name[0].lower() + tag_name[1:]

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class AmazonError(Error):
    """Error returned by amazon"""
    
    def __init__(self, response):
        if isinstance(response.errors, list):
            Error.__init__(self, "%s: %s" % (response.errors[0].errorCode, response.errors[0].reasonText))
        else:
            Error.__init__(self, "%s: %s" % (response.errors.error.code, response.errors.error.message))
        self.response = response

class FPSResponse(object):
    def __init__(self, element=None):
        if element is not None:
            if isinstance(element, str):
                element = ET.fromstring(element)
        self.element = element

        for child in element.getchildren():
            if len(child.getchildren()) ==0:
                value = child.text
                if child.tag.find("Date") >= 0:
                    # TODO this is a little less than ideal
                    # we truncate the milliseconds and time zone info
                    value = value[0:value.find(".")]
                    value = datetime.strptime(value,
                                             "%Y-%m-%dT%H:%M:%S")
                if child.tag == "Amount":
                    value = float(child.text)
                if child.tag.find("Size") >= 0:
                    value = int(child.text)
                setattr(self, _attr_name_from_tag(child.tag), value)
            else:
                if child.tag == "Errors" and child.getchildren()[0].tag == "Errors":
                    self.errors = []
                    for e in child.getchildren():
                        self.errors.append(FPSResponse(e))
                elif child.tag =="Transactions":
                    if not hasattr(self, "transactions"):
                        self.transactions = []
                    self.transactions.append(FPSResponse(child))
                else:
                    setattr(self, _attr_name_from_tag(child.tag), FPSResponse(child))

        if hasattr(self, "status"):
            self.success = (self.status == "Success")
        if hasattr(self, "transactionResponse"):
            setattr(self, "transaction", self.transactionResponse)
            delattr(self, "transactionResponse")
        
        if hasattr(self, "errors"):
            raise AmazonError(self)

class FlexiblePaymentClient(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, 
                 fps_url="https://fps.sandbox.amazonaws.com",
                 pipeline_url="https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start"):
        self.access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.fps_url = fps_url
        self.fps_host = fps_url.split("://")[1].split("/")[0]
        self.pipeline_url = pipeline_url
        self.pipeline_path = pipeline_url.split("amazon.com")[1]
        self.pipeline_host = pipeline_url.split("://")[1].split("/")[0]

    def sign_string(self, string, hashfunc):
        """
        Strings going to and from the Amazon FPS service must be cryptographically
        signed to validate the identity of the caller.

        Sign the given string with the aws_secret_access_key using the SHA1 algorithm,
        Base64 encode the result and strip whitespace.
        """
        _log.debug("to sign: %s" % string)
        sig = base64.encodestring(hmac.new(self.aws_secret_access_key, 
                                           string, 
                                           hashfunc).digest()).strip()
        _log.debug(sig)
        return(sig)

    def get_signature(self, parameters, path=None, http_verb='GET', http_host=None, hashfunc=hashlib.sha256):
        """
        Returns the signature for the Amazon FPS Pipeline request that will be
        made with the given parameters.  Pipeline signatures are calculated with
        a different algorithm from the REST interface.  Names and values are
        url encoded and separated with an equal sign, unlike the REST 
        signature calculation.
        """
        if path is None:
            path = self.pipeline_path
        if http_host is None:
            http_host = self.pipeline_host

        keys = parameters.keys()
        keys.sort()

        parameters_string = "&".join(["%s=%s" % (urllib.quote(k), urllib.quote(str(parameters[k])).replace("/", "%2F")) for k in keys])
        signature_base_string = "\n".join([http_verb, http_host, path, parameters_string])
        _log.debug(signature_base_string)
        return self.sign_string(signature_base_string, hashfunc)

    def execute(self, parameters, sign=True):
        """
        A generic call to the FPS service.  The parameters dictionary
        is sorted, signed, and turned into a valid FPS REST call.  
        The response is read via urllib2 and parsed into an FPSResponse object
        """

        # Throw out parameters that == None
        parameters = dict([(k,v) for k,v in parameters.items() if v != None])

        parameters['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        parameters['Version'] = '2008-09-17'

        if sign:
            parameters['AWSAccessKeyId'] = self.access_key_id
            parameters['SignatureVersion'] = 2
            parameters['SignatureMethod'] = 'HmacSHA256'
            parameters['Signature'] = self.get_signature(parameters, path='/', http_host=self.fps_host)
        
        query_str = urllib.urlencode(parameters)
        _log.debug("request_url == %s/?%s" % (self.fps_url, query_str))

        data = None
        try:
            response = urllib2.urlopen("%s/?%s" % (self.fps_url, query_str))
            data = response.read()
            response.close()
        except urllib2.HTTPError, httperror:
            data = httperror.read()
            httperror.close()

        return FPSResponse(ET.fromstring(data))
    
    def cancel(self, transaction_id, description=None):
        params = {'Action': 'Cancel',
                  'TransactionId': transaction_id,
                  'Description': description}
        return self.execute(params)
    
    def cancel_token(self, token_id, reason=None):
        params = {'Action': 'CancelToken',
                  'TokenId': token_id,
                  'ReasonText': reason}
        return self.execute(params)
    
    def get_receipient_verification_status(self, token_id):
        params = {'Action': 'GetReceipientVerificationStatus',
                  'RecipientTokenID': token_id}
        return self.execute(params)
    
    def get_transaction_status(self, transaction_id):
        params = {'Action': 'GetTransactionStatus',
                  'TransactionId': transaction_id}
        return self.execute(params)
    
    def get_pipeline_url(self, 
                       caller_reference, 
                       payment_reason, 
                       transaction_amount, 
                       return_url, 
                       pipeline_name="SingleUse", 
                       recurring_period=None
                       ):
        """Gets the URL for making a co-branded service request, like in this Java
        code:
        http://docs.amazonwebservices.com/AmazonFPS/latest/FPSGettingStartedGuide/index.html?gsMakingCoBrandedUIRequests.html#d0e1242
        """
        parameters = {'callerReference': caller_reference,
                      'paymentReason': payment_reason,
                      'transactionAmount': transaction_amount,
                      'callerKey': self.access_key_id,
                      'pipelineName': pipeline_name,
                      'returnURL': return_url,
                      'signatureVersion': 2,
                      'signatureMethod': 'HmacSHA256'
                      }

        if recurring_period is not None:
            parameters['recurringPeriod'] = recurring_period
        parameters['signature'] = self.get_signature(parameters)
        query_string = urllib.urlencode(parameters)
        url = "%s?%s" % (self.pipeline_url, query_string)
        _log.debug(url)
        return url

    def get_token_by_caller(self, token_id=None, caller_reference=None):
        params = {'Action': 'GetTokenByCaller',
                  'CallerReference': caller_reference,
                  'TokenId': token_id}
        return self.execute(params)

    def pay(self,
            sender_token,
            amount,
            caller_reference,
            recipient_token=None,
            caller_description = None,
            charge_fee_to='Recipient'):
        params = {'Action': 'Pay',
                  'SenderTokenId': sender_token,
                  'RecipientTokenId': recipient_token,
                  'TransactionAmount.Value': amount,
                  'TransactionAmount.CurrencyCode': 'USD',
                  'CallerReference': caller_reference,
                  'CallerDescription': caller_description,
                  'ChargeFeeTo': charge_fee_to,
            }

        return self.execute(params)

    def refund(self,
               transaction_id,
               caller_reference,
               refund_amount=None,
               caller_description=None,
               ):
        params = {'Action': 'Refund',
                  'TransactionId': transaction_id,
                  'CallerReference': caller_reference,
                  'CallerDescription': caller_description,
                  'RefundAmount.Value': refund_amount,
                  'RefundAmount.CurrencyCode': (refund_amount and "USD")}
        return self.execute(params)

    def reserve(self,
                sender_token,
                amount,
                caller_reference,
                caller_description=None):
        params = {'Action': 'Reserve',
                  'SenderTokenId': sender_token,
                  'TransactionAmount.Value': amount,
                  'TransactionAmount.CurrencyCode': 'USD',
                  'CallerReference': caller_reference,
                  'CallerDescription': caller_description
                  }

        return self.execute(params)

    def settle(self,
               transaction_id,
               amount=None):
        params = {'Action': 'Settle',
                  'ReserveTransactionId': transaction_id,
                  'TransactionAmount.Value': amount,
                  'TransactionAmount.CurrencyCode': (amount and 'USD')}

        return self.execute(params)
    
    def verify_signature(self,
                        url_endpoint,
                        http_parameters):
        params = {'Action': 'VerifySignature',
                  'UrlEndPoint': url_endpoint,
                  'HttpParameters': http_parameters}
        return self.execute(params, sign=False)