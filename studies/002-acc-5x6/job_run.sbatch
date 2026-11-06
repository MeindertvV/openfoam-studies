#!/bin/bash
# Gebruik: sbatch --export=ALL,V=<variant>,N=<iteraties> job_run.sbatch
#SBATCH --job-name=acc5x6-run
#SBATCH --partition=hpc
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=02:00:00
#SBATCH --output=slurm-run-%j.out

source /opt/openfoam11/etc/bashrc
set -euo pipefail
cd "$SLURM_SUBMIT_DIR/runs/$V"

foamDictionary -entry numberOfSubdomains -set "$SLURM_NTASKS" system/decomposeParDict > /dev/null
foamDictionary -entry endTime -set "$N" system/controlDict > /dev/null
foamDictionary -entry writeInterval -set 150 system/controlDict > /dev/null
foamDictionary -entry purgeWrite -set 2 system/controlDict > /dev/null
foamDictionary -entry writeFormat -set binary system/controlDict > /dev/null
decomposePar -force > log.decomposePar 2>&1
mpirun -np "$SLURM_NTASKS" foamRun -parallel > log.foamRun 2>&1
