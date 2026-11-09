# -*- coding: utf-8 -*-
"""Sistema adituaren funtzionamenduaren froga.

1. Proba-kasuak: arau bakoitza noiz aktibatzen den egiaztatzen da (assert).
2. Datu errealak: 306 egunetan zenbat alerta sortzen diren arauka.
3. Sentikortasun-analisia: mugak aldatzean alerta kopurua nola aldatzen den.
4. Logika lausoa: arrisku-indizearen adibideak.

Emaitzak: emaitzak/sistema_aditua_froga.md eta emaitzak/sentikortasuna.png
(irudia matplotlib instalatuta badago bakarrik).

Erabilera:  python probak_sistema_aditua.py
"""
from __future__ import print_function

import datetime
import io
import os
import sys

from inferentzia import KARPETA, AireEredua, irakurri_csv
from sistema_aditua import MUGAK, SistemaAditua, arrisku_lausoa, egitateak_sortu

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EMAITZAK = os.path.join(KARPETA, 'emaitzak')
if not os.path.isdir(EMAITZAK):
    os.makedirs(EMAITZAK)


def egitateak(**kw):
    oinarria = {'data': '2026-07-01', 'hilabetea': 7, 'pm10_neurtua': 10.0, 'pm10_iragarria': 10.0,
                'pm25': 5.0, 'o3': 60.0, 'no2': 3.0, 'klusterra': 1}
    oinarria.update(kw)
    return oinarria


# --- 1. Proba-kasuak -------------------------------------------------------------
KASUAK = [
    ('Egun normala', egitateak(), set()),
    ('PM10 neurgailurik ez', egitateak(pm10_neurtua=None, pm10_iragarria=12.0), {'R1'}),
    ('PM10 hutsik + estimazio altua (kateatzea R1 -> R2)',
     egitateak(pm10_neurtua=None, pm10_iragarria=50.0), {'R1', 'R2'}),
    ('PM10 OME muga gainditzen', egitateak(pm10_neurtua=60.0, pm10_iragarria=55.0), {'R2'}),
    ('PM10 "Ona" gainditzen', egitateak(pm10_neurtua=25.0, pm10_iragarria=22.0), {'R3'}),
    ('Neurgailu-anomalia', egitateak(pm10_neurtua=30.0, pm10_iragarria=12.0), {'R3', 'R4'}),
    ('Ozono-episodioa (klusterra 2)', egitateak(o3=85.0, klusterra=2), {'R5'}),
    ('O3 altua baina beste kluster bat', egitateak(o3=85.0, klusterra=1), set()),
    ('O3 OME muga gainditzen', egitateak(o3=110.0, klusterra=2), {'R5', 'R6'}),
    ('NO2 OME muga gainditzen', egitateak(no2=30.0), {'R7'}),
]


def proba_kasuak(sistema):
    errenkadak = []
    for izena, egit, espero in KASUAK:
        memoria, alertak, exekutatuak = sistema.inferentzia(egit)
        lortua = {a['araua'] for a in alertak}
        ondo = lortua == espero
        errenkadak.append((izena, sorted(espero), sorted(lortua), exekutatuak,
                           memoria.get('pm10_eraginkorra'), ondo))
        assert ondo, '{}: espero {} lortua {}'.format(izena, espero, lortua)
    return errenkadak


# --- 2. Datu errealak ------------------------------------------------------------
def egun_errealak():
    eredua = AireEredua()
    egunak = irakurri_csv(os.path.join(KARPETA, 'MUNDAKA.csv'))
    pm10 = eredua.iragarri_pm10(egunak)
    klusterrak = eredua.klusterra(egunak, pm10)
    return [egitateak_sortu(e, p, k) for e, p, k in zip(egunak, pm10, klusterrak)]


def alerta_kopurua(sistema, egitate_zerrenda):
    arauka, egunak_alertarekin, egunak_abisuarekin = {}, 0, 0
    for egit in egitate_zerrenda:
        _, alertak, _ = sistema.inferentzia(egit)
        mailak = {a['maila'] for a in alertak}
        egunak_alertarekin += 'ALERTA' in mailak
        egunak_abisuarekin += 'ABISUA' in mailak
        for a in alertak:
            arauka[a['araua']] = arauka.get(a['araua'], 0) + 1
    return arauka, egunak_alertarekin, egunak_abisuarekin


# --- 3. Sentikortasuna ------------------------------------------------------------
FAKTOREAK = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]


def sentikortasuna(egitate_zerrenda):
    emaitzak = []
    for f in FAKTOREAK:
        mugak = {k: v * f for k, v in MUGAK.items()}
        _, alertak, abisuak = alerta_kopurua(SistemaAditua(mugak=mugak), egitate_zerrenda)
        emaitzak.append((f, alertak, abisuak))
    return emaitzak


def irudia(sent, bidea):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    x = [f for f, _, _ in sent]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x, [a for _, _, a in sent], color='#2a78d6', lw=2, marker='o', ms=6, label='Abisua duten egunak')
    ax.plot(x, [a for _, a, _ in sent], color='#eb6834', lw=2, marker='o', ms=6, label='Alerta duten egunak')
    for serie, kolorea, testua in [([a for _, _, a in sent], '#2a78d6', 'Abisuak'),
                                   ([a for _, a, _ in sent], '#eb6834', 'Alertak')]:
        ax.annotate(testua, (x[1], serie[1]), xytext=(8, 4), textcoords='offset points',
                    va='bottom', color='#52514e', fontsize=9)
    ax.axvline(1.0, color='#a3a29b', lw=1, ls='--')
    ax.text(1.0, ax.get_ylim()[1] * 0.97, ' oinarrizko mugak', color='#52514e', fontsize=9, va='top')
    ax.set_xlabel('Mugen faktorea (1,0 = OME / ICA mugak)')
    ax.set_ylabel('Egun kopurua (306 egunetik)')
    ax.set_title('Sistema adituaren sentikortasuna mugekiko', loc='left')
    ax.grid(axis='y', color='#e8e7e2')
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False, loc='upper right')
    fig.tight_layout()
    fig.savefig(bidea, dpi=130)
    plt.close(fig)
    return True


def main():
    sistema = SistemaAditua()
    kasuak = proba_kasuak(sistema)
    print('Proba-kasuak: {}/{} ondo'.format(sum(k[-1] for k in kasuak), len(kasuak)))

    egit = egun_errealak()
    arauka, n_alerta, n_abisu = alerta_kopurua(sistema, egit)
    print('Datu errealak:', arauka, '| alerta duten egunak:', n_alerta, '| abisua dutenak:', n_abisu)

    sent = sentikortasuna(egit)
    irudi_bidea = os.path.join(EMAITZAK, 'sentikortasuna.png')
    irudia_badago = irudia(sent, irudi_bidea)

    lausoak = [('Aire garbia', 8, 55, 3), ('Udako eguna', 18, 85, 3), ('O3 muga inguruan', 20, 98, 4),
               ('Partikula-episodioa', 48, 70, 10), ('NO2 altua', 12, 60, 32)]

    s = io.StringIO()
    w = lambda *a: print(*a, file=s)
    w('# Sistema adituaren funtzionamenduaren froga\n')
    w('Sortua: {} · Script-a: `probak_sistema_aditua.py`\n'.format(datetime.date.today()))
    w('## 1. Proba-kasuak\n')
    w('| Kasua | Espero ziren arauak | Lortutako alertak | Exekutatutako arauak (ordena) | PM10 eraginkorra | Emaitza |')
    w('|---|---|---|---|---|---|')
    for izena, espero, lortua, exek, pm10, ondo in kasuak:
        w('| {} | {} | {} | {} | {:.1f} | {} |'.format(izena, ', '.join(espero) or '-', ', '.join(lortua) or '-',
                                                     ' → '.join(exek), pm10, 'Ondo' if ondo else 'ERROREA'))
    w('\nHirugarren kasuak **aurrerantz kateatzea** erakusten du: R1-ek `pm10_eraginkorra` egitatea sortzen du '
      'ereduaren estimazioarekin, eta motorrak arauak berriro ebaluatzean R2 aktibatzen da.\n')
    w('## 2. Mundakako datu errealak (306 egun)\n')
    w('| Araua | Aktibazio kopurua |\n|---|---|')
    for araua in sorted(arauka):
        w('| {} | {} |'.format(araua, arauka[araua]))
    w('\nALERTA mailako alertaren bat duten egunak: **{}**. ABISUA duten egunak: **{}**.\n'.format(n_alerta, n_abisu))
    w('Mundaka aire garbiko estazioa da: PM10-ak eta NO2-ak ez dute inoiz OMEren muga gainditzen, eta alerta '
      'bakarrak ozonoarenak dira (udan). R1 49 aldiz aktibatzen da, PM10 neurgailuak daturik eman ez duen egunetan.\n')
    w('## 3. Sentikortasun-analisia\n')
    w('Muga guztiak faktore berarekin biderkatu ditugu eta alerta kopurua berriro kalkulatu dugu.\n')
    w('| Faktorea | Alerta duten egunak | Abisua duten egunak |\n|---|---|---|')
    for f, a, b in sent:
        w('| {:.1f} | {} | {} |'.format(f, a, b))
    if irudia_badago:
        w('\n![Sentikortasuna](sentikortasuna.png)\n')
    oinarria = [x for x in sent if x[0] == 1.0][0]
    jaitsia = [x for x in sent if x[0] == 0.8][0]
    w('\nSistema oso sentikorra da mugekiko, batez ere ozonoarenekiko: O3-aren balio gehienak 60-90 µg/m³ '
      'artean daude, mugatik gertu. Mugak %20 jaistean, alerta duten egunak {} izatetik {} izatera pasatzen dira '
      '(alarma-nekea: herritarrek alertei kasu egiteari uzten diote). Mugak igotzean, alertak desagertu egiten dira '
      'eta benetako episodioak gal daitezke. OME/ICA mugak (faktorea 1,0) zientifikoki justifikatuta daude eta '
      'oreka ona ematen dute estazio honetarako.\n'.format(oinarria[1], jaitsia[1]))
    w('## 4. Arrisku-indize lausoa\n')
    w('| Egoera | PM10 | O3 | NO2 | Indizea (0-100) | Etiketa |\n|---|---|---|---|---|---|')
    for izena, p, o, n in lausoak:
        ind, et = arrisku_lausoa(p, o, n)
        w('| {} | {} | {} | {} | {:.1f} | {} |'.format(izena, p, o, n, ind, et))
    w('\nLogika lausoak muga zorrotzen arazoa leuntzen du: O3 = 98 eta O3 = 101 egunek alerta desberdina '
      'ematen dute arau zorrotzekin, baina antzeko arrisku-indizea lausoarekin.')

    bidea = os.path.join(EMAITZAK, 'sistema_aditua_froga.md')
    with open(bidea, 'w', encoding='utf-8') as f:
        f.write(s.getvalue())
    print('Gordeta:', bidea, '| irudia:', irudi_bidea if irudia_badago else 'ez (matplotlib gabe)')


if __name__ == '__main__':
    main()
