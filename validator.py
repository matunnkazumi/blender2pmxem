#
# validator.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

from . import pmx
from typing import List


def validate_pmx(pmx_data: pmx.Model) -> List[str]:
    result = []

    bone_name_list = [bone.Name for bone in pmx_data.Bones]
    if len(bone_name_list) != len(set(bone_name_list)):
        result.append('Bone name must be unique.')

    rigid_name_list = [rigid.Name for rigid in pmx_data.Rigids]
    if len(rigid_name_list) != len(set(rigid_name_list)):
        result.append('Rigid name must be unique.')

    joint_name_list = [joint.Name for joint in pmx_data.Joints]
    if len(joint_name_list) != len(set(joint_name_list)):
        result.append('Joint name must be unique.')

    return result
