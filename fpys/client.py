import base64, hmac, sha
import urllib, urllib2
import logging
import time

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

class FPSResponse(object):
    def __init__(self, document=None):
        if document is not None:
            document = ET.ElementTree(document)
        self.document = document

        if document.find("RequestId"):
            self.requestId = document.find("RequestId").text
        elif document.find("RequestID"):
            self.requestId = document.find("RequestID").text

        if document.find("Status") is not None:
            if document.find("Status").text == "Success":
                self.success = True
            else:
                self.success = False
                self.errors = []

                for error in document.findall("//Errors/Errors"):
                    print "parsing errors"
                    print ET.tostring(error)
                    err = {}
                    err['type'] = error.find("ErrorType").text
                    err['retriable'] = error.find("IsRetriable").text
                    if err['retriable'] == "False":
                        err['retriable'] = False
                    else:
                        err['retriable'] = True
                    err['errorCode'] = error.find("ErrorCode").text
                    err['reason'] = error.find("ReasonText").text
                    self.errors.append(err)


        for name in ['CallerTokenId', 'SenderTokenId', 'RecipientTokenId', 'TokenId']:
            if document.find(name) is not None:
                attr_name = name[0].lower() + name[1:]
                setattr(self, attr_name, document.find(name).text)

        if document.find("AccountBalance"):
            self.balances = {}
            for bal in ['TotalBalance', 'PendingInBalance', 'PendingOutBalance', 
                        'DisburseBalance', 'RefundBalance']:
                self.balances[bal] = (float(document.find("//" + bal).find("Amount").text),
                                      document.find("//" + bal).find("CurrencyCode").text)
            

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
        log.debug("returned_data == %s" % data)

        return FPSResponse(ET.fromstring(data))
        
    def cancelToken(self, token_id, reason=None):
        params = {'Action': 'CancelToken',
                  'TokenId': token_id}
        if reason is not None:
            params['ReasonText'] = reason
        return self.execute(params)

    def discardResults(self):
        pass

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

    def getTokenByCaller(self):
        pass

    def getTokenUsage(self, token_id):
        params = {'Action': 'GetTokenUsage',
                  'TokenId': token_id}
        return self.execute(params)

    def getTransaction(self):
        pass

    def installPaymentInstruction(self, 
                                  payment_instruction, 
                                  caller_reference, 
                                  token_type, 
                                  token_friendly_name=None, 
                                  payment_reason=None):
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
        pass

    def payBatch(self):
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

    def refund(self):
        pass

    def reserve(self):
        pass

    def retryTransaction(self):
        pass

    def settle(self):
        pass

