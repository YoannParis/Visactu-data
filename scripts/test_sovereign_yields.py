import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from sovereign_yields import SOURCES, collect, parse, validated

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / 'fixtures'


class CollectorTests(unittest.TestCase):
    def fixture(self, c):
        suffix = '.json' if c == 'PT' else '.html' if c in ('GR', 'IT') else '.csv'
        return parse(c, (FIXTURES / (c + suffix)).read_bytes())

    def test_real_official_formats(self):
        expected = {'FR': 4.899, 'IT': 4.524, 'PT': 4.0, 'GR': 4.53}
        for c, src in SOURCES.items():
            points = validated(self.fixture(c), src['frequency'], NOW.date())
            self.assertGreater(len(points), 0)
            if c in expected:
                self.assertAlmostEqual(points[-1]['value'], expected[c], places=4)

    def test_missing_zero_negative_and_invalid(self):
        points = validated([('2026-09-30', ''), ('2026-09-29', '0'), ('2026-09-28', '-0,2')], 'quotidienne', NOW.date())
        self.assertEqual([p['value'] for p in points], [-0.2, 0.0])
        for value in ('NaN', 'Infinity', '1000'):
            with self.assertRaises(ValueError):
                validated([('2026-09-30', value)], 'quotidienne', NOW.date())
        with self.assertRaises(ValueError):
            validated([('2099-01-01', '4')], 'quotidienne', NOW.date())

    def test_failure_preserves_data_and_success_date(self):
        previous, _ = collect({}, self.fixture, NOW)
        def fail(c):
            if c == 'FR':
                raise TimeoutError('test outage')
            return self.fixture(c)
        result, failures = collect(previous, fail, NOW)
        self.assertIn('FR', failures)
        self.assertEqual(previous['data']['FR'], result['data']['FR'])
        self.assertEqual(previous['countries']['FR']['lastSuccessAt'], result['countries']['FR']['lastSuccessAt'])
        self.assertEqual(result['countries']['FR']['status'], 'error')
        self.assertEqual(result['countries']['GR']['status'], 'ok')

    def test_regression_does_not_replace_latest(self):
        previous, _ = collect({}, self.fixture, NOW)
        def old(c):
            return [('2025-01-02', '2')] if c == 'FR' else self.fixture(c)
        result, failures = collect(previous, old, NOW)
        self.assertIn('FR', failures)
        self.assertEqual(result['data']['FR'], previous['data']['FR'])

    def test_series_identity_and_greek_layout(self):
        raw = (FIXTURES / 'FR.csv').read_bytes().replace(b'FM.D.FR', b'FM.M.FR')
        with self.assertRaises(ValueError):
            parse('FR', raw)
        raw = (FIXTURES / 'GR.html').read_bytes().replace(b'colspan="2">10', b'colspan="2">12')
        with self.assertRaises(ValueError):
            parse('GR', raw)

    def test_france_daily_replaces_monthly_history(self):
        previous = {'data': {'FR': [{'date': '2026-09', 'value': 4.4771}]},
                    'countries': {'FR': {'series': 'FM.M.FR.EUR.FR2.BB.FR10YT_RR.YLD',
                                         'lastSuccessAt': '2026-10-02T12:00:00+00:00'}}}
        result, _ = collect(previous, self.fixture, NOW)
        self.assertEqual(result['countries']['FR']['frequency'], 'quotidienne')
        self.assertEqual(result['countries']['FR']['source'], 'Euronext')
        self.assertTrue(all(len(p['date']) == 10 for p in result['data']['FR']))
        self.assertFalse(any(p['date'] == '2026-09' for p in result['data']['FR']))
        self.assertEqual(result['countries']['IT']['frequency'], 'quotidienne')

    def test_italy_daily_history_and_source_boundaries(self):
        previous = {'data': {'IT': [{'date': '2026-09', 'value': 4.3772}]},
                    'countries': {'IT': {'series': 'FM.M.IT.EUR.FR2.BB.IT10YT_RR.YLD'}}}
        result, failures = collect(previous, self.fixture, NOW)
        self.assertNotIn('IT', failures)
        points = result['data']['IT']
        self.assertGreater(len(points), 1500)
        self.assertEqual(len(points), len({p['date'] for p in points}))
        self.assertTrue(all(len(p['date']) == 10 for p in points))
        values = {p['date']: p['value'] for p in points}
        self.assertEqual(values['2026-09-30'], 4.59)  # Countryeconomy, not Investing
        self.assertEqual(values['2026-10-01'], 4.708)  # Investing
        self.assertEqual(values['2026-10-05'], 4.638)
        self.assertEqual(values['2026-10-06'], 4.524)  # MTS, not Investing 4.559
        self.assertEqual(result['frequency'], 'quotidienne')
        self.assertEqual(len(result['countries']['IT']['segments']), 3)

    def test_mts_rejects_wrong_maturity_intraday_or_inconsistent_date(self):
        raw = (FIXTURES / 'IT.html').read_bytes()
        self.assertEqual(parse('IT', raw), [('2026-10-06', '4.524')])
        for before, after in [(b'AA_Spread_IT', b'AA_30ySprd_IT'),
                              (b'5:30 PM', b'4:30 PM'),
                              (b'10/06/2026', b'10/05/2026'),
                              (b'Italy (3.8%', b'Spain (3.8%')]:
            with self.assertRaises(ValueError):
                parse('IT', raw.replace(before, after))

    def test_italy_migration_outage_and_daily_accumulation(self):
        previous = {'data': {'IT': [{'date': '2026-09', 'value': 4.3772}]},
                    'countries': {'IT': {'series': 'FM.M.IT.EUR.FR2.BB.IT10YT_RR.YLD',
                                         'source': 'Banque de France — Webstat', 'frequency': 'mensuelle',
                                         'lastSuccessAt': '2026-10-02T12:00:00+00:00'}}}
        def fail(c):
            if c == 'IT':
                raise TimeoutError('MTS outage')
            return self.fixture(c)
        fallback, _ = collect(previous, fail, NOW)
        self.assertEqual(fallback['data']['IT'], previous['data']['IT'])
        self.assertEqual(fallback['countries']['IT']['frequency'], 'mensuelle')
        self.assertEqual(fallback['frequency'], 'mixte')
        daily, _ = collect(fallback, self.fixture, NOW)
        outage, _ = collect(daily, fail, NOW)
        self.assertEqual(outage['data']['IT'], daily['data']['IT'])
        self.assertEqual(outage['countries']['IT']['lastSuccessAt'], daily['countries']['IT']['lastSuccessAt'])
        def next_day(c):
            return [('2026-10-07', '4.5')] if c == 'IT' else self.fixture(c)
        updated, _ = collect(daily, next_day, datetime(2026, 10, 7, tzinfo=timezone.utc))
        self.assertEqual(updated['data']['IT'][-2:], [{'date': '2026-10-06', 'value': 4.524}, {'date': '2026-10-07', 'value': 4.5}])

    def test_bpstat_selects_daily_ten_year_series(self):
        self.assertEqual(self.fixture('PT'), [('2026-10-01', 4.03), ('2026-10-02', 3.95), ('2026-10-05', 4.0)])
        for dim in (18, 40, 45, 63, 70):
            body = json.loads((FIXTURES / 'PT.json').read_text())
            series = next(s for s in body['extension']['series'] if s['id'] == 12099459)
            next(c for c in series['dimension_category'] if c['dimension_id'] == dim)['category_id'] = -1
            with self.assertRaises(ValueError):
                parse('PT', json.dumps(body).encode())

    def test_bpstat_sparse_missing_zero_negative_and_index_map(self):
        body = json.loads((FIXTURES / 'PT.json').read_text())
        body['value'] = {'15': 0, '16': -0.2}
        for dim in body['dimension'].values():
            dim['category']['index'] = {key: i for i, key in enumerate(dim['category']['index'])}
        self.assertEqual(parse('PT', json.dumps(body).encode()), [('2026-10-01', 0), ('2026-10-02', -0.2)])

    def test_portugal_migration_and_outage_preserve_correct_metadata(self):
        previous = {'data': {'PT': [{'date': '2026-09', 'value': 3.8608}]},
                    'countries': {'PT': {'series': 'FM.M.PT.EUR.FR2.BB.PT10YT_RR.YLD',
                                         'frequency': 'mensuelle', 'source': 'Banque de France — Webstat',
                                         'lastSuccessAt': '2026-10-02T12:00:00+00:00'}}}
        def fail(c):
            if c == 'PT':
                raise PermissionError('HTTP 403')
            return self.fixture(c)
        fallback, failures = collect(previous, fail, NOW)
        self.assertIn('PT', failures)
        self.assertEqual(fallback['data']['PT'], previous['data']['PT'])
        self.assertEqual(fallback['countries']['PT']['frequency'], 'mensuelle')
        self.assertEqual(fallback['countries']['PT']['source'], 'Banque de France — Webstat')
        daily, _ = collect(fallback, self.fixture, NOW)
        self.assertEqual(daily['countries']['PT']['frequency'], 'quotidienne')
        self.assertEqual(daily['countries']['PT']['series'], '12099459')
        self.assertTrue(all(len(p['date']) == 10 for p in daily['data']['PT']))
        outage, _ = collect(daily, fail, NOW)
        self.assertEqual(outage['data']['PT'], daily['data']['PT'])
        self.assertEqual(outage['countries']['PT']['frequency'], 'quotidienne')
        self.assertEqual(outage['countries']['PT']['lastSuccessAt'], daily['countries']['PT']['lastSuccessAt'])


if __name__ == '__main__':
    unittest.main()
