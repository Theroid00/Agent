#!/bin/zsh
set -eu
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
    print -u2 'Project environment is missing. Follow the local setup in README.md.'
    exit 1
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python -m cyberagents run --system S3 --seed 42 --live "$@"
