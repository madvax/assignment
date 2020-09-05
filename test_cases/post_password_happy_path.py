#!/usr/bin/python3

# Test Case: Post password "Happy Path"
# Posts passwords to the Password Hashing Application.
# The Password Hashing Application (PHA) should return a
# job identifier immediately. The PHA should then wait
# five seconds and compute the password hash.
# The hashing algorithm should be SHA512.
# Example Post to the /hash endpoint
# $ curl -X POST -H "application/json" -d '{"password":"angrymonkey"}' http://127.0.0.1:8088/hash
# RETURNS: job_identifier

# Standard library imports
import sys
import os
import random
import string
import hashlib
import base64
from getopt import getopt
import time
from threading import Thread


# Some useful CONSTANTS and VARIABLES
VERSION        = "1.0.1"
VERBOSE        = True
DEBUG          = True
FIRST          = 0
LAST           = -1
DELAY          = 1
ME             = os.path.split(sys.argv[FIRST])[LAST] # Name of this file
MY_PATH        = os.path.dirname(os.path.realpath(__file__))  # Path for this file
LIBRARY_PATH   = os.path.join(MY_PATH, "../lib")
CONFIG_FILE    = os.path.join(MY_PATH, "../conf/target.conf")
RESULTS_FILE   = os.path.join(MY_PATH, "../results/results.csv")
PASSED         = "\033[32mPASSED\033[0m"  # \
WARNING        = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED         = "\033[31mFAILED\033[0m"  #  /
ERROR          = "\033[31mERROR\033[0m"   # /
THREAD_MONITOR = []
CLIENTS        = 10 # Default number of clients to execute in parallel


# Native Functions

#TODO: Make an object of type password that has cool methods like: get_hash, generate_random, ..., etc.
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

# ----------------------------------------------------------------------------- post_and_validate()
def post_password(endpoint, password, thread_index):
   """ per-thread client actions """
   global THREAD_MONITOR
   results = None
   try:
      # mark the cliebt as "running" 1 = running, 0 = not running
      THREAD_MONITOR[thread_index] = 1

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
      # "client, result, password, expected hash, observed hash, hash endpoint, client count, call time, "
      result_record = "%d, %s, %s, %s, %s, %s, %d, %s " %(thread_index        ,
                                                          result              ,
                                                          password            ,
                                                          hash_expected       ,
                                                          hash_from_server    ,
                                                          endpoint            ,
                                                          sum(THREAD_MONITOR) ,
                                                          elapsed_time        )
      write_result_record_to_file(record=result_record)
   except Exception as e:
      sys.stderr.write("%s -- Unable to post and validate %s %s\n" % (ERROR, str(endpoint), str(password)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
      results = None
   finally:
      THREAD_MONITOR[thread_index] = 0
      return results

# ----------------------------------------------------------------------------- usage()
def usage():
    """usage() - Prints the usage message on stdout. """
    print("\n\n%s, Version %s, Test Case POST password \"Happy Path\"." % (ME, VERSION))
    print("Happy Path for the POST password route")
    print(" ")
    print("USAGE: %s [OPTIONS] " % ME)
    print(" ")
    print("OPTIONS: ")
    print("   -h --help      Display this message. ")
    print("   -v --verbose   Runs the program in verbose mode, default: %s. " % VERBOSE)
    print("   -d --debug     Runs the program in debug mode (implies verbose). ")
    print("   -c --clients=  Client count [0-500], default: %s. " %str(CLIENTS))
    print(" ")
    print("EXIT CODES: ")
    print("    0 - Successful completion of the program. ")
    print("    1 - Bad or missing command line arguments. ")
    print("    2 - Unable to import third-party library")
    print("    3 - Unable to import custom library")

    print(" ")
    print("EXAMPLES: ")
    print("    TODO - I'll make some examples up later. ")
    print(" ")


# Parse and Process the command line arguments
try:
   arguments = getopt(sys.argv[1:]   ,
                      'hvdc:'      ,
                      ['help'      ,
                       'verbose'   ,
                       'debug'     ,
                       'clients='  ] )
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
    for arg in arguments[0]:
      if arg[0]== "-c" or arg[0] == "--clients":
         try:
            CLIENTS = int(arg[1])
            if CLIENTS > 500: raise ValueError("Client count too high, must be [0-500]")
         except: raise ValueError("Bad clients argument %s" %str(arg[1]))
except Exceptions as e:
    sys.stderr.write("ERROR -- %s\n\n" %str(e))
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
timeout             = server_process_time + network_latency
post_hash_endpoint  = "%s:%s/%s" % (base_url, port, hash_route)

# Quietly try to remove any old results file(s)
try: os.remove(RESULTS_FILE)
except: pass

# Start the threads
counter = 0
for i in range(CLIENTS):
   THREAD_MONITOR.append(0)
   counter += 1
   password_length = random.randrange(0, 101, 2)
   random_password = get_random_password(password_length )
   print("Test %d: password=\"%s\"" %(counter, random_password))
   t = Thread(target=post_password, args=(post_hash_endpoint, random_password, (len(THREAD_MONITOR)-1 ),))
   t.start()
   time.sleep(1)

while sum(THREAD_MONITOR) > 0:
   sys.stdout.write("Running %d clients\n" %sum(THREAD_MONITOR)  )
   sys.stdout.flush()
   time.sleep(1)




