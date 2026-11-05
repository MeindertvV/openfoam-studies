---
name: monitor-run
description: "Volgt een lopende OpenFOAM-job op de tijdelijke Azure-VM: squeue en sacct via ssh, laatste logregels, residuen- en Courant-trend, en meldt divergentie of stagnatie. Gebruik als de gebruiker vraagt hoe een job ervoor staat of na een submit."
---

# monitor-run

Alleen lezen. Nooit `scancel` zonder expliciet "ja", ook niet bij divergentie: meld het en wacht.

Zet deze regel vooraan in elke Bash-aanroep; de variabelen blijven niet staan tussen aanroepen:
```bash
source scripts/env.sh --no-foam && require_azure
```
Het job-id staat in de tabel `## Jobs` van `NOTES.md`.

## 1. Jobstatus
```bash
ssh $AZ_SSH_OPTS "$AZ_TARGET" "squeue -j <jobid> -o '%i %T %M %l %D %R'"
```
`sacct` werkt niet op de VM: accounting staat uit. Staat de job niet meer in `squeue`, dan is hij klaar: controleer in stap 2 dat de log met `End` eindigt en dat `slurm-<jobid>.out` leeg is.
PENDING: meld de reden uit `%R` en stop.

## 2. Log
Het pad is `$AZ_REMOTE_ROOT/studies/<studie>/case`.
```bash
ssh $AZ_SSH_OPTS "$AZ_TARGET" "cd <pad> && tail -n 20 log.foamRun && grep -n -m1 -A8 -E 'FOAM FATAL|Floating point exception' log.foamRun slurm-<jobid>.out"
```
Doe hier alleen `tail` en `grep`; rekenwerk loopt via Slurm.

## 3. Trend
1. `scripts/sync_from_azure.sh <studie>`.
2. `python3 post/residuals.py <studie>` toont de laatste residuen en maakt de PNG.
3. Alleen transient: `grep -E '^Courant' studies/<studie>/case/log.foamRun | tail -n 5`.

## 4. Beoordelen
Toets aan `convergentie` in `case.yaml`.

| Melding | Teken |
|---|---|
| Divergentie | `FOAM FATAL`, floating point exception of `nan` in de log; initial residual stijgt een factor 10 over de laatste 20% van de iteraties; Courant max groeit snel of ligt ruim boven de waarde in `controlDict` |
| Stagnatie | Residuen veranderen minder dan 10% over de laatste 20% van de iteraties en voldoen nog niet aan het criterium |
| Convergeert | Residuen dalen of voldoen al aan het criterium |

## 5. Rapporteren
Geef in enkele regels: status, verstreken tijd, tijd of iteratie, laatste residuen, Courant, oordeel. Vergelijk de voortgang met de uren uit `az_up.sh`: redt de job het niet binnen de automatische uitschakeling, meld dat dan op tijd, want langer doorrekenen vraagt een nieuw "ja". Stel bij divergentie de eerste fout voor en vraag wat de gebruiker wil. Is de job klaar of gefaald, ga dan door met de post-report-skill, zodat de VM niet blijft staan.
