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

class CommandRunner(object):
    def __init__(self):
        pass

    @staticmethod
    def popen_timeout(command, timeout):
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

    @staticmethod
    def popen_stdin_timeout(command, timeout):
        subcmnds = command.split("|")
        p1 = subprocess.Popen(
            subcmnds[0].split(),
            stdout=subprocess.PIPE,
        )
        pvs_stdin = p1.stdout
        for subcmd in subcmnds[1:]:
            p2 = subprocess.Popen(
                subcmd.split(),
                stdin=pvs_stdin,
                stdout=subprocess.PIPE,
            )
            pvs_stdin = p2.stdout
        for t in range(timeout):
            if p2.poll() is not None:
                return p2.communicate()
            sleep(0.1)
        p2.kill()
        return (False, False)

    @staticmethod
    def run_timeout(command:dict):
        try:
            if command["pvs_stdin"]:
                p = subprocess.run(
                    command["cmd"], 
                    input = command["pvs_stdin"].decode("utf-8"),
                    encoding="utf-8",
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
            else:
                p = subprocess.run(
                    command["cmd"], 
                    encoding="utf-8",
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
            return p.stdout, p.stderr
        except Exception as e:
            return (False, str(e))
        
    @staticmethod
    def run_stdin_timeout(command:dict):
        subcmnds = command["cmd"].split("|")
        try:
            if command["pvs_stdin"]:
                p1 = subprocess.run(
                    subcmnds[0].split(),
                    input = command["pvs_stdin"].decode("utf-8"),
                    encoding="utf-8",
                    stdout = subprocess.PIPE,
                )
            else:
                p1 = subprocess.run(
                    subcmnds[0].split(),
                    stdout = subprocess.PIPE,
                )
            pvs_stdin = p1.stdout
            for subcmd in subcmnds[1:]:
                p2 = subprocess.Popen(
                    subcmd.split(),
                    stdin=pvs_stdin,
                    encoding="utf-8",
                    stdout=subprocess.PIPE,
                )
                pvs_stdin = p2.stdout
            return p2.stdout, p2.stderr

        except Exception as e:
            return (False, str(e))


    def handleNonPipelineCommand(self, cmd_in:str):
        if "|" in cmd_in:
            try:
                out, err = self.popen_stdin_timeout(cmd_in, 60)
                if out == False:
                    err = "Cannot able to run this command"
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: popen")
        else:
            try:
                out, err = self.popen_timeout(cmd_in.split(), 60)
                if out == False:
                    err = "Cannot able to run this command"
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: popen")
        if err:
            if isinstance(err, str):
                return {"output": "", "error": err.encode()}
            else:
                return {"output": "", "error": err}

        if isinstance(out, str):
            out = out.encode()

        return {"output": out, "error": "".encode()}


    def handlePipelineCommand(self, cmd_in:dict):
        if "|" in cmd_in["cmd"]:
            try:
                out, err = self.run_stdin_timeout(cmd_in)
                if out == False:
                    err = "Cannot able to run this command"
            except Exception as e:
                err = str(e)
                logging.exception("Unexpected exception: run_stdnin")
        else:
            try:
                out, err = self.run_timeout(cmd_in)
                if out == False:
                    if not err:
                        err = "Cannot able to run this command"
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


class Server(CommandRunner):
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

    def handle(self, connection, address):
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("process-%r" % (address,))
        try:
            logger.debug("Connected %r at %r", connection, address)
            while True:
                data = connection.recv(4080)
                if not data:
                    continue
                try:
                    data_b64 = eval(base64.b64decode(data))
                except SyntaxError:
                    data_b64 = dict()
                    logging.exception("Unexpected exception: Syntax Error data_b64")
                if data_b64:
                    logger.debug("Received data %r", data_b64)
                    if data_b64["pvs_stdin"]:
                        res = self.handlePipelineCommand(data_b64)
                    else:
                        res = self.handleNonPipelineCommand(data_b64["cmd"])
                    base64_dict = base64.b64encode(str(res).encode('utf-8'))
                    connection.sendall(base64_dict)
                    logger.debug("Sent data")
        except:
            logger.exception("Problem handling request")
        finally:
            logger.debug("Closing socket")
            sys.exit()
            connection.close()

    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)

        while True:
            try:
                conn, address = self.socket.accept()
            except KeyboardInterrupt:
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
        logging.info("Shutting down")
        # for process in multiprocessing.active_children():
        #     logging.info("Shutting down process %r", process)
        #     process.terminate()
        #     process.join()
        #     print(process, "terminated")

        logging.info("All done")

if __name__ == "__main__":
    server = Server("0.0.0.0", PORT)
    try:
        logging.info("Listening")
        server.start()
    except:
        logging.exception("Unexpected exception")