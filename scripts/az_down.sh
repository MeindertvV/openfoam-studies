#!/bin/bash
# Verwijdert de tijdelijke VM met alles erop, na bevestiging. Alleen de resourcegroep uit .azjob,
# en alleen als die met ofjob- begint. Haal de resultaten eerst op met sync_from_azure.sh.
# Gebruik: az_down.sh
set -euo pipefail
source "$(dirname "$0")/env.sh" --no-foam

[ -f "$REPO_ROOT/.azjob" ] || die "geen .azjob: er is geen actieve VM bekend"
group=${AZ_RESOURCE_GROUP:-}
[[ $group == ofjob-* ]] || die "onverwachte resourcegroep: $group"

if [ "$(az group exists -n "$group")" = true ]; then
    az resource list -g "$group" --query '[].{naam:name, soort:type}' -o table
    echo "Alles hierboven en alle data op de VM gaan definitief weg."
    read -r -p "Resourcegroep $group verwijderen? Typ \"ja\": " answer || answer=
    [ "$answer" = ja ] || { echo "Afgebroken, de VM blijft bestaan en kost geld."; exit 1; }
    az group delete -n "$group" --yes
fi

[ "$(az group exists -n "$group")" = false ] || die "resourcegroep $group bestaat nog"
rm -f "$REPO_ROOT/.azjob"
echo "Verwijderd: $group"
az resource list --tag ofjob=1 --query '[].name' -o tsv | sed 's/^/LET OP, nog aanwezig: /'
