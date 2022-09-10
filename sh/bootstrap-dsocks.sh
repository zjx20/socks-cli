#!/bin/bash
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GIT_REPO="https://github.com/zjx20/dsocks.git"
REVISION="527ce0df5b519e5dca70a4c44d10b148bda67a1c"

cd "${CURRENT_DIR}/.."
[ ! -d dsocks ] && git clone "${GIT_REPO}"

if [ -d dsocks ]; then
    cd dsocks
    if [ ! -f libdsocks.so ] || [ "$(git rev-parse HEAD)" != "${REVISION}" ]; then
        git reset --hard HEAD && git fetch && git checkout "${REVISION}"
        ./compile.sh -f
    fi
fi

if [ -f "${CURRENT_DIR}/../dsocks/libdsocks.so" ]; then
    exit 0
else
    exit 1
fi
