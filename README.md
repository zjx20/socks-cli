socks-cli
=========

`socks-cli` is a solution to make CLI commands use the specified socks5 proxy, by setting up special environment variables, such as `ALL_PROXY`. It works on linux and macOS with bash and python installed.

Here is an incomplete list of supported commands:

* git
* curl
* wget
* brew
* pod
* gem
* npm
* mvn
* ssh
* scp
* ...

## Usage

1. Clone the code.
	```bash
	git clone https://github.com/zjx20/socks-cli.git
	```

2. Copy `socksproxyenv.sample` to `socksproxyenv`, and fill your socks5 server into it.
	```bash
	cd socks-cli
	cp socksproxyenv.sample socksproxyenv

	# edit socksproxyenv, complete the line:
	#   export SOCKS_PROXY=
	```

3. Invoke `source socks-cli/activate` before running your CLI commands:
	```bash
	$ source socks-cli/activate
	Serving HTTP proxy on 127.0.0.1 port 54967 ...
	Done! Variables or aliases have been changed to:
	  GIT_PROXY_COMMAND=/Users/x/socks-git/sh/socksified-connect.sh
	  GIT_SSH=/Users/x/socks-git/sh/socksified-ssh.sh
	  ALL_PROXY=socks5h://127.0.0.1:1080
	  HTTP_PROXY=http://127.0.0.1:54967
	  HTTPS_PROXY=http://127.0.0.1:54967

	# Following commands will use the socks proxy!

	$ git clone git@github.com:git/git.git
	Cloning into 'git'...
	remote: Counting objects: 213208, done.
	remote: Compressing objects: 100% (372/372), done.
	Receiving objects 2.0% (1/213208), 620.00 KiB | 121.00 KiB/s
	...

	# Check your external IP!
	$ curl ipinfo.io
	...
	```

4. Optionally, you can invoke `source socks-cli/deactivate` to deactivate `socks-cli`.

For more details, please see [socksproxyenv.sample](socksproxyenv.sample).

### One-Shot Mode

The usage described above affects all commands in the terminal session. If you wish to temporarily enable the socks proxy for only a particular command, you can use the `socksify` script. (Note: You still need to configure the `socksproxyenv` file first.)

```bash
# make a symlink to PATH
ln -s /path/to/socks-cli/socksify /usr/local/bin/socksify

# or make an alias
alias socksify='/path/to/socks-cli/socksify'

# enable for one-shot
socksify curl ipinfo.io
```
