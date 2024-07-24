#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import fcntl
import os
import sys
import select
import argparse
from socks2http.socks5 import create_connection

# Python 2 and 3 compatibility for reading from stdin and writing to stdout
if sys.version_info[0] >= 3:
    def read_stdin(size):
        return sys.stdin.buffer.read1(size)
    def write_stdout(data):
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
else:
    fd = sys.stdin.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    def read_stdin(size):
        return sys.stdin.read(size)
    def write_stdout(data):
        sys.stdout.write(data)
        sys.stdout.flush()


def proxy(target_host, target_port, socks_proxy=None):
    target_address = (target_host, target_port)
    sock = create_connection(target_address, socks_proxy)

    inputs = [sys.stdin, sock]

    while True:
        readable, _, _ = select.select(inputs, [], [])

        for source in readable:
            if source == sys.stdin:
                data = read_stdin(4*4096)
                if not data:
                    return
                sock.sendall(data)
            else:
                data = sock.recv(4*4096)
                if not data:
                    return
                write_stdout(data)

def main():
    parser = argparse.ArgumentParser(description="TCP Proxy with optional SOCKS5 support")
    parser.add_argument('-s', '--socks', help="SOCKS5 proxy address (host:port)")
    parser.add_argument('host', help="Target host")
    parser.add_argument('port', type=int, help="Target port")

    args = parser.parse_args()

    try:
        proxy(args.host, args.port, args.socks)
    except KeyboardInterrupt:
        print("\nProxy terminated by user", file=sys.stderr)
    except Exception as e:
        print("Error: %s" % str(e), file=sys.stderr)

if __name__ == "__main__":
    main()
