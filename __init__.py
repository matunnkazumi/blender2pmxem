bl_info = {
    "name": "MMD PMX Format (Extend)",
    "author": "NaNashi",
    "version": (1, 0, 3),
    "blender": (2, 7, 6),
    "api": 38019,
    "location": "File > Import-Export",
    "description": "Import-Export PMX model data. give priority to english name.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

import bpy
import os
from glob import glob
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, PointerProperty, IntProperty
from blender2pmxe import import_pmx, export_pmx
from blender2pmxe import add_function, solidify_edge, global_variable
from blender2pmxe import space_view3d_materials_utils

# global_variable
GV = global_variable.Init()


# ------------------------------------------------------------------------
#    store properties in the active scene
# ------------------------------------------------------------------------
def preset_template_callback(scene, context):
    prefs = context.user_preferences.addons[GV.FolderName].preferences
    items = [
        ("Type1", prefs.textType1, ""),
        ("Type2", prefs.textType2, ""),
        ("Type3", prefs.textType3, ""),
        ("Type4", prefs.textType4, ""),
    ]
    return items


def preset_ik_callback(scene, context):
    isJP = context.user_preferences.addons[GV.FolderName].preferences.use_japanese_ui
    textLeg = ("Leg", "足")
    textToe = ("Toe", "つま先")
    textHair = ("Hair", "髪")
    textNecktie = ("Necktie", "ネクタイ")
    items = [
        ("leg", textLeg[isJP], ""),
        ("toe", textToe[isJP], ""),
        ("hair", textHair[isJP], ""),
        ("necktie", textNecktie[isJP], ""),
    ]
    return items


class Blender2PmxeProperties(bpy.types.PropertyGroup):

    @classmethod
    def register(cls):
        bpy.types.Scene.b2pmxe_properties = PointerProperty(type=cls)

        cls.edge_color = FloatVectorProperty(
            name="Color",
            default=(0.0, 0.0, 0.0),
            min=0.0, max=1.0, step=10, precision=3,
            subtype='COLOR'
        )

        cls.edge_thickness = FloatProperty(
            name="Thickness",
            default=0.01, min=0.0025, max=0.05, step=0.01, precision=4,
            unit='LENGTH'
        )

        cls.template = EnumProperty(
            name="Template type:",
            description="Select Template type",
            items=preset_template_callback
        )

        cls.ik = EnumProperty(
            name="IK type:",
            description="Select IK type",
            items=preset_ik_callback
        )

        cls.fix_bone_position = BoolProperty(
            name="Fix bone position",
            description="Fix bone position using *.pmx file",
            default=False
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.b2pmxe_properties


# ------------------------------------------------------------------------


class Blender2PmxeAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    use_japanese_ui = BoolProperty(
        name="Use Japanese UI",
        description="Use japanese name on the button",
        default=False
    )

    use_T_stance = BoolProperty(
        name="Append with T stance",
        description="Append template armature with T stance",
        default=False
    )

    use_custom_shape = BoolProperty(
        name="Use Custom Shape",
        description="Use Custom Shape when creating bones",
        default=False
    )

    use_japanese_name = BoolProperty(
        name="Use Japanese Bone name",
        description="Append template armature with Japanese bone name",
        default=False
    )

    saveVersions = IntProperty(name="Save Versions", default=0, min=0, max=32)

    rotShoulder = FloatProperty(name="Shoulder", default=0.261799, min=-1.5708, max=1.5708, unit='ROTATION')
    rotArm = FloatProperty(name="Arm", default=0.401426, min=-1.5708, max=1.5708, unit='ROTATION')

    twistBones = IntProperty(name="Twist bones", default=3, min=0, max=3)
    autoInfluence = FloatProperty(name="Influence", default=0.5, min=-1.0, max=1.0, step=1)
    threshold = FloatProperty(name="Threshold", default=0.01, min=0.0, max=1.0, step=0.001, precision=5)

    textType1 = StringProperty(name="Type1", default="Normal")
    textType2 = StringProperty(name="Type2", default="Big")
    textType3 = StringProperty(name="Type3", default="Small")
    textType4 = StringProperty(name="Type4", default="Chibi")

    def draw(self, context):
        layout = self.layout

        row = layout.split(0.025)
        row.label("")

        split = row.split(0.4)
        col = split.column()
        col.prop(self, "use_japanese_ui")
        col.separator()
        col.prop(self, "use_japanese_name")

        col = split.column()
        col.prop(self, "use_custom_shape")
        col.separator()
        col.prop(self, "use_T_stance")

        layout.separator()

        row = layout.split(0.01)
        row.label("")
        split = row.split(percentage=0.4)
        col = split.column()
        col.label(text="Number of .xml old versions:")
        col.separator()  # separator 0 #####
        col.label(text="Angle of T stance and A stance:")
        col.separator()  # separator 1 #####
        col.label(text="Number of Twist link bones:")
        col.separator()  # separator 2 #####
        col.label(text="Auto Bone influence:")
        col.separator()  # separator 3 #####
        col.label(text="Rename Chain threshold:")
        col.separator()  # separator 4 #####
        col.label(text="Template Armature name:")

        split = split.split(percentage=0.95)
        col = split.column()
        col.prop(self, "saveVersions")
        col.separator()  # separator 0 #####
        row = col.row(align=True)
        row.prop(self, "rotShoulder")
        row.prop(self, "rotArm")
        col.separator()  # separator 1 #####
        col.prop(self, "twistBones")
        col.separator()  # separator 2 #####
        col.prop(self, "autoInfluence")
        col.separator()  # separator 3 #####
        col.prop(self, "threshold")
        col.separator()  # separator 4 #####
        box = col.box()
        row = box.row()
        row.prop(self, "textType1")
        row.prop(self, "textType2")
        row = box.row()
        row.prop(self, "textType3")
        row.prop(self, "textType4")

        layout.separator()


class ImportBlender2Pmx(bpy.types.Operator, ImportHelper):

    '''Load a MMD PMX File.'''
    bl_idname = "import.pmx_data_e"
    bl_label = "Import PMX Data (Extend)"
    # bl_options = {'PRESET'}

    filename_ext = ".pmx"
    filter_glob = StringProperty(default="*.pm[dx]", options={'HIDDEN'})

    adjust_bone_position = BoolProperty(
        name="Adjust bone position",
        description="Automatically adjust bone position",
        default=False
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", ))
        return import_pmx.read_pmx_data(context, **keywords)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, "adjust_bone_position")


class ExportBlender2Pmx(bpy.types.Operator, ExportHelper):

    '''Save a MMD PMX File.'''
    bl_idname = "export.pmx_data_e"
    bl_label = "Export PMX Data (Extend)"
    bl_options = {'PRESET'}

    # ExportHelper mixin class uses this
    filename_ext = ".pmx"
    filter_glob = StringProperty(default="*.pmx", options={'HIDDEN'})

    encode_type = EnumProperty(items=(('OPT_Utf-8', "UTF-8", "To use UTF-8 encoding."),
                                      ('OPT_Utf-16', "UTF-16", "To use UTF-16 encoding."),
                                      ),
                               name="Encode",
                               description="Select the encoding to use",
                               default='OPT_Utf-16'
                               )

    use_mesh_modifiers = BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers (Warning, may be slow)",
        default=False,
    )

    use_custom_normals = BoolProperty(
        name="Custom Normals",
        description="Use custom normals",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'ARMATURE')

    def execute(self, context):
        file_name = bpy.path.basename(self.filepath)

        if file_name == "":
            bpy.ops.b2pmxe.message('INVOKE_DEFAULT', message="Filename is empty.")
            return {'CANCELLED'}

        arm_obj = context.active_object

        # Remove empty materials
        for obj in bpy.data.objects:
            if obj.users == 0:
                continue
            if obj.type != 'MESH':
                continue

            # Get Weight Bone
            mesh_parent = obj.find_armature()

            if mesh_parent != arm_obj:
                continue

            # Remove empty materials
            mats = obj.data.materials
            index = 0
            while index < len(mats):
                if mats[index] is None:
                    mats.pop(index)
                    index -= 1
                index += 1

        keywords = self.as_keywords(ignore=("check_existing", "filter_glob", ))

        return export_pmx.write_pmx_data(context, **keywords)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.split(percentage=0.3)
        row.label(text="Encode:")
        row.prop(self, "encode_type", text="")

        box.prop(self, "use_mesh_modifiers")
        box.prop(self, "use_custom_normals")


#
#   The error message operator. When invoked, pops up a dialog
#   window with the given message.
#
class B2PmxeMessageOperator(bpy.types.Operator):
    bl_idname = "b2pmxe.message"
    bl_label = "B2Pmxe Message"

    message = StringProperty()
    use_console = BoolProperty(default=False)

    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=360)

    def draw(self, context):
        layout = self.layout
        layout.label("Info:", icon='INFO')

        row = layout.split(0.075)
        row.label("")
        col = row.column(align=True)
        col.label(self.message)

        if self.use_console == True:
            col.label("Please check the Console.")

        layout.separator()


class B2PmxeMakeXML(bpy.types.Operator):

    '''Make a MMD XML File. and Update Materials.'''
    bl_idname = "b2pmxe.make_xml"
    bl_label = "Make XML File"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (bpy.data.is_saved) and (obj and obj.type == 'ARMATURE')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        directory = bpy.path.abspath("//")
        files = [os.path.relpath(x, directory) for x in glob(os.path.join(directory, '*.pmx'))]

        if len(files) == 0:
            return {'CANCELLED'}

        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        directory = bpy.path.abspath("//")
        files = [os.path.relpath(x, directory) for x in glob(os.path.join(directory, '*.pmx'))]

        layout = self.layout
        layout.label(text="Select File:", icon="FILE_TEXT")

        row = layout.split(0.01)
        row.label("")

        split = row.split(0.968)
        col = split.column(align=True)

        props = context.scene.b2pmxe_properties
        col.prop(props, "fix_bone_position")
        col.separator()

        for file in files:
            col.operator("b2pmxe.save_as_xml", text=file).filename = file

        layout.separator()


class B2PmxeSaveAsXML(bpy.types.Operator):

    '''Save As a MMD XML File.'''
    bl_idname = "b2pmxe.save_as_xml"
    bl_label = "Save As XML File"
    bl_options = {'UNDO'}

    filename = StringProperty(name="Filename", default="")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (bpy.data.is_saved) and (obj and obj.type == 'ARMATURE')

    def execute(self, context):
        prefs = context.user_preferences.addons[GV.FolderName].preferences
        use_japanese_name = prefs.use_japanese_name
        xml_save_versions = prefs.saveVersions

        directory = bpy.path.abspath("//")
        filepath = os.path.join(directory, self.filename)

        if os.path.isfile(filepath) != True:
            return {'CANCELLED'}

        with open(filepath, "rb") as f:
            from blender2pmxe import pmx
            pmx_data = pmx.Model()
            pmx_data.Load(f)

        # Make XML
        blender_bone_list = import_pmx.make_xml(pmx_data, filepath, use_japanese_name, xml_save_versions)

        #
        # Fix Armature
        #

        arm_obj = context.active_object
        bone_id = {}

        props = context.scene.b2pmxe_properties
        if props.fix_bone_position == True:
            # Set Bone Position
            bone_id = import_pmx.Set_Bone_Position(pmx_data, arm_obj.data, blender_bone_list, fix=True)

            # BoneItem Direction
            bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            bpy.ops.armature.select_all(action='SELECT')
            bpy.ops.b2pmxe.calculate_roll()
            bpy.ops.armature.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

        # Set Bone Status
        bpy.ops.object.mode_set(mode="POSE", toggle=False)
        for (bone_index, data_bone) in enumerate(pmx_data.Bones):
            bone_name = blender_bone_list[bone_index]

            pb = arm_obj.pose.bones.get(bone_name)
            if pb is None:
                continue

            # Set IK
            if data_bone.UseIK != 0:
                pb["IKLoops"] = data_bone.IK.Loops
                pb["IKLimit"] = data_bone.IK.Limit

        bpy.ops.object.mode_set(mode='OBJECT')

        #
        # Fix Materials
        #

        # Rename Images
        for item in bpy.data.images:
            item.name = bpy.path.basename(item.filepath)

        # Add Textures
        textures_dic = {}
        for (tex_index, tex_data) in enumerate(pmx_data.Textures):
            tex_path = os.path.join(directory, tex_data.Path)
            try:
                bpy.ops.image.open(filepath=tex_path)
                textures_dic[tex_index] = bpy.data.textures.new(os.path.basename(tex_path), type='IMAGE')
                textures_dic[tex_index].image = bpy.data.images[os.path.basename(tex_path)]

                # Use Alpha
                textures_dic[tex_index].image.use_alpha = True
                textures_dic[tex_index].image.alpha_mode = 'PREMUL'

            except:
                pass

        # Fix Material
        for mat_data in pmx_data.Materials:
            blender_mat_name = import_pmx.Get_JP_or_EN_Name(mat_data.Name, mat_data.Name_E, use_japanese_name)

            temp_mattrial = bpy.data.materials.get(blender_mat_name)
            if temp_mattrial is not None:
                temp_mattrial.diffuse_color = mat_data.Deffuse.xyz
                temp_mattrial.alpha = mat_data.Deffuse.w
                temp_mattrial.specular_color = mat_data.Specular
                temp_mattrial.specular_hardness = mat_data.Power
                temp_mattrial["Ambient"] = mat_data.Ambient
                temp_mattrial.use_transparency = True

                # Texture
                if mat_data.TextureIndex != -1:

                    if temp_mattrial.texture_slots[0] is None:
                        temp_mattrial.texture_slots.add()

                    temp_mattrial.texture_slots[0].texture = textures_dic.get(mat_data.TextureIndex, None)
                    temp_mattrial.texture_slots[0].texture_coords = "UV"

                    # MMD Settings
                    temp_mattrial.texture_slots[0].use_map_color_diffuse = True
                    temp_mattrial.texture_slots[0].use_map_alpha = True
                    temp_mattrial.texture_slots[0].blend_type = 'MULTIPLY'

                if mat_data.SphereIndex != -1:

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
                        temp_mattrial.texture_slots[1].blend_type = 'MIX'

        # Remove Textures
        for item in bpy.data.textures:
            if item.users == 0:
                bpy.data.textures.remove(item)

        return {'FINISHED'}


class Blender2PmxeEditPanel(bpy.types.Panel):
    bl_label = "Blender2Pmxe Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "armature_edit"

    textDelete = ("Delete _R", "右側を削除")
    textSelect = ("Select _L", "左側を選択")
    textRoll = ("Recalculate Roll", "ロールを再計算")
    textAuto = ("Add Auto Bone", "自動ボーンを追加")
    textTwist = ("Add Twist Bones", "捩りボーンを追加")
    textSleeve = ("Add Sleeve IK Bones", "袖IKボーンを追加")
    textMirror = ("Mirror Bones", "ボーンをX軸ミラー")
    textChain = ("Rename Chain", "縦列をリネーム")
    textPeriod = ("Replace . to _", ". を _ に置換")
    textLR = ("to L/R", "L/Rに変換")
    textNum = ("to Number", "連番に変換")

    def draw(self, context):
        layout = self.layout
        isJP = context.user_preferences.addons[GV.FolderName].preferences.use_japanese_ui

        # Undo & Redo
        # row = layout.row(align=True)
        # row.operator("ed.undo")
        # row.operator("ed.redo")

        # Tools
        layout.label(text="Tools:")
        col = layout.column(align=True)

        row = col.row(align=True)
        row.operator("b2pmxe.delete_right", text=self.textDelete[isJP], icon="X")
        row.operator("b2pmxe.select_left", text=self.textSelect[isJP], icon="BORDER_RECT")

        col.operator("b2pmxe.calculate_roll", text=self.textRoll[isJP], icon="MANIPUL")

        col = layout.column(align=True)
        col.operator("b2pmxe.sleeve_bones", text=self.textSleeve[isJP], icon="CONSTRAINT_DATA")
        col.operator("b2pmxe.twist_bones", text=self.textTwist[isJP], icon="CONSTRAINT_DATA")
        col.operator("b2pmxe.auto_bone", text=self.textAuto[isJP], icon="CONSTRAINT_DATA")

        layout.operator("b2pmxe.mirror_bones", text=self.textMirror[isJP], icon="ALIGN")

        # Rename
        layout.label(text="Name:")
        col = layout.column(align=True)
        col.operator("b2pmxe.rename_chain", text=self.textChain[isJP], icon="LINKED")

        row = col.row(align=True)
        row.operator("b2pmxe.rename_chain_lr", text=self.textLR[isJP], icon="LINKED")
        row.operator("b2pmxe.rename_chain_num", text=self.textNum[isJP], icon="LINKED")

        layout.operator("b2pmxe.replace_period", text=self.textPeriod[isJP], icon="DOT")

        # Display
        layout.label(text="Display:")
        obj = context.object

        split = layout.split()

        col = split.column()
        col.prop(obj.data, "show_names", text="Names")
        col.prop(obj.data, "show_axes", text="Axes")

        col = split.column()
        col.prop(obj, "show_x_ray")
        col.prop(obj.data, "use_mirror_x", text="X Mirror")


class Blender2PmxePosePanel(bpy.types.Panel):

    bl_label = "Blender2Pmxe Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "posemode"

    textTpose = ("to T pose", "T ポーズへ")
    textApose = ("to A pose", "A ポーズへ")
    textClear = ("Clear", "クリア")
    textRebind = ("Rebind", "リバインド")
    textLockLoc = ("Lock Location", "移動不可にする")
    textLockRot = ("Lock Rotation", "回転不可にする")
    textAddLoc = ("Copy Location", "移動+")
    textAddRot = ("Copy Rotation", "回転+")
    textLimit = ("Limit Rotation", "軸制限")

    def draw(self, context):
        layout = self.layout
        isJP = context.user_preferences.addons[GV.FolderName].preferences.use_japanese_ui

        # Undo & Redo
        # row = layout.row(align=True)
        # row.operator("ed.undo")
        # row.operator("ed.redo")

        # Tools
        layout.label(text="Tools:")
        col = layout.column(align=True)

        row = col.row(align=True)
        row.operator("b2pmxe.to_stance", text=self.textTpose[isJP], icon="OUTLINER_DATA_ARMATURE").to_A_stance = False
        row.operator("b2pmxe.to_stance", text=self.textApose[isJP], icon="OUTLINER_DATA_ARMATURE").to_A_stance = True

        row = col.row(align=True)
        row.operator("b2pmxe.clear_pose", text=self.textClear[isJP], icon="LOOP_BACK")
        row.operator("b2pmxe.rebind_armature", text=self.textRebind[isJP], icon="POSE_HLT")

        col = layout.column(align=True)
        col.operator("b2pmxe.lock_location", text=self.textLockLoc[isJP], icon="LOCKED").flag = True
        col.operator("b2pmxe.lock_rotation", text=self.textLockRot[isJP], icon="LOCKED").flag = True

        layout.label(text="Constraints:")

        col = layout.column(align=True)
        col.operator("b2pmxe.add_location", text=self.textAddLoc[isJP], icon="CONSTRAINT_DATA")
        col.operator("b2pmxe.add_rotation", text=self.textAddRot[isJP], icon="CONSTRAINT_DATA")
        col.operator("b2pmxe.limit_rotation", text=self.textLimit[isJP], icon="CONSTRAINT_DATA")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("b2pmxe.add_ik", text="IK", icon="CONSTRAINT_DATA")

        mute_type = True
        for bone in context.active_object.pose.bones:
            for const in bone.constraints:
                if const.type == 'IK':
                    if const.mute == True:
                        mute_type = False
                        break

        row.operator(
            "b2pmxe.mute_ik",
            text="",
            icon="VISIBLE_IPO_ON" if mute_type == True else "VISIBLE_IPO_OFF"
        ).flag = mute_type

        row = col.row(align=True)
        row.prop(context.scene.b2pmxe_properties, "ik", expand=True)

        # Display
        layout.label(text="Display:")
        obj = context.object

        split = layout.split()

        col = split.column()
        col.prop(obj.data, "show_names", text="Names")
        col.prop(obj.data, "show_axes", text="Axes")

        col = split.column()
        col.prop(obj, "show_x_ray")
        col.prop(obj.data, "use_auto_ik")


class Blender2PmxeObjectPanel(bpy.types.Panel):

    bl_label = "Blender2Pmxe Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"

    textSolidify = ("Solidify Edge:", "輪郭線:")
    textXML = ("Make XML File", "XMLファイルを生成")
    textAppend = ("Append Template", "テンプレートをアペンド")
    textTextured = ("BF Culling", "裏面の非表示")
    textShadeless = ("Shadeless", "陰影なし")

    def draw(self, context):
        layout = self.layout
        isJP = context.user_preferences.addons[GV.FolderName].preferences.use_japanese_ui

        ao = context.active_object
        scn = context.scene
        isRender = True
        isView = True
        active_mod = None
        active_mat = None
        color_map = None

        # Get Solidify Edge Flag
        if ao and ao.type == 'MESH':
            # WeightType Group
            color_map = ao.data.vertex_colors.get(GV.WeightTypeName)

            # Modifier
            active_mod = ao.modifiers.get(GV.SolidfyName)
            if active_mod is not None:
                isRender = active_mod.show_render
                isView = active_mod.show_viewport

            # Material
            for mat in ao.data.materials:
                if mat is None:
                    continue
                if mat.name.startswith(GV.SolidfyName):
                    active_mat = mat
                    break

        # Tools
        # Solidify Edge
        box = layout.box()
        row = box.split(percentage=0.6)
        row.label(text=self.textSolidify[isJP], icon='MOD_SOLIDIFY')

        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.operator(
            "b2pmxe.toggle_solidify_render",
            text="",
            icon='RESTRICT_RENDER_OFF' if isRender == True else 'RESTRICT_RENDER_ON'
        )
        row.operator(
            "b2pmxe.toggle_solidify_view",
            text="",
            icon='RESTRICT_VIEW_OFF' if isView == True else 'RESTRICT_VIEW_ON'
        )
        row.operator("b2pmxe.get_solidify_param", text="", icon='EYEDROPPER')

        col = box.column()

        row = col.row(align=True)
        row.label(text="Color")
        row.prop(scn.b2pmxe_properties, "edge_color", text="")

        if active_mat is None:
            row.label(text="")
            row.label(text="", icon='BLANK1')
        else:
            row.prop(active_mat, "diffuse_color", text="")
            row.operator("b2pmxe.set_solidify_mat", text="", icon='STYLUS_PRESSURE')

        row = col.row(align=True)
        row.label(text="Thickness")
        row.prop(scn.b2pmxe_properties, "edge_thickness", text="", slider=True)

        if active_mod is None:
            row.label(text="")
            row.label(text="", icon='BLANK1')
        else:
            row.prop(active_mod, "thickness", text="")
            row.operator("b2pmxe.set_solidify_mod", text="", icon='STYLUS_PRESSURE')

        # Solidify Edge UI Button
        row = box.row(align=True)
        row.operator("b2pmxe.delete_solidify", text="Delete", icon='X')
        row.operator(
            "b2pmxe.add_solidify",
            text="Add" if active_mat is None else "Reload",
            icon='ZOOMIN' if active_mat is None else 'FILE_REFRESH'
        )

        col = layout.column(align=True)

        # Material to Texface
        row = col.row(align=True)
        row.operator("b2pmxe.texface_remove", text="Delete", icon="X")
        row.operator("b2pmxe.material_to_texface", text="Mat to Tex", icon='POTATO')

        # WeightType Group
        row = col.row(align=True)
        row.operator("b2pmxe.delete_weight_type", text="Delete", icon="X")
        row.operator(
            "b2pmxe.create_weight_type",
            text="WeightType" if color_map is None else "Reload",
            icon='COLOR'
        )

        # Add Driver
        row = col.row(align=True)
        row.operator("b2pmxe.add_driver", text="Delete", icon="X").delete = True
        row.operator("b2pmxe.add_driver", text="Add Driver", icon="LOGIC")

        col.operator("b2pmxe.make_xml", text=self.textXML[isJP], icon="FILE_TEXT")
        col.operator("b2pmxe.apply_modifier", icon="FILE_TICK")

        # Append Template
        col = layout.column(align=True)
        col.operator("b2pmxe.append_template", text=self.textAppend[isJP], icon="ARMATURE_DATA")

        row = col.row(align=True)
        row.prop(scn.b2pmxe_properties, "template", expand=True)

        # Shading
        row = layout.row()
        row.operator(
            "b2pmxe.toggle_bf_culling",
            text=self.textTextured[isJP],
            icon="CHECKBOX_HLT" if context.space_data.show_backface_culling == True else "CHECKBOX_DEHLT",
            emboss=False
        )
        row.operator(
            "b2pmxe.toggle_shadeless",
            text=self.textShadeless[isJP],
            icon="CHECKBOX_HLT" if context.space_data.show_textured_shadeless == True else "CHECKBOX_DEHLT",
            emboss=False
        )


# Registration
def menu_func_import(self, context):
    self.layout.operator(ImportBlender2Pmx.bl_idname, text="PMX File for MMD (Extend) (.pmx)", icon='PLUGIN')


def menu_func_export(self, context):
    self.layout.operator(ExportBlender2Pmx.bl_idname, text="PMX File for MMD (Extend) (.pmx)", icon='PLUGIN')


def menu_func_vg(self, context):
    isJP = context.user_preferences.addons[GV.FolderName].preferences.use_japanese_ui
    textMirror = ("Mirror active vertex group (L/R)", "ミラー反転した新しい頂点グループを追加 (L/R)")
    self.layout.separator()
    self.layout.operator("b2pmxe.mirror_vertexgroup", text=textMirror[isJP], icon='ZOOMIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.MESH_MT_vertex_group_specials.append(menu_func_vg)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.MESH_MT_vertex_group_specials.remove(menu_func_vg)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == '__main__':
    register()
