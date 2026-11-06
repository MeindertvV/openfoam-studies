#!/bin/bash
#SBATCH --job-name=acc5x6-mesh
#SBATCH --partition=hpc
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=01:00:00
#SBATCH --output=slurm-mesh-%j.out

source /opt/openfoam11/etc/bashrc
set -euo pipefail
cd "$SLURM_SUBMIT_DIR/case"

python3 mkGeometry.py
blockMesh > log.blockMesh 2>&1
surfaceFeatures > log.surfaceFeatures 2>&1
foamDictionary -entry numberOfSubdomains -set "$SLURM_NTASKS" system/decomposeParDict > /dev/null
decomposePar -noFields > log.decomposePar 2>&1
mpirun -np "$SLURM_NTASKS" snappyHexMesh -parallel -overwrite > log.snappyHexMesh 2>&1
reconstructPar -constant -noFields > log.reconstructPar 2>&1
rm -rf processor*
topoSet > log.topoSet 2>&1
checkMesh -allGeometry -allTopology > log.checkMesh 2>&1 || true
cd ..
for v in windstil wind scherm; do
    cp -r case/constant/polyMesh "runs/$v/constant/"
    cp -r case/constant/geometry "runs/$v/constant/"
done
(cd runs/scherm && topoSet > log.topoSet 2>&1)
