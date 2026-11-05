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
@@POST_LOAD@@
set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
root=../../..

if [ -d processor0 ]; then
    reconstructPar -latestTime -newTimes > log.reconstructPar 2>&1
fi

python3 "$root/post/residuals.py" . > log.post 2>&1
if compgen -G 'postProcessing/*/*/forces.dat' > /dev/null \
    || compgen -G 'postProcessing/*/*/forceCoeffs.dat' > /dev/null; then
    python3 "$root/post/forces.py" . >> log.post 2>&1
fi
for field in @@FIELDS@@; do
    @@PV_CMD@@ "$root/post/pv_render.py" . --field "$field" >> log.post 2>&1
done
