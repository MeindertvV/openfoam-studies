# PROGRESS

## Status
- Fase 0 (inventaris): af.
- Fase 1 (repo-structuur): af.
- Fase 2 (skills en permissies): af. `.claude/settings.json` is opgeslagen na akkoord van de gebruiker.
- Fase 3 (lokale proefrun): af, wacht op akkoord.
- Fase 4 (Azure-droogtest): af. pitzDaily draaide op een tijdelijke VM, resultaten opgehaald, alles verwijderd. Rapport: `studies/000-pitzDaily/rapport.md`. Geschatte kosten EUR 0,33 van EUR 0,70.
- Afronden: af. README bijgewerkt en eerste commit gemaakt op `main`; geen remote.

## Fase 3: resultaat
- `studies/000-pitzDaily` uit `incompressibleFluid/pitzDailySteady`, ongewijzigd; `system/` en `0/` zijn gelijk aan de tutorial.
- Mesh: 12225 cellen, maxNonOrtho 5,95, maxSkewness 0,26: voldoet.
- Smoke-test: 100 iteraties, eindigt met End, geen fouten. Laatste residuen: Ux 0,0035, Uy 0,025, p 0,015, k 0,0051, epsilon 0,0040.
- PNG's in `studies/000-pitzDaily/results/`: `residuals_smoke`, `mesh`, `U_slice_smoke`, `p_slice_smoke`.
- Controle op kopie: volledige run convergeert in 287 iteraties. Uy stijgt rond iteratie 100 tijdelijk.
- `forces.py` is niet getest op deze case: de tutorial heeft geen forces-functie. Wel getest op bestaande resultaten in `run/`.
- De fixes staan in het fix-log van `studies/000-pitzDaily/NOTES.md`.
- De deny-regels gelden al in deze sessie: `rm -rf` op een absoluut pad werd geweigerd, ook in de scratchpad.

## Fase 2: wat er is
- Vier skills in `.claude/skills/`: openfoam-setup, azure-submit, monitor-run, post-report.
- `scripts/slurm_post_template.sbatch` en `submit.sh --post`: post-processing als Slurm-job. Soort-kolom in `## Jobs`.
- `pv_render.py --edges`: meshrender zonder veld voor de visuele controle.
- Getest op kopie: render mesh/U/p/contour, `submit.sh --post` met nep-`ssh` en -`rsync`. Skills zelf zijn nog niet doorlopen.
- Bekend: `pv_render.py` kan op een case met alleen `0/` geen veld tonen (reader slaat tijd 0 over), wel de mesh.

## Fase 1: wat er is
- Git geïnitialiseerd (branch `main`). `run/` en `platforms/` staan in `.gitignore`.
- uv 0.13.7 in `~/.local/bin` (niet op PATH gezet; `~/.bashrc` is niet aangepast).
- `.venv` met foamlib 1.6.2, numpy, matplotlib, pyyaml.
- Alle bestanden uit de fase 1-lijst staan er. Extra: `scripts/yaml_get.py`, `post/common.py`, sectie `## Jobs` in `template/NOTES.md`.
- `studies/` is leeg: tests draaiden op kopieën in de scratchpad.

## Fase 1: getest
- Lokaal: new_study, mesh, check_mesh (geslaagd, te lage grens, echte mislukte log, ontbrekende log), smoke, residuals, forces (op bestaande resultaten in `run/`, read-only), pv_render (slice, contour).
- Azure-scripts: alleen offline met nep-`ssh` en -`rsync`, geen verbinding gemaakt. Nog nooit tegen een echt cluster gedraaid.
- `.gitignore`-regels met `git check-ignore`.

## Lokale inventaris
- OpenFOAM: openfoam.org 11 (apt-pakket openfoam11 20240612), `/opt/openfoam11`, `FOAM_TUTORIALS=/opt/openfoam11/tutorials`, Open MPI 4.1.2.
- `simpleFoam` is in v11 een doorverwijzing; echte solver is `foamRun -solver incompressibleFluid`.
- Ontbreekt: gmsh, az CLI, azcopy, xvfb-run, pip.
- SSH: geen `~/.ssh/config`, geen sleutels in `~/.ssh`, geen `~/.azure`.
- Hardware: 12 threads, 7,6 GiB RAM.
- ParaView 5.10.0-RC1: `pvbatch` krijgt `LIBGL_ALWAYS_SOFTWARE=1` via `env.sh` (d3d12-driver crasht) en heeft een X-server nodig (WSLg). Zonder `DISPLAY` breekt hij af.

## Bekende kleine punten
- `pv_render.py`: de cellen in de meshrender zijn zichtbaar, maar verfijning bij wanden blijft dicht; voor detail is ParaView nodig. Fijnere meshes worden op 1600 px snel te dicht.

## Volgende stap
De werkomgeving is klaar. Een nieuwe studie start met `scripts/new_study.sh` en de openfoam-setup-skill.

## Azure-opzet
- De gebruiker heeft geen cluster, alleen een eigen Azure-account (rol Eigenaar). Gekozen: per job één tijdelijke VM met Slurm, daarna alles verwijderen. Geen kosten tussen jobs.
- Wensen: tot ongeveer 10 miljoen cellen; alleen per job betalen met vooraf genoemd budget.
- Afspraak: één "ja" per job dekt aanmaken, syncen, submitten, ophalen en verwijderen, binnen VM-type, uren en budget. Staat in `CLAUDE.md`.
- Gemaakt: `scripts/az_up.sh`, `az_down.sh`, `az_price.py`, `cloud-init.yaml`. `.env` is ingevuld (geen geheimen). De VM-gegevens komen in `.azjob` (in `.gitignore`).
- `azure-cli` 2.92.0 staat in `~/.local/bin`. Ingelogd op de eigen directory; `az login` zonder `--tenant` vindt geen abonnement.
- pitzDaily is klaar voor de run: `system/decomposeParDict` toegevoegd, 4 cores, walltime 20 minuten.
- Echt getest in fase 4: `az_up.sh`, cloud-init, sync, submit, post, ophalen, `az_down.sh`.
- Regio: `swedencentral`; West- en Noord-Europa beperken `Standard_F8s_v2` per zone voor dit abonnement.
- Quota: FSv2 10 vCPU's, regionaal 64 vCPU's in West-Europa, HBv3 0. HBv3 staat niet in de prijslijst van Zweden Centraal; HB176rs_v4 daar EUR 8,40/uur.
- Prijzen West Europe, excl. btw, 2026-11-05: F8s_v2 EUR 0,35/uur; HB120rs_v3 EUR 4,20/uur, spot EUR 0,85/uur.
- Referentie: warmtepomp_825rpm op 64 cores: 1,65 s per iteratie.

## Open
- Voor grote jobs: quotumverhoging aanvragen en regio kiezen (HBv3 West-Europa of HBv4 Zweden Centraal).
- Meshen op de VM: nog geen meshjob. `submit.sh` kent alleen de solver- en post-job. Nodig voor grote meshes.
- Werkelijke kosten van fase 4 controleren in Azure Kostenbeheer.
