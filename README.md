socks-git
=========

Simple scripts to make socks5 work for git.

## Usage

1. Clone the code.

2. Copy `socksproxyenv.sample` to `socksproxyenv`, and fill your socks5 server into it.

3. Call `source socks-git/activate` before your git command:
	```
	$ source socks-git/activate
	Overrided GIT_PROXY_COMMAND, GIT_SSH and ALL_PROXY env in order to
	use localhost:1088 as the proxy server for git command!

	$ git clone git@github.com:git/git.git
	Cloning into 'git'...
	remote: Counting objects: 213208, done.
	remote: Compressing objects: 100% (372/372), done.
	Receiving objects 2.0% (1/213208), 620.00 KiB | 121.00 KiB/s
	...
	```

4. Optionally, you can call `source socks-git/deactivate` to deactivate `socks-git`.

## Side Effect

Since `socks-git` uses the ALL_PROXY env to proxy http/https to socks5, other tools that support the ALL_PROXY env will be affected too.
