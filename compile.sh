#!/usr/bin/env bash
set -euo pipefail

gcc -shared -o somatic_engine_v2.so -fPIC somatic_engine_v2.c

echo "Compiled somatic_engine_v2.so"
