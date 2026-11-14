#!/usr/bin/env bash
# Build for Ableton Move without a target glibc or toolchain sysroot.
# Freestanding DSP library: no libc, libm, dynamic linker deps, or host API copies.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build dist
python3 scripts/generate_tables.py
CC="${CC:-clang}"
"$CC" --target=aarch64-linux-gnu -ffreestanding -nostdinc \
    -isystem "$($CC -print-resource-dir)/include" \
    -nostdlib -shared -fPIC -O2 -fvisibility=hidden \
    -fno-stack-protector -fno-builtin -fuse-ld=lld \
    -Wl,-soname,dsp.so -Wl,--no-undefined \
    src/dsp.c -o build/dsp.so
readelf -h build/dsp.so | grep -q 'AArch64'
nm -D build/dsp.so | grep -q 'move_plugin_init_v2'
if readelf -d build/dsp.so | grep -q NEEDED; then
    echo 'Unexpected dynamic dependencies' >&2;exit 1
fi
rm -rf dist/sprig-wt
mkdir -p dist/sprig-wt
cp build/dsp.so src/module.json src/web_ui.html dist/sprig-wt/
tar -C dist -czf dist/sprig-wt-module.tar.gz sprig-wt
printf 'Built: %s\n' "$(realpath dist/sprig-wt-module.tar.gz)"
