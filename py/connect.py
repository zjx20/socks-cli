#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import argparse
import threading
import fcntl
import select
import errno
import time

from socks2http.SocksiPy import socks


def _loop(f, t, cond):
    try:
        fd = f.fileno()
        reads = [f]
        size = 16*1024
        while True:
            readable, _, _ = select.select(reads, [], [], 1)
            if len(readable) > 0:
                try:
                    buf = os.read(fd, size)
                    if buf:
                        t.write(buf)
                    else:
                        break
                except OSError as e:
                    if e.errno == errno.EAGAIN:
                        pass
                    else:
                        raise e
    except:
        pass
    finally:
        cond.acquire()
        cond.notify()
        cond.release()


def _pipe(f, t, cond):
    thread = threading.Thread(target=_loop, args=(f, t, cond))
    thread.daemon = True
    thread.start()


def tunnel(config):
    addr = config.addr
    port = config.port
    sock = None
    if config.socks5_server:
        proxy = (config.socks5_server.split(":") + ["1080"])[:2]
        sock = socks.socksocket()
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, proxy[0], int(proxy[1]))
    else:
        sock = socket.socket()
    sock.connect((addr, port))
    sock.settimeout(60)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
    sock.setblocking(0)

    # Make stdin non-blocking
    fd = sys.stdin.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    sys.stdin = os.fdopen(sys.stdin.fileno(), 'rb', 0)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'wb', 0)
    rfile = sock.makefile("rb", 0)
    wfile = sock.makefile("wb", 0)

    cond = threading.Condition()
    _pipe(sys.stdin, wfile, cond)
    _pipe(rfile, sys.stdout, cond)

    try:
        cond.acquire()
        cond.wait()  # Wait for completion
        cond.release()
    except:
        pass


def parseCmd(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("addr",
                        action="store",
                        help="Target IP or host")
    parser.add_argument("port",
                        action="store",
                        type=int,
                        help="Target port")
    parser.add_argument("--socks5-server", "-s",
                        action="store",
                        help="The upstream SOCKS5 proxy server, " +
                             "e.g. \"localhost:1080\"")
    return parser.parse_args(argv)


if __name__ == "__main__":
    config = parseCmd()
    tunnel(config)
