socks2http
==========

`socks2http` is a protocol adaptor. It acts as a http proxy and redirects traffics to a socks5 proxy. Programs that only support http proxy can leverage socks5 proxies via this tool.

## Features

* Lightweight: zero dependency and low memory footprint
* Supports chunked transfer encoding, in both directions
* SOCKS5 upstream proxy
* Traditional HTTP proxying via `GET`, `POST` etc
* HTTP tunnel, AKA the `CONNECT` method

## Usage

```
usage: socks2http.py [-h] [--bind BIND] [--port PORT]
                     [--socks5-server SOCKS5_SERVER] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --bind BIND, -b BIND  The bind address for the proxy server
  --port PORT, -p PORT  The port for the proxy server
  --socks5-server SOCKS5_SERVER, -s SOCKS5_SERVER
                        The upstream SOCKS5 proxy server, e.g.
                        "localhost:1080"
  --debug, -d           Debug mode (verbose output)
```

## Misc

Keeping `socks2http` lightweight is the first principle. The performance of `socks2http` should be reasonable but not outstanding. However, if [`gevent`](https://github.com/gevent/gevent) has been installed, `socks2http` can use its power automatically, and gain a better concurrency.

socks2http vendored [SocksiPy](http://socksipy.sourceforge.net) for handling socks5 protocol. All credit goes to its author!
