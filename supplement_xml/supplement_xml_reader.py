#
# supplement_xml_reader.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

import os
import pathlib

from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element

from typing import Dict
from typing import List
from typing import Tuple
from typing import Optional
from typing import Generator

from . import supplement_xml


class Header:
    name: str
    name_e: str
    comment: str
    comment_e: str


class SupplementXmlReader:

    file_name: str
    has_xml_file: bool
    def_root: Optional[ElementTree]
    xml_root: Optional[ElementTree]

    def __init__(self, file_name: str, pmx_file_path: str, use_japanese_name: bool) -> None:
        import xml.etree.ElementTree as ETree

        xml_path = os.path.splitext(pmx_file_path)[0] + ".xml"
        self.has_xml_file = os.path.isfile(xml_path)

        default_xml = "default_jp.xml" if use_japanese_name else "default_en.xml"
        base_path = pathlib.Path(__file__).parents[1]
        def_path = os.path.join(base_path, default_xml)
        has_def_file = os.path.isfile(def_path)

        self.file_name = file_name
        self.def_root = ETree.parse(def_path) if has_def_file else None
        self.xml_root = ETree.parse(xml_path) if self.has_xml_file else None

        if self.xml_root is None:
            self.xml_root = self.def_root

    def header(self) -> Optional[Header]:
        if self.xml_root is None:
            return None

        infonode = self.xml_root.find("pmdinfo")
        if infonode is None:
            return None

        header = Header()
        header.name = infonode.findtext("name", self.file_name)
        header.name_e = infonode.findtext("name_e", header.name)
        header.comment = infonode.findtext("comment", "Comment").replace("\n", "\r\n")
        header.comment_e = infonode.findtext("comment_e", "Comment").replace("\n", "\r\n")

        return header

    def bone_dict(self) -> Dict[str, Element]:
        if self.xml_root is None:
            return {}

        list = {}

        bone_root = self.xml_root.find("bones")
        bone_list = bone_root.findall("bone") if bone_root else []

        for bone in bone_list:
            b_name = bone.get("b_name")
            if b_name is not None:
                list[b_name] = bone

        return list

    def material(self) -> Tuple[Dict[int, str], Dict[str, supplement_xml.Material]]:

        xml_mat_index = {}
        xml_mat_list = {}

        if self.xml_root is not None:
            mat_root = self.xml_root.find("materials")
            mat_list = mat_root.findall("material") if mat_root else []

            for xml_index, mat in enumerate(mat_list):
                b_name = mat.get("b_name")
                if b_name is not None:
                    xml_mat_index[xml_index] = b_name
                    xml_mat_list[b_name] = self._material_element_read(mat)

        return (xml_mat_index, xml_mat_list)

    def _material_element_read(self, element: Element):
        obj = supplement_xml.elm_to_obj(element, supplement_xml.Material)
        obj.edge_color = self._find_and_convert(element, 'edge_color', supplement_xml.EdgeColor)
        obj.diffuse = self._find_and_convert(element, 'deffuse', supplement_xml.Diffuse)
        obj.specular = self._find_and_convert(element, 'specular', supplement_xml.Specular)
        obj.ambient = self._find_and_convert(element, 'ambient', supplement_xml.Ambient)
        obj.sphere = self._find_and_convert(element, 'sphere', supplement_xml.Sphere)
        return obj

    def _find_and_convert(self, element: Element, child_name: str, klass):
        child = element.find(child_name)
        if child is None:
            return None
        else:
            return supplement_xml.elm_to_obj(child, klass)

    def morph(self) -> Tuple[Dict[int, str], Dict[str, supplement_xml.Morph]]:

        xml_morph_index = {}
        xml_morph_list = {}

        if self.def_root is not None:
            morph_root = self.def_root.find("morphs")
            morph_l = morph_root.findall("morph") if morph_root else []

            for morph_elm in morph_l:
                morph = supplement_xml.elm_to_obj(morph_elm, supplement_xml.Morph)
                b_name = morph.b_name
                if b_name is not None:
                    xml_morph_list[b_name] = morph

        if self.xml_root is not None:
            morph_root = self.xml_root.find("morphs")
            morph_l = morph_root.findall("morph") if morph_root else []

            for xml_index, morph_elm in enumerate(morph_l):
                morph = supplement_xml.elm_to_obj(morph_elm, supplement_xml.Morph)
                if morph.type == 8:
                    morph.offsets = self.material_morph_offset(morph_elm)

                b_name = morph.b_name
                if b_name is not None:
                    xml_morph_index[xml_index] = b_name
                    xml_morph_list[b_name] = morph

        return (xml_morph_index, xml_morph_list)

    def material_morph_offset(self, elm: Element) -> Generator[supplement_xml.MaterialMorphOffset, None, None]:

        for offset_elm in elm.findall('material_offsets/material_offset'):

            def as_color(child_name, klass):
                child = offset_elm.find(child_name)
                if child is None:
                    return klass()
                else:
                    return supplement_xml.elm_to_obj(child, klass)

            offset = supplement_xml.elm_to_obj(offset_elm, supplement_xml.MaterialMorphOffset)
            offset.diffuse = as_color('mat_diffuse', supplement_xml.RGBADiff)
            offset.speculer = as_color('mat_speculer', supplement_xml.RGBDiff)
            offset.ambient = as_color('mat_ambient', supplement_xml.RGBDiff)
            offset.edge_color = as_color('mat_edge_color', supplement_xml.RGBADiff)
            offset.texture = as_color('mat_texture', supplement_xml.RGBADiff)
            offset.sphere = as_color('mat_sphere', supplement_xml.RGBADiff)
            offset.toon = as_color('mat_toon', supplement_xml.RGBADiff)

            yield offset

    def label(self) -> List[Element]:
        return self._element_list("labels", "label")

    def rigid(self) -> List[Element]:
        return self._element_list("rigid_bodies", "rigid")

    def joint(self) -> List[Element]:
        return self._element_list("constraints", "constraint")

    def _element_list(self, list: str, item: str) -> List[Element]:
        if self.xml_root is None:
            return []
        list_root = self.xml_root.find(list)
        return list_root.findall(item) if list_root else []
