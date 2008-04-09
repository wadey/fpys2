from cgi import parse_qs

class FlexiblePaymentService(object):
    def __init__(self):
        self.instruction_installed = False

    def process_request(self, environ):
        environ['fps.params'] = parse_qs(environ['QUERY_STRING'])
        return getattr(self, environ['fps.params']['Action'][0])(environ)

    def CancelToken(self, environ):
        if environ['fps.params']['TokenId'][0].find("INVALID") != -1:
            response = """<ns0:CancelTokenResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>InvalidParams</ErrorCode><ReasonText>"tokenId" has to be a valid token ID. Specified value: Z24XPGA4G3IMGV1EL2DL5KDOKQ4WXZJL9175MNR5I5LF1CKH8UMK3R5NFJUEHXMQasdf</ReasonText></Errors></Errors><RequestId>6b221931-3a58-419a-9958-de56690393c1:0</RequestId></ns0:CancelTokenResponse>"""
        else:
            response = """<ns0:CancelTokenResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Success</Status><RequestId>2a4e67a6-a499-4b3c-b9fa-efd97e117b13:0</RequestId></ns0:CancelTokenResponse>"""
        return [response]

    def GetAccountBalance(self, environ):
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
        response = """<ns0:GetDebtBalanceResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>InvalidParams</ErrorCode><ReasonText>CreditInstrumentId : invalid_instrument_id is invalid</ReasonText></Errors></Errors><RequestId>0c26312a-f03f-4aa0-b1d4-5904ceda690a:0</RequestId></ns0:GetDebtBalanceResponse>"""

        return [response]

    def GetTokenByCaller(self, environ):
        responses = {"Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ": """<ns0:GetTokenByCallerResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Token><TokenId>Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ</TokenId><FriendlyName>fpes.achievewith.us_caller</FriendlyName><Status>Active</Status><DateInstalled>2007-11-06T21:08:11.000-08:00</DateInstalled><CallerInstalled>JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9</CallerInstalled><CallerReference>fpes.achievewith.us_caller</CallerReference><TokenType>Unrestricted</TokenType><OldTokenId>Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ</OldTokenId></Token><Status>Success</Status><RequestId>484360e9-a301-4846-8511-cc44cf84b3bc:0</RequestId></ns0:GetTokenByCallerResponse>""",
                     "Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC": """<ns0:GetTokenByCallerResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Token><TokenId>Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC</TokenId><FriendlyName>fpes.achievewith.us_7_20080325003953_recipient</FriendlyName><Status>Inactive</Status><DateInstalled>2008-03-24T22:40:35.000-07:00</DateInstalled><CallerInstalled>JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9</CallerInstalled><CallerReference>fpes.achievewith.us_7_20080325003953_recipient</CallerReference><TokenType>SingleUse</TokenType><OldTokenId>Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC</OldTokenId><PaymentReason>FPeS Invoice #7</PaymentReason></Token><Status>Success</Status><RequestId>d8b9dc37-cd72-42a6-b7f5-7b3a38eed0ec:0</RequestId></ns0:GetTokenByCallerResponse>""",
                     "fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2" : """<ns0:GetTokenByCallerResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Token><TokenId>ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN</TokenId><FriendlyName>fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2</FriendlyName><Status>Active</Status><DateInstalled>2008-03-10T19:31:48.000-07:00</DateInstalled><CallerInstalled>JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9</CallerInstalled><CallerReference>fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2</CallerReference><TokenType>Unrestricted</TokenType><OldTokenId>ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN</OldTokenId></Token><Status>Success</Status><RequestId>f953e962-e0a5-4c49-a194-6a7520111932:0</RequestId></ns0:GetTokenByCallerResponse>"""}
        if environ['fps.params'].has_key('TokenId'):
            key = environ['fps.params']['TokenId'][0]
        else:
            key = environ['fps.params']['CallerReference'][0]
        return [responses[key]]

    def GetTokenUsage(self, environ):
        if environ['fps.params']['TokenId'][0] == "Z74XLGQ4GSIKGV2ES2DQ5GDOCQZWXIJV9195JNRZIVLFSC1H84M33RDN3JUGHFM5":
            response = """<ns0:GetTokenUsageResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>InvalidTokenType</ErrorCode><ReasonText>Type of token "{0}" is invalid for this operation.</ReasonText></Errors></Errors><RequestId>f2689f79-9848-4980-ba53-74981c25ef89:0</RequestId></ns0:GetTokenUsageResponse>"""
        elif environ['fps.params']['TokenId'][0] == "Z54XNG14GBILGV8EM2D95FDOZQHWX3JT91X5CNR8I3LFICUH88MU3RBNZJUNHGM7":
            response = """<ns0:GetTokenUsageResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Success</Status><RequestId>b48725f7-7842-4a83-a31a-8a728c2e8a6b:0</RequestId></ns0:GetTokenUsageResponse>"""
        return [response]

    def GetPaymentInstruction(self, environ):
        response = """<ns0:GetPaymentInstructionResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Token><TokenId>ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN</TokenId><FriendlyName>fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2</FriendlyName><Status>Active</Status><DateInstalled>2008-03-10T19:31:48.000-07:00</DateInstalled><CallerInstalled>JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9</CallerInstalled><CallerReference>fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2</CallerReference><TokenType>Unrestricted</TokenType><OldTokenId>ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN</OldTokenId></Token><PaymentInstruction>MyRole == \'Caller\';</PaymentInstruction><AccountId>JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9</AccountId><TokenFriendlyName>fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2</TokenFriendlyName><Status>Success</Status><RequestId>29a86313-d869-4c94-b5b6-570e95254f10:0</RequestId></ns0:GetPaymentInstructionResponse>"""
        return [response]

    def InstallPaymentInstruction(self, environ):
        if environ['fps.params']['PaymentInstruction'][0].find("Invalid") != -1:
            response = """<ns0:InstallPaymentInstructionResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>BadRule</ErrorCode><ReasonText>Parse errors: line 1:9: unexpected token: instruction</ReasonText></Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>BadRule</ErrorCode><ReasonText>Parse errors: expecting \'\'\', found \'&lt;EOF&gt;\'</ReasonText></Errors></Errors><RequestId>23328ff9-3717-4273-8443-607769d2cfcf:0</RequestId></ns0:InstallPaymentInstructionResponse>"""
        elif self.instruction_installed:
            response = """<ns0:InstallPaymentInstructionResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><Status>Failure</Status><Errors><Errors><ErrorType>Business</ErrorType><IsRetriable>false</IsRetriable><ErrorCode>DuplicateRequest</ErrorCode><ReasonText>This request is a duplicate of a previous request and cannot be executed.</ReasonText></Errors></Errors><RequestId>46eaa53d-220c-4f63-a14d-1870db5b8375:0</RequestId></ns0:InstallPaymentInstructionResponse>"""
        else:
            response = """<ns0:InstallPaymentInstructionResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><TokenId>ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN</TokenId><Status>Success</Status><RequestId>b9b7be73-e8d5-40b8-8b7e-25f8f94703d9:0</RequestId></ns0:InstallPaymentInstructionResponse>"""
            self.instruction_installed = True
        return [response]

    def Pay(self, environ):
        response = """<ns0:PayResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><ns0:TransactionResponse><TransactionId>133I77HJS56JVM7M54OZIRITRVLUT5F227U</TransactionId><Status>Initiated</Status></ns0:TransactionResponse><Status>Success</Status><RequestId>99a81daa-1a13-46eb-872e-98c61bde612e:0</RequestId></ns0:PayResponse>"""
        return [response]

    def Reserve(self, environ):
        response = """<ns0:ReserveResponse xmlns:ns0="http://fps.amazonaws.com/doc/2007-01-08/"><ns0:TransactionResponse><TransactionId>134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC</TransactionId><Status>Initiated</Status></ns0:TransactionResponse><Status>Success</Status><RequestId>cedef0ad-76f0-4604-82bb-ad28020a4ddc:0</RequestId></ns0:ReserveResponse>"""
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
