import os
import sys
from server import Server
from client import Client

PORT = 40150

def main():
    try:
        pid = os.fork()
    except OSError:
        print("Problem in running fork command")
        sys.exit()
    try:
        if pid == 0:
            # print("Child")
            # We are in the child process.
            client = Client(PORT)
            client.start()
        else:
            # print("Server")
            # We are in the parent process.
            server = Server("0.0.0.0", PORT)
            server.start()
    except OSError:
        sys.exit()

if __name__ == "__main__":
    main()