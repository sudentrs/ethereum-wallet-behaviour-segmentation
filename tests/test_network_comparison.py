import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.run_year_end_network_comparison import sample_update, compare_null, stream_month, RUNS
from scripts.apply_network_holm_correction import holm


class NetworkComparisonTests(unittest.TestCase):
    def test_priority_sampling_independent_of_chunk_boundaries(self):
        src=np.arange(100,dtype=np.int32)
        dst=src[::-1]
        full=sample_update(None,src,dst,np.random.default_rng(492),17)
        rng=np.random.default_rng(492)
        split=sample_update(None,src[:43],dst[:43],rng,17)
        split=sample_update(split,src[43:],dst[43:],rng,17)
        self.assertEqual(set(full[1]),set(split[1]))
        self.assertEqual(len(np.unique(full[1])),17)

    def test_common_permutations_and_fixed_graph(self):
        labels=np.array([[0,0,1,1],[0,0,1,1]])
        src=np.array([0,0,2,2,1,3]); dst=np.array([0,1,2,3,0,2])
        observed,mean,std,p=compare_null(labels,src,dst,99,492)
        self.assertTrue(np.all(observed==1))
        self.assertEqual(mean[0],mean[1])
        self.assertEqual(std[0],std[1])
        self.assertEqual(p[0],p[1])
        self.assertTrue(np.all(p>=.01))
        self.assertTrue(np.all(np.isfinite(std)))

    def test_stream_normalizes_filters_and_keeps_repeated_transfers(self):
        with tempfile.TemporaryDirectory(prefix='tmp_network_',dir=Path.cwd()) as folder:
            folder=Path(folder)
            a,b,c=[f'{i:040x}' for i in (1,2,3)]
            path=folder/'month.tsv'
            pd.DataFrame({'sender':['0x'+a,a,b,c],
                          'recipient':[b,b,b,a]}).to_csv(path,sep='\t',index=False)
            labels=np.array([[0,1] for _ in RUNS],dtype=np.int8)
            raw,eligible,sample,adj=stream_month(path,pd.Series([a,b]),labels,20,492,folder/'spill')
            self.assertEqual((raw,eligible),(4,3))
            self.assertEqual(len(sample[1]),3)
            for matrix in adj:
                self.assertEqual(matrix.sum(),3)
                self.assertEqual(matrix[0,1],2)
                self.assertEqual(matrix[1,1],1)

    def test_global_holm_family_includes_all_84_tests(self):
        adjusted=holm(np.full(84,.001))
        np.testing.assert_allclose(adjusted,.084)

    def test_compiled_statistics_match_reference_permutations_exactly(self):
        rng=np.random.default_rng(11)
        labels=np.vstack([rng.integers(0,k,60) for k,_ in RUNS])
        src,dst=rng.integers(0,60,size=(2,200))
        fast=compare_null(labels,src,dst,99,492)
        slow=compare_null(labels,src,dst,99,492,accelerated=False)
        for actual,expected in zip(fast,slow):
            np.testing.assert_array_equal(actual,expected)


if __name__=='__main__':
    unittest.main()
