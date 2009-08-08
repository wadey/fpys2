#!/System/Library/Frameworks/Python.framework/Versions/2.5/Resources/Python.app/Contents/MacOS/Python
import pkg_resources
pkg_resources.require("TurboGears")

from turbogears import config, update_config, start_server
import cherrypy
cherrypy.lowercase_api = True
from os.path import *
import sys

# first look on the command line for a desired config file,
# if it's not on the command line, then
# look for setup.py in this directory. If it's not there, this script is
# probably installed
if len(sys.argv) > 1:
    update_config(configfile=sys.argv[1],
        modulename="fpes.config")
elif exists(join(dirname(__file__), "setup.py")):
    update_config(configfile="dev.cfg",modulename="fpes.config")
else:
    update_config(configfile="prod.cfg",modulename="fpes.config")
config.update(dict(package="fpes"))

from fpes.controllers import Root
from fpes import model
model.init()

abort = False
if config.get("aws_access_key_id", "") == "":
    print "The 'aws_access_key_id' variable must be set in your configuration file (usually dev.cfg)"
    abort = True
if config.get("secret_access_key", "") == "":
    print "The 'secret_access_key' variable must be set in your configuration file (usually dev.cfg)"
    abort = True

if abort:
    sys.exit(-1)


start_server(Root())
