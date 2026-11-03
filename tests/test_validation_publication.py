import unittest
import numpy as np
import pandas as pd
from scripts.finalize_year_end_validation import validate_network
from scripts.run_monthly_count_validation import return_null


class PublicationTests(unittest.TestCase):
    def table(self):
        return pd.DataFrame([(202200+m,k,seed,.0001,.0084) for m in range(1,13)
            for k,seed in [(2,492),(3,492),(4,492),(5,492),(6,492),(3,493),(3,494)]],
            columns=['month','k','label_seed','p_raw','p_holm_84'])

    def test_complete_family_passes(self):
        validate_network(self.table(),{'complete':True})

    def test_partial_or_duplicated_tests_cannot_be_published(self):
        table=self.table()
        for bad in [table.iloc[:-1],pd.concat([table.iloc[:-1],table.iloc[:1]])]:
            with self.assertRaises(ValueError):
                validate_network(bad,{'complete':True})
        with self.assertRaises(ValueError):
            validate_network(table,{'complete':False})

    def test_incorrect_correction_is_rejected(self):
        table=self.table()
        table['p_holm_84']=.0012
        with self.assertRaises(AssertionError):
            validate_network(table,{'complete':True})

    def test_binary_switcher_return_null_is_structurally_constant(self):
        middle=np.array([0,0,0,1,1,1])
        start=1-middle
        future=np.array([1,0,1,0,1,0])
        null,expected=return_null(start,middle,future,2,99,np.random.default_rng(492))
        observed=np.mean(start==future)
        np.testing.assert_allclose(null,observed)
        self.assertAlmostEqual(expected,observed)


if __name__=='__main__':
    unittest.main()
