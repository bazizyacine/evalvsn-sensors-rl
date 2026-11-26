#!/usr/bin/env bash
#
# build.sh - builds ns-allinone-2.35 with this project's modules, outside the
# repository.
#
# Usage: [NS2_HOME=DIR] [NS2_ARCHIVE=FILE] bash build.sh [--force]
#
# Takes the official ns-allinone-2.35 release (NS2_ARCHIVE when that file
# exists, otherwise downloaded, into NS2_ARCHIVE when it is set so that the
# next build reuses it), refuses it unless its sha256 is the release's,
# extracts it into NS2_HOME, copies modules/ns-2.35/ over its ns-2.35/ (the
# added and modified files of MODIFICATIONS.md), and runs the release's
# ./install with gcc-4.8 and g++-4.8, the compilers ns-2.35 still builds with.
# ./install regenerates the configure scripts of Tcl and Tk with autoconf
# itself. nam and xgraph may fail on a recent system: ns needs neither.
# --force rebuilds an existing NS2_HOME from scratch.
set -euo pipefail

URL=https://sourceforge.net/projects/nsnam/files/allinone/ns-allinone-2.35/ns-allinone-2.35.tar.gz/download
SHA256=2216f4e8e274f5c2437741fc6e9c9728369fabe1838c708ef974d262b941cd5d
MODULES="$(cd "$(dirname "$0")" && pwd)/modules/ns-2.35"
NS2_HOME="${NS2_HOME:-$HOME/ns-allinone-2.35}"
FORCE=0

die() { echo "build.sh: $*" >&2; exit 1; }

for arg in "$@"; do
	case "$arg" in
		--force) FORCE=1 ;;
		-h | --help) sed -n '2,17p' "$0"; exit 0 ;;
		*) die "unknown option: $arg" ;;
	esac
done

[[ -d $MODULES ]] || die "no modules in $MODULES"
for cmd in curl sha256sum tar make autoconf gcc-4.8 g++-4.8; do
	command -v "$cmd" >/dev/null || die "$cmd not found"
done
if [[ -e $NS2_HOME ]]; then
	[[ $FORCE -eq 1 ]] || die "$NS2_HOME exists; --force rebuilds it from scratch"
	rm -rf "$NS2_HOME"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
archive="${NS2_ARCHIVE:-$tmp/ns-allinone-2.35.tar.gz}"
if [[ ! -f $archive ]]; then
	echo "== downloading $URL"
	curl -fL --retry 3 -o "$tmp/download" "$URL"
	mv "$tmp/download" "$archive"
fi
echo "$SHA256  $archive" | sha256sum -c --quiet - \
	|| die "$archive is not the official release (sha256 $SHA256 expected)"

echo "== extracting $archive into $NS2_HOME"
mkdir -p "$NS2_HOME"
NS2_HOME="$(cd "$NS2_HOME" && pwd)"
tar -xzf "$archive" -C "$NS2_HOME" --strip-components=1
[[ -x $NS2_HOME/install && -d $NS2_HOME/ns-2.35 ]] || die "unexpected layout in $archive"

echo "== copying $(find "$MODULES" -type f | wc -l) module files over ns-2.35/"
cp -r "$MODULES/." "$NS2_HOME/ns-2.35/"

echo "== ./install with gcc-4.8 and g++-4.8 ($(date '+%F %T'))"
rc=0
(cd "$NS2_HOME" && CC=gcc-4.8 CXX=g++-4.8 ./install) || rc=$?
echo "== ./install ended with code $rc ($(date '+%F %T'))"
[[ -x $NS2_HOME/ns-2.35/ns ]] || die "ns-2.35/ns was not built; see the ./install output above"
for tool in nam-1.15/nam xgraph-12.2/xgraph; do
	[[ -x $NS2_HOME/$tool ]] || echo "note: $tool was not built; ns does not need it"
done

cat <<EOF
== built: $NS2_HOME/ns-2.35/ns
Export before running ns:
export PATH="$NS2_HOME/bin:$NS2_HOME/tcl8.5.10/unix:$NS2_HOME/tk8.5.10/unix:\$PATH"
export LD_LIBRARY_PATH="$NS2_HOME/otcl-1.14:$NS2_HOME/lib:\${LD_LIBRARY_PATH:-}"
EOF
