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
    assert 16.5 == response.balances['TotalBalance'][0]

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
    assert response.errors[0]['errorCode'] == "DuplicateRequest"

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
    assert response.errors[0]['reason'].startswith("Parse errors")


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
    assert response.errors[0]['errorCode'] == "InvalidParams"

def test_getTokenUsageInvalid():
    """Retrieve token usage for a SingleUse token"""
    # GetTokenUsage is only valid for multi-use tokens
    response = fps_client.getTokenUsage("Z74XLGQ4GSIKGV2ES2DQ5GDOCQZWXIJV9195JNRZIVLFSC1H84M33RDN3JUGHFM5")
    assert response.success == False
    assert response.errors[0]['errorCode'] == 'InvalidTokenType'

def test_getTokenUsageUnrestricted():
    """Retrieve token usage for an unrestricted token"""
    response = fps_client.getTokenUsage("Z54XNG14GBILGV8EM2D95FDOZQHWX3JT91X5CNR8I3LFICUH88MU3RBNZJUNHGM7")
    assert response.success == True

def test_getTokenUsage():
    """Retrieve a token with usage restrictions"""
    # TODO sample, please?
    pass

