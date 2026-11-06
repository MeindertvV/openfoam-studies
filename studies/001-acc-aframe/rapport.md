# Rapport 001-acc-aframe

Een A-frame-unit met fan, windstil, lokaal gerekend (229k cellen, 1000 iteraties, serieel).

| Grootheid | Resultaat | Criterium | Oordeel |
|---|---|---|---|
| Fan-debiet | 507 m3/s bij 150 Pa | 500 m3/s +/-10% | voldoet |
| Warmtebalans | Q lucht 12,00 MW, Q bundels 12,18 MW, -1,4% | binnen 2% | voldoet |
| Warmteafvoer | 12,2 MW | ontwerp ~12 MW | herijkt |
| Convergentie | fan-spreiding 0,2 m3/s over 200 iteraties | binnen 1% | voldoet |

Lucht warmt in de controlebox gemiddeld op van 288,0 naar 304,0 K; die uitstroom bevat ook meegezogen lucht.

## Beperkingen
- Fancurve, f en htc zijn aannames; f en htc zijn herijkt op deze mesh en gelden voor deze bundelresolutie.
- De bundelweerstand in de solver werkt op de cel-U, die in een zone van 2-3 cellen achterblijft bij de flux.
- Bundels zijn trapvormige cellZones.
- Het veld in de omgeving is niet volledig stationair: het p_rgh-residu blijft rond 0,05.
- Geen meshstudie; `check_mesh.py` meldt 8533 concave cellen, gewone `checkMesh` geeft Mesh OK.
