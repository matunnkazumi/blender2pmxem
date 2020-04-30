#
# validator.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

from . import pmx
from typing import List


def validate_pmx(pmx_data: pmx.Model, use_ja_name: bool) -> List[str]:
    result = []

    if use_ja_name:
        morph_name_list = [morph.Name for morph in pmx_data.Morphs]
        if len(morph_name_list) != len(set(morph_name_list)):
            result.append('Morph Japanese name must be unique in PMX.')

        bone_name_list = [bone.Name for bone in pmx_data.Bones]
        if len(bone_name_list) != len(set(bone_name_list)):
            result.append('Bone Japanese name must be unique in PMX.')
    else:
        morph_name_list = [morph.Name_E for morph in pmx_data.Morphs]
        if len(morph_name_list) != len(set(morph_name_list)):
            result.append('Morph English name must be unique in PMX.')

        bone_name_list = [bone.Name_E for bone in pmx_data.Bones]
        if len(bone_name_list) != len(set(bone_name_list)):
            result.append('Bone English name must be unique in PMX.')

    rigid_name_list = [rigid.Name for rigid in pmx_data.Rigids]
    if len(rigid_name_list) != len(set(rigid_name_list)):
        result.append('Rigid name must be unique in PMX.')

    joint_name_list = [joint.Name for joint in pmx_data.Joints]
    if len(joint_name_list) != len(set(joint_name_list)):
        result.append('Joint name must be unique in PMX.')

    return result


def validate_xml(xml_root) -> List[str]:
    result = []

    morph_b_name_list = [e.get("b_name") for e in xml_root.findall("morphs/morph")]
    if len(morph_b_name_list) != len(set(morph_b_name_list)):
        result.append('Morph name must be unique in XML.')

    bone_name_list = [e.get("name") for e in xml_root.findall("bones/bone")]
    if len(bone_name_list) != len(set(bone_name_list)):
        result.append('Bone name must be unique in XML.')

    rigid_name_list = [e.get("name") for e in xml_root.findall("rigid_bodies/rigid")]
    if len(rigid_name_list) != len(set(rigid_name_list)):
        result.append('Rigid name must be unique in XML.')

    joint_name_list = [e.get("name") for e in xml_root.findall("constraints/constraint")]
    if len(joint_name_list) != len(set(joint_name_list)):
        result.append('Joint name must be unique in XML.')

    return result
