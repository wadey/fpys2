import base64
import hmac
import sha
import urllib, urllib2
import logging
import time
from datetime import datetime, tzinfo

try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

log = logging.getLogger("fpys")

def upcase_compare(left, right):
    left = left.upper()
    right = right.upper()
    if(left < right):
        return -1
    elif(left > right):
        return 1
    return 0

def attr_name_from_tag(tag_name):
    # some tag names have an XML namespace that we
    # aren't really concerned with.  This strips them:
    tag_name = tag_name[tag_name.find("}")+1:]
    # Then we lowercase the first letter
    return tag_name[0].lower() + tag_name[1:]

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
                setattr(self, attr_name_from_tag(child.tag), value)
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
                    setattr(self, attr_name_from_tag(child.tag), FPSResponse(child))

        if hasattr(self, "status"):
            self.success = (self.status == "Success")
        if hasattr(self, "transactionResponse"):
            setattr(self, "transaction", self.transactionResponse)
            delattr(self, "transactionResponse")

class FlexiblePaymentClient(object):
    def __init__(self, aws_access_key_id, aws_secret_access_key, 
                 fps_url="https://fps.sandbox.amazonaws.com",
                 pipeline_url="https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start"):
        self.access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.fps_url = fps_url
        self.pipeline_url = pipeline_url
        self.pipeline_path = pipeline_url.split("amazon.com")[1]

    def sign_string(self, string):
        """
        Strings going to and from the Amazon FPS service must be cryptographically
        signed to validate the identity of the caller.

        Sign the given string with the aws_secret_access_key using the SHA1 algorithm,
        Base64 encode the result and strip whitespace.
        """
        log.debug("to sign: %s" % string)
        sig = base64.encodestring(hmac.new(self.aws_secret_access_key, 
                                           string, 
                                           sha).digest()).strip()
        log.debug(sig)
        return(sig)

    def get_pipeline_signature(self, parameters, path=None):
        """
        Returns the signature for the Amazon FPS Pipeline request that will be
        made with the given parameters.  Pipeline signatures are calculated with
        a different algorithm from the REST interface.  Names and values are
        url encoded and separated with an equal sign, unlike the REST 
        signature calculation.
        """
        if path is None:
            path = self.pipeline_path + "?"
        keys = parameters.keys()
        keys.sort(upcase_compare)
        
        to_sign = path
        for k in keys:
            to_sign += "%s=%s&" % (urllib.quote(k), urllib.quote(parameters[k]).replace("/", "%2F"))
        to_sign = to_sign[0:-1]
        log.debug(to_sign)
        return self.sign_string(to_sign)

    def validate_pipeline_signature(self, signature, path, parameters):
        """
        Generates a pipeline signature for the given parameters and compares
        it with the provided signature.  If an awsSignature parameter is provided,
        it is ignored.

        Returns True or False
        """
        if parameters.has_key('awsSignature'):
            del parameters['awsSignature']

        if signature == self.get_pipeline_signature(parameters, path):
            log.debug("checks out")
            return True
        log.debug("you fail")
        return False

    def get_signed_query(self, parameters, signature_name='Signature'):
        """
        Returns a signed query string ready for use against the FPS REST
        interface.  Encodes the given parameters and adds a signature 
        parameter.
        """
        keys = parameters.keys()
        keys.sort(upcase_compare)
        message = ''
        for k in keys:
            message += "%s%s" % (k, parameters[k])
        sig = self.sign_string(message)
        log.debug("signature = %s" % sig)
        
        parameters[signature_name]  = sig
        return urllib.urlencode(parameters)

    def execute(self, parameters):
        """
        A generic call to the FPS service.  The parameters dictionary
        is sorted, signed, and turned into a valid FPS REST call.  
        The response is read via urllib2 and parsed into an FPSResponse object
        """

        parameters['AWSAccessKeyId'] = self.access_key_id
        parameters['SignatureVersion'] = 1
        parameters['Timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        parameters['Version'] = '2007-01-08'

        query_str = self.get_signed_query(parameters)
        log.debug("request_url == %s/?%s" % (self.fps_url, query_str))

        data = None
        try:
            response = urllib2.urlopen("%s/?%s" % (self.fps_url, query_str))
            data = response.read()
            response.close()
        except urllib2.HTTPError, httperror:
            data = httperror.read()
            httperror.close()

        return FPSResponse(ET.fromstring(data))
        
    def cancelToken(self, token_id, reason=None):
        params = {'Action': 'CancelToken',
                  'TokenId': token_id}
        if reason is not None:
            params['ReasonText'] = reason
        return self.execute(params)

    def discardResults(self, transaction_ids):
        params = {'Action':  'DiscardResults',
                  'TransactionIds': transaction_ids}
        return self.execute(params)

    def getAccountActivity(self, start_date, end_date=None,
                           operation=None, payment_method=None,
                           max_batch_size=None, response_group="Detail",
                           sort_order="Descending", role=None,
                           status=None):
        params = {'Action': 'GetAccountActivity',
                  'StartDate': start_date,
                  'ResponseGroup': response_group,
                  'SortOrderByDate': sort_order,
                  }
        # TODO
        # these blocks of if statements sprinkled throughout
        # the client strike me as ugly
        if end_date is not None:
            params['EndDate'] = end_date
        if operation is not None:
            params['Operation'] = operation
        if max_batch_size is not None:
            params['MaxBatchSize'] = max_batch_size
        if role is not None:
            params['Role'] = role
        if status is not None:
            params['Status'] = status

        return self.execute(params)

    def getAccountBalance(self):
        params = {'Action': 'GetAccountBalance'}
        return self.execute(params)

    def getDebtBalance(self, instrument_id):
        params = {'Action': 'GetDebtBalance',
                  'CreditInstrumentId': instrument_id}
        return self.execute(params)

    def getAllCreditInstruments(self, instrument_status='All'):
        params = {'Action': 'GetAllCreditInstruments',
                  'InstrumentStatus': instrument_status}
        return self.execute(params)

    def getPaymentInstruction(self, token_id):
        params = {'Action': 'GetPaymentInstruction',
                  'TokenId': token_id}
        return self.execute(params)

    def getPipelineUrl(self, 
                       caller_reference, 
                       payment_reason, 
                       transaction_amount, 
                       return_url, 
                       pipeline_name="SingleUse", 
                       ):
        parameters = {'callerReference': caller_reference,
                      'paymentReason': payment_reason,
                      'transactionAmount': transaction_amount,
                      'callerKey': self.access_key_id,
                      'pipelineName': pipeline_name,
                      'returnURL': return_url
                      }

        parameters['awsSignature'] = self.get_pipeline_signature(parameters)
        query_string = urllib.urlencode(parameters)
        url = "%s?%s" % (self.pipeline_url, query_string)
        log.debug(url)
        return url

    def getPrepaidBalance(self, instrument_id):
        params = {'Action': 'GetPrepaidBalance',
                  'PrepaidInstrumentId': instrument_id}
        return self.execute(params)

    def getResults(self, operation=None, max=None):
        params = {'Action': 'GetResults'}
        if operation != None:
            params['Operation'] = operation,
        if max != None:
            params['MaxResultsCount'] = max
        return self.execute(params)

    def getTokenByCaller(self, token_id=None, caller_reference=None):
        params = {'Action': 'GetTokenByCaller'}
        if token_id != None:
            params['TokenId'] = token_id
        if caller_reference != None:
            params['CallerReference'] = caller_reference
        return self.execute(params)

    def getTokenUsage(self, token_id):
        params = {'Action': 'GetTokenUsage',
                  'TokenId': token_id}
        return self.execute(params)

    def getTransaction(self, transaction_id):
        params = {'Action': 'GetTransaction',
                  'TransactionId': transaction_id}
        return self.execute(params)

    def installPaymentInstruction(self, 
                                  payment_instruction, 
                                  caller_reference, 
                                  token_type, 
                                  token_friendly_name=None, 
                                  payment_reason=None):
        """
        Install a payment instruction that conforms to the GateKeeper
        language specification
        """

        params = {'Action': 'InstallPaymentInstruction',
                  'PaymentInstruction': payment_instruction,
                  'CallerReference': caller_reference,
                  'TokenType': token_type,
                  }
        if token_friendly_name is not None:
            params['TokenFriendlyName'] = token_friendly_name
        if payment_reason is not None:
            params['PaymentReason'] = payment_reason
            
        return self.execute(params)

    def installPaymentInstructionBatch(self):
        """ Not implemented.  See http://fpys.achievewith.us/project/ticket/10 """
        pass

    def payBatch(self):
        """ Not implemented.  See http://fpys.achievewith.us/project/ticket/11"""
        pass

    def pay(self,
            caller_token,
            sender_token,
            recipient_token,
            amount,
            caller_reference,
            date = None,
            charge_fee_to='Recipient'):
        params = {'Action': 'Pay',
                  'CallerTokenId': caller_token,
                  'SenderTokenId': sender_token,
                  'RecipientTokenId': recipient_token,
                  'TransactionAmount.Amount': amount,
                  'TransactionAmount.CurrencyCode': 'USD',
                  'CallerReference': caller_reference,
                  'ChargeFeeTo': charge_fee_to
            }

        if date is not None:
            params['TransactionDate'] = date

        return self.execute(params)

    def refund(self,
               caller_token,
               refund_sender_token,
               transaction_id,
               caller_reference,
               refund_amount=None,
               date = None,
               charge_fee_to='Recipient',
               ):
        params = {'Action': 'Refund',
                  'CallerTokenId': caller_token,
                  'RefundSenderTokenId': refund_sender_token,
                  'TransactionId': transaction_id,
                  'CallerReference': caller_reference,
                  'ChargeFeeTo': charge_fee_to,
                  }
        if date is not None:
            params['TransactionDate'] = date
        if refund_amount is not None:
            params['RefundAmount.Amount'] = refund_amount
            params['RefundAmount.CurrencyCode'] = "USD"
        return self.execute(params)

    def reserve(self,
                caller_token,
                sender_token,
                recipient_token,
                amount,
                caller_reference,
                date = None,
                charge_fee_to='Recipient'):
        params = {'Action': 'Reserve',
                  'CallerTokenId': caller_token,
                  'SenderTokenId': sender_token,
                  'RecipientTokenId': recipient_token,
                  'TransactionAmount.Amount': amount,
                  'TransactionAmount.CurrencyCode': 'USD',
                  'CallerReference': caller_reference,
                  'ChargeFeeTo': charge_fee_to,
                  }
        if date is not None:
            params['TransactionDate'] = date

        return self.execute(params)

    def retryTransaction(self, transaction_id):
        params = {'Action': 'RetryTransaction',
                  'OriginalTransactionId': transaction_id}
        return self.execute(params)

    def settle(self,
               transaction_id,
               amount,
               date = None):
        params = {'Action': 'Settle',
                  'ReserveTransactionId': transaction_id,
                  'TransactionAmount.Amount': amount,
                  'TransactionAmount.CurrencyCode': 'USD'}
        if date is not None:
            params['TransactionDate'] = date

        return self.execute(params)

                  

