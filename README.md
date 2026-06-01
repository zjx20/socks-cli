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

## Dev Container Feature

`socks-cli` is available as a [Dev Container Feature](https://containers.dev/implementors/features/), hosted on GHCR. It installs `socks-cli` automatically and provides the `sca` / `scd` shell aliases out of the box.

### Setup

1. Add the feature to your `.devcontainer/devcontainer.json` and pass the SOCKS settings as feature options:

    ```jsonc
    {
        "features": {
            "ghcr.io/zjx20/socks-cli/socks-cli:1": {
                // e.g. a SOCKS5 proxy accessible from the container
                "SOCKS_CLI_SOCKS_PROXY": "192.168.10.1:1080"
            }
        }
    }
    ```

   If your SOCKS proxy runs on the host machine, `host.docker.internal` is usually the easiest way to reach it from the container:

    ```jsonc
    {
        "features": {
            "ghcr.io/zjx20/socks-cli/socks-cli:1": {
                "SOCKS_CLI_SOCKS_PROXY": "host.docker.internal:1080"
            }
        }
    }
    ```

2. Rebuild the container. `socks-cli` is installed to `/opt/socks-cli` and the two aliases are ready in your shell.

### Aliases

| Alias | Action |
|-------|--------|
| `sca` | `source /opt/socks-cli/activate` — enable the SOCKS proxy for the current shell session |
| `scd` | `source /opt/socks-cli/deactivate` — disable the proxy and restore original environment |
| `sf`  | `/opt/socks-cli/socksify` — one-shot proxy, e.g. `sf curl ipinfo.io` |

### Auto-activation

Set `SOCKS_CLI_AUTO_ACTIVATE` to any non-empty value and `socks-cli` will activate automatically every time a shell starts:

```jsonc
{
    "features": {
        "ghcr.io/zjx20/socks-cli/socks-cli:1": {
            "SOCKS_CLI_SOCKS_PROXY": "192.168.10.1:1080",
            "SOCKS_CLI_AUTO_ACTIVATE": "1"
        }
    }
}
```

You can still run `scd` at any point to deactivate for the current session.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `version` | `latest` | Git ref (branch, tag, or commit SHA) of socks-cli to install |
| `SOCKS_CLI_SOCKS_PROXY` | empty | SOCKS5 proxy host and port used by `activate` and the installer download fallback |
| `SOCKS_CLI_AUTO_ACTIVATE` | empty | Any non-empty value enables automatic activation for new shells |

Example — pin to a specific tag:

```jsonc
{
    "features": {
        "ghcr.io/zjx20/socks-cli/socks-cli:1": {
            "version": "v1.2.3"
        }
    }
}
```
