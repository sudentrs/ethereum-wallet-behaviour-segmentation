"""Reference-statistic checks for the new referee controls."""
import unittest
import numpy as np
import pandas as pd
from scripts.run_referee_network import null_counts, baseline_labels
from scripts.run_referee_robustness import matched_jaccard, holm, block_shuffle


class RefereeControls(unittest.TestCase):
    def test_accelerated_null_matches_independent_reference(self):
        labels=np.array([[0,0,1,1,2,2],[1,0,1,0,1,0]],dtype=np.int8)
        src=np.array([0,0,1,2,3,4,5,5],dtype=np.int32)
        dst=np.array([0,1,2,3,4,5,0,5],dtype=np.int32)
        groups=np.array([0,2,4,1,3,5],dtype=np.int32)
        offsets=np.array([0,3,6],dtype=np.int32);seeds=np.array([492,493,494],dtype=np.int64)
        expected=[]
        for seed in seeds:
            rng=np.random.RandomState(seed);p=np.arange(6)
            for lo,hi in zip(offsets[:-1],offsets[1:]):
                for i in range(hi-lo-1,0,-1):
                    j=rng.randint(i+1);a,b=groups[lo+i],groups[lo+j];p[a],p[b]=p[b],p[a]
            expected.append([sum(row[p[s]]==row[p[t]] for s,t in zip(src,dst)) for row in labels])
        np.testing.assert_array_equal(null_counts(labels,src,dst,groups,offsets,seeds),expected)

    def test_singleton_strata_and_self_transfers_are_invariant(self):
        y=np.array([[0,1,2]],dtype=np.int8);s=np.array([0,1,2],dtype=np.int32)
        c=null_counts(y,s,s,s,np.arange(4,dtype=np.int32),np.array([1,2],dtype=np.int64))
        np.testing.assert_array_equal(c,np.full((2,1),3))

    def test_matching_is_label_permutation_invariant(self):
        a=np.array([0,0,1,1,2,2]);b=np.array([2,2,0,0,1,1])
        self.assertEqual(matched_jaccard(a,b,3),{0:1.,1:1.,2:1.})

    def test_holm_reference_example(self):
        np.testing.assert_allclose(holm([.01,.04,.03]),[.03,.06,.06])

    def test_rules_have_explicit_boundary_and_ties(self):
        d=pd.DataFrame(dict(total_tx=[1,1,2,3,3,4],activity_span_days=[30,31,365,1,31,31],active_days_observed=[2,23,24,1,24,25]))
        total,rule,cuts=baseline_labels(d)
        np.testing.assert_array_equal(rule,[0,1,2,0,2,2])
        self.assertEqual(total[0],total[1]);self.assertEqual(total[3],total[4])

    def test_block_null_preserves_daily_histogram_including_short_block(self):
        x=np.arange(3*365).reshape(3,365)
        for block in [1,7,30,365]:
            y=block_shuffle(x,block,np.random.default_rng(492))
            np.testing.assert_array_equal(np.sort(y,axis=1),x)
            if block==365:
                np.testing.assert_allclose(np.abs(np.fft.rfft(y,axis=1)),np.abs(np.fft.rfft(x,axis=1)),atol=1e-9)

if __name__=='__main__':unittest.main()
