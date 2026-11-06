# OpenFOAM-studies

Kleine tests draaien lokaal in WSL. Meshing en CFD-runs draaien op een tijdelijke VM in Azure met Slurm, die per job wordt aangemaakt en daarna verwijderd. Post-processing gebeurt headless.

Lees bij een nieuwe of onderbroken sessie eerst `PROGRESS.md` en ga daar verder. Wees zuinig: geen lange uitleg, alleen wat de gebruiker moet weten of beslissen.

## Harde regels
- Noem vóór elke job het maximale budget in euro's. Laat na een job nooit een VM staan: `scripts/az_down.sh` hoort bij elke job.
- Geen keys, wachtwoorden, IP's of hostnamen in bestanden die in git komen. Gebruik `.env` (in `.gitignore`) plus `.env.example`.
- Niets overschrijven wat al in deze map staat zonder te vragen. `run/` en `platforms/` zijn bestaand werk en blijven onaangeroerd.
- Alle rekenwerk op de VM gaat via Slurm, ook post-processing. De VM is tegelijk login- en rekennode.

## Versies
| Plek | OpenFOAM | Laden |
|---|---|---|
| Lokaal | openfoam.org 11 (`/opt/openfoam11`) | `source scripts/env.sh` |
| Tijdelijke VM | openfoam.org 11, zelfde apt-bron; `az_up.sh` toont de versie | `AZ_OF_LOAD` in `.env` |

**Waarschuwing:** meld het de gebruiker als lokaal en de VM verschillen, en test dan niet op de aanname dat een case op beide hetzelfde werkt.

In v11 zijn `simpleFoam` en `pimpleFoam` alleen doorverwijzingen. Gebruik `foamRun` met `solver incompressibleFluid` in `system/controlDict`.

## Fases per studie
1. **Spec:** `case.yaml` volledig invullen.
2. **Tutorial-first baseline:** passende tutorial kopiëren en ongewijzigd laten draaien.
3. **Minimale edits:** alleen wat de spec vraagt; afwijkingen in `NOTES.md`.
4. **Mesh:** `scripts/mesh.sh`.
5. **check_mesh:** `scripts/check_mesh.py`.
6. **STOP** voor de visuele meshcontrole door de gebruiker.
7. **Smoke-test lokaal:** `scripts/smoke.sh`.
8. **Azure-submit** na akkoord op het budget: `scripts/az_up.sh`, `scripts/sync_to_azure.sh`, `scripts/submit.sh`.
9. **Monitoring.**
10. **Headless post**, resultaten ophalen en de VM verwijderen: `scripts/az_down.sh`.
11. **Rapport** tegen het acceptatiecriterium in `case.yaml`.

## Werkregels
- Bij een fout: los de EERSTE fout in de log op, niet de vervolgfouten.
- Elke fix komt in het fix-log van `NOTES.md`: symptoom | oorzaak | wijziging | verificatie.
- Nooit een case vanaf nul schrijven als er een passende tutorial is.
- Elke case en rundir krijgt een `.foam`-bestand voor ParaView, ook kopieën, varianten en opgehaalde resultaten. `new_study.sh`, `mesh.sh` en `smoke.sh` doen dit zelf; noem het pad aan de gebruiker.
