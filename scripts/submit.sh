#!/bin/bash
# Vult het Slurm-sjabloon in, toont het script, vraagt bevestiging, submit en schrijft
# het job-id naar NOTES.md. Waarden komen uit case.yaml en .env; opties gaan daarboven.
# Met --post wordt het de post-processing-job in plaats van de solverjob.
# Gebruik: submit.sh <studie> [--nodes N] [--ntasks N] [--time HH:MM:SS] [--partition P]
#                    [--reconstruct] [--post] [--dry-run]
set -euo pipefail
source "$(dirname "$0")/env.sh" --no-foam
resolve_study "${1:-}"
require_azure AZ_OF_LOAD
shift

spec() { python3 "$REPO_ROOT/scripts/yaml_get.py" "$STUDY_DIR/case.yaml" "$1"; }

kind=solver
for arg in "$@"; do
    [ "$arg" = --post ] && kind=post
done

if [ "$kind" = post ]; then
    nodes=1
    ntasks=1
    walltime=00:30:00
else
    nodes=$(spec rekenplek.nodes)
    ntasks=$(spec rekenplek.cores)
    walltime=$(spec rekenplek.walltime)
fi
partition=${AZ_PARTITION:-}
reconstruct=no
dry_run=no
while [ $# -gt 0 ]; do
    case $1 in
        --nodes) nodes=${2:?}; shift 2 ;;
        --ntasks) ntasks=${2:?}; shift 2 ;;
        --time) walltime=${2:?}; shift 2 ;;
        --partition) partition=${2:?}; shift 2 ;;
        --reconstruct) reconstruct=yes; shift ;;
        --post) shift ;;
        --dry-run) dry_run=yes; shift ;;
        *) die "onbekende optie: $1" ;;
    esac
done

[ -n "$partition" ] || die "AZ_PARTITION is leeg; vul .env in"
[[ $nodes =~ ^[1-9][0-9]*$ ]] || die "ongeldig aantal nodes: $nodes"
[[ $ntasks =~ ^[1-9][0-9]*$ ]] || die "ongeldig aantal tasks: $ntasks"
[[ $walltime =~ ^([0-9]+-)?[0-9]+:[0-9]{2}:[0-9]{2}$ ]] || die "ongeldige walltime: $walltime"
if [ -n "${AZ_CORES_PER_NODE:-}" ] && [ "$ntasks" -gt $(( nodes * AZ_CORES_PER_NODE )) ]; then
    die "$ntasks tasks past niet op $nodes node(s) van $AZ_CORES_PER_NODE cores"
fi
if [ "$kind" = solver ] && [ ! -f "$CASE_DIR/system/decomposeParDict" ]; then
    die "system/decomposeParDict ontbreekt in de case"
fi

module=$(spec fysica.solver)
solver="foamRun${module:+ -solver $module}"
name=$(basename "$STUDY_DIR")
fields=$(spec output.velden | xargs)
extra=
[ -n "${AZ_ACCOUNT:-}" ] && extra+="#SBATCH --account=$AZ_ACCOUNT"$'\n'
[ -n "${AZ_QOS:-}" ] && extra+="#SBATCH --qos=$AZ_QOS"$'\n'
extra=${extra%$'\n'}

if [ "$kind" = post ]; then
    job=$(<"$REPO_ROOT/scripts/slurm_post_template.sbatch")
    job_name=$name-post
    job_file=job_post.sbatch
else
    job=$(<"$REPO_ROOT/scripts/slurm_template.sbatch")
    job_name=$name
    job_file=job.sbatch
fi
job=${job//@@JOB_NAME@@/"$job_name"}
job=${job//@@PARTITION@@/"$partition"}
job=${job//@@NODES@@/"$nodes"}
job=${job//@@NTASKS@@/"$ntasks"}
job=${job//@@TIME@@/"$walltime"}
job=${job//@@EXTRA_SBATCH@@/"$extra"}
job=${job//@@OF_LOAD@@/"$AZ_OF_LOAD"}
job=${job//@@POST_LOAD@@/"${AZ_POST_LOAD:-}"}
job=${job//@@FIELDS@@/"$fields"}
job=${job//@@PV_CMD@@/"${AZ_PV_CMD:-pvbatch --force-offscreen-rendering}"}
job=${job//@@SOLVER@@/"$solver"}
job=${job//@@MPI_CMD@@/"${AZ_MPI_CMD:-mpirun -np \$SLURM_NTASKS}"}
job=${job//@@RECONSTRUCT@@/"$reconstruct"}

printf '%s\n' "$job" > "$STUDY_DIR/$job_file"
cat "$STUDY_DIR/$job_file"
echo "-----"
echo "$kind: $nodes node(s), $ntasks tasks, walltime $walltime, partitie $partition"
[ "$dry_run" = no ] || { echo "Dry-run: niet gesubmit."; exit 0; }

read -r -p 'Submit naar Slurm? Typ "ja": ' answer || answer=
[ "$answer" = ja ] || { echo "Afgebroken, niets gesubmit."; exit 1; }

remote=$AZ_REMOTE_ROOT/studies/$name/case
rsync -e "ssh ${AZ_SSH_OPTS:-}" "$STUDY_DIR/$job_file" "$AZ_TARGET:$remote/$job_file"
# shellcheck disable=SC2086
output=$(ssh -n ${AZ_SSH_OPTS:-} "$AZ_TARGET" "cd '$remote' && sbatch --parsable $job_file")
jobid=${output%%;*}
[[ $jobid =~ ^[0-9]+$ ]] || die "onverwachte uitvoer van sbatch: $output"

echo "| $(date +%F) | $jobid | $kind | $partition | $nodes | $ntasks | $walltime |" >> "$STUDY_DIR/NOTES.md"
echo "Job $jobid gesubmit en vastgelegd in NOTES.md"
