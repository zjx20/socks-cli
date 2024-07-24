#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
scp -o ProxyCommand="${CURRENT_DIR}/socksified-connect.sh %h %p" "$@"
