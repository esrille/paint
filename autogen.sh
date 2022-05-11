#!/bin/sh
set -e
set -x

aclocal
autopoint -f
automake --add-missing --copy
autoconf
./configure "$@"
