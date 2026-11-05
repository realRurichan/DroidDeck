#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
if [ "${1:-}" = --native ]; then shift; fi
out=${1:?usage: tools/onsyuri/build.sh [--native] OUT}
mkdir -p "$out"
out=$(cd "$out" && pwd)
. "$here/source.env"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git init -q "$work/source"
git -C "$work/source" remote add origin "$ONSYURI_REPOSITORY"
git -C "$work/source" fetch --depth 1 origin "$ONSYURI_COMMIT"
git -C "$work/source" checkout -q --detach FETCH_HEAD
test "$(git -C "$work/source" rev-parse HEAD)" = "$ONSYURI_COMMIT"
git -C "$work/source" submodule update --init --depth 1
git -C "$work/source/src/onsyuri_libretro/deps/SDL_ttf" submodule update --init --depth 1 external/freetype
cmake -S "$work/source/src/onsyuri_libretro" -B "$work/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
    -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++
cmake --build "$work/build" --parallel "${JOBS:-2}"
aarch64-linux-gnu-strip --strip-unneeded "$work/build/onsyuri_libretro.so"
install -m644 "$work/build/onsyuri_libretro.so" "$out/onsyuri_libretro.so"
install -m644 "$work/source/src/onsyuri_libretro/onsyuri_libretro.info" "$out/onsyuri_libretro.info"
{
    printf 'Source: %s\nCommit: %s\nBuild: tools/onsyuri/build.sh\n\n' "$ONSYURI_REPOSITORY" "$ONSYURI_COMMIT"
    git -C "$work/source" submodule status --recursive
    find "$work/source" -type f \( -iname 'COPYING*' -o -iname 'LICENSE*' -o -name 'FTL.TXT' \) -not -path '*/.git/*' -print0 |
        sort -z | while IFS= read -r -d '' license; do
            printf '\n--- %s ---\n' "${license#"$work/source/"}"
            cat "$license"
        done
} > "$out/LICENSES.txt"
