# -*- coding: utf-8 -*-
"""Inferentzia-denboren neurketa (PC-an eta Jetson Nano-n exekutatzeko).

NumPy bakarrik behar du. TFLite (MLP) neurketa aukerakoa da: tflite_runtime edo
tensorflow instalatuta badago bakarrik egiten da.

Neurtzen dena:
  * Ridge, egun bat (aurreprozesamendua + iragarpena)
  * Ridge, 306 egun batera (lotea)
  * K-means, egun bat
  * Sistema aditua, egun bat
  * Kate osoa, egun bat (Ridge + K-means + sistema aditua): dashboard-ak egiten duena
  * MLP TFLite, egun bat (aukerakoa)

Emaitza: emaitzak/neurketa_<gailua>.json eta taula pantailan.

Erabilera:  python3 neurketa.py [--errepikapenak 1000]
"""
from __future__ import print_function

import argparse
import json
import os
import platform
import socket
import sys
import time

import numpy as np

from inferentzia import KARPETA, AireEredua, irakurri_csv
from sistema_aditua import SistemaAditua, egitateak_sortu

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def gailuaren_izena():
    """Jetson-ean /proc/device-tree/model irakurtzen da; bestela prozesadorea."""
    try:
        with open('/proc/device-tree/model') as f:
            return f.read().strip('\x00\n ')
    except (IOError, OSError):
        return platform.processor() or platform.machine()


def neurtu(funtzioa, errepikapenak, berotzea=50):
    """Funtzioa exekutatu eta denborak milisegundotan itzuli."""
    for _ in range(berotzea):
        funtzioa()
    denborak = np.empty(errepikapenak)
    for i in range(errepikapenak):
        t0 = time.perf_counter()
        funtzioa()
        denborak[i] = (time.perf_counter() - t0) * 1000.0
    return {'batezbestekoa_ms': float(denborak.mean()), 'mediana_ms': float(np.median(denborak)),
            'p95_ms': float(np.percentile(denborak, 95)), 'max_ms': float(denborak.max()),
            'errepikapenak': errepikapenak}


def tflite_interpretea():
    bidea = os.path.join(KARPETA, 'mlp_pm10.tflite')
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        try:
            from tensorflow.lite import Interpreter  # noqa
        except ImportError:
            return None
    interp = Interpreter(model_path=bidea)
    interp.allocate_tensors()
    return interp


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--errepikapenak', type=int, default=1000)
    args = parser.parse_args()
    n = args.errepikapenak

    eredua = AireEredua()
    sistema = SistemaAditua()
    egunak = irakurri_csv(os.path.join(KARPETA, 'MUNDAKA.csv'))
    eguna = [egunak[-1]]
    p = eredua.iragarri_pm10(eguna)
    k = eredua.klusterra(eguna, p)
    egitateak = egitateak_sortu(eguna[0], p[0], k[0])

    def katea():
        pm10 = eredua.iragarri_pm10(eguna)
        kl = eredua.klusterra(eguna, pm10)
        return sistema.inferentzia(egitateak_sortu(eguna[0], pm10[0], kl[0]))

    neurketak = [
        ('Ridge, egun 1', lambda: eredua.iragarri_pm10(eguna), n),
        ('Ridge, {} egun (lotea)'.format(len(egunak)), lambda: eredua.iragarri_pm10(egunak), max(n // 10, 20)),
        ('K-means, egun 1', lambda: eredua.klusterra(eguna, p), n),
        ('Sistema aditua, egun 1', lambda: sistema.inferentzia(egitateak), n),
        ('Kate osoa, egun 1', katea, n),
    ]

    interp = tflite_interpretea()
    if interp is not None:
        sarrera = interp.get_input_details()[0]
        irteera = interp.get_output_details()[0]
        x = eredua.ezaugarriak(eguna).astype(np.float32)

        def mlp():
            interp.set_tensor(sarrera['index'], x)
            interp.invoke()
            return interp.get_tensor(irteera['index'])
        neurketak.append(('MLP TFLite, egun 1', mlp, n))

    emaitzak = {
        'gailua': gailuaren_izena(),
        'ostalaria': socket.gethostname(),
        'sistema': platform.platform(),
        'python': platform.python_version(),
        'numpy': np.__version__,
        'tflite': interp is not None,
        'neurketak': {},
    }
    print('Gailua: {} | Python {} | NumPy {}'.format(emaitzak['gailua'], emaitzak['python'], emaitzak['numpy']))
    print('{:<28} {:>12} {:>10} {:>10}'.format('Neurketa', 'Batezb. ms', 'Mediana', 'p95'))
    for izena, funtzioa, errep in neurketak:
        r = neurtu(funtzioa, errep)
        emaitzak['neurketak'][izena] = r
        print('{:<28} {:>12.4f} {:>10.4f} {:>10.4f}'.format(izena, r['batezbestekoa_ms'], r['mediana_ms'], r['p95_ms']))
    if interp is None:
        print('(TFLite ez dago instalatuta: MLP neurketa saltatu da)')

    karpeta = os.path.join(KARPETA, 'emaitzak')
    if not os.path.isdir(karpeta):
        os.makedirs(karpeta)
    jetson = 'jetson' in emaitzak['gailua'].lower()
    bidea = os.path.join(karpeta, 'neurketa_{}.json'.format('jetson' if jetson else 'pc'))
    with open(bidea, 'w', encoding='utf-8') as f:
        json.dump(emaitzak, f, ensure_ascii=False, indent=1)
    print('Gordeta:', bidea)


if __name__ == '__main__':
    main()
