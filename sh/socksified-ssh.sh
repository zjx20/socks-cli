#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ssh -o ProxyCommand="${CURRENT_DIR}/socksified-connect.sh %h %p" "$@"
