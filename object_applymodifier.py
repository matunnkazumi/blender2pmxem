# The MIT License (MIT)*************
#
#
# Copyright (c) 2013 mato.sus304(mato.sus304@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#**********************************

import bpy
from blender2pmxe import global_variable

# global_variable
GV = global_variable.Init()


######################################################

class Init(object):

    def __init__(self):
        self.MasterObj = None

    def Set_MasterObj(self, scn, target_obj, shape_keys):
        # has shape_keys
        if shape_keys is not None:
            target_obj.show_only_shape_key = True
            target_obj.active_shape_key_index = 0

            tmp_mesh = target_obj.to_mesh(scn, True, 'PREVIEW')
            self.MasterObj = bpy.data.objects.new(tmp_mesh.name, tmp_mesh)

            # add 'basis' shape_key
            tmp_name = shape_keys.key_blocks[0].name
            self.MasterObj.shape_key_add(tmp_name, False)
        # no shape_key
        else:
            tmp_mesh = target_obj.to_mesh(scn, True, 'PREVIEW')
            self.MasterObj = bpy.data.objects.new(tmp_mesh.name, tmp_mesh)

    def Set_AnimData(self, pre_anim_data):
        if pre_anim_data is not None:
            properties = [p.identifier for p in pre_anim_data.bl_rna.properties if not p.is_readonly]
            anim_data = self.MasterObj.data.shape_keys.animation_data_create()

            # copy keyframes
            for prop in properties:
                setattr(anim_data, prop, getattr(pre_anim_data, prop))

    # Set show_viewport flag (for 'object.to_mesh')
    def Set_Apply_All(self, target_obj):
        for mod in target_obj.modifiers:
            if mod.type == 'SOLIDIFY' and mod.name == GV.SolidfyName:
                mod.show_viewport = False
                continue

            if mod.type == 'ARMATURE':
                mod.show_viewport = False
                continue

            if mod.type == 'EDGE_SPLIT':
                mod.use_edge_angle = False

            mod.show_viewport = True

    # Set show_viewport flag (for 'object.to_mesh')
    def Set_Apply_Target(self, target_obj, target_modifiers):
        for mod in target_obj.modifiers:
            if mod.type in target_modifiers:
                mod.show_viewport = True
                continue

            mod.show_viewport = False

    def Count_Modifiers(self, target_obj):
        count = 0
        for mod in target_obj.modifiers:
            if mod.type == 'SOLIDIFY' and mod.name == GV.SolidfyName:
                continue

            if mod.type == 'ARMATURE':
                continue

            count += 1

        return count

    def Get_Apply_Mesh(self, target_obj, target_modifiers=None):
        scn = bpy.context.scene

        # count modifiers
        if target_modifiers is None:
            mod_count = self.Count_Modifiers(target_obj)

            if mod_count == 0:
                return target_obj.data

        # Get pre flag
        pre_only_shape = target_obj.show_only_shape_key
        pre_show_viewport = [mod.show_viewport for mod in target_obj.modifiers]
        pre_index = target_obj.active_shape_key_index
        pre_anim_data = None

        # Set show_viewport flag
        if target_modifiers is None:
            self.Set_Apply_All(target_obj)

        else:
            self.Set_Apply_Target(target_obj, target_modifiers)

        shape_keys = target_obj.data.shape_keys

        self.Set_MasterObj(scn, target_obj, shape_keys)

        # has shape_keys
        if shape_keys is not None:
            vert_array = [0 for x in range(len(self.MasterObj.data.vertices) * 3)]
            pre_anim_data = shape_keys.animation_data

            for i in range(1, len(shape_keys.key_blocks)):
                target_obj.active_shape_key_index = i

                # add shape_keys
                tmp_name = shape_keys.key_blocks[i].name
                tmp_block = self.MasterObj.shape_key_add(tmp_name, False)

                tmp_mesh = target_obj.to_mesh(scn, True, 'PREVIEW')

                # modify shape_keys
                tmp_mesh.vertices.foreach_get('co', vert_array)
                tmp_block.data.foreach_set('co', vert_array)

                # remove tmp_mesh
                bpy.data.meshes.remove(tmp_mesh)

        # Set pre flag
        target_obj.show_only_shape_key = pre_only_shape
        target_obj.modifiers.foreach_set('show_viewport', pre_show_viewport)
        target_obj.active_shape_key_index = pre_index

        # Set copy keyframes
        self.Set_AnimData(pre_anim_data)

        return self.MasterObj.data

    def Remove(self):
        if self.MasterObj is None:
            return

        tmp_mesh = self.MasterObj.data
        bpy.data.objects.remove(self.MasterObj)
        self.MasterObj = None

        if tmp_mesh.users == 0:
            bpy.data.meshes.remove(tmp_mesh)


class B2PmxeApplyModifier(bpy.types.Operator):

    '''Apply Modifier to selected mesh object'''
    bl_idname = "b2pmxe.apply_modifier"
    bl_label = "Apply Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    def clear_modifiers(self, obj):
        for mod in obj.modifiers:
            if mod.type == 'SOLIDIFY' and mod.name == GV.SolidfyName:
                continue

            if mod.type == 'ARMATURE':
                continue

            obj.modifiers.remove(mod)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        apply_mod = Init()

        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            # get modifier applied mesh
            new_mesh = apply_mod.Get_Apply_Mesh(obj)

            # same mesh
            if new_mesh == obj.data:
                continue

            # rename data
            tmp_name = obj.data.name
            old_mesh = obj.data
            old_mesh.name = tmp_name + '_'
            new_mesh.name = tmp_name

            # set modifier applied mesh
            obj.data = new_mesh

            # clear modifiers
            self.clear_modifiers(obj)

            # remove old mesh
            bpy.data.meshes.remove(old_mesh)
            apply_mod.Remove()

        return {'FINISHED'}
