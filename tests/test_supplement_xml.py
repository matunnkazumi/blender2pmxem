import unittest
import xml.etree.ElementTree as etree

from typing import Optional

from supplement_xml.supplement_xml import elm_to_obj
from supplement_xml.supplement_xml import obj_to_elm


class Test1:
    aaa: str
    bbb: int
    ccc: float
    dddd = 0


class Test2:
    aaa: str = 'test2'
    bbb: int = 1
    ccc: float = 0.1
    ddd: Test1


class Test3:
    aaa: Optional[str]
    bbb: Optional[int]
    ccc: Optional[float]


class TestSupplementXmlReader(unittest.TestCase):

    def test_read_xml_attribute(self):
        elm = etree.Element('test', attrib={'aaa': 'test', 'bbb': '10', 'ccc': '1.1'})
        obj = elm_to_obj(elm, Test1)

        self.assertEqual(obj.aaa, 'test')
        self.assertEqual(obj.bbb, 10)
        self.assertEqual(obj.ccc, 1.1)

    def test_read_default_value(self):
        elm = etree.Element('test')
        obj = elm_to_obj(elm, Test2)

        self.assertEqual(obj.aaa, 'test2')
        self.assertEqual(obj.bbb, 1)
        self.assertEqual(obj.ccc, 0.1)

    def test_read_xml_attribute_no_annotated(self):
        elm = etree.Element('test', attrib={'ddd': 'test'})
        obj = elm_to_obj(elm, Test1)

        self.assertEqual(obj.dddd, 0)

    def test_read_optional_exist(self):
        elm = etree.Element('test', attrib={'aaa': 'test', 'bbb': '10', 'ccc': '1.1'})
        obj = elm_to_obj(elm, Test3)

        self.assertEqual(obj.aaa, 'test')
        self.assertEqual(obj.bbb, 10)
        self.assertEqual(obj.ccc, 1.1)

    def test_read_optional_not_exist(self):
        elm = etree.Element('test')
        obj = elm_to_obj(elm, Test3)

        self.assertIsNone(obj.aaa)
        self.assertIsNone(obj.bbb)
        self.assertIsNone(obj.ccc)

    def test_write(self):
        elm = etree.Element('test')
        obj = Test1()
        obj.aaa = 'test'
        obj.bbb = 100
        obj.ccc = 1.1

        obj_to_elm(obj, elm)

        self.assertEqual(elm.get('aaa'), 'test')
        self.assertEqual(elm.get('bbb'), '100')
        self.assertEqual(elm.get('ccc'), '1.1')


if __name__ == '__main__':
    unittest.main()
