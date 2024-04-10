#!/usr/bin/env bash

set -ex

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path_to_file> [--upload] [--refresh] [--update]"
    exit 1
fi

if [ ! -f .env/bin/activate ]; then
    python3 -m venv .env
    .env/bin/pip install -r requirements.txt
fi

.env/bin/python3 ./generate.py --log_file $1

function update {
    if ! command -v git &>/dev/null; then
        echo "Git is not installed."
        return
    fi

    echo "Cloning latest ruleset..."
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "master" ]; then
        echo "Switching to master branch..."
        git checkout master
    fi

    git fetch origin master
    git reset --hard origin/master
    echo "Ruleset updated."
}

function refresh {
    if ! command -v service &>/dev/null; then
        echo "Service command not found."
        return
    fi

    service coredns restart
}

function upload {
    echo "Not implemented yet."
}

shift
for arg in "$@"; do
    case "$arg" in
        --upload)
            upload
            ;;
        --refresh)
            refresh
            ;;
        --update)
            update
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done
