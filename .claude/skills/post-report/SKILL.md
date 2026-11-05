---
name: post-report
description: "Post-processing van een afgeronde OpenFOAM-run: headless op de tijdelijke VM via Slurm, alleen PNG en CSV ophalen, de VM verwijderen en een kort rapport.md tegen het acceptatiecriterium. Gebruik als een Azure-job klaar is of de gebruiker om resultaten vraagt."
---

# post-report

Post-processing draait als Slurm-job op de VM. Dit valt onder het "ja" van de job, zolang het binnen de uren en het budget blijft.

## 1. Controles
1. Bevestig dat de job niet meer in `squeue` staat en dat `log.foamRun` op de VM met `End` eindigt. Is de job gefaald, sla dan stap 2 over en haal alleen de logs op; laat de VM staan tot de gebruiker heeft gekozen.

## 2. Post-job
1. Zijn `post/` of `scripts/` lokaal gewijzigd: eerst `scripts/sync_to_azure.sh <studie> --execute`.
2. `scripts/submit.sh <studie> --post --dry-run`. Toon het script. De job doet reconstructPar waar nodig, residuals, forces en een render per veld uit `output.velden`.
3. Dan: `echo ja | scripts/submit.sh <studie> --post`.
4. Volg de job met `squeue` zoals in de monitor-run-skill. Bij falen: kijk in `log.post` en de `slurm-<jobid>.out`.

## 3. Ophalen
1. `scripts/sync_from_azure.sh <studie>`. Dit haalt alleen PNG, CSV, logs en postProcessing op, geen tijdmappen. Gebruik `--full` alleen als de gebruiker daarom vraagt.
2. Controleer dat de PNG's en logs lokaal staan.
3. Wil de gebruiker de velden bewaren? Vraag dat vóór het verwijderen, tenzij al afgesproken: daarna zijn ze weg. De VM kost per minuut, dus wacht hier niet onnodig.
4. `echo ja | scripts/az_down.sh`, en controleer dat de melding `Verwijderd:` verschijnt zonder `LET OP`.

## 4. Beoordelen
1. Bekijk de PNG's in `results/`.
2. Lees waarden uit de CSV's of uit de uitvoer in `log.post`, zoals het gemiddelde over de laatste 10%.
3. Staat `doel_yPlus` in `case.yaml`: lees `postProcessing/yPlus/*/yPlus.dat`.
4. Toets aan `convergentie` en `acceptatie` in `case.yaml`.

## 5. Rapport
Schrijf `studies/<studie>/rapport.md`:

```markdown
# Rapport: <titel>
Conclusie: <voldoet / voldoet niet> aan het acceptatiecriterium, in één zin.

| Criterium | Eis | Gemeten | Oordeel |
|---|---|---|---|

## Run
Job-id, cores, walltime, mesh (cellen, maxNonOrtho, maxSkewness).

## Resultaten
De relevante PNG's met één regel uitleg.

## Opmerkingen
Afwijkingen, onzekerheden, vervolgstappen.
```

Noem een criterium dat niet is gehaald of niet te meten was gewoon zo. Noem ook de werkelijke VM-tijd en de geschatte kosten tegenover het budget. Werk `PROGRESS.md` bij.
