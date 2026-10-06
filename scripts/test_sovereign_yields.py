import unittest
from datetime import datetime, timezone
from pathlib import Path
from sovereign_yields import SOURCES, collect, parse, validated

NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)
FIXTURES = Path(__file__).parent / 'fixtures'


class CollectorTests(unittest.TestCase):
    def fixture(self, c):
        return parse(c, (FIXTURES / (c + ('.html' if c == 'GR' else '.csv'))).read_bytes())

    def test_real_official_formats(self):
        expected = {'FR': 4.899, 'IT': 4.3772, 'PT': 3.8608, 'GR': 4.53}
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
        self.assertEqual(result['countries']['IT']['frequency'], 'mensuelle')


if __name__ == '__main__':
    unittest.main()
