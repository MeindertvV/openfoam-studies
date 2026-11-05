#!/bin/bash
#SBATCH --job-name=@@JOB_NAME@@
#SBATCH --partition=@@PARTITION@@
#SBATCH --nodes=@@NODES@@
#SBATCH --ntasks=@@NTASKS@@
#SBATCH --time=@@TIME@@
#SBATCH --output=slurm-%j.out
@@EXTRA_SBATCH@@

# OpenFOAM's bashrc verdraagt set -e niet
@@OF_LOAD@@
set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
solver="@@SOLVER@@"
log="log.${solver%% *}"

foamDictionary -entry numberOfSubdomains -set "$SLURM_NTASKS" system/decomposeParDict > /dev/null
decomposePar > log.decomposePar 2>&1
@@MPI_CMD@@ $solver -parallel > "$log" 2>&1

if [ "@@RECONSTRUCT@@" = yes ]; then
    reconstructPar -latestTime > log.reconstructPar 2>&1
fi
