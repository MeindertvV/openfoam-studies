#!/bin/bash
# Draait N iteraties/tijdstappen serieel in <studie>/smoke, zodat de case zelf schoon blijft,
# en daarna foamLog. N komt uit het argument of anders uit looptijd.smoke_iteraties.
# Gebruik: smoke.sh <studie> [N]
set -euo pipefail
source "$(dirname "$0")/env.sh"
resolve_study "${1:-}"

n=${2:-$(python3 "$REPO_ROOT/scripts/yaml_get.py" "$STUDY_DIR/case.yaml" looptijd.smoke_iteraties)}
n=${n:-100}
[[ $n =~ ^[0-9]+$ ]] && [ "$n" -gt 0 ] || die "ongeldig aantal iteraties: $n"
[ -d "$CASE_DIR/constant/polyMesh" ] || die "geen mesh; draai eerst mesh.sh"

smoke=$STUDY_DIR/smoke
rm -rf "$smoke"
mkdir "$smoke"
cp -r "$CASE_DIR/constant" "$CASE_DIR/system" "$smoke/"
if [ -d "$CASE_DIR/0" ]; then
    cp -r "$CASE_DIR/0" "$smoke/"
elif [ -d "$CASE_DIR/0.orig" ]; then
    cp -r "$CASE_DIR/0.orig" "$smoke/0"
else
    die "geen 0/ of 0.orig/ in $CASE_DIR"
fi
cd "$smoke"

dict=system/controlDict
app=$(foamDictionary -entry application -value "$dict")
dt=$(foamDictionary -entry deltaT -value "$dict")
end=$(awk -v d="$dt" -v n="$n" 'BEGIN { printf "%.10g", n * d }')
foamDictionary -entry startFrom -set startTime "$dict" > /dev/null
foamDictionary -entry startTime -set 0 "$dict" > /dev/null
foamDictionary -entry stopAt -set endTime "$dict" > /dev/null
foamDictionary -entry endTime -set "$end" "$dict" > /dev/null
foamDictionary -entry writeControl -set timeStep "$dict" > /dev/null
foamDictionary -entry writeInterval -set "$n" "$dict" > /dev/null

echo "== $app: $n stappen tot t=$end > $smoke/log.$app"
status=0
"$app" > "log.$app" 2>&1 || status=$?
if [ "$status" -ne 0 ] || ! grep -q '^End' "log.$app"; then
    echo "FOUT: smoke-test mislukt (exit $status). Eerste fout in $smoke/log.$app:" >&2
    grep -n -m1 -A8 -E 'FOAM FATAL|Floating point exception|sigFpe' "log.$app" >&2 || tail -8 "log.$app" >&2
    exit 1
fi

foamLog -quiet "log.$app" > /dev/null
echo "OK: logs in $smoke/logs/"
