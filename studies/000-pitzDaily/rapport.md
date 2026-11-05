# Rapport: pitzDaily proefrun
Conclusie: voldoet aan het acceptatiecriterium; de hele keten draaide foutloos op een tijdelijke Azure-VM.

| Criterium | Eis | Gemeten | Oordeel |
|---|---|---|---|
| Mesh | maxNonOrtho <= 70, maxSkewness <= 4 | 5,95 en 0,26 | Voldoet |
| Solver | Eindigt met `End` | `End`, geen FOAM-fouten of waarschuwingen | Voldoet |
| Convergentie | p < 1e-2, U, k en epsilon < 1e-3, voor endTime 2000 | Geconvergeerd na 293 iteraties: p 1,4e-3, Ux 1,3e-4, Uy 9,9e-4, k 2,3e-4, epsilon 1,4e-4 | Voldoet |
| Residuen dalen | Dalende trend | Dalend; Uy stijgt tijdelijk tot rond iteratie 130 | Voldoet |
| PNG's | Aangemaakt | `residuals.png`, `U_slice.png`, `p_slice.png` | Voldoet |

## Run
- Job 1 (solver) en job 2 (post), Slurm op `Standard_F8s_v2` in Zweden Centraal, 4 tasks.
- Rekentijd solver: 2,6 s. OpenFOAM op de VM: `11-e1fc8c682ae6`, gelijk aan lokaal.
- Mesh: 12225 cellen, maxNonOrtho 5,95, maxSkewness 0,26.

## Kosten
- VM-tijd: ongeveer 7 minuten (mislukte eerste VM) plus ongeveer 50 minuten (tweede VM).
- Geschat: EUR 0,33 plus enkele centen voor schijf en IP-adres, excl. btw. Budget: EUR 0,70.
- De werkelijke factuur is nog niet gecontroleerd; die verschijnt later in Azure Kostenbeheer.
- De meeste VM-tijd was wachten: de rekenjob duurde seconden.

## Resultaten
- `results/residuals.png`: alle residuen onder de grens bij iteratie 293.
- `results/U_slice.png`: snelheid met het recirculatiegebied achter de stap.
- `results/p_slice.png`: druk.

## Opmerkingen
- Dit is een ketentest; de fysica is niet gevalideerd tegen metingen.
- Twee fouten gevonden en opgelost, zie het fix-log in `NOTES.md`.
- `forces.py` is niet op deze case getest: de tutorial heeft geen forces-functie.
- Alle resources van de job zijn verwijderd en gecontroleerd. Azure heeft zelf een gratis network watcher in Zweden aangemaakt.
