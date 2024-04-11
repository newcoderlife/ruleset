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
    url=$(curl -sL https://api.github.com/repos/Loyalsoldier/geoip/releases/latest | jq -r '.assets[] | select(.name == "Country.mmdb") | .browser_download_url')
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

function update {
    update_repo
    update_database
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
