#!/bin/bash
# Kopieert template/ naar studies/NNN-naam/ en vult de case optioneel vanuit een tutorial.
# Gebruik: new_study.sh <naam> [--tutorial <pad onder $FOAM_TUTORIALS>]
set -euo pipefail
source "$(dirname "$0")/env.sh"

name=${1:-}
tutorial=
[ "${2:-}" = --tutorial ] && tutorial=${3:-}
[ "${2:-}" = --tutorial ] && [ -z "$tutorial" ] && die "--tutorial mist een pad"
[ -n "${2:-}" ] && [ "${2:-}" != --tutorial ] && die "onbekende optie: $2"
[[ $name =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || die "gebruik: new_study.sh <naam> [--tutorial <pad>]"

src=
if [ -n "$tutorial" ]; then
    src=$FOAM_TUTORIALS/$tutorial
    [ -f "$src/system/controlDict" ] || die "geen tutorial-case: $src"
fi

last=$(find "$REPO_ROOT/studies" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' \
    | grep -E '^[0-9]{3}-' | sort | tail -1 | cut -c1-3 || true)
if [ -n "$last" ]; then
    number=$(printf '%03d' $(( 10#$last + 1 )))
else
    number=000
fi
target=$REPO_ROOT/studies/$number-$name

cp -r "$REPO_ROOT/template" "$target"
rm -f "$target/case/.gitkeep"
sed -i "s|^titel: \"\"|titel: \"$name\"|" "$target/case.yaml"

if [ -n "$tutorial" ]; then
    cp -r "$src/." "$target/case/"
    sed -i "s|^- Tutorial:\$|- Tutorial: $tutorial|" "$target/NOTES.md"
fi

echo "$target"
