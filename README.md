socks-cli
=========

`socks-cli` is a solution to make CLI commands use the specified socks5 proxy, by setting up special environment variables, such as `ALL_PROXY`. It works on linux and macOS with bash and python2.7 installed.

Here is a incomplete list of supported commands:

* git
* curl
* brew
* pod
* gem
* npm
* ...

## Usage

1. Clone the code.

2. Copy `socksproxyenv.sample` to `socksproxyenv`, and fill your socks5 server into it.

3. Call `source socks-cli/activate` before your CLI commands:
	```
	$ source socks-cli/activate
	Done! Some environment variables have been changed to:
	  GIT_SSH=/Users/x/socks-cli/socks5proxyssh
	  ALL_PROXY=socks5h://localhost:1080
	  GIT_PROXY_COMMAND=/Users/x/socks-cli/socks5proxywrapper

	$ git clone git@github.com:git/git.git
	Cloning into 'git'...
	remote: Counting objects: 213208, done.
	remote: Compressing objects: 100% (372/372), done.
	Receiving objects 2.0% (1/213208), 620.00 KiB | 121.00 KiB/s
	...
	```

4. Optionally, you can call `source socks-cli/deactivate` to deactivate `socks-cli`.

For more details, please see [socksproxyenv.sample](socksproxyenv.sample).
