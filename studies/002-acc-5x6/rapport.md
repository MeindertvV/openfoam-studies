# Rapport 002-acc-5x6

**Conclusie:** alleen windstil is af. Wind en scherm zijn niet stabiel gedraaid, dus de vergelijking met en zonder wind en scherm is er niet. Het criterium "drie cases vergelijkbaar op dezelfde mesh" is niet gehaald.

## Acceptatie
| Criterium | Windstil | Wind | Scherm |
|---|---|---|---|
| Warmtebalans binnen 2% | -1,43% (365,0 MW lucht, 370,3 MW bundels): gehaald | geen eindresultaat | geen resultaat |
| Fandebiet binnen 10% van 500 m3/s | 492-509 m3/s, gemiddeld 503: gehaald | geen eindresultaat | geen resultaat |

## Windstil
- Mesh 4.044.022 cellen, 1200 iteraties, velden op t=1000 in `runs/windstil/windstil.foam`.
- Drukstap per fan 149-155 Pa. Totaal debiet 15.103 m3/s.
- Inlaat-T 287,5-288,1 K: gelijk aan de omgeving min adiabatische afkoeling, geen teken van recirculatie.
- Het bundeldebiet uit `cv_balans.py` (11.152 m3/s) is lager dan het fandebiet. Dat komt waarschijnlijk door dezelfde afwijking van cel-U in dunne zones als bij de fan; gebruik het fandebiet.
- Windstil draaide met `corrected`-schema's en maxCo 1, wind en scherm met `limited corrected 0.33` en maxCo 0,7.

## Wind: tussenstand, niet geconvergeerd
Waarden op iteratie 330, kort voor de ontsporing, 9 m/s op 45 m. Debiet zakte nog. Alleen als richting gebruiken.

| Rij vanaf windzijde | Debiet per fan (m3/s) | Hoogste inlaat-T (K) |
|---|---|---|
| 1 | 284-343 | 291,4 |
| 2 | 438-464 | 288,1 |
| 3 | 451-470 | 287,7 |
| 4 | 478-488 | 287,7 |
| 5 | 493-496 | 287,7 |

- Totaal 13.144 m3/s, 13% onder windstil. De windzijde verliest het meest, tot ~40%.
- De eerste rij zuigt tot 3,6 K warmere lucht aan. De oorzaak is niet onderzocht.
- `runs/wind/wind.foam` toont t=300, niet geconvergeerd.

## Waarom wind en scherm mislukten
- Elke poging ontspoort: iteratie 5, 8, 217 en 372. Scherm is gestopt bij iteratie 120 en is nooit voorbij de crashplek gekomen.
- De diagnose ziet k rond iteratie 377 springen tot 1510, en nut tot 3641, op ~(-38, 4, 72) en daarna ~(-38, 25, 70): boven de windzijde.
- Waarschijnlijke oorzaak: de hoge inlaat-nut (10-58 m2/s) komt in de fijne cellen aan en maakt het expliciete deel van de viscositeitsterm daar instabiel. Niet bewezen.

## Volgende stap
Lokaal op de 1,28M-mesh, zonder Azure-kosten: inlaat-k en daarmee nut begrenzen, of maxCo verlagen. Pas als dat voorbij iteratie 500 stabiel is, is een nieuwe Azure-run zinvol (ongeveer 2,5 uur op F16, ~€3 plus 10 minuten mesh).

## Kosten
Geschat ~€12,60 (~$14,50, koers niet gecontroleerd), inclusief ~€6 aan VM-tijd zonder lopende job. VM en opslag zijn verwijderd.
