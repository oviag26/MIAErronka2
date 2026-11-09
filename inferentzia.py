# -*- coding: utf-8 -*-
"""Jetson Nano-rako inferentzia: NumPy bakarrik.

Ridge eredua (PM10) eta K-means eredua (egun-motak) JSON fitxategietatik kargatzen
ditu eta scikit-learn-en aurreprozesamendu bera eskuz aplikatzen du. Ez du
scikit-learn, pandas edo TensorFlow behar, eta Python 3.6-rekin bateragarria da
(Jetson Nano-ko JetPack 4.x).

Erabilera:
    python3 inferentzia.py                # MUNDAKA.csv-ko azken 5 egunak
    python3 inferentzia.py --csv beste.csv
"""
import argparse
import csv
import datetime
import json
import os

import numpy as np

KARPETA = os.path.dirname(os.path.abspath(__file__))

# CSV-ko zutabeak (latin1 kodeketarekin irakurrita)
ZUTABEAK = ['NO (µg/m3)', 'NOX (µg/m3)', 'NO2 (µg/m3)', 'O3 (µg/m3)',
            'PM10 (µg/m3)', 'PM2,5 (µg/m3)']

# Airearen Kalitatearen Indizea (ICA, MITECO), PM10 eguneko batezbestekoa (µg/m³)
ICA_PM10 = [(20, 'Ona'), (40, 'Nahiko ona'), (50, 'Erregularra'),
            (100, 'Txarra'), (150, 'Oso txarra'), (float('inf'), 'Muturrekoa')]


def ica_kategoria(pm10):
    """PM10 balio bati dagokion ICA kategoria."""
    for muga, izena in ICA_PM10:
        if pm10 <= muga:
            return izena
    return ICA_PM10[-1][1]


def irakurri_csv(bidea):
    """Open Data Euskadi-ko CSV-a irakurri: egun bakoitza dict bat, ordena kronologikoan.

    Balio hutsak None dira.
    """
    egunak = []
    with open(bidea, encoding='latin1', newline='') as f:
        for errenkada in csv.DictReader(f, delimiter=';'):
            eguna = {'Date': datetime.datetime.strptime(errenkada['Date'], '%d/%m/%Y').date()}
            for z in ZUTABEAK:
                balioa = (errenkada.get(z) or '').strip().replace(',', '.')
                eguna[z] = float(balioa) if balioa else None
            egunak.append(eguna)
    egunak.sort(key=lambda e: e['Date'])
    return egunak


class AireEredua(object):
    """PM10 Ridge eredua eta K-means eredua, JSON fitxategietatik kargatuta."""

    def __init__(self, karpeta=KARPETA):
        with open(os.path.join(karpeta, 'aurreprozesamendua.json'), encoding='utf-8') as f:
            aurre = json.load(f)
        with open(os.path.join(karpeta, 'ridge_eredua.json'), encoding='utf-8') as f:
            ridge = json.load(f)
        with open(os.path.join(karpeta, 'kmeans_eredua.json'), encoding='utf-8') as f:
            kmeans = json.load(f)

        # Ridge-ren aurreprozesamendua
        self.zenbakizkoak = aurre['zenbakizkoak']
        self.medianak = np.array(aurre['medianak'], dtype=np.float64)
        self.batezbestekoak = np.array(aurre['batezbestekoak'], dtype=np.float64)
        self.desbideratzeak = np.array(aurre['desbideratzeak'], dtype=np.float64)
        self.hilabeteak = list(aurre['kategoriak'][0])
        self.asteko_egunak = list(aurre['kategoriak'][1])
        self.koefizienteak = np.array(ridge['koefizienteak'], dtype=np.float64)
        self.konstantea = float(ridge['konstantea'])
        self.n_ezaugarri = len(self.zenbakizkoak) + len(self.hilabeteak) + len(self.asteko_egunak)
        assert self.n_ezaugarri == len(self.koefizienteak), 'Ezaugarri kopurua ez dator bat'

        # K-means
        self.k_zutabeak = kmeans['zutabeak']
        self.k_medianak = np.array(kmeans['medianak'], dtype=np.float64)
        self.k_batezbestekoak = np.array(kmeans['batezbestekoak'], dtype=np.float64)
        self.k_desbideratzeak = np.array(kmeans['desbideratzeak'], dtype=np.float64)
        self.zentroideak = np.array(kmeans['zentroideak'], dtype=np.float64)
        self.kluster_izenak = kmeans['izenak']

    # --- PM10 erregresioa -------------------------------------------------
    def ezaugarriak(self, egunak):
        """Egunen zerrenda -> (n, 21) matrizea, scikit-learn-en ColumnTransformer-aren baliokidea.

        1) Zenbakizkoak: hutsak medianarekin bete eta estandarizatu.
        2) Month eta DayOfWeek: one-hot. Entrenamenduan agertu ez diren balioek
           (adib. urria eta azaroa) zero bektorea ematen dute (handle_unknown='ignore').
        """
        n = len(egunak)
        X = np.zeros((n, self.n_ezaugarri), dtype=np.float64)
        nz, nh = len(self.zenbakizkoak), len(self.hilabeteak)
        for i, eguna in enumerate(egunak):
            zenb = [eguna.get(z) for z in self.zenbakizkoak]
            zenb = np.array([self.medianak[j] if v is None else v for j, v in enumerate(zenb)])
            X[i, :nz] = (zenb - self.batezbestekoak) / self.desbideratzeak
            hilabetea = eguna['Date'].month
            asteguna = eguna['Date'].weekday()  # astelehena = 0, pandas-en dayofweek bezala
            if hilabetea in self.hilabeteak:
                X[i, nz + self.hilabeteak.index(hilabetea)] = 1.0
            if asteguna in self.asteko_egunak:
                X[i, nz + nh + self.asteko_egunak.index(asteguna)] = 1.0
        return X

    def iragarri_pm10(self, egunak):
        """Egun bakoitzeko PM10 kalkulatua (µg/m³)."""
        return self.ezaugarriak(egunak).dot(self.koefizienteak) + self.konstantea

    # --- K-means ------------------------------------------------------------
    def klusterra(self, egunak, pm10_ordezkoak=None):
        """Egun bakoitzaren klusterra (indizea).

        PM10 hutsik badago eta pm10_ordezkoak ematen bada, ereduaren estimazioa
        erabiltzen da medianaren ordez (bi ereduen arteko integrazioa).
        """
        X = np.zeros((len(egunak), len(self.k_zutabeak)), dtype=np.float64)
        for i, eguna in enumerate(egunak):
            for j, z in enumerate(self.k_zutabeak):
                v = eguna.get(z)
                if v is None and z == 'PM10 (µg/m3)' and pm10_ordezkoak is not None:
                    v = float(pm10_ordezkoak[i])
                X[i, j] = self.k_medianak[j] if v is None else v
        X = (X - self.k_batezbestekoak) / self.k_desbideratzeak
        distantziak = ((X[:, None, :] - self.zentroideak[None, :, :]) ** 2).sum(axis=2)
        return distantziak.argmin(axis=1)

    def kluster_izena(self, indizea):
        return self.kluster_izenak[str(int(indizea))]


def main():
    parser = argparse.ArgumentParser(description='PM10 inferentzia NumPy-rekin')
    parser.add_argument('--csv', default=os.path.join(KARPETA, 'MUNDAKA.csv'))
    parser.add_argument('--azkenak', type=int, default=5, help='Erakutsi beharreko azken egunak')
    args = parser.parse_args()

    eredua = AireEredua()
    egunak = irakurri_csv(args.csv)[-args.azkenak:]
    pm10 = eredua.iragarri_pm10(egunak)
    klusterrak = eredua.klusterra(egunak, pm10)
    print('{:<12} {:>8} {:>10} {:<12} {}'.format('Data', 'PM10', 'Kalkulatua', 'ICA', 'Klusterra'))
    for eguna, p, k in zip(egunak, pm10, klusterrak):
        neurtua = '-' if eguna['PM10 (µg/m3)'] is None else '{:.0f}'.format(eguna['PM10 (µg/m3)'])
        print('{:<12} {:>8} {:>10.2f} {:<12} {}'.format(
            str(eguna['Date']), neurtua, p, ica_kategoria(p), eredua.kluster_izena(k)))


if __name__ == '__main__':
    main()
