import unittest
from pathlib import Path
import lzma

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

    def test_vertex_length_type2(self):
        test_pmx = Path(__file__).parent / 'data' / 'test_02_vertex_64009.pmx.xz'

        model = pmx.Model()
        with lzma.open(test_pmx, mode="rb") as f:
            model.Load(f)

        self.assertEqual(len(model.Vertices), 64010)
        self.assertEqual(len(model.Faces), 127008*3)

        vert_first = model.Vertices[0]
        self.assertEqual(vert_first.Type, 0)
        self.assertEqual(vert_first.Bones, [0])
        self.assertEqual(vert_first.Weights, [])
        self.assertAlmostEqual(vert_first.EdgeSize, 1.0)
        vert_last = model.Vertices[-1]
        self.assertEqual(vert_last.Type, 0)
        self.assertEqual(vert_last.Bones, [0])
        self.assertEqual(vert_last.Weights, [])
        self.assertAlmostEqual(vert_last.EdgeSize, 1.0)

        self.assertEqual(model.Faces[0], 28288)
        self.assertEqual(model.Faces[1], 28291)
        self.assertEqual(model.Faces[2], 28289)
        self.assertEqual(model.Faces[-3], 15923)
        self.assertEqual(model.Faces[-2], 64003)
        self.assertEqual(model.Faces[-1], 64000)

    def test_vertex_length_type4(self):
        test_pmx = Path(__file__).parent / 'data' / 'test_02_vertex_66409.pmx.xz'

        model = pmx.Model()
        with lzma.open(test_pmx, mode="rb") as f:
            model.Load(f)

        self.assertEqual(len(model.Vertices), 66049)
        self.assertEqual(len(model.Faces), 131072*3)

        vert_first = model.Vertices[0]
        self.assertEqual(vert_first.Type, 0)
        self.assertEqual(vert_first.Bones, [0])
        self.assertEqual(vert_first.Weights, [])
        self.assertAlmostEqual(vert_first.EdgeSize, 1.0)
        vert_last = model.Vertices[-1]
        self.assertEqual(vert_last.Type, 0)
        self.assertEqual(vert_last.Bones, [0])
        self.assertEqual(vert_last.Weights, [])
        self.assertAlmostEqual(vert_last.EdgeSize, 1.0)

        self.assertEqual(model.Faces[0], 29185)
        self.assertEqual(model.Faces[1], 29188)
        self.assertEqual(model.Faces[2], 29186)
        self.assertEqual(model.Faces[-3], 4412)
        self.assertEqual(model.Faces[-2], 66043)
        self.assertEqual(model.Faces[-1], 66040)
