#!/usr/bin/python3

# Test Case: Password Size Test
# Test both the minimum and maximun sized passwords
# Using the post hash route.
# Example Post to the /hash endpoint
# $ curl -X POST -H "application/json" -d '{"password":"angrymonkey"}' http://127.0.0.1:8088/hash
# RETURNS: job_identifier
# Then use the job identifier to validate the correct hash was
# performed by the server.

import sys
import os
import random
import string
import hashlib
import base64
from getopt import getopt
import time


# Some useful CONSTANTS and VARIABLES
VERSION          = "1.0.1"
VERBOSE          = True
DEBUG            = False
FIRST            = 0
LAST             = -1
DELAY            = 1
ME               = os.path.split(sys.argv[FIRST])[LAST] # Name of this file
MY_PATH          = os.path.dirname(os.path.realpath(__file__))  # Path for this file
LIBRARY_PATH     = os.path.join(MY_PATH, "../lib")
CONFIG_FILE      = os.path.join(MY_PATH, "../conf/target.conf")
RESULTS_FILE     = os.path.join(MY_PATH, "../results/length_test_results.csv")
PASSED           = "\033[32mPASSED\033[0m"  # \
WARNING          = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED           = "\033[31mFAILED\033[0m"  #  /
ERROR            = "\033[31mERROR\033[0m"   # /


# ----------------------------------------------------------------------------- get_random_password()
def get_random_password(length=0):
   """ generate and return a random password of length specified """
   # Assumption: Valid passwords are composed of letters, numbers and special characters
   random_password    = None
   special_characters = "!@#$%^&*()_-+=<>.;:|{}[]\\/~`"
   try:
      character_set = string.ascii_letters + string.digits + special_characters
      random_password = ''.join((random.choice(character_set) for i in range(length)))
   except Exception as e:
      sys.stderr.write("%s -- Unable to get a random password of length %s\n" % (ERROR, str(length)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
      random_password = None
   finally:
      return random_password

# ----------------------------------------------------------------------------- write_result_record_to_file()
def write_result_record_to_file(results_file=RESULTS_FILE, record=""):
   """ writes a record to the results file """
   try:
       f = open(results_file, 'a')
       f.write("%s\n" % str(record))
       f.close()
   except Exception as e:
      sys.stderr.write("%s -- Unable to write to results file '%s'\n" % (ERROR, str(results_file)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
   finally:
      return

# ----------------------------------------------------------------------------- post_password()
def post_password(endpoint, password):
   """ Post a password to  the post hash route and validate the hash  """

   result = FAILED # Assume failure
   try:
      # make the call to post the password
      s = Session()
      # Assumption: Using the argument json={} implies header "application/json"
      req = Request("POST", post_hash_endpoint, json={"password": password})
      prepped = s.prepare_request(req)
      if VERBOSE:
         sys.stdout.write("   - Calling %s\n" %endpoint)
         sys.stdout.flush()
      start_time = time.time() * 1000.0
      resp = s.send(prepped, timeout=timeout)
      stop_time = time.time() * 1000.0
      elapsed_time = stop_time - start_time
      if VERBOSE:
         sys.stdout.write("   - Call time:   %5.1f milliseconds\n" %elapsed_time)
         sys.stdout.write("   - Status Code: %s\n" % str(resp.status_code))
         sys.stdout.write("   - Status Text: %s\n" % str(resp.text))
         sys.stdout.flush()

      # Using the job itentifier, get the hashed password from the API
      get_hash_endpoint = "%s:%s/hash/%s" %(base_url, str(port), str(resp.text))
      hash_from_server = job_identifier_to_hash(get_hash_endpoint)
      hash_expected    = get_sha512_hash(password)
      if VERBOSE:
         sys.stdout.write("   - Expected: %s\n" %hash_expected)
         sys.stdout.write("   - Observed: %s\n" %hash_from_server)
         sys.stdout.flush()

      if hash_from_server == hash_expected:
         result = PASSED
      else:
         result = FAILED
      if VERBOSE:
         sys.stdout.write("   - Result: %s\n" %result)
         sys.stdout.flush()

      # Write the results of this client to the results file
      # "result, password, expected hash, observed hash, hash endpoint, call time, "
      result_record = "%s, %s, %s, %s, %s, %d" %(result           ,
                                                 password         ,
                                                 hash_expected    ,
                                                 hash_from_server ,
                                                 endpoint         ,
                                                 elapsed_time     )
      write_result_record_to_file(record=result_record)

   except Exception as e:
      sys.stderr.write("%s -- Unable to post and validate %s %s\n" % (ERROR, str(endpoint), str(password)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
      results = None
   finally:
      return result






# ----------------------------------------------------------------------------- usage()
def usage():
    """usage() - Prints the usage message on stdout. """
    print("\n\n%s, Version %s, Test Case Password Length." % (ME, VERSION))
    print("Test the minimum and maximum password lengths")
    print(" ")
    print("USAGE: %s [OPTIONS] " % ME)
    print(" ")
    print("OPTIONS: ")
    print("   -h --help      Display this message. ")
    print("   -v --verbose   Runs the program in verbose mode, default: %s. " % VERBOSE)
    print("   -d --debug     Runs the program in debug mode (implies verbose). ")
    print(" ")
    print("EXIT CODES: ")
    print("    0 - Successful completion of the program, all tests passed. ")
    print("    1 - Bad or missing command line arguments. ")
    print("    2 - Unable to import third-party library")
    print("    3 - Unable to import custom library")
    print("  100 - Successful completion of the program, one or more tests failed")

    print(" ")
    print("EXAMPLES: ")
    print("    TODO - I'll make some examples up later. ")
    print(" ")


# Parse and Process the command line arguments
try:
   arguments = getopt(sys.argv[1:]   ,
                      'hvd'        ,
                      ['help'      ,
                       'verbose'   ,
                       'debug'     ] )
except:
  sys.stderr.write("ERROR -- Bad or missing command line argument(s)\n\n")
  usage()
  sys.exit(1)

try:
    # --- Check for a help option
    for arg in arguments[0]:
      if arg[0]== "-h" or arg[0] == "--help":
         usage()
         sys.exit(0)
    # --- Check for a verbose option
    for arg in arguments[0]:
      if arg[0]== "-v" or arg[0] == "--verbose":
         VERBOSE = True
    # --- Check for a debug option
    for arg in arguments[0]:
      if arg[0]== "-d" or arg[0] == "--debug":
         DEBUG   = True
         VERBOSE = True
except Exception as e:
    sys.stderr.write("%s -- %s\n\n" %(ERROR,str(e)))
    usage()
    sys.exit(1)



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

# Custom library imports
sys.path.append(LIBRARY_PATH)
try:
   from config    import readConfigFile
   from api_utils import job_identifier_to_hash
   from sha512    import get_sha512_hash
except:
   sys.stderr.write("%s -- Unable to import custom library\n" % ERROR)
   sys.stderr.write("         Try: git pull\n\n")
   sys.exit(3)


configs = readConfigFile(CONFIG_FILE)
# Test Setup Variables
base_url            = configs["base_url"]
port                = configs["port"]
hash_route          = configs["hash_route"]
stats_route         = configs["stats_route"]
network_latency     = int(configs["network_latency"])
server_process_time = int(configs["server_process_time"])
max_password_length = int(configs["max_password_length"])
min_password_length = 1
timeout             = server_process_time + network_latency
post_hash_endpoint  = "%s:%s/%s" % (base_url, port, hash_route)

# Quietly try to remove any old results file(s)
try: os.remove(RESULTS_FILE)
except: pass

header = "Result, Password, Expected Hash, Observed Hash, Hash Endpoint, Call Time (ms) "
f = open(RESULTS_FILE, 'a')
f.write("%s\n" % str(header))
f.close()

test_results = []

if VERBOSE: print("Test 1: Min Password Length = %d" %min_password_length )
password = get_random_password(min_password_length)
if VERBOSE: print("Password: %s" %password )
test_results.append( post_password(post_hash_endpoint, password))

if VERBOSE: print("Test 2: Max Password Length = %d"  %max_password_length)
password = get_random_password(max_password_length)
if VERBOSE: print("Password: %s" %password )
test_results.append( post_password(post_hash_endpoint, password))

print("Results posted to %s" %RESULTS_FILE)
# Grade the tests
return_code = 0
for test in test_results:
    if test == FAILED:
        return_code = 100
    break
sys.exit(return_code)
