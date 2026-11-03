"""Small synthetic inputs exercise monthly source validation and cache membership."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.run_monthly_count_validation import month_features, cohort_cache, transform, FEATURES


class MonthlySourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tmp_monthly_', dir=Path.cwd())
        self.root = Path(self.temp.name)
        self.wallet = '0'*39+'1'
        self.cohort = self.root/'cohort.parquet'
        cohort_cache(pd.Series([self.wallet]), self.cohort)

    def tearDown(self):
        self.temp.cleanup()

    def source(self, rows):
        path = self.root/'daily.csv'
        pd.DataFrame(rows, columns=['wallet', 'date', 'tx_count']).assign(
            total_in=0., total_out=0.)[['wallet','date','total_in','total_out','tx_count']].to_csv(path,index=False)
        return path

    def test_normalization_and_zero_days_preserve_monthly_denominators(self):
        path = self.source([('0x'+self.wallet, '2022-01-02', 2),
                            (self.wallet, '2022-01-05', 4),
                            (self.wallet, '2022-01-06', 0)])
        row = month_features(path, self.cohort, '202201').iloc[0]
        self.assertEqual(row.wallet, self.wallet)
        self.assertAlmostEqual(row.tx_per_calendar_day, 6/31)
        self.assertAlmostEqual(row.active_day_fraction, 2/31)
        self.assertEqual(row.tx_per_active_day, 3)
        self.assertAlmostEqual(row.span_fraction, 4/31)

    def test_invalid_source_rows_are_not_silently_dropped(self):
        cases = [(self.wallet,'2022-02-01',2),
                 (self.wallet,'2022-01-01',-1),
                 (self.wallet,'2022-01-01',np.inf),
                 (self.wallet,'2022-01-01',np.nan),
                 (self.wallet,'2022-01-01',1.5),
                 ('invalid','2022-01-01',2)]
        for bad in cases:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    month_features(self.source([bad]), self.cohort, '202201')

    def test_duplicate_days_rejected_even_below_calendar_day_count(self):
        path = self.source([(self.wallet,'2022-01-01',2),('0x'+self.wallet,'2022-01-01',4)])
        with self.assertRaisesRegex(ValueError, 'Duplicate wallet-day'):
            month_features(path,self.cohort,'202201')

    def test_changed_cohort_replaces_stale_join_table(self):
        other = '0'*39+'2'
        cohort_cache(pd.Series([other]),self.cohort)
        self.assertEqual(pd.read_parquet(self.cohort).wallet.tolist(),[other])
        path = self.source([(self.wallet,'2022-01-01',2),(other,'2022-01-01',4)])
        self.assertEqual(month_features(path,self.cohort,'202201').wallet.tolist(),[other])

    def test_feature_row_order_is_stable_under_source_reordering(self):
        other='0'*39+'2'
        cohort_cache(pd.Series([other,self.wallet]),self.cohort)
        rows=[(other,'2022-01-01',4),(self.wallet,'2022-01-01',2)]
        first=month_features(self.source(rows),self.cohort,'202201')
        second=month_features(self.source(rows[::-1]),self.cohort,'202201')
        pd.testing.assert_frame_equal(first,second)
        self.assertEqual(first.wallet.tolist(),[self.wallet,other])

    def test_transform_does_not_mutate_training_or_evaluation_frames(self):
        frame=pd.DataFrame(np.ones((3,len(FEATURES))),columns=FEATURES)
        before=frame.copy(deep=True)
        first,second=transform(frame),transform(frame)
        pd.testing.assert_frame_equal(frame,before)
        np.testing.assert_array_equal(first,second)


if __name__ == '__main__':
    unittest.main()
