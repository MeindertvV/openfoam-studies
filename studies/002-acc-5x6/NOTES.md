# Notities

## Gekozen basistutorial + reden
- Tutorial: geen; kopie van studies/001-acc-aframe
- Reden: zelfde model, getegeld; gekalibreerd op de grovere bundelresolutie

## Afwijkingen ten opzichte van de tutorial
- Bundel en dek 0,75 m dik, cel 0,375 m; f 56, htc 54 herijkt in `kalibratie/`: 498 m3/s, 12,6 MW, balans -1,8%.
- Fan-code tegelt 30 fans, met celkaart en Tin per fan.
- `p_rghFinal` relTol 0.01. `nCorrectors` blijft 2: met 1 crasht de 4M-mesh.
- Wind-aannames: 9 m/s op 45 m, z0 0,1 m, +x. Scherm: kruisvorm z 5-44,25 m (op verzoek gebruiker, was z 30; jobs 19 en 32 draaiden nog met z 30), K 10, 1,5 m dik.
- Lokale test op 1,28M cellen: windstil, wind en scherm starten; 12 tot 25 iteraties. Skewness daar 4,02 (grens 4).

## Fix-log
| Symptoom | Oorzaak | Wijziging | Verificatie |
|---|---|---|---|
| Wind: ph_rgh variatie 1680 Pa, h divergeert | fixedFluxPressure op de inlaat trekt de inlaatsnelheid in de hydrostatische start | ph_rgh zeroGradient op inlet, outlet, sides | variatie 40 Pa, geen crash meer door deze oorzaak |
| Wind: solution singularity in U bij iteratie 1 | beginveld U = 9 m/s in het hele domein; oorzaak niet uitgediept | beginveld U = 0 | wind en scherm draaien |
| snappyHexMesh parallel stopt: `distributor` undefined | zelf ingekorte `decomposeParDict` | `distributor ptscotch` toegevoegd | job 8 op de VM |
| Op 4M crashen alle drie de runs na 7-27 iteraties: k en epsilon naar 1e20, T negatief | `nCorrectors 1` was alleen op de 79k-unit getest. Niet de mesh: met 2 correctors draait dezelfde mesh | `nCorrectors 2` | job 15: 73 iteraties, fans ~500 m3/s, continuiteit 3e-7 |
| Wind en scherm op 4M crashen bij iteratie 5-6: k tot 4e5, epsilon tot 8e8, daarna T negatief | Niet opgelost. Eerste vermoeden (plotselinge inlaat) is weerlegd: met de opbouw crashen job 21 en 23 bij iteratie 8 met SIGFPE, bij nog 8% inlaatsnelheid | inlaat als `codedFixedValue` opgebouwd in 100 iteraties, staat nog in `mkRuns.py` en `0/U` | job 21 en 23: mislukt |
| Job 21, 23: SIGFPE in GAMG bij iteratie 8 | Waarschijnlijk: nut ~ 10,8 m2/s uit de begin-k/epsilon plus dt tot 2 s op 0,375 m-cellen maakt het expliciete dev2(T(grad(U)))-deel instabiel. Niet los gemeten | begin-k/epsilon gelijk aan windstil (0,1 / 0,01), `maxDeltaT 0.2` | job 26: voorbij iteratie 8, geen bounding |
| Job 26: SIGFPE in GAMG bij iteratie 217, zelfde rank 8, Ux- en p_rgh-residuen lopen op | Onbekend; vermoedelijk wind door de slechtste cellen (skewness 4, niet-orthogonaliteit 55). Plek niet bepaald | wind/scherm: `limited corrected 0.33`, `grad(U) cellLimited`, maxCo 0.7, smoothing 0.05, damping 0.5; 750 iteraties, schrijven elke 150 | Job 30 kwam verder (crash bij 372), geen oplossing |
| Job 30: k springt rond iteratie 336 en T wordt negatief bij 372. Herstart vanaf t=300 (job 39) ziet k bij ~377 springen naar 1510, nut 3641, bij (-38, 4, 72) en daarna (-38, 25, 70) | Waarschijnlijk: inlaat-nut (10-58 m2/s, ABL-k) bereikt de fijne cellen boven de windzijde en het expliciete deel is daar instabiel. Niet bewezen. Tijdstip verschilt per start (336 vs 377), dus geen vast mesh-punt | Niet opgelost; budget op | Volgende stap lokaal op 1,28M: inlaat-k/nut begrenzen of maxCo verlagen |
| `cv_balans.py` stopt op `zone()` bij 4M | `cellZones` staat daar als `cellLabels 40234 (`, zonder `List<label>` | regex verruimd | job 25: `runs/windstil/balans.txt`, balansfout -1,43% |
| SSH op poort 22 onbereikbaar vanaf 16:09 UTC, sshd ziet geen pogingen; NSG en IP kloppen | onbekend, iets tussen lokaal en de VM. Mogelijk door mijn ssh-poll elke 60 s | tijdelijk sshd op poort 2222 met eigen NSG-regel, `-p 2222` in `.azjob` | ssh en rsync werken op 2222 |
| Scherm niet zichtbaar in ParaView: `screen` staat niet onder Mesh Regions, ook niet met Read Zones (5.10.0-RC1) | Oorzaak in de reader niet uitgezocht; mesh ontbrak ook lokaal in `runs/scherm` | 4M-mesh gekopieerd uit `runs/windstil`, `topoSet`, `foamToVTK -cellSet screenCells` naar `runs/scherm/VTK/screenCells_0.vtk` | zone 7686 cellen; bounds kloppen; `runs/scherm/results/mesh_scherm.png` |
| Gaten in schermzone: x-arm 16 kolommen leeg, en 143 kolommen 3 m dik in plaats van 1,5 m (onder z ~35) | Celcentra van 1,5 m-cellen liggen op precies +-0,75 m, de rand van `boxToCell`; afronding bepaalt per cel in of uit | box 0,01 m verschoven in `mkRuns.py` (`EPS_SCHERM`) en `runs/scherm/system/topoSetDict`; zone opnieuw gemaakt | 7565 cellen, 0 kolommen leeg, 3 per arm dubbel (bij de kruising); jobs 19 en 32 draaiden met de oude zone, maar die runs zijn toch mislukt |
| Scherm begint te hoog: z 30 in plaats van ongeveer 5 m boven de grond | Aanname in `mkRuns.py`; gebruiker gaf 5 m door | `ZSCHERM` naar z 5; extra box-rij voor z<9, want daar zijn de cellen 3 m met centra op +-1,5 en mist de 1,5 m-box ze | 8885 cellen; effectief vanaf z 6, rij z 6-9 is 3 m dik en loopt tot x 33 en y +-39 en mist x -31,5 tot -30; rest 1,5 m, geen gaten behalve 0,1 m aan de armeinden |
| Wind en scherm ontsporen op 4M (job 26, 30, 39) | Waarschijnlijk hoge inlaat-nut; niet bewezen, geen controlerun | Inlaat-epsilon `codedFixedValue` met nut <= 5 m2/s (`EPSCAP` in `mkRuns.py`), nieuwe `runs/wind_v2` en `runs/scherm_v2`, instellingen verder als job 30 | VM 2 job 1 en 3: 1200 iteraties, geen FATAL, residuen dalend |
| `postProcessing/*/0/` niet opgehaald voordat de VM weg was | Mijn rsync-exclude `0/` matchte ook die mappen | Geen; data weg. Bij een volgende keer `/0/` per run uitsluiten | Convergentie alleen uit `log.foamRun` af te leiden |

## Jobs
| Datum | Job-id | Soort | Partitie | Nodes | Tasks | Walltime |
|---|---|---|---|---|---|---|
| 2026-11-05 | - | vm | Standard_F8s_v2 | 1 | 8 | 20:00:00 |
| 2026-11-05 | - | vm | Standard_F16as_v6 | 1 | 16 | 6:00:00 |
| 2026-11-05 | 8 | mesh | hpc | 1 | 16 | 01:00:00 |
| 2026-11-05 | 15 | solver windstil | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 16 | post windstil | hpc | 1 | 1 | 01:00:00 |
| 2026-11-05 | 17 | solver wind | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 18 | post wind | hpc | 1 | 1 | 01:00:00 |
| 2026-11-05 | 19 | solver scherm | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 20 | post scherm | hpc | 1 | 1 | 01:00:00 |
| 2026-11-05 | 26 | solver wind | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 30 | solver wind | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 31 | post wind | hpc | 1 | 1 | 01:00:00 |
| 2026-11-05 | 32 | solver scherm | hpc | 1 | 16 | 02:00:00 |
| 2026-11-05 | 33 | post scherm | hpc | 1 | 1 | 01:00:00 |
| 2026-11-06 | 34-38 | diagnose wind (mislukt: 34-37 ph_rgh of functie-instelling, 38 tot iteratie 345 zonder ontsporing) | hpc | 1 | 16 | 00:20:00 |
| 2026-11-06 | 39 | diagnose wind tot iteratie 385 | hpc | 1 | 16 | 00:20:00 |
| 2026-11-06 | - | vm westeurope, budget EUR 7,12 plus schijf | Standard_F16as_v6 | 1 | 16 | 6:00:00 |
| 2026-11-06 | 1 (VM 2) | solver wind_v2, 1200 iteraties, inlaat-nut begrensd | hpc | 1 | 16 | 02:00:00 |
| 2026-11-06 | 2 (VM 2) | post wind_v2 | hpc | 1 | 1 | 01:00:00 |
| 2026-11-06 | 3 (VM 2) | solver scherm_v2, alleen na geslaagde wind_v2 | hpc | 1 | 16 | 02:00:00 |
| 2026-11-06 | 4 (VM 2) | post scherm_v2 | hpc | 1 | 1 | 01:00:00 |

## Lokale testen
`lokaal/wind_basis`: instellingen van job 30 op 1,28M. `lokaal/wind_nut`: idem, inlaat-nut begrensd op 5 m2/s via epsilon. Lopen; uitkomst komt in `rapport.md`.
| 2026-11-06 | - | vm | Standard_F16as_v6 | 1 | 16 | 6:00:00 |
