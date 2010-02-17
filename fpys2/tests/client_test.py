import unittest
import uuid
from fpys2 import FlexiblePaymentClient
import hashlib

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
    signed = "JBwBZJ1Myf1MDFqQBiiwrQ9CYAbhPGKyZYmXbxgFRwo="
    assert fps_client.sign_string(to_sign, hashlib.sha256) == signed, "Signed strings do not match"

def test_get_signature():
    parameters = {'callerReference': 'a_caller_reference',
                  'paymentReason': 'a_payment_reason',
                  'transactionAmount': '1000.00',
                  'callerKey': aws_access_key_id,
                  'pipelineName': 'SingleUse',
                  'returnURL': 'http://localhost/capture'
                  }
    signature = "XhQ1h0ro5eUU2fCZSz4rNNbYDrwHNi4dpfaTe9VrZTE="
    assert fps_client.get_signature(parameters, "/capture") == signature, "Signatures do not match"

def test_cancel_token():
    """Cancel a valid token"""
    token_id = "Z24XPGA4G3IMGV1EL2DL5KDOKQ4WXZJL9175MNR5I5LF1CKH8UMK3R5NFJUEHXMQ"
    response = fps_client.cancel_token(token_id)
    assert response.success == True

def test_cancel_token_invalid():
    """Cancel an invalid token"""
    token_id = "INVALID_TOKEN"
    response = fps_client.cancel_token(token_id)
    assert response.success == False
    assert response.errors[0].errorCode == "InvalidParams"

def test_get_token_by_caller():
    response = fps_client.get_token_by_caller(token_id='Z34XMGF4GCILGV7EV2D45DDO4Q6WXEJZ9175UNR5I9LFEC1H8MMX3R6NBJUJH8MQ')
    assert response.success == True
    assert response.token is not None
    assert response.token.status == 'Active'
    assert response.token.friendlyName.startswith("fpes.achievewith.us")

    response = fps_client.get_token_by_caller(token_id='Z44X4G84G1ILGV4ER2DQ5HDO3Q2WXBJS91C5QNREICLF3CZH8SMA3RXN1JUDH9MC')
    assert response.success == True
    assert response.token.status == 'Inactive'
    assert response.token.callerInstalled == 'JMXHWUQJONDR53DM28EHVCGFILGI4RGNX541Z9'

    response = fps_client.get_token_by_caller(caller_reference='fpes.achievewith.us_caller4685bc1eef1311dc952e00142241a3a2')
    assert response.success == True
    assert response.token.status == 'Active'
    assert response.token.dateInstalled.year == 2008
    assert response.token.dateInstalled.month == 3
    assert response.token.dateInstalled.day == 10

def test_pay():
    """Initiates a payment"""
    response = fps_client.pay(sender_token="2646ZQ3Z19JBRPIBXCM97QRHKT6APPGB2VE9ATJD48N7CF1LXNEZ3YFHBDBPXFGM",
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


