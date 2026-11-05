# Notities

## Gekozen basistutorial + reden
- Tutorial: incompressibleFluid/pitzDailySteady
- Reden: stationaire variant van pitzDaily, in OpenFOAM 11 de tegenhanger van simpleFoam.

## Afwijkingen ten opzichte van de tutorial
- `system/decomposeParDict` toegevoegd vanuit `incompressibleFluid/impeller` (4 delen, scotch), nodig voor de parallelle run op Azure.

## Fix-log
| Symptoom | Oorzaak | Wijziging | Verificatie |
|---|---|---|---|
| `pvbatch`: `No module named 'paraview'` | Ubuntu-pvbatch start zonder dist-packages op `sys.path` | `pv_render.py` voegt dat pad toe als de import faalt | Render loopt verder tot de renderstap |
| `pvbatch`: SIGSEGV bij het renderen | d3d12-driver van WSL | `env.sh` zet `LIBGL_ALWAYS_SOFTWARE=1` als `/dev/dxg` bestaat | PNG's van U en p aangemaakt |
| Render met veel witruimte, cellen niet te zien | Vast beeldformaat 2:1 | `frame_slice` snijdt beeld bij op de geometrie, legenda onder | `mesh.png` en `U_slice_smoke.png` bekeken |
| Eerste VM: `sinfo` en `openfoam11` ontbreken, cloud-init `degraded done` | Letter `é` in `cloud-init.yaml` maakte de YAML onleesbaar (`#xdce9`) | Tekst naar ASCII; `az_up.sh` weigert niet-ASCII | Tweede VM: `sinfo` en OpenFOAM werken |
| Jobscript stopt bij het laden van OpenFOAM | `bashrc` verdraagt `set -e` niet | In beide sjablonen OpenFOAM laden vóór `set -euo pipefail` | Jobscript lokaal gedraaid op een kopie |
| `sacct`: accounting storage is disabled | Slurm-accounting staat niet aan op de VM | Skills controleren `squeue` en `End` in de log | Job 1 en 2 zo beoordeeld |
| Legenda toont `U` zonder aanduiding grootte | ParaView negeert de aangepaste titel | `ComponentTitle` op `Magnitude` | Legenda toont `U Magnitude` |

## Jobs
| Datum | Job-id | Soort | Partitie | Nodes | Tasks | Walltime |
|---|---|---|---|---|---|---|
| 2026-11-05 | - | vm | Standard_F8s_v2 | 1 | 8 | 1:00:00 |
| 2026-11-05 | 1 | solver | hpc | 1 | 4 | 00:20:00 |
| 2026-11-05 | 2 | post | hpc | 1 | 1 | 00:30:00 |
