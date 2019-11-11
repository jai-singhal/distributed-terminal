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
PORT = 8074

class Client(object):
    def __init__(self, port:int = PORT):
        self.port = port

    @staticmethod
    def popen_timeout(command:str, timeout:int):
        p = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        for t in range(timeout):
            if p.poll() is not None:
                return p.communicate()
            sleep(0.1)
            
        p.kill()
        return (False, False)

    def handlePipelineCommands(self, command:str):
        data_b64 = ""
        for sub_cmnd in command.split("||"):
            sub_cmnd = sub_cmnd.strip()
            ip_cmd = sub_cmnd.split(">", 1)

            if not re.search(r"[0-9a-z\.]+[ ]*\>[ ]*.+", sub_cmnd):
                print(CRED + "Invalid command. Try using IP>cmd")
                print(CWHITE2)
                return None

            ip, cmd = ip_cmd[0], ip_cmd[1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((ip.strip(), PORT))
            except:
                print(CRED + "Unable to connect to: \'{}\'. Try again".format(ip))
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


    def handleBasicCommands(self, command):
        ip_cmd = command.split(">", 1)
        ip, cmd = ip_cmd[0], ip_cmd[1]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip.strip(), PORT))
        except:
            print(CRED + "Unable to connect to: \'{}\'. Try again".format(ip))
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

    def decorateTerminal(self):
        currpath, err = self.popen_timeout("pwd", 2)
        if not currpath:
            print("Unable to connect")
            sys.exit()
        if not err:
            currpath = re.sub(r"[\n]", "", currpath.decode("utf-8"))
            hostname = socket.gethostname() 
            IPAddr = socket.gethostbyname(hostname) 
            print(CGREEN + f"{hostname}@{IPAddr}:", end = "")
            print(CBLUE2 + "~" + currpath, end = "")
            print(CRED + "(*)")

        print(CBEIGE2 + "> ", end="")
        print(CWHITE2, end="")
        
    def start(self):
        os.system('clear')
        while True:
            self.decorateTerminal()
            try:
                command = input()
            except KeyboardInterrupt:
                return
                
            if not command:
                continue
            if not re.search(r"[0-9a-z\.]+[ ]*\>[ ]*.+", command):
                print(CRED + "Invalid command. Try using IP>cmd")
                continue
            if "||" in command:
                res = self.handlePipelineCommands(command)
            else:
                res = self.handleBasicCommands(command)
            if not res:
                continue
            else:
                print(res)


if __name__ == "__main__":
    client = Client()
    client.start()

# // 172.17.48.146