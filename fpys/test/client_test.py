import unittest
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
    assert 16.5 == response.balances['TotalBalance'][0]

def test_getDebtBalance():
    response = fps_client.getDebtBalance(instrument_id = "123")
    assert 0.0 == "blah"

