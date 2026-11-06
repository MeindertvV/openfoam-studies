#!/bin/bash
# Stuurt een studie plus scripts/ en post/ naar de VM. Standaard een dry-run.
# Echt syncen alleen met --execute. Verwijdert nooit iets op de VM.
# Gebruik: sync_to_azure.sh <studie> [--execute]
set -euo pipefail
source "$(dirname "$0")/env.sh" --no-foam
resolve_study "${1:-}"
require_azure

case ${2:-} in
    "") mode=(--dry-run); echo "== DRY-RUN: er wordt niets verzonden" ;;
    --execute) mode=() ;;
    *) die "onbekende optie: $2" ;;
esac
[ "${AZ_TRANSFER:-rsync}" = rsync ] || die "AZ_TRANSFER=$AZ_TRANSFER is nog niet ingebouwd"

cd "$REPO_ROOT"
rsync -avzR "${mode[@]}" -e "ssh ${AZ_SSH_OPTS:-}" \
    --exclude='__pycache__/' \
    --exclude='processor*/' \
    --exclude='log.*' \
    --exclude='postProcessing/' \
    --exclude='/studies/*/smoke/' \
    --exclude='/studies/*/results/' \
    --exclude='/studies/*/kalibratie/' \
    --exclude='/studies/*/job*.sbatch' \
    --exclude='/studies/*/case/[1-9]*/' \
    --exclude='/studies/*/case/0.[0-9]*/' \
    scripts post requirements.txt "studies/$(basename "$STUDY_DIR")" \
    "$AZ_TARGET:$AZ_REMOTE_ROOT/"
