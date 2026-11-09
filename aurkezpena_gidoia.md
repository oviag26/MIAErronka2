# Aurkezpenaren gidoia (10-15 min)

NexAI Innovations-ek Bizkaiko Foru Aldundiari soluzioa aurkezten dio. Diapositiba bakoitzak irudi bat izan behar du. Edozein taldekidek aurkeztu behar du dena azaltzeko gai izan.

| # | Diapositiba | Edukia | Irudia | Denbora |
|---|---|---|---|---|
| 1 | Azala | «Smart Environment AI – Airearen Kalitatearen Monitorizazioa eta Iragarpen Adimenduna», taldekideak, 4IABD1, PIA/SAA/MIA moduluak | Logoa / Mundakako argazkia | 0:20 |
| 2 | Aurkibidea | 8 atalak | – | 0:10 |
| 3 | Arazoa | Aldundiak zer behar duen: kutsadura aurreikusi, arriskuak goiz detektatu, herritarrei informatu | Kutsadura-ikonoa | 1:00 |
| 4 | Soluzioa | Arkitektura: neurgailuak → Jetson (Ridge + K-means + sistema aditua) → dashboard-a | Arkitektura-diagrama (MIA_txostena 1. atala) | 1:00 |
| 5 | Datuak | Open Data Euskadi, Mundaka, 306 egun; hutsuneak (PM10 %16), O3-aren urtaroa | PIAko denbora-seriea eta korrelazio-matrizea | 1:30 |
| 6 | Aurreprozesamendua | Mediana, IQR (outlier-ak mantendu), one-hot, Pipeline, PCA | Pipeline-aren eskema | 1:00 |
| 7 | Ereduak | Erregresioa (Ridge onena), sailkapena (ahula, eta zergatik), K-means (3 egun-mota) | SAAko taulak + `k_aukeraketa.png` | 2:00 |
| 8 | Sare neuronala | MLP vs Ridge; zergatik ez du irabazten (205 errenkada, ezegonkorra) | MIA koadernoko konparazio-taula | 1:30 |
| 9 | Jetson Nano | Zergatik JSON + NumPy; egiaztapena (0 aldea); inferentzia-denborak PC vs Jetson | Denbora-taula + Jetson-aren argazkia | 1:30 |
| 10 | Dashboard-a eta sistema aditua (DEMOA) | Zuzeneko demoa edo bideoa: urtea erreproduzitu, episodioa simulatu, alertak | Dashboard-aren pantaila-argazkia | 2:30 |
| 11 | Sistema aditua barrutik | Arauak, kateatzea (R1 → R2), sentikortasuna, logika lausoa | `sentikortasuna.png` | 1:00 |
| 12 | Ondorioak eta mugak | R² 0,36, ez da biharko iragarpena, meteorologia falta; hobekuntzak | – | 1:00 |
| 13 | Iturriak eta galderak | Open Data Euskadi, OME 2021, MITECO ICA, scikit-learn, Keras | – | 0:20 |

## Galdera posibleak (prestatu)

- **Zergatik banaketa kronologikoa eta ez ausazkoa?** Egun jarraituak oso antzekoak dira; ausazkoak R² ≈ 0,75 ematen du, baina ez da erreala (etorkizuna iragartzeko iragana bakarrik dugu).
- **Zergatik ez MLP-a, sare neuronala «hobea» bada?** 205 errenkada bakarrik; balidazioan okerragoa eta haziaren arabera ezegonkorra. Ridge-k emaitza bera ematen du 0,6 KB-rekin.
- **Zer gertatzen da urriarekin, entrenamenduan ez badago?** One-hot-ak zero bektorea ematen du (handle_unknown='ignore'); NumPy bertsioak berdin egiten du eta egiaztatuta dago.
- **Zergatik ez dago PM10 alertarik datu errealetan?** Mundaka aire garbiko estazioa da (PM10 max. 35 < 45). Horregatik episodio-eszenatokia gehitu dugu.
- **Nola gehituko zenukete haizearen araua?** Euskalmet-eko datuak batu eta arau bat gehitu `ARAUAK` zerrendan; motorra ez da aldatzen.
- **Zer da aurrerantz kateatzea?** Motorrak egitateetatik abiatuta arauak exekutatzen ditu eta egitate berriek beste arau batzuk aktiba ditzakete (R1 → R2).

## Demoaren plana

1. Jetson-ean `python3 dashboard.py`; ordenagailuko nabigatzailean `http://<jetson-ip>:8050`.
2. Abiadura «0,1 s» ekainera arte (ozono-alertak ikusteko), gero «1 s».
3. «Kutsadura-episodioa simulatu» sakatu: R2 eta R7 alertak.
4. **B plana:** grabatutako bideoa, Jetson-ak edo sareak huts egiten badu.
