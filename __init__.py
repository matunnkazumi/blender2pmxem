from . import add_function
from . import global_variable
from . import object_applymodifier
from . import import_pmx
from . import export_pmx
from . import validator
from bpy.props import StringProperty
from bpy.props import BoolProperty
from bpy.props import EnumProperty
from bpy.props import FloatProperty
from bpy.props import FloatVectorProperty
from bpy.props import PointerProperty
from bpy.props import IntProperty
from bpy_extras.io_utils import ExportHelper
from bpy_extras.io_utils import ImportHelper
from bpy.app.translations import pgettext_iface as iface_
from glob import glob
import os
import bpy
from itertools import zip_longest

bl_info = {
    "name": "MMD PMX Format (Extend)",
    "author": "matunnkazumi",
    "version": (1, 1, 1),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import-Export PMX model data",
    "warning": "",
    "wiki_url": "https://github.com/matunnkazumi/blender2pmxem/wiki",
    "tracker_url": "https://github.com/matunnkazumi/blender2pmxem/issues",
    "doc_url": "https://blender2pmxem.netlify.app/",
    "category": "Import-Export"
}


# global_variable
GV = global_variable.Init()

translation_dict = {
    "ja_JP": {
        ("*", "Failed to create some shape keys."): "いくつかのシェイプキーの作成に失敗しました。",
        ("*", "maybe cause is merge vertex by Mirror modifier."): "多分原因はミラーモディファイアの頂点結合です。",
        ("*", "Could not use custom split normals data."): "カスタム分割法線データを使用できませんでした。",
        ("*", "Enable 'Auto Smooth' option."): "「自動スムーズ」オプションをONにして下さい。",
        ("*", "or settings of modifier is incorrect."): "またはモディファイアの設定が正しくありません。",
        ("*", "Bone name format incorrect (e.g. %s)"): "ボーン名の書式が正しくありません (例. %s)",
        ("*", "Select %d bones"): "ボーンを%dつ選択してください",
        ("*", "'%s' No parent bone found"): "'%s' 親ボーンが見つかりませんでした",
        ("*", "'%s' No parent bone and child bone found"): "'%s' 親ボーンと子ボーンが見つかりませんでした",
        ("*", "Morph Japanese name must be unique in PMX."): "PMXのモーフの日本語名が重複しています",
        ("*", "Morph English name must be unique in PMX."): "PMXのモーフの英語名が重複しています",
        ("*", "Bone Japanese name must be unique in PMX."): "PMXのボーンの日本語名が重複しています",
        ("*", "Bone English name must be unique in PMX."): "PMXのボーンの英語名が重複しています",
        ("*", "Rigid name must be unique in PMX."): "PMXの剛体の名前が重複しています",
        ("*", "Joint name must be unique in PMX."): "PMXのジョイントの名前が重複しています",
        ("*", "Morph name must be unique in XML."): "XMLのモーフの名前が重複しています",
        ("*", "Bone name must be unique in XML."): "XMLのボーンの名前が重複しています",
        ("*", "Rigid name must be unique in XML."): "XMLの剛体の名前が重複しています",
        ("*", "Joint name must be unique in XML."): "XMLのジョイントの名前が重複しています",
        ("*", "MMD PMX Format (Extend)"): "MMD PMXフォーマット (機能拡張版)",
        ("*", "Import-Export PMX model data"): "PMXモデルをインポート・エクスポートできます",
        ("*", "File > Import-Export"): "ファイル > インポート・エクスポート",
        ("Operator", "Import PMX Data (Extend)"): "PMXインポート (機能拡張版)",
        ("Operator", "Export PMX Data (Extend)"): "PMXエクスポート (機能拡張版)",
        ("*", "Load a MMD PMX File"): "PMXファイルを読み込みます",
        ("*", "Save a MMD PMX File"): "PMXファイルを出力します",
        ("*", "Make a MMD xml file, and update materials"): "PMX出力用のxmlファイルを作成し、マテリアルを更新します",
        ("Operator", "Make XML File"): "XMLファイル作成",
        ("Operator", "Delete _R"): "右側を削除",
        ("Operator", "Select _L"): "左側を選択",
        ("Operator", "Add Auto Bone"): "自動ボーンを追加",
        ("Operator", "Add Twist Bones"): "捩りボーンを追加",
        ("Operator", "Add Sleeve IK Bones"): "袖IKボーンを追加",
        ("Operator", "Mirror Bones"): "ボーンをX軸ミラー",
        ("Operator", "Rename Chain"): "縦列をリネーム",
        ("Operator", "Replace . to _"): ". を _ に置換",
        ("Operator", "to L/R"): "L/Rに変換",
        ("Operator", "to Number"): "連番に変換",
        ("*", "Leg"): "足",
        ("*", "Toe"): "つま先",
        ("*", "Necktie"): "ネクタイ",
        ("Operator", "Add IK"): "IKを追加",
        ("Operator", "to T pose"): "T ポーズへ",
        ("Operator", "to A pose"): "A ポーズへ",
        ("Operator", "Rebind"): "リバインド",
        ("Operator", "Lock Location"): "移動不可にする",
        ("Operator", "Lock Rotation"): "回転不可にする",
        ("Operator", "Add Copy Location"): "移動+を追加",
        ("Operator", "Add Copy Rotation"): "回転+を追加",
        ("Operator", "Add Limit Rotation"): "軸制限を追加",
        ("*", "Solidify Edge:"): "輪郭線:",
        ("Operator", "Append Template Armature"): "アーマチュアの雛形をアペンド",
        ("*", "Mirror active vertex group (L/R)"): "ミラー反転した新しい頂点グループを追加 (L/R)",
        ("Operator", "PMX File for MMD (Extend) (.pmx)"): "PMXファイル for MMD (機能拡張版) (.pmx)",
        ("*", "Chibi"): "ちび",
        ("*", "Shoulder"): "肩",
        ("*", "Arm"): "腕",
        ("*", "Use Japanese Bone name"): "日本語のボーン名を使う",
        ("*", "Use Custom Shape"): "カスタムシェイプを使う",
        ("*", "Append with T stance"): "Tスタンスでアペンドする",
        ("*", "Arm"): "腕",
        ("*", "Number of .xml old versions:"): "xmlファイルのバックアップのバージョン数:",
        ("*", "Angle of T stance and A stance:"): "TスタンスとAスタンスの間の角度:",
        ("*", "Number of Twist link bones:"): "捩りで連動するボーン数:",
        ("*", "Auto Bone influence:"): "自動ボーンの初期影響値:",
        ("*", "Rename Chain threshold:"): "L/Rにリネームする際のしきい値:",
        ("*", "Filename is empty."): "ファイル名が空です。",
        ("*", "Some Texture file not found."): "いくつかのテクスチャファイルが見つかりません。",
        ("*", "See the console log for more information."): "詳細はコンソール・ログを参照してください。",
        ("*", "Adjust bone position"): "ボーンの位置を自動調整する",
        ("*", "Fix Bones:"): "ボーン修正:",
        ("*", "File Select:"): "ファイルを選択:",
        ("*", "Fix"): "修正",
        ("*", "Fix bone position"): "ボーンの位置を修正する",
        ("*", "Transfer"): "転送",
        ("*", "Transfer bones and weights"): "ボーンとウェイトを転送する",
        ("*", "Export finished."): "エクスポートが完了しました",
    }
}


# ------------------------------------------------------------------------
#    store properties in the active scene
# ------------------------------------------------------------------------
class Blender2PmxemProperties(bpy.types.PropertyGroup):

    @classmethod
    def register(cls):
        bpy.types.Scene.b2pmxem_properties = PointerProperty(type=cls)

        def toggle_shadeless(self, context):
            context.space_data.show_textured_shadeless = self.shadeless

            # Toggle Material Shadeless
            for mat in bpy.data.materials:
                if mat:
                    mat.use_shadeless = self.shadeless

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
        cls.shadeless = BoolProperty(
            name="Shadeless",
            update=toggle_shadeless,
            default=False
        )
        cls.make_xml_option = EnumProperty(
            name="Make XML Option",
            items=(
                ('NONE', "None", ""),
                ('POSITION', "Position", "Fix bone position"),
                ('TRANSFER', "Transfer", "Transfer bones and weights"),
            ), default='NONE'
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.b2pmxem_properties


# ------------------------------------------------------------------------


class Blender2PmxemAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    use_T_stance: BoolProperty(  # type: ignore
        name="Append with T stance",
        description="Append template armature with T stance",
        default=False
    )
    use_custom_shape: BoolProperty(  # type: ignore
        name="Use Custom Shape",
        description="Use Custom Shape when creating bones",
        default=False
    )
    use_japanese_name: BoolProperty(  # type: ignore
        name="Use Japanese Bone name",
        description="Append template armature with Japanese bone name",
        default=False
    )

    saveVersions: IntProperty(  # type: ignore
        name="Save Versions",
        default=0,
        min=0,
        max=32
    )

    rotShoulder: FloatProperty(  # type: ignore
        name="Shoulder",
        default=0.261799,
        min=-1.5708,
        max=1.5708,
        unit='ROTATION'
    )
    rotArm: FloatProperty(  # type: ignore
        name="Arm",
        default=0.401426,
        min=-1.5708,
        max=1.5708,
        unit='ROTATION'
    )

    twistBones: IntProperty(  # type: ignore
        name="Number",
        default=3,
        min=0,
        max=3
    )
    autoInfluence: FloatProperty(  # type: ignore
        name="Influence",
        default=0.5,
        min=-1.0,
        max=1.0,
        step=1
    )
    threshold: FloatProperty(  # type: ignore
        name="Threshold",
        default=0.01,
        min=0.0,
        max=1.0,
        step=0.001,
        precision=5
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "use_japanese_name")
        row.prop(self, "use_custom_shape")
        row.prop(self, "use_T_stance")

        col = layout.column_flow(columns=2)
        col.label(text="Number of .xml old versions:")
        col.label(text="Angle of T stance and A stance:")
        col.label(text="Number of Twist link bones:")
        col.label(text="Auto Bone influence:")
        col.label(text="Rename Chain threshold:")

        col.prop(self, "saveVersions")
        row = col.row(align=True)
        row.prop(self, "rotShoulder")
        row.prop(self, "rotArm")
        col.prop(self, "twistBones")
        col.prop(self, "autoInfluence")
        col.prop(self, "threshold")


class B2PMXEM_OT_ImportBlender2Pmx(bpy.types.Operator, ImportHelper):
    '''Load a MMD PMX File'''
    bl_idname = "import.pmx_data_em"
    bl_label = "Import PMX Data (Extend)"
    # bl_options = {'PRESET'}

    filename_ext = ".pmx"
    filter_glob: StringProperty(  # type: ignore
        default="*.pm[dx]",
        options={'HIDDEN'}
    )

    adjust_bone_position: BoolProperty(  # type: ignore
        name="Adjust bone position",
        description="Automatically adjust bone position",
        default=False
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("filter_glob", ))

        prefs = context.preferences.addons[GV.FolderName].preferences
        use_japanese_name = prefs.use_japanese_name

        with open(keywords['filepath'], "rb") as f:
            from .pmx import pmx
            pmx_data = pmx.Model()
            pmx_data.Load(f)

        validate_result = validator.validate_pmx(pmx_data, use_japanese_name)
        if validate_result:
            msg = '\n'.join(validate_result)
            bpy.ops.b2pmxem.multiline_message('INVOKE_DEFAULT',
                                              type='ERROR',
                                              lines=msg)
            return {'CANCELLED'}

        import_pmx.read_pmx_data(context, **keywords)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, "adjust_bone_position")


class B2PMXEM_OT_ExportBlender2Pmx(bpy.types.Operator, ExportHelper):
    '''Save a MMD PMX File'''
    bl_idname = "export.pmx_data_em"
    bl_label = "Export PMX Data (Extend)"
    bl_options = {'PRESET'}

    # ExportHelper mixin class uses this
    filename_ext = ".pmx"
    filter_glob: StringProperty(  # type: ignore
        default="*.pmx",
        options={'HIDDEN'}
    )

    encode_type: EnumProperty(  # type: ignore
        items=(
            ('OPT_Utf-8', "UTF-8", "To use UTF-8 encoding."),
            ('OPT_Utf-16', "UTF-16", "To use UTF-16 encoding."),
        ),
        name="Encode",
        description="Select the encoding to use",
        default='OPT_Utf-16'
    )

    use_mesh_modifiers: BoolProperty(  # type: ignore
        name="Apply Modifiers",
        description="Apply modifiers (Warning, may be slow)",
        default=False,
    )
    use_custom_normals: BoolProperty(  # type: ignore
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
            bpy.ops.b2pmxem.message('INVOKE_DEFAULT', type='ERROR', line1="Filename is empty.")
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
                    mats.pop(index=index)
                    index -= 1
                index += 1

        keywords = self.as_keywords(ignore=("check_existing", "filter_glob", ))

        ret = export_pmx.write_pmx_data(context, **keywords)
        if ret == {'FINISHED'}:
            self.report({'INFO'}, 'Export finished.')
        return ret

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.split(factor=0.3)
        row.label(text="Encode:")
        row.prop(self, "encode_type", text="")

        box.prop(self, "use_mesh_modifiers")
        box.prop(self, "use_custom_normals")


#
#   The error message operator. When invoked, pops up a dialog
#   window with the given message.
#
class B2PMXEM_OT_MessageOperator(bpy.types.Operator):
    bl_idname = "b2pmxem.message"
    bl_label = "B2Pmxem Message"

    type: EnumProperty(  # type: ignore
        items=(
            ('ERROR', "Error", ""),
            ('INFO', "Info", ""),
        ), default='ERROR')
    line1: StringProperty(  # type: ignore
        default=""
    )
    line2: StringProperty(  # type: ignore
        default=""
    )
    line3: StringProperty(  # type: ignore
        default=""
    )
    use_console: BoolProperty(  # type: ignore
        default=False
    )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=360)

    def draw(self, context):
        layout = self.layout

        if self.type == 'ERROR':
            layout.label(text=iface_("Error") + ":", icon='ERROR')
        elif self.type == 'INFO':
            layout.label(text=iface_("Info") + ":", icon='INFO')

        row = layout.split(factor=0.05)
        row.label(text="")
        col = row.column(align=True)
        col.label(text=self.line1)

        type_text = "[{0:s}]".format(self.type)
        print("{0:s} {1:s}".format(type_text, self.line1))

        if self.line2:
            col.label(text=self.line2)
            print("{0:s} {1:s}".format(" " * (len(type_text)), self.line2))
        if self.line3:
            col.label(text=self.line3)
            print("{0:s} {1:s}".format(" " * (len(type_text)), self.line3))
        if self.use_console:
            col.label(text="See the console log for more information.")

        layout.separator()


#
#   The error message operator. When invoked, pops up a dialog
#   window with the given message for multiple lines.
#
class B2PMXEM_OT_MultiLineMessageOperator(bpy.types.Operator):
    bl_idname = "b2pmxem.multiline_message"
    bl_label = "B2Pmxem Multiline Message"

    type: EnumProperty(  # type: ignore
        items=(
            ('ERROR', "Error", ""),
            ('INFO', "Info", ""),
        ), default='ERROR')
    lines: StringProperty(  # type: ignore
        default=""
    )
    use_console: BoolProperty(  # type: ignore
        default=False
    )

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=360)

    def draw(self, context):
        layout = self.layout

        if self.type == 'ERROR':
            layout.label(text=iface_("Error") + ":", icon='ERROR')
        elif self.type == 'INFO':
            layout.label(text=iface_("Info") + ":", icon='INFO')

        row = layout.split(factor=0.05)
        row.label(text="")
        col = row.column(align=True)

        line_list = self.lines.splitlines()
        type_text = "[{0:s}]".format(self.type)

        for msg, pre in zip_longest(line_list, [type_text], fillvalue=" " * (len(type_text))):
            col.label(text=msg)
            print("{0:s} {1:s}".format(pre, msg))

        if self.use_console:
            col.label(text="See the console log for more information.")

        layout.separator()


class B2PMXEM_OT_MakeXML(bpy.types.Operator):
    '''Make a MMD xml file, and update materials'''
    bl_idname = "b2pmxem.make_xml"
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
        row = layout.split(factor=0.01)
        row.label(text="")

        split = row.split(factor=0.968)
        col = split.column(align=True)

        col.label(text="Fix Bones:")
        props = context.scene.b2pmxem_properties
        row = col.row(align=True)
        row.prop(props, "make_xml_option", expand=True)
        col.separator()

        col.label(text="File Select:")
        for file in files:
            col.operator(B2PMXEM_OT_SaveAsXML.bl_idname, text=file).filename = file

        layout.separator()


class B2PMXEM_OT_SaveAsXML(bpy.types.Operator):
    '''Save As a MMD XML File.'''
    bl_idname = "b2pmxem.save_as_xml"
    bl_label = "Save As XML File"
    bl_options = {'UNDO'}

    filename: StringProperty(  # type: ignore
        name="Filename",
        default=""
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (bpy.data.is_saved) and (obj and obj.type == 'ARMATURE')

    def execute(self, context):
        prefs = context.preferences.addons[GV.FolderName].preferences
        use_japanese_name = prefs.use_japanese_name
        xml_save_versions = prefs.saveVersions
        props = context.scene.b2pmxem_properties
        arm = context.active_object

        directory = bpy.path.abspath("//")
        filepath = os.path.join(directory, self.filename)

        if not os.path.isfile(filepath):
            return {'CANCELLED'}

        with open(filepath, "rb") as f:
            from .pmx import pmx
            pmx_data = pmx.Model()
            pmx_data.Load(f)

        validate_result = validator.validate_pmx(pmx_data, use_japanese_name)
        if validate_result:
            msg = '\n'.join(validate_result)
            bpy.ops.b2pmxem.multiline_message('INVOKE_DEFAULT',
                                              type='ERROR',
                                              lines=msg)
            return {'CANCELLED'}

        if props.make_xml_option == 'TRANSFER':
            import_arm, import_obj = import_pmx.read_pmx_data(context, filepath, bone_transfer=True)
            arm.data = import_arm.data

            # Set active object
            def set_active(obj):
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj

            set_active(import_obj)

            # Select object
            def select_object(obj):
                # Show object
                obj.hide_viewport = False
                obj.hide_select = False

                obj.select_set(True)

            for obj in context.collection.objects:
                if obj.find_armature() == arm:
                    select_object(obj)

                    # Data Transfer
                    bpy.ops.object.data_transfer(data_type='VGROUP_WEIGHTS',
                                                 vert_mapping='NEAREST',
                                                 ray_radius=0,
                                                 layers_select_src='ALL',
                                                 layers_select_dst='NAME',
                                                 mix_mode='REPLACE',
                                                 mix_factor=1)

            # Unlink
            context.collection.objects.unlink(import_obj)
            context.collection.objects.unlink(import_arm)

            set_active(arm)

        else:
            # Make XML
            blender_bone_list = import_pmx.make_xml(pmx_data, filepath, use_japanese_name, xml_save_versions)

            # --------------------
            # Fix Armature
            # --------------------
            arm_obj = context.active_object

            if props.make_xml_option == 'POSITION':
                # Set Bone Position
                import_pmx.Set_Bone_Position(pmx_data, arm_obj.data, blender_bone_list, fix=True)

                # BoneItem Direction
                bpy.ops.object.mode_set(mode="EDIT", toggle=False)
                bpy.ops.armature.select_all(action='SELECT')
                bpy.ops.b2pmxem.calculate_roll()
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

        return {'FINISHED'}


class B2PMXEM_PT_EditPanel(bpy.types.Panel):
    bl_label = "Blender2Pmxem Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "armature_edit"

    def draw(self, context):
        layout = self.layout

        # Tools
        col = layout.column(align=True)
        col.label(text="Tools:")

        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_DeleteRight.bl_idname, text="Delete _R", icon="X")
        row.operator(add_function.B2PMXEM_OT_SelectLeft.bl_idname, text="Select _L", icon="UV_SYNC_SELECT")

        col.operator(add_function.B2PMXEM_OT_RecalculateRoll.bl_idname, icon="EMPTY_DATA")
        col.separator()
        col.operator(add_function.B2PMXEM_OT_SleeveBones.bl_idname, icon="LIBRARY_DATA_DIRECT")
        col.operator(add_function.B2PMXEM_OT_TwistBones.bl_idname, icon="LIBRARY_DATA_DIRECT")
        col.operator(add_function.B2PMXEM_OT_AutoBone.bl_idname, icon="LIBRARY_DATA_DIRECT")
        col.separator()
        col.operator(add_function.B2PMXEM_OT_MirrorBones.bl_idname, icon="MOD_MIRROR")

        # Rename
        col = layout.column(align=True)
        col.label(text="Name:")
        col.operator(add_function.B2PMXEM_OT_RenameChain.bl_idname, icon="LINKED")

        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_RenameChainToLR.bl_idname, text="to L/R", icon="LINKED")
        row.operator(add_function.B2PMXEM_OT_RenameChainToNum.bl_idname, text="to Number", icon="LINKED")
        col.separator()
        col.operator(add_function.B2PMXEM_OT_ReplacePeriod.bl_idname, text="Replace . to _", icon="DOT")

        # Display
        obj = context.object
        col = layout.column(align=True)
        col.label(text="Display:")

        col = col.column_flow(columns=2)
        col.prop(obj.data, "show_names", text="Name")
        col.prop(obj.data, "show_axes", text="Axis")
        col.prop(obj, "show_in_front")
        col.prop(obj.data, "use_mirror_x", text="X Mirror")


class B2PMXEM_PT_PosePanel(bpy.types.Panel):
    bl_label = "Blender2Pmxem Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "posemode"

    def draw(self, context):
        layout = self.layout

        # Tools
        col = layout.column(align=True)
        col.label(text="Tools:")

        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_ToStance.bl_idname, text="to T pose",
                     icon="OUTLINER_DATA_ARMATURE").to_A_stance = False
        row.operator(add_function.B2PMXEM_OT_ToStance.bl_idname, text="to A pose",
                     icon="OUTLINER_DATA_ARMATURE").to_A_stance = True

        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_ClearPose.bl_idname, text="Clear", icon="LOOP_BACK")
        row.operator(add_function.B2PMXEM_OT_RebindArmature.bl_idname, text="Rebind", icon="POSE_HLT")
        col.separator()
        col.operator(add_function.B2PMXEM_OT_LockLoc.bl_idname, icon="LOCKED").flag = True
        col.operator(add_function.B2PMXEM_OT_LockRot.bl_idname, icon="LOCKED").flag = True

        col = layout.column(align=True)
        col.label(text="Constraints:")

        col.operator(add_function.B2PMXEM_OT_AddCopyLoc.bl_idname, icon="LIBRARY_DATA_DIRECT")
        col.operator(add_function.B2PMXEM_OT_AddCopyRot.bl_idname, icon="LIBRARY_DATA_DIRECT")
        col.operator(add_function.B2PMXEM_OT_AddLimit.bl_idname, icon="LIBRARY_DATA_DIRECT")

        row = col.row(align=True)
        row.operator_menu_enum(add_function.B2PMXEM_OT_AddIK.bl_idname, 'type', icon="LIBRARY_DATA_DIRECT")

        mute_type = True
        for bone in context.active_object.pose.bones:
            for const in bone.constraints:
                if const.type == 'IK':
                    if const.mute:
                        mute_type = False
                        break

        row.operator(
            add_function.B2PMXEM_OT_MuteIK.bl_idname,
            text="",
            icon="HIDE_OFF" if mute_type else "HIDE_ON"
        ).flag = mute_type

        # Display
        obj = context.object
        col = layout.column(align=True)
        col.label(text="Display:")

        col = col.column_flow(columns=2)
        col.prop(obj.data, "show_names", text="Name")
        col.prop(obj.data, "show_axes", text="Axis")
        col.prop(obj, "show_in_front")
        col.prop(obj.pose, "use_auto_ik")


class B2PMXEM_PT_ObjectPanel(bpy.types.Panel):
    bl_label = "Blender2Pmxem Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        ao = context.active_object
        color_map = None

        # Get Solidify Edge Flag
        if ao and ao.type == 'MESH':
            # WeightType Group
            color_map = ao.data.vertex_colors.get(GV.WeightTypeName)

        # Tools

        col = layout.column(align=True)

        # WeightType Group
        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_DeleteWeightType.bl_idname, text="Delete", icon="X")
        row.operator(
            add_function.B2PMXEM_OT_CreateWeightType.bl_idname,
            text="WeightType" if color_map is None else "Reload",
            icon='COLOR'
        )

        # Add Driver
        row = col.row(align=True)
        row.operator(add_function.B2PMXEM_OT_AddDriver.bl_idname, text="Delete", icon="X").delete = True
        row.operator(add_function.B2PMXEM_OT_AddDriver.bl_idname, text="Add Driver", icon="DRIVER")

        col.operator(B2PMXEM_OT_MakeXML.bl_idname, icon="FILE_TEXT")
        col.operator(object_applymodifier.B2PMXEM_OT_ApplyModifier.bl_idname, icon="FILE_TICK")
        col.separator()

        # Append Template
        col.operator_menu_enum(add_function.B2PMXEM_OT_AppendTemplate.bl_idname, 'type', icon="ARMATURE_DATA")


# Registration
def menu_func_import(self, context):
    self.layout.operator(B2PMXEM_OT_ImportBlender2Pmx.bl_idname, text="PMX File for MMD (Extend) (.pmx)", icon='PLUGIN')


def menu_func_export(self, context):
    self.layout.operator(B2PMXEM_OT_ExportBlender2Pmx.bl_idname, text="PMX File for MMD (Extend) (.pmx)", icon='PLUGIN')


def menu_func_vg(self, context):
    self.layout.separator()
    self.layout.operator(add_function.B2PMXEM_OT_MirrorVertexGroup.bl_idname,
                         text=iface_("Mirror active vertex group (L/R)"), icon='ZOOM_IN')


classes = [
    add_function.B2PMXEM_OT_MirrorVertexGroup,
    add_function.B2PMXEM_OT_RecalculateRoll,
    add_function.B2PMXEM_OT_AddDriver,
    add_function.B2PMXEM_OT_CreateWeightType,
    add_function.B2PMXEM_OT_DeleteWeightType,
    add_function.B2PMXEM_OT_AppendTemplate,
    add_function.B2PMXEM_OT_ToStance,
    add_function.B2PMXEM_OT_DeleteRight,
    add_function.B2PMXEM_OT_SelectLeft,
    add_function.B2PMXEM_OT_ReplacePeriod,
    add_function.B2PMXEM_OT_RenameChain,
    add_function.B2PMXEM_OT_RenameChainToLR,
    add_function.B2PMXEM_OT_RenameChainToNum,
    add_function.B2PMXEM_OT_MirrorBones,
    add_function.B2PMXEM_OT_AutoBone,
    add_function.B2PMXEM_OT_SleeveBones,
    add_function.B2PMXEM_OT_TwistBones,
    add_function.B2PMXEM_OT_ClearPose,
    add_function.B2PMXEM_OT_RebindArmature,
    add_function.B2PMXEM_OT_LockRot,
    add_function.B2PMXEM_OT_LockLoc,
    add_function.B2PMXEM_OT_AddCopyLoc,
    add_function.B2PMXEM_OT_AddCopyRot,
    add_function.B2PMXEM_OT_AddLimit,
    add_function.B2PMXEM_OT_AddIK,
    add_function.B2PMXEM_OT_MuteIK,
    object_applymodifier.B2PMXEM_OT_ApplyModifier,
    Blender2PmxemAddonPreferences,
    Blender2PmxemProperties,
    B2PMXEM_OT_ExportBlender2Pmx,
    B2PMXEM_OT_ImportBlender2Pmx,
    B2PMXEM_OT_MakeXML,
    B2PMXEM_OT_SaveAsXML,
    B2PMXEM_OT_MessageOperator,
    B2PMXEM_OT_MultiLineMessageOperator,
    B2PMXEM_PT_EditPanel,
    B2PMXEM_PT_PosePanel,
    B2PMXEM_PT_ObjectPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.MESH_MT_vertex_group_context_menu.append(menu_func_vg)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.MESH_MT_vertex_group_context_menu.remove(menu_func_vg)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.app.translations.unregister(__name__)


if __name__ == '__main__':
    register()
