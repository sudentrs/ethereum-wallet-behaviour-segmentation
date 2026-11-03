"""Independent numerical checks for the corrected-cohort signal branch."""
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from scripts.run_year_end_signal_validation import features, timing_metrics, holm, agreement, build_signals

SCRATCH = Path(__file__).resolve().parents[1]/'tmp'
SCRATCH.mkdir(exist_ok=True)


class SignalValidationTests(unittest.TestCase):
    def test_constant_signals_have_no_ac_spectrum(self):
        x = np.array([[0]*365,[4]*365],dtype=np.uint32)
        values, positive, totals = features(x)
        self.assertEqual(positive.tolist(),[False,False])
        np.testing.assert_array_equal(totals,[0,1460])
        np.testing.assert_array_equal(values[:,6:],0)
        self.assertEqual(values[0,2],1)
        self.assertEqual(values[1,1],1)

    def test_exact_fourier_bin_and_independent_time_statistics(self):
        # A nonnegative signal with a single exact Fourier bin after log1p.
        day = np.arange(365)
        x = np.expm1(2 + .5*np.cos(2*np.pi*10*day/365))[None,:]
        values,positive,_ = features(x)
        self.assertTrue(positive[0])
        self.assertAlmostEqual(values[0,12],0,places=10)
        self.assertAlmostEqual(values[0,11],1,places=10)
        self.assertAlmostEqual(values[0,7],1,places=10)
        self.assertAlmostEqual(values[0,6:9].sum(),1,places=10)
        self.assertAlmostEqual(values[0,5],float(x.std()/x.mean()),places=12)

    def test_impulse_has_uniform_non_dc_power(self):
        x=np.zeros((1,365));x[0,140]=11
        v,positive,total=features(x)
        self.assertTrue(positive[0])
        self.assertEqual(total[0],11)
        self.assertAlmostEqual(v[0,11],1/182,places=12)
        self.assertAlmostEqual(v[0,12],np.log2(182),places=12)
        self.assertEqual(v[0,1],1/365)
        self.assertEqual(v[0,2],224/365)
        self.assertEqual(v[0,3],2/364)

    def test_null_preserves_counts_and_matches_direct_spectral_summaries(self):
        rng=np.random.default_rng(77)
        x=rng.poisson(.3,size=(10,365))
        perm=np.take_along_axis(x,np.argsort(rng.random(x.shape),axis=1),axis=1)
        np.testing.assert_array_equal(np.sort(x),np.sort(perm))
        v,_,_=features(x)
        np.testing.assert_allclose(timing_metrics(x),np.column_stack([v[:,6],v[:,11],-v[:,12]]))

    def test_comparison_is_label_invariant_and_holm_is_joint(self):
        r=agreement([0,0,1,1],[1,1,0,0])
        self.assertEqual(r,dict(ari=1.,nmi=1.,matched_agreement=1.))
        np.testing.assert_allclose(holm([.04,.001,.02]),[.04,.003,.04])

    def test_monthly_reconstruction_preserves_wallet_order_and_calendar_positions(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temp:
            root=Path(temp); daily=root/'daily'; daily.mkdir(); cache=root/'cache';cache.mkdir()
            for month in range(1,13):
                rows=[['a'*40,f'2022-{month:02d}-01',0,0,month],
                      ['b'*40,f'2022-{month:02d}-01',0,0,2*month],
                      ['c'*40,f'2022-{month:02d}-01',0,0,999]]
                pd.DataFrame(rows,columns=['wallet','date','total_in','total_out','tx_count']).to_csv(
                    daily/f'wallet_daily_clean_2022{month:02d}.csv',index=False)
            signal=build_signals(SimpleNamespace(cache=cache,daily=daily),pd.Series(['b'*40,'a'*40]),{'test':'calendar'})
            self.assertEqual(signal.shape,(2,365))
            np.testing.assert_array_equal(signal.sum(axis=1),[156,78])
            self.assertEqual(np.count_nonzero(signal),24)
            self.assertEqual(signal[0,334],24)  # December 1, independent day index.
            self.assertEqual(signal[1,59],3)    # March 1 in non-leap 2022.
            self.assertEqual(signal[1,60],0)
            # Release the Windows mapping before TemporaryDirectory removes it.
            signal._mmap.close()

    def test_duplicate_wallet_day_is_rejected_before_assignment(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temp:
            root=Path(temp);daily=root/'daily';daily.mkdir();cache=root/'cache';cache.mkdir()
            rows=[['a'*40,'2022-01-01',0,0,1],['a'*40,'2022-01-01',0,0,2]]
            pd.DataFrame(rows,columns=['wallet','date','total_in','total_out','tx_count']).to_csv(
                daily/'wallet_daily_clean_202201.csv',index=False)
            with self.assertRaises(AssertionError):
                build_signals(SimpleNamespace(cache=cache,daily=daily),pd.Series(['a'*40]),{'test':'duplicates'})


if __name__=='__main__':
    unittest.main()
