#!/bin/bash
set -e

INSTALL_DIR="/opt/socks-cli"
VERSION="${VERSION:-"latest"}"

echo "Installing socks-cli (version: ${VERSION})..."

# Install missing packages using whatever package manager is available
_install_pkgs() {
    if command -v apt-get &>/dev/null; then
        apt-get update -y
        apt-get install -y --no-install-recommends "$@"
    elif command -v apk &>/dev/null; then
        apk add --no-cache "$@"
    elif command -v dnf &>/dev/null; then
        dnf install -y "$@"
    elif command -v yum &>/dev/null; then
        yum install -y "$@"
    else
        echo "ERROR: no supported package manager found (apt/apk/dnf/yum)" >&2
        return 1
    fi
}

MISSING=()
command -v curl    &>/dev/null || MISSING+=(curl)
command -v python3 &>/dev/null || MISSING+=(python3)

if [ ${#MISSING[@]} -gt 0 ]; then
    _install_pkgs "${MISSING[@]}"
fi

# Download and extract the repo archive from GitHub
REF="${VERSION:-master}"
[ "$REF" = "latest" ] && REF="master"
URL="https://github.com/zjx20/socks-cli/archive/${REF}.tar.gz"

CURL_PROXY_OPTS=()
if [ -n "${SOCKS_PROXY}" ]; then
    CURL_PROXY_OPTS=(--proxy "socks5h://${SOCKS_PROXY}")
fi

mkdir -p "$INSTALL_DIR"
echo "Downloading ${URL}..."
if [ ${#CURL_PROXY_OPTS[@]} -gt 0 ]; then
    # Try via SOCKS_PROXY first, fall back to direct if it fails
    curl -fsSL --retry 3 "${CURL_PROXY_OPTS[@]}" "$URL" \
        | tar -xz -C "$INSTALL_DIR" --strip-components=1 \
        || curl -fsSL --retry 3 "$URL" \
            | tar -xz -C "$INSTALL_DIR" --strip-components=1
else
    curl -fsSL --retry 3 "$URL" \
        | tar -xz -C "$INSTALL_DIR" --strip-components=1
fi

# Generate socksproxyenv.
# SOCKS_CLI_SOCKS_PROXY is expected to be injected via devcontainer.json "remoteEnv" / "containerEnv".
cat > "$INSTALL_DIR/socksproxyenv" << 'EOF'
export SOCKS_PROXY="${SOCKS_CLI_SOCKS_PROXY}"
LOAD_SUPPORT git
LOAD_SUPPORT http
LOAD_SUPPORT wget
LOAD_SUPPORT mvn
LOAD_SUPPORT ssh
LOAD_SUPPORT scp
EOF

chmod -R 755 "$INSTALL_DIR"

# Write aliases + auto-activation to a profile.d script (picked up by bash/sh login shells)
cat > /etc/profile.d/socks-cli.sh << 'PROFILE'
alias sca='source /opt/socks-cli/activate'
alias scd='source /opt/socks-cli/deactivate'
alias sf='/opt/socks-cli/socksify'

if [ -n "${SOCKS_CLI_AUTO_ACTIVATE}" ] && [ "${_socks_cli}" != "1" ]; then
    source /opt/socks-cli/activate > /dev/null
fi
PROFILE
chmod 644 /etc/profile.d/socks-cli.sh

SHELL_SNIPPET=$(cat << 'SNIPPET'

# socks-cli: sca=activate, scd=deactivate, sf=one-shot
alias sca='source /opt/socks-cli/activate'
alias scd='source /opt/socks-cli/deactivate'
alias sf='/opt/socks-cli/socksify'

# Auto-activate when SOCKS_CLI_AUTO_ACTIVATE is non-empty and not already active
if [ -n "${SOCKS_CLI_AUTO_ACTIVATE}" ] && [ "${_socks_cli}" != "1" ]; then
    source /opt/socks-cli/activate > /dev/null
fi
SNIPPET
)

# /etc/bash.bashrc is sourced for interactive non-login bash shells (e.g. most terminals in devcontainers)
if [ -f /etc/bash.bashrc ]; then
    echo "$SHELL_SNIPPET" >> /etc/bash.bashrc
fi

# zsh support
if [ -f /etc/zsh/zshrc ]; then
    echo "$SHELL_SNIPPET" >> /etc/zsh/zshrc
fi

echo "socks-cli installed to ${INSTALL_DIR}"
