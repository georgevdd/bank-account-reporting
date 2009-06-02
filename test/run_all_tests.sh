#!/bin/bash

this_dir=${0%/*}
cd ${this_dir}

find . -type f -name '*Test.py' \
    | sed -e 's|\./\(.*\)\.py|\1|' \
    | sed 's|/|.|g' \
    | xargs ./ut.py
