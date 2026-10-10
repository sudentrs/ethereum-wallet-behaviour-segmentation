"""Small independent checks for chance correction and conditional permutation null."""
import itertools
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from run_temporal_validation_v2 import aggregate_frame, holm, return_null, transition_stats
from build_full_kmeans6_expanded_features import aggregate_daily_features, derive_features


class TemporalValidationTests(unittest.TestCase):
    def test_chance_uses_both_marginals(self):
        a = np.array([0,0,0,1], dtype=np.int8)
        b = np.array([0,0,1,1], dtype=np.int8)
        counts, obs, exp, kappa = transition_stats(a,b,2)
        np.testing.assert_array_equal(counts, [[2,1],[0,1]])
        self.assertEqual(obs,.75)
        self.assertEqual(exp,.5)
        self.assertEqual(kappa,.5)

    def test_zero_denominator_is_not_perfect_kappa(self):
        _,obs,exp,kappa = transition_stats(np.zeros(4,dtype=int),np.zeros(4,dtype=int),2)
        self.assertEqual(obs,1)
        self.assertEqual(exp,1)
        self.assertTrue(np.isnan(kappa))

    def test_stratification_preserves_middle_state_structure(self):
        # Return is guaranteed by s1 -> s2. Global shuffling would invent evidence.
        s0 = np.array([0,0,1,1],dtype=np.int8)
        s1 = np.array([1,1,0,0],dtype=np.int8)
        s2 = s0.copy()
        null,exact = return_null(s0,s1,s2,2,99,np.random.default_rng(42))
        np.testing.assert_array_equal(null,1.)
        self.assertEqual(exact,1.)
        self.assertEqual((1+sum(null>=1.))/100,1.)

    def test_conditional_expectation_against_exhaustive_permutations(self):
        s0 = np.array([0,0,2,0,1],dtype=np.int8)
        s1 = np.array([1,1,1,2,2],dtype=np.int8)
        s2 = np.array([0,2,2,1,0],dtype=np.int8)
        null,exact = return_null(s0,s1,s2,3,999,np.random.default_rng(42))
        outcomes=[]
        for first in itertools.permutations(s2[:3]):
            for second in itertools.permutations(s2[3:]):
                outcomes.append(np.mean(s0==np.array(first+second)))
        self.assertAlmostEqual(exact,np.mean(outcomes))
        self.assertLess(abs(null.mean()-exact),.03)
        self.assertTrue(set(np.round(null,8)) <= set(np.round(outcomes,8)))

    def test_holm_matches_known_example(self):
        np.testing.assert_allclose(holm([.04,.001,.02]),[.04,.003,.04])

    def test_daily_aggregation_known_wallet(self):
        d=pd.DataFrame(dict(wallet=['a','a'],date=['2022-01-01','2022-01-03'],
                            tx_count=[2,4],total_in=[3.,5.],total_out=[1.,1.]))
        row=aggregate_frame(d).iloc[0]
        self.assertEqual(row.active_days_observed,2)
        self.assertEqual(row.activity_span_days,3)
        self.assertEqual(row.total_tx,6)
        self.assertEqual(row.avg_daily_tx_count,3)
        self.assertEqual(row.std_daily_tx_count,1)
        self.assertEqual(row.total_net_flow_sum,6)

    def test_batched_months_equal_original_chunked_builder(self):
        rng=np.random.default_rng(2)
        d=pd.DataFrame(dict(wallet=np.repeat(['a','b','c'],4),
            date=list(pd.date_range('2022-01-29',periods=4).astype(str))*3,
            total_in=rng.uniform(0,100,12),total_out=rng.uniform(0,100,12),
            tx_count=rng.integers(1,10,12)))
        batched=aggregate_frame(d,by_month=True)
        with tempfile.TemporaryDirectory() as tmp:
            for month,part in d.groupby(d.date.str[:7]):
                path=Path(tmp)/'daily.csv'
                part.to_csv(path,index=False)
                agg,_,_=aggregate_daily_features(path,pd.DataFrame({'wallet':['a','b','c']}),3)
                expected=derive_features(agg).sort_values('wallet').reset_index(drop=True)
                actual=batched[batched._month==int(month[-2:])-1].drop(columns='_month').sort_values('wallet').reset_index(drop=True)
                pd.testing.assert_frame_equal(actual,expected,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)


if __name__ == '__main__':
    unittest.main()
