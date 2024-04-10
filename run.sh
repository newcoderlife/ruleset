#!/usr/bin/env bash

set -ex

if command -v git &>/dev/null; then
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "master" ]; then
        echo "Switching to master branch..."
        git checkout master
    fi

    git fetch origin master
    git stash push -m "ruleset.noncn" ruleset.noncn
    git reset --hard origin/master
    git stash pop
fi

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
