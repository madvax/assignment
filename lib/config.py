#!/usr/bin/python3

# This library holds functions that allow scripts to read  configuration files.

import os
import sys

# -----------------------------------------------------------------------------
# Some useful variables
VERSION = "1.0.2"
VERBOSE = False
DEBUG   = False
FIRST   = 0
LAST    = -1
ME      = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH = os.path.dirname(os.path.realpath(__file__))  # Path for this file
PASSED  = "\033[32mPASSED\033[0m"  # \
FAILED  = "\033[31mFAILED\033[0m"  # > Linux-specific colorization
ERROR   = "\033[31mERROR\033[0m"   # /


# ----------------------------------------------------------------------------- readConfigFile()
def readConfigFile(file_name):
    """ Reads a config file and returns a dictionary of key/value pairs from
        the configuration file. If anything goes wrong then return an
        empty dictionary. Any errors are sent to standard error.

    """
    configurations = {}
    config_data    = ""
    delimiter      = ' '
    try:
        config_data = open(file_name, 'r').read()
        for line in config_data.split('\n'):
            line = line.strip()  # Clean up leading and trailing whitespace
            if len(line) < 1:
                pass  # Skip blank lines
            elif line[FIRST] == '#':
                pass  # Skip comment lines
            elif line.find(delimeter) == -1:
                pass  # Skip mal-formed lines (lines without an equal sign character'=')
            else:
                line = line.strip()  # Clean up the whitespace
                key = line.split(delimiter, 1)[FIRST].strip()
                value = line.split(delimiter, 1)[LAST].strip()
                configurations[key] = value
    except Exception as e:
        sys.stderr.write("%s -- Unable to read from configurations file %s\n" % (ERROR, file_name))
        print(e)
        configurations = {}  # Trust no one. If there was a problem then flush the data
    return configurations


if __name__ == "__main__":
   pass
