---
name: openfoam-setup
description: "Zet een OpenFOAM-studie op van case.yaml tot geslaagde lokale smoke-test. Gebruik als de gebruiker een nieuwe studie wil starten, een case wil opzetten of \"gebruik de openfoam-setup-skill\" zegt. Stopt na check_mesh voor de visuele meshcontrole."
---

# openfoam-setup

Lees eerst `CLAUDE.md` en `PROGRESS.md`. Alles draait lokaal; niets op Azure. Werk vanuit de repo-root.

## 1. Spec
1. Bepaal de studie (`studies/NNN-naam/`). Bestaat die niet: `scripts/new_study.sh <naam>`.
2. Lees `case.yaml`. Stel alle ontbrekende velden in één keer als vraag; gok niets.
3. Controleer `acceptatie` en `convergentie`: ze moeten meetbaar zijn.

## 2. Tutorial-first baseline
1. Zoek een passende tutorial: `find $FOAM_TUTORIALS -type d -name '<term>*'` (na `source scripts/env.sh`).
2. Schrijf nooit een case vanaf nul als er een passende tutorial is. Is er echt geen: meld dat en vraag akkoord.
3. Is `case/` leeg, kopieer de tutorial: `cp -r $FOAM_TUTORIALS/<pad>/. studies/<studie>/case/`, of maak de studie met `new_study.sh <naam> --tutorial <pad>`.
4. Vul in `NOTES.md` de tutorial en de reden in.
5. Draai de ongewijzigde tutorial: `scripts/mesh.sh <studie>` en `scripts/smoke.sh <studie> 10`. Faalt dit, repareer dan eerst dat.

## 3. Minimale edits
1. Pas alleen aan wat `case.yaml` vraagt: geometrie, randvoorwaarden, stofeigenschappen, tijden, output.
2. Gebruik in v11 `foamRun` met `solver <module>` in `system/controlDict`, niet `simpleFoam` of `pimpleFoam`.
3. Staat `doel_yPlus` in `case.yaml`, zet dan `#includeFunc yPlus` in `functions` van `controlDict`, zodat de waarde na de run beschikbaar is.
4. Is `rekenplek.plek` azure, voeg dan `system/decomposeParDict` toe vanuit de tutorial die het dichtst in de buurt komt.
5. Noteer elke afwijking onder "Afwijkingen ten opzichte van de tutorial" in `NOTES.md`.

## 4. Mesh en check_mesh
1. `scripts/mesh.sh <studie>`.
2. `scripts/check_mesh.py <studie>`.
3. Bij falen: los de EERSTE fout in de log op, niet de vervolgfouten. Zet elke fix in het fix-log van `NOTES.md`: symptoom | oorzaak | wijziging | verificatie. Herhaal stap 1 en 2.
4. Render de mesh voor de controle: `source scripts/env.sh && pvbatch --force-offscreen-rendering post/pv_render.py <studie> --edges`. Voeg `--origin` en `--normal` toe voor een zinvolle doorsnede.

## 5. STOP: visuele meshcontrole
Stop hier. Toon de getallen uit `check_mesh.py` en de PNG uit `results/`, en meld dat de gebruiker de mesh ook kan openen met `paraFoam -case studies/<studie>/case`. Ga pas verder na akkoord van de gebruiker.

## 6. Smoke-test
1. `scripts/smoke.sh <studie>`.
2. `python3 post/residuals.py studies/<studie>/smoke`.
3. De test is geslaagd als `smoke.sh` exit 0 geeft, er geen `FOAM FATAL` in de log staat en de residuen over het geheel dalen. Meld een veld dat aan het eind stijgt; een kleine tijdelijke stijging is geen fout (pitzDaily: Uy stijgt rond iteratie 100 en de run convergeert daarna gewoon).
4. Bij falen: eerste fout oplossen en in het fix-log zetten.

## 7. Afsluiten
Rapporteer in enkele regels: tutorial, afwijkingen, meshgetallen, smoke-resultaat en de residuen-PNG. Werk `PROGRESS.md` bij. De volgende stap is de azure-submit-skill, na akkoord.
