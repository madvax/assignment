#!/usr/bin/python3

# Clean Shutdown Test
# In Flight Responses should still process even if a shutdown command is issued.
# We will use two threads to accomplish this. Thread "A" will loop through 10
# password hash calls. When Thread "A" initiates call number 5 then
# Thread "B" will immediately send the shutdown call to the server. In a
# successful test Thread "A" call number 5 should be successful and all
# subsequent calls should fail.

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
VERBOSE        = False
DEBUG          = False
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
THREAD_A_DONE  = False
RESULT_MONITOR = [] # array of results. 0 = passed 1 = failed
SEND_SHUTDOWN  = False # Flag to signal Thread "B" to send the Shutdown Signal

# ----------------------------------------------------------------------------- thread_a()
def thread_a(post_hash_endpoint):
   """ The Thread that calls the password hash service """
   global THREAD_A_DONE
   global RESULT_MONITOR
   global SEND_SHUTDOWN
   try:
      for i in range(10):

         if i == 4:
            SEND_SHUTDOWN = True
            message = "Thread 'A' sent the shutdown signal to Thread B"
            sys.stdout.write("%s\n" %message)
            sys.stdout.flush()

         message = "Thread 'A' Calling post hash route %d" %i
         sys.stdout.write("%s\n" %message)
         sys.stdout.flush()
         r = None
         try:
            r = requests.post(post_hash_endpoint, json={"password": "P2$$w0rd"})
            message = "Thread 'A' Back from call to post hash route %d" %i
            sys.stdout.write("%s\n" % message)
            sys.stdout.flush()
         except:
            pass
         if r == None:
            RESULT_MONITOR.append(1)
            message = "Thread 'A' Back from call no response from post hash route %d" % i
            sys.stdout.write("%s\n" % message)
            sys.stdout.flush()
         else:
            RESULT_MONITOR.append(0)
   except Exception as e:
      message = "Tread 'A': %s" %str(e)
      sys.stderr.write("%s -- %s\n" %(ERROR, message))
      sys.stderr.flush()
   finally:
      message = "Thread 'A' Finished"
      sys.stdout.write("%s\n" % message)
      sys.stdout.flush()
      THREAD_A_DONE = True
      return

# ----------------------------------------------------------------------------- thread_b()
def thread_b(post_hash_endpoint):
   """ The Thread that sends the shutdown signal based on 'SEND_SHUTDOWN' """
   global SEND_SHUTDOWN

   try:

      # TODO: Make this some sort of signal/slot solution. see: QThread
      while not SEND_SHUTDOWN:
          time.sleep(0.5) # Wait for the signal checking every half a second

      time.sleep(1) # Ensure that Thread A got the fifth call in flight

      r = requests.post(post_hash_endpoint, data='shutdown')
      message = "Thread 'B' SENT SHUTDOWN SIGNAL TO SERVER %s" %post_hash_endpoint
      sys.stdout.write("%s\n" % message)
      sys.stdout.flush()
   except Exception as e:
      message = "Tread 'B': %s"
      sys.stderr.write("%s -- %s\n" %(ERROR, str(e)))
      sys.stderr.flush()
   finally:
      message = "Thread 'B' Finished"
      sys.stdout.write("%s\n" % message)
      sys.stdout.flush()
      return




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






t_a = Thread(target=thread_a, args=(post_hash_endpoint,))
t_a.start()

t_b = Thread(target=thread_b, args=(post_hash_endpoint,))
t_b.start()

while not THREAD_A_DONE:
   time.sleep(1)

print(RESULT_MONITOR)

if RESULT_MONITOR == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]:
   result = PASSED
   exit_code = 0
else:
   result = FAILED
   exit_code = 1
print("%s Clean Shutdown Test" %result)
sys.exit(exit_code)
