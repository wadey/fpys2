from cgi import parse_qs

class FlexiblePaymentService(object):
    def __init__(self):
        pass

    def process_request(self, environ):
        environ['fps.params'] = parse_qs(environ['QUERY_STRING'])
        return getattr(self, environ['fps.params']['Action'][0])(environ)

    def GetAccountBalance(self, environ):
        print "getting account balance"
        response = """<ns0:GetAccountBalanceResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/">
<AccountBalance>
 <TotalBalance><CurrencyCode>USD</CurrencyCode><Amount>16.500000</Amount></TotalBalance>
 <PendingInBalance><CurrencyCode>USD</CurrencyCode><Amount>0.000000</Amount></PendingInBalance>
 <PendingOutBalance><CurrencyCode>USD</CurrencyCode><Amount>0.000000</Amount></PendingOutBalance>
 <AvailableBalances>
  <DisburseBalance><CurrencyCode>USD</CurrencyCode><Amount>16.500000</Amount></DisburseBalance>
  <RefundBalance><CurrencyCode>USD</CurrencyCode><Amount>16.500000</Amount></RefundBalance>
 </AvailableBalances>
</AccountBalance>
<Status>Success</Status>
<RequestId>eac52bd4-c704-44d8-baaa-290b30e08582:0</RequestId></ns0:GetAccountBalanceResponse>\n"""
        return [response]

    def GetDebtBalance(self, environ):
        print "getting debt balance"
        response = """<ns0:GetDebtBalanceResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>InvalidParams</ErrorCode><ReasonText>CreditInstrumentId : invalid_instrument_id is invalid</ReasonText></Errors></Errors><RequestId>0c26312a-f03f-4aa0-b1d4-5904ceda690a:0</RequestId></ns0:GetDebtBalanceResponse>"""

        return [response]

flexible_payment_service = FlexiblePaymentService()


def fps_service(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    print "intercepted"
    print environ

    return flexible_payment_service.process_request(environ)

def create_fps_service():
    return fps_service
