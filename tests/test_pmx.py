import unittest
from pathlib import Path

from pmx import pmx


class TestPmx(unittest.TestCase):

    def test_Model(self):
        model = pmx.Model()
        self.assertIsNotNone(model)

    def test_load_model(self):
        test_pmx = Path(__file__).parent / 'data' / 'test_01.pmx'

        model = pmx.Model()
        with test_pmx.open(mode="rb") as f:
            model.Load(f)

        self.assertEqual(len(model.Vertices), 14)
        self.assertEqual(len(model.Faces), 12*3)
        self.assertEqual(len(model.Textures), 0)
        self.assertEqual(len(model.Materials), 1)
        self.assertEqual(len(model.Bones), 1)
        self.assertEqual(len(model.Morphs), 1)
        self.assertEqual(len(model.DisplayFrames), 3)
        self.assertEqual(len(model.Rigids), 1)
        self.assertEqual(len(model.Joints), 2)
        self.assertEqual(len(model.SoftBodies), 0)
