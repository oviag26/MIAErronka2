# -*- coding: utf-8 -*-
"""Monitorizazio-dashboard-a: Python-en liburutegi estandarra + NumPy.

Ez du Flask, Streamlit edo interneteko konexiorik behar, eta beraz Jetson Nano-n
zuzenean exekuta daiteke (Python 3.6+). Zerbitzariak MUNDAKA.csv egunez egun
"erreproduzitzen" du (denbora errealeko monitorizazio simulatua): nabigatzaileak
egun bat eskatzen duen bakoitzean, inferentzia gailuan bertan egiten da
(Ridge + K-means + sistema aditua + arrisku lausoa) eta denbora neurtzen da.

Erabilera:
    python3 dashboard.py [--ataka 8050]
    Gero nabigatzailean: http://localhost:8050  (edo http://<jetson-ip>:8050)
"""
from __future__ import print_function

import argparse
import json
import os
import socketserver
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from inferentzia import KARPETA, AireEredua, ica_kategoria, irakurri_csv
from sistema_aditua import MUGAK, SistemaAditua, arrisku_lausoa, egitateak_sortu

EREDUA = AireEredua()
SISTEMA = SistemaAditua()
EGUNAK = irakurri_csv(os.path.join(KARPETA, 'MUNDAKA.csv'))
HTML_BIDEA = os.path.join(KARPETA, 'dashboard.html')

# "Kutsadura-episodioa" eszenatokia: neurketak biderkatu alertak erakusteko (demoa)
EPISODIOA = {'PM10 (µg/m3)': 3.5, 'PM2,5 (µg/m3)': 3.5, 'NO2 (µg/m3)': 8.0, 'NOX (µg/m3)': 6.0,
             'NO (µg/m3)': 4.0, 'O3 (µg/m3)': 1.25}


def egun_bat(i, eszenatokia):
    eguna = dict(EGUNAK[i % len(EGUNAK)])
    if eszenatokia == 'episodioa':
        for z, f in EPISODIOA.items():
            if eguna.get(z) is not None:
                eguna[z] = eguna[z] * f

    t0 = time.perf_counter()
    pm10 = EREDUA.iragarri_pm10([eguna])
    klusterra = EREDUA.klusterra([eguna], pm10)
    memoria, alertak, exekutatuak = SISTEMA.inferentzia(egitateak_sortu(eguna, pm10[0], klusterra[0]))
    indizea, etiketa = arrisku_lausoa(memoria['pm10_eraginkorra'], eguna.get('O3 (µg/m3)'),
                                      eguna.get('NO2 (µg/m3)'))
    ms = (time.perf_counter() - t0) * 1000.0

    return {
        'i': i % len(EGUNAK),
        'data': str(eguna['Date']),
        'neurketak': {z.split(' ')[0]: eguna.get(z) for z in
                      ['NO (µg/m3)', 'NOX (µg/m3)', 'NO2 (µg/m3)', 'O3 (µg/m3)', 'PM10 (µg/m3)', 'PM2,5 (µg/m3)']},
        'pm10_iragarria': round(float(pm10[0]), 2),
        'pm10_eraginkorra': round(float(memoria['pm10_eraginkorra']), 2),
        'pm10_estimatua': bool(memoria['pm10_estimatua']),
        'kategoria': ica_kategoria(memoria['pm10_eraginkorra']),
        'klusterra': int(klusterra[0]),
        'kluster_izena': EREDUA.kluster_izena(klusterra[0]),
        'alertak': alertak,
        'arauak': exekutatuak,
        'arriskua': {'indizea': round(indizea, 1), 'etiketa': etiketa},
        'inferentzia_ms': round(ms, 4),
        'eszenatokia': eszenatokia,
    }


class Kudeatzailea(BaseHTTPRequestHandler):
    def _bidali(self, kodea, edukia, mota):
        datuak = edukia.encode('utf-8')
        self.send_response(kodea)
        self.send_header('Content-Type', mota + '; charset=utf-8')
        self.send_header('Content-Length', str(len(datuak)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(datuak)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        if url.path in ('/', '/index.html'):
            with open(HTML_BIDEA, encoding='utf-8') as f:
                self._bidali(200, f.read(), 'text/html')
        elif url.path == '/api/info':
            info = {'egunak': len(EGUNAK), 'hasiera': str(EGUNAK[0]['Date']),
                    'amaiera': str(EGUNAK[-1]['Date']), 'mugak': MUGAK,
                    'klusterrak': EREDUA.kluster_izenak}
            self._bidali(200, json.dumps(info, ensure_ascii=False), 'application/json')
        elif url.path == '/api/eguna':
            try:
                i = int(q.get('i', ['0'])[0])
            except ValueError:
                return self._bidali(400, '{"errorea": "i ez da zenbakia"}', 'application/json')
            eszenatokia = q.get('eszenatokia', ['normala'])[0]
            self._bidali(200, json.dumps(egun_bat(i, eszenatokia), ensure_ascii=False), 'application/json')
        else:
            self._bidali(404, 'Ez da aurkitu', 'text/plain')

    def log_message(self, *args):
        pass  # kontsola garbi mantentzeko


class Zerbitzaria(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ataka', type=int, default=8050)
    parser.add_argument('--helbidea', default='0.0.0.0', help='0.0.0.0 = sareko beste gailuetatik ere ikusgai')
    args = parser.parse_args()
    zerb = Zerbitzaria((args.helbidea, args.ataka), Kudeatzailea)
    print('Dashboard-a martxan: http://localhost:{}  (Ctrl+C gelditzeko)'.format(args.ataka))
    sys.stdout.flush()
    try:
        zerb.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
