#!/bin/bash
# Maakt een tijdelijke reken-VM voor één job, na bevestiging van het maximale budget.
# De VM krijgt OpenFOAM en Slurm via cloud-init en wordt na --hours uur automatisch
# uitgeschakeld. Verwijderen gaat met az_down.sh. De gegevens van de actieve VM staan in .azjob.
# Gebruik: az_up.sh <studie> --size <VM-type> --hours <1-23> [--spot] [--region <regio>]
set -euo pipefail
source "$(dirname "$0")/env.sh" --no-foam
resolve_study "${1:-}"
shift

size=
hours=
spot=no
region=${AZ_REGION:-swedencentral}
while [ $# -gt 0 ]; do
    case $1 in
        --size) size=${2:?}; shift 2 ;;
        --hours) hours=${2:?}; shift 2 ;;
        --spot) spot=yes; shift ;;
        --region) region=${2:?}; shift 2 ;;
        *) die "onbekende optie: $1" ;;
    esac
done
[ -n "$size" ] || die "--size ontbreekt"
[[ $hours =~ ^[0-9]+$ ]] && [ "$hours" -ge 1 ] && [ "$hours" -le 23 ] \
    || die "--hours moet 1 t/m 23 zijn; de uitschakeltijd is een tijdstip binnen 24 uur"
[ ! -f "$REPO_ROOT/.azjob" ] || die ".azjob bestaat al: er is nog een actieve VM. Draai eerst az_down.sh"
az account show > /dev/null || die "niet ingelogd; zie README"
# Niet-ASCII maakt cloud-init onleesbaar voor de VM, die dan niets installeert
if LC_ALL=C grep -qP '[^\x00-\x7F]' "$REPO_ROOT/scripts/cloud-init.yaml"; then
    die "cloud-init.yaml bevat niet-ASCII-tekens"
fi

if [ "$spot" = yes ]; then
    # De prijsgrens begrenst het budget; stijgt spot daarboven, dan stopt Azure de VM
    rate=$(python3 "$REPO_ROOT/scripts/az_price.py" "$size" "$region" --spot)
    rate=$(awk -v r="$rate" 'BEGIN { printf "%.4f", r * 1.25 }')
    priority=(--priority Spot --eviction-policy Delete --max-price "$rate")
else
    rate=$(python3 "$REPO_ROOT/scripts/az_price.py" "$size" "$region")
    priority=()
fi
budget=$(awk -v r="$rate" -v h="$hours" 'BEGIN { printf "%.2f", r * h }')

echo "VM-type:     $size ($region, spot: $spot)"
echo "Uurprijs:    EUR $rate, excl. btw"
echo "Maximaal:    $hours uur, daarna automatisch uit"
echo "Budget:      EUR $budget, plus enkele centen per uur voor schijf en IP-adres"
read -r -p 'VM aanmaken? Typ "ja": ' answer || answer=
[ "$answer" = ja ] || { echo "Afgebroken, niets aangemaakt."; exit 1; }

key=${AZ_SSH_KEY:-$HOME/.ssh/openfoam_azure}
if [ ! -f "$key" ]; then
    mkdir -p "$(dirname "$key")"
    chmod 700 "$(dirname "$key")"
    ssh-keygen -q -t ed25519 -N '' -f "$key"
fi

stamp=$(date +%Y%m%d-%H%M)
group=ofjob-$(basename "$STUDY_DIR")-$stamp
vm=ofjob
known=$HOME/.ssh/known_hosts_azure
rm -f "$known"

az group create -n "$group" -l "$region" --tags ofjob=1 -o none
cat > "$REPO_ROOT/.azjob" <<EOF
AZ_RESOURCE_GROUP=$group
AZ_VM=$vm
AZ_SSH_OPTS="-i $key -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$known -o ConnectTimeout=15"
EOF
trap 'echo "FOUT: resourcegroep $group bestaat mogelijk nog; draai az_down.sh" >&2' ERR

ip=$(az vm create -g "$group" -n "$vm" --image Ubuntu2204 --size "$size" \
    --admin-username "${AZ_SSH_USER:-azureuser}" --ssh-key-values "$key.pub" \
    --os-disk-size-gb "${AZ_DISK_GB:-64}" --os-disk-delete-option Delete \
    --public-ip-sku Standard --nsg-rule NONE \
    --custom-data "$REPO_ROOT/scripts/cloud-init.yaml" \
    "${priority[@]}" --query publicIpAddress -o tsv)
az vm auto-shutdown -g "$group" -n "$vm" --time "$(date -u -d "+$hours hours" +%H%M)" -o none

# SSH alleen vanaf het huidige adres van deze pc
mine=$(curl -fsS https://api.ipify.org)
az network nsg rule create -g "$group" --nsg-name "${vm}NSG" -n ssh-from-me --priority 1000 \
    --access Allow --protocol Tcp --destination-port-ranges 22 \
    --source-address-prefixes "$mine/32" -o none
echo "AZ_SSH_HOST=$ip" >> "$REPO_ROOT/.azjob"

source "$REPO_ROOT/scripts/env.sh" --no-foam
require_azure
echo "== Wachten op de installatie op de VM"
# shellcheck disable=SC2086
for _ in $(seq 1 30); do
    ssh -n $AZ_SSH_OPTS "$AZ_TARGET" true 2> /dev/null && break
    sleep 10
done
# shellcheck disable=SC2086
ssh -n $AZ_SSH_OPTS "$AZ_TARGET" "cloud-init status --wait > /dev/null; cloud-init status"
# shellcheck disable=SC2086
cores=$(ssh -n $AZ_SSH_OPTS "$AZ_TARGET" "mkdir -p $AZ_REMOTE_ROOT && nproc")
echo "AZ_CORES_PER_NODE=$cores" >> "$REPO_ROOT/.azjob"

# shellcheck disable=SC2086
ssh -n $AZ_SSH_OPTS "$AZ_TARGET" "sinfo -h -o '%P %a %D %T'; dpkg-query -W openfoam11"
echo "Lokaal: $(dpkg-query -W openfoam11)"
echo "| $(date +%F) | - | vm | $size | 1 | $cores | ${hours}:00:00 |" >> "$STUDY_DIR/NOTES.md"
echo "VM klaar: $cores cores, budget EUR $budget"
