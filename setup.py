from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name = "FPyS",
      version = "0.1",
      description = "Amazon FPS Library",
      author = "Tim Freund",
      author_email = "tim@digital-achievement.com",
      url = "http://achievewith.us",
      packages = find_packages('lib'),
      package_dir = {'': 'lib'},
      entry_points = {},
      license = 'MIT License',
      long_description = """\
FPyS is a library for interacting with the Amazon Flexible Payment Service.

FPys communicates with the service via the available REST interface.  It handles the
details of request signing and response parsing for the application developer.

An Amazon web services account is required to begin working with FPyS in the development
environment.  An approved account is required to move software into production.""",
      classifiers = [
        "Development Status :: 3 - Alpha"
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        ])
