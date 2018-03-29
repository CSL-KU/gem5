#!/usr/bin/python

#############################################################################################
#
# This module is able to run commands in gem5's FS mode. Your rcS script must start bash
# at the end (/bin/bash) or no rcS should be provided since the default rcS file in
# /etc/init.d/rcS will start bash.
#
#############################################################################################
#
# Start pyterm as follows:
#
# (term, inpipe) = pyterm.pyterm([port])
#
#
# Run commands like this:
#
# inpipe.send("ls -l\n")
#
#
# Clean up after yourself:
#
# close_pyterm(term, inpipe)
#
#############################################################################################
#
# Full example:
#
#
# import pyterm
#
# (term, inpipe) = pyterm.pyterm(3456)
#
# exit_event = m5.simulate()
# exit_cause = exit_event.getCause()
#
# while exit_cause == "myexitevent":
#     inpipe.send("ls -l\n")
#
#     exit_event = m5.simulate()
#     exit_cause = exit_event.getCause()
#
# close_pyterm(term, inpipe)
#
#############################################################################################
import multiprocessing
import socket
import select
import sys

# Polling terminal process ... should be the most efficient way to do this.
def TerminalProcess(pipe, port):
    inpipe, outpipe = pipe
    inpipe.close()

    sock = socket.create_connection(("127.0.0.1", port))

    sock.settimeout(10)

    epoll = select.epoll()
    epoll.register(sock.fileno(), select.EPOLLIN)
    epoll.register(outpipe.fileno(), select.EPOLLIN)

    should_exit = False

    while not should_exit:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == sock.fileno():
                sys.stdout.write(sock.recv(65536))
            elif fileno == outpipe.fileno():
                try:
                    cmd = outpipe.recv()
                    sock.send(cmd)
                except EOFError:
                    should_exit = True
                    break

    epoll.unregister(sock.fileno())
    epoll.unregister(outpipe.fileno())
    epoll.close()
    outpipe.close()
    sock.close()

# Returns the term and input pipe.
# term should be exited via .join() when exiting gem5
# input pipe can be used to send data to gem5
def pyterm(port=3456):
    print "Trying to connect pyterm to port %d" % port
    (inpipe, outpipe) = multiprocessing.Pipe()
    term = multiprocessing.Process(target=TerminalProcess, args=((inpipe,outpipe),port,))
    term.start()
    outpipe.close()

    return (term, inpipe)

# Closes the input pipe and exits the child process
def close_pyterm(term, inpipe):
    inpipe.close()
    term.join()

