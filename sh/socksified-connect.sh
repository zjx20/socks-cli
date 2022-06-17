#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "${CURRENT_DIR}"
if [ -z "${SOCKS_PROXY}" ]; then
    source ../socksproxyenv
fi
../py/py_wrapper ../py/connect.py -s ${SOCKS_PROXY} "$@"
