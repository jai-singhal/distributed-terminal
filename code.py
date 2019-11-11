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
            # We are in the child process.
            client = Client(PORT)
            client.start()
            print("%d (child) just was created by %d." % (os.getpid(), os.getppid()))
        else:
            # We are in the parent process.
            server = Server("0.0.0.0", PORT)
            server.start()
            print("%d (parent) just created %d." % (os.getpid(), pid))
    except OSError:
        sys.exit()
if __name__ == "__main__":
    main()