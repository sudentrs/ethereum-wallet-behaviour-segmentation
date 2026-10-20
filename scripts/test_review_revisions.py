"""Focused checks for the monthly representation and historical-cache fixes."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/validation"))
from eoa_contract_contamination_check import load_cache
from run_monthly_count_validation import month_features, transform
from build_full_eoa_temporal_signal_streaming import spectral_features
from run_conditioned_network_review import measures


class ReviewTests(unittest.TestCase):
    def test_zero_power_has_no_dominant_frequency(self):
        result=spectral_features(np.ones(365),"tx")
        self.assertEqual(result["tx_dominant_frequency"],0)
        self.assertEqual(result["tx_dominant_period_days"],0)

    def test_full_mixing_detects_complementary_roles(self):
        labels=np.array([0,1])
        # Every transfer crosses roles: same-role concentration is zero,
        # but knowledge of sender role fully predicts recipient role.
        result=measures(labels,np.array([0,1]),np.array([1,0]),2)
        self.assertEqual(result[0],0)
        self.assertAlmostEqual(result[1],1)

    def test_historical_cache_does_not_reuse_latest(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cache.csv"
            pd.DataFrame([dict(address="0xabc",block="latest",account_type="eoa"),
                          dict(address="0xabc",block="0x10",account_type="contract")]).to_csv(p,index=False)
            self.assertEqual(load_cache(p,block="0x10")["0xabc"]["account_type"],"contract")
            self.assertEqual(load_cache(p,block="0x20"),{})

    def test_month_features_include_zero_calendar_days(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"daily.csv"
            pd.DataFrame(dict(wallet=["a","a","outside"],date=["2022-02-01","2022-02-03","2022-02-01"],
                              tx_count=[2,4,999])).to_csv(p,index=False)
            f=month_features(p,{"a"},"202202",1)
            self.assertEqual(len(f),1)
            self.assertAlmostEqual(f.active_day_fraction.iloc[0],2/28)
            self.assertAlmostEqual(f.tx_per_calendar_day.iloc[0],6/28)
            self.assertAlmostEqual(f.tx_per_active_day.iloc[0],3)
            self.assertAlmostEqual(f.span_fraction.iloc[0],3/28)
            self.assertAlmostEqual(f.peak_count_share.iloc[0],4/6)
            self.assertTrue(np.isfinite(transform(f)).all())

    def test_out_of_window_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"daily.csv"
            pd.DataFrame(dict(wallet=["a"],date=["2022-03-01"],tx_count=[1])).to_csv(p,index=False)
            with self.assertRaises(ValueError):month_features(p,{"a"},"202202",100)


if __name__=="__main__":unittest.main()
