#!/usr/bin/env python
# main.py
__author__ = "Jai Singhal"
__copyright__ = "Copyright 2019"
__version__ = "1.0.0"
__maintainer__ = "Jai Singhal"
__email__ = "jaisinghal48@gmail.com"
__website__ = "http://jai-singhal.github.io"
__repository__ = "https://github.com/jai-singhal/distributed-terminal"

import os
import sys
from server import Server
from client import Client

PORT = 40150

def main():
    try:
        # Run two process one for client and one for server
        pid = os.fork()
    except OSError:
        print("Problem in running fork command")
        sys.exit()
    try:
        if pid == 0:
            # We are in the child process.
            client = Client(PORT)
            client.start()
        else:
            # We are in the parent process.
            server = Server("0.0.0.0", PORT)
            server.start()
            print(f"Hope you like the project. Star(*) my repository {__repository__} if you like this.")

    except OSError:
        sys.exit()

if __name__ == "__main__":
    main()