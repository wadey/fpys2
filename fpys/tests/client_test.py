import unittest
import uuid
from fpys import FlexiblePaymentClient

import wsgi_intercept
from wsgi_responder import create_fps_service
from wsgi_intercept.urllib2_intercept import install_opener
install_opener()
wsgi_intercept.add_wsgi_intercept('mockfps', 80, create_fps_service)

aws_access_key_id = "not_really_an_id"
aws_secret_access_key = "not_really_a_key"
fps_client = FlexiblePaymentClient(aws_access_key_id,
                                   aws_secret_access_key,
                                   fps_url="http://mockfps:80")


def test_sign_string():
    to_sign = "Sign this string, please"
    signed = "r7ME+3CJWSzzfCBer3Hk9Vlln2Q="
    assert fps_client.sign_string(to_sign) == signed, "Signed strings do not match"

def test_get_pipeline_signature():
    parameters = {'callerReference': 'a_caller_reference',
                  'paymentReason': 'a_payment_reason',
                  'transactionAmount': '1000.00',
                  'callerKey': aws_access_key_id,
                  'pipelineName': 'SingleUse',
                  'returnURL': 'http://localhost/capture'
                  }
    signature = "zZ0RV6OpqpsoVo21UelNUwpwZN8="
    assert fps_client.get_pipeline_signature(parameters, "/capture") == signature, "Signatures do not match"

def test_validate_pipeline_signature():
    parameters = {'callerReference': 'a_caller_reference',
                  'paymentReason': 'a_payment_reason',
                  'transactionAmount': '1000.00',
                  'callerKey': aws_access_key_id,
                  'pipelineName': 'SingleUse',
                  'returnURL': 'http://localhost/capture'
                  }
    signature = "zZ0RV6OpqpsoVo21UelNUwpwZN8="
    
    assert fps_client.validate_pipeline_signature(signature, "/capture", parameters)

def test_getAccountBalance():
    response = fps_client.getAccountBalance()
    assert 16.5 == response.accountBalance.totalBalance.amount

# def test_getDebtBalance():
#     response = fps_client.getDebtBalance(instrument_id = "123")
#     assert 0.0 == "blah"

def test_installPaymentInstruction():
    """
    Install a valid instruction
    """

    unique = "4685bc1eef1311dc952e00142241a3a2"

    # This call should work
    response = fps_client.installPaymentInstruction(payment_instruction="MyRole == 'Caller';",
                                                    caller_reference="fpes.achievewith.us_caller" + unique,
                                                    token_type="Unrestricted",
                                                    token_friendly_name="fpes.achievewith.us_caller" + unique)
    assert response.success == True
    assert response.tokenId == "ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN"


def test_installPaymentInstructionDuplicate():
    """Attempt to install a duplicate instruction"""
    unique = "4685bc1eef1311dc952e00142241a3a2"
    # This call is a duplicate of the last one, it fails
    response = fps_client.installPaymentInstruction(payment_instruction="MyRole == 'Caller';",
                                                    caller_reference="fpes.achievewith.us_caller" + unique,
                                                    token_type="Unrestricted",
                                                    token_friendly_name="fpes.achievewith.us_caller" + unique)
    assert response.success == False
    assert len(response.errors) == 1
    assert response.errors[0].errorCode == "DuplicateRequest"

def test_installPaymentInstructionInvalid():
    """Attempt to install an invalid instruction"""
    # This call has an invalid instruction
    unique = "1234567890"
    response = fps_client.installPaymentInstruction(payment_instruction="Invalid Instruction;",
                                                    caller_reference="fpes.achievewith.us_caller" + unique,
                                                    token_type="Unrestricted",
                                                    token_friendly_name="fpes.achievewith.us_caller" + unique)
    assert response.success == False
    assert len(response.errors) == 2
    assert response.errors[0].reasonText.startswith("Parse errors")


def test_cancelToken():
    """Cancel a valid token"""
    token_id = "Z24XPGA4G3IMGV1EL2DL5KDOKQ4WXZJL9175MNR5I5LF1CKH8UMK3R5NFJUEHXMQ"
    response = fps_client.cancelToken(token_id)
    assert response.success == True

def test_cancelTokenInvalid():
    """Cancel an invalid token"""
    token_id = "INVALID_TOKEN"
    response = fps_client.cancelToken(token_id)
    assert response.success == False
    assert response.errors[0].errorCode == "InvalidParams"

def test_discardResults():
    """Test DiscardResults"""
    response = fps_client.discardResults("135AHMQA9H3NEFJL73GQ33873PLPNGLQZP1")
    assert response.success == True

def test_getAccountActivity():
    response = fps_client.getAccountActivity("2008-04-13")
    assert response.success == True
    assert response.responseBatchSize == 8
    trans = response.transactions[0]
    assert trans.transactionParts.feePaid.amount == 0.0
    assert trans.callerTokenId == "Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ"
    assert trans.operation == "Pay"
    assert trans.dateReceived.month == 4

def test_getPaymentInstruction():
    """Retrive an existing payment instruciton"""
    response = fps_client.getPaymentInstruction("ZS4X8G44GEIVGVSEN2DI5NDO6Q2WX3JQ9125FNR8IBLF5CFH8ZMT3RLNBJUJH9MN")
    assert response.success == True
    assert response.token is not None
    assert response.token.status == 'Active'
    assert response.token.tokenType == 'Unrestricted'
    assert response.paymentInstruction.startswith("MyRole =")

def test_getTokenByCaller():
    response = fps_client.getTokenByCaller(token_id='Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ')
    assert response.success == True
    assert response.token is not None
    assert response.token.status == 'Active'
    assert response.token.friendlyName.startswith("fpes.achievewith.us")

    response = fps_client.getTokenByCaller(token_id='Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC')
    assert response.success == True
    assert response.token.status == 'Inactive'
    assert response.token.callerInstalled == 'JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9'

    response = fps_client.getTokenByCaller(caller_reference='fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2')
    assert response.success == True
    assert response.token.status == 'Active'
    assert response.token.dateInstalled.year == 2008
    assert response.token.dateInstalled.month == 3
    assert response.token.dateInstalled.day == 10

def test_getTokenUsageInvalid():
    """Retrieve token usage for a SingleUse token"""
    # GetTokenUsage is only valid for multi-use tokens
    response = fps_client.getTokenUsage("Z74XLGQ4GSIKGV2ES2DQ5GDOCQZWXIJV9195JNRZIVLFSC1H84M33RDN3JUGHFM5")
    assert response.success == False
    assert response.errors[0].errorCode == 'InvalidTokenType'

def test_getTokenUsageUnrestricted():
    """Retrieve token usage for an unrestricted token"""
    response = fps_client.getTokenUsage("Z54XNG14GBILGV8EM2D95FDOZQHWX3JT91X5CNR8I3LFICUH88MU3RBNZJUNHGM7")
    assert response.success == True

def test_getTokenUsage():
    """Retrieve a token with usage restrictions"""
    # TODO sample, please?
    pass

def test_getTransaction():
    response = fps_client.getTransaction("135AHMQA9H3NEFJL73GQ33873PLPNGLQZP1")
    assert response.success == True
    assert response.transaction.transactionId == "135AHMQA9H3NEFJL73GQ33873PLPNGLQZP1"
    assert response.transaction.senderName == "Kate M DeHaven"
    assert response.transaction.operation == "Pay"
    assert response.transaction.paymentMethod == "CC"

def test_pay():
    """Initiates a payment"""
    response = fps_client.pay(caller_token="Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ",
                              sender_token="2646ZQ3Z19JBRPIBXCM97QRHKT6APPGB2VE9ATJD48N7CF1LXNEZ3YFHBDBPXFGM",
                              recipient_token="Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC",
                              amount=2.0,
                              caller_reference="FPeS Invoice 37")
    assert response.success == True
    assert response.transaction.transactionId == "133I77HJS56JVM7M54OZIRITRVLUT5F227U"
    assert response.transaction.status == "Initiated"

def test_refund():
    # the following was used to create a new token to authorize the refund
    #     fps_client.installPaymentInstruction("MyRole == 'Sender';\nOperationType == 'Refund';",
    #                                          "unit_test_refund_01",
    #                                          "SingleUse",
    #                                          "Refund of Test Transaction",
    #                                          "unit_test_refund_01")
    response = fps_client.refund(caller_token="Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ",
                                 refund_sender_token="Z74XVGZ4G2IKGVIE52D453DOEQGWXMJ491V58NR6I3LFQC2H8BM73R8NMJUJHCMN",
                                 transaction_id="134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC",
                                 caller_reference="Unit Test Refund",
                                 refund_amount="19.95")
    assert response.success == True
    assert response.transaction.status == "Initiated"
    assert response.transaction.transactionId == "134P2CRSN5JFN3KDV3RKPKVQ3OG4H67PPR8"

def test_reserve():
    response = fps_client.reserve("Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ",
                                  "2146KQCZ13JKRP8BHCMI7JRHPTBAPZGU2VB9FTJ84UN7UF7LXAE33YJHSDB8XCG2",
                                  "Z44XQGE4GAI1GV4E92DU5KDOTQPWXKJC91V5MNRII7LFICFH8HMX3RNNPJU4HCMN",
                                  "19.95",
                                  "unit_test_ref_1")
    assert response.success == True
    assert response.transaction.status == "Initiated"
    assert response.transaction.transactionId == "134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC"

def test_retry():
    response = fps_client.retryTransaction("123")
    assert response.success == True
    assert response.transaction.status == "Initiated"

def test_settle_over_amount():
    response = fps_client.settle("134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC",
                                 "100.00")
    assert response.success == False
    assert 1 == len(response.errors)
    assert response.errors[0].errorCode == 'SettleAmountGreaterThanReserveAmount'

def test_settle():
    response = fps_client.settle("134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC",
                                 "19.95")
    assert response.success == True
    assert response.transaction.transactionId == "134OLF7MHB2L4V9T54RHADQ9FCK5NLVZHDC"
    assert response.transaction.status == "Initiated"


