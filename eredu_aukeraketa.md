# Ereduaren aukeraketa: zergatik Ridge

**Erronka:** 2. Erronka – Smart Environment AI · **Modulua:** Adimen Artifizialaren ereduak

## Erabakia

Jetson Nano-ra **Ridge erregresioa** (`alpha ≈ 31,6`) eramango dugu, egun bereko PM10-a kalkulatzeko. MLP sare neuronala ere garatu eta ebaluatu dugu, baina ez dugu aukeratu.

Enuntziatuak MLP bat eraikitzea eta eredu klasikoekin konparatzea eskatzen du, eta ondoren **eredurik onena** Jetson Nano-ra eramatea. Ridge erregresio-eredua da eta konparazio horretan onena izan da, beraz baldintza betetzen du.

## Nola konparatu ditugu

Bi ereduek baldintza berberak izan dituzte:

- **Datuak:** Mundakako estazioa, 2026ko 257 egun (PM10 hutsik gabekoak).
- **Ezaugarriak:** NO, NOX, NO2, O3, PM2,5, hilabetea eta asteko eguna.
- **Banaketa kronologikoa:** lehen %80 entrenatzeko (205 egun) eta azken %20 probatzeko (52 egun).
- **Balidazioa:** `TimeSeriesSplit` (5 zati) entrenamenduko datuetan. Eredua eta hiperparametroak balidazioarekin aukeratu ditugu, ez *test* multzoarekin.

## Emaitzak

| Eredua | Balidazio RMSE | Test MAE (µg/m³) | Test RMSE (µg/m³) | Test R² |
|---|---|---|---|---|
| Beti batezbestekoa iragartzea | – | 2,64 | 3,23 | -0,14 |
| **Ridge** | **2,73** | **1,82** | **2,42** | **0,36** |
| MLP (42 hazia) | 3,33 | 1,83 | 2,42 | 0,36 |
| MLP (5 haziren batezbestekoa) | 3,33 | 2,13 | 2,72 | 0,16 |

Aukeratutako MLP-ak 8 neuronako geruza ezkutu bakarra du, eta probatutako 6 konfigurazioetatik onena izan da balidazioan.

## Arrazoiak

1. **Balidazioan hobea da.** Ridge-ren RMSE-a ≈ 2,73 da, eta MLP-arena ≈ 3,33. Hau da erabakia hartzeko irizpide nagusia.
2. **Egonkorragoa da.** Ridge-k beti emaitza bera ematen du. MLP-aren R²-a, aldiz, -0,64 eta 0,50 artean dago hasierako hazi aleatorioaren arabera, eta 42 haziarekin lortutako berdinketa ez da ohikoa.
3. **Arinagoa da.** Ridge NumPy-rekin bakarrik exekuta daiteke, 0,6 KB-eko fitxategi batekin (gehi 0,7 KB-eko aurreprozesamendua). Horrek Jetson Nano-n exekutatzea errazten du, ez baitu TensorFlow behar.
4. **Interpretagarriagoa da.** Koefizienteek aldagai bakoitzaren eragina erakusten dute, eta hori erabilgarria da emaitzak Aldundiari azaltzeko.

**Zergatik ez du sare neuronalak irabazi?** MLP-ek datu asko behar izaten dituzte erlazio konplexuak ikasteko, eta hemen 205 entrenamendu-errenkada eta urte bakarreko datuak ditugu. Datu gutxirekin, eredu sinple eta erregularizatu bat egokiagoa da.

## Mugak

- **Doitasun apala:** R² ≈ 0,36 da, eta ereduak PM10-aren aldakortasunaren zati bat bakarrik azaltzen du.
- **Ez da benetako aurreikuspena:** egun bereko neurketak behar ditu. Biharko PM10-a iragartzeko probak ez du emaitza erabilgarririk eman (ikus SAA zatiko 3.1. atala).
- **Datu mugatuak:** estazio bakarra, eguneko datuak eta 2026ko hilabeteak bakarrik. Urriko eta azaroko daturik ez dago entrenamenduan.
- **Exekuzio-denborak falta dira:** Jetson Nano-n neurtu behar dira.

Datu gehiagorekin (urte gehiago, estazio gehiago, meteorologia) konparazioa errepikatu beharko litzateke, emaitza alda baitaiteke.

## Fitxategiak

- `erronka_MIA.ipynb`: MLP-a, doikuntza, konparazioa eta esportazioa.
- `ridge_eredua.json` eta `aurreprozesamendua.json`: Jetson Nano-ra eramango den eredua.
- `mlp_pm10.keras` eta `mlp_pm10.tflite`: sare neuronala, konparaziorako eta erakusteko.
