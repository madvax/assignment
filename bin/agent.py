#!/usr/bin/env python

# Agent Listener - Listens on a TCP/IP socket for commands to execute

"""
THEORY OF OPERATION

This program sets up a TCP listener on socket defined by the IP Address
and IP Port number specified either in the code by default or at invocation
via command line options/arguments (see the usage function). Once the TCP
listener has started, it will accept message from a TCP clients and act as
directed by the message from the client(s).

Message received by the Agent via TCP should be of the form:

   DIRECTIVE:COMMAND

Valid directives are:

   TA - Used for commands that control/query the test agent itself
   OS - Used for commands intended to be executed on the operating system
        on which the Agent is running.

Valid TA Commands are:

   version     - Gets the version of the Agent
   bye         - Ends the session with the Agent
   quit        - Ends the session with the Agent
   exit        - Ends the session with the Agent
   getname     - Gets the name of the Agent (each agent has/should have a unique name)
   setname     - Sets the name of the  Agent
   getusername - Gets the name of the user that the Agent is running as
   shutdown    - Shuts down the agent
   localtime   - Get the localtime of server that the Agent is running on

All TA directives return a Python dictionary of two key-value pairs.
The first key-value pair is:
   AGENT_RETURN_CODE : integer  (zero indicates success, non-zero indicates failure)
The second key-value pair is:
   AGENT_MESSAGE : "string"     (double quote encapsulated string)

This message is either an answer to the TA command or an agent error message.

Examples:

   --- Get the Version of the Agent
   tcp send from client:    TA:version
   tcp recv from agent :    {AGENT_RETURN_CODE:0, AGENT_MESSAGE:"VERSION: 1.1.0"}

   --- Get the name of the Agent
   tcp send from client:    TA:getname
   tcp recv from agent :    {AGENT_RETURN_CODE:0:, AGENT_MESSAGE:"Some Name"}

   --- Set the name of the agent
   tcp send from client:    TA:setname=New Name
   tcp recv from agent :    {AGENT_RETURN_CODE:0, AGENT_MESSAGE:"Agent Name set to 'New Name'"}

   --- Close the session with the agent
   tcp send from client:    TA:bye
   tcp recv from agent :    {AGENT_RETURN_CODE:0, AGENT_MESSAGE:"CLOSING CONNECTION"}

   --- Shutting down the Agent
   tcp send from client:    TA:shutdown
   tcp recv from agent :    {AGENT_RETURN_CODE:0, AGENT_MESSAGE:"shutting down agent"}

   --- Bad TA Command
   tcp send from client:    TA:qwert
   tcp recv from agent :    {AGENT_RETURN_CODE:201, AGENT_MESSAGE:"UNKNOWN TA COMMAND: qwert"}

Agent Return Codes:
     0 - Successful execution of command
   200 - Unknown Directive
   201 - Unknown TA Command
   220 - Unable to process OS Command
   255 - Invalid message format

The OS directive is a command that is intended to be executed on the
operating where the agent is running. The OS directive returns a
Python dictionary with six key-value pairs in it:

   {  AGENT_RETURN_CODE  : int    ,
	  AGENT_MESSAGE      : string ,
	  OS_COMMAND         : string ,
	  OS_STDOUT          : string ,
	  OS_STDERR          : string ,
      OS_RETURNCODE      : int	  }

The command supplied along with the OS directive will be invoked as the
same user that the agent is running as. However, if necessary there are
methods for privilege escalation.

Examples:

   --- OS uname command
       Note: output and errors string may have line breaks
   tcp send from client:    OS:uname
   tcp recv from agent :    { "AGENT_RETURN_CODE" : 0       ,
                              "AGENT_MESSAGE"     : ""      ,
	                          "OS_COMMAND"        : "uname" ,
	                          "OS_STDOUT"         : "Linux" ,
	                          "OS_STDERR"         : ""      ,
                              "OS_RETURNCODE"     : 0       }



   --- OS ps command
   tcp send from client:    OS:ps -a | grep python
   tcp recv from agent :    { "AGENT_RETURN_CODE" : 0                                ,
                              "AGENT_MESSAGE"     : ""                               ,
	                          "OS_COMMAND"        : "ps -a | grep python"            ,
	                          "OS_STDOUT"         : "14074 pts/2    00:00:00 python" ,
	                          "OS_STDERR"         : ""                               ,
                              "OS_RETURNCODE"     : 0                                }

   --- OS Bad command
   tcp send from client:    OS:Qwert
   tcp recv from agent :    { "AGENT_RETURN_CODE" : 0                                    ,
                              "AGENT_MESSAGE"     : ""                                   ,
	                           "OS_COMMAND"       : "Qwert"                              ,
	                           "OS_STDOUT"        : ""                                   ,
	                           "OS_STDERR"        : "/bin/sh: Qwert: command not found"  ,
                              "OS_RETURNCODE"     : 127                                  }

To connect to an agent using the Python Programming language see the
example below

# --- PROGRAM STARTS HERE ------------------------------------------------------
from socket import socket                  # The Socket library
from socket import AF_INET, SOCK_STREAM    # Specific constants from socket
from sys    import exit                    # Import the exit function
AGENT_IP    = "localhost"                  # The Agent IP Address
AGENT_PORT  = 1100                         # The Agent Port number
BUFFER      = 14336 # 14k                  # The size of the TCP Buffer
tcpSocket = socket(AF_INET, SOCK_STREAM)   # Create an object of type socket
tcpSocket.connect((AGENT_IP,AGENT_PORT))   # Establish a connection
tcpSocket.send("TA:version")               # Send the TA:version command
response = tcpSocket.recv(BUFFER)          # Get the response from the agent
print response                             # Print the response
tcpSocket.send("TA:bye")                   # End the session with the agent
response = tcpSocket.recv(BUFFER)          # Get the closing notice
print response                             # Print the closing response
exit(0)                                    # clean exit
# --- PROGRAM ENDS HERE --------------------------------------------------------

Any TCP AF_INET SOCKET_STREAM connections are accepted by the Agent
regardless of language used. Please refer to the documentation for your
specific language to establish a TCP AF_INET, SOCKET_STREAM connection

Please be sure to end your session with the agent using either:

   TA:bye
   or
   TA:quit

commands.
                                                                           Q.E.D
"""

# ==============================================================================
# STANDARD LIBRARY IMPORTS
import sys
import os
import socket
import time
import getopt
import subprocess
from thread import start_new_thread

# ==============================================================================
# GLOBALS
VERSION       = "1.1.0"  # Version of the agent
DEBUG         = False  # Flag for debug operation
VERBOSE       = False  # Flag for verbose operation
FIRST         = 0  # first element in a list
LAST          = -1  # last element in a list
ME            = os.path.split(sys.argv[FIRST])[LAST]  # Name of this file
MY_PATH       = os.path.dirname(os.path.realpath(__file__))  # Path for this file
FOR_READING   = 'r'  # \
FOR_WRITING   = 'w'  # > -- File I/O modes
FOR_APPENDING = 'a'  # /
INFO          = 1  # \
WARN          = 2  # > -- Log Level definitions
ERROR         = 3  # /
HOST          = '192.168.1.129'  # address/hostname for the agent
PORT          = 1100  # Port number for the agent
BUF_SIZE      = 14336  # 14k                    # Size of the TCP comm. buffer
ADDRESS       = (HOST, PORT)  # Agent socket
LOGGING       = False  # Flag for logging
LOG_FILE      = ME + ".log"  # Log file name
PAUSE_PROMPT  = "Press <Enter> to continue."  # Pause prompt text
EXIT_SUCCESS  = 0  # Exit code
USER          = "Unknown"  # User the agent is running as
AGENT_NAME    = "NO_NAME"  # Name of the agent
AGENT_RETURN_CODE = "AGENT_RETURN_CODE"  # \
AGENT_MESSAGE     = "AGENT_MESSAGE"      #  \
OS_COMMAND        = "OS_COMMAND"         #   \__ Response key names used in
OS_STDOUT         = "OS_STDOUT"          #   /   the response dictionary
OS_STDERR         = "OS_STDERR"          #  /
OS_RETURNCODE     = "OS_RETURNCODE"      # /
closeSocketPause   = 3  # Time in seconds to wait for the socket to close cleanly
helpMessage = """
Agent commands must be of the form TA:command or OS:command.

Valid TA commands are: help, version, exit, quit, bye, or shutdown
Valid OS commands depend on the Angent's operating system."" 
"""

# =============================================================================
# CLASSES
# ==================================================================== Command()
class Command:

    # --------------------------------------------------------- Command.__init__()
    def __init__(self, command):
        """ Creates an instance of an object of type Command. """
        self.command    = str(command).strip()    # The command to execute
        self._stdout    = subprocess.PIPE         # Standard Output PIPE
        self._stderr    = subprocess.PIPE         # Standard Error PIPE
        self.output     = "Command not executed"  # Output from command
        self.error      = "Command not executed"  # Error from command
        self.returnCode = 127                     # Return code from command

    # ------------------------------------------------------------- Command.run()
    def run(self):
        """ Executes the command in the specified shell. """
        try:
            results = subprocess.Popen(self.command,
                                       stdout=self._stdout,
                                       shell=True,
                                       stderr=self._stderr)  # Execute the command
            self.output, self.error = results.communicate()  # Get output and error
            self.returnCode = results.returncode  # Get Return Code
        except Exception as e:
            self.output = str(e)
            self.error = "Unable to execute: \"%s\"" % self.command
            self.returnCode = 113

    # ----------------------------------------------------- Command.showResults()
    def showResults(self):
        """ Prints original command and resutls to stdout. """
        print "COMMAND     : \"%s\"" % self.command
        print "OUTPUT      : \"%s\"" % self.output.strip()
        print "ERROR       : \"%s\"" % self.error.strip()
        print "RETURN CODE : %d" % self.returnCode

        # ---------------------------------------------------- Command.returnResuls()

    def returnResults(self):
        """ Returns a dictionary containing the original command  and results. """
        results = {"command": self.command.strip(),
                   "output": self.output.strip(),
                   "error": self.error.strip(),
                   "returnCode": self.returnCode}
        return results

    # ==================================================================== Logger()


class Logger:

    """ Rolling my own Logger for ... reasons """

    # --------------------------------------------------------- Logger.__init__()
    def __init__(self, logFile):
        """ Creates an instance of an object of type Logger. """
        self.logPathFile      = str(logFile).strip()                         # Log path and file name
        self.logFile          = os.path.split(self.logPathFile)[LAST]        # Log file name only
        self.logPath          = os.path.split(self.logPathFile)[FIRST]       # Log path only
        self._infoLevel       = 1                                            # Info level entry
        self._warnLevel       = 2                                            # warning level entry
        self._errorLevel      = 3                                            # error level entry
        self._infoString      = "INFO"                                       # log text for information
        self._warnString      = "WARN"                                       # log text for warning
        self._errorString     = "ERROR"                                      # log text for error
        self._logEntrySep     = ", "                                         # log entry separator
        dateString            = "%Y-%b-%d"                                   # Date format string
        timeString            = "%H:%M:%S"                                   # Time format string
        self._timestampFormat = dateString + self._logEntrySep + timeString  # log text timestamp format
        self.valid            = False                                        # is the log file valid
        # - - - - - - - - - - - - - - - - - - - - - - - -
        self._createLogFolder()
        self._createLogFile()

    # ------------------------------------------------- Logger.createLogFolder()
    def _createLogFolder(self):
        """ If necessary, create the folder for the log file. If the folder cannot
            be created, then empty the string self.logPath. An empty string for the
            self.logPath indicates an error condition in the logging object."""
        if len(self.logPath) > 0:  # Check to see if a path was given
            if not os.path.exists(self.logPath):  # Check to see if the path exists
                try:
                    os.makedirs(self.logPath)
                except:
                    self._showError("Unable to create folder \"%s\"" % self.logPath)
                    self.logPath = ""
        else:
            # If no path was given, assume the path is the current working folder.
            # Don't forget to rebuild self.logPathFile
            self.logPath = os.path.dirname(os.path.realpath(__file__))
            self.logPathFile = os.path.join(self.logPath, self.logFile)

    # ---------------------------------------------------- Logger.createLogFile()
    def _createLogFile(self):
        """ If necessary, create the log file if and only if there is a defined
              self.logPath.  is the log path is empty then do not create the
            log file as this is an indication of a folder that does not exist
               and could not be crated. """
        if len(self.logPath) > 0:
            try:
                f = open(self.logPathFile, FOR_APPENDING)
                f.close()
                self.valid = True
            except:
                self._showError("Unable to write to the log file \"%s\"" % self.logFile)

    # ------------------------------------------------------- Logger._showError()
    def _showError(self, message):
        """ writes error message to stderr"""
        message = str(message)
        sys.stderr.write("\n\nLogger ERROR -- %s\n\n" % message)
        sys.stderr.flush()

    # ------------------------------------------------------------- Logger._now()
    def _now(self):
        """ returns a consistent time stamp """
        if DEBUG: print self._timestampFormat
        return time.strftime(self._timestampFormat, time.localtime())

    # ------------------------------------------------------------ Logger.logit()
    def logit(self, message, level=1):
        """logIt(message, optional level) Writes an ertry to a log file.
           Log level vaules are: 1=INFO, 2=WARNING, 3=ERROR.
           By default all log entries are INFO. """
        if self.valid:
            entry = self._now() + self._logEntrySep
            if level == self._infoLevel:
                entry = entry + self._infoString + self._logEntrySep
            elif level == self._warnLevel:
                entry = entry + self._warnString + self._logEntrySep
            elif level == self._errorLevel:
                entry = entry + self._errorString + self._logEntrySep
            else:
                entry = entry + "GOK" + self._logEntrySep  # God only knows
            entry = entry + str(message) + os.linesep
            try:
                log = open(self.logFile, FOR_APPENDING)
                log.write(entry)
                log.close()
            except Exception as e:
                self.showError("Unable to write to log file \"%s\"\n%s" % (self.logPathFile), str(e))
        else:
            self._showError("Log file \"%s\" is not valid" % self.logPathFile)

    # ------------------------------------------------------------ Logger.reset()
    def reset(self):
        if self.valid:
            try:
                os.remove(self.logPathFile)
                self.valid = False
            except Exceptions as e:
                self._showError("Unable to reset the log file \"%s\"" % self.logPathFile)
            if self.valid: self.logit("Log file reset")

# === End of class Logger =====


# ==============================================================================
# NATIVE FUNCTIONS
#    This section holds all of the functions used by the script.

# ---------------------------------------------------------------------- usage()
def usage():
    """usage() - Prints the usage message on stdout. """
    print "\n\n%s, Version %s, This is a Remote Agent.              " % (ME, VERSION)
    print "\nUSAGE: %s [OPTIONS]                                    " % ME
    print "                                                         "
    print "OPTIONS:                                                 "
    print "   -h --help      Display this message.                  "
    print "   -v --verbose   Runs the program in verbose mode, default: %s. " % VERBOSE
    print "   -d --debug     Runs the program on debug mode (implies verbose). "
    print "   -p --port=     The TCP port number for the listener, default: %s " % PORT
    print "   -a --address=  The TCP address for the listener, default: %s " % HOST
    print "   -l --logging   Enables logging, default=%s, logfile=%s  " % (LOGGING, LOG_FILE)
    print "   -b --buffer=   The size of the TCP comm. buffer, default: %d " % BUF_SIZE
    print "                                                         "
    print "EXIT CODES:                                              "
    print "    0 - Successful completion of the program.            "
    print "    1 - Cannot import this script as a module.           "
    print "    2 - Bad command line arguments.                      "
    print "    3 - Bad port, must be a an integer                   "
    print "    4 - Bad port, must be between 1025-65534 inclusive   "
    print "    5 - Bad address, must be a string                    "
    print "    6 - Bad buffer, must be etween 1025-65534 inclusive "
    print "                                                         "
    print "EXAMPLES:                                                "
    print "    TODO - I'll make some examples up later.             "
    print "                                                         "


# ----------------------------------------------------------------------------- pause()
def pause():
    """pause() Holds script execution until the user responds. """
    raw_input(PAUSE_PROMPT)
    return

# ----------------------------------------------------------------------------- now()
def now():
    """now() returns a timestamp string of the form "YYYY-MM-DD, HH:MM:SS"  """
    return time.strftime("%Y-%b-%d, %H:%M:%S", time.localtime())

# ----------------------------------------------------------------------------- showError()
def showError(message):
    """showError(str message) write error message to stderr"""
    message = str(message)
    sys.stderr.write("\n\nERROR -- %s\n\n" % message)
    sys.stderr.flush()
    return


# ----------------------------------------------------------------------------- showWarning()
def showWarning(message):
    """showWarning(str message) write error message to stderr"""
    message = str(message)
    sys.stderr.write("\n\nWARNING -- %s\n\n" % message)
    sys.stderr.flush()
    return


# ----------------------------------------------------------------------------- showMessage()
def showMessage(message):
    message = str(message)
    sys.stdout.write("\n%s\n" % message)
    sys.stdout.flush()
    return


# ----------------------------------------------------------------------------- build_TA_Response()
def build_TA_Response(taCode, taMessage):
    response = {}
    try:
        response[AGENT_RETURN_CODE] = int(taCode)
        response[AGENT_MESSAGE] = str(taMessage)
    except:
        response = {AGENT_RETURN_CODE: 99,
                    AGENT_MESSAGE: "Unable to process Test Agent Directive"}
    return response


# ----------------------------------------------------------------------------- build_OS_Response()
def build_OS_Response(taCode, taMessage, osCommand, osOutput, osError, osReturncode):
    response = {}
    try:
        response[AGENT_RETURN_CODE] = int(taCode)
        response[AGENT_MESSAGE] = str(taMessage)
        response[OS_COMMAND] = str(osCommand)
        response[OS_STDOUT] = str(osOutput)
        response[OS_STDERR] = str(osError)
        response[OS_RETURNCODE] = int(osReturncode)
    except:
        response = {AGENT_RETURN_CODE: 99,
                    AGENT_MESSAGE: "Unable to process Operating System Directive"}
    return response


# ==============================================================================
# MAIN
if __name__ == "__main__":

    # --- Get my Username -------------------------------------------------------
    USER = "Unknown"
    try:
        USER = os.environ["USER"]  # Most Linux systems
    except:
        try:
            USER = os.environ["USERNAME"]  # Windows
        except:
            pass  # if reached => USER = "Unknown"

    # --- Process command line arguments ----------------------------------------
    try:
        arguments = getopt.getopt(sys.argv[1:],
                                  "hvdp:a:lb:",
                                  ['help',
                                   'verbose',
                                   'debug',
                                   'port=',
                                   'address=',
                                   'logging',
                                   'buffer='])
    except:
        showError("Bad command line argument(s)")
        usage()
        sys.exit(2)
        # --- Check for a help option
    for arg in arguments[0]:
        if arg[0] == "-h" or arg[0] == "--help":
            usage()
            sys.exit(EXIT_SUCCESS)
    # --- Check for a verbose option
    for arg in arguments[0]:
        if arg[0] == "-v" or arg[0] == "--verbose":
            VERBOSE = True
            # --- Check for a logging option
    for arg in arguments[0]:
        if arg[0] == "-l" or arg[0] == "--logging":
            LOGGING = True

            # --- Check for a debug option
    for arg in arguments[0]:
        if arg[0] == "-d" or arg[0] == "--debug":
            DEBUG = True
            VERBOSE = True
    # --- Check for a "port" or "-p" option
    for arg in arguments[0]:
        if arg[0] == "-p" or arg[0] == "--port":
            try:
                tryPort = int(arg[1])
            except:
                message = "Invalid port specified \"%s\", port must be an integer." % tryPort
                showError(message)
                usage()
                sys.exit(3)
            if tryPort < 65535 and tryPort > 1024:
                PORT = tryPort
            else:
                message = "Invalid port number specified \"%s\", port must be between 1025 and 65534." % tryPort
                showError(message)
                usage()
                sys.exit(4)
                # --- Check for an "address" or "-a" option
    for arg in arguments[0]:
        if arg[0] == "-a" or arg[0] == "--address":
            try:
                tryAddress = str(arg[1])  # Sanity check
                socket.inet_aton(tryAddress)  # valid IPV4 address check
                HOST = tryAddress  # Looks good, let's use it
            except:
                message = "Invalid address specified \"%s\", address must be a string." % tryPort
                showError(message)
                usage()
                sys.exit(5)
                # --- Check for a "--buffer" or "-b" option
    for arg in arguments[0]:
        if arg[0] == "-b" or arg[0] == "--buffer":
            try:
                tryBuffer = int(arg[1])
            except:
                message = "Invalid buffer specified \"%s\", port must be an integer." % tryBuffer
                showError(message)
                usage()
                sys.exit(6)
            if tryBuffer < 65535 and tryBuffer > 1024:
                BUF_SIZE = tryBuffer
            else:
                message = "Invalid buffer size specified \"%s\", buffer must be between 1025 and 65534." % tryBuffer
                showError(message)
                usage()
                sys.exit(6)

                # --- Initialize the Log file
    log = Logger(LOG_FILE)
    # --- Display operating parameters
    if DEBUG:
        # TODO: Clean this up to support Python 3
        print "--------------- PARAMETERS ---------------"
        print "Program name is                  %s" % ME
        print "Program running as user          %s" % USER
        print "Program started at               %s" % now()
        print "Program started on               %s" % HOST
        print "Program started in               %s" % MY_PATH
        print "Program configured for port      %s" % PORT
        print "Program logging                  %s" % LOGGING
        print "Program Buffer                   %s" % BUF_SIZE
        pause()

    # --- Program opens ---------------------------------------------------------
    message = "%s started on %s in %s as %s" % (ME, HOST, MY_PATH, USER)
    if VERBOSE: showMessage(message)
    if LOGGING: log.logit(message)
    if DEBUG: pause()
    # --- Listener Loop ---------------------------------------------------------
    try:
        message = "Starting listener on %s:%d" % (HOST, PORT)
        if VERBOSE: showMessage(message)
        if LOGGING: log.logit(message)
        listenerSocket = (HOST, PORT)
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            tcpSocket.bind(listenerSocket)
            tcpSocket.listen(5)
            if VERBOSE: showMessage("Listener started!")
        except socketError, e:
            message = "Test Agent unable to bind to %s:%s - " % (HOST, str(PORT))
            message += "%s" % str(e[1])
            showError(message)
            if LOGGING:
                logit(message)
            exit(6)  # Exit with 6 for "Unable to bind test_agent to host:port"

        # --------------------------------------------------------- Listener Loop
        # Listener loop starts here.
        #
        listenerRunning = True
        while listenerRunning:
            message = "Waiting for a connection ..."
            if VERBOSE: showMessage(message)
            if LOGGING: log.logit(message)
            connection, remoteAddr = tcpSocket.accept()
            message = "Connection from: %s" % str(remoteAddr)
            if VERBOSE: showMessage(message)
            if LOGGING: log.logit(message)
            sessionActive = True
            while sessionActive:

                data = connection.recv(BUF_SIZE)
                data = data.strip()
                message = "Message from %s: %s" % (str(remoteAddr), data)
                if VERBOSE: showMessage(message)
                if LOGGING: log.logit(message)

                # --- Check message from client and see if it is in form:
                #     DIRECTIVE:COMMAND
                messageParts = data.split(':', 1)
                if len(messageParts) != 2:
                    response = build_TA_Response(98, "Invalid message")
                    if VERBOSE: showMessage("Sending: %s" % str(response))
                    if LOGGING: log.logit("Sending: %s" % str(response))
                    connection.send(str(response))
                else:
                    # --- Parse out and clean up the directive and command
                    directive = messageParts[FIRST]
                    directive = directive.strip()
                    directive = directive.upper()
                    command = messageParts[LAST]
                    command = command.strip()
                    # --- Process directives and commands

                    if directive == "TA":
                        #
                        #    *** **************************** ***
                        #    *** TA DIRECTIVES PROCESSED HERE ***
                        #    *** **************************** ***
                        #
                        # ------------------------------------------------- TA:VERSION
                        if command == "version":
                            response = build_TA_Response(0, "VERSION %s" % VERSION)
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))
                        # ----------------------------------------------------- TA:BYE
                        elif command == "bye" or command == "quit" or command == "exit":
                            response = build_TA_Response(0, "CLOSING CONNECTION")
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))
                            time.sleep(closeSocketPause)
                            connection.close()
                            sessionActive = False  # Flag end of session
                        # ------------------------------------------------ TA:SHUTDOWN
                        elif command == "shutdown" or command == "SHUTDOWN":
                            response = build_TA_Response(0, "SHUTTING DOWN AGENT")
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))
                            time.sleep(closeSocketPause)
                            connection.close()
                            sessionActive = False  # Flag end of session
                            listenerRunning = False  # Flag end of listener Loop
                        # ------------------------------------------------- TA:GETNAME
                        elif command == "getname" or command == "GETNAME":
                            if VERBOSE: showMessage("sending name: %s" % AGENT_NAME)
                            connection.send("[0, \"%s\"]" % AGENT_NAME)
                        elif command.find("setname") > -1:
                            if command.find('=') > -1:
                                parts = command.split('=')
                                if len(parts) != 2:
                                    connection.send(
                                        "[2, \"Bad TA:setname - must have a name after the \'=\' operator\"]")
                                else:
                                    agentName = parts[LAST]
                                    agentName = agentName.strip()
                                    AGENT_NAME = agentName
                                    if VERBOSE: showMessage("Agent Name set to \"%s\"" % AGENT_NAME)
                                    connection.send("[0, \"Agent Name set to \'%s\'\"]" % AGENT_NAME)
                            else:
                                connection.send("[1, \"TA:setname requires an assignment using \'=\'\"]")
                            pass
                            # --------------------------------------------- TA:GETUSERNAME
                        elif command == "getusername" or command == "GETUSERNAME":
                            if VERBOSE:
                                showMessage("Sending \"%s\"" % USER)
                            connection.send("[0, \"%s\"]" % USER)
                            # ----------------------------------------------- TA:LOCALTIME
                        elif command == "localtime" or command == "LOCALTIME":
                            timestamp = now()
                            response = build_TA_Response(0, timestamp)
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))
                        # ----------------------------------------------- TA:LOCALTIME
                        elif command == "help" or command == "HELP":
                            message = "Valid TA Commands are: version, localtime, bye, shutdown, help"
                            response = build_TA_Response(0, message)
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))
                        # --------------------------------------------- TA:BAD COMMAND
                        else:
                            message = "Unknown TA Command \"%s\"" % command
                            response = build_TA_Response(97, message)
                            if VERBOSE: showMessage("Sending: %s" % str(response))
                            if LOGGING: log.logit("Sending: %s" % str(response))
                            connection.send(str(response))

                    elif directive == "OS":
                        #
                        #    *** **************************** ***
                        #    *** OS DIRECTIVES PROCESSED HERE ***
                        #    *** **************************** ***
                        #
                        # ------------------------------------------------- OS:COMMAND
                        if VERBOSE: showMessage("OS Command \"%s\"" % command)
                        c = Command(command)
                        c.run()
                        results = c.returnResults()
                        response = build_OS_Response(0,
                                                     "",
                                                     results["command"],
                                                     results["output"],
                                                     results["error"],
                                                     results["returnCode"])
                        if VERBOSE: showMessage("Sending: %s" % str(response))
                        if LOGGING: log.logit("Sending: %s" % str(response))
                        connection.send(str(response))

                    elif directive == "HELP" or directive == "help":
                        #
                        #    *** ****************************** ***
                        #    *** HELP DIRECTIVES PROCESSED HERE ***
                        #    *** ****************************** ***
                        #
                        message = "[0, \"%s\"]" % helpMessage
                        response = build_TA_Response(0, helpMessage)
                        if VERBOSE: showMessage("Sending: %s" % str(response))
                        if LOGGING: log.logit("Sending: %s" % str(response))
                        connection.send(message)


                    else:
                        #
                        #    *** ********************************* ***
                        #    *** UNKNOWN DIRECTIVES PROCESSED HERE ***
                        #    *** ********************************* ***
                        #
                        if VERBOSE: showMessage("Sending Unknown Directive")
                        connection.send("[200, \"UNKNOWN DIRECTIVE: %s\"]" % directive)

        # --------------------------------------------------- End of Listener Loop
        #
        # Shutting down the Agent on a shutdown command
        message = "Shutting down agent ..."
        if VERBOSE: showMessage(message)
        if LOGGING: log.logit(message)


    except  KeyboardInterrupt:
        # Close the socket on Control C
        #TODO: Clean this up to support Python 3
        print "\n\n\n"
        print "*** ******************** ***"
        print "*** Caught <Control>-<C> ***"
        print "*** ******************** ***"
        print ""
        print "Closing listener ..."
        if LOGGING: log.logit("Caught <Control>-<C>")

        # --- Close the Listener Socket
    message = "Closing the listener socket..."
    if VERBOSE: showMessage(message)
    if LOGGING: log.logit(message)
    time.sleep(closeSocketPause)
    tcpSocket.close()
    message = "Closed listener socket"
    if VERBOSE: showMessage(message)
    if LOGGING: log.logit(message)

    # --- Program closes --------------------------------------------------------
    message = "%s terminated with exit code %d" % (ME, EXIT_SUCCESS)
    if LOGGING: log.logit(message)
    if VERBOSE: showMessage(message)
    exit(EXIT_SUCCESS) # I miss programming in C

else:
    exit(1)
