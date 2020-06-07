import unittest

from pmx import pmx

class TestPmx(unittest.TestCase):

    def test_Model(self):
        model = pmx.Model()
        self.assertIsNotNone(model)
