import bpy
import os
import csv
from mathutils import Color, Vector
import math
from bpy.app.translations import pgettext_iface as iface_
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from . import object_applymodifier
from . import global_variable

# global_variable
GV = global_variable.Init()

# twist position (twist1, twist2, twist3, master)
# 0 = head, 1 = tail
ArmTwistPos = (0.32, 0.52, 0.72, 0.6)
WristTwistPos = (0.285, 0.497, 0.708, 0.6)


def Get_Edit_Bone(edit_bones, jp_name, en_name):
    eb = edit_bones.get(jp_name)
    if eb is None:
        eb = edit_bones.get(en_name)

    return eb


class B2PMXEM_OT_RenameChain(bpy.types.Operator):
    '''Rename chain bone names'''
    bl_idname = "b2pmxem.rename_chain"
    bl_label = "Rename Chain"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        for bone in context.selected_editable_bones:
            name_list = bone.name.rsplit('_')
            name_base = name_list[0]

            if len(name_list) != 3:
                self.report({'ERROR'}, iface_("Bone name format incorrect (e.g. %s)") % "skirt_0_0")
                continue

            tmp_bone = bone
            v = name_list[2]        # vertical index(string)
            h = 1                   # horizonal index(int)

            while len(tmp_bone.children) == 1:
                tmp_bone = tmp_bone.children[0]
                tmp_bone.name = "_".join([name_base, str(h), v])
                h += 1

        return {'FINISHED'}


class B2PMXEM_OT_RenameChainToLR(bpy.types.Operator):
    '''Rename chain bone names to L/R'''
    bl_idname = "b2pmxem.rename_chain_lr"
    bl_label = "Rename Chain to L/R"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        active_bone = get_active_bone(self, context)

        if active_bone is None:
            return {'CANCELLED'}

        # get master name
        name_list = active_bone.name.rsplit('_')

        if len(name_list) != 3:
            self.report({'ERROR'}, iface_("Bone name format incorrect (e.g. %s)") % "skirt_0_0")
            return {'FINISHED'}

        name_base = name_list[0]
        threshold = context.preferences.addons[GV.FolderName].preferences.threshold

        # get max bone num
        bone_max = 0
        bone_list = []
        is_center = False

        for bone in context.object.data.edit_bones:
            name_list = bone.name.rsplit('_')

            if len(name_list) != 3:
                continue

            temp_base = name_list[0]

            if temp_base == name_base:
                # select
                bone.select = bone.select_head = bone.select_tail = True
                bone_list.append(bone)

                if name_list[1] == '0':
                    bone_max += 1

                    if name_list[2] == '0':
                        if abs(bone.head[0]) < threshold:
                            is_center = True

        quot, rem = divmod(bone_max, 2)

        for bone in bone_list:
            name_list = bone.name.rsplit('_')
            LR = 'R' if bone.head[0] < 0 else 'L'

            if is_center:
                if name_list[2] == '0':
                    continue

                # center ON and odd number
                if rem == 1:
                    if int(name_list[2]) <= quot:
                        bone.name = bone.name + '_' + LR
                    else:
                        bone.name = '_'.join([name_list[0], name_list[1], str(bone_max - int(name_list[2])), LR])

                # center ON and even number
                else:
                    if int(name_list[2]) == quot:
                        continue

                    if int(name_list[2]) < quot:
                        bone.name = bone.name + '_' + LR
                    else:
                        bone.name = '_'.join([name_list[0], name_list[1], str(bone_max - int(name_list[2])), LR])
            else:
                # (center OFF and odd number)
                if rem == 1:
                    if int(name_list[2]) == quot:
                        continue

                if int(name_list[2]) < quot:
                    bone.name = bone.name + '_' + LR
                else:
                    bone.name = '_'.join([name_list[0], name_list[1], str(bone_max - 1 - int(name_list[2])), LR])

        return {'FINISHED'}


class B2PMXEM_OT_RenameChainToNum(bpy.types.Operator):

    '''Rename chain bone names to Number'''
    bl_idname = "b2pmxem.rename_chain_num"
    bl_label = "Rename Chain to Number"
    bl_options = {'REGISTER', 'UNDO'}

    reverse: BoolProperty(name="Reverse", description="Rename reverse order", default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        active_bone = get_active_bone(self, context)

        if active_bone is None:
            return {'CANCELLED'}

        # get master name
        name_list = active_bone.name.rsplit('_')

        if len(name_list) != 4:
            self.report({'ERROR'}, iface_("Bone name format incorrect (e.g. %s)") % "skirt_0_0_L")
            return {'FINISHED'}

        name_base = name_list[0]
        threshold = context.preferences.addons[GV.FolderName].preferences.threshold

        # get max bone num
        bone_max = 0
        bone_list = []
        is_center = False

        for bone in context.object.data.edit_bones:
            name_list = bone.name.rsplit('_')

            if len(name_list) not in (3, 4):
                continue

            temp_base = name_list[0]

            if temp_base == name_base:
                # select
                bone.select = bone.select_head = bone.select_tail = True

                if len(name_list) == 4:
                    bone_list.append(bone)

                if name_list[1] == '0':
                    bone_max += 1

                    if name_list[2] == '0':
                        if abs(bone.head[0]) < threshold:
                            is_center = True

        LR = 'R' if self.reverse else 'L'
        quot, rem = divmod(bone_max, 2)

        for bone in bone_list:
            name_list = bone.name.rsplit('_')

            # 'L' (reverse == False)
            if name_list[3] == LR:
                bone.name = bone.name.rstrip('_' + LR)

            # 'R' (center ON)
            elif is_center:
                bone.name = '_'.join([name_list[0], name_list[1], str(bone_max - int(name_list[2]))])

            # (center OFF)
            else:
                bone.name = '_'.join([name_list[0], name_list[1], str(bone_max - 1 - int(name_list[2]))])

        return {'FINISHED'}


# replace period to underscore
def replace_period(context):
    for bone in context.selected_editable_bones:
        bone.name = bone.name.replace('.', '_')


class B2PMXEM_OT_ReplacePeriod(bpy.types.Operator):

    '''Replace period to underscore'''
    bl_idname = "b2pmxem.replace_period"
    bl_label = "Replace Period"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        replace_period(context)
        return {'FINISHED'}


class B2PMXEM_OT_MirrorBones(bpy.types.Operator):

    '''Create X axis mirror in selected bones'''
    bl_idname = "b2pmxem.mirror_bones"
    bl_label = "Mirror Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        if len(context.selected_editable_bones) == 0:
            return {'CANCELLED'}

        areas = {}
        for i, area in enumerate(context.screen.areas):
            areas[area.type] = i

        before_pivot = context.tool_settings.transform_pivot_point
        before_location = context.scene.cursor.location
        context.tool_settings.transform_pivot_point = 'CURSOR'
        context.scene.cursor.location = (0.0, 0.0, 0.0)

        # mirror & L/R naming
        bname = context.selected_editable_bones[0].name
        if bname[-2:] not in GV.TextLR:
            bpy.ops.armature.autoside_names(type='XAXIS')

        replace_period(context)

        bpy.ops.b2pmxem.calculate_roll()
        bpy.ops.armature.duplicate_move()
        bpy.ops.transform.mirror(constraint_axis=(True, False, False))
        bpy.ops.armature.flip_names()
        bpy.ops.b2pmxem.calculate_roll()

        # replace period to underscore
        replace_period(context)

        # reset pivot
        context.tool_settings.transform_pivot_point = before_pivot
        context.scene.cursor.location = before_location

        return {'FINISHED'}


def get_target_bones(self, context):
    active_pose = None
    target_pose = None
    bones = context.selected_pose_bones

    if len(bones) != 2:
        self.report({'ERROR'}, iface_("Select %d bones") % 2)
    else:
        active_pose = context.active_pose_bone
        target_pose = bones[1] if bones[0] == active_pose else bones[0]

    return (active_pose, target_pose)


def get_active_bone(self, context):
    obj = context.active_object
    active_bone = None
    bones = context.selected_pose_bones if obj.mode == 'POSE' else context.selected_editable_bones

    if len(bones) != 1:
        self.report({'ERROR'}, iface_("Select %d bones") % 1)
    else:
        active_bone = context.active_pose_bone if obj.mode == 'POSE' else context.active_bone

    return active_bone


# BoneItem Direction
class B2PMXEM_OT_RecalculateRoll(bpy.types.Operator):

    '''Recalculate Roll for MMD'''
    bl_idname = "b2pmxem.calculate_roll"
    bl_label = "Recalculate Roll"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        axis_x = Vector((1.0, 0.0, 0.0))  # x

        for eb in context.selected_editable_bones:
            eb.roll = 0
            # local_matrix = mathutils.Matrix(eb.matrix)
            local_y = eb.y_axis  # axis_y * local_matrix   #y'
            local_z = eb.z_axis  # axis_z * local_matrix   #z'
            target_z = axis_x.cross(local_y)  # Z''

            if target_z.z > 0:
                target_z = local_y.cross(axis_x)  # Z''

            rot_y = 0
            try:
                tmp = 1.0
                tmp = target_z.dot(local_z) / (local_z.length * target_z.length)
                rot_y = math.acos(tmp)

            except:
                if tmp > 1.0:
                    tmp = 1.0

                elif tmp < -1.0:
                    tmp = -1.0

                rot_y = math.acos(tmp)
                # self.report({'WARNING'}, "Please check the orientation of the bone:" + "  " + eb.name)

            if local_z.x > 0:
                rot_y *= -1

            eb.roll = rot_y

        return {'FINISHED'}


class B2PMXEM_OT_AddIK(bpy.types.Operator):
    '''Add IK Constraint to the active Bone for MMD'''
    bl_idname = "b2pmxem.add_ik"
    bl_label = "Add IK"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(
        name="Type",
        items=(
            ('LEG', "Leg", ""),
            ('TOE', "Toe", ""),
            ('HAIR', "Hair", ""),
            ('NECKTIE', "Necktie", ""),
        ))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        active_pose, target_pose = get_target_bones(self, context)

        if active_pose is None:
            return {'CANCELLED'}

        # recalculate roll
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.b2pmxem.calculate_roll()
        bpy.ops.object.mode_set(mode='POSE')

        # add constraint
        ik = active_pose.constraints.new('IK')
        ik.target = context.active_object
        ik.subtarget = target_pose.name

        if self.type == 'LEG':
            active_pose.use_ik_limit_x = True
            active_pose.ik_min_x = -3.14159
            active_pose.ik_max_x = 0
            active_pose.lock_ik_y = True
            active_pose.lock_ik_z = True
            target_pose["IKLimit"] = 2.0
            target_pose["IKLoops"] = 40
            ik.chain_count = 2

        elif self.type == 'TOE':
            target_pose["IKLimit"] = 4.0
            target_pose["IKLoops"] = 3
            ik.chain_count = 1

        elif self.type == 'HAIR':
            target_pose["IKLimit"] = 0.120
            target_pose["IKLoops"] = 8
            # ik.chain_count = 1

        elif self.type == 'NECKTIE':
            target_pose["IKLimit"] = 0.120
            target_pose["IKLoops"] = 15
            # ik.chain_count = 1

        return {'FINISHED'}


class B2PMXEM_OT_MuteIK(bpy.types.Operator):
    '''Toggle Mute IK Constraint'''
    bl_idname = "b2pmxem.mute_ik"
    bl_label = "Toggle Mute IK"
    bl_options = {'REGISTER', 'UNDO'}

    flag: BoolProperty(name="Mute", description="Set Mute Flag", default=True, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        for bone in context.active_object.pose.bones:
            for const in bone.constraints:
                if const.type == 'IK':
                    const.mute = self.flag

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='POSE')

        return {'FINISHED'}


# Add COPY_ROTATION
def add_copy_rotation(context, active, target_name, influence=1.0):
    const = active.constraints.new('COPY_ROTATION')
    const.target = context.active_object
    const.subtarget = target_name
    const.target_space = 'LOCAL'
    const.owner_space = 'LOCAL'
    const.influence = abs(influence)

    if influence < 0:
        const.invert_x = True
        const.invert_y = True
        const.invert_z = True


class B2PMXEM_OT_AddCopyRot(bpy.types.Operator):
    '''Add Copy Rotation Constraint to the active Bone for MMD'''
    bl_idname = "b2pmxem.add_rotation"
    bl_label = "Add Copy Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        active_pose, target_pose = get_target_bones(self, context)

        if active_pose is None:
            return {'CANCELLED'}

        # Add COPY_ROTATION
        add_copy_rotation(context, active=active_pose, target_name=target_pose.name)

        return {'FINISHED'}


# Add COPY_LOCATION
def add_copy_location(context, active, target_name, influence=1.0):
    const = active.constraints.new('COPY_LOCATION')
    const.target = context.active_object
    const.subtarget = target_name
    const.target_space = 'LOCAL'
    const.owner_space = 'LOCAL'
    const.influence = influence


class B2PMXEM_OT_AddCopyLoc(bpy.types.Operator):
    '''Add Copy Location Constraint to the active Bone for MMD'''
    bl_idname = "b2pmxem.add_location"
    bl_label = "Add Copy Location"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        active_pose, target_pose = get_target_bones(self, context)

        if active_pose is None:
            return {'CANCELLED'}

        # Add COPY_LOCATION
        add_copy_location(context, active=active_pose, target_name=target_pose.name)

        return {'FINISHED'}


# Add LIMIT_ROTATION
def add_limit_rotation(context, active):
    const = active.constraints.new('LIMIT_ROTATION')
    const.use_limit_x = True
    const.use_limit_z = True
    const.owner_space = 'LOCAL'
    active.lock_rotation = [True, False, True]


class B2PMXEM_OT_AddLimit(bpy.types.Operator):
    '''Add Limit Rotation Constraint to the active Bone for MMD'''
    bl_idname = "b2pmxem.limit_rotation"
    bl_label = "Add Limit Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        active_pose = get_active_bone(self, context)

        if active_pose is None:
            return {'CANCELLED'}

        # Add LIMIT_ROTATION
        add_limit_rotation(context, active=active_pose)

        return {'FINISHED'}


# vertex_groups
class B2PMXEM_OT_CreateWeightType(bpy.types.Operator):

    '''Create WeightType vertex group'''
    bl_idname = "b2pmxem.create_weight_type"
    bl_label = "Create WeightType"
    bl_options = {'REGISTER', 'UNDO'}

    color_dict = {
        0: Color((1.0, 0.0, 0.0)),                 # BDEF0 - red
        1: Color((0.784314, 1.0, 0.392157)),       # BDEF1 - light green
        2: Color((0.14902, 0.6, 1.0)),             # BDEF2 - light blue
        3: Color((0.196078, 0.509804, 0.478431)),  # BDEF3 - deep green
        4: Color((0.196078, 0.509804, 0.478431)),  # BDEF4 - deep green
    }                                              # other - red

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.users == 0:
                continue
            if obj.type != 'MESH':
                continue
            if obj.hide_viewport:
                continue

            mesh = obj.data

            # get armature
            arm_obj = obj.find_armature()

            if arm_obj is None:
                continue

            # get vertex_color group
            color_map = mesh.vertex_colors.get(GV.WeightTypeName)

            # create new vertex_color group
            if color_map is None:
                color_map = mesh.vertex_colors.new(name=GV.WeightTypeName)

            # Set active group
            color_map.active = True

            bone_names = arm_obj.data.bones.keys()
            color_list = []

            # Get vertex WeightType
            for v in mesh.vertices:
                count = 0

                for n in v.groups:
                    if len(obj.vertex_groups) > n.group:
                        if obj.vertex_groups[n.group].name in bone_names:
                            if n.weight > 0.0:
                                count += 1

                color_list.append(count)

            # Set Color
            i = 0
            for poly in mesh.polygons:
                for idx in poly.loop_indices:
                    loop = mesh.loops[idx]
                    v = loop.vertex_index

                    c = self.color_dict.get(color_list[v], Color((1.0, 0.0, 0.0)))
                    color_map.data[i].color = (c.r, c.g, c.b, 1.0)
                    i += 1

        return {'FINISHED'}


# delete_groups
class B2PMXEM_OT_DeleteWeightType(bpy.types.Operator):

    '''Delete WeightType vertex group'''
    bl_idname = "b2pmxem.delete_weight_type"
    bl_label = "Delete WeightType"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.users == 0:
                continue
            if obj.type != 'MESH':
                continue

            vertex_colors = obj.data.vertex_colors
            color_map = vertex_colors.get(GV.WeightTypeName)

            if color_map is not None:
                vertex_colors.remove(color_map)

        return {'FINISHED'}


class B2PMXEM_OT_ClearPose(bpy.types.Operator):

    '''Reset Transform of all bones'''
    bl_idname = "b2pmxem.clear_pose"
    bl_label = "Clear Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        bpy.ops.pose.select_all(action='DESELECT')
        return {'FINISHED'}


# apply and skin
class B2PMXEM_OT_RebindArmature(bpy.types.Operator):

    '''Rebind Armature'''
    bl_idname = "b2pmxem.rebind_armature"
    bl_label = "Rebind Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        arm_obj = context.active_object
        obj_list = []    # object list

        # search meshes
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                # get armature
                mod_obj = obj.find_armature()
                if mod_obj == arm_obj:
                    obj_list.append(obj)

        if len(obj_list) == 0:
            # self.report({'WARNING'}, "Not found armature applied object")
            return {'CANCELLED'}

        apply_mod = object_applymodifier.Init()

        # apply 'ARMATURE' modifier
        for obj in obj_list:
            # get modifier applied mesh
            new_mesh = apply_mod.Get_Apply_Mesh(obj, ['ARMATURE'])

            # rename data
            tmp_name = obj.data.name
            old_mesh = obj.data
            old_mesh.name = tmp_name + '_'
            new_mesh.name = tmp_name

            # set modifier applied mesh
            obj.data = new_mesh

            # remove old mesh
            bpy.data.meshes.remove(old_mesh)
            apply_mod.Remove()

        # apply pose as rest pose
        bpy.ops.pose.armature_apply()

        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


# Set Custom Shape
def set_custom_shape(context, pose_bone, shape):
    arm_obj = context.active_object
    use_custom_shape = context.preferences.addons[GV.FolderName].preferences.use_custom_shape

    if use_custom_shape:
        shape_obj = bpy.data.objects.get(shape)

        if shape_obj is None:
            append_object(shape)
            shape_obj = bpy.data.objects[shape]

            # Delete shape object
            context.scene.objects.unlink(shape_obj)
            arm_obj.select = True

        pose_bone.custom_shape = shape_obj
        arm_obj.data.bones[pose_bone.name].show_wire = True


# Twist Bones
class B2PMXEM_OT_TwistBones(bpy.types.Operator):

    '''Add twist bones'''
    bl_idname = "b2pmxem.twist_bones"
    bl_label = "Add Twist Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def add_twist(self, context, bone):
        arm_obj = context.active_object

        parent_bone = bone
        parent_name = bone.name

        dict_child = {
            'arm twist': 'elbow',
            '腕捩': 'ひじ',
            'wrist twist': 'wrist',
            '手捩': '手首',
        }
        twist_type = ""
        twist_list = []

        if parent_name.startswith('arm'):
            twist_type = "arm twist"
            twist_list = ArmTwistPos

        elif parent_name.startswith('腕'):
            twist_type = "腕捩"
            twist_list = ArmTwistPos

        elif parent_name.startswith('elbow'):
            twist_type = "wrist twist"
            twist_list = WristTwistPos

        elif parent_name.startswith('ひじ'):
            twist_type = "手捩"
            twist_list = WristTwistPos

        # Get child
        child_list = []
        for child in parent_bone.children:
            if child.name.startswith(dict_child.get(twist_type)):
                child_list.append(child)

        vec = parent_bone.tail - parent_bone.head
        bone_length = vec * 0.1

        # AutoName L/R
        LR = parent_name[-2:] if parent_name[-2:] in GV.TextLR else ""

        # calc bone location
        pos_list = [parent_bone.head + vec * x for x in twist_list]

        # add twist_master(edit_bone)
        eb = arm_obj.data.edit_bones.new(twist_type + LR)
        eb.select = True
        eb.use_connect = False
        eb.parent = arm_obj.data.edit_bones[parent_name]
        eb.head = pos_list[3]
        eb.tail = pos_list[3] + bone_length
        eb.layers = [False, False, False, False, True, False, False, False, False, False, False, False,
                     False, False, False, False, False, False, False, False, False, False, False, False,
                     False, False, False, False, False, False, False, False]
        bone_name = eb.name

        # Set child bone's parent
        for child in child_list:
            child.use_connect = False
            child.parent = eb

        bpy.ops.object.mode_set(mode='POSE')

        # Add LIMIT_ROTATION
        twist_master = arm_obj.pose.bones[bone_name]
        twist_master.lock_location = [True, True, True]
        add_limit_rotation(context, active=twist_master)

        # Custom Shape
        set_custom_shape(context, twist_master, shape=GV.ShapeTwist1)

        # Add Twist Bones
        n = context.preferences.addons[GV.FolderName].preferences.twistBones
        inc = round(1 / (n + 1), 2)
        for i in range(0, n):
            bpy.ops.object.mode_set(mode='EDIT')

            # add twist link bone
            name = twist_type + str(i + 1) + LR
            eb = arm_obj.data.edit_bones.new(name)
            eb.select = True
            eb.use_connect = False
            eb.parent = arm_obj.data.edit_bones[parent_name]
            eb.head = pos_list[i]
            eb.tail = pos_list[i] + bone_length
            eb.layers = [False, False, False, False, True, False, False, False, False, False, False, False,
                         False, False, False, False, False, False, False, False, False, False, False, False,
                         False, False, False, False, False, False, False, False]
            bone_name = eb.name

            bpy.ops.object.mode_set(mode='POSE')

            # Add COPY_ROTATION
            pb = arm_obj.pose.bones[bone_name]
            pb.lock_location = [True, True, True]
            pb.lock_rotation = [True, False, True]
            influence = inc + inc * i
            add_copy_rotation(context, active=pb, target_name=twist_master.name, influence=influence)

            # Custom Shape
            set_custom_shape(context, pb, shape=GV.ShapeTwist2)

        bpy.ops.object.mode_set(mode='EDIT')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        # deselect bone
        bpy.ops.armature.select_all(action='DESELECT')

        arm_obj = context.active_object
        arm_obj.data.layers[4] = True
        bones = arm_obj.data.edit_bones

        # arm_L --------------------------------------
        bone = Get_Edit_Bone(bones, "腕_L", "arm_L")
        if bone is not None:
            self.add_twist(context, bone)

        # arm_R --------------------------------------
        bone = Get_Edit_Bone(bones, "腕_R", "arm_R")
        if bone is not None:
            self.add_twist(context, bone)

        # elbow_L --------------------------------------
        bone = Get_Edit_Bone(bones, "ひじ_L", "elbow_L")
        if bone is not None:
            self.add_twist(context, bone)

        # elbow_R --------------------------------------
        bone = Get_Edit_Bone(bones, "ひじ_R", "elbow_R")
        if bone is not None:
            self.add_twist(context, bone)

        # recalculate roll
        bpy.ops.b2pmxem.calculate_roll()

        return {'FINISHED'}


# Auto Bone
class B2PMXEM_OT_AutoBone(bpy.types.Operator):
    '''Add bone automatically rotate'''
    bl_idname = "b2pmxem.auto_bone"
    bl_label = "Add Auto Bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        arm_obj = context.active_object
        arm_obj.data.layers[6] = True
        active_bone = get_active_bone(self, context)

        if active_bone is None:
            return {'CANCELLED'}

        # if has parent?
        parent_bone = active_bone.parent
        if parent_bone is None:
            self.report({'ERROR'}, iface_("'%s' No parent bone found") % active_bone.name)
            return {'CANCELLED'}

        active_name = active_bone.name
        parent_name = parent_bone.name

        # japanese name?
        auto = " auto"
        for c in active_name:
            try:
                if ord(c) > 255:
                    auto = "自動"
                    break
            except:
                pass

        LR = active_name[-2:] if active_name[-2:] in GV.TextLR else ""
        auto_name = active_name.rstrip(LR) + auto + LR

        vec = active_bone.tail - active_bone.head
        bone_length = vec * 0.3

        # calc bone location
        pos = active_bone.head

        # recalculate roll
        bpy.ops.b2pmxem.calculate_roll()

        # deselect bone
        bpy.ops.armature.select_all(action='DESELECT')

        # add auto_bone(edit_bone)
        eb = arm_obj.data.edit_bones.new(auto_name)
        eb.select = True
        eb.use_connect = False
        eb.parent = arm_obj.data.edit_bones[parent_name]
        eb.head = pos
        eb.tail = pos + bone_length
        eb.layers = [False, False, False, False, False, False, True, False, False, False, False, False,
                     False, False, False, False, False, False, False, False, False, False, False, False,
                     False, False, False, False, False, False, False, False]
        bone_name = eb.name

        # recalculate roll
        bpy.ops.b2pmxem.calculate_roll()

        bpy.ops.object.mode_set(mode='POSE')

        # Add COPY_ROTATION
        pb = arm_obj.pose.bones[bone_name]
        pb.lock_location = [True, True, True]
        autoInfluence = context.preferences.addons[GV.FolderName].preferences.autoInfluence
        add_copy_rotation(context, active=pb, target_name=active_name, influence=autoInfluence)

        # Custom Shape
        set_custom_shape(context, pb, shape=GV.ShapeAuto)

        # set active
        arm_obj.data.bones.active = arm_obj.data.bones[bone_name]
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class B2PMXEM_OT_SleeveBones(bpy.types.Operator):
    '''Add sleeve IK bones'''
    bl_idname = "b2pmxem.sleeve_bones"
    bl_label = "Add Sleeve IK Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def add_sleeve(self, context, bone, parent_name=None):
        arm_obj = context.active_object

        active_name = bone.name
        pos_head = bone.head
        pos_tail = bone.tail

        LR = active_name[-2:] if active_name[-2:] in GV.TextLR else ""
        sleeve_name = active_name.rstrip(LR) + "+" + LR
        ik_name = active_name.rstrip(LR) + "+IK" + LR

        # add sleeve_bone(edit_bone)
        eb = arm_obj.data.edit_bones.new(sleeve_name)
        eb.select = True
        eb.use_connect = False
        eb.parent = (arm_obj.data.edit_bones[active_name].parent if parent_name is None
                     else arm_obj.data.edit_bones[parent_name])
        eb.head = pos_head
        eb.tail = pos_tail
        eb.layers = [False, False, True, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False]
        sleeve_name = eb.name

        # add ik_bone(edit_bone)
        eb = arm_obj.data.edit_bones.new(ik_name)
        eb.select = True
        eb.use_connect = False
        eb.parent = arm_obj.data.edit_bones[active_name].children[0]
        eb.head = pos_tail
        eb.tail = pos_tail + Vector((0.0, 0.2, 0.0))
        eb.layers = [False, False, True, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False, False, False, False, False,
                     False, False]
        ik_name = eb.name

        bpy.ops.object.mode_set(mode='POSE')

        # Add IK Constraint
        pb = arm_obj.pose.bones[sleeve_name]
        pb.lock_location = [True, True, True]
        ik = pb.constraints.new('IK')
        ik.target = arm_obj
        ik.subtarget = ik_name
        ik.chain_count = 1

        target_pose = arm_obj.pose.bones[ik_name]
        target_pose["IKLimit"] = 1.570796
        target_pose["IKLoops"] = 2

        bpy.ops.object.mode_set(mode='EDIT')

        return sleeve_name

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        # deselect bone
        bpy.ops.armature.select_all(action='DESELECT')

        arm_obj = context.active_object
        arm_obj.data.layers[2] = True
        bones = arm_obj.data.edit_bones

        parent_name = None

        # L
        # arm_L --------------------------------------
        bone = Get_Edit_Bone(bones, "腕_L", "arm_L")
        if bone is not None:
            # if has parent?
            if bone.parent is None or len(bone.children) == 0:
                self.report({'ERROR'}, iface_("'%s' No parent bone and child bone found") % bone.name)

            else:
                parent_name = self.add_sleeve(context, bone)

        # elbow_L --------------------------------------
        bone = Get_Edit_Bone(bones, "ひじ_L", "elbow_L")
        if bone is not None:
            # if has parent?
            if bone.parent is None or len(bone.children) == 0:
                self.report({'ERROR'}, iface_("'%s' No parent bone and child bone found") % bone.name)

            else:
                self.add_sleeve(context, bone, parent_name)

        parent_name = None

        # R
        # arm_R --------------------------------------
        bone = Get_Edit_Bone(bones, "腕_R", "arm_R")
        if bone is not None:
            # if has parent?
            if bone.parent is None or len(bone.children) == 0:
                self.report({'ERROR'}, iface_("'%s' No parent bone and child bone found") % bone.name)

            else:
                parent_name = self.add_sleeve(context, bone)

        # elbow_R --------------------------------------
        bone = Get_Edit_Bone(bones, "ひじ_R", "elbow_R")
        if bone is not None:
            # if has parent?
            if bone.parent is None or len(bone.children) == 0:
                self.report({'ERROR'}, iface_("'%s' No parent bone and child bone found") % bone.name)

            else:
                self.add_sleeve(context, bone, parent_name)

        # recalculate roll
        bpy.ops.b2pmxem.calculate_roll()

        return {'FINISHED'}


def append_object(objname, activeflag=True):
    path_script = os.path.dirname(__file__)
    path_object = "\\Object\\"
    file_name = "template.blend"

    opath = "//" + file_name + path_object + objname
    dpath = os.path.join(path_script, file_name + path_object)

    bpy.ops.wm.link(
        filepath=opath,     # "//filename.blend\\Folder\\"
        directory=dpath,    # "fullpath + \\Folder
        filename=objname,   # "object_name
        relative_path=True,
        link=False,
        autoselect=activeflag,
        active_collection=activeflag)


class B2PMXEM_OT_AppendTemplate(bpy.types.Operator):
    '''Append basic template armature'''
    bl_idname = "b2pmxem.append_template"
    bl_label = "Append Template Armature"
    bl_options = {'REGISTER', 'UNDO'}

    type: EnumProperty(
        name="Type",
        items=(
            ('Type1', "Standard", ""),
            ('Type2', "Large", ""),
            ('Type3', "Small", ""),
            ('Type4', "Chibi", ""),
        ))

    def execute(self, context):
        prefs = context.preferences.addons[GV.FolderName].preferences

        name = self.type + '_Arm'
        append_object(name)

        ao = context.selected_objects
        if len(ao):
            context.view_layer.objects.active = ao[0]

            toJP = {}
            if prefs.use_japanese_name:
                filepath = os.path.join(os.path.dirname(__file__), "template_dict.csv")

                with open(filepath) as csvfile:
                    reader = csv.reader(csvfile)
                    toJP = {en: jp for en, jp in reader}

            bpy.ops.object.mode_set(mode='POSE')

            for pb in context.object.pose.bones:
                # rename EN to JP name
                if prefs.use_japanese_name:
                    pb.name = toJP.get(pb.name, pb.name)

                # set custom shape
                if pb.name in ["master", "全ての親"]:
                    set_custom_shape(context, pb, GV.ShapeMaster)

                elif pb.name in ["eyes", "両目"]:
                    set_custom_shape(context, pb, GV.ShapeEyes)

            # want to A pose? then
            if prefs.use_T_stance:
                bpy.ops.b2pmxem.to_stance(to_A_stance=True)
                bpy.ops.pose.armature_apply()

            bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}


class B2PMXEM_OT_DeleteRight(bpy.types.Operator):

    '''Delete right side bones'''
    bl_idname = "b2pmxem.delete_right"
    bl_label = "Delete Right Sides"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        arm_obj = context.active_object

        bpy.ops.object.select_pattern(pattern="*_R", extend=False)
        bpy.ops.object.select_pattern(pattern="*.R", extend=True)

        if len(context.selected_editable_bones):
            if arm_obj.data.use_mirror_x:
                arm_obj.data.use_mirror_x = False
                bpy.ops.armature.delete()
                arm_obj.data.use_mirror_x = True

            else:
                bpy.ops.armature.delete()

        return {'FINISHED'}


class B2PMXEM_OT_SelectLeft(bpy.types.Operator):

    '''Select left side bones'''
    bl_idname = "b2pmxem.select_left"
    bl_label = "Select Left Sides"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT')

    def execute(self, context):
        bpy.ops.object.select_pattern(pattern="*_L", extend=False)
        bpy.ops.object.select_pattern(pattern="*.L", extend=True)
        return {'FINISHED'}


class B2PMXEM_OT_MirrorVertexGroup(bpy.types.Operator):
    '''Mirror active vertex group (L/R)'''
    bl_idname = "b2pmxem.mirror_vertexgroup"
    bl_label = "Mirror active group"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        if obj and obj.type == 'MESH':
            vg = obj.vertex_groups
            index = vg.active_index

            if index != -1:
                name = vg[index].name
                return (name[-2:] in GV.TextLR)

        return False

    def execute(self, context):
        vg = context.active_object.vertex_groups

        old_index = vg.active_index
        vg_name = vg[old_index].name
        base_name = vg_name[:-2]

        dict_LR = {
            '_L': '_R',
            '.L': '.R',
            '_R': '_L',
            '.R': '.L',
        }
        LR = dict_LR.get(vg_name[-2:])

        bpy.ops.object.vertex_group_copy()
        bpy.ops.object.vertex_group_mirror(use_topology=False)
        bpy.ops.object.vertex_group_clean(group_select_mode='ACTIVE', limit=0)

        new_index = vg.active_index
        vg[new_index].name = base_name + LR

        while (new_index - 1) != old_index:
            bpy.ops.object.vertex_group_move(direction='UP')
            new_index -= 1

        return {'FINISHED'}


def rotate_pose(context, to_A_stance):
    settings = context.preferences.addons[GV.FolderName].preferences
    pose_bones = context.object.data.bones
    sign = -1 if to_A_stance else 1

    str_shoulder = ("shoulder_L", "shoulder.L", "肩_L", "肩.L")
    str_arm = ("arm_L", "arm.L", "腕_L", "腕.L")

    bpy.ops.pose.select_all(action='DESELECT')

    for name in str_shoulder:
        bone = pose_bones.get(name)

        # find shoulder
        if bone is not None:
            pose_bones.active = bone
            bpy.ops.transform.rotate(value=settings.rotShoulder * sign,
                                     orient_axis='Y',
                                     constraint_axis=(False, True, False),
                                     orient_type='GLOBAL')
            bpy.ops.pose.copy()
            bpy.ops.pose.paste(flipped=True)
            break

    bpy.ops.pose.select_all(action='DESELECT')

    for name in str_arm:
        bone = pose_bones.get(name)

        # find arm
        if bone is not None:
            pose_bones.active = bone
            bpy.ops.transform.rotate(value=settings.rotArm * sign,
                                     orient_axis='Y',
                                     constraint_axis=(False, True, False),
                                     orient_type='GLOBAL')
            bpy.ops.pose.copy()
            bpy.ops.pose.paste(flipped=True)
            break

    bpy.ops.pose.select_all(action='DESELECT')


class B2PMXEM_OT_ToStance(bpy.types.Operator):

    '''Rotate bones to A or T stance'''
    bl_idname = "b2pmxem.to_stance"
    bl_label = "to A or T stance"
    bl_options = {'REGISTER', 'UNDO'}

    to_A_stance: BoolProperty(name="to A stance",
                              description="Rotate bones to A stance",
                              default=True,
                              options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        rotate_pose(context, self.to_A_stance)
        return {'FINISHED'}


class B2PMXEM_OT_LockLoc(bpy.types.Operator):
    '''Toggle Lock XYZ location of selected bones'''
    bl_idname = "b2pmxem.lock_location"
    bl_label = "Lock Location"
    bl_options = {'REGISTER', 'UNDO'}

    flag: BoolProperty(name="Lock", description="Set Lock Flag", default=True, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        for bone in context.selected_pose_bones:
            bone.lock_location = [self.flag, self.flag, self.flag]

        bpy.ops.object.posemode_toggle()
        bpy.ops.object.posemode_toggle()

        return {'FINISHED'}


class B2PMXEM_OT_LockRot(bpy.types.Operator):
    '''Toggle Lock XYZ rotation of selected bones'''
    bl_idname = "b2pmxem.lock_rotation"
    bl_label = "Lock Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    flag: BoolProperty(name="Lock", description="Set Lock Flag", default=True, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE' and obj.mode == 'POSE')

    def execute(self, context):
        for bone in context.selected_pose_bones:
            bone.lock_rotation = [self.flag, self.flag, self.flag]

        bpy.ops.object.posemode_toggle()
        bpy.ops.object.posemode_toggle()

        return {'FINISHED'}


class B2PMXEM_OT_AddDriver(bpy.types.Operator):

    '''Add driver to the same shape_key name of all objects'''
    bl_idname = "b2pmxem.add_driver"
    bl_label = "Add Shape Driver"
    bl_options = {'REGISTER', 'UNDO'}

    delete: BoolProperty(name="Delete", description="Set Delete Flag", default=False, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and obj.data.shape_keys is not None)

    def add_driver(self, active_keys, target_block, active_block):
        if self.delete:
            return

        # add driver
        fcurve = target_block.driver_add('value')

        # driver setting
        drv = fcurve.driver
        drv.type = 'AVERAGE'

        # variable setting
        var = drv.variables.new()
        # var.name = active_block.name
        var.type = 'SINGLE_PROP'

        targ = var.targets[0]
        targ.id_type = 'KEY'
        targ.id = active_keys
        targ.data_path = active_block.path_from_id('value')

    def execute(self, context):
        active_obj = context.active_object
        active_keys = active_obj.data.shape_keys

        for index, active_block in enumerate(active_keys.key_blocks):
            # pass 'basis' shape
            if index == 0:
                continue

            for target_obj in bpy.data.objects:
                if target_obj.type != 'MESH':
                    continue
                if target_obj == active_obj:
                    continue

                target_keys = target_obj.data.shape_keys
                if target_keys is None:
                    continue

                target_block = target_keys.key_blocks.get(active_block.name)

                # find target shape_key
                if target_block is not None:
                    if hasattr(target_keys.animation_data, "drivers"):
                        target_drivers = target_keys.animation_data.drivers

                        for fcurve in target_drivers:
                            fcurve_name = fcurve.data_path.split('"')[1]

                            # find exist (Don't overlap created)
                            if fcurve_name == active_block.name:
                                if self.delete:
                                    target_block.driver_remove('value')
                                break
                        # not found
                        else:
                            self.add_driver(active_keys, target_block, active_block)
                    else:
                        self.add_driver(active_keys, target_block, active_block)

        return {'FINISHED'}
