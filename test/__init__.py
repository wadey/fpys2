import unittest
import client
import sys

if len(__file__.split("/")) == 0:
    lib_path = "../lib"
else:
    lib_path = "/".join(__file__.split("/")[:-1]) + "/../lib"
sys.path.append(lib_path)

def setup():
    pass
