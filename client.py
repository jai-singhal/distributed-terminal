#!/usr/bin/env python
# client.py
__author__ = "Jai Singhal"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0"
__maintainer__ = "Jai Singhal"
__email__ = "jaisinghal48@gmail.com"
__website__ = "http://jai-singhal.github.io"

import socket
import re
import os
import sys
import subprocess
import base64
from time import sleep

CRED = '\033[91m'
CGREEN  = '\33[32m'
CBLUE2   = '\33[94m'
CBEIGE2  = '\33[96m'
CWHITE2  = '\33[97m'

PORT = 40150

class Client(object):
    """
    Client Class
    """
    def __init__(self, port:int = PORT):
        self.port = port

    def handlePipelineCommands(self, command:str):
        """
        Handle (||) Commands
        Args: string  of command which to be run and pvs output
         which is going to passed as input in this command
        Returns dict of stdout and stderr if success
        """
        data_b64 = ""
        for sub_cmnd in command.split("||"):
            sub_cmnd = sub_cmnd.strip()
            ip_cmd = sub_cmnd.split(">", 1)

            if not re.search(r"[0-9a-z\.]+[ ]*\>[ ]*.+", sub_cmnd):
                print(CRED + "Invalid command. Try using IP>cmd\n")
                print(CWHITE2)
                return None

            ip, cmd = ip_cmd[0].strip(), ip_cmd[1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((ip.strip(), self.port))
            except Exception as e:
                print(CRED + "Unable to connect to: \'{}\'. Try again".format(ip))
                print(e)
                print(CWHITE2)
                return None
            toSend = {
                "pvs_stdin": data_b64,
                "cmd": cmd.strip()
            }
            base64_dict = base64.b64encode(str(toSend).encode('utf-8'))
            sock.sendall(base64_dict)
            data = sock.recv(40800)
            sock.close()
            if data:
                data_b64 = eval(base64.b64decode(data))
                if data_b64["error"]:
                    return data_b64["error"].decode("utf-8")
                else:
                    data_b64 = data_b64["output"]
        return data_b64.decode("utf-8")


    def handleBasicCommands(self, command:str):
        """
        Handle Basic Non Pipe Commands
        Args: command(str) Command which to be run
        Returns dict of stdout and stderr if success
        """
        ip_cmd = command.split(">", 1)
        ip, cmd = ip_cmd[0].strip(), ip_cmd[1]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip.strip(), self.port))
        except Exception as e:
            print(CRED + "Unable to connect to: \'{}\'. Try again".format(ip))
            print(e)
            print(CWHITE2)
            return None
        
        toSend = {
            "pvs_stdin": "".encode(),
            "cmd": cmd.strip()
        }
        base64_dict = base64.b64encode(str(toSend).encode('utf-8'))
        sock.sendall(base64_dict)
        data = sock.recv(40800)
        sock.close()
        if data:
            data_b64 = eval(base64.b64decode(data))
            if data_b64["error"]:
                return data_b64["error"].decode("utf-8")
            else:
                return data_b64["output"].decode("utf-8")
        return str()

    @staticmethod
    def get_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    def decorateTerminal(self):
        """
        Utility function that prints the host and ip, also
        the poth at which currently
        """
        hostname = socket.gethostname() 
        try:
            IPAddr = self.get_ip_address()
        except:
            IPAddr = socket.gethostbyname(hostname)
            
        print(CGREEN + f"{hostname}@{IPAddr}", end = "")
        print(CWHITE2 + ":", end="")
        print(CBLUE2 + "~/", end = "")
        print(CWHITE2 + "$ ", end = "")
        print(CWHITE2, end="")
        
    def start(self):
        """
        Driver function of the Client class.
        Takes the input from user(command),checks for
        which type of input, and executes it.
        """
        os.system('clear')
        while True:
            self.decorateTerminal()
            try:
                command = input()
            except KeyboardInterrupt:
                print("\n Client: Keyboard Interrupt".capitalize())
                return
                
            if not command: continue

            if not re.search(r"[0-9a-z\.]+[ ]*\>[ ]*.+", command):
                print(CRED + "Invalid command. Try using IP>cmd\n")
                continue
            if "||" in command:
                res = self.handlePipelineCommands(command)
            else:
                res = self.handleBasicCommands(command)

            if not res: continue
            else: print(res)


if __name__ == "__main__":
    client = Client(PORT)
    client.start()
