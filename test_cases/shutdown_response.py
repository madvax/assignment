#!/usr/bin/python3

# Test Case: Shutdown Response - Should status code 200 and empty
# Test the shutdown response
# Using the post hash route.
# Example Post to the /hash endpoint
# $ curl -i -X POST -d 'shutdown' http://127.0.0.1:1100/hash
# RETURNS: nothing, status code 200

import sys
import os
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
RESULTS_FILE     = os.path.join(MY_PATH, "../results/shutdown_response_results.txt")
PASSED           = "\033[32mPASSED\033[0m"  # \
WARNING          = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED           = "\033[31mFAILED\033[0m"  #  /
ERROR            = "\033[31mERROR\033[0m"   # /



# ----------------------------------------------------------------------------- usage()
def usage():
    """usage() - Prints the usage message on stdout. """
    print("\n\n%s, Version %s, Test Case Shutdown response." % (ME, VERSION))
    print("Test the shutdown response, should status code 200 and empty")
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


OK_TO_TEST = True
final_result = FAILED

if OK_TO_TEST:
   result = FAILED
   payload = 'shutdown'
   r = None
   print("Step 1: Calling %s with data %s" %(post_hash_endpoint, payload))
   try:
      start_time = time.time() * 1000.0
      r = requests.post(post_hash_endpoint, data=payload)
      stop_time = time.time() * 1000.0
      elapsed_time = stop_time - start_time
      print("Back from call in %d ms" %elapsed_time)
      if r == None:
         raise ValueError("No Response from %s" %base_url)
      elif r.status_code == requests.codes.ok:
         response = r.text
         status_code = r.status_code
         print("Response: '%s' " % str(response))
         print("Status Code: %d" % status_code)
         if r.status_code == 200 and r.text == "":
             result = PASSED
         else:
             result = FAILED
             OK_TO_TEST = False

      else :
         raise ValueError("Bad response %d from %s\n%s" %(r.status_code, post_hash_endpoint, r.text))
   except Exception as e:
      sys.stderr.write("%s -- %s\n" %(ERROR, str(e)))
      sys.stderr.write("Check Server\n")
      OK_TO_TEST  = False
   print("%s Step 1" %result)

if OK_TO_TEST:
   # Give it a few seconds to actually shut down
   print("Waiting ...")
   time.sleep(5)
   print("Step 2: Validate that the server has actually shut down.")
   r = None
   try: r = requests.post(post_hash_endpoint, data=payload)
   except: pass

   if r == None:
      print("%s Step 2 Sever at %s is actually shut down." %(PASSED, base_url))
      final_result = PASSED
   else:
      print("%s Step 2 Server is still running." %FAILED)
      final_result = FAILED
else:
   print("Skipping Step 2: Validate that the server has actually shut down.")



# sorry I phoned this one in :-)
message = "Final Result: %s" %final_result
print(message)
f = open(RESULTS_FILE, 'a')
f.write("%s\n" % str(message))
f.close()

if final_result == PASSED: return_code = 0
else: return_code = 100

sys.exit(return_code)