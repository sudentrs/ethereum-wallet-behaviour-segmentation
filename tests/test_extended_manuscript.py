import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.build_extended_manuscript import validate_inputs


class ManuscriptInputTests(unittest.TestCase):
    def test_narrative_rebuild_requires_the_frozen_results(self):
        with tempfile.TemporaryDirectory(prefix='tmp_manuscript_',dir=Path.cwd()) as folder:
            root=Path(folder); path=root/'results.csv';path.write_bytes(b'k,ari\n3,0.9\n')
            expected={'results.csv':hashlib.sha256(path.read_bytes()).hexdigest()}
            validate_inputs(root,expected)
            path.write_bytes(b'k,ari\n3,0.2\n')
            with self.assertRaisesRegex(ValueError,'Result input changed'):
                validate_inputs(root,expected)
            with self.assertRaisesRegex(ValueError,'Result input changed'):
                validate_inputs(root,{'missing.csv':'0'*64})


if __name__=='__main__':unittest.main()
