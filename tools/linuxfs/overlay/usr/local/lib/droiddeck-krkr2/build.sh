#!/bin/bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
. "$here/source.env"
work=${1:?usage: build.sh WORK OUTPUT}
out=${2:?usage: build.sh WORK OUTPUT}
mkdir -p "$work" "$out"
work=$(cd "$work" && pwd)
out=$(cd "$out" && pwd)
export VCPKG_DISABLE_METRICS=1 VCPKG_MAX_CONCURRENCY=${JOBS:-2}
export VCPKG_FORCE_SYSTEM_BINARIES=1
export VCPKG_BINARY_SOURCES=clear
checkout() {
    git init -q "$1"
    git -C "$1" remote add origin "$2"
    git -C "$1" fetch --depth 1 origin "$3"
    git -C "$1" checkout -q --detach FETCH_HEAD
    test "$(git -C "$1" rev-parse HEAD)" = "$3"
}
echo '== STEP Krkr2 source and build tools'
checkout "$work/source" https://github.com/2468785842/krkr2.git "$KRKR2_COMMIT"
checkout "$work/vcpkg" https://github.com/microsoft/vcpkg.git "$VCPKG_COMMIT"
python3 "$here/prepare.py" "$work/source"
case "$(uname -m)" in
    aarch64) arch=arm64 ;;
    x86_64) arch=x64 ;;
    *) echo 'Unsupported build architecture' >&2; exit 1 ;;
esac
printf 'set(VCPKG_TARGET_ARCHITECTURE %s)\nset(VCPKG_CRT_LINKAGE dynamic)\nset(VCPKG_LIBRARY_LINKAGE static)\nset(VCPKG_CMAKE_SYSTEM_NAME Linux)\nset(VCPKG_BUILD_TYPE release)\n' "$arch" > "$work/source/vcpkg/triplets/$arch-linux-release.cmake"
python3 -m venv "$work/tools"
"$work/tools/bin/pip" install --disable-pip-version-check 'cmake==3.31.6'
export PATH="$work/tools/bin:$PATH" VCPKG_ROOT="$work/vcpkg"
bash "$VCPKG_ROOT/bootstrap-vcpkg.sh" -disableMetrics
echo '== STEP Build Krkr2 dependencies and engine'
cmake -S "$work/source" -B "$work/build" -G Ninja -DLINUX=ON \
    -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DBUILD_TOOLS=OFF \
    -DVCPKG_TARGET_TRIPLET="$arch-linux-release"
cmake --build "$work/build" --target krkr2 --parallel "${JOBS:-2}"
binary=$(find "$work/build/bin" -type f -name krkr2 -print -quit)
test -n "$binary"
cp -aL "$(dirname "$binary")/." "$out/"
strip --strip-unneeded "$out/krkr2"
"$out/krkr2" --help
mkdir -p "$out/licenses"
cp "$work/source/LICENSE" "$out/licenses/krkr2.txt"
(cd "$work/build/vcpkg_installed" && find . -path '*/share/*/copyright' -type f -exec cp --parents '{}' "$out/licenses/" \;)
printf 'Source: https://github.com/2468785842/krkr2\nCommit: %s\nvcpkg: %s\n' "$KRKR2_COMMIT" "$VCPKG_COMMIT" > "$out/BUILD.txt"
