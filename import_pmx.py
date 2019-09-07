# if "bpy" in locals():
#    import imp
#    if "pmx" in locals():
#        imp.reload(pmx)
import bpy
import mathutils
import os
import math
import xml.etree.ElementTree as etree
import re

from blender2pmxe import add_function, global_variable

# global_variable
GV = global_variable.Init()


GlobalMatrix = mathutils.Matrix(
    ([1, 0, 0, 0],
     [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 5]))


def GT(vec, mat):  # GlobalTransformation
    v = vec.copy()
    v.resize_4d()

    w = mat * v
    w = w / w.w
    w.resize_3d()
    return w


def GT_normal(vec, mat):  # GlobalTransformation
    v = vec.copy()
    v.resize_4d()

    w = mat * v
    w = w / w.w
    w.resize_3d()
    w.normalize()
    return w


def Get_JP_or_EN_Name(jp_name, en_name, use_japanese_name, bone_mode=False):
    tmp_name = jp_name

    if use_japanese_name == False and en_name != "":
        tmp_name = en_name

    if bone_mode == True:
        findR = re.compile("\u53f3")
        findL = re.compile("\u5de6")

        if findR.search(tmp_name):
            tmp_name = findR.sub("", tmp_name) + "_R"

        elif findL.search(tmp_name):
            tmp_name = findL.sub("", tmp_name) + "_L"

    return tmp_name


def Get_Edit_Bone(edit_bones, jp_name, en_name):
    eb = edit_bones.get(jp_name)
    if eb is None:
        eb = edit_bones.get(en_name)

    return eb


def Get_Adjust_Data(edit_bones, jp_name, en_name):
    eb = Get_Edit_Bone(edit_bones, jp_name, en_name)
    vec = None
    axis = None
    length = None

    # Calc Adjust Data
    if eb is not None:
        vec = eb.tail - eb.head
        axis = vec * 0.1
        length = vec.length

    return (eb, vec, axis, length)


def Set_Adjust_Data(active, eb, vec, axis, length):
    len_active = (active.head - eb.head).length
    active.head = eb.head + vec * (len_active / length)
    active.tail = active.head + axis


def Search_Master(bone_name):
    return bone_name in ["master", "全ての親"]


def Search_Eyes(bone_name):
    return bone_name in ["eyes", "両目"]


def Search_Twist_Master(bone_name):
    # 腕捩 \u8155\u6369
    # 手捩 \u624B\u6369
    name_jp = re.search(r'^(\u8155|\u624B)\u6369_', bone_name) is not None
    name_en = re.search(r'^(arm|wrist)\s+twist(\.|_)', bone_name) is not None
    return (name_jp or name_en)


def Search_Twist_Num(bone_name):
    # 腕捩 \u8155\u6369
    # 手捩 \u624B\u6369
    name_jp = re.search(r'^(\u8155|\u624B)\u6369[0-9]+', bone_name) is not None
    name_en = re.search(r'^(arm|wrist)\s+twist[0-9]+', bone_name) is not None
    return (name_jp or name_en)


def Search_Auto_Bone(bone_name):
    # 自動 \u81EA\u52D5
    # 補助 \u88DC\u52A9
    name_jp = re.search(r'(\u81EA\u52D5|\u88DC\u52A9)', bone_name) is not None
    name_en = re.search(r'(auto|sub)', bone_name) is not None
    return (name_jp or name_en)


def Search_Leg_Dummy(bone_name):
    # 足 \u8DB3
    # ひざ \u3072\u3056
    # 足首 \u8DB3\u9996
    name_jp = re.search(r'^(\u8DB3|\u3072\u3056|\u8DB3\u9996)D', bone_name) is not None
    name_en = re.search(r'(\.|_)(L|R)D$', bone_name) is not None
    return (name_jp or name_en)


def Set_Bone_Position(pmx_data, arm_dat, blender_bone_list, fix=False):
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    bone_id = {}

    for (bone_index, data_bone) in enumerate(pmx_data.Bones):
        bone_name = blender_bone_list[bone_index]

        # find tip bone
        if data_bone.Visible == 0 and data_bone.AdditionalRotation == 0 and data_bone.AdditionalMovement == 0:
            tip_type1 = (data_bone.ToConnectType == 0 and data_bone.TailPosition == mathutils.Vector((0, 0, 0)))
            tip_type2 = (data_bone.ToConnectType == 1 and data_bone.ChildIndex <= 0)

            if tip_type1 == True or tip_type2 == True:
                parent_id = bone_id.get(blender_bone_list.get(data_bone.Parent), -1)
                bone_id[bone_name] = parent_id
                continue

        eb = None
        if fix == True:
            eb = arm_dat.edit_bones.get(bone_name)
            if eb is None:
                continue

        else:
            eb = arm_dat.edit_bones.new(bone_name)

        eb.head = GT(data_bone.Position, GlobalMatrix)
        eb.roll = 0
        # eb.hide = (data_bone.Visible == 0)
        eb.use_connect = False

        bone_id[bone_name] = bone_name
        fixed_axis = None

        if data_bone.Parent != -1:
            parent_id = bone_id.get(blender_bone_list.get(data_bone.Parent), -1)

            if parent_id != -1:
                parent_bone = arm_dat.edit_bones[parent_id]
                eb.parent = parent_bone
                fixed_axis = (parent_bone.tail - parent_bone.head) * 0.1

                if pmx_data.Bones[data_bone.Parent].ChildIndex == bone_index:
                    if data_bone.Movable == 0 and eb.head != eb.parent.head:
                        eb.use_connect = True

        # Set TailPosition
        if data_bone.ToConnectType == 0:
            eb.tail = GT(data_bone.Position + data_bone.TailPosition, GlobalMatrix)

        elif data_bone.ChildIndex != -1:
            eb.tail = GT(pmx_data.Bones[data_bone.ChildIndex].Position, GlobalMatrix)

        else:
            eb.tail = GT(data_bone.Position + mathutils.Vector((0, 0, 1.0)), GlobalMatrix)

        if data_bone.UseFixedAxis == 1 and eb.head == eb.tail:
            if fixed_axis is None:
                eb.tail = GT(data_bone.Position + data_bone.FixedAxis, GlobalMatrix)
            else:
                eb.tail = eb.head + fixed_axis

        if eb.head == eb.tail:
            if data_bone.AdditionalBoneIndex >= 0 and pmx_data.Bones[data_bone.AdditionalBoneIndex].UseFixedAxis == 1:
                if fixed_axis is None:
                    eb.tail = GT(data_bone.Position + pmx_data.Bones[data_bone.AdditionalBoneIndex].FixedAxis, GlobalMatrix)
                else:
                    eb.tail = eb.head + fixed_axis
            else:
                eb.tail = GT(data_bone.Position + mathutils.Vector((0, 0, 1.0)), GlobalMatrix)

    # Bones Update
    bpy.ops.object.mode_set(mode='OBJECT')

    return bone_id


def read_pmx_data(context, filepath="",
                  adjust_bone_position=False,
                  bone_transfer=False,
                  ):

    prefs = context.user_preferences.addons[GV.FolderName].preferences
    use_japanese_name = prefs.use_japanese_name
    use_custom_shape = prefs.use_custom_shape
    xml_save_versions = prefs.saveVersions

    GV.SetStartTime()

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    with open(filepath, "rb") as f:

        from blender2pmxe import pmx
        pmx_data = pmx.Model()
        pmx_data.Load(f)

        if pmx_data.Status.Magic == 0:
            #Echo("Loading Pmd ")
            from blender2pmxe import pmd
            from blender2pmxe import pmd2pmx
            f.seek(0)
            d_pmd = pmd.Model()
            d_pmd.Load(f)
            pmx_data = pmd2pmx.Convert(d_pmd)

        scene = context.scene
        base_path = os.path.dirname(filepath)

        for ob in scene.objects:
            ob.select = False

        tmp_name = Get_JP_or_EN_Name(pmx_data.Name, pmx_data.Name_E, use_japanese_name)

        arm_dat = bpy.data.armatures.new(tmp_name + "_Arm")
        arm_obj = bpy.data.objects.new(tmp_name + "_Arm", arm_dat)

        arm_obj.show_x_ray = True
        arm_dat.draw_type = "STICK"

        scn = bpy.context.scene
        scn.objects.link(arm_obj)
        scn.objects.active = arm_obj
        scn.update()

        # Make XML
        blender_bone_list = make_xml(pmx_data, filepath, use_japanese_name, xml_save_versions)

        arm_obj.select = True
        bone_id = {}

        # Set Bone Position
        bone_id = Set_Bone_Position(pmx_data, arm_dat, blender_bone_list)

        bpy.ops.object.mode_set(mode="POSE", toggle=False)

        # Set Bone Status
        for (bone_index, data_bone) in enumerate(pmx_data.Bones):
            bone_name = blender_bone_list[bone_index]

            pb = arm_obj.pose.bones.get(bone_name)
            if pb is None:
                continue

            # Find name (True or False)
            find_master = Search_Master(bone_name)
            find_eyes = Search_Eyes(bone_name)
            find_twist_m = Search_Twist_Master(bone_name)
            find_twist_n = Search_Twist_Num(bone_name)
            find_auto = Search_Auto_Bone(bone_name)

            if find_twist_n == True:
                pb.lock_rotation = [True, False, True]

            if data_bone.Rotatable == 0:
                pb.lock_rotation = [True, True, True]

            if data_bone.Movable == 0:
                pb.lock_location = [True, True, True]

            if data_bone.Operational == 0:
                pb.lock_rotation = [True, True, True]
                pb.lock_location = [True, True, True]

            if data_bone.AdditionalRotation == 1:
                const = pb.constraints.new('COPY_ROTATION')
                const.target = arm_obj
                const.subtarget = blender_bone_list[data_bone.AdditionalBoneIndex]
                const.target_space = 'LOCAL'
                const.owner_space = 'LOCAL'

                const.influence = abs(data_bone.AdditionalPower)
                if data_bone.AdditionalPower < 0:
                    const.invert_x = True
                    const.invert_y = True
                    const.invert_z = True

            if data_bone.AdditionalMovement == 1:
                const = pb.constraints.new('COPY_LOCATION')
                const.target = arm_obj
                const.subtarget = blender_bone_list[data_bone.AdditionalBoneIndex]
                const.target_space = 'LOCAL'
                const.owner_space = 'LOCAL'

                const.influence = abs(data_bone.AdditionalPower)
                if data_bone.AdditionalPower < 0:
                    const.invert_x = True
                    const.invert_y = True
                    const.invert_z = True

            if data_bone.UseFixedAxis == 1:
                const = pb.constraints.new('LIMIT_ROTATION')
                const.use_limit_x = True
                const.use_limit_z = True
                const.owner_space = 'LOCAL'
                pb.lock_rotation = [True, False, True]

            if data_bone.UseLocalAxis == 0:
                pass
            if data_bone.AfterPhysical == 0:
                pass
            if data_bone.ExternalBone == 0:
                pass

            # Set Custom Shape
            if use_custom_shape == True:
                len_const = len(pb.constraints)

                if find_master == True:
                    add_function.set_custom_shape(context, pb, shape=GV.ShapeMaster)

                elif find_eyes == True:
                    add_function.set_custom_shape(context, pb, shape=GV.ShapeEyes)

                elif find_twist_m == True and len_const:
                    add_function.set_custom_shape(context, pb, shape=GV.ShapeTwist1)

                elif find_twist_n == True and len_const:
                    add_function.set_custom_shape(context, pb, shape=GV.ShapeTwist2)

                elif find_auto == True and len_const:
                    add_function.set_custom_shape(context, pb, shape=GV.ShapeAuto)

            # Set IK
            if data_bone.UseIK != 0:
                pb["IKLoops"] = data_bone.IK.Loops
                pb["IKLimit"] = data_bone.IK.Limit

                if len(data_bone.IK.Member) > 0:
                    ik_name = blender_bone_list[data_bone.IK.Member[0].Index]
                    new_ik = arm_obj.pose.bones[ik_name].constraints.new("IK")
                    new_ik.target = arm_obj
                    new_ik.subtarget = blender_bone_list[bone_index]
                    new_ik.chain_count = len(data_bone.IK.Member)

                for ik_member in data_bone.IK.Member:
                    if ik_member.UseLimit == 1:
                        member_name = blender_bone_list[ik_member.Index]
                        pose_member = arm_obj.pose.bones[member_name]

                        if ik_member.UpperLimit.x == ik_member.LowerLimit.x:
                            pose_member.lock_ik_x = True

                        else:
                            pose_member.use_ik_limit_x = True
                            pose_member.ik_min_x = ik_member.LowerLimit.x
                            pose_member.ik_max_x = ik_member.UpperLimit.x

                        if ik_member.UpperLimit.y == ik_member.LowerLimit.y:
                            pose_member.lock_ik_y = True

                        else:
                            pose_member.use_ik_limit_y = True
                            pose_member.ik_min_y = ik_member.LowerLimit.y
                            pose_member.ik_max_y = ik_member.UpperLimit.y

                        if ik_member.UpperLimit.z == ik_member.LowerLimit.z:
                            pose_member.lock_ik_z = True

                        else:
                            pose_member.use_ik_limit_z = True
                            pose_member.ik_min_z = ik_member.LowerLimit.z
                            pose_member.ik_max_z = ik_member.UpperLimit.z

        bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        # Adjust Bone Position
        if adjust_bone_position == True:
            # Get_Adjust_Data(edit_bones, jp_name, en_name)
            arm_L, vec_arm_L, axis_arm_L, len_arm_L = Get_Adjust_Data(arm_dat.edit_bones, "腕_L", "arm_L")
            arm_R, vec_arm_R, axis_arm_R, len_arm_R = Get_Adjust_Data(arm_dat.edit_bones, "腕_R", "arm_R")

            elb_L, vec_elb_L, axis_elb_L, len_elb_L = Get_Adjust_Data(arm_dat.edit_bones, "ひじ_L", "elbow_L")
            elb_R, vec_elb_R, axis_elb_R, len_elb_R = Get_Adjust_Data(arm_dat.edit_bones, "ひじ_R", "elbow_R")

            for eb in arm_dat.edit_bones:
                # Find name (True or False)
                find_master = Search_Master(eb.name)
                find_eyes = Search_Eyes(eb.name)
                find_twist_m = Search_Twist_Master(eb.name)
                find_twist_n = Search_Twist_Num(eb.name)
                find_auto = Search_Auto_Bone(eb.name)
                find_leg_d = Search_Leg_Dummy(eb.name)

                # Master
                if find_master == True:
                    eb_center = Get_Edit_Bone(arm_dat.edit_bones, "センター", "center")

                    if eb_center is not None:
                        eb.head = [0.0, 0.0, 0.0]
                        eb.tail = eb_center.head

                # Eyes
                elif find_eyes == True:
                    eb_eye = Get_Edit_Bone(arm_dat.edit_bones, "目_L", "eye_L")

                    if eb_eye is not None:
                        eb.head.x = 0.0
                        eb.head.y = 0.0
                        eb.head.z = eb.tail.z = eb_eye.head.z * 1.16
                        eb.tail.x = 0.0
                        eb.tail.y = -0.25

                # Auto Bone (Sub Bone), Leg_D Bone
                elif find_auto == True or find_leg_d == True:
                    pb = arm_obj.pose.bones[eb.name]

                    for const in pb.constraints:
                        if hasattr(const, "subtarget"):
                            eb.use_connect = False

                            for child in eb.children:
                                child.use_connect = False

                            eb_sub = arm_dat.edit_bones[const.subtarget]
                            multi = 0.3 if find_auto == True else 1.0
                            axis = (eb_sub.tail - eb_sub.head) * multi
                            eb.head = eb_sub.head
                            eb.tail = eb_sub.head + axis
                            break

                # Twist
                elif find_twist_m == True or find_twist_n == True:
                    eb.use_connect = False

                    for child in eb.children:
                        child.use_connect = False

                    # Set_Adjust_Data(active, eb, vec, axis, length)
                    if re.search(r'^(\u8155|arm)', eb.name) is not None:
                        if eb.name.endswith("_L") and arm_L is not None:
                            Set_Adjust_Data(eb, arm_L, vec_arm_L, axis_arm_L, len_arm_L)

                        elif eb.name.endswith("_R") and arm_R is not None:
                            Set_Adjust_Data(eb, arm_R, vec_arm_R, axis_arm_R, len_arm_R)

                    else:   # "手" or "wrist"
                        if eb.name.endswith("_L") and elb_L is not None:
                            Set_Adjust_Data(eb, elb_L, vec_elb_L, axis_elb_L, len_elb_L)

                        elif eb.name.endswith("_R") and elb_R is not None:
                            Set_Adjust_Data(eb, elb_R, vec_elb_R, axis_elb_R, len_elb_R)

        # BoneItem Direction
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.b2pmxe.calculate_roll()
        bpy.ops.armature.select_all(action='DESELECT')

        bpy.ops.object.mode_set(mode='OBJECT')

        # Create Mash
        mesh = bpy.data.meshes.new(tmp_name)
        obj_mesh = bpy.data.objects.new(mesh.name, mesh)
        scene.objects.link(obj_mesh)

        # Link Parent
        mod = obj_mesh.modifiers.new('RigModif', 'ARMATURE')
        mod.object = arm_obj
        mod.use_bone_envelopes = False
        mod.use_vertex_groups = True

        # Add Vertex Group
        vert_group = {}
        vert_group_index = {}
        for bone_index, bone_data in enumerate(pmx_data.Bones):
            bone_name = blender_bone_list[bone_index]
            target_name = arm_dat.bones[bone_id[bone_name]].name
            vert_group_index[bone_index] = target_name

            if not target_name in vert_group.keys():
                vert_group[target_name] = obj_mesh.vertex_groups.new(target_name)

        mesh.update()

        # Add Vertex
        mesh.vertices.add(len(pmx_data.Vertices))

        for vert_index, vert_data in enumerate(pmx_data.Vertices):
            mesh.vertices[vert_index].co = GT(vert_data.Position, GlobalMatrix)
            mesh.vertices[vert_index].normal = GT_normal(vert_data.Normal, GlobalMatrix)
            #mesh.vertices[vert_index].uv = pmx_data.Vertices[vert_index].UV

            # BDEF1
            if vert_data.Type == 0:
                vert_group[vert_group_index[vert_data.Bones[0]]].add([vert_index], 1.0, 'REPLACE')

            # BDEF2
            elif vert_data.Type == 1:
                vert_group[vert_group_index[vert_data.Bones[0]]].add([vert_index], vert_data.Weights[0], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[1]]].add([vert_index], 1.0 - vert_data.Weights[0], 'ADD')

            # BDEF4
            elif vert_data.Type == 2:
                vert_group[vert_group_index[vert_data.Bones[0]]].add([vert_index], vert_data.Weights[0], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[1]]].add([vert_index], vert_data.Weights[1], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[2]]].add([vert_index], vert_data.Weights[2], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[3]]].add([vert_index], vert_data.Weights[3], 'ADD')

            # SDEF
            elif vert_data.Type == 3:
                vert_group[vert_group_index[vert_data.Bones[0]]].add([vert_index], vert_data.Weights[0], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[1]]].add([vert_index], 1.0 - vert_data.Weights[0], 'ADD')
                # Todo? SDEF

            # QDEF
            elif vert_data.Type == 4:
                vert_group[vert_group_index[vert_data.Bones[0]]].add([vert_index], vert_data.Weights[0], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[1]]].add([vert_index], vert_data.Weights[1], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[2]]].add([vert_index], vert_data.Weights[2], 'ADD')
                vert_group[vert_group_index[vert_data.Bones[3]]].add([vert_index], vert_data.Weights[3], 'ADD')
                # Todo? QDEF

        mesh.update()

        # Add Face
        poly_count = len(pmx_data.Faces) // 3
        mesh.polygons.add(poly_count)
        mesh.polygons.foreach_set("loop_start", range(0, poly_count * 3, 3))
        mesh.polygons.foreach_set("loop_total", (3,) * poly_count)
        mesh.polygons.foreach_set("use_smooth", (True,) * poly_count)
        mesh.loops.add(len(pmx_data.Faces))
        #mesh.loops.foreach_set("vertex_index" ,pmx_data.Faces)

        for faceIndex in range(poly_count):
            mesh.loops[faceIndex * 3].vertex_index = pmx_data.Faces[faceIndex * 3]
            mesh.loops[faceIndex * 3 + 1].vertex_index = pmx_data.Faces[faceIndex * 3 + 2]
            mesh.loops[faceIndex * 3 + 2].vertex_index = pmx_data.Faces[faceIndex * 3 + 1]

        mesh.update()

        if bone_transfer:
            scene.update()
            return arm_obj, obj_mesh

        # Add Textures
        #image_dic = {}
        textures_dic = {}
        NG_tex_list = []
        for (tex_index, tex_data) in enumerate(pmx_data.Textures):
            tex_path = os.path.join(base_path, tex_data.Path)
            try:
                bpy.ops.image.open(filepath=tex_path)
                #image_dic[tex_index] = bpy.data.images[len(bpy.data.images)-1]
                textures_dic[tex_index] = bpy.data.textures.new(os.path.basename(tex_path), type='IMAGE')
                textures_dic[tex_index].image = bpy.data.images[os.path.basename(tex_path)]

                # Use Alpha
                textures_dic[tex_index].image.use_alpha = True
                textures_dic[tex_index].image.alpha_mode = 'PREMUL'

            except:
                NG_tex_list.append(tex_data.Path)

        # print NG_tex_list
        if len(NG_tex_list):
            bpy.ops.b2pmxe.message('INVOKE_DEFAULT', type='INFO', line1="Some Texture file not found.", use_console=True)
            for data in NG_tex_list:
                print("   --> %s" % data)

        mesh.update()

        # Add Material
        mat_status = []
        for (mat_index, mat_data) in enumerate(pmx_data.Materials):
            blender_mat_name = Get_JP_or_EN_Name(mat_data.Name, mat_data.Name_E, use_japanese_name)

            temp_mattrial = bpy.data.materials.new(blender_mat_name)
            temp_mattrial.diffuse_color = mat_data.Deffuse.xyz
            temp_mattrial.alpha = mat_data.Deffuse.w
            temp_mattrial.specular_color = mat_data.Specular
            temp_mattrial.specular_hardness = mat_data.Power
            temp_mattrial["Ambient"] = mat_data.Ambient
            temp_mattrial.use_transparency = True

            mat_status.append((len(mat_status), mat_data.FaceLength))

            mesh.materials.append(temp_mattrial)

            # Flags
            #self.Both = 0
            #self.GroundShadow = 1
            #self.DropShadow = 1
            #self.OnShadow = 1
            #self.OnEdge = 1
            #
            # Edge
            #self.EdgeColor =  mathutils.Vector((0,0,0,1))
            #self.EdgeSize = 1.0

            # Texture
            if mat_data.TextureIndex != -1:
                temp_tex = pmx_data.Textures[mat_data.TextureIndex]

                if temp_mattrial.texture_slots[0] is None:
                    temp_mattrial.texture_slots.add()

                temp_mattrial.texture_slots[0].texture = textures_dic.get(mat_data.TextureIndex, None)
                temp_mattrial.texture_slots[0].texture_coords = "UV"
                temp_mattrial.texture_slots[0].uv_layer = "UV_Data"

                # MMD Settings
                temp_mattrial.texture_slots[0].use_map_color_diffuse = True
                temp_mattrial.texture_slots[0].use_map_alpha = True
                temp_mattrial.texture_slots[0].blend_type = 'MULTIPLY'
                temp_mattrial.texture_slots[0]

            if mat_data.SphereIndex != -1:
                temp_tex = pmx_data.Textures[mat_data.SphereIndex]

                if temp_mattrial.texture_slots[1] is None:
                    temp_mattrial.texture_slots.add()

                if temp_mattrial.texture_slots[1] is None:
                    temp_mattrial.texture_slots.add()

                temp_mattrial.texture_slots[1].texture = textures_dic.get(mat_data.SphereIndex, None)

                #[0:None 1:Multi 2:Add 3:SubTexture]
                if mat_data.SphereType == 1:
                    temp_mattrial.texture_slots[1].texture_coords = 'NORMAL'
                    temp_mattrial.texture_slots[1].blend_type = 'MULTIPLY'

                elif mat_data.SphereType == 2:
                    temp_mattrial.texture_slots[1].texture_coords = 'NORMAL'
                    temp_mattrial.texture_slots[1].blend_type = 'ADD'

                elif mat_data.SphereType == 3:
                    temp_mattrial.texture_slots[1].texture_coords = "UV"
                    temp_mattrial.texture_slots[1].uv_layer = "UV_Data"
                    temp_mattrial.texture_slots[1].blend_type = 'MIX'

        mesh.update()

        # Set Material & UV
        # Set UV Layer
        if mesh.uv_textures.active_index < 0:
            mesh.uv_textures.new("UV_Data")

        mesh.uv_textures.active_index = 0

        uv_data = mesh.uv_layers.active.data[:]

        #uvtex = mesh.uv_textures.new("UV_Data")
        #uv_data = uvtex.data

        index = 0
        for dat in mat_status:
            for i in range(dat[1] // 3):
                # Set Material
                mesh.polygons[index].material_index = dat[0]

                # Set Texture
                if pmx_data.Materials[dat[0]].TextureIndex < len(bpy.data.images) and pmx_data.Materials[dat[0]].TextureIndex >= 0:
                    if textures_dic.get(pmx_data.Materials[dat[0]].TextureIndex, None) is not None:
                        mesh.uv_textures[0].data[index].image = textures_dic[pmx_data.Materials[dat[0]].TextureIndex].image

                # Set UV
                poly_vert_index = mesh.polygons[index].loop_start
                uv_data[poly_vert_index + 0].uv = pmx_data.Vertices[mesh.polygons[index].vertices[0]].UV
                uv_data[poly_vert_index + 1].uv = pmx_data.Vertices[mesh.polygons[index].vertices[1]].UV
                uv_data[poly_vert_index + 2].uv = pmx_data.Vertices[mesh.polygons[index].vertices[2]].UV

                # Inv UV V
                uv_data[poly_vert_index + 0].uv[1] = 1 - uv_data[poly_vert_index + 0].uv[1]
                uv_data[poly_vert_index + 1].uv[1] = 1 - uv_data[poly_vert_index + 1].uv[1]
                uv_data[poly_vert_index + 2].uv[1] = 1 - uv_data[poly_vert_index + 2].uv[1]

                # TwoSide 2.6 not use?
                # todo set parameter
                # uv_data[index].use_twoside = True

                index = index + 1

        mesh.update()

        # Add Shape Key
        if len(pmx_data.Morphs) > 0:
            # Add Basis key
            if mesh.shape_keys is None:
                obj_mesh.shape_key_add("Basis", False)
                mesh.update()

            for data in pmx_data.Morphs:
                # Vertex Morph
                if data.Type == 1:
                    blender_morph_name = Get_JP_or_EN_Name(data.Name, data.Name_E, use_japanese_name)
                    temp_key = obj_mesh.shape_key_add(blender_morph_name, False)

                    for v in data.Offsets:
                        temp_key.data[v.Index].co += GT(v.Move, GlobalMatrix)

                    mesh.update()

            # To activate "Basis" shape
            obj_mesh.active_shape_key_index = 0

        scene.update()

        GV.SetVertCount(len(pmx_data.Vertices))
        GV.PrintTime(filepath, type='import')

    return


def make_xml(pmx_data, filepath, use_japanese_name, xml_save_versions):

    # const
    # "\u0030\u003a\u0062\u0061\u0073\u0065\u0028\u56fa\u5b9a\u0029\u0031\u003a\u307e\u3086\u0020\u0032\u003a\u76ee\u0020\u0033\u003a\u30ea\u30c3\u30d7\u0020\u0034\u003a\u305d\u306e\u4ed6"
    J_Face_Comment = "\u8868\u60C5\u30B0\u30EB\u30FC\u30D7\u0020\u0030\u003A\u4F7F\u7528\u4E0D\u53EF\u0020\u0031\u003A\u307E\u3086\u0020\u0032\u003A\u76EE\u0020\u0033\u003A\u30EA\u30C3\u30D7\u0020\u0034\u003A\u305D\u306E\u4ED6"

    # filename
    root, ext = os.path.splitext(filepath)
    xml_path = root + ".xml"

    num = 1
    xml_exist_list = []

    a = re.search(r'[0-9]{1,2}$', root)
    if a is not None:
        num += int(a.group())
        root = root.rstrip(a.group())

    for index in range(num, xml_save_versions + 1):
        if os.path.isfile(xml_path) != True:
            break

        xml_exist_list.append(bpy.path.basename(xml_path))
        xml_path = root + str(index) + ".xml"

    save_message = 'Save As "%s"' % bpy.path.basename(xml_path)
    bpy.ops.b2pmxe.message('INVOKE_DEFAULT', type='INFO', line1=save_message)

    # print xml_exist_list
    if len(xml_exist_list):
        print("xml_file is exist:")
        for data in xml_exist_list:
            print("   --> %s" % data)

    #
    # XML
    #
    root = etree.Element('{local}pmxstatus', attrib={'{http://www.w3.org/XML/1998/namespace}lang': 'jp'})

    #
    # Header
    #   Name
    #   Comment

    # Add Info
    infonode = etree.SubElement(root, "pmdinfo")
    infonode.tail = "\r\n"

    # Add Name
    pmx_name = etree.SubElement(infonode, "name")
    pmx_name.text = pmx_data.Name.rstrip()
    pmx_name_e = etree.SubElement(infonode, "name_e")
    pmx_name_e.text = pmx_data.Name_E.rstrip()

    # Add Comment
    pmx_cmment = etree.SubElement(infonode, "comment")
    pmx_cmment.text = pmx_data.Comment.rstrip()
    pmx_cmment_e = etree.SubElement(infonode, "comment_e")
    pmx_cmment_e.text = pmx_data.Comment_E.rstrip()

    #
    # Morphs
    #

    # Add Morph
    morph_root = etree.SubElement(root, "morphs")
    morph_root.tail = "\r\n"
    morph_comment = etree.Comment(J_Face_Comment)
    morph_comment.tail = "\r\n"
    morph_root.append(morph_comment)

    # Morph
    # Name    # morph name
    # Name_E  # morph name English
    # Panel   # [1:Eyebrows 2:Mouth 3:Eye 4:Other 0:System]
    # Type    # [0:Group 1:Vertex 2:Bone 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4 8:Material]
    # Offsets # offset data
    for (morph_index, pmx_morph) in enumerate(pmx_data.Morphs):
        blender_morph_name = Get_JP_or_EN_Name(pmx_morph.Name.rstrip(), pmx_morph.Name_E.rstrip(), use_japanese_name)

        morph_node = etree.SubElement(morph_root, "morph")
        morph_node.tail = "\r\n"
        # morph_node.set('index' , str(morph_index))
        morph_node.set('group', str(pmx_morph.Panel))
        morph_node.set('name', pmx_morph.Name.rstrip())
        morph_node.set('name_e', pmx_morph.Name_E.rstrip())
        morph_node.set('b_name', blender_morph_name)

    #
    # Bones
    #
    bone_root = etree.SubElement(root, "bones")
    bone_root.tail = "\r\n"

    blender_bone_list = {}

    for (bone_index, pmx_bone) in enumerate(pmx_data.Bones):
        blender_bone_name = Get_JP_or_EN_Name(pmx_bone.Name, pmx_bone.Name_E, use_japanese_name, bone_mode=True)
        blender_bone_list[bone_index] = (blender_bone_name)

    for (bone_index, pmx_bone) in enumerate(pmx_data.Bones):
        blender_bone_name = blender_bone_list[bone_index]
        bone_node = etree.SubElement(bone_root, "bone")
        bone_node.tail = "\r\n"
        # bone_node.set("index" , str(bone_index))
        bone_node.set("name", pmx_bone.Name)
        bone_node.set("name_e", pmx_bone.Name_E)
        bone_node.set("b_name", blender_bone_name)

        # Bone Status
        bone_node.set("rotatable", str(pmx_bone.Rotatable))
        bone_node.set("movable", str(pmx_bone.Movable))
        bone_node.set("visible", str(pmx_bone.Visible))
        bone_node.set("operational", str(pmx_bone.Operational))
        bone_node.set("ik", str(pmx_bone.UseIK))
        bone_node.set("add_rot", str(pmx_bone.AdditionalRotation))

        if pmx_bone.AdditionalBoneIndex >= 0:
            bone_node.set("target", blender_bone_list[pmx_bone.AdditionalBoneIndex])

        bone_node.set("power", str(pmx_bone.AdditionalPower))
        bone_node.set("add_move", str(pmx_bone.AdditionalMovement))

        if pmx_bone.AdditionalMovement == 1 or pmx_bone.AdditionalRotation == 1:
            bone_node.set("target", blender_bone_list[pmx_bone.AdditionalBoneIndex])
            bone_node.set("power", str(pmx_bone.AdditionalPower))

        bone_node.set("fixed_axis", str(pmx_bone.UseFixedAxis))
        bone_node.set("local_axis", str(pmx_bone.UseLocalAxis))

        set_Vector(bone_node, pmx_bone.LocalAxisX, "local_x")
        set_Vector(bone_node, pmx_bone.LocalAxisZ, "local_z")

        bone_node.set("level", str(pmx_bone.Level))
        bone_node.set("after_physical", str(pmx_bone.AfterPhysical))
        # if pmx_bone.AfterPhysical  = 0 unsupport
        # if pmx_bone.ExternalBone = 0   unsupport

    #
    # Labels
    #

    # Add Labels
    labels_root = etree.SubElement(root, "labels")
    labels_root.text = "\r\n"
    labels_root.tail = "\r\n"

    for (label_index, pmx_label) in enumerate(pmx_data.DisplayFrames):
        label_node = etree.SubElement(labels_root, "label")
        label_node.tail = "\r\n"
        # label_node.set("index" , str(label_index))
        label_node.set("name", pmx_label.Name)
        label_node.set("name_e", pmx_label.Name_E)
        label_node.set("type", str(pmx_label.Type))

        for (index, member) in enumerate(pmx_label.Members):
            member_node = etree.SubElement(label_node, "tab")
            member_node.tail = "\r\n"
            # member_node.set("index" , str(index))

            if member[0] == 0:
                member_node.set("type", "bone")
                member_node.set("name", blender_bone_list[member[1]])

            else:
                member_node.set("type", "morph")
                label_morph_name = Get_JP_or_EN_Name(
                    pmx_data.Morphs[member[1]].Name,
                    pmx_data.Morphs[member[1]].Name_E,
                    use_japanese_name)
                member_node.set("name", label_morph_name)

    #
    # Materials
    #
    material_root = etree.SubElement(root, "materials")
    material_root.tail = "\r\n"

    for (mat_index, pmx_mat) in enumerate(pmx_data.Materials):
        blender_mat_name = Get_JP_or_EN_Name(pmx_mat.Name, pmx_mat.Name_E, use_japanese_name)

        material_node = etree.SubElement(material_root, "material")
        material_node.tail = "\r\n"
        # material_node.set("index",str(mat_index))
        material_node.set("name", pmx_mat.Name)
        material_node.set("name_e", pmx_mat.Name_E)
        material_node.set("b_name", blender_mat_name)
        material_node.set("use_systemtoon", str(pmx_mat.UseSystemToon))

        if pmx_mat.UseSystemToon == 1:
            material_node.set("toon", str(pmx_mat.ToonIndex))

        elif pmx_mat.ToonIndex < 0:
            material_node.set("toon", "-1")

        else:
            material_node.set("toon", str(pmx_data.Textures[pmx_mat.ToonIndex].Path))

        material_node.set("both", str(pmx_mat.Both))
        material_node.set("ground_shadow", str(pmx_mat.GroundShadow))
        material_node.set("drop_shadow", str(pmx_mat.DropShadow))
        material_node.set("on_shadow", str(pmx_mat.OnShadow))
        material_node.set("on_edge", str(pmx_mat.OnEdge))
        material_node.set("edge_size", str(pmx_mat.EdgeSize))
        material_edge_color = etree.SubElement(material_node, "edge_color")
        material_edge_color.set("r", str(pmx_mat.EdgeColor.x))
        material_edge_color.set("g", str(pmx_mat.EdgeColor.y))
        material_edge_color.set("b", str(pmx_mat.EdgeColor.z))
        material_edge_color.set("a", str(pmx_mat.EdgeColor.w))

    #
    # Rigid
    #
    rigid_root = etree.SubElement(root, "rigid_bodies")
    rigid_root.text = "\r\n"
    rigid_root.tail = "\r\n"

    for (rigid_index, pmx_rigid) in enumerate(pmx_data.Rigids):
        rigid_node = etree.SubElement(rigid_root, "rigid")
        rigid_node.tail = "\r\n"
        # rigid_node.set("index",str(rigid_index))
        rigid_node.set("name", pmx_rigid.Name)
        rigid_node.set("name_e", pmx_rigid.Name_E)

        if (pmx_rigid.Bone < 0):
            rigid_node.set("attach", "World")
        else:
            rigid_node.set("attach", blender_bone_list[pmx_rigid.Bone])

        rigid_node.set("type", str(pmx_rigid.PhysicalType))
        rigid_node.set("group", str(pmx_rigid.Group))
        rigid_node.set("groups", str(pmx_rigid.NoCollision))
        rigid_node.set("shape", str(pmx_rigid.BoundType))

        rigid_size = etree.SubElement(rigid_node, "size")
        rigid_size.set("a", str("%.7f" % pmx_rigid.Size[0]))
        rigid_size.set("b", str("%.7f" % pmx_rigid.Size[1]))
        rigid_size.set("c", str("%.7f" % pmx_rigid.Size[2]))

        set_Vector(rigid_node, pmx_rigid.Position, "pos")
        set_Vector_Deg(rigid_node, pmx_rigid.Rotate, "rot")

        rigid_node.set("mass", str("%.7f" % pmx_rigid.Mass))
        rigid_node.set("pos_dump", str("%.7f" % pmx_rigid.PosLoss))
        rigid_node.set("rot_dump", str("%.7f" % pmx_rigid.RotLoss))
        rigid_node.set("restitution", str("%.7f" % pmx_rigid.OpPos))
        rigid_node.set("friction", str("%.7f" % pmx_rigid.Friction))

    #
    # Joint
    #
    joint_root = etree.SubElement(root, "constraints")
    joint_root.text = "\r\n"
    joint_root.tail = "\r\n"

    for (joint_index, pmx_joint) in enumerate(pmx_data.Joints):

        joint_node = etree.SubElement(joint_root, "constraint")
        joint_node.tail = "\r\n"
        # joint_node.set("index",str(joint_index))
        joint_node.set("name", pmx_joint.Name)
        joint_node.set("name_e", pmx_joint.Name_E)
        joint_node.set("body_A", str(pmx_joint.Parent))
        joint_node.set("body_B", str(pmx_joint.Child))

        set_Vector(joint_node, pmx_joint.Position, "pos")
        set_Vector_Deg(joint_node, pmx_joint.Rotate, "rot")

        joint_pos_limit = etree.SubElement(joint_node, "pos_limit")
        set_Vector(joint_pos_limit, pmx_joint.PosLowerLimit, "from")
        set_Vector(joint_pos_limit, pmx_joint.PosUpperLimit, "to")

        joint_rot_limit = etree.SubElement(joint_node, "rot_limit")
        set_Vector_Deg(joint_rot_limit, pmx_joint.RotLowerLimit, "from")
        set_Vector_Deg(joint_rot_limit, pmx_joint.RotUpperLimit, "to")

        set_Vector(joint_node, pmx_joint.PosSpring, "pos_spring")
        set_Vector(joint_node, pmx_joint.RotSpring, "rot_spring")

    tree = etree.ElementTree(root)
    tree.write(xml_path, encoding="utf-8")
    return blender_bone_list


def set_Vector(_node, _data, _name):
    data = etree.SubElement(_node, _name)
    data.set("x", str("%.7f" % _data.x))
    data.set("y", str("%.7f" % _data.y))
    data.set("z", str("%.7f" % _data.z))
    return True


def set_Vector_Deg(_node, _data, _name):
    data = etree.SubElement(_node, _name)
    data.set("x", str("%.7f" % math.degrees(_data.x)))
    data.set("y", str("%.7f" % math.degrees(_data.y)))
    data.set("z", str("%.7f" % math.degrees(_data.z)))
    return True

if __name__ == '__main__':
    filepath = "imput.pmx"
    read_pmx_data(bpy.context, filepath)
    pass
