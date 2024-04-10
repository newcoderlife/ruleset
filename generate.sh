#!/usr/bin/env bash

if [ ! -f .env/bin/activate ]; then
    python3 -m venv .env
fi

source .env/bin/activate
pip install -r requirements.txt

./generate.py --log_file /var/log/coredns.log
