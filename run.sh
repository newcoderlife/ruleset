#!/usr/bin/env bash

set -ex

if [ $# -eq 0 ]; then
    echo "Usage: $0 <path_to_log_file>"
    exit 1
fi

if [ ! -f .env/bin/activate ]; then
    python3 -m venv .env
fi

source .env/bin/activate
pip install -r requirements.txt

./generate.py --log_file $1
