# Smart Environment AI – MIA zatia (2. Erronka)

Mundakako airearen kalitatearen monitorizazioa: sare neuronala, Jetson Nano-ko zabaltzea, dashboard-a eta sistema aditua.
Modulua: **5071. Adimen Artifizialaren ereduak** · 4IABD1 · 3. taldea.

Erronkaren beste zatiak:
- PIA (EDA eta aurreprozesamendua): https://github.com/AsierLaiz/Erronka2PIA
- SAA (erregresioa, sailkapena, K-means): https://github.com/AsierLaiz/Erronka2SAA

## Fitxategiak

| Fitxategia | Zertarako | Non exekutatu |
|---|---|---|
| `erronka_MIA.ipynb` | MLP Keras-ekin, Ridge-rekin konparazioa, esportazioa | PC (TensorFlow) |
| `eredu_aukeraketa.md` | Zergatik Ridge eta ez MLP | – |
| `MIA_txostena.md` | **MIA zatiko txosten osoa** (teoria + emaitzak) | – |
| `aurreprozesamendua.json`, `ridge_eredua.json` | Ridge eredua JSON-en | – |
| `kmeans_eredua.json` | SAAko K-means-a JSON-en (`esportatu_kmeans.py`-k sortua) | – |
| `mlp_pm10.keras`, `mlp_pm10.tflite` | Sare neuronala | – |
| `inferentzia.py` | Inferentzia NumPy-rekin bakarrik (Ridge + K-means) | **Jetson** / PC |
| `sistema_aditua.py` | Sistema aditua (8 arau, aurrerantz kateatzea) + logika lausoa | **Jetson** / PC |
| `neurketa.py` | Inferentzia-denboren neurketa → `emaitzak/neurketa_*.json` | **Jetson** / PC |
| `dashboard.py` + `dashboard.html` | Monitorizazio-dashboard-a (http://localhost:8050) | **Jetson** / PC |
| `probak_sistema_aditua.py` | Sistema adituaren froga eta sentikortasuna → `emaitzak/` | PC |
| `egiaztatu_esportazioa.py` | NumPy == scikit-learn dela egiaztatu | PC (scikit-learn) |
| `esportatu_kmeans.py` | SAAko `kmeans_eredua.pkl` → JSON | PC (scikit-learn) |
| `aurkezpena_gidoia.md` | Aurkezpenaren gidoia (10-15 min) | – |
| `zaharrak/` | Hasierako probak, ez dira azken soluzioa | – |

## Exekuzioa

PC-an (scikit-learn duen ingurunea, adib. conda `SAA`):

```bash
python esportatu_kmeans.py        # behin bakarrik
python egiaztatu_esportazioa.py   # ONDO atera behar du
python probak_sistema_aditua.py
python neurketa.py
python dashboard.py               # http://localhost:8050
```

Jetson Nano-n (Python 3.6+ eta NumPy bakarrik):

```bash
scp -r MIAErronka2 <erabiltzailea>@<jetson-ip>:~/
ssh <erabiltzailea>@<jetson-ip>
cd ~/MIAErronka2
python3 inferentzia.py
python3 neurketa.py               # -> emaitzak/neurketa_jetson.json
python3 dashboard.py              # http://<jetson-ip>:8050
```

NumPy falta bada: `sudo apt install python3-numpy`. TFLite-ko MLP-a neurtzeko (aukerakoa), `tflite_runtime` instalatu behar da.
