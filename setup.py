from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name = "FPyS",
      version = "0.5",
      description = "Amazon FPS Library",
      author = "Tim Freund",
      author_email = "tim@digital-achievement.com",
      url = "http://fpys.achievewith.us",
      packages = ["fpys"],
      install_requires = ["wsgi_intercept",
                          ],
      entry_points = {},
      license = 'MIT License',
      long_description = """\
FPyS is a library for interacting with the Amazon Flexible Payment Service.

FPys communicates with the service via the available REST interface.  It handles the
details of request signing and response parsing for the application developer.

An Amazon web services account is required to begin working with FPyS in the development
environment.  An approved account is required to move software into production.

Development Trac: http://fpys.achievewith.us
Mailing List: http://groups.google.com/group/fpys/
""",
      classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ])
