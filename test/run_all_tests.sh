#!/bin/bash

find . -type f -name '*Test.py' | cut -d . -f 2 | cut -c 2- | tr / . | xargs ./ut.py
