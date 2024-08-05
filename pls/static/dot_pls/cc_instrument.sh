#!/bin/bash
g++ \
  -I"$2" \
  -D PLS_INSTRUMENTATION \
  -E \
  "$1" 2>/dev/null \
| grep PLS_INSTRUMENTATION_OUTPUT \
| sed 's/^PLS_INSTRUMENTATION_OUTPUT//g'
