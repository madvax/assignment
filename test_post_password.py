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


# Some useful CONSTANTS and VARIABLES
VERSION = "1.0.1"
VERBOSE = True
DEBUG   = True
FIRST   = 0
LAST    = -1
DELAY   = 1
ME      = os.path.split(sys.argv[FIRST])[LAST] # Name of this file
MY_PATH = os.path.dirname(os.path.realpath(__file__))  # Path for this file
PASSED  = "\033[32mPASSED\033[0m"  # \
WARNING = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED  = "\033[31mFAILED\033[0m"  #  /
ERROR   = "\033[31mERROR\033[0m"   # /

# Test Setup Variables
# TODO: Put this into a config file of some sort
base_url            = "http://localhost"
port                = 1100
hash_route          = "hash"
stats_route         = "stats"
network_latency     = 1
server_process_time = 5
timeout             = server_process_time + network_latency

# Native Functions
# ----------------------------------------------------------------------------- get_random_password()
def get_random_password(length=0):
    """ generate and return a random password of length specified"""
    # Assumption: Valid passwords are composed of characters below
    random_password    = None
    special_characters = "!@#$%^&*()_-+=<>,.;:|{}[]\\/~`"
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

# ----------------------------------------------------------------------------- get_sha512_hash()
def get_sha512_hash(input_string=""):
    """ calculate and return the sha512 hash of the input string """
    return_string = None
    try:
       input_string  = input_string.encode()
       sha512_hash   = hashlib.sha512(input_string).digest()
       return_string = base64.b64encode(sha512_hash)
       return_string = return_string.decode("utf-8")
    except Exception as e:
       sys.stderr.write("%s -- Unable to get a SHA-512 hash for \"%s\"\n" %(ERROR, input_string))
       sys.stderr.write("%s\n\n" %str(e))
       sys.stderr.flush()
       return_string = None
    finally:
       return return_string

# ----------------------------------------------------------------------------- post_and_validate()
def post_password(endpoint, password):
   results = None
   try:
      s = Session()
      req = Request("POST", post_hash_endpoint, json={"password": password})
      prepped = s.prepare_request(req)
      if VERBOSE: print("Calling %s" %endpoint)
      start_time = time.time() * 1000.0
      resp = s.send(prepped, timeout=timeout)
      stop_time = time.time() * 1000.0
      elapsed_time = stop_time - start_time
      if VERBOSE: print("   - Call time:   %5.1f milliseconds " %elapsed_time)
      if VERBOSE: print("   - Status Code: %s" % str(resp.status_code))
      if VERBOSE: print("   - Status Text: %s" % str(resp.text))

      get_hash_endpoint = "%s:%s/hash/%s" %(base_url, str(port), str(resp.text))
      hash_from_server = job_identifier_to_hash(get_hash_endpoint)
      hash_expected    = get_sha512_hash(password)
      print("   - Expected: %s" %hash_expected)
      print("   - Observed: %s" %hash_from_server)

      if hash_from_server == hash_expected:
         print(PASSED)
      else:
         print(FAILED)

   except Exception as e:
      sys.stderr.write("%s -- Unable to post and validate %s %s\n" % (ERROR, str(endpoint), str(password)))
      sys.stderr.write("%s\n\n" % str(e))
      sys.stderr.flush()
      results = None
   finally:
      return results

# ----------------------------------------------------------------------------- job_identifier_to_hash()
def job_identifier_to_hash(endpoint):
   """ given an endpoint with a valid job identifier, returned the hashed password """
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
    print("   -b --base_url= Endpoint base url, default: %s. " %base_url)
    print("   -p --port=     Endpoint port number, default: %s. " %str(port))
    print(" ")
    print("EXIT CODES: ")
    print("    0 - Successful completion of the program. ")
    print("    1 - Bad or missing command line arguments. ")
    print("    2 - Unable to import third-party library")
    print(" ")
    print("EXAMPLES: ")
    print("    TODO - I'll make some examples up later. ")
    print(" ")


# Process the command line arguments
try:
   arguments = getopt(sys.argv[1:]   ,
                      'hvdb:p:'      ,
                      ['help'      ,
                       'verbose'   ,
                       'debug'     ,
                       'base_url=' ,
                       'port='     ]  )
except:
  sys.stderr.write("ERROR -- Bad or missing command line argument(s)\n\n")
  usage()
  sys.exit(1)

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




post_hash_endpoint = "%s:%s/%s" % (base_url, port, hash_route)

counter = 0
for i in range(3):


   counter += 1
   password_length = random.randrange(0, 101, 2)
   random_password = get_random_password(password_length )
   print("Test %d: password=\"%s\"" %(counter, random_password))
   post_password(post_hash_endpoint, random_password)


