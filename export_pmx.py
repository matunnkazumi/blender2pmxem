import bpy
import mathutils as Math
import os
from math import radians
from dataclasses import astuple

from typing import Dict
from typing import List
from typing import Tuple
from typing import Optional
from typing import Any
from typing import Union
from typing import Generator
from typing import Callable

from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from bpy.types import Object
from bpy.types import Material
from bpy.types import BlendDataObjects

from .pmx import pmx
from . import object_applymodifier
from . import global_variable
from . import validator
from .supplement_xml import supplement_xml_reader
from .supplement_xml.supplement_xml import Material as XMLMaterial
from .supplement_xml.supplement_xml import Morph as XMLMorph
from .supplement_xml.supplement_xml import MorphOffsets as XMLMorphOffsets
from .supplement_xml.supplement_xml import GroupMorphOffset as XMLGroupMorphOffset
from .supplement_xml.supplement_xml import MaterialMorphOffset as XMLMaterialMorphOffset
from .supplement_xml.supplement_xml import BoneMorphOffset as XMLBoneMorphOffset
from .supplement_xml.supplement_xml import Rotate as XMLRotate

# global_variable
GV = global_variable.Init()

# DEBUG = True


# def Echo(data):
#     if DEBUG:
#         print(data)

GlobalMatrix = Math.Matrix(
    ([1, 0, 0, 0],
     [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0.2]))


def GT(vec, mat):  # GlobalTransformation
    v = vec.copy()
    v.resize_4d()

    w = GlobalMatrix @ mat @ v
    w = w / w.w
    w.resize_3d()
    return w


def GT_normal(vec, mat):  # GlobalTransformation
    v = vec.copy()
    v.resize_4d()

    w = GlobalMatrix @ mat.to_3x3().to_4x4() @ v
    w.resize_3d()
    w.normalize()
    return w


# Find Object using Material
def exist_object_using_material(material: Material, target_armature: Object, objects: BlendDataObjects) -> bool:

    for mat_obj in objects:
        if mat_obj.users == 0:
            continue
        if mat_obj.type != 'MESH':
            continue

        # Get Weight Bone
        mesh_parent = mat_obj.find_armature()

        if mesh_parent != target_armature:
            continue

        tmp_mat = mat_obj.data.materials.get(material.name)
        if tmp_mat is not None:
            # Find Material
            return True

    # Not Found
    return False


BoneStackEntry = Union[Tuple[str, str], Tuple[str, str, Optional[str]]]


def create_bone_stack(arm_obj, xml_bone_list: Dict[str, Any], use_japanese_name: bool) -> List[BoneStackEntry]:
    bone_stack = []  # type: List[BoneStackEntry]

    for bone in arm_obj.data.edit_bones:
        if (arm_obj.name, bone.name) in bone_stack:
            continue

        bone_stack.append((arm_obj.name, bone.name))

        for const in arm_obj.pose.bones[bone.name].constraints:
            if const.type == 'IK':
                has_child = False

                for child_bone in bone.children:
                    if child_bone.use_connect:
                        has_child = True
                        break

                if not has_child:
                    tip_name_jp, tip_name_en = tip_bone_names(bone.name)
                    search_name = tip_name_jp if use_japanese_name else tip_name_en
                    bone_stack.append((arm_obj.name, search_name, bone.name))

                if (const.target.name, const.subtarget) in bone_stack:
                    bone_stack.remove((const.target.name, const.subtarget))

                bone_stack.append((const.target.name, const.subtarget))

    if xml_bone_list:
        # insertion-order is preserved from python 3.7
        b_names = list(xml_bone_list.keys())

        def get_index(e: BoneStackEntry):
            bone_name = e[1]
            if bone_name in b_names:
                return b_names.index(bone_name)
            else:
                return float('inf')

        return sorted(bone_stack, key=get_index)
    else:
        return bone_stack


def create_bone_index(bone_stack: List[BoneStackEntry]) -> Dict[str, int]:
    return {bone_name[1]: index for index, bone_name in enumerate(bone_stack)}


def tip_bone_names(bone_name: str) -> Tuple[str, str]:
    tip_name_jp = ""
    tip_name_en = ""
    b_name = bone_name[:-2]
    lr = bone_name[-2:]
    find_lr = lr in GV.TextLR

    if b_name in GV.TextAnkle and find_lr:
        tip_name_jp = GV.GetLR_JP[lr] + GV.GetAnkle_JP[b_name]
        tip_name_en = GV.GetAnkle_EN[b_name] + lr

    elif find_lr:
        tip_name_jp = GV.GetLR_JP[lr] + b_name + GV.Tip_JP
        tip_name_en = b_name + GV.Tip_EN + lr

    else:
        tip_name_jp = bone_name + GV.Tip_JP
        tip_name_en = bone_name + GV.Tip_EN

    return tip_name_jp, tip_name_en


def create_PMMaterial(mat: Material,
                      xml_mat_list: Dict[str, XMLMaterial],
                      tex_dic: Dict[str, int],
                      filepath: str) -> pmx.PMMaterial:

    principled = PrincipledBSDFWrapper(mat, is_readonly=True)
    pmx_mat = pmx.PMMaterial()
    pmx_mat.Name = mat.name
    pmx_mat.Name_E = mat.name

    xml_deffuse = None
    xml_specular = None
    xml_ambient = None

    r, g, b, *rem = principled.base_color
    a = principled.alpha if not rem else rem[0]

    # Load XML Status
    if pmx_mat.Name in xml_mat_list.keys():
        temp_mat = xml_mat_list[pmx_mat.Name]
        pmx_mat.Name = temp_mat.name if temp_mat.name is not None else mat.name
        pmx_mat.Name_E = temp_mat.name_e if temp_mat.name_e is not None else pmx_mat.Name
        pmx_mat.UseSystemToon = temp_mat.use_systemtoon

        if pmx_mat.UseSystemToon == 1:
            pmx_mat.ToonIndex = int(temp_mat.toon) if temp_mat.toon is not None else 0

        else:
            tex_path = temp_mat.toon if temp_mat.toon is not None else "toon01.bmp"

            if tex_path == "" or tex_path == "-1":
                pmx_mat.ToonIndex = -1

            else:
                pmx_mat.ToonIndex = tex_dic.setdefault(tex_path, len(tex_dic))

        if temp_mat.memo:
            pmx_mat.Comment = temp_mat.memo.replace("\n", "\r\n")

        pmx_mat.Both = temp_mat.both
        pmx_mat.GroundShadow = temp_mat.ground_shadow
        pmx_mat.DropShadow = temp_mat.drop_shadow
        pmx_mat.OnShadow = temp_mat.on_shadow

        pmx_mat.OnEdge = temp_mat.on_edge
        pmx_mat.EdgeSize = temp_mat.edge_size

        edge_c = temp_mat.edge_color
        if edge_c is not None:
            pmx_mat.EdgeColor = Math.Vector((edge_c.r, edge_c.g, edge_c.b, edge_c.a))
        else:
            pmx_mat.EdgeColor = Math.Vector((0.0, 0.0, 0.0, 1.0))

        deffuse_elm = temp_mat.diffuse
        if deffuse_elm is not None:
            c = (deffuse_elm.r if deffuse_elm.r is not None else r,
                 deffuse_elm.g if deffuse_elm.g is not None else g,
                 deffuse_elm.b if deffuse_elm.b is not None else b,
                 deffuse_elm.a if deffuse_elm.a is not None else a)
            xml_deffuse = Math.Vector(c)

        specular_elm = temp_mat.specular
        if specular_elm is not None:
            xml_specular = Math.Vector((specular_elm.r,
                                        specular_elm.g,
                                        specular_elm.b))

        ambient_elm = temp_mat.ambient
        if ambient_elm is not None:
            xml_ambient = Math.Vector((ambient_elm.r,
                                       ambient_elm.g,
                                       ambient_elm.b))

        pmx_mat.Power = temp_mat.power

        sphere_elm = temp_mat.sphere
        if sphere_elm is not None:
            path = sphere_elm.path
            pmx_mat.SphereIndex = tex_dic.setdefault(path, len(tex_dic))
            pmx_mat.SphereType = sphere_elm.type

    pmx_mat.Deffuse = xml_deffuse if xml_deffuse is not None else Math.Vector((r, g, b, a))

    pmx_mat.Specular = xml_specular if xml_specular is not None else Math.Vector((0.0, 0.0, 0.0))
    pmx_mat.Ambient = xml_ambient if xml_ambient is not None else pmx_mat.Deffuse.xyz * 0.4

    pmx_mat.FaceLength = 0

    tex_base_path = bpy.path.abspath("//")

    if tex_base_path == "":
        tex_base_path = os.path.dirname(filepath)

    texture = principled.base_color_texture
    if texture and texture.image:
        image_filepath = texture.image.filepath

        tex_abs_path = bpy.path.abspath(image_filepath)
        tex_path = bpy.path.relpath(tex_abs_path, tex_base_path)
        tex_path = tex_path.replace("//", "", 1)

        pmx_mat.TextureIndex = tex_dic.setdefault(tex_path, len(tex_dic))

    return pmx_mat


def as_vector(dc) -> Math.Vector:
    return Math.Vector(astuple(dc))


MorphOffsetConverter = Callable[[XMLMorphOffsets], Generator[pmx.PMMorphOffset, None, None]]


def create_PMMorph(xml_morph: XMLMorph, type: int, converter: MorphOffsetConverter) -> pmx.PMMorph:

    pm_morph = pmx.PMMorph()
    pm_morph.Name = xml_morph.name
    pm_morph.Name_E = xml_morph.name_e
    pm_morph.Panel = xml_morph.group
    pm_morph.Type = type
    pm_morph.Offsets = [o for o in converter(xml_morph.offsets)]
    return pm_morph


def create_PMMorph_dict(xml_morph_list: Dict[str, XMLMorph],
                        type: int,
                        converter: MorphOffsetConverter) -> Dict[str, pmx.PMMorph]:

    def filter_map() -> Generator[Tuple[str, pmx.PMMorph], None, None]:
        for k, v in xml_morph_list.items():
            if v.type == type:
                yield k, create_PMMorph(v, type, converter)

    return {k: v for k, v in filter_map()}


def create_group_PMMorphOffset(xml_morph_offset: XMLGroupMorphOffset, morph_index: int) -> pmx.PMMorphOffset:
    offset = pmx.PMMorphOffset()
    offset.Index = morph_index
    offset.Power = xml_morph_offset.power
    return offset


def create_group_PMMorph(xml_morph: XMLMorph, index_dict: Dict[str, int]) -> pmx.PMMorph:

    def converter(offsets) -> Generator[pmx.PMMorphOffset, None, None]:
        for offset in offsets:
            for name, index in index_dict.items():
                if offset.morph_name == name:
                    yield create_group_PMMorphOffset(offset, index)
                    break

    return create_PMMorph(xml_morph, 0, converter)


def pmx_euler2quat(eular: XMLRotate) -> Math.Vector:
    radian = (radians(eular.x), radians(eular.y), radians(eular.z))
    rotate_euler = Math.Euler(radian, "ZXY")
    rotate_quat = rotate_euler.to_quaternion()
    return Math.Vector((rotate_quat.x, rotate_quat.y, rotate_quat.z, rotate_quat.w))


def create_bone_PMMorphOffset(xml_morph_offset: XMLBoneMorphOffset, bone_index: int) -> pmx.PMMorphOffset:
    offset = pmx.PMMorphOffset()
    offset.Index = bone_index
    offset.Move = as_vector(xml_morph_offset.move)
    offset.Rotate = pmx_euler2quat(xml_morph_offset.rotate)
    return offset


def create_bone_morph_dict(xml_morph_list: Dict[str, XMLMorph],
                           bone_name_list: List[str]) -> Dict[str, pmx.PMMorph]:

    def converter(offsets) -> Generator[pmx.PMMorphOffset, None, None]:
        for offset in offsets:
            for i, name in enumerate(bone_name_list):
                if offset.bone_name == name:
                    yield create_bone_PMMorphOffset(offset, i)
                    break

    return create_PMMorph_dict(xml_morph_list, 2, converter)


def create_material_PMMorphOffset(xml_morph_offset: XMLMaterialMorphOffset, mat_index: int) -> pmx.PMMorphOffset:
    offset = pmx.PMMorphOffset()
    offset.Index = mat_index
    offset.MatEffectType = xml_morph_offset.effect_type
    offset.MatDiffuse = as_vector(xml_morph_offset.diffuse)
    offset.MatSpeculer = as_vector(xml_morph_offset.speculer)
    offset.MatPower = xml_morph_offset.power
    offset.MatAmbient = as_vector(xml_morph_offset.ambient)
    offset.MatEdgeColor = as_vector(xml_morph_offset.edge_color)
    offset.MatEdgeSize = xml_morph_offset.edge_size
    offset.MatTexture = as_vector(xml_morph_offset.texture)
    offset.MatSphere = as_vector(xml_morph_offset.sphere)
    offset.MatToon = as_vector(xml_morph_offset.toon)
    return offset


def create_material_morph_dict(xml_morph_list: Dict[str, XMLMorph],
                               mat_name_list: List[str]) -> Dict[str, pmx.PMMorph]:

    def converter(offsets) -> Generator[pmx.PMMorphOffset, None, None]:
        for offset in offsets:
            if offset.material_name is not None:
                for i, name in enumerate(mat_name_list):
                    if offset.material_name == name:
                        yield create_material_PMMorphOffset(offset, i)
                        break
            else:
                yield create_material_PMMorphOffset(offset, -1)

    return create_PMMorph_dict(xml_morph_list, 8, converter)


def sort_and_resolve_PMMorph(xml_morph_list: Dict[str, XMLMorph],
                             pm_morph_dict: Dict[str, pmx.PMMorph]) -> Tuple[List[pmx.PMMorph], Dict[str, int]]:

    def output_morph_names_in_xml() -> Generator[str, None, None]:
        for name, morph in xml_morph_list.items():
            if morph.type == 0:  # Group Morph
                yield name
            else:
                if name in pm_morph_dict:
                    yield name

    index_dict = {k: i for i, k in enumerate(output_morph_names_in_xml())}

    def morphs_in_xml() -> Generator[pmx.PMMorph, None, None]:
        for name in output_morph_names_in_xml():
            xml_morph = xml_morph_list[name]
            if xml_morph.type == 0:
                yield create_group_PMMorph(xml_morph, index_dict)
            else:
                yield pm_morph_dict[name]

    output_morph_names_not_in_xml = [name for name in pm_morph_dict.keys() if name not in index_dict]

    def morphs_not_in_xml() -> Generator[pmx.PMMorph, None, None]:
        for name, morph in pm_morph_dict.items():
            if name in output_morph_names_not_in_xml:
                yield morph

    morph_list = list(morphs_in_xml()) + list(morphs_not_in_xml())
    name_list = list(output_morph_names_in_xml()) + output_morph_names_not_in_xml
    name_index_dict = {k: i for i, k in enumerate(name_list)}
    return morph_list, name_index_dict


def create_PMJoint(joint, rigid_index: Dict[str, int]) -> pmx.PMJoint:

    pmx_joint = pmx.PMJoint()

    pmx_joint.Name = joint.get("name")
    pmx_joint.Name_E = joint.get("name_e")

    body_A = joint.get("body_A")
    pmx_joint.Parent = rigid_index.get(body_A, -1) if body_A else -1
    body_B = joint.get("body_B")
    pmx_joint.Child = rigid_index.get(body_B, -1) if body_B else -1
    pmx_joint.Position = get_Vector(joint.find("pos"))
    pmx_joint.Rotate = get_Vector_Rad(joint.find("rot"))

    joint_pos_limit = joint.find("pos_limit")
    pmx_joint.PosLowerLimit = get_Vector(joint_pos_limit.find("from"))
    pmx_joint.PosUpperLimit = get_Vector(joint_pos_limit.find("to"))

    joint_rot_limit = joint.find("rot_limit")
    pmx_joint.RotLowerLimit = get_Vector_Rad(joint_rot_limit.find("from"))
    pmx_joint.RotUpperLimit = get_Vector_Rad(joint_rot_limit.find("to"))

    pmx_joint.PosSpring = get_Vector(joint.find("pos_spring"))
    pmx_joint.RotSpring = get_Vector(joint.find("rot_spring"))

    return pmx_joint


def write_pmx_data(context, filepath="",
                   encode_type='OPT_Utf-16',
                   use_mesh_modifiers=False,
                   use_custom_normals=False,
                   ):

    prefs = context.preferences.addons[GV.FolderName].preferences
    use_japanese_name = prefs.use_japanese_name

    GV.SetStartTime()

    with open(filepath, "wb") as f:

        pmx_data = None
        pmx_data = pmx.Model()

        #
        # XML
        #
        file_name = bpy.path.basename(filepath)
        xml_reader = supplement_xml_reader.SupplementXmlReader(file_name, filepath, use_japanese_name)

        if xml_reader.xml_root is not None:
            validate_result = validator.validate_xml(xml_reader.xml_root)
            if validate_result:
                msg = '\n'.join(validate_result)
                bpy.ops.b2pmxem.multiline_message('INVOKE_DEFAULT',
                                                  type='ERROR',
                                                  lines=msg)
                return {'CANCELLED'}

        #
        # Header
        #
        header = xml_reader.header()
        if header is not None:
            # Name
            pmx_data.Name = header.name
            pmx_data.Name_E = header.name_e

            # Comment
            pmx_data.Comment = header.comment
            pmx_data.Comment_E = header.comment_e

        # Fixed Stats
        # print("Export to " + encode_type)
        pmx_data.Status.Encode = 0 if encode_type == 'OPT_Utf-16' else 1
        pmx_data.Status.Magic = 1  # Pmx
        pmx_data.Status.Version = 2.0  # Pmx

        #
        # Bone Read
        #
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # read xml
        xml_bone_list = xml_reader.bone_dict()

        # make index
        arm_obj = bpy.context.active_object
        bone_stack = create_bone_stack(arm_obj, xml_bone_list, use_japanese_name)
        bone_index = create_bone_index(bone_stack)

        # output bone
        ik_stack = []
        for bone_name in bone_stack:
            pmx_bone = pmx.PMBone()
            # arm_obj = bpy.data.objects[bone_name[0]]
            arm_mat = arm_obj.matrix_world
            bone = arm_obj.data.edit_bones.get(bone_name[1], None)

            # Tail Bone
            if bone is None:
                bone = arm_obj.data.edit_bones.get(bone_name[2], None)  # get parent
                tip_name_jp, tip_name_en = tip_bone_names(bone.name)
                pmx_bone.Name = tip_name_jp
                pmx_bone.Name_E = tip_name_en

                search_name = tip_name_jp if use_japanese_name else tip_name_en
                if search_name in xml_bone_list.keys():
                    pmx_bone = load_xml_bone(search_name, xml_bone_list, bone_index)

                pmx_bone.Position = GT(bone.tail, arm_mat)
                pmx_bone.Parent = bone_index.get(bone.name, -1)
                pmx_bone.ToConnectType = 1  # [@:Offset 1:Bone]
                pmx_bone.Rotatable = 0
                pmx_bone.Movable = 0
                pmx_bone.Visible = 0
                pmx_bone.Operational = 0
                pmx_bone.ChildIndex = -1

                pmx_data.Bones.append(pmx_bone)

            # Normal Bone
            else:
                if bone.name in xml_bone_list.keys():
                    pmx_bone = load_xml_bone(bone.name, xml_bone_list, bone_index)

                else:
                    bone_name_jp = ""
                    lr = bone.name[-2:]

                    if lr in GV.TextLR:
                        bone_name_jp = GV.GetLR_JP[lr] + bone.name[:-2]

                    else:
                        bone_name_jp = bone.name

                    pmx_bone.Name = bone_name_jp
                    pmx_bone.Name_E = bone.name

                bonehead = GT(bone.head, arm_mat)
                bonetail = GT(bone.tail, arm_mat)

                pmx_bone.Position = bonehead

                if bone.parent is None:
                    pmx_bone.Parent = -1
                else:
                    pmx_bone.Parent = bone_index.get(bone.parent.name, -1)

                pmx_bone.ToConnectType = 0
                pmx_bone.TailPosition = bonetail - bonehead

                for child_bone in bone.children:
                    if child_bone.use_connect:
                        pmx_bone.ToConnectType = 1
                        pmx_bone.ChildIndex = bone_index.get(child_bone.name, -1)
                        break

                pb = arm_obj.pose.bones[bone.name]

                # params
                # rotate
                lr = pb.lock_rotation
                if lr[0] and lr[1] and lr[2]:
                    pmx_bone.Rotatable = 0

                # move
                ll = pb.lock_location
                if ll[0] and ll[1] and ll[2]:
                    pmx_bone.Movable = 0

                # visible
                # if bone.hide :
                #     pmx_bone.Visible = 0
                #     pmx_bone.ToConnectType = 1
                #     pmx_bone.ChildIndex  = -1

                # Constraint
                for const in pb.constraints:
                    # Copy Move
                    if const.type == 'COPY_LOCATION':
                        pmx_bone.AdditionalMovement = 1

                        if const.invert_x and const.invert_y and const.invert_z:
                            pmx_bone.AdditionalPower = -const.influence
                        else:
                            pmx_bone.AdditionalPower = const.influence

                        pmx_bone.AdditionalBoneIndex = bone_index.get(const.subtarget, -1)

                    # Copy Rot
                    elif const.type == 'COPY_ROTATION':
                        pmx_bone.AdditionalRotation = 1

                        if const.invert_x and const.invert_y and const.invert_z:
                            pmx_bone.AdditionalPower = -const.influence
                        else:
                            pmx_bone.AdditionalPower = const.influence

                        pmx_bone.AdditionalBoneIndex = bone_index.get(const.subtarget, -1)

                    # Fixed Axis
                    elif const.type == 'LIMIT_ROTATION':
                        if const.use_limit_x and const.use_limit_z:
                            pmx_bone.UseFixedAxis = 1
                    # IK
                    elif const.type == 'IK':
                        ik = pmx.PMIK()

                        if pmx_bone.ToConnectType == 0:
                            # Make Tail
                            tip_name_jp, tip_name_en = tip_bone_names(bone.name)
                            search_name = tip_name_jp if use_japanese_name else tip_name_en
                            pmx_bone.ToConnectType = 1
                            pmx_bone.ChildIndex = bone_index.get(search_name, -1)

                        ik.TargetIndex = pmx_bone.ChildIndex
                        ik_bone = const.target.pose.bones[const.subtarget]

                        if "IKLoops" in ik_bone:
                            ik.Loops = int(ik_bone["IKLoops"])
                        else:
                            ik.Loops = 10

                        if "IKLimit" in ik_bone:
                            ik.Limit = float(ik_bone["IKLimit"])
                        else:
                            ik.Limit = 2.0

                        ik.Member = []
                        cursor = arm_obj.pose.bones[bone.name]

                        for i in range(const.chain_count):
                            ik_member = pmx.PMIKLink()
                            ik_member.Index = bone_index.get(cursor.name, -1)

                            if cursor.lock_ik_x \
                               or cursor.lock_ik_y \
                               or cursor.lock_ik_z \
                               or cursor.use_ik_limit_x \
                               or cursor.use_ik_limit_y \
                               or cursor.use_ik_limit_z:

                                ik_member.UseLimit = 1
                                ik_member.UpperLimit = Math.Vector((0, 0, 0))
                                ik_member.LowerLimit = Math.Vector((0, 0, 0))

                                # X Axis
                                if cursor.lock_ik_x:
                                    ik_member.UpperLimit.x = 0.0
                                    ik_member.LowerLimit.x = 0.0

                                elif cursor.use_ik_limit_x:
                                    ik_member.UpperLimit.x = cursor.ik_max_x
                                    ik_member.LowerLimit.x = cursor.ik_min_x

                                else:
                                    ik_member.UpperLimit.x = 180
                                    ik_member.LowerLimit.x = -180

                                # Y Axis
                                if cursor.lock_ik_y:
                                    ik_member.UpperLimit.z = 0.0
                                    ik_member.LowerLimit.z = 0.0

                                elif cursor.use_ik_limit_y:
                                    ik_member.UpperLimit.y = cursor.ik_max_y
                                    ik_member.LowerLimit.y = cursor.ik_min_y

                                else:
                                    ik_member.UpperLimit.y = 180
                                    ik_member.LowerLimit.y = -180

                                # Z Axis
                                if cursor.lock_ik_z:
                                    ik_member.UpperLimit.y = 0.0
                                    ik_member.LowerLimit.y = 0.0

                                elif cursor.use_ik_limit_z:
                                    ik_member.UpperLimit.z = cursor.ik_max_z
                                    ik_member.LowerLimit.z = cursor.ik_min_z

                                else:
                                    ik_member.UpperLimit.z = 180
                                    ik_member.LowerLimit.z = -180

                            else:
                                ik_member.UseLimit = 0

                            ik.Member.append(ik_member)
                            cursor = cursor.parent

                        ik_stack.append((const, ik))

                if pmx_bone.UseFixedAxis == 1:
                    pmx_bone.FixedAxis = bonetail - bonehead
                    pmx_bone.FixedAxis.normalize()

                if pmx_bone.UseLocalAxis == 1:
                    if pmx_bone.LocalAxisX == Math.Vector((0, 0, 0)) and pmx_bone.LocalAxisZ == Math.Vector((0, 0, 0)):
                        pmx_bone.LocalAxisX = bonetail - bonehead
                        pmx_bone.LocalAxisX.normalize()
                        pmx_bone.LocalAxisZ = Math.Vector((0, 0, -1))

                    # pmx_bone.LocalAxisX = bone.x_axis
                    # pmx_bone.LocalAxisY = bone.y_axis
                    # pmx_bone.LocalAxisZ = bone.z_axis

                if pmx_bone.ExternalBone == 1:
                    pmx_bone.ExternalBoneIndex = 0

                pmx_data.Bones.append(pmx_bone)

        # IK Set
        for temp_ik in ik_stack:
            ik_index = bone_index.get(temp_ik[0].subtarget, -1)
            if ik_index < 0:
                continue

            pmx_data.Bones[ik_index].IK = temp_ik[1]
            pmx_data.Bones[ik_index].UseIK = 1

        # Temporary Bone
        if len(pmx_data.Bones) == 0:
            pmx_data.Bones.append(pmx.PMBone())

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        # Material Read
        xml_mat_index, xml_mat_list = xml_reader.material()

        faceTemp = {}
        tex_dic = {}
        mat_list = {}
        mat_name_List = []

        for mat in bpy.data.materials:
            if mat.users == 0:
                continue
            if mat.name.startswith(GV.SolidfyName):
                continue

            # Find Object using Material
            found = exist_object_using_material(mat, arm_obj, bpy.data.objects)
            if not found:
                continue

            pmx_mat = create_PMMaterial(mat, xml_mat_list, tex_dic, filepath)

            faceTemp[mat.name] = []
            mat_list[mat.name] = pmx_mat

        xml_mat_index_keys = list(xml_mat_index.keys())
        xml_mat_index_keys.sort()

        if xml_mat_index_keys is not None:
            for mat_i in xml_mat_index_keys:
                mat_name = xml_mat_index[mat_i]

                if mat_name in mat_list.keys():
                    pmx_data.Materials.append(mat_list[mat_name])
                    mat_name_List.append(mat_name)

        t_key = list(mat_list.keys())
        t_key.sort()

        for mat_name in t_key:
            if mat_name not in xml_mat_list.keys():
                pmx_data.Materials.append(mat_list[mat_name])
                mat_name_List.append(mat_name)

        # Texture
        # print("Get Texture")
        for i in range(len(tex_dic)):
            pmx_tex = pmx.PMTexture()
            pmx_data.Textures.append(pmx_tex)

        for tex, tex_index in tex_dic.items():
            pmx_data.Textures[tex_index].Path = tex

        # Face
        morph_list = {}

        # read default_xml data
        xml_morph_list = xml_reader.morph()

        # Vertex
        # print("Get Vertex")
        base_vert_index = 0  # start position
        vert_uv_dic = {}    # vertUV <-> faceUV
        copy_vert = {}

        NG_object_list = []
        OK_normal_list = []

        apply_mod = object_applymodifier.Init()

        for mesh_obj in bpy.data.objects:
            # Get Mesh Object
            if mesh_obj.users == 0:
                continue
            if mesh_obj.type != 'MESH':
                continue

            mesh = mesh_obj.data
            mesh_mat = mesh_obj.matrix_world
            mesh_scale = mesh_obj.matrix_world.to_scale()
            mesh_inv = mesh_scale.x * mesh_scale.y * mesh_scale.z > 0

            # Get Weight Bone
            mesh_parent = mesh_obj.find_armature()

            if mesh_parent != arm_obj:
                continue

            # Doesn't have Material
            if len(mesh_obj.data.materials) == 0:
                NG_object_list.append(mesh_obj.name)
                continue

            # Apply Modifiers
            if use_mesh_modifiers:
                try:
                    mesh = apply_mod.Get_Apply_Mesh(mesh_obj)
                except object_applymodifier.ShapeVertexError as e:
                    bpy.ops.b2pmxem.message(
                        'INVOKE_DEFAULT',
                        type='ERROR',
                        line1="Failed to create some shape keys.",
                        line2="maybe cause is merge vertex by Mirror modifier.",
                        use_console=True
                    )
                    mesh = e.data

            # Re-calc Normals
            mesh.calc_normals()

            # Custom Normals
            normals = {}
            if use_custom_normals and hasattr(mesh, "has_custom_normals"):
                if mesh.has_custom_normals and mesh.use_auto_smooth:
                    OK_normal_list.append(mesh_obj.name)

                    mesh.calc_normals_split()

                    for loop in mesh.loops:
                        normals.setdefault(loop.vertex_index, loop.normal)

            # Get Vertex Position & Weight
            for index, vert in enumerate(mesh.vertices):
                pmx_vert = pmx.PMVertex()
                pmx_vert.Position = GT(vert.co, mesh_mat)
                pmx_vert.Normal = GT_normal(normals.get(index, vert.normal), mesh_mat)

                pmx_vert.Type = 0
                pmx_vert.Bones = [0]
                pmx_vert.UV = Math.Vector((-1.0, -1.0))
                temp_weight = []

                for group_data in vert.groups.values():
                    if group_data.weight == 0:
                        continue

                    if len(mesh_obj.vertex_groups) > group_data.group:
                        bone_name = mesh_obj.vertex_groups[group_data.group].name
                        bone_id = bone_index.get(bone_name, -1)
                        if bone_id < 0:
                            continue

                        temp_weight.append((bone_id, group_data.weight))

                weight_count = len(temp_weight)

                # BDEF1
                if weight_count == 1:
                    pmx_vert.Bones[0] = temp_weight[0][0]

                # BDEF2
                elif weight_count == 2:
                    pmx_vert.Type = 1
                    pmx_vert.Bones = [0, 0]
                    pmx_vert.Weights = [1.0]
                    pmx_vert.Bones[0] = temp_weight[0][0]
                    pmx_vert.Bones[1] = temp_weight[1][0]
                    pmx_vert.Weights[0] = temp_weight[0][1] / (temp_weight[0][1] + temp_weight[1][1])

                # BDEF4
                elif weight_count > 2:
                    pmx_vert.Type = 2
                    pmx_vert.Bones = [0, 0, 0, 0]
                    pmx_vert.Weights = [0.0, 0.0, 0.0, 0.0]

                    for bone, weight in temp_weight:
                        t_bone = bone
                        t_weight = weight

                        for i in range(4):
                            if pmx_vert.Weights[i] < t_weight:
                                b = pmx_vert.Bones[i]
                                w = pmx_vert.Weights[i]
                                pmx_vert.Bones[i] = t_bone
                                pmx_vert.Weights[i] = t_weight
                                t_bone = b
                                t_weight = w

                    total_weight = pmx_vert.Weights[0] + pmx_vert.Weights[1] + pmx_vert.Weights[2] + pmx_vert.Weights[3]
                    pmx_vert.Weights = [w / total_weight for w in pmx_vert.Weights]

                # Todo pmx_vert.Type = 3

                # pmx_vert.EdgeSize
                # pmx_vert.AppendUV
                pmx_data.Vertices.append(pmx_vert)

            # Get Face & UV
            uv_data = None
            add_vertex_count = 0
            if len(mesh.uv_layers) > 0:
                # mesh.uv_textures.active_index = 0
                uv_data = mesh.uv_layers.active.data[:]

            # Polygonal > Triangle
            faceList = []
            for face in mesh.polygons:
                loop = mesh.loops[face.loop_start:face.loop_start + face.loop_total]
                n = face.loop_total - 1

                for i in range(n // 2):
                    faceList.append((face, (loop[i], loop[i + 1], loop[n - i])))

                    if(i + 1 != n - i - 1):
                        faceList.append((face, (loop[n - i], loop[i + 1], loop[n - i - 1])))

            # UV split
            for face, loops in faceList:
                v = []
                if uv_data is None:
                    for loop in loops:
                        v.append(loop.vertex_index + base_vert_index)
                else:
                    for loop in loops:
                        temp_index = loop.vertex_index + base_vert_index
                        target_uv = uv_data[loop.index].uv
                        vert_key = (temp_index, target_uv[0], target_uv[1])

                        if vert_key in vert_uv_dic.keys():
                            pass

                        # Vertex update
                        elif pmx_data.Vertices[temp_index].UV == Math.Vector((-1.0, -1.0)):
                            pmx_data.Vertices[temp_index].UV = Math.Vector((target_uv[0], 1.0 - target_uv[1]))
                            vert_uv_dic[vert_key] = temp_index

                        # Vertex added
                        else:
                            new_vert = pmx.PMVertex()

                            new_vert.Position = pmx_data.Vertices[temp_index].Position
                            new_vert.Normal = pmx_data.Vertices[temp_index].Normal
                            new_vert.Type = pmx_data.Vertices[temp_index].Type
                            new_vert.Bones = pmx_data.Vertices[temp_index].Bones
                            new_vert.Weights = pmx_data.Vertices[temp_index].Weights

                            new_index = len(pmx_data.Vertices)
                            pmx_data.Vertices.append(new_vert)
                            add_vertex_count += 1

                            copy_vert.setdefault(temp_index, [])
                            copy_vert[temp_index].append(new_index)

                            # Vertex update
                            pmx_data.Vertices[new_index].UV = Math.Vector((target_uv[0], 1.0 - target_uv[1]))
                            vert_uv_dic[vert_key] = new_index

                        v.append(vert_uv_dic[vert_key])

                # Add Face
                if mesh_inv:
                    faceTemp[mesh.materials[face.material_index].name].append(v[0])
                    faceTemp[mesh.materials[face.material_index].name].append(v[2])
                    faceTemp[mesh.materials[face.material_index].name].append(v[1])
                else:
                    faceTemp[mesh.materials[face.material_index].name].append(v[0])
                    faceTemp[mesh.materials[face.material_index].name].append(v[1])
                    faceTemp[mesh.materials[face.material_index].name].append(v[2])

            # Shape Key
            face_key = mesh.shape_keys

            if face_key is not None:
                base_key = face_key.reference_key

                for block in face_key.key_blocks:
                    if block.name == base_key.name:
                        continue

                    pmd_morph = morph_list.get(block.name, None)

                    if pmd_morph is None:
                        pmd_morph = pmx.PMMorph()
                        pmd_morph.Type = 1  # Vertex Morph

                        xml_morph = xml_morph_list.get(block.name, None)

                        if xml_morph is None:
                            pmd_morph.Name = block.name
                            pmd_morph.Name_E = block.name
                            pmd_morph.Panel = 4  # Other

                        else:
                            pmd_morph.Name = xml_morph.name if xml_morph.name is not None else block.name
                            pmd_morph.Name_E = xml_morph.name_e if xml_morph.name_e is not None else block.name
                            pmd_morph.Panel = xml_morph.group

                    # calculate relative morph position
                    morph_index = 0
                    for base_v, morph_v in zip(base_key.data, block.data):
                        if base_v.co != morph_v.co:
                            v = pmx.PMMorphOffset()
                            v.Index = morph_index + base_vert_index
                            v.Move = GT(morph_v.co, mesh_mat) - GT(base_v.co, mesh_mat)
                            pmd_morph.Offsets.append(v)

                            if v.Index in copy_vert.keys():
                                for i in copy_vert[v.Index]:
                                    v2 = pmx.PMMorphOffset()
                                    v2.Index = i
                                    v2.Move = v.Move
                                    pmd_morph.Offsets.append(v2)

                        morph_index += 1

                    morph_list[block.name] = pmd_morph

            base_vert_index += (len(mesh.vertices) + add_vertex_count)

            # remove modifier applied mesh
            if use_mesh_modifiers:
                apply_mod.Remove()

        apply_mod.finish()

        # print NG_object_list
        if len(NG_object_list):
            print("Doesn't have Material:")
            for data in NG_object_list:
                print("   --> %s" % data)

        # print OK_normal_list
        if len(OK_normal_list):
            print("Exported using custom normals:")
            for data in OK_normal_list:
                print("   --> %s" % data)

        # Set Face
        # print("Get Face")
        for i, mat_name in enumerate(mat_name_List):
            pmx_mat = pmx_data.Materials[i]
            pmx_mat.FaceLength = len(faceTemp[mat_name])

            for face in faceTemp[mat_name]:
                pmx_data.Faces.append(face)

        # Set Morph

        # Bone Moprh
        bone_morph_dict = create_bone_morph_dict(xml_morph_list, bone_index)
        morph_list.update(bone_morph_dict)

        # Material Morph
        material_morph_dict = create_material_morph_dict(xml_morph_list, mat_name_List)
        morph_list.update(material_morph_dict)

        # Group Morph and set to PMX
        pmx_data.Morphs, morph_tag_index = sort_and_resolve_PMMorph(xml_morph_list, morph_list)

        # Label
        # print("Get Label")
        if xml_reader.has_xml_file:
            label_list = xml_reader.label()

            for label in label_list:
                pmx_label = pmx.PMDisplayFrame()
                pmx_label.Name = label.get("name", "label")
                pmx_label.Name_E = label.get("name_e", pmx_label.Name)
                pmx_label.Type = int(label.get("type", "0"))
                pmx_label.Members = []

                for member in label.findall("tab"):
                    # Bone Label
                    if member.get("type", "") == "bone":
                        find_bone = bone_index.get(member.get("name"), -1)

                        if find_bone != -1:
                            pmx_label.Members.append([0, find_bone])
                    # Morph Label
                    else:
                        find_morph = morph_tag_index.get(member.get("name"), -1)

                        if find_morph != -1:
                            pmx_label.Members.append([1, find_morph])

                pmx_data.DisplayFrames.append(pmx_label)

        # No files
        else:
            pmx_label0 = pmx.PMDisplayFrame()
            pmx_label0.Name = "Root"
            pmx_label0.Name_E = "Root"
            pmx_label0.Type = 1
            pmx_label0.Members = [[0, 0]]

            pmx_data.DisplayFrames.append(pmx_label0)

            pmx_label1 = pmx.PMDisplayFrame()
            pmx_label1.Name = "\u8868\u60C5"
            pmx_label1.Name_E = "Exp"
            pmx_label1.Type = 1
            pmx_label1.Members = []

            for _index in range(len(pmx_data.Morphs)):
                pmx_label1.Members.append([1, _index])

            pmx_data.DisplayFrames.append(pmx_label1)

            pmx_label2 = pmx.PMDisplayFrame()
            pmx_label2.Name = "\u9AA8"
            pmx_label2.Name_E = "Bone"
            pmx_label2.Type = 0
            pmx_label2.Members = []

            for _index in range(len(pmx_data.Bones)):
                pmx_label2.Members.append([0, _index])

            pmx_data.DisplayFrames.append(pmx_label2)

        # Rigid
        # print("Get Rigid")
        rigid_index = {}  # type: Dict[str, int]
        if xml_reader.has_xml_file:
            rigid_list = xml_reader.rigid()

            for index, rigid in enumerate(rigid_list):
                rigid_index[rigid.get("name")] = index

                pmx_rigid = pmx.PMRigid()
                pmx_rigid.Name = rigid.get("name")
                pmx_rigid.Name_E = rigid.get("name_e")
                attach = rigid.get("attach")
                # print (attach,end="  ")

                if attach == "World":
                    pmx_rigid.Bone = -1
                else:
                    pmx_rigid.Bone = bone_index.get(attach, -1)

                # print(pmx_rigid.Bone)
                pmx_rigid.PhysicalType = int(rigid.get("type"))
                pmx_rigid.Group = int(rigid.get("group"))
                pmx_rigid.NoCollision = int(rigid.get("groups"))
                pmx_rigid.BoundType = int(rigid.get("shape"))

                rigid_size = rigid.find("size")
                pmx_rigid.Size = Math.Vector((float(rigid_size.get("a")),
                                              float(rigid_size.get("b")),
                                              float(rigid_size.get("c"))))

                pmx_rigid.Position = get_Vector(rigid.find("pos"))
                pmx_rigid.Rotate = get_Vector_Rad(rigid.find("rot"))

                pmx_rigid.Mass = float(rigid.get("mass"))
                pmx_rigid.PosLoss = float(rigid.get("pos_dump"))
                pmx_rigid.RotLoss = float(rigid.get("rot_dump"))
                pmx_rigid.OpPos = float(rigid.get("restitution"))
                pmx_rigid.Friction = float(rigid.get("friction"))

                pmx_data.Rigids.append(pmx_rigid)

        # Joint
        # print("Get Joint")
        if xml_reader.has_xml_file:
            joint_list = xml_reader.joint()

            for joint in joint_list:
                pmx_joint = create_PMJoint(joint, rigid_index)
                pmx_data.Joints.append(pmx_joint)

        pmx_data.Save(f)

        GV.SetVertCount(len(pmx_data.Vertices))
        GV.PrintTime(filepath, type='export')

    # finish notification
    if use_custom_normals:
        if len(OK_normal_list):
            bpy.ops.b2pmxem.message(
                'INVOKE_DEFAULT',
                type='INFO',
                line1="Export finished.",
            )
        else:
            bpy.ops.b2pmxem.multiline_message(
                'INVOKE_DEFAULT',
                type='ERROR',
                lines="\n".join(["Export finished.",
                                 "",
                                 "Could not use custom split normals data.",
                                 "Enable 'Auto Smooth' option.",
                                 "or settings of modifier is incorrect."])
            )
    else:
        bpy.ops.b2pmxem.message(
            'INVOKE_DEFAULT',
            type='INFO',
            line1="Export finished.",
        )

    return {'FINISHED'}


def load_xml_bone(bone_name, xml_bone_list, bone_index):
    pmx_bone = pmx.PMBone()

    pmx_bone.Name = xml_bone_list[bone_name].get("name", bone_name)
    pmx_bone.Name_E = xml_bone_list[bone_name].get("name_e", pmx_bone.Name)

    pmx_bone.Rotatable = int(xml_bone_list[bone_name].get("rotatable", "0"))
    pmx_bone.Movable = int(xml_bone_list[bone_name].get("movable", "0"))
    pmx_bone.Visible = int(xml_bone_list[bone_name].get("visible", "0"))
    pmx_bone.Operational = int(xml_bone_list[bone_name].get("operational", "0"))

    pmx_bone.UseIK = int(xml_bone_list[bone_name].get("ik", "0"))

    pmx_bone.AdditionalRotation = int(xml_bone_list[bone_name].get("add_rot", "0"))
    pmx_bone.AdditionalMovement = int(xml_bone_list[bone_name].get("add_move", "0"))
    target_name = xml_bone_list[bone_name].get("target", "Null")
    pmx_bone.AdditionalBoneIndex = int(bone_index.get(target_name, "-1"))
    pmx_bone.AdditionalPower = float(xml_bone_list[bone_name].get("power", "0.0"))

    pmx_bone.UseFixedAxis = int(xml_bone_list[bone_name].get("fixed_axis", "0"))
    pmx_bone.UseLocalAxis = int(xml_bone_list[bone_name].get("local_axis", "0"))

    pmx_bone.LocalAxisX = get_Vector(xml_bone_list[bone_name].find("local_x"))
    pmx_bone.LocalAxisZ = get_Vector(xml_bone_list[bone_name].find("local_z"))

    pmx_bone.Level = int(xml_bone_list[bone_name].get("level", "0"))
    pmx_bone.AfterPhysical = int(xml_bone_list[bone_name].get("after_physical", "0"))
    # if pmx_bone.ExternalBone = 0   unsupport

    return pmx_bone


def get_Vector(data):
    if data is None:
        return Math.Vector((0, 0, 0))

    else:
        x = float(data.get("x"))
        y = float(data.get("y"))
        z = float(data.get("z"))
        return Math.Vector((x, y, z))


def get_Vector_Rad(data):
    x = radians(float(data.get("x")))
    y = radians(float(data.get("y")))
    z = radians(float(data.get("z")))
    return Math.Vector((x, y, z))


if __name__ == '__main__':
    filepath = "output.pmx"
    write_pmx_data(bpy.context, filepath, 'OPT_Utf-16')
    pass
