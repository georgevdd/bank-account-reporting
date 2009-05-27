#!/bin/bash

owner=$1

if [ -z ${owner} ]; then
  echo "Usage: install.sh <owner>"
  exit 1
fi

script=$(cat <<EOF
CREATE DATABASE bills WITH OWNER $OWNER;

CREATE USER test;
ALTER USER test WITH PASSWORD 'test';
CREATE DATABASE bills_test WITH OWNER test;
EOF
)

sudo -u postgres echo "${script}" | psql -U postgres -e -f /dev/stdin
./Database.py add_new
./test/TestSetup.py add_new
