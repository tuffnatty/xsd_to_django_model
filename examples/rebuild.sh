#!/bin/bash
export PYTHONPATH=.
for F in $(find . -name README.md); do
    D=$(dirname "$F")
    CMD=$(grep "^PYTHONPATH" $F | sed 's/^PYTHONPATH=\.//')
    (cd $D; $CMD < /dev/null 2> errors.txt)
done
