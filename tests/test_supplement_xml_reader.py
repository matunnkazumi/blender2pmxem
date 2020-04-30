import unittest
import os
import shutil
import tempfile
from dataclasses import astuple

from supplement_xml.supplement_xml_reader import SupplementXmlReader


class TestSupplementXmlReader(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_header_no_xml_use_japanese(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)

        reader = SupplementXmlReader(file_name, file_path, True)
        header = reader.header()

        self.assertIsNotNone(header)
        self.assertEqual(header.name, 'モデル名')
        self.assertEqual(header.name_e, 'Model Name')
        self.assertEqual(header.comment, 'コメント')
        self.assertEqual(header.comment_e, 'Comment')

    def test_header_no_xml_use_english(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)

        reader = SupplementXmlReader(file_name, file_path, False)
        header = reader.header()

        self.assertIsNotNone(header)
        self.assertEqual(header.name, 'モデル名')
        self.assertEqual(header.name_e, 'Model Name')
        self.assertEqual(header.comment, 'コメント')
        self.assertEqual(header.comment_e, 'Comment')

    def test_header_xml(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <pmdinfo>
              <name>モデル名 test</name>
              <name_e>Model Name for test</name_e>
              <comment>コメント for test</comment>
              <comment_e>Comment for test</comment_e>
            </pmdinfo>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, False)
        header = reader.header()

        self.assertIsNotNone(header)
        self.assertEqual(header.name, 'モデル名 test')
        self.assertEqual(header.name_e, 'Model Name for test')
        self.assertEqual(header.comment, 'コメント for test')
        self.assertEqual(header.comment_e, 'Comment for test')

    def test_material(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <materials>
            <material b_name="mat1" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル1" name_e="mat 1" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /><deffuse a="1.0" b="0.7098038792610168" g="0.9411764740943909" r="1.0" /><specular b="0.07000000029802322" g="0.07000000029802322" r="0.07000000029802322" /><ambient b="0.23999999463558197" g="0.3199999928474426" r="0.44999998807907104" /></material>
            <material b_name="mat2" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル2" name_e="mat 2" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /><deffuse a="1.0" b="0.7098038792610168" g="0.9411764740943909" r="1.0" /><specular b="0.07000000029802322" g="0.07000000029802322" r="0.07000000029802322" /><ambient b="0.23999999463558197" g="0.3199999928474426" r="0.44999998807907104" /></material>
            <material b_name="mat3" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル3" name_e="mat 3" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /><deffuse a="1.0" b="1.0" g="1.0" r="1.0" /><specular b="1.0" g="0.0" r="0.0" /><ambient b="0.4000000059604645" g="0.4000000059604645" r="0.4000000059604645" /></material>
            </materials>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.material()

        self.assertEqual(index_dict[0], 'mat1')
        self.assertEqual(index_dict[1], 'mat2')
        self.assertEqual(index_dict[2], 'mat3')
        self.assertEqual(element_dict['mat1'].b_name, 'mat1')
        self.assertEqual(element_dict['mat1'].both, 0)
        self.assertEqual(element_dict['mat1'].edge_color.a, 1.0)
        self.assertEqual(element_dict['mat1'].edge_color.r, 0.0)
        self.assertAlmostEqual(element_dict['mat1'].diffuse.r, 1.0)
        self.assertAlmostEqual(element_dict['mat1'].specular.b, 0.07)
        self.assertAlmostEqual(element_dict['mat1'].ambient.g, 0.32)
        self.assertEqual(element_dict['mat2'].b_name, 'mat2')
        self.assertEqual(element_dict['mat2'].both, 0)
        self.assertAlmostEqual(element_dict['mat2'].diffuse.a, 1.0)
        self.assertAlmostEqual(element_dict['mat2'].specular.b, 0.070000000)
        self.assertAlmostEqual(element_dict['mat2'].ambient.g, 0.3199999928474426)
        self.assertEqual(element_dict['mat3'].b_name, 'mat3')
        self.assertEqual(element_dict['mat3'].both, 0)
        self.assertAlmostEqual(element_dict['mat3'].diffuse.a, 1.0)
        self.assertAlmostEqual(element_dict['mat3'].specular.b, 1.0)
        self.assertAlmostEqual(element_dict['mat3'].ambient.r, 0.4)

    def test_material_optional_element(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <materials>
            <material b_name="mat1" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル1" name_e="mat 1" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"></material>
            </materials>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.material()

        self.assertEqual(index_dict[0], 'mat1')
        self.assertIsNone(element_dict['mat1'].edge_color)
        self.assertIsNone(element_dict['mat1'].diffuse)
        self.assertIsNone(element_dict['mat1'].specular)
        self.assertIsNone(element_dict['mat1'].ambient)
        self.assertIsNone(element_dict['mat1'].sphere)

    def test_morph(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <morphs>
            <morph b_name="あ" group="1" name="あ" name_e="A" />
            <morph b_name="い" group="2" name="い" name_e="I" />
            <morph b_name="う" group="3" name="う" name_e="U" />
            <morph b_name="え" group="4" name="え" name_e="E" />
            <morph b_name="お" name="お" name_e="O" />
            <morph b_name="にやり" group="3" name="にやり" name_e="Smirk" />
            <morph b_name="困る" group="1" name="困る" name_e="Troubled" />
            </morphs>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.morph()

        self.assertEqual(index_dict[0], 'あ')
        self.assertEqual(index_dict[1], 'い')
        self.assertEqual(index_dict[2], 'う')
        self.assertEqual(index_dict[3], 'え')
        self.assertEqual(index_dict[4], 'お')
        self.assertEqual(index_dict[5], 'にやり')
        self.assertEqual(index_dict[6], '困る')
        self.assertEqual(element_dict['あ'].b_name, 'あ')
        self.assertEqual(element_dict['い'].b_name, 'い')
        self.assertEqual(element_dict['う'].b_name, 'う')
        self.assertEqual(element_dict['え'].b_name, 'え')
        self.assertEqual(element_dict['お'].b_name, 'お')
        self.assertEqual(element_dict['あ'].group, 1)
        self.assertEqual(element_dict['い'].group, 2)
        self.assertEqual(element_dict['う'].group, 3)
        self.assertEqual(element_dict['え'].group, 4)
        self.assertEqual(element_dict['お'].group, 4)
        self.assertEqual(element_dict['あ'].type, 1)
        self.assertEqual(element_dict['い'].type, 1)
        self.assertEqual(element_dict['う'].type, 1)
        self.assertEqual(element_dict['え'].type, 1)
        self.assertEqual(element_dict['お'].type, 1)
        self.assertEqual(element_dict['困る'].group, 1)
        # デフォルトXML
        self.assertEqual(element_dict['もぐもぐ'].b_name, 'もぐもぐ')

    def test_morph_material_offset(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <morphs>
            <morph b_name="A" group="1" name="A" name_e="A" />
            <morph b_name="B" group="2" name="B" name_e="I" type="8">
            <material_offsets>
            <material_offset edge_size="0.3" effect_type="1" material_name="aaa" power="0.1">
            <mat_diffuse a="1.0" b="3.0" g="2.0" r="1.0" />
            <mat_speculer b="1.0" g="3.0" r="3.0" />
            <mat_ambient b="6.0" g="5.0" r="4.0" />
            <mat_edge_color a="2.0" b="3.0" g="4.0" r="1.0" />
            <mat_texture a="5.0" b="4.0" g="3.0" r="2.0" />
            <mat_sphere a="1.0" b="2.0" g="3.0" r="4.0" />
            <mat_toon a="2.0" b="3.0" g="6.0" r="7.0" />
            </material_offset>
            <material_offset material_name="bbb">
            <mat_diffuse a="1.0" b="0.0" g="0.0" r="0.0" />
            <mat_speculer b="0.0" g="0.0" r="0.0" />
            <mat_ambient b="0.0" g="0.0" r="0.0" />
            <mat_edge_color a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_texture a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_sphere a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_toon a="0.0" b="0.0" g="0.0" r="0.0" />
            </material_offset>
            </material_offsets>
            </morph>
            <morph b_name="C" group="3" name="C" name_e="U" type="8">
            <material_offsets>
            <material_offset edge_size="1.0" effect_type="1" material_name="ccc" power="0.3">
            <mat_diffuse a="1.0" b="0.0" g="0.0" r="0.0" />
            <mat_speculer b="0.0" g="0.0" r="0.0" />
            <mat_ambient b="0.0" g="0.0" r="0.0" />
            <mat_edge_color a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_texture a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_sphere a="0.0" b="0.0" g="0.0" r="0.0" />
            <mat_toon a="0.0" b="0.0" g="0.0" r="0.0" />
            </material_offset>
            <material_offset edge_size="0.5" effect_type="0" material_name="ddd" power="0.4">
            </material_offset>
            <material_offset />
            </material_offsets>
            </morph>
            </morphs>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.morph()

        m_A = element_dict['A']
        m_B = element_dict['B']
        m_C = element_dict['C']

        self.assertEqual(m_A.type, 1)
        self.assertEqual(len(m_A.offsets), 0)

        iter_m_B = iter(m_B.offsets)
        offset = next(iter_m_B)
        self.assertEqual(m_B.type, 8)
        self.assertAlmostEqual(offset.edge_size, 0.3)
        self.assertAlmostEqual(offset.power, 0.1)
        self.assertEqual(offset.effect_type, 1)
        self.assertEqual(offset.material_name, "aaa")
        self.assertEqual(astuple(offset.diffuse), (1.0, 2.0, 3.0, 1.0))
        self.assertEqual(astuple(offset.speculer), (3.0, 3.0, 1.0))
        self.assertEqual(astuple(offset.ambient), (4.0, 5.0, 6.0))
        self.assertEqual(astuple(offset.edge_color), (1.0, 4.0, 3.0, 2.0))
        self.assertEqual(astuple(offset.texture), (2.0, 3.0, 4.0, 5.0))
        self.assertEqual(astuple(offset.sphere), (4.0, 3.0, 2.0, 1.0))
        self.assertEqual(astuple(offset.toon), (7.0, 6.0, 3.0, 2.0))
        offset = next(iter_m_B)
        self.assertAlmostEqual(offset.edge_size, 0)
        self.assertAlmostEqual(offset.power, 0)
        self.assertEqual(offset.effect_type, 0)
        self.assertEqual(offset.material_name, "bbb")
        self.assertEqual(astuple(offset.diffuse), (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(astuple(offset.speculer), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.ambient), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.edge_color), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.texture), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.sphere), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.toon), (0.0, 0.0, 0.0, 0.0))
        with self.assertRaises(StopIteration):
            next(iter_m_B)

        iter_m_C = iter(m_C.offsets)
        offset = next(iter_m_C)
        self.assertEqual(m_C.type, 8)
        self.assertAlmostEqual(offset.edge_size, 1.0)
        self.assertAlmostEqual(offset.power, 0.3)
        self.assertEqual(offset.effect_type, 1)
        self.assertEqual(offset.material_name, "ccc")
        self.assertEqual(astuple(offset.diffuse), (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(astuple(offset.speculer), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.ambient), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.edge_color), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.texture), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.sphere), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.toon), (0.0, 0.0, 0.0, 0.0))
        offset = next(iter_m_C)
        self.assertAlmostEqual(offset.edge_size, 0.5)
        self.assertAlmostEqual(offset.power, 0.4)
        self.assertEqual(offset.effect_type, 0)
        self.assertEqual(offset.material_name, "ddd")
        self.assertEqual(astuple(offset.diffuse), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.speculer), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.ambient), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.edge_color), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.texture), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.sphere), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.toon), (0.0, 0.0, 0.0, 0.0))
        offset = next(iter_m_C)
        self.assertAlmostEqual(offset.edge_size, 0.0)
        self.assertAlmostEqual(offset.power, 0.0)
        self.assertEqual(offset.effect_type, 0)
        self.assertEqual(offset.material_name, None)
        with self.assertRaises(StopIteration):
            next(iter_m_C)

    def test_morph_bone_offset(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <morphs>
            <morph b_name="A" group="1" name="A" name_e="A" />
            <morph b_name="B" group="2" name="B" name_e="I" type="2">
            <bone_offsets>
            <bone_offset bone_name="aaa">
            <bone_move x="0.1" y="0.2" z="0.3" />
            <bone_rotate x="0.4" y="0.5" z="0.6" />
            </bone_offset>
            <bone_offset bone_name="bbb">
            <bone_move x="0.7" y="0.8" z="0.9" />
            <bone_rotate x="1.0" y="1.1" z="1.2" />
            </bone_offset>
            </bone_offsets>
            </morph>
            <morph b_name="C" group="3" name="C" name_e="U" type="2">
            <bone_offsets>
            <bone_offset bone_name="ccc">
            <bone_move x="0.0" y="0.0" z="0.0" />
            <bone_rotate x="0.0" y="0.0" z="0.0" />
            </bone_offset>
            <bone_offset bone_name="ddd">
            </bone_offset>
            </bone_offsets>
            </morph>
            </morphs>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.morph()

        m_A = element_dict['A']
        m_B = element_dict['B']
        m_C = element_dict['C']

        self.assertEqual(m_A.type, 1)
        self.assertEqual(len(m_A.offsets), 0)

        iter_m_B = iter(m_B.offsets)
        offset = next(iter_m_B)
        self.assertEqual(m_B.type, 2)
        self.assertEqual(offset.bone_name, "aaa")
        self.assertEqual(astuple(offset.move), (0.1, 0.2, 0.3))
        self.assertEqual(astuple(offset.rotate), (0.4, 0.5, 0.6))
        offset = next(iter_m_B)
        self.assertEqual(offset.bone_name, "bbb")
        self.assertEqual(astuple(offset.move), (0.7, 0.8, 0.9))
        self.assertEqual(astuple(offset.rotate), (1.0, 1.1, 1.2))
        with self.assertRaises(StopIteration):
            next(iter_m_B)

        iter_m_C = iter(m_C.offsets)
        offset = next(iter_m_C)
        self.assertEqual(m_C.type, 2)
        self.assertEqual(offset.bone_name, "ccc")
        self.assertEqual(astuple(offset.move), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.rotate), (0.0, 0.0, 0.0))
        offset = next(iter_m_C)
        self.assertEqual(offset.bone_name, "ddd")
        self.assertEqual(astuple(offset.move), (0.0, 0.0, 0.0))
        self.assertEqual(astuple(offset.rotate), (0.0, 0.0, 0.0))
        with self.assertRaises(StopIteration):
            next(iter_m_C)

    def test_morph_group_offset(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <morphs>
            <morph b_name="A" group="1" name="A" name_e="A" />
            <morph b_name="B" group="2" name="B" name_e="I" type="0">
            <group_offsets>
            <group_offset morph_name="aaa" power="1.0" />
            <group_offset morph_name="bbb" power="2.0" />
            <group_offset morph_name="ccc" power="3.0" />
            </group_offsets>
            </morph>
            <morph b_name="C" group="3" name="C" name_e="U" type="0">
            <group_offsets>
            <group_offset morph_name="ddd" />
            </group_offsets>
            </morph>
            </morphs>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.morph()

        m_A = element_dict['A']
        m_B = element_dict['B']
        m_C = element_dict['C']

        self.assertEqual(m_A.type, 1)
        self.assertEqual(len(m_A.offsets), 0)

        iter_m_B = iter(m_B.offsets)
        offset = next(iter_m_B)
        self.assertEqual(m_B.type, 0)
        self.assertEqual(offset.morph_name, "aaa")
        self.assertAlmostEqual(offset.power, 1.0)
        offset = next(iter_m_B)
        self.assertEqual(offset.morph_name, "bbb")
        self.assertAlmostEqual(offset.power, 2.0)
        offset = next(iter_m_B)
        self.assertEqual(offset.morph_name, "ccc")
        self.assertAlmostEqual(offset.power, 3.0)
        with self.assertRaises(StopIteration):
            next(iter_m_B)

        iter_m_C = iter(m_C.offsets)
        offset = next(iter_m_C)
        self.assertEqual(m_C.type, 0)
        self.assertEqual(offset.morph_name, "ddd")
        self.assertAlmostEqual(offset.power, 0.0)
        with self.assertRaises(StopIteration):
            next(iter_m_C)

    def test_label(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <labels>
            <label name="Root" name_e="Root" type="1"></label>
            <label name="表情" name_e="Exp" type="1"></label>
            <label name="体" name_e="Body" type="0"></label>
            <label name="足" name_e="Legs" type="0"></label>
            </labels>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        list = reader.label()

        self.assertEqual(len(list), 4)
        self.assertEqual(list[0].get('name'), 'Root')
        self.assertEqual(list[1].get('name'), '表情')
        self.assertEqual(list[2].get('name'), '体')
        self.assertEqual(list[3].get('name'), '足')

    def test_rigid(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <rigid_bodies>
            <rigid attach="ひじ_L" friction="0.5000000" group="0" groups="-1" mass="1.0000000" name="左ひじ" name_e="" pos_dump="0.5000000" restitution="0.0000000" rot_dump="0.5000000" shape="2" type="0"><size a="1.2000000" b="1.5000000" c="0.0000000" /><pos x="5.4000807" y="11.3638115" z="-0.0141793" /><rot x="-0.0000102" y="-0.0000132" z="52.4439307" /></rigid>
            <rigid attach="ひじ_R" friction="0.5000000" group="0" groups="-1" mass="1.0000000" name="右ひじ" name_e="" pos_dump="0.5000000" restitution="0.0000000" rot_dump="0.5000000" shape="2" type="0"><size a="1.2000000" b="1.5000000" c="0.0000000" /><pos x="-5.4000840" y="11.3638115" z="-0.0141801" /><rot x="-0.0000048" y="0.0000062" z="-52.4439410" /></rigid>
            <rigid attach="下半身" friction="0.5000000" group="0" groups="-1" mass="1.0000000" name="下半身" name_e="" pos_dump="0.5000000" restitution="0.0000000" rot_dump="0.5000000" shape="1" type="0"><size a="1.9000000" b="1.4764251" c="1.0000000" /><pos x="-0.0000000" y="10.5438004" z="0.4550781" /><rot x="-10.9509004" y="0.0000000" z="0.0000000" /></rigid>
            <rigid attach="ひざ_L" friction="0.5000000" group="0" groups="-1" mass="1.0000000" name="左ひざ" name_e="" pos_dump="0.5000000" restitution="0.0000000" rot_dump="0.5000000" shape="2" type="0"><size a="1.2000000" b="4.8503203" c="0.0000000" /><pos x="0.8899624" y="3.2874398" z="-0.2498198" /><rot x="-1.1652503" y="-0.0223907" z="1.1009002" /></rigid>
            <rigid attach="ひざ_R" friction="0.5000000" group="0" groups="-1" mass="1.0000000" name="右ひざ" name_e="" pos_dump="0.5000000" restitution="0.0000000" rot_dump="0.5000000" shape="2" type="0"><size a="1.2000000" b="4.8503194" c="0.0000000" /><pos x="-0.8899635" y="3.2874451" z="-0.2498208" /><rot x="-1.1652439" y="0.0223907" z="-1.1009069" /></rigid>
            </rigid_bodies>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        list = reader.rigid()

        self.assertEqual(len(list), 5)
        self.assertEqual(list[0].get('name'), '左ひじ')
        self.assertEqual(list[1].get('name'), '右ひじ')
        self.assertEqual(list[2].get('name'), '下半身')
        self.assertEqual(list[3].get('name'), '左ひざ')
        self.assertEqual(list[4].get('name'), '右ひざ')

    def test_joint(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <constraints>
            <constraint body_A="legQ_L" body_B="左裾1" name="左裾1" name_e=""><pos x="0.3808662" y="9.4287338" z="0.9677922" /><rot x="0.0000000" y="0.0000000" z="0.0000000" /><pos_limit><from x="0.0000000" y="0.0000000" z="0.0000000" /><to x="0.0000000" y="0.0000000" z="0.0000000" /></pos_limit><rot_limit><from x="-3.0000001" y="-3.0000001" z="-10.0000006" /><to x="100.0000005" y="3.0000001" z="10.0000006" /></rot_limit><pos_spring x="0.0000000" y="0.0000000" z="0.0000000" /><rot_spring x="0.0000000" y="0.0000000" z="0.0000000" /></constraint>
            <constraint body_A="legQ_R" body_B="右裾1" name="右裾1" name_e=""><pos x="-0.3808662" y="9.4287338" z="0.9677922" /><rot x="0.0000000" y="0.0000000" z="0.0000000" /><pos_limit><from x="0.0000000" y="0.0000000" z="0.0000000" /><to x="0.0000000" y="0.0000000" z="0.0000000" /></pos_limit><rot_limit><from x="-3.0000001" y="-3.0000001" z="-10.0000006" /><to x="100.0000005" y="3.0000001" z="10.0000006" /></rot_limit><pos_spring x="0.0000000" y="0.0000000" z="0.0000000" /><rot_spring x="0.0000000" y="0.0000000" z="0.0000000" /></constraint>
            <constraint body_A="legQ_L" body_B="左裾2" name="左裾2" name_e=""><pos x="1.0832090" y="9.4287338" z="0.8821672" /><rot x="0.0000000" y="10.0000006" z="0.0000000" /><pos_limit><from x="0.0000000" y="0.0000000" z="0.0000000" /><to x="0.0000000" y="0.0000000" z="0.0000000" /></pos_limit><rot_limit><from x="-3.0000001" y="-3.0000001" z="-10.0000006" /><to x="100.0000005" y="3.0000001" z="10.0000006" /></rot_limit><pos_spring x="0.0000000" y="0.0000000" z="0.0000000" /><rot_spring x="0.0000000" y="0.0000000" z="0.0000000" /></constraint>
            <constraint body_A="legQ_R" body_B="右裾2" name="右裾2" name_e=""><pos x="-1.0832090" y="9.4287338" z="0.8821672" /><rot x="0.0000000" y="-10.0000006" z="0.0000000" /><pos_limit><from x="0.0000000" y="0.0000000" z="0.0000000" /><to x="0.0000000" y="0.0000000" z="0.0000000" /></pos_limit><rot_limit><from x="-3.0000001" y="-3.0000001" z="-10.0000006" /><to x="100.0000005" y="3.0000001" z="10.0000006" /></rot_limit><pos_spring x="0.0000000" y="0.0000000" z="0.0000000" /><rot_spring x="0.0000000" y="0.0000000" z="0.0000000" /></constraint>
            </constraints>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        list = reader.joint()

        self.assertEqual(len(list), 4)
        self.assertEqual(list[0].get('body_A'), 'legQ_L')
        self.assertEqual(list[1].get('body_A'), 'legQ_R')
        self.assertEqual(list[2].get('body_A'), 'legQ_L')
        self.assertEqual(list[3].get('body_A'), 'legQ_R')


if __name__ == '__main__':
    unittest.main()
