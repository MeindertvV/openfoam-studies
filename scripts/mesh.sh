#!/bin/bash
# Draait de meshstappen van een studie en daarna checkMesh; elke stap logt naar log.<stap>.
# Stappen komen uit geometrie.mesh_stappen in case.yaml, of anders automatisch uit system/.
# Gebruik: mesh.sh <studie>
set -euo pipefail
source "$(dirname "$0")/env.sh"
resolve_study "${1:-}"
cd "$CASE_DIR"
touch case.foam

steps=()
while IFS= read -r line; do
    steps+=("$line")
done < <(python3 "$REPO_ROOT/scripts/yaml_get.py" "$STUDY_DIR/case.yaml" geometrie.mesh_stappen)

if [ ${#steps[@]} -eq 0 ]; then
    [ -f system/blockMeshDict ] && steps+=("blockMesh")
    [ -f system/surfaceFeaturesDict ] && steps+=("surfaceFeatures")
    [ -f system/snappyHexMeshDict ] && steps+=("snappyHexMesh -overwrite")
fi
[ ${#steps[@]} -gt 0 ] || die "geen meshstappen gevonden; vul geometrie.mesh_stappen in"
steps+=("checkMesh -allGeometry -allTopology")

declare -A seen
for step in "${steps[@]}"; do
    app=${step%% *}
    seen[$app]=$(( ${seen[$app]:-0} + 1 ))
    log=log.$app
    [ "${seen[$app]}" -gt 1 ] && log=$log.${seen[$app]}

    echo "== $step > $log"
    status=0
    bash -c "$step" > "$log" 2>&1 || status=$?
    # checkMesh geeft exit 1 bij mislukte checks; check_mesh.py beoordeelt die
    if [ "$status" -ne 0 ] && [ "$app" != checkMesh ]; then
        echo "FOUT in $step (exit $status). Eerste fout in $CASE_DIR/$log:" >&2
        grep -n -m1 -A8 -E 'FOAM FATAL|Fatal error|command not found' "$log" >&2 || tail -8 "$log" >&2
        exit "$status"
    fi
done
