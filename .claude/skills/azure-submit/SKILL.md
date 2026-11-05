---
name: azure-submit
description: "Start een OpenFOAM-job op een tijdelijke Azure-VM: budget tonen, wachten op akkoord, VM aanmaken, syncen, submitten en het job-id vastleggen. Gebruik als een studie een geslaagde smoke-test heeft en de gebruiker een run op Azure wil starten."
---

# azure-submit

Dit kost geld. Eén "ja" dekt één job met het getoonde VM-type, de uren en het budget, tot en met het verwijderen van de VM. Langer rekenen of een groter VM-type vraagt een nieuw "ja".

## 1. Controles (lokaal)
1. De smoke-test van deze studie is geslaagd en `rekenplek` in `case.yaml` klopt.
2. `system/decomposeParDict` bestaat in de case.
3. Er is geen actieve VM: `.azjob` bestaat niet. Bestaat die wel, meld dat en stop.
4. `az account show` werkt; anders inloggen zoals in de README, met `--tenant`.

## 2. Plan en budget
1. Kies het VM-type: `Standard_F8s_v2` voor kleine tests, `Standard_HB120rs_v3` tot ongeveer 10 miljoen cellen. Controleer quota en beschikbaarheid in de regio van `AZ_REGION`: `az vm list-usage -l <regio> -o table` en `az vm list-skus -l <regio> --size <type>`. HB-types hebben nog quota 0 en HBv3 staat niet in de prijslijst van Zweden Centraal.
2. Schat de rekentijd uit eerdere runs. Leg de aanname uit en neem marge.
3. Bepaal `--hours`: installatie (15 minuten), meshen, rekenen, post-processing, ophalen en marge.
4. Haal de prijs op met `python3 scripts/az_price.py <type> <regio>` en noem aan de gebruiker: VM-type, uren, maximaal budget, en of spot wordt gebruikt.
5. Wacht op "ja". Spot alleen als de gebruiker dat kiest: de VM kan dan zonder waarschuwing verdwijnen, met alle data.

## 3. VM en sync
1. `echo ja | scripts/az_up.sh <studie> --size <type> --hours <uren>`.
2. Vergelijk de getoonde OpenFOAM-versies. Verschillen ze, meld dat.
3. Mislukt het, draai dan `az_down.sh`, ook als de VM niet is afgekomen.
4. `scripts/sync_to_azure.sh <studie>` en controleer dat er geen `processor*`, tijdmappen of `smoke/` meegaan.
5. `scripts/sync_to_azure.sh <studie> --execute`.

## 4. Submit
1. `scripts/submit.sh <studie> --dry-run`, met `--ntasks`, `--time` of `--reconstruct` waar nodig. De walltime moet ruim binnen `--hours` vallen.
2. Toon het script kort aan de gebruiker.
3. `echo ja | scripts/submit.sh <studie>` met dezelfde opties.
4. Controleer dat het job-id in de tabel `## Jobs` van `NOTES.md` staat.

## 5. Afsluiten
Meld het job-id, de tijd tot de automatische uitschakeling en het budget. Werk `PROGRESS.md` bij en ga door met de monitor-run-skill.
