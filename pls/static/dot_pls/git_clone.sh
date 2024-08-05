#!/bin/bash
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
(cd "$SCRIPT_DIR"; mkdir -p deps)
(cd "$SCRIPT_DIR/deps"; git clone "$1" "$2")
