import bpy
from . import global_variable

# global_variable
GV = global_variable.Init()


class B2PmxeSolidifyAdd(bpy.types.Operator):

    '''Add Solidify Edge to selected objects'''
    bl_idname = "b2pmxem.add_solidify"
    bl_label = "Add Solidify Edge"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        scn = context.scene

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            mat_reload = False
            mat_solidfy = None
            mat_index = -1

            # Get Reload Flag
            for index, mat in enumerate(obj.data.materials):
                if mat is None:
                    continue
                if mat.name.startswith(GV.SolidfyName):
                    mat_reload = True
                    mat_solidfy = mat
                    mat_index = index
                    break

            # Change Render Engine
            pre_engine = bpy.context.scene.render.engine
            bpy.context.scene.render.engine = 'BLENDER_RENDER'

            # Add Solidfy Material
            if not mat_reload:
                if len(obj.material_slots) == 0:
                    obj.data.materials.append(bpy.data.materials.new("Material"))

                # Create Solidfy Material
                mtl = bpy.data.materials.new(GV.SolidfyName)
                mtl.diffuse_color = scn.b2pmxem_properties.edge_color
                mtl.use_shadeless = True
                mtl.use_transparency = True
                mtl.use_nodes = True

                # Create Solidfy Material Node
                nodes = mtl.node_tree.nodes
                nodes['Material'].material = mtl

                node_geometry = nodes.new('ShaderNodeGeometry')
                link_input = node_geometry.outputs['Front/Back']
                link_output = nodes['Output'].inputs['Alpha']

                mtl.node_tree.links.new(link_input, link_output)

                # Append
                mtl.user_clear()
                obj.data.materials.append(mtl)

            else:  # mat_reload == True
                obj.data.materials.pop(mat_index)
                obj.data.materials.append(mat_solidfy)

            bpy.context.scene.render.engine = pre_engine

            # Add Solidify Modifire
            mod = obj.modifiers.get(GV.SolidfyName)
            if mod is None:
                mod = obj.modifiers.new(name=GV.SolidfyName, type='SOLIDIFY')
                mod.show_render = False
                mod.thickness = scn.b2pmxem_properties.edge_thickness
                mod.offset = 1.0
                mod.use_flip_normals = True
                mod.use_rim = False
                mod.material_offset = len(obj.material_slots)

            else:
                # Modify Solidify Modifire
                mod.material_offset = len(obj.material_slots)

        return {'FINISHED'}


class B2PmxeSolidifyView(bpy.types.Operator):

    '''Toggle Solidify Edge show_viewport of all objects'''
    bl_idname = "b2pmxem.toggle_solidify_view"
    bl_label = "Toggle Solidify Edge viewport"

    def execute(self, context):
        toggle = {}
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            # Toggle show_viewport
            mod = obj.modifiers.get(GV.SolidfyName)
            if mod is not None:
                mod.show_viewport = toggle.setdefault('modStatus', not mod.show_viewport)

        return {"FINISHED"}


class B2PmxeSolidifyRender(bpy.types.Operator):

    '''Toggle Solidify Edge show_render of all objects'''
    bl_idname = "b2pmxem.toggle_solidify_render"
    bl_label = "Toggle Solidify Edge render"

    def execute(self, context):
        toggle = {}
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue

            # Toggle show_render
            mod = obj.modifiers.get(GV.SolidfyName)
            if mod is not None:
                mod.show_render = toggle.setdefault('modStatus', not mod.show_render)

        return {"FINISHED"}


class B2PmxeSolidifyDelete(bpy.types.Operator):

    '''Delete Solidify Edge of selected objects'''
    bl_idname = "b2pmxem.delete_solidify"
    bl_label = "Delete Solidify Edge"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Delete Solidify Modifire
            mod = obj.modifiers.get(GV.SolidfyName)
            if mod is not None:
                obj.modifiers.remove(mod)

            # Delete Solidify Material
            for index, mat in enumerate(obj.data.materials):
                if mat is None:
                    continue
                if mat.name.startswith(GV.SolidfyName):
                    obj.data.materials.pop(index)
                    if mat.users == 0:
                        bpy.data.materials.remove(mat)
                    break

        return {"FINISHED"}


def solidify_copy(scn, obj, mode, type):
    if type == 'mat':
        # Copy Solidify Material parameter
        for mat in obj.data.materials:
            if mat is None:
                continue
            if mat.name.startswith(GV.SolidfyName):
                if mode == 'get':
                    scn.b2pmxem_properties.edge_color = mat.diffuse_color
                else:  # mode == 'set'
                    mat.diffuse_color = scn.b2pmxem_properties.edge_color
                break

    else:  # type == 'mod'
        # Copy Solidify Modifire parameter
        mod = obj.modifiers.get(GV.SolidfyName)
        if mod is not None:
            if mode == 'get':
                scn.b2pmxem_properties.edge_thickness = mod.thickness
            else:  # mode == 'set'
                mod.thickness = scn.b2pmxem_properties.edge_thickness


class B2PmxeSolidifyGetParam(bpy.types.Operator):

    '''Get Solidify Edge parameter of active object'''
    bl_idname = "b2pmxem.get_solidify_param"
    bl_label = "Get Solidify Edge parameter"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        scn = context.scene
        ao = context.active_object

        # Get Solidify Material parameter
        solidify_copy(scn, ao, mode='get', type='mat')

        # Get Solidify Modifire parameter
        solidify_copy(scn, ao, mode='get', type='mod')

        return {"FINISHED"}


class B2PmxeSolidifySetMat(bpy.types.Operator):

    '''Set Solidify Edge diffuse_color of selected objects'''
    bl_idname = "b2pmxem.set_solidify_mat"
    bl_label = "Set Solidify Edge diffuse_color"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        scn = context.scene

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Set Solidify Material parameter
            solidify_copy(scn, obj, mode='set', type='mat')

        return {"FINISHED"}


class B2PmxeSolidifySetMod(bpy.types.Operator):

    '''Set Solidify Edge thickness of selected objects'''
    bl_idname = "b2pmxem.set_solidify_mod"
    bl_label = "Set Solidify Edge thickness"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        scn = context.scene

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # Set Solidify Modifire parameter
            solidify_copy(scn, obj, mode='set', type='mod')

        return {"FINISHED"}
