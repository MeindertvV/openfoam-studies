# OpenFOAM-studies
<img width="1302" height="762" alt="afbeelding" src="https://github.com/user-attachments/assets/49b840a2-a1c1-4904-aa90-7a4c42ff21ac" />

Werkomgeving voor OpenFOAM-studies: kleine tests lokaal in WSL, meshing en runs op een tijdelijke Azure-VM met Slurm, post-processing headless. Regels en fases staan in [CLAUDE.md](CLAUDE.md), de stand van zaken in [PROGRESS.md](PROGRESS.md).

## Studies
| Studie | Inhoud | Stand |
|---|---|---|
| [000-pitzDaily](studies/000-pitzDaily/rapport.md) | Tutorial, droogtest van de Azure-keten | Af |
| [001-acc-aframe](studies/001-acc-aframe/rapport.md) | Enkel A-frame met fan, 229k cellen, windstil | Af: 507 m3/s, warmtebalans -1,4% |
| [002-acc-5x6](studies/002-acc-5x6/rapport.md) | 5x6 grid, 4M cellen: windstil, wind 9 m/s, wind met kruisvormig scherm | Drie cases af, 1200 iteraties zonder ontsporing. Warmtebalans wind en scherm 4-5%, boven het criterium van 2% |

### Uitkomst 002 in het kort
| | Windstil | Wind | Wind + scherm |
|---|---|---|---|
| Totaal debiet (m3/s) | 15.103 | 12.527 (-17%) | 13.324 (-12%) |
| Debiet per fan, rij aan de windzijde (m3/s) | 500-506 | 259-334 | 371-392 |

Het scherm haalt een deel van het windverlies terug, vooral in de eerste rij. De scherm-K (10) is een aanname, en de convergentie is niet volledig aangetoond. Zie het rapport.

### Volgende stap
- 002: warmtebalans onder 2% krijgen en K van het scherm variëren.

## Data en ParaView
Werkwijze en fixes per studie staan in `NOTES.md`, de runinstellingen in `case/`, `runs/` en `mkRuns.py`. Velden en meshes staan niet in git, maar in de releases:

| Release | Inhoud |
|---|---|
| [data-5x6-v1](https://github.com/MeindertvV/openfoam-studies/releases/tag/data-5x6-v1) | 002 windstil (t=1000) en oude wind (t=300, niet geconvergeerd) |
| [data-5x6-v2](https://github.com/MeindertvV/openfoam-studies/releases/tag/data-5x6-v2) | 002 wind_v2 en scherm_v2 (t=1200), met mesh |

Uitpakken staat in het rapport per studie. Open daarna het `.foam`-bestand van de run met Case Type: Reconstructed Case. Poreuze zones, zoals de bundels en het scherm, zie je pas na **Read Zones** (tandwiel in Properties) en het aanvinken onder Mesh Regions.

## Installatie
```bash
cp .env.example .env
uv venv .venv --python 3.10
uv pip install --python .venv/bin/python -r requirements.txt
```

Azure eenmalig: inloggen met `~/.local/bin/az login --tenant <directory>.onmicrosoft.com --use-device-code`. Zonder `--tenant` vindt een persoonlijk account geen abonnement. `az` en `gh` staan in `~/.local/bin`, niet op PATH.

## Nieuwe studie
```bash
scripts/new_study.sh naam --tutorial incompressibleFluid/pitzDailySteady
```
Vul daarna `studies/NNN-naam/case.yaml` in en vraag Claude: "gebruik de openfoam-setup-skill".

## Rekenen op Azure
Vraag Claude: "gebruik de azure-submit-skill". Claude noemt eerst VM-type, uren en maximaal budget. Na jouw "ja" gebeurt de hele job:

1. `scripts/az_up.sh` maakt een tijdelijke VM met OpenFOAM en Slurm.
2. `scripts/sync_to_azure.sh` en `scripts/submit.sh` starten de berekening.
3. De monitor-run-skill volgt de job.
4. De post-report-skill maakt de PNG's en CSV's, haalt ze op en schrijft `rapport.md`.
5. `scripts/az_down.sh` verwijdert alles, zodat er tussen jobs geen kosten zijn.

Data op de VM verdwijnt met de VM. Vraag vooraf om `--full` als je de tijdmappen wilt bewaren.

Regio en quota: standaard `swedencentral`, maar daar is het quotum 10 vCPU. Voor 16 kernen of meer gebruik je `--region westeurope` (64 vCPU). Een F16as_v6 kost daar ongeveer €1,19 per uur; een run van 1200 iteraties op 4M cellen duurt ongeveer 70 minuten.

## Scripts
| Script | Doel |
|---|---|
| `scripts/env.sh` | Laadt `.env`, de OpenFOAM-omgeving en `.venv` |
| `scripts/new_study.sh` | Kopieert `template/` naar `studies/NNN-naam/` |
| `scripts/mesh.sh` | Draait de meshstappen en `checkMesh`, logt naar `log.*` |
| `scripts/check_mesh.py` | Toetst `log.checkMesh` aan de drempels uit `case.yaml` |
| `scripts/smoke.sh` | Draait N iteraties in `smoke/` en daarna `foamLog` |
| `scripts/az_up.sh` | Toont het budget, maakt na `ja` een tijdelijke VM met OpenFOAM en Slurm |
| `scripts/az_down.sh` | Verwijdert de VM en alles erop, na `ja` |
| `scripts/az_price.py` | Haalt de actuele uurprijs van een VM op |
| `scripts/cloud-init.yaml` | Installatie van de VM |
| `scripts/sync_to_azure.sh` | Stuurt een studie naar de VM; standaard dry-run |
| `scripts/sync_from_azure.sh` | Haalt PNG/CSV/logs/postProcessing op, geen tijdmappen |
| `scripts/slurm_template.sbatch` | Sjabloon voor de Slurm-job |
| `scripts/slurm_post_template.sbatch` | Sjabloon voor de post-processing-job |
| `scripts/submit.sh` | Vult een sjabloon in, vraagt bevestiging, submit, schrijft het job-id naar `NOTES.md` |
| `scripts/yaml_get.py` | Leest één waarde uit `case.yaml` voor de shellscripts |
| `post/residuals.py` | Residuen naar PNG |
| `post/forces.py` | Forces en coefficients naar PNG en CSV |
| `post/pv_render.py` | Slice of contour van een veld naar PNG via pvbatch |
