#!/usr/bin/python3

# Standard library imports
import sys
import hashlib
import base64

PASSED  = "\033[32mPASSED\033[0m"  # \
WARNING = "\033[33mWARNING\033[0m" #  \___ Linux-specific colorization
FAILED  = "\033[31mFAILED\033[0m"  #  /
ERROR   = "\033[31mERROR\033[0m"   # /

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
