#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_REPO="https://github.com/zjx20/dsocks.git"
REVISION="655f734c8ffc5657a691c839cc67bb46c032a2f0"

cd "${CURRENT_DIR}/.."
[ ! -d dsocks ] && git clone "${GIT_REPO}"

if [ -d dsocks ]; then
    cd dsocks
    if [ ! -f libdsocks.so ] || [ "$(git rev-parse HEAD)" != "${REVISION}" ]; then
        git reset --hard HEAD && git fetch && git checkout "${REVISION}"
        ./compile.sh
    fi
fi

if [ -f "${CURRENT_DIR}/../dsocks/libdsocks.so" ]; then
    exit 0
else
    exit 1
fi
