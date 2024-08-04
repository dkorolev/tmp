#!/bin/bash
g++ \
  -I/home/dima/playground6/.pls/pls_h_dir \
  -D PLS_INSTRUMENTATION \
  -E \
  "$1" 2>/dev/null \
| grep PLS_INSTRUMENTATION_OUTPUT \
| sed 's/^PLS_INSTRUMENTATION_OUTPUT//g'
