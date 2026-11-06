# Notities

## Gekozen basistutorial + reden
- Tutorial: fluid/hotRoomBoussinesqSteady
- Reden: `fluid`-module met drijfkracht, stationair. Warme pluim en terugstroming zijn juist het doel van latere studies.

## Afwijkingen ten opzichte van de tutorial
- Geometrie: `mkGeometry.py` (STL's, `nx`/`ny` voor tegelen), snappyHexMesh in plaats van alleen blockMesh; `meshQualityDict` uit motorBikeSteady.
- Randen: ground, structure, sides, top in plaats van gesloten kamer; open randen als `fluid`-tutorials met `prghTotalHydrostaticPressure` en `ph_rgh`, zoals `multicomponentFluid/smallPoolFire3D`; `setFields` vervallen, T overal 288 K.
- `perfectGas` met `pRef` 1e5 uit `fluid/hotRoom`, niet Boussinesq. Omgeving is daarmee isotherm, dus iets stabieler dan neutraal.
- Stofeigenschappen: lucht, Cp 1006, mu 1,8e-5, Pr 0,71.
- `fvModels` nieuw: poreus uit `fluid/angledDuct`, `heatTransfer` (vaste stoomtemperatuur), coded fan met drukstap en swirl.
- `fvSolution`/`fvSchemes`: GAMG voor p_rgh, geen pRefCell (open rand), lokale tijdstap in plaats van steadyState.
- Fan afwijkend van de keuze "fanPressureJump": die heeft geen swirl, daarom een coded bron met dezelfde fancurve.
- Bundels zijn cellZones op celmiddelpunt (trapjes, geen conforme rand); doorsnede 2 tot 3 cellen.
- Bundeldikte 0,5 m in plaats van 0,22 m, zodat twee cellen passen; f is daarop geschaald. Bundellengte ~10 m (bron: 10,7 m), pitch 12,6 m.

## Open punten
- check_mesh.py faalt alleen op 8533 concave cellen uit `-allGeometry`; gewone `checkMesh` geeft Mesh OK. Ze zitten ook bij boxranden zonder geometrie (tot z 120).
- Coded fan is nog niet gecompileerd of gedraaid.

## Eerste run (1500 iteraties, lokale tijdstap, 38 minuten, serieel)
- Fan Q 583 m3/s, dp 117 Pa, spreiding 0,2 m3/s over 200 iteraties. Criterium 500 m3/s +/-10%: niet gehaald (+17%).
- Warmte bundels 9,50 MW, spreiding 0,01%.
- Randmeting was onbruikbaar (-5,5 MW, massa door sides en top wisselt ~180 kg/s). `cv_balans.py` meet over een box rond de unit met upwind-T: netto massa -0,008 kg/s, Q lucht 9,31 MW tegen Q bundels 9,47 MW, balansfout -1,7%.
- Plenum is dicht (flood-fill bereikt buiten niet); alle 560 kg/s gaat door de bundels. Dat is 463 m3/s, niet de 583 m3/s uit de fanmonitor.
- Residuen aan het eind (eerste corrector): p_rgh 0,055, Uy 0,014, Ux 0,011, h 2e-4. De vergelijking 5e-4 tegen 0,06 uit de 60-iteratietest was fout: die 5e-4 was een latere corrector.

## Fix-log
| Symptoom | Oorzaak | Wijziging | Verificatie |
|---|---|---|---|
| snappyHexMesh stopt: `resolveFeatureAngle` undefined | zelf geschreven dict gebruikte een oude sleutelnaam | `resolveTreeAngle` vervangen door `resolveFeatureAngle 30` | snappyHexMesh eindigt met End |
| Skewness 10,1 op bundelvoet (z 48) en nok (z 57) | bundel als faceZone gesnapt tegen de constructie; de snijlijn is geen feature, dus scherpe wiggen | bundels niet meer snappen: cellZone achteraf met `topoSet` uit dezelfde STL | maxSkewness 2,4, maxNonOrtho 42 |
| Bundelzones ongelijk: L 3084, R 8595 cellen; eerder 1128 | eerst sneden `includeCut false` de schijf weg; daarna gaf `useSurfaceOrientation` verkeerde normalen op de rechterbundel (onnodige hoekwissel in `mkGeometry.py`) | hoekwissel weg, `useSurfaceOrientation true`, f en htc herschaald op het vrije bundelvolume | L en R beide 3084 cellen, samen ~96 m3 |
| FOAM FATAL "Negative initial temperature" in iteratie 2; Q sprong naar 901 m3/s; met 10x lagere dp exact dezelfde continuiteitsfout | `fluid` zet bij de start `p_rgh = p - rho*gh`; met p = 0 in 0/ geeft dat ~1760 Pa hoogteverschil tegen p0 = 0 op de open rand | `hydrostaticInitialisation yes` met 0/ph_rgh. De eerdere dp-relaxatie (`dpRelax` 0.1) in de fan blijft staan tegen aan-uit-gedrag rond de fancurve | smoke 100 iteraties zonder fout |
| FOAM FATAL "Maximum number of iterations exceeded" en spurieuze ph_rgh van 8 Pa | Boussinesq telt p/rho mee in h: over 144 m hoogte daalt T ~1,4 K terwijl rho(T) omhoog stijgt, dus onecht instabiel | `perfectGas`, `pRef` 1e5, open randen gesplitst in sides en top (hydrostatisch) | smoke 100 iteraties zonder fout |
| FPE in GAMG rond iteratie 330-490, plotselinge divergentie; één cel met p_rgh 36 kPa bij (-19,5 -11,5 66,5) | epsilon liep in stilstaande lucht naar de numerieke ondergrens: iteratie 332 geeft nut = 3,4e7 in die cel, iteratie 333 de drukpiek. Een derde van het domein had epsilon < 1e-5 | `kMin 1e-4` en `epsilonMin 1e-5` in `momentumTransport`. Eerdere wissel naar `DICGaussSeidel` was niet de oorzaak (crash bleef, later); blijft staan | crasht niet meer (lokale tijdstap, runs van 1000 en 1500 iteraties) |
| Crash bij iteratie 176 en 501 met wisselende plek; laatste keer U van 17 naar 1e5 m/s bij (-82 78 6), T negatief, vlak bij de zijrand in stilstaande lucht; nut was daar vooraf niet extreem | waarschijnlijk: stationaire matrix heeft in vrijwel stilstaande cellen bijna geen diagonaal, dus rAU is enorm en kleine drukfouten geven grote snelheden. Niet rechtstreeks gemeten | lokale tijdstap (`localEuler`, uit `fluid/angledDuctLTS`), maxCo 1, maxDeltaT 2 s, relaxatie vervalt | crasht niet meer (lokale tijdstap, runs van 1000 en 1500 iteraties) |
| Fanmonitor 583 m3/s tegen massastroom 560 kg/s (463 m3/s); bundeldebiet uit cel-U 349 m3/s; drukval bundel 77 Pa tegen 130 Pa volgens f | cel-U wijkt af van de flux in dunne zones met sterke kracht (fan 1-2 cellen, bundel 2-3 cellen), dus fancurve en Forchheimer zien een verkeerde snelheid | fan-Q en swirl nu uit `fvc::reconstruct(phi)`; f herijkt 72 naar 84 op de gemeten drukval; htc herijkt 53 naar 81 op ~12 MW | Run 1000 iteraties: Q 507 m3/s, balansfout -1,4% (flood-fill: plenum dicht) |

## Jobs
| Datum | Job-id | Soort | Partitie | Nodes | Tasks | Walltime |
|---|---|---|---|---|---|---|
