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

_pkg_name() {
    local cmd="$1"

    case "$cmd" in
        pgrep)
            if command -v apt-get &>/dev/null; then
                echo "procps"
            elif command -v apk &>/dev/null; then
                echo "procps"
            elif command -v dnf &>/dev/null || command -v yum &>/dev/null; then
                echo "procps-ng"
            else
                echo "procps"
            fi
            ;;
        *)
            echo "$cmd"
            ;;
    esac
}

_shell_quote() {
    local value="$1"
    printf "'%s'" "${value//\'/\'\\\'\'}"
}

MISSING=()
command -v curl    &>/dev/null || MISSING+=("$(_pkg_name curl)")
command -v python3 &>/dev/null || MISSING+=("$(_pkg_name python3)")
command -v pgrep   &>/dev/null || MISSING+=("$(_pkg_name pgrep)")

if [ ${#MISSING[@]} -gt 0 ]; then
    _install_pkgs "${MISSING[@]}"
fi

# Download and extract the repo archive from GitHub
REF="${VERSION:-master}"
[ "$REF" = "latest" ] && REF="master"
URL="https://github.com/zjx20/socks-cli/archive/${REF}.tar.gz"

CURL_PROXY_OPTS=()
if [ -n "${SOCKS_CLI_SOCKS_PROXY}" ]; then
    CURL_PROXY_OPTS=(--proxy "socks5h://${SOCKS_CLI_SOCKS_PROXY}")
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

# Persist the feature options for later shells.
SOCKS_CLI_SOCKS_PROXY_QUOTED="$(_shell_quote "${SOCKS_CLI_SOCKS_PROXY:-}")"
SOCKS_CLI_AUTO_ACTIVATE_QUOTED="$(_shell_quote "${SOCKS_CLI_AUTO_ACTIVATE:-}")"

SHELL_SNIPPET=$(cat <<'SNIPPET'
export SOCKS_CLI_SOCKS_PROXY=__SOCKS_CLI_SOCKS_PROXY__
export SOCKS_CLI_AUTO_ACTIVATE=__SOCKS_CLI_AUTO_ACTIVATE__

alias sca='source /opt/socks-cli/activate'
alias scd='source /opt/socks-cli/deactivate'
alias sf='/opt/socks-cli/socksify'

# Auto-activate when SOCKS_CLI_AUTO_ACTIVATE is non-empty and not already active
if [ -n "${SOCKS_CLI_AUTO_ACTIVATE}" ] && [ "${_socks_cli}" != "1" ]; then
    source /opt/socks-cli/activate > /dev/null
fi
SNIPPET
)
SHELL_SNIPPET="${SHELL_SNIPPET/__SOCKS_CLI_SOCKS_PROXY__/${SOCKS_CLI_SOCKS_PROXY_QUOTED}}"
SHELL_SNIPPET="${SHELL_SNIPPET/__SOCKS_CLI_AUTO_ACTIVATE__/${SOCKS_CLI_AUTO_ACTIVATE_QUOTED}}"

# Write aliases + auto-activation to a profile.d script (picked up by bash/sh login shells)
cat > /etc/profile.d/socks-cli.sh <<PROFILE
${SHELL_SNIPPET}
PROFILE
chmod 644 /etc/profile.d/socks-cli.sh

# /etc/bash.bashrc is sourced for interactive non-login bash shells (e.g. most terminals in devcontainers)
if [ -f /etc/bash.bashrc ]; then
    echo "$SHELL_SNIPPET" >> /etc/bash.bashrc
fi

# zsh support
if [ -f /etc/zsh/zshrc ]; then
    echo "$SHELL_SNIPPET" >> /etc/zsh/zshrc
fi

echo "socks-cli installed to ${INSTALL_DIR}"
