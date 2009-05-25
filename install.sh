#!/bin/bash

OWNER=$1

sudo -u postgres psql -U postgres -e -c "CREATE DATABASE bills WITH OWNER $OWNER"
./Database.py add_new
