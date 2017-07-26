#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import shutil
import signal
import socket
import select
import time
import errno
import os
import sys

from SocksiPy import socks

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        # python 3
        from io import StringIO

if sys.version_info < (3, 0):
    import httplib
    import thread
    from urlparse import urlparse
    from SocketServer import ThreadingMixIn, TCPServer
    from BaseHTTPServer import BaseHTTPRequestHandler
else:
    import http.client as httplib
    import _thread as thread
    from urllib.parse import urlparse
    from socketserver import ThreadingMixIn, TCPServer
    from http.server import BaseHTTPRequestHandler

SOCKS5_PROXY = None
DEBUG_MODE = False


class BoundedReader(object):
    def __init__(self, fp, limit=-1):
        self.fp = fp
        self.limit = limit
        self._curr = 0
        self._eof = False

    def read(self, size=None):
        if self.limit < 0:
            return self.fp.read(size)
        if self._eof:
            return None
        s = min(size or self.limit, self.limit - self._curr)
        data = self.fp.read(s)
        if data:
            self._curr += len(data)
            if self._curr == self.limit:
                self._eof = True
        return data


# https://en.wikipedia.org/wiki/Chunked_transfer_encoding
class ChunkedEncodingValidator(object):
    class Error(Exception):
        pass

    MAX_LINE_SIZE = 4*1024
    PIECE_SIZE = 32*1024

    STATE_HEADER = 1
    STATE_CONTENT = 2
    STATE_TRAILER = 3
    STATE_EOF = 4

    def __init__(self, fp):
        self.fp = fp
        self._len = -1
        self._curr = 0
        self._line = ""
        self._state = self.STATE_HEADER

    def read(self, size=None):
        buf = StringIO()
        while size is None or size > 0:
            # Consume the buffered line
            if self._line:
                l = len(self._line)
                if size is not None:
                    l = min(l, size)
                buf.write(self._line[:l])
                self._line = self._line[l:]
                size = self._reduceSize(size, l)
                continue

            if self._state == self.STATE_HEADER:
                self._readChunkHeader()
                if self._len == 0:
                    self._state = self.STATE_TRAILER
                else:
                    self._state = self.STATE_CONTENT
                continue
            if self._state == self.STATE_CONTENT:
                data = self._readChunkBody(size or self.PIECE_SIZE)
                if data:
                    buf.write(data)
                    size = self._reduceSize(size, len(data))
                else:
                    # End of chunk
                    self._readCrlf(buf)
                    size = self._reduceSize(size, 2)
                    self._state = self.STATE_HEADER
                continue
            if self._state == self.STATE_TRAILER:
                self._readTrailerLine()
                if len(self._line) == 2:
                    self._state = self.STATE_EOF
                continue
            if self._state == self.STATE_EOF:
                break

        data = buf.getvalue()
        buf.close()
        if data:
            return data
        return None

    def _reduceSize(self, size, v):
        if size is not None:
            return size - v
        return None

    def _ch(self, buf=None):
        ch = self.fp.read(1)
        if ch and buf:
            buf.write(ch)
        return ch

    def _readChunkHeader(self):
        assert self._state == self.STATE_HEADER
        buf = StringIO()
        count = 0
        while count < self.MAX_LINE_SIZE:
            ch = self._ch(buf)
            count += 1
            if ch is None:
                raise self.Error("Unexpected EOF, needed chunk header")
            elif ch == "\r":
                ch = self._ch(buf)
                if ch != "\n":
                    raise self.Error("Expected '\n' but got '%s'" % ch)
                break
        else:
            raise self.Error("Chunk header line was too long")
        self._line = buf.getvalue()
        buf.close()
        # Split with ':' to handle chunk extensions (if have)
        length = self._line.strip().split(";")[0].strip()
        try:
            self._len = int(length, 16)
            self._curr = 0
        except ValueError:
            raise self.Error("Bad chunk length")

    def _readChunkBody(self, size):
        assert self._state == self.STATE_CONTENT
        if self._curr >= self._len:
            return None
        l = min(size, self._len - self._curr)
        data = self.fp.read(l)
        if data is None or len(data) != l:
            raise self.Error("Insufficient chunk body")
        self._curr += len(data)
        return data

    def _readCrlf(self, buf):
        ch = self._ch(buf)
        if ch != "\r":
            raise self.Error("Expected '\r' but got '%s'" % ch)
        ch = self._ch(buf)
        if ch != "\n":
            raise self.Error("Expected '\n' but got '%s'" % ch)

    def _readTrailerLine(self):
        buf = StringIO()
        assert self._state == self.STATE_TRAILER
        count = 0
        while count < self.MAX_LINE_SIZE:
            ch = self._ch(buf)
            count += 1
            if ch is None:
                raise self.Error("Unexpected EOF, needed trailer lines")
            elif ch == "\r":
                ch = self._ch(buf)
                if ch != "\n":
                    raise self.Error("Expected '\n' but got '%s'" % ch)
                break
        else:
            raise self.Error("Chunk header line was too long")
        self._line = buf.getvalue()
        buf.close()


class ProxyHTTPRequestHandler(BaseHTTPRequestHandler, object):
    # Settings from StreamRequestHandler
    timeout = 30
    disable_nagle_algorithm = True

    # Settings from BaseHTTPRequestHandler
    protocol_version = "HTTP/1.1"
    server_version = "socks2http.py 1.0"

    _setup = BaseHTTPRequestHandler.setup
    _send_header = BaseHTTPRequestHandler.send_header
    _log_message = BaseHTTPRequestHandler.log_message
    _finish = BaseHTTPRequestHandler.finish

    # override
    def setup(self):
        self._setup()
        self.set_header_blacklist(None)

    def set_header_blacklist(self, blacklist):
        self._header_blacklist = blacklist

    def header_blacklist(self):
        return self._header_blacklist

    # override
    def send_header(self, keyword, value):
        blacklist = self.header_blacklist()
        if blacklist is None or keyword.lower() not in blacklist:
            self._send_header(keyword, value)

    # override
    def log_message(self, fmt, *args):
        if DEBUG_MODE:
            self._log_message(fmt, *args)

    # override
    def finish(self):
        try:
            self._finish()
        except socket.error:
            # Ignore the final socket error, such as broken pipe
            pass

    def doCommon(self):
        url = self.path
        pieces = urlparse(url)
        if not all((pieces.scheme, pieces.netloc)):
            return self.send_error(400, "Invalid URL to proxy")

        headers = {k.lower():v for k, v in self.headers.items()}
        omittedRequestHeaders = ("accept-encoding", "host", "proxy-connection")
        for k in omittedRequestHeaders:
            if k in headers:
                del headers[k]
        host, port = (pieces.netloc.split(":") + [None])[:2]
        conn = httplib.HTTPConnection(host=host, port=port)
        if SOCKS5_PROXY:
            sock = socks.socksocket()
            if port is None:
                port = 80
                if pieces.scheme.lower() == "https":
                    port = 443
            sock.connect((host, int(port)))
            conn.sock = sock
        cl = int(self.headers.get("content-length", "0"))
        body = None
        if cl > 0:
            body = BoundedReader(self.rfile, int(cl))
        elif self.headers.get("transfer-encoding") == "chunked":
            body = ChunkedEncodingValidator(self.rfile)
        conn.request(self.command, url, body, headers)

        res = conn.getresponse()

        # send_response() sends "Server" and "Date" headers as well as the
        # status code. But those headers might already exist in the response
        # of upstream. Thus here we suppress implicit headers from httplib
        # to prefer the value from upstream.
        blacklist = ("server", "date")
        blacklist = [x for x in blacklist if res.getheader(x) is not None]
        self.set_header_blacklist(blacklist)
        self.send_response(res.status)
        self.set_header_blacklist(None)

        chunked = res.getheader("transfer-encoding") == "chunked"
        closeConn = False
        if res.getheader("content-length") is None and not chunked:
            # Close the connection to indicate EOF since the remote server
            # didn't tell the content length and the response was not
            # chunked-encoding.
            closeConn = True

        connection = res.getheader("connection", default="Keep-Alive")
        if closeConn:
            connection = "Close"
        self.send_header("Connection", connection)

        # Forward headers
        omittedResponseHeaders = ("connection",)
        for k, v in res.getheaders():
            if k not in omittedResponseHeaders:
                self.send_header(k, v)
        self.end_headers()

        # Forward content
        bufsize = 32*1024
        while True:
            buf = res.read(bufsize)
            if not buf:
                if chunked:
                    self.wfile.write(b"0\r\n\r\n")
                break
            if chunked:
                c = "%X\r\n%s\r\n" % (len(buf), buf)
                self.wfile.write(c.encode("utf-8"))
            else:
                self.wfile.write(buf)
        if closeConn:
            self.finish()

    def _proxy(self):
        try:
            self.doCommon()
        except socket.gaierror as e:
            msg = str(e)
            return self.send_error(500, msg)
        except socket.error as e:
            if e.errno == errno.EPIPE:
                # Ignore broken pipe error
                pass
            else:
                msg = str(e)
                return self.send_error(500, msg)

    def do_OPTIONS(self):
        self._proxy()

    def do_GET(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_TRACE(self):
        self._proxy()

    def do_CONNECT(self):
        host, port = (self.path.split(":") + ["80"])[:2]
        port = int(port)
        if SOCKS5_PROXY:
            sock = socks.socksocket()
        else:
            sock = socket.socket()
        try:
            sock.connect((host, port))
        except Exception as e:
            msg = str(e)
            return self.send_error(400, msg)
        self.log_request(200)
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n")
        proxy_agent = "Proxy-agent: " + self.version_string() + "\r\n"
        self.wfile.write(proxy_agent.encode("utf-8"))
        self.wfile.write(b"\r\n")

        try:
            bufsize = 32*1024
            lastactive = time.time()
            csock, ssock = self.connection, sock
            csockclosed, ssockclosed = False, False
            cbuf, sbuf = "", ""

            csock.setblocking(0)
            ssock.setblocking(0)
            while True:
                reads = []
                writes = []
                if not cbuf:
                    if not csockclosed:
                        reads.append(csock)
                else:
                    writes.append(ssock)
                if not sbuf:
                    if not ssockclosed:
                        reads.append(ssock)
                else:
                    writes.append(csock)
                if len(reads) == 0 and len(writes) == 0:
                    # Nothing to read and write, this session is done
                    self.log_message("Gracefully shutdown the session")
                    break
                readable, writable, _ = select.select(reads, writes, [], 1)
                for r in readable:
                    data = r.recv(bufsize)
                    if not data:
                        # EOF
                        if r is csock:
                            csockclosed = True
                        else:
                            ssockclosed = True
                        continue
                    if r is csock:
                        cbuf = data
                    else:
                        sbuf = data
                    lastactive = time.time()
                for w in writable:
                    if w is csock:
                        n = csock.send(sbuf)
                        sbuf = sbuf[n:]
                    else:
                        n = ssock.send(cbuf)
                        cbuf = cbuf[n:]
                    lastactive = time.time()
                if time.time() - lastactive > 60:
                    self.log_message("Killing the idle connection")
                    break
        except socket.error:
            pass
        finally:
            ssock.close()
            # Close csock by the web framework
            self.close_connection = 1


# We don't use BaseHTTPServer.HTTPServer because it tries to get
# FQDN of the server when starting, which is quite slow.
class ThreadedHTTPServer(ThreadingMixIn, TCPServer):
    # Settings from ThreadingMixIn
    daemon_threads = True

    # Settings from TCPServer
    allow_reuse_address = True


def runProxyServer(config):
    try:
        # Use gevent when possible
        import gevent.monkey
        gevent.monkey.patch_all()
        print("Using gevent...")
    except ImportError:
        pass

    global SOCKS5_PROXY
    global DEBUG_MODE
    DEBUG_MODE = config.debug
    if config.socks5_server:
        SOCKS5_PROXY = (config.socks5_server.split(":") + ["1080"])[:2]
        SOCKS5_PROXY[1] = int(SOCKS5_PROXY[1])
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, *SOCKS5_PROXY)

    server_address = (config.bind, config.port)
    httpd = ThreadedHTTPServer(server_address, ProxyHTTPRequestHandler)

    def handler(signum, frame):
        # The documentation said shutdown() should be called on a
        # different thread from which called serve_forever().
        thread.start_new_thread(httpd.shutdown, ())
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    if config.foreground is not None:
        ppid = config.foreground
        if ppid == 0:
            # There is a risk that the parent process had already exited at
            # this monent.
            ppid = os.getppid()
        pid = os.getpid()

        def exitIfOrphan():
            while True:
                curr_ppid = os.getppid()
                if ppid != curr_ppid:
                    os.kill(pid, signal.SIGTERM)
                time.sleep(30)

        thread.start_new_thread(exitIfOrphan, ())

    ipport = httpd.socket.getsockname()
    if config.save_port is not None:
        with open(config.save_port, "w") as f:
            f.write(str(ipport[1]))
    print("Serving HTTP proxy on %s port %d ..." % ipport)
    httpd.serve_forever()


def parseCmd(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", "-b",
                        action="store",
                        help="The bind address for the proxy server",
                        default="127.0.0.1",
                        metavar="ADDR")
    parser.add_argument("--port", "-p",
                        action="store",
                        type=int,
                        help="The port for the proxy server",
                        default="0")
    parser.add_argument("--save-port",
                        action="store",
                        metavar="FILE",
                        help="Save the port number to file")
    parser.add_argument("--socks5-server", "-s",
                        action="store",
                        metavar="SOCKS5_SERVER",
                        help="The upstream SOCKS5 proxy server, " +
                             "e.g. \"localhost:1080\"")
    parser.add_argument("--debug", "-d",
                        action="store_true",
                        help="Debug mode (verbose output)")
    parser.add_argument("--foreground", "-f",
                        action="store",
                        type=int,
                        metavar="PID",
                        help="As opposed to background or daemon, " +
                             "the program will be terminated when " +
                             "its parent exited. Expected a pid number or 0.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    config = parseCmd()
    runProxyServer(config)
