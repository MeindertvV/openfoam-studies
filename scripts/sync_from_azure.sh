#!/bin/bash
# Haalt resultaten van de VM op: standaard alleen PNG, CSV, logs en postProcessing,
# geen tijdmappen. Lokale bestanden die nieuwer zijn blijven staan.
# Gebruik: sync_from_azure.sh <studie> [--dry-run] [--full]
set -euo pipefail
source "$(dirname "$0")/env.sh" --no-foam
resolve_study "${1:-}"
require_azure
shift

mode=()
filters=(
    --exclude='processor*/'
    --exclude='dynamicCode/'
    --exclude='/case/[0-9]*/'
    --exclude='/case/constant/'
    --exclude='/case/system/'
    --exclude='*.vt?'
    --include='*/'
    --include='*.png'
    --include='*.csv'
    --include='log.*'
    --include='slurm-*.out'
    --include='/case/postProcessing/***'
    --exclude='*'
)
for arg in "$@"; do
    case $arg in
        --dry-run) mode=(--dry-run) ;;
        --full) filters=(--exclude='processor*/') ;;
        *) die "onbekende optie: $arg" ;;
    esac
done
[ "${AZ_TRANSFER:-rsync}" = rsync ] || die "AZ_TRANSFER=$AZ_TRANSFER is nog niet ingebouwd"

rsync -avzu --prune-empty-dirs "${mode[@]}" -e "ssh ${AZ_SSH_OPTS:-}" "${filters[@]}" \
    "$AZ_TARGET:$AZ_REMOTE_ROOT/studies/$(basename "$STUDY_DIR")/" "$STUDY_DIR/"
