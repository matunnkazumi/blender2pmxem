import unittest
import os
import shutil
import tempfile

from supplement_xml_reader import SupplementXmlReader


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
            <material b_name="mat1" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル1" name_e="mat 1" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /></material>
            <material b_name="mat2" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル2" name_e="mat 2" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /></material>
            <material b_name="mat3" both="0" drop_shadow="1" edge_size="1.0" ground_shadow="1" name="マテリアル3" name_e="mat 3" on_edge="1" on_shadow="1" toon="0" use_systemtoon="1"><edge_color a="1.0" b="0.0" g="0.0" r="0.0" /></material>
            </materials>
            </ns0:pmxstatus>
            """
            fp.write(test_content)

        reader = SupplementXmlReader(file_name, file_path, True)
        index_dict, element_dict = reader.material()

        self.assertEqual(index_dict[0], 'mat1')
        self.assertEqual(index_dict[1], 'mat2')
        self.assertEqual(index_dict[2], 'mat3')
        self.assertEqual(element_dict['mat1'].get('b_name'), 'mat1')
        self.assertEqual(element_dict['mat2'].get('b_name'), 'mat2')
        self.assertEqual(element_dict['mat3'].get('b_name'), 'mat3')

    def test_morph(self):
        file_name = 'test.pmx'
        file_path = os.path.join(self.test_dir, file_name)
        xml_file_path = os.path.join(self.test_dir, 'test.xml')

        with open(xml_file_path, 'w') as fp:
            test_content = """
            <ns0:pmxstatus xmlns:ns0="local" xml:lang="jp">
            <morphs>
            <morph b_name="あ" group="3" name="あ" name_e="A" />
            <morph b_name="い" group="3" name="い" name_e="I" />
            <morph b_name="う" group="3" name="う" name_e="U" />
            <morph b_name="え" group="3" name="え" name_e="E" />
            <morph b_name="お" group="3" name="お" name_e="O" />
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
        self.assertEqual(element_dict['あ'].get('b_name'), 'あ')
        self.assertEqual(element_dict['い'].get('b_name'), 'い')
        self.assertEqual(element_dict['う'].get('b_name'), 'う')
        self.assertEqual(element_dict['え'].get('b_name'), 'え')
        self.assertEqual(element_dict['お'].get('b_name'), 'お')
        # デフォルトXML
        self.assertEqual(element_dict['もぐもぐ'].get('b_name'), 'もぐもぐ')

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

    def test_intentional_failure(self):
        self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
