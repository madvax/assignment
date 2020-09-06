#!/usr/bin/python3


# Standard library imports
import sys
import os
import random
import string
import time
import unittest
import json


# Some useful CONSTANTS and VARIABLES
VERSION        = "1.0.0"
VERBOSE        = True
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

# Custom and third-party library imports
try:
    import requests
    from requests import Request, Session
except:
   sys.stderr.write("%s -- Unable to import the 'requests' third-party library\n" % ERROR)
   sys.stderr.write("         Try: pip3 install requests --user\n\n")
   sys.exit(2)

sys.path.append(LIBRARY_PATH)
try:
   from config    import readConfigFile
   from api_utils import job_identifier_to_hash
   from sha512    import get_sha512_hash
   from command   import Command
except:
   sys.stderr.write("%s -- Unable to import custom library\n" % ERROR)
   sys.stderr.write("         Try: git pull\n\n")
   sys.exit(3)

# ============================================================================= Regression_Suite
class Regression_Suite(unittest.TestCase):

   # -------------------------------------------------------------------------- setUp()
   def setUp(self):
      """ Get ready to test.
          Read the configs for the target.
          Ensure the Target is running with a clean start  """


      # Read in test setup variables from config file
      configs                  = readConfigFile(CONFIG_FILE)
      self.base_url            = configs["base_url"]
      self.port                = configs["port"]
      self.hash_route          = configs["hash_route"]
      self.stats_route         = configs["stats_route"]
      self.network_latency     = int(configs["network_latency"])
      self.server_process_time = int(configs["server_process_time"])
      self.timeout             = self.server_process_time + self.network_latency
      self.post_hash_endpoint  = "%s:%s/%s" %(self.base_url, self.port, self.hash_route)
      self.get_stats_endpoint  = "%s:%s/%s" %(self.base_url, self.port, self.stats_route)
      self.server_start_command = "nohup ../target/broken-hashserve_darwin > /dev/null 2>&1 &"

      # Check to see fo the server is running if it is then restart it
      # If it is not then just start it
      if VERBOSE: print("\n\n*** STARTING TEST CASE ***\n")
      r = None
      try: r = requests.get(self.get_stats_endpoint)
      except: pass
      if r != None:
         # Send shutdown signal
         if VERBOSE: print("Shutting down server ...\n")
         requests.post(self.post_hash_endpoint, data="shutdown")
         time.sleep(3)
      # Start server, Assumes that we know where it is
      c = Command(self.server_start_command)
      if VERBOSE:
         print("Starting Server ...\n")
         print(self.server_start_command)
      c.run()
      time.sleep(2)
      if VERBOSE: print("Server Started.\n")
      return

   # -------------------------------------------------------------------------- tearDown()
   def tearDown(self):
      """ Send the shutdown signal to the server  """
      if VERBOSE: print("Shutting down server ...\n")
      requests.post(self.post_hash_endpoint, data="shutdown")
      time.sleep(3)
      if VERBOSE: print("*** Test Case complete ***\n")

   # -------------------------------------------------------------------------- post_password()
   def post_password(self, password):
      """ Post a password to the hash server. Returns a dictionary example below:
          {"status_code": 200, "job_identifier": "42"} """
      payload = {"password":password}
      return_values = {"status_code": 0, "job_identifier": ""}
      r = None
      try: r = requests.post(self.post_hash_endpoint,
                             headers={'Content-type': 'application/json'},
                             json=payload )
      except: pass

      if r == None:
         raise ValueError("No response from %s\n" %self.post_hash_endpoint)
      elif r.status_code == requests.codes.ok:
         self.job_id = r.text
         print("Status Code from server was %d" %r.status_code)
         print("Job Identifier was %s" %str(self.job_id))
         return_values = {"status_code": r.status_code, "job_identifier": r.text}

      else:
         raise ValueError("Bad response %d from %s\nEndpoint: %s\nPayload: %s\n" %(r.status_code, self.post_hash_endpoint, payload) )
      return return_values

   # ----------------------------------------------------------------------------- get_random_password()
   def get_random_password(self, length=0):
      """ generate and return a random password of length specified """
      # Assumption: Valid passwords are composed of letters, numbers and special characters
      random_password = None
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


   # -------------------------------------------------------------------------- test_post_password_waits_5_seconds()
   def test_post_password_waits_5_seconds(self):
      """ """
      start_time = int(time.time())
      self.post_password("Test_Pa$$w0rd")
      stop_time = int(time.time())
      elapsed_seconds = stop_time - start_time
      self.assertGreaterEqual(elapsed_seconds, 5)

   # -------------------------------------------------------------------------- test_post_password_returns_200()
   def test_post_password_returns_200(self):
      """ """
      response = self.post_password("Test_Pa$$w0rd")
      self.assertEqual(response["status_code"], requests.codes.ok)


   # -------------------------------------------------------------------------- test_post_password_returns_job_identifier()
   def test_post_password_returns_job_identifier(self):
      """ """
      response = self.post_password("Test_Pa$$w0rd")
      self.assertNotEqual(response["job_identifier"], "")
      self.assertIsNotNone(response["job_identifier"])

   # -------------------------------------------------------------------------- test_hashed_value()
   def test_hashed_value(self):
      """ """
      random_password = self.get_random_password(48)
      if VERBOSE: print("Password: %s" %random_password)
      response = self.post_password("Test_Pa$$w0rd")
      job_identifier = response["job_identifier"]
      url = "%s/%s" %(self.post_hash_endpoint, str(job_identifier))
      hashed_password_from_server = job_identifier_to_hash(url)
      expected_hashed_password = get_sha512_hash(random_password)
      if VERBOSE:
         print("Expected: %s" %expected_hashed_password)
         print("Observed: %s" %hashed_password_from_server)
      self.assertEqual(expected_hashed_password, hashed_password_from_server)

   # -------------------------------------------------------------------------- test_stats_route()
   def test_stats_route(self):
      """ Check number of requests and average time returned by the server """

      response_times = []
      for i in range(10):

         random_password = self.get_random_password(48)

         start_time = time.time() * 1000.0
         self.post_password(random_password)
         stop_time = time.time() * 1000.0
         elapsed_time = stop_time - start_time
         response_times.append(elapsed_time)

      if len(response_times) > 0:
         r = requests.get(self.get_stats_endpoint)
         response = json.loads(r.text)
         expected_requests     = len(response_times)
         expected_average_time = sum(response_times) / expected_requests

         if VERBOSE:
            print("Expected Requests: %s" %str(expected_requests))
            print("Observed Requests: %s" %str(response["TotalRequests"]))
            print("Expected Average Time: %s" %str(expected_average_time))
            print("Observed Average Time: %s" %str(response["AverageTime"]))

         self.assertEqual(expected_requests, response["TotalRequests"])
         self.assertAlmostEqual(expected_average_time, response["AverageTime"], delta=2000)

      else:
         raise ValiueError("No responses from server to measure")



if __name__ == '__main__':
    unittest.main()

    