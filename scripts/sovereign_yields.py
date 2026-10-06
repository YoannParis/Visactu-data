"""Collect official 10-year sovereign yields. Python standard library only."""
import csv
import io
import json
import math
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'sovereign-yields/10y.json'
SOURCES = {
    c: dict(source='Banque de France — Webstat', frequency='mensuelle',
            series=f'FM.M.{c}.EUR.FR2.BB.{c}10YT_RR.YLD',
            url=f'https://webstat.banque-france.fr/export/csv/fr/catalog/FM/FM.M.{c}.EUR.FR2.BB.{c}10YT_RR.YLD',
            note='Moyenne mensuelle du rendement de l’emprunt phare à 10 ans.')
    for c in ('IT', 'PT')
}
SOURCES.update({
    'FR': dict(source='Euronext', frequency='quotidienne',
        series='FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA',
        url='https://webstat.banque-france.fr/export/csv/fr/catalog/FM/FM.D.FR.EUR.FR2.BB.FRMOYTEC10.HSTA',
        note='TEC 10 : taux à échéance constante de 10 ans, calculé par Euronext et rediffusé par la Banque de France. Observation quotidienne, et non moyenne mensuelle.'),
    'DE': dict(source='Deutsche Bundesbank', frequency='quotidienne',
        series='BBSSY.D.REN.EUR.A630.000000WT1010.A',
        url='https://api.statistiken.bundesbank.de/rest/download/BBSSY/D.REN.EUR.A630.000000WT1010.A?format=csv&lang=en',
        note='Rendement de l’obligation fédérale de référence à 10 ans.'),
    'ES': dict(source='Banco de España', frequency='quotidienne', series='D_G0B1F0ZP',
        url='https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_3.csv',
        note='Rendement des obligations de référence à 10 ans sur le marché secondaire.'),
    'BE': dict(source='Banque nationale de Belgique', frequency='quotidienne', series='BE2:DF_IROLOBE2(1.0)/D.10Y.F',
        url='https://nsidisseminate-stat.nbb.be/rest/data/BE2,DF_IROLOBE2,1.0/D.10Y.F?startPeriod=2021-01-01',
        note='Rendement OLO à durée résiduelle fixe de 10 ans.'),
    'GR': dict(source='Banque de Grèce', frequency='quotidienne', series='Greek government securities / 10 years / Yield (%)',
        url='https://www.bankofgreece.gr/en/statistics/financial-markets-and-interest-rates/greek-government-securities',
        note='Rendement des titres d’État à 10 ans. Historique quotidien accumulé depuis la mise en service.'),
})


def parse(country, raw):
    src = SOURCES[country]
    text = raw.decode('latin1' if country == 'ES' else 'utf-8-sig')
    if country in ('FR', 'IT', 'PT'):
        rows = list(csv.DictReader(io.StringIO(text), delimiter=';'))
        expected_frequency = 'D' if src['frequency'] == 'quotidienne' else 'M'
        if not rows or any(r['series_key'] != src['series'] or r['FREQ'] != expected_frequency or r['UNIT'] != 'PC' for r in rows):
            raise ValueError('Unexpected Webstat series or units')
        if country == 'FR' and any(r['SOURCE_AGENCY'] != 'EUXT' for r in rows):
            raise ValueError('Unexpected TEC10 provider')
        return [(r['time_period'], r['obs_value']) for r in rows]
    if country == 'DE':
        rows = list(csv.reader(io.StringIO(text)))
        if src['series'] not in rows[0]:
            raise ValueError('Unexpected Bundesbank series')
        return [(r[0], r[1]) for r in rows if len(r) >= 2 and re.fullmatch(r'\d{4}-\d{2}-\d{2}', r[0])]
    if country == 'ES':
        rows = list(csv.reader(io.StringIO(text)))
        col = rows[0].index(src['series'])
        months = {m: i + 1 for i, m in enumerate('ENE FEB MAR ABR MAY JUN JUL AGO SEP OCT NOV DIC'.split())}
        points = []
        for r in rows[1:]:
            match = re.fullmatch(r'(\d{2}) ([A-Z]{3}) (\d{4})', r[0].strip())
            if match:
                day, month, year = match.groups()
                points.append((f'{year}-{months[month]:02d}-{day}', r[col]))
        return points
    if country == 'BE':
        rows = list(csv.DictReader(io.StringIO(text)))
        if not rows or any((r['FREQ'], r['IROLOBE2_MATUR'], r['IROLOBE2_TYPE']) != ('D', '10Y', 'F') for r in rows):
            raise ValueError('Unexpected Belgian maturity or frequency')
        return [(r['TIME_PERIOD'], r['OBS_VALUE']) for r in rows]
    if country == 'GR':
        # Restrict parsing to the published maturity table; fail closed if it changes.
        tables = re.findall(r'<table\b[^>]*>.*?</table>', text, re.S)
        table = next(t for t in tables if 'Maturity (Years)' in t and 'Yield (%)' in t)
        maturities = re.findall(r'<th colspan="2">(\d+)</th>', table)
        if maturities != ['3', '5', '7', '10', '15', '20', '30']:
            raise ValueError('Greek table layout changed')
        points = []
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', table, re.S):
            cells = [unescape(re.sub('<[^>]+>', '', c)).strip() for c in re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.S)]
            if len(cells) == 15 and re.fullmatch(r'\d{2}/\d{2}/\d{4}', cells[0]):
                points.append((datetime.strptime(cells[0], '%d/%m/%Y').date().isoformat(), cells[8]))
        return points
    raise ValueError('Unsupported country')


def validated(points, frequency, today):
    values = {}
    for day, raw in points:
        if str(raw).strip() in ('', '.', '_', '-', '—', '…', 'N/A'):
            continue
        expected = r'\d{4}-\d{2}' if frequency == 'mensuelle' else r'\d{4}-\d{2}-\d{2}'
        if not re.fullmatch(expected, day):
            raise ValueError('Invalid observation date')
        parsed = date.fromisoformat(day + '-01' if len(day) == 7 else day)
        value = float(str(raw).replace(',', '.'))
        if not math.isfinite(value) or not -10 <= value <= 100:
            raise ValueError('Invalid yield')
        if parsed > today:
            raise ValueError('Future observation')
        if parsed >= today - timedelta(days=6 * 366):
            values[day] = value
    if not values:
        raise ValueError('No valid observations')
    return [{'date': d, 'value': v} for d, v in sorted(values.items())]


def fetch_source(country):
    req = urllib.request.Request(SOURCES[country]['url'], headers={
        'User-Agent': 'Visactu-official-yields/1.0', 'Accept': 'text/csv,text/html;q=0.9,*/*;q=0.8'})
    with urllib.request.urlopen(req, timeout=50) as res:
        raw = res.read(15_000_001)
    if len(raw) > 15_000_000:
        raise ValueError('Oversized response')
    return parse(country, raw)


def collect(previous, fetcher=fetch_source, now=None):
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat()
    data, metadata, failures = {}, {}, []

    def one(country):
        src = SOURCES[country]
        old_meta = previous.get('countries', {}).get(country, {})
        old = previous.get('data', {}).get(country, []) if old_meta.get('series') == src['series'] else []
        meta = {**src, 'checkedAt': stamp, 'lastSuccessAt': old_meta.get('lastSuccessAt') if old_meta.get('series') == src['series'] else None, 'status': 'ok'}
        try:
            fresh = validated(fetcher(country), src['frequency'], now.date())
            if old and fresh[-1]['date'] < old[-1]['date']:
                raise ValueError('Source returned older data')
            # Merge only observations from the SAME series. Preserve Greek rolling history.
            merged = {p['date']: p['value'] for p in old}
            merged.update({p['date']: p['value'] for p in fresh})
            points = validated(merged.items(), src['frequency'], now.date())
            meta['lastSuccessAt'] = stamp
        except Exception as exc:
            points = old
            meta['status'] = 'error'
            meta['error'] = type(exc).__name__ + ': ' + str(exc)[:200]
        meta['lastObservation'] = points[-1]['date'] if points else None
        if points and meta['status'] == 'ok':
            latest = date.fromisoformat(points[-1]['date'] + ('-01' if src['frequency'] == 'mensuelle' else ''))
            limit = 75 if src['frequency'] == 'mensuelle' else 10
            if (now.date() - latest).days > limit:
                meta['status'] = 'stale'
        return country, points, meta

    with ThreadPoolExecutor(max_workers=4) as pool:
        for country, points, meta in pool.map(one, SOURCES):
            data[country], metadata[country] = points, meta
            if meta['status'] != 'ok':
                failures.append(country)
    return dict(schemaVersion=1, maturity='10Y', frequency='mixte', mode='per_country',
                source='Euronext et banques centrales nationales (détail par pays)', fetchedAt=stamp,
                data=data, countries=metadata), failures


def main():
    previous = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}
    snapshot, failures = collect(previous)
    if not any(snapshot['data'].values()):
        raise RuntimeError('No data available; existing file not modified')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')) + '\n')
    tmp.replace(OUTPUT)
    for c, m in snapshot['countries'].items():
        print(c, m['lastObservation'], m['status'])
    # Publish last-good values/status before failing the workflow's final health check.
    return 2 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
