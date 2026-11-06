#!/bin/bash
# Gebruik: sbatch --export=ALL,V=<variant> job_post.sbatch
#SBATCH --job-name=acc5x6-post
#SBATCH --partition=hpc
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=slurm-post-%j.out

source /opt/openfoam11/etc/bashrc
export LIBGL_ALWAYS_SOFTWARE=1
set -uo pipefail
cd "$SLURM_SUBMIT_DIR/runs/$V"
root=../../../..

reconstructPar -latestTime > log.reconstructPar 2>&1
foamDictionary -entry writeFormat -set ascii system/controlDict > /dev/null
foamFormatConvert -latestTime > log.convert 2>&1
rm -rf processor*
python3 "$root/post/residuals.py" . > log.post 2>&1
python3 ../../cv_balans.py . "" 36 42 > balans.txt 2>&1
python3 ../../fans_csv.py . > fans.txt 2>&1
mkdir -p plots
pv() { xvfb-run -a pvbatch --force-offscreen-rendering "$root/post/pv_render.py" . "$@" >> log.post 2>&1; }
pv --field T --origin 0 0 40 --normal 0 0 1 -o "$PWD/plots/T_onder_dek.png"
pv --field T --origin 0 0.13 50 --normal 0 1 0 -o "$PWD/plots/T_xz.png"
pv --field U --origin 0 0.13 50 --normal 0 1 0 -o "$PWD/plots/U_xz.png"
pv --field U --origin 0 0 40 --normal 0 0 1 -o "$PWD/plots/U_onder_dek.png"
pv --field T --origin 0 0 50 --normal 0 0 1 -o "$PWD/plots/T_bundels.png"
