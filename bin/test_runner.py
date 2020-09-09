#!/tmp/python3

# Test Master
# This script executes test cases listed in a test suite file.
# The test suite file should be specified on the command line as a
# command line argument to this script. See the usage() function for details.
# Test suite results are maintained in the "results" folder specified in the test
# master config file located in the etc folder for this package.
#  -- H. Wilson, January 2018

import logging
# -----------------------------------------------------------------------------
# Standard Library Imports
import os
import sys
import time
from getopt import getopt
import logging

# -----------------------------------------------------------------------------
# Some useful variables
VERSION        = "1.0.0"
VERBOSE        = True
DEBUG          = False
FIRST          = 0
LAST           = -1
ME             = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH        = os.path.dirname(os.path.realpath(__file__))  # Path for this file
LIBRARY_PATH   = os.path.join(MY_PATH, "../lib")
LOG_PATH       = os.path.join(MY_PATH, "../log")
LOG_FILE       = os.path.join(LOG_PATH, "%s.log" % ME.split('.')[FIRST])  # test_runner.log
LOG_FORMAT     = "%(asctime)s, %(levelname)s, %(message)s"
TESTSUITE_PATH = os.path.join(MY_PATH, "../test_suites")
TESTCASE_PATH  = os.path.join(MY_PATH, "../test_cases")
RESULTS_HOME   = os.path.join(MY_PATH, "../results")
TC_OUTPUT_FILE = "output.txt"
TC_ERRORS_FILE = "errors.txt"
PASSED         = "\033[32mPASSED\033[0m"  #\
WARNING        = "\033[33mWARNING\033[0m" # \___ Linux-specific colorization
FAILED         = "\033[31mFAILED\033[0m"  # /
ERROR          = "\033[31mERROR\033[0m"   #/

# ----------------------------------------------------------------------------- usage()
def usage():
    """usage() - Prints the usage message on stdout. """
    print("\n\n%s, Version %s, Test Suite Runner." % (ME, VERSION))
    print("Runs test cases read from a test suite file")
    print(" ")
    print("USAGE: %s [OPTIONS] test_suite_filename" % ME)
    print(" ")
    print("OPTIONS: ")
    print("   -h --help      Display this message. ")
    print("   -v --verbose   Runs the program in verbose mode, default: %s. " % VERBOSE)
    print("   -d --debug     Runs the program in debug mode (implies verbose). ")
    print(" ")
    print("EXIT CODES: ")
    print("    0 - Successful completion of the program, all tests passed. ")
    print("    1 - Bad or missing command line arguments. ")
    print("  100 - Successful completion of the program, one or more tests failed")

    print(" ")
    print("EXAMPLES: ")
    print("    TODO - I'll make some examples up later. ")
    print(" ")


# Parse and Process the command line options
try:
   arguments = getopt(sys.argv[1:]   ,
                      'hvdc:'      ,
                      ['help'      ,
                       'verbose'   ,
                       'debug'     ] )
except:
  sys.stderr.write("%s -- Bad or missing command line argument(s)\n\n" %ERROR)
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

sys.path.append(LIBRARY_PATH)
from command import Command
import command
from config import readConfigFile

# -----------------------------------------------------------------------------
# STEP 1: Create, configure, and initialize a logger for this script.
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()
logger.info("%s Started =======================================================" % ME)

# -----------------------------------------------------------------------------
# STEP 2: Make sure a test suite file was provided and that it exists.
test_suite_filename = sys.argv[LAST]
test_suite_filename = os.path.join(TESTSUITE_PATH, test_suite_filename)
if os.path.isfile(test_suite_filename):
    message = "Found test suite file %s" %test_suite_filename
    logger.info(message)
else:
    message = "Unable to find test suite file %s" %test_suite_filename
    sys.stderr.write("%s -- %s\n" %(ERROR, message))
    logger.critical(message)
    sys.exit(3)

# STEP 3: Get a list of test cases from thee test suite file
list_of_test_cases = []
test_suite_data = open(test_suite_filename, 'r').read()
for line in test_suite_data.split('\n'):
    line = line.strip()  # Clean up leading and trailing whitespace
    if len(line) < 1:
        pass  # Skip blank lines
    elif line[FIRST] == '#':
        pass  # Skip comment lines
    else:
        list_of_test_cases.append(line)
# Check for empty test suite file
if len(list_of_test_cases) < 1:
    message = "No test cases found in %s, nothing to do" %test_suite_filename
    print("%s -- %s"%(WARNING, message))
    logger.warning(message)
    sys.exit(0)

message = "Test cases %s" %str(list_of_test_cases)
logger.info(message)
# Create a folder in the results folder for this run
folder_name = time.strftime("%Y%m%d-%H%M%S"  , time.localtime())
results_folder = os.path.join(RESULTS_HOME, folder_name)
os.mkdir(results_folder)

# STEP 4: Loop through each test case, run the test case
#         and write the results to the results folder.

# Dictionary that holds the results for each test case
suite_results = {}

test_case_counter = 0
for test_case in list_of_test_cases:

    # manage the test case counter
    test_case_counter += 1

    # pretty up the test case name, no '.py' necessary
    test_case_name = test_case.split('.',)[FIRST]

    # log the event
    message = "Running (%d of %d) %s" %(test_case_counter, len(list_of_test_cases), test_case_name)
    print(message)
    logger.info(message)

    # figure out and create a test case results folder for this test case
    test_case_results_folder = os.path.join(results_folder, test_case_name)
    os.mkdir(test_case_results_folder)

    # Run the test case
    test_case_execution_command = os.path.join(TESTCASE_PATH, test_case)
    message = "Executing: %s" %test_case_execution_command
    print(message)
    logger.info(message)

    #    *** ******************* ***
    #    *** TEST CASE EXECUTION ***
    #    *** ******************* ***
    c = Command(test_case_execution_command)
    c.run()

    # show the results on stdout
    c.showResults()

    # Save the results for this test case to the Dictionary
    suite_results[test_case_name] = c.returnResults()

    if suite_results[test_case_name]["returnCode"] == 0: result = PASSED
    else: result = FAILED

    message = "Test Case (%d of %d) %s %s" %(test_case_counter, len(list_of_test_cases), test_case, result)
    print(message)
    logger.info(message)


    # write the results to the test case results folder
    output_file_name = os.path.join(test_case_results_folder, TC_OUTPUT_FILE)
    f = open(output_file_name, 'w')
    f.write(suite_results[test_case_name]["output"])
    f.close()
    error_file_name = os.path.join(test_case_results_folder, TC_ERRORS_FILE)
    f = open(error_file_name, 'w')
    f.write(suite_results[test_case_name]["error"])
    f.close()

# -----------------------------------------------------------------------------
# Write the summary report
report_string = """
==================
Test Suite Results
==================

        Test Case           Result
----------------------------------
"""
passed_count = 0
for test_case in suite_results:
    passed_count += 1
    if suite_results[test_case]["returnCode"] == 0: result = PASSED
    else: result = FAILED
    report_string += "%26s  %s\n" %(test_case, result)
report_string += "----------------------------------\n"
report_string += "%26s  %d of %d\n" %("Passed", passed_count, len(list_of_test_cases))
print(report_string)
summary_file = os.path.join(results_folder ,"SUMMARY.txt")
f = open(summary_file, 'w')
f.write(report_string)
f.close()

print("\n\nTest case execution complete, by your command.\n\n")
sys.exit(0)