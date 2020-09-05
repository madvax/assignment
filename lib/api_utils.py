#!/usr/bin/python3

# This library holds functions that support API calls.

import os
import sys

# -----------------------------------------------------------------------------
# Some useful variables
VERSION = "1.0.0"
VERBOSE = False
DEBUG   = False
FIRST   = 0
LAST    = -1
ME      = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH = os.path.dirname(os.path.realpath(__file__))  # Path for this file
PASSED  = "\033[32mPASSED\033[0m"  # \
FAILED  = "\033[31mFAILED\033[0m"  # > Linux-specific colorization
ERROR   = "\033[31mERROR\033[0m"   # /


# Third-party library imports
# Import third party libraries after parsing command line arguments
# so you can get the usage message even if the library is not installed
try:
    import requests
    from requests import Request, Session
except:
   sys.stderr.write("%s -- Unable to import the 'requests' third-party library\n" % ERROR)
   sys.stderr.write("         Try: pip3 install requests --user\n\n")
   sys.exit(2)


# ----------------------------------------------------------------------------- job_identifier_to_hash()
def job_identifier_to_hash(endpoint):
   """ given an endpoint with a valid job identifier, returnes the hashed password """
   hashed_password = None

   try:
      r = requests.get(endpoint)
      hashed_password = r.text
      # print("Hashed Password from server: %s"%str(hashed_password))
   except Exception as e:
      sys.stderr.write("%s -- Unable to resolve job identifier using %s\n" % (ERROR, str(endpoint)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
      hashed_password = None
   finally:
      return hashed_password
