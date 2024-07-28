#!/usr/bin/env bash

set -ex

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path_to_file> [--upload] [--refresh] [--update]"
    exit 1
fi

if [ ! -f .env/bin/activate ]; then
    python3 -m venv .env
fi

source .env/bin/activate
python3 -m pip install -r requirements.txt -i https://mirrors.volces.com/pypi/simple/
python3 ./generate.py --log_file $1
deactivate

function update_repo {
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

function update_database {
    echo "Downloading latest GeoIP database..."
    if ! command -v jq &>/dev/null; then
        echo "jq is not installed."
        return
    fi
    if ! command -v curl &>/dev/null; then
        echo "curl is not installed."
        return
    fi

    name="Country.mmdb.tmp"
    url="https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/Country.mmdb"
    status=$(curl -Lo $name $url --write-out "%{http_code}" --silent --output /dev/null)
    if [[ "$status" -eq 200 && -f "$name" && -s "$name" ]]; then
        mv $name Country.mmdb
        echo "Download successful: $name"
    else
        echo "Download failed: status=$status"
    fi
    rm -f $name
    echo "GeoIP database updated."
}

function generate_local {
    if [ ! -f local.noncn ]; then
        echo "# Put noncn domain here. Like 'twitter.com.'" > local.noncn
    fi
}

function update {
    update_repo
    update_database
    generate_local
}

function refresh {
    generate_local

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
