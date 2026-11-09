# -*- coding: utf-8 -*-
"""SAA zatiko K-means eredua (kmeans_eredua.pkl) JSON formatura esportatu.

PC-an exekutatzen da (scikit-learn behar du). Emaitza, kmeans_eredua.json,
Jetson Nano-n NumPy bakarrik erabiliz kargatzen da (ikus inferentzia.py).

Erabilera:
    python esportatu_kmeans.py [--pkl ../../SAA/Erronka2SAA/kmeans_eredua.pkl]
"""
import argparse
import json
import os

import joblib

KARPETA = os.path.dirname(os.path.abspath(__file__))
PKL_LEHENETSIA = os.path.join(KARPETA, '..', '..', 'SAA', 'Erronka2SAA', 'kmeans_eredua.pkl')

# SAA koadernoko interpretazioa (5. atala)
IZENAK = {'0': 'NOx altuko egunak', '1': 'Aire garbiko egunak',
          '2': 'O3 eta partikula altuko egunak'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pkl', default=PKL_LEHENETSIA)
    args = parser.parse_args()

    pipeline = joblib.load(args.pkl)
    imputer = pipeline.named_steps['aurre'].named_steps['imputer']
    scaler = pipeline.named_steps['aurre'].named_steps['scaler']
    kmeans = pipeline.named_steps['kmeans']

    parametroak = {
        'zutabeak': list(pipeline.feature_names_in_),
        'medianak': imputer.statistics_.tolist(),
        'batezbestekoak': scaler.mean_.tolist(),
        'desbideratzeak': scaler.scale_.tolist(),
        'zentroideak': kmeans.cluster_centers_.tolist(),
        'izenak': IZENAK,
    }
    irteera = os.path.join(KARPETA, 'kmeans_eredua.json')
    with open(irteera, 'w', encoding='utf-8') as f:
        json.dump(parametroak, f, ensure_ascii=False, indent=1)
    print('Gordeta:', irteera, '({:.1f} KB)'.format(os.path.getsize(irteera) / 1024))


if __name__ == '__main__':
    main()
