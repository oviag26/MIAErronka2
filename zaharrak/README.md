# Fitxategi zaharrak

Erronkaren hasierako probak dira, eta **ez dira azken soluzioaren parte**. Hemen gordetzen ditugu historia ez galtzeko.

- `preparar.py`, `modelos.py`: ausazko banaketa (`train_test_split`), RandomForest eta PM10-aren kuartiletan oinarritutako kategoriak.
- `modelo_reg.pkl`, `modelo_clf.pkl`, `modelo_mlp.pkl`: script horiekin entrenatutako ereduak.

Azken soluzioak **banaketa kronologikoa** eta `TimeSeriesSplit` balidazioa erabiltzen ditu. Ausazko banaketak emaitzak puztu egiten ditu, egun jarraituak oso antzekoak direlako: Ridge-k R² ≈ 0,75 lortzen du ausazko banaketarekin, eta R² ≈ 0,36 kronologikoarekin. Ikus `../erronka_MIA.ipynb` eta SAA zatiko `konparazio_txostena.md`.
