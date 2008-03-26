# This file sets up an FPS client for you to experiement with
# at the python interpreter prompt.  To get started, copy
# shellconfig.py.example to shellconfig.py and set the variables
# with your values.
#
# Once that is done, load this file into a python interpreter
# with one of the following commands:
# python -i shell.py
# ipython shell.py


import shellconfig
from fpys.client import *
import xml.etree.ElementTree as ET

fps_client = FlexiblePaymentClient(shellconfig.aws_access_key_id,
                                   shellconfig.aws_secret_access_key)

print "ElementTree available at ET"
print "FlexiblePaymentClient instance at fps_client"

