#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct

def create_connection(address, proxy=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if proxy:
        proxy_host, proxy_port = proxy.split(':')
        proxy_port = int(proxy_port)

        # Connect to the SOCKS5 proxy
        sock.connect((proxy_host, proxy_port))

        # SOCKS5 handshake
        sock.sendall(b'\x05\x01\x00')
        response = sock.recv(2)
        if response != b'\x05\x00':
            raise Exception("SOCKS5 handshake failed")

        # Send connection request
        host, port = address
        request = b'\x05\x01\x00\x03' + chr(len(host)).encode() + host.encode() + struct.pack('>H', port)
        sock.sendall(request)

        # Receive response
        response = sock.recv(10)
        code = response[1]
        if not isinstance(code, int):
            code = ord(code)
        if code != 0:
            raise Exception("SOCKS5 connection failed with error %d" % code)
    else:
        # Direct connection
        sock.connect(address)

    return sock