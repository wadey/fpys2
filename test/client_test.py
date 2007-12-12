import unittest
from fpys import FlexiblePaymentClient

aws_access_key_id = "not_really_an_id"
secret_access_key = "not_really_a_key"
fps_client = FlexiblePaymentClient(aws_access_key_id,
                                   secret_access_key)


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
