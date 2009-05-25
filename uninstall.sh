#!/bin/bash

sudo -u postgres psql -U postgres -e -c "DROP DATABASE bills"
