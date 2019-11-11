# Distributed Terminal

## Features

- There will be a Distributed Network where each node is connected to each other.
- In this Distributed terminal application, when a node wants to send a command to other
node, it will send using IP address of that other node.
- Let’s say node A want to send ls command to node B then node A will use IP address of
node B and the command will be executed on node B, node B will send the response back
to node A and the output will be shown on the terminal of node A.
    - Ex: B > ls (you can use ‘>’ operator to differentiate the node and command in
    input string)
- Here any node can act as a client (which is sending a command) or as a server (which is
executing a command).
- There also can be a pipeline of commands where one command is executed on one node
then the response will be given to the next node and so on, the final output is shown on
the client terminal.
    - Ex: B > ls || C > uniq || D > wc (here, ‘||’ operator is used for the pipeline)
- You program should support basic linux commands like:
    - ls, date, mkdir, rmdir, rm, mv, cp, man, wc, uniq, sort

## How to run

There are two ways of running this program.

### Method 1

Running single python file.

```shell
$ python3 main.py
```

### Method 2

Running client and server python file seperately

```shell
$ python3 server.py
```

```shell
$ python3 client.py
```

## Screenshots
