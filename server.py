#!/usr/bin/env python
# server.py
__author__ = "Jai Singhal"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0"
__maintainer__ = "Jai Singhal"
__email__ = "jaisinghal48@gmail.com"
__website__ = "http://jai-singhal.github.io"


import multiprocessing
import socket
import subprocess
import re
import os
import sys
import logging
from time import sleep
import base64
import threading

PORT = 40150

class LinuxCommandExecuter(object):

    def __init__(self):
        pass

    # @staticmethod
    # def popen_timeout(command:list, timeout:int):
    #     """
    #     Runs the linux command until the timeout
    #     Args: command: list of command and option
    #           timeout: timeout time for command
    #     Returns tuple of stdout and stderr
    #     """
    #     p = subprocess.Popen(
    #         command, 
    #         stdout=subprocess.PIPE, 
    #         stderr=subprocess.PIPE
    #     )
    #     for t in range(timeout):
    #         if p.poll() is not None:
    #             return p.communicate()
    #         sleep(0.1)
    #     p.kill()
    #     logging.exception("Unable to run the command: " + " ".join(command))
    #     return (False, False)

    # @staticmethod
    # def popen_stdin_timeout(command:str, timeout:int):
    #     """
    #     Runs the linux Pipe(|) command using Popen until the
    #     timeout, seperated from basic command because the output 
    #     is to be maintained after running each sub command

    #     Args: command: string of command and options
    #           timeout: timeout time for command
    #     Returns tuple of stdout and stderr if success
    #         else return Tuple of (False, False)
    #     """

    #     subcmnds = command.split("|")
    #     p1 = subprocess.Popen(
    #         subcmnds[0].split(),
    #         stdout=subprocess.PIPE,
    #     )
    #     pvs_stdin = p1.stdout
    #     for subcmd in subcmnds[1:]:
    #         p2 = subprocess.Popen(
    #             subcmd.split(),
    #             stdin=pvs_stdin,
    #             stdout=subprocess.PIPE,
    #         )
    #         pvs_stdin = p2.stdout
    #     for t in range(timeout):
    #         if p2.poll() is not None:
    #             return p2.communicate()
    #         sleep(0.1)
    #     p2.kill()
    #     logging.exception("Unable to run the command: " + " ".join(command))
    #     return (False, False)

    @staticmethod
    def subprocess_run(command:str, input_stdin:str = None):
        try:
            p = subprocess.Popen(
                    command.split(), 
                    stdin = subprocess.PIPE,
                    encoding="utf-8",
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    # timeout=1
                )

            if input_stdin is not None:
                p.stdin.write(input_stdin)
            for t in range(30):
                if p.poll() is not None:
                    return p.communicate()
                sleep(0.1)
            p.kill()
        except Exception as e:
            return (False, str(e))      

    def run_nonpipe_command(self, command: str, pvs_stdin: str =  None):
        """
        Runs the linux command using Run  until the timeout.

        Args: command(dict): dict of command and options, and
                previous command which use as input to it
              timeout: timeout time for command
        Returns tuple of stdout and stderr if success
            else return Tuple of (False, error)
        """
        try:
            return self.subprocess_run(command, pvs_stdin)
        except Exception as e:
            logging.exception("Unexpected exception: run_nonpipe_command")
            logging.exception(str(e))
            return (False, str(e))
        
    def run_pipe_command(self, command: str, pvs_stdin: str =  None):
        """
        Runs the linux Pipe(|) command using Popen until the
        timeout, seperated from basic command because the output 
        is to be maintained after running each sub command

        Args: command(dict): dict of command and options, and
                previous command which use as input to it
              timeout: timeout time for command
        Returns tuple of stdout and stderr if success
            else return Tuple of (False, False)
        """
        subcmnds = command.split("|")
        try:
            pvs_stdin = None
            for subcmd in subcmnds:
                if isinstance(pvs_stdin, bytes):
                    pvs_stdin = pvs_stdin.decode("utf-8")
                pvs_stdin, p_error = self.subprocess_run(subcmd.strip(), pvs_stdin)
                print(pvs_stdin, p_error)
                if not pvs_stdin: return False, p_error
            return pvs_stdin, p_error
        except Exception as e:
            logging.exception("Unexpected exception: run_pipe_command")
            logging.exception(str(e))
            return (False, str(e))


    def handleNonPipelineCommand(self, cmd_in:str):
        """
        Handle Basic Non Pipe Commands
        Args: command(str) Command which to be run
        Returns dict of stdout and stderr if success
        """
        if re.match(r"cd .+", cmd_in):
            try:
                os.chdir(cmd_in.split(" ", 1)[1])
                return {"output": "".encode(), "error": "".encode()}
            except OSError as e:
                return {"output": "".encode(), "error": str(e).encode()}

        if "|" in cmd_in:
            try:
                out, err = self.run_pipe_command(cmd_in)
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: popen")
                logging.exception(err)
        else:
            try:
                out, err = self.run_nonpipe_command(cmd_in)
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: popen")
                logging.exception(err)
        if err:
            if isinstance(err, str):
                return {"output": "", "error": err.encode()}
            else:
                return {"output": "", "error": err}

        if isinstance(out, str): out = out.encode()

        return {"output": out, "error": "".encode()}


    def handlePipelineCommand(self, command:str, pvs_stdin:str):
        """
        Handle (||) Commands
        Args: command(dict) Command which to be run and pvs output
         which is going to passed as input in this command
        Returns dict of stdout and stderr if success
        """
        if "|" in command:
            try:
                out, err = self.run_pipe_command(command, pvs_stdin)
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: run_stdnin")
        else:
            try:
                out, err = self.run_nonpipe_command(command, pvs_stdin)
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: run_stdnin")
        if err:
            if isinstance(err, str):
                return {"output": "", "error": err.encode()}
            else:
                return {"output": "", "error": err}

        if isinstance(out, str):
            out = out.encode()

        return {"output": out, "error": "".encode()}


class Server(LinuxCommandExecuter):
    """
    Server Class inherits LinuxCommandExecuter
    """
    def __init__(self, hostname, port):
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port
        logging.basicConfig(
            filename='server.log', 
            filemode='w',
            format='%(name)s - %(levelname)s - %(message)s',
            level=logging.DEBUG
        )

    @staticmethod
    def recvall(sock):
        BUFF_SIZE = 2048 # 2 KiB
        data = b''
        while True:
            part = sock.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                break
        return data

    def handle(self, connection:socket.socket, address:tuple):
        """
        For each new client connect to the server, executes this.
        Recieves the command and then sends the output of the given
        command.
        Args: socket object and address of the client.
        return None
        """
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("Thread-%r" % (address,))
        try:
            logger.debug("Connected %r at %r", connection, address)
            data = self.recvall(connection) # command getter + pvs output
            data_b64 = None
            try:
                data_b64 = eval(base64.b64decode(data))
            except SyntaxError as e:
                logging.exception("Unexpected exception: Syntax Error data_b64")
                logging.exception(str(e))
            if data_b64:
                logger.debug("Received Data from client: %r" %(data_b64,))
                if data_b64["pvs_stdin"].decode("utf-8"):
                    command = data_b64["cmd"].decode("utf-8")
                    pvs_stdin = data_b64["pvs_stdin"].decode("utf-8")
                    res = self.handlePipelineCommand(command, pvs_stdin)
                else:
                    command = data_b64["cmd"].decode("utf-8")
                    res = self.handleNonPipelineCommand(command)
                base64_dict = base64.b64encode(str(res).encode('utf-8'))
                connection.sendall(base64_dict)
                logger.debug("Data is Sent to %r" %(address,))
            else:
                res = {
                    "output": "".encode(), 
                    "error": "Error while executing previous command".encode()
                }
                base64_dict = base64.b64encode(str(res).encode('utf-8'))
                connection.sendall(base64_dict) 
        except:
            logger.exception("Problem handling request")
            res = {
                "output": "".encode(), 
                "error": "Error while executing previous command".encode()
            }
            base64_dict = base64.b64encode(str(res).encode('utf-8'))
            connection.sendall(base64_dict) 

        finally:
            logger.debug("Closing Thread %r" %(address,))
            sys.exit()
            logger.debug("Closing socket")
            connection.close()

    def start(self):
        """
        Driver function of the Server class
        Listens to the new client and creates new process for 
        new active client and then terminates after it executes command.
        """
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)

        while True:
            try:
                conn, address = self.socket.accept()
            except KeyboardInterrupt:
                print("\nServer: Keyboard Interrupt".capitalize())
                logging.info("Shutting down")
                
                return
            self.logger.debug("Got connection")
            thread = threading.Thread(target=self.handle, args=(conn, address))
            thread.daemon = True
            thread.start()
            self.logger.debug("Started Thread %r", thread)
            # process = multiprocessing.Process(target=self.handle, args=(conn, address))
            # process.daemon = True
            # process.start()
            # self.logger.debug("Started process %r", process)
    
    def __del__(self):
        logging.info("All done")

if __name__ == "__main__":
    server = Server("0.0.0.0", PORT)
    try:
        logging.info("Listening")
        server.start()
        logging.info("Shutting down")
        logging.info("All done")
    except:
        logging.exception("Unexpected exception")