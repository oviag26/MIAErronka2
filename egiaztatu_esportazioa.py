# -*- coding: utf-8 -*-
"""Egiaztatu NumPy inferentziak (inferentzia.py) scikit-learn-en emaitza berberak ematen dituela.

PC-an exekutatzen da (scikit-learn eta pandas behar ditu). Ridge pipeline-a
erronka_MIA.ipynb-n bezala berreraikitzen du (banaketa kronologikoa, alpha
balidazioarekin) eta K-means-a SAA zatiko .pkl-tik kargatzen du. Gero 306
egunetan bi inplementazioak konparatzen ditu, urria eta azaroa barne
(entrenamenduan agertzen ez diren hilabeteak).
"""
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from esportatu_kmeans import PKL_LEHENETSIA
from inferentzia import KARPETA, AireEredua, irakurri_csv

sys.stdout.reconfigure(encoding='utf-8')

zenbakizkoak = ['NO (µg/m3)', 'NOX (µg/m3)', 'NO2 (µg/m3)', 'O3 (µg/m3)', 'PM2,5 (µg/m3)']
kategorikoak = ['Month', 'DayOfWeek']

df = pd.read_csv(os.path.join(KARPETA, 'MUNDAKA.csv'), sep=';', encoding='latin1')
df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
df = df.sort_values('Date').reset_index(drop=True)
df['Month'] = df['Date'].dt.month
df['DayOfWeek'] = df['Date'].dt.dayofweek

# 1. Ridge, koadernoko pauso berberak
df_eredua = df.dropna(subset=['PM10 (µg/m3)'])
muga = int(len(df_eredua) * 0.8)
X_tr = df_eredua[zenbakizkoak + kategorikoak].iloc[:muga]
y_tr = df_eredua['PM10 (µg/m3)'].iloc[:muga]
aurre = ColumnTransformer([
    ('zenbakizkoak', Pipeline([('imputer', SimpleImputer(strategy='median')),
                               ('scaler', StandardScaler())]), zenbakizkoak),
    ('kategorikoak', OneHotEncoder(handle_unknown='ignore', sparse_output=False), kategorikoak)])
bilaketa = GridSearchCV(Pipeline([('aurre', aurre), ('eredua', Ridge())]),
                        {'eredua__alpha': np.logspace(-3, 2, 11)}, cv=TimeSeriesSplit(n_splits=5),
                        scoring='neg_root_mean_squared_error').fit(X_tr, y_tr)
ridge_sk = bilaketa.best_estimator_

eredua = AireEredua()
egunak = irakurri_csv(os.path.join(KARPETA, 'MUNDAKA.csv'))
assert [e['Date'] for e in egunak] == list(df['Date'].dt.date), 'Data-ordena ez dator bat'

pred_sk = ridge_sk.predict(df[zenbakizkoak + kategorikoak])
pred_np = eredua.iragarri_pm10(egunak)
alde_ridge = np.abs(pred_sk - pred_np).max()
urri_azaro = df['Month'].isin([10, 11]).to_numpy()
print('Ridge alpha = {:.3f}'.format(bilaketa.best_params_['eredua__alpha']))
print('Ridge: scikit-learn vs NumPy, alde handiena 306 egunetan: {:.2e} µg/m³'.format(alde_ridge))
print('       urria eta azaroa bakarrik ({} egun): {:.2e} µg/m³'.format(
    urri_azaro.sum(), np.abs(pred_sk - pred_np)[urri_azaro].max()))

# 2. K-means, SAAko .pkl-a
kmeans_sk = joblib.load(PKL_LEHENETSIA)
zut_k = list(kmeans_sk.feature_names_in_)
k_sk = kmeans_sk.predict(df[zut_k])
k_np = eredua.klusterra(egunak)  # ordezkorik gabe: medianarekin, scikit-learn-en berdin
print('K-means: bat datozen egunak {}/{}'.format((k_sk == k_np).sum(), len(k_np)))

ondo = alde_ridge < 1e-9 and (k_sk == k_np).all()
print('EMAITZA:', 'ONDO, inplementazioak baliokideak dira' if ondo else 'ERROREA')
sys.exit(0 if ondo else 1)
