import unittest
from tests.utils import fast_session_patches

class FastPatchedTestCase(unittest.TestCase):
    def setUp(self):
        self._ctx = fast_session_patches()
        self._ctx.__enter__()
    
    def tearDown(self):
        self._ctx.__exit__(None, None, None)