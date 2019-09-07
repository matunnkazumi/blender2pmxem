import bpy
import mathutils as Math
import os
from math import radians

from blender2pmxe import pmx
from blender2pmxe import object_applymodifier, global_variable

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

    w = GlobalMatrix * mat * v
    w = w / w.w
    w.resize_3d()
    return w


def GT_normal(vec, mat):  # GlobalTransformation
    v = vec.copy()
    v.resize_4d()

    w = GlobalMatrix * mat.to_3x3().to_4x4() * v
    w.resize_3d()
    w.normalize()
    return w


def write_pmx_data(context, filepath="",
                   encode_type='OPT_Utf-16',
                   use_mesh_modifiers=False,
                   use_custom_normals=False,
                   ):

    prefs = context.user_preferences.addons[GV.FolderName].preferences
    use_japanese_name = prefs.use_japanese_name

    GV.SetStartTime()

    with open(filepath, "wb") as f:

        import xml.etree.ElementTree as ETree
        pmx_data = None
        pmx_data = pmx.Model()

        #
        # Filepath
        #
        file_name = bpy.path.basename(filepath)

        xml_path = bpy.path.ensure_ext(filepath, ".xml", True)
        has_xml_file = os.path.isfile(xml_path)

        default_xml = "default_jp.xml" if use_japanese_name == True else "default_en.xml"
        def_path = os.path.join(os.path.dirname(__file__), default_xml)
        has_def_file = os.path.isfile(def_path)

        #
        # XML
        #
        def_root = ETree.parse(def_path) if has_def_file else None
        xml_root = ETree.parse(xml_path) if has_xml_file else None

        if xml_root is None:
            xml_root = def_root
            has_xml_file = has_def_file

        #
        # Header
        #
        if has_xml_file and xml_root is not None:
            infonode = xml_root.find("pmdinfo")

            # Name
            pmx_data.Name = infonode.findtext("name", file_name)
            pmx_data.Name_E = infonode.findtext("name_e", pmx_data.Name)

            # Comment
            pmx_data.Comment = infonode.findtext("comment", "Comment")
            pmx_data.Comment_E = infonode.findtext("comment_e", "Comment")

            pmx_data.Comment = pmx_data.Comment.replace("\n", "\r\n")
            pmx_data.Comment_E = pmx_data.Comment_E.replace("\n", "\r\n")

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
        xml_bone_list = {}
        if has_xml_file and xml_root is not None:
            bone_root = xml_root.find("bones")
            bone_list = bone_root.findall("bone")

            for bone in bone_list:
                xml_bone_list[bone.get("b_name")] = bone

        # make index
        bone_stack = []
        arm_obj = bpy.context.active_object

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
                        bone_stack.append((arm_obj.name, bone.name + "_", bone.name))

                    if (const.target.name, const.subtarget) in bone_stack:
                        bone_stack.remove((const.target.name, const.subtarget))

                    bone_stack.append((const.target.name, const.subtarget))

        bone_index = {}
        for index, bone_name in enumerate(bone_stack):
            bone_index[bone_name[1]] = index

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
                tip_name_jp = ""
                tip_name_en = ""
                b_name = bone.name[:-2]
                lr = bone.name[-2:]
                find_lr = lr in GV.TextLR

                if b_name in GV.TextAnkle and find_lr:
                    tip_name_jp = GV.GetLR_JP[lr] + GV.GetAnkle_JP[b_name]
                    tip_name_en = GV.GetAnkle_EN[b_name] + lr

                elif find_lr:
                    tip_name_jp = GV.GetLR_JP[lr] + b_name + GV.Tip_JP
                    tip_name_en = b_name + GV.Tip_EN + lr

                else:
                    tip_name_jp = bone.name + GV.Tip_JP
                    tip_name_en = bone.name + GV.Tip_EN

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
                            pmx_bone.ToConnectType = 1
                            pmx_bone.ChildIndex = bone_index.get(bone.name + "_", -1)

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

                            if cursor.lock_ik_x or cursor.lock_ik_y or cursor.lock_ik_z or cursor.use_ik_limit_x or cursor.use_ik_limit_y or cursor.use_ik_limit_z:
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
        xml_mat_index = {}
        xml_mat_list = {}

        if has_xml_file and xml_root is not None:
            mat_root = xml_root.find("materials")
            mat_list = mat_root.findall("material")

            for xml_index, mat in enumerate(mat_list):
                xml_mat_index[xml_index] = mat.get("b_name")
                xml_mat_list[mat.get("b_name")] = mat

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
            for mat_obj in bpy.data.objects:
                if mat_obj.users == 0:
                    continue
                if mat_obj.type != 'MESH':
                    continue

                # Get Weight Bone
                mesh_parent = mat_obj.find_armature()

                if mesh_parent != arm_obj:
                    continue

                tmp_mat = mat_obj.data.materials.get(mat.name)
                if tmp_mat is not None:
                    # Find Material
                    break
            # Not found
            else:
                continue

            pmx_mat = pmx.PMMaterial()
            pmx_mat.Name = mat.name
            pmx_mat.Name_E = mat.name

            # Load XML Status
            if pmx_mat.Name in xml_mat_list.keys():
                temp_mat = xml_mat_list[pmx_mat.Name]
                pmx_mat.Name = temp_mat.get("name", mat.name)
                pmx_mat.Name_E = temp_mat.get("name_e", pmx_mat.Name)
                pmx_mat.UseSystemToon = int(temp_mat.get("use_systemtoon", "1"))

                if pmx_mat.UseSystemToon == 1:
                    pmx_mat.ToonIndex = int(temp_mat.get("toon", "0"))

                else:
                    tex_path = temp_mat.get("toon", "toon01.bmp")

                    if tex_path == "" or tex_path == "-1":
                        pmx_mat.ToonIndex = -1

                    else:
                        pmx_mat.ToonIndex = tex_dic.setdefault(tex_path, len(tex_dic))

                pmx_mat.Both = int(temp_mat.get("both", "0"))
                pmx_mat.GroundShadow = int(temp_mat.get("ground_shadow", "0"))
                pmx_mat.DropShadow = int(temp_mat.get("drop_shadow", "0"))
                pmx_mat.OnShadow = int(temp_mat.get("on_shadow", "0"))

                pmx_mat.OnEdge = int(temp_mat.get("on_edge", "0"))
                pmx_mat.EdgeSize = float(temp_mat.get("edge_size", "1.0"))

                edge_c = temp_mat.find("edge_color")
                pmx_mat.EdgeColor = Math.Vector((float(edge_c.get("r", "0.0")), float(edge_c.get("g", "0.0")), float(edge_c.get("b", "0.0")), float(edge_c.get("a", "1.0"))))

            r, g, b = mat.diffuse_color
            pmx_mat.Deffuse = Math.Vector((r, g, b, mat.alpha))

            r, g, b = mat.specular_color
            pmx_mat.Specular = Math.Vector((r, g, b))
            pmx_mat.Power = mat.specular_hardness

            if "Ambient" in mat:
                pmx_mat.Ambient = Math.Vector(mat["Ambient"].to_list())
            else:
                pmx_mat.Ambient = pmx_mat.Deffuse.xyz * 0.4

            pmx_mat.FaceLength = 0

            tex_base_path = bpy.path.abspath("//")

            if tex_base_path == "":
                tex_base_path = os.path.dirname(filepath)

            texture_0 = None if mat.texture_slots[0] is None else mat.texture_slots[0].texture

            if texture_0 is not None and texture_0.type == "IMAGE" and texture_0.image is not None:
                tex_abs_path = bpy.path.abspath(texture_0.image.filepath)
                tex_path = bpy.path.relpath(tex_abs_path, tex_base_path)
                tex_path = tex_path.replace("//", "", 1)

                pmx_mat.TextureIndex = tex_dic.setdefault(tex_path, len(tex_dic))

            texture_1 = None if mat.texture_slots[1] is None else mat.texture_slots[1].texture

            if texture_1 is not None and texture_1.type == "IMAGE" and texture_1.image is not None:
                tex_abs_path = bpy.path.abspath(texture_1.image.filepath)
                tex_path = bpy.path.relpath(tex_abs_path, tex_base_path)
                tex_path = tex_path.replace("//", "", 1)

                pmx_mat.SphereIndex = tex_dic.setdefault(tex_path, len(tex_dic))

                #[0:None 1:Multi 2:Add 3:SubTexture]
                if mat.texture_slots[1].texture_coords == 'UV':
                    pmx_mat.SphereType = 3

                if mat.texture_slots[1].blend_type == 'ADD':
                    pmx_mat.SphereType = 2

                elif mat.texture_slots[1].blend_type == 'MULTIPLY':
                    pmx_mat.SphereType = 1

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
            if not mat_name in xml_mat_list.keys():
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
        xml_morph_index = {}
        xml_morph_list = {}
        morph_list = {}

        # read default_xml data
        if has_def_file and def_root is not None:
            morph_root = def_root.find("morphs")
            morph_l = morph_root.findall("morph")

            for morph in morph_l:
                xml_morph_list[morph.get("b_name")] = morph

        if has_xml_file and xml_root is not None:
            morph_root = xml_root.find("morphs")
            morph_l = morph_root.findall("morph")

            for xml_index, morph in enumerate(morph_l):
                # print(morph.get("b_name"))
                xml_morph_index[xml_index] = morph.get("b_name")
                xml_morph_list[morph.get("b_name")] = morph

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
            if use_mesh_modifiers == True:
                mesh = apply_mod.Get_Apply_Mesh(mesh_obj)

            # Custom Normals
            normals = {}
            if use_custom_normals == True and hasattr(mesh, "has_custom_normals"):
                if mesh.has_custom_normals == True:
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
            if len(mesh.uv_textures) > 0:
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
                        target_vert = mesh.vertices[loop.vertex_index]
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
                            pmd_morph.Name = xml_morph.get("name", block.name)
                            pmd_morph.Name_E = xml_morph.get("name_e", block.name)
                            pmd_morph.Panel = int(xml_morph.get("group", "4"))

                    # calculate relative morph position
                    morph_index = 0
                    for base_v, morph_v in zip(base_key.data, block.data):
                        if base_v.co != morph_v.co:
                            v = pmx.PMMorphOffset()
                            v.Index = morph_index + base_vert_index
                            v.Move = GT(morph_v.co, mesh_mat) - GT(base_v.co, mesh_mat)
                            pmd_morph.Offsets.append(v)

                            if v.Index in copy_vert.keys():
                                v2 = pmx.PMMorphOffset()
                                v2.Move = v.Move

                                for i in copy_vert[v.Index]:
                                    v2.Index = i
                                    pmd_morph.Offsets.append(v2)

                        morph_index += 1

                    morph_list[block.name] = pmd_morph

            base_vert_index += (len(mesh.vertices) + add_vertex_count)

            # remove modifier applied mesh
            if use_mesh_modifiers == True:
                apply_mod.Remove()

        # print NG_object_list
        if len(NG_object_list):
            print("Doesn't have Material:")
            for data in NG_object_list:
                print("   --> %s" % data)

        # print OK_normal_list
        if len(OK_normal_list):
            print("Export with Custom Normals:")
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
        keys = list(xml_morph_index.keys())
        keys.sort()
        # print(keys)

        morph_tag_index = {}
        index = 0
        for key in keys:
            m_name = xml_morph_index[key]
            if m_name in morph_list.keys():
                pmx_data.Morphs.append(morph_list[m_name])
                morph_tag_index[m_name] = index
                index += 1

        for m_name, morph in morph_list.items():
            check_index = morph_tag_index.get(m_name, -1)
            if check_index == -1:
                pmx_data.Morphs.append(morph)
                morph_tag_index[m_name] = index
                index += 1

        # Label
        # print("Get Label")
        if has_xml_file and xml_root is not None:
            label_root = xml_root.find("labels")
            label_list = label_root.findall("label")

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
        if has_xml_file and xml_root is not None:
            rigid_root = xml_root.find("rigid_bodies")
            rigid_list = rigid_root.findall("rigid")

            for rigid in rigid_list:
                pmx_rigid = pmx.PMRigid()
                pmx_rigid.Name = rigid.get("name")
                pmx_rigid.Name_E = rigid.get("name_e")
                attach = rigid.get("attach")
                #print (attach,end="  ")

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
                pmx_rigid.Size = Math.Vector((float(rigid_size.get("a")), float(rigid_size.get("b")), float(rigid_size.get("c"))))

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
        if has_xml_file and xml_root is not None:
            joint_root = xml_root.find("constraints")
            joint_list = joint_root.findall("constraint")

            for joint in joint_list:
                pmx_joint = pmx.PMJoint()
                # joint_node.set("index",str(index))
                pmx_joint.Name = joint.get("name")
                pmx_joint.Name_E = joint.get("name_e")
                pmx_joint.Parent = int(joint.get("body_A"))
                pmx_joint.Child = int(joint.get("body_B"))
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

                pmx_data.Joints.append(pmx_joint)

        pmx_data.Save(f)

        GV.SetVertCount(len(pmx_data.Vertices))
        GV.PrintTime(filepath, type='export')

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
