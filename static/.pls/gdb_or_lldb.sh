#!/bin/bash
DIR=$(dirname "${BASH_SOURCE[0]}")
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "export GDB_OR_LLDB=lldb" > "${DIR}/../.vscode/gdb_or_lldb"
else
  echo "export GDB_OR_LLDB=gdb" > "${DIR}/../.vscode/gdb_or_lldb"
fi
