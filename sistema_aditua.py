# -*- coding: utf-8 -*-
"""Airearen kalitaterako sistema aditua (NumPy eta Python estandarra bakarrik).

Egitura klasikoa du:

* **Ezagutza-basea** (ARAUAK): arauak datu gisa, kodetik bereizita. Arau
  bakoitzak baldintzak (ETA) eta ekintzak ditu. Ekintza batzuek alerta bat
  sortzen dute eta beste batzuek egitate berriak gehitzen dituzte memorian.
* **Lan-memoria**: egun bakoitzeko egitateak (neurketak, ereduaren iragarpena,
  klusterra...).
* **Inferentzia-motorra**: aurrerantz kateatzea (forward chaining). Arauak
  behin eta berriz ebaluatzen ditu, egitate berririk sortzen ez den arte.
  Arau bakoitza behin bakarrik exekutatzen da (refractoriness).

Horrez gain, logika lausoko (fuzzy) arrisku-indize bat dago (arrisku_lausoa),
muga zorrotzen ordez gradu jarraituak erabiltzen dituena.

Mugak OMEren 2021eko gidalerroetatik (eguneko batezbestekoak) eta MITECOren
Airearen Kalitatearen Indizetik (ICA) hartu dira.
"""
from __future__ import print_function

import copy

import numpy as np

# --- Mugak (µg/m³) -----------------------------------------------------------
MUGAK = {
    'PM10_OME': 45.0,       # OME 2021, PM10 24 h
    'PM10_ICA_ONA': 20.0,   # ICA: "Ona" kategoriaren goiko muga
    'NO2_OME': 25.0,        # OME 2021, NO2 24 h
    'O3_OME': 100.0,        # OME 2021, O3 8 h (eguneko batezbestekoari aplikatua, kontserbadorea)
    'O3_UDA': 80.0,         # O3 altua udako episodioetan
    'ANOMALIA': 3 * 2.73,   # 3 x Ridge-ren balidazio RMSE-a
}

# --- Ezagutza-basea ------------------------------------------------------------
# Baldintza: (egitatea, eragilea, balioa). Balioa string bat bada eta MUGAK-en
# badago, muga hori erabiltzen da (horrela mugak aldatu daitezke arauak ukitu gabe).
ARAUAK = [
    {'id': 'R0', 'izena': 'PM10 neurtua erabili',
     'baldintzak': [('pm10_neurtua', 'badago', None)],
     'ekintzak': {'ezarri': {'pm10_eraginkorra': 'pm10_neurtua', 'pm10_estimatua': False}}},

    {'id': 'R1', 'izena': 'PM10 neurgailurik ez: ereduaren estimazioa',
     'baldintzak': [('pm10_neurtua', 'ez_dago', None)],
     'ekintzak': {'ezarri': {'pm10_eraginkorra': 'pm10_iragarria', 'pm10_estimatua': True},
                  'alerta': ('INFO', 'Neurgailuak ez du PM10 eman: ereduaren estimazioa erabiltzen da')}},

    {'id': 'R2', 'izena': 'Partikula-alerta (OME)',
     'baldintzak': [('pm10_eraginkorra', '>', 'PM10_OME')],
     'ekintzak': {'alerta': ('ALERTA', 'PM10-ak OMEren eguneko muga gainditzen du')}},

    {'id': 'R3', 'izena': 'Partikula-abisua (ICA)',
     'baldintzak': [('pm10_eraginkorra', '>', 'PM10_ICA_ONA'),
                    ('pm10_eraginkorra', '<=', 'PM10_OME')],
     'ekintzak': {'alerta': ('ABISUA', 'PM10-ak "Ona" kategoria gainditu du')}},

    {'id': 'R4', 'izena': 'Neurgailu-anomalia',
     'baldintzak': [('hondarra_abs', '>', 'ANOMALIA')],
     'ekintzak': {'alerta': ('ABISUA', 'PM10 neurtua eta kalkulatua oso desberdinak: neurgailua egiaztatu')}},

    {'id': 'R5', 'izena': 'Ozono-episodioa',
     'baldintzak': [('o3', '>', 'O3_UDA'),
                    ('klusterra', '==', 2)],
     'ekintzak': {'alerta': ('ABISUA', 'O3 eta partikula altuko eguna: talde sentikorrei kanpoko ariketa mugatzea gomendatu')}},

    {'id': 'R6', 'izena': 'Ozono-alerta (OME)',
     'baldintzak': [('o3', '>', 'O3_OME')],
     'ekintzak': {'alerta': ('ALERTA', 'O3-ak OMEren muga gainditzen du')}},

    {'id': 'R7', 'izena': 'NO2-alerta (OME)',
     'baldintzak': [('no2', '>', 'NO2_OME')],
     'ekintzak': {'alerta': ('ALERTA', 'NO2-ak OMEren eguneko muga gainditzen du')}},
]

LARRITASUNA = {'INFO': 0, 'ABISUA': 1, 'ALERTA': 2}


class SistemaAditua(object):
    def __init__(self, arauak=None, mugak=None):
        self.arauak = copy.deepcopy(arauak if arauak is not None else ARAUAK)
        self.mugak = dict(MUGAK)
        if mugak:
            self.mugak.update(mugak)

    def _balioa(self, balioa):
        if isinstance(balioa, str) and balioa in self.mugak:
            return self.mugak[balioa]
        return balioa

    def _bete(self, baldintza, memoria):
        egitatea, eragilea, balioa = baldintza
        if eragilea == 'badago':
            return memoria.get(egitatea) is not None
        if eragilea == 'ez_dago':
            return egitatea in memoria and memoria[egitatea] is None
        x = memoria.get(egitatea)
        if x is None:
            return False  # egitatea ez dago oraindik: ezin da ebaluatu
        y = self._balioa(balioa)
        return {'>': x > y, '>=': x >= y, '<': x < y, '<=': x <= y, '==': x == y}[eragilea]

    def _egitate_eratorriak(self, memoria):
        """Arauek erabiltzen dituzten egitate kalkulatuak."""
        if memoria.get('pm10_neurtua') is not None and memoria.get('pm10_iragarria') is not None:
            memoria['hondarra_abs'] = abs(memoria['pm10_neurtua'] - memoria['pm10_iragarria'])

    def inferentzia(self, egitateak):
        """Aurrerantz kateatzea. Itzultzen du: (lan-memoria, alertak, exekutatutako arauak)."""
        memoria = dict(egitateak)
        self._egitate_eratorriak(memoria)
        exekutatuak, alertak = [], []
        aldaketa = True
        while aldaketa:
            aldaketa = False
            for araua in self.arauak:
                if araua['id'] in exekutatuak:
                    continue
                if all(self._bete(b, memoria) for b in araua['baldintzak']):
                    exekutatuak.append(araua['id'])
                    ekintzak = araua['ekintzak']
                    for egitatea, iturria in ekintzak.get('ezarri', {}).items():
                        memoria[egitatea] = memoria.get(iturria) if isinstance(iturria, str) else iturria
                    if 'alerta' in ekintzak:
                        maila, testua = ekintzak['alerta']
                        alertak.append({'araua': araua['id'], 'maila': maila, 'testua': testua})
                    aldaketa = True  # egitate berriak: arauak berriro ebaluatu
        alertak.sort(key=lambda a: -LARRITASUNA[a['maila']])
        return memoria, alertak, exekutatuak


# --- Logika lausoa (fuzzy) ---------------------------------------------------------
def trapezioa(x, a, b, c, d):
    """Trapezio formako kide-funtzioa: 0 a-tik behera, 1 b eta c artean, 0 d-tik gora."""
    x = np.asarray(x, dtype=np.float64)
    gora = np.ones_like(x) if b == a else np.clip((x - a) / (b - a), 0, 1)
    behera = np.ones_like(x) if d == c else np.clip((d - x) / (d - c), 0, 1)
    return np.minimum(gora, behera)


# Kutsatzaile bakoitzaren multzo lausoak: baxua / ertaina / altua
MULTZO_LAUSOAK = {
    'pm10': {'baxua': (0, 0, 15, 25), 'ertaina': (15, 25, 35, 45), 'altua': (35, 45, 999, 999)},
    'o3':   {'baxua': (0, 0, 60, 80), 'ertaina': (60, 80, 90, 100), 'altua': (90, 100, 999, 999)},
    'no2':  {'baxua': (0, 0, 10, 20), 'ertaina': (10, 20, 20, 30), 'altua': (20, 30, 999, 999)},
}
# Irteera: arrisku-indizea 0-100
ARRISKUA_X = np.linspace(0, 100, 201)
ARRISKUA = {'baxua': (0, 0, 20, 40), 'ertaina': (20, 40, 60, 80), 'altua': (60, 80, 100, 100)}


def arrisku_lausoa(pm10, o3, no2):
    """Mamdani motako inferentzia lausoa -> arrisku-indizea (0-100) eta etiketa.

    Arauak:
      1. Kutsatzaileren bat altua bada            -> arriskua altua
      2. Kutsatzaileren bat ertaina bada          -> arriskua ertaina
      3. Kutsatzaile guztiak baxuak badira        -> arriskua baxua
    Desfuzifikazioa: zentroidea.
    """
    sarrerak = {'pm10': pm10, 'o3': o3, 'no2': no2}
    gradua = {}
    for aldagaia, x in sarrerak.items():
        x = 0.0 if x is None else x
        gradua[aldagaia] = {m: float(trapezioa(x, *p)) for m, p in MULTZO_LAUSOAK[aldagaia].items()}

    indarra = {
        'altua': max(g['altua'] for g in gradua.values()),             # EDO = max
        'ertaina': max(g['ertaina'] for g in gradua.values()),
        'baxua': min(g['baxua'] for g in gradua.values()),             # ETA = min
    }
    agregatua = np.zeros_like(ARRISKUA_X)
    for etiketa, p in ARRISKUA.items():
        agregatua = np.maximum(agregatua, np.minimum(indarra[etiketa], trapezioa(ARRISKUA_X, *p)))
    if agregatua.sum() == 0:
        indizea = 0.0
    else:
        indizea = float((ARRISKUA_X * agregatua).sum() / agregatua.sum())
    etiketa = 'baxua' if indizea < 35 else ('ertaina' if indizea < 65 else 'altua')
    return indizea, etiketa


def egitateak_sortu(eguna, pm10_iragarria, klusterra):
    """inferentzia.py-ko egun bat -> sistema adituaren lan-memoria."""
    return {
        'data': str(eguna['Date']),
        'hilabetea': eguna['Date'].month,
        'pm10_neurtua': eguna.get('PM10 (µg/m3)'),
        'pm10_iragarria': float(pm10_iragarria),
        'pm25': eguna.get('PM2,5 (µg/m3)'),
        'o3': eguna.get('O3 (µg/m3)'),
        'no2': eguna.get('NO2 (µg/m3)'),
        'klusterra': int(klusterra),
    }


if __name__ == '__main__':
    from inferentzia import AireEredua, KARPETA, irakurri_csv
    import os

    eredua = AireEredua()
    sistema = SistemaAditua()
    egunak = irakurri_csv(os.path.join(KARPETA, 'MUNDAKA.csv'))
    pm10 = eredua.iragarri_pm10(egunak)
    klusterrak = eredua.klusterra(egunak, pm10)
    kopurua = {}
    for eguna, p, k in zip(egunak, pm10, klusterrak):
        memoria, alertak, _ = sistema.inferentzia(egitateak_sortu(eguna, p, k))
        for a in alertak:
            kopurua[a['araua']] = kopurua.get(a['araua'], 0) + 1
            if a['maila'] != 'INFO':
                print(memoria['data'], a['maila'], a['araua'], a['testua'])
    print('\nAlertak arauka ({} egun):'.format(len(egunak)), kopurua)
