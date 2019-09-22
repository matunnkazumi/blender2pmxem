#  (c) 2010 Michael Williamson (michaelw)
#  ported from original by Michael Williamson

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
This script has several functions and operators, grouped for convenience:

* remove texface
    removes all texface of the all object.

* material to texface
    transfers material assignments to the UV editor. This is useful if you
    assigned materials in the properties editor, as it will use the already
    set up materials to assign the UV images per-face. It will use the first
    image texture (texture_slots[0]).

"""


import bpy


def mat_to_texface():
    # assigns the first image in each material to the polygons in the active
    # uvlayer for all selected objects

    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue

        # build a list of images, one per material
        images = []

        # get the textures from the mats
        for m in ob.material_slots:
            if m.material is None:
                images.append(None)
                continue

            gotimage = False
            t = m.material.texture_slots[0]

            if t is not None:
                tex = t.texture

                if tex is not None and tex.type == 'IMAGE':
                    images.append(tex.image)
                    gotimage = True

            # image not found
            if not gotimage:
                images.append(None)

        # doesn't have material
        if len(images) == 0:
            continue

        # now we have the images
        # apply them to the uvlayer

        me = ob.data

        # got uvs?
        if not me.uv_textures:
            me.uv_textures.new()

        # get active uvlayer
        uvtex = me.uv_textures.active.data

        for f in me.polygons:
            # check that material had an image!
            img = images[f.material_index]
            uvtex[f.index].image = img

        me.update()


def remove_texface():

    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue

        me = ob.data

        # got uvs?
        if not me.uv_textures:
            continue

        # get active uvlayer
        uvtex = me.uv_textures.active.data

        for f in uvtex:
            f.image = None

        me.update()


# -----------------------------------------------------------------------------
# operator classes:

class VIEW3D_OT_material_to_texface(bpy.types.Operator):

    """Transfer material assignments to UV editor"""
    bl_idname = "b2pmxe.material_to_texface"
    bl_label = "Material Images to Texface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mat_to_texface()
        return {'FINISHED'}


class VIEW3D_OT_texface_remove(bpy.types.Operator):

    """Remove all texface from all objects"""
    bl_idname = "b2pmxe.texface_remove"
    bl_label = "Remove All Texface"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        remove_texface()
        return {'FINISHED'}
