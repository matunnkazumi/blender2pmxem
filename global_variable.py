import bpy
import os
import time


class Init(object):

    def __init__(self):
        self.StartTime = 0.0
        self.VertCount = 0

        # Addon Folder Name
        self.FolderName = os.path.basename(os.path.dirname(__file__))

        # Solidify Name (use Modifire and Material)
        self.SolidfyName = "Solidify_Edge"

        # WeightType vertex group name
        self.WeightTypeName = "*WeightType"

        # Left/Right Naming Conventions
        self.TextLR = ('_L', '.L', '_R', '.R')
        self.GetLR_JP = {
            '_L': '\u5de6',
            '.L': '\u5de6',
            '_R': '\u53f3',
            '.R': '\u53f3',
        }

        # Bone Name
        self.TextAnkle = ('ankle', '\u8DB3\u9996')
        self.GetAnkle_JP = {
            'ankle': '\u3064\u307E\u5148',
            '\u8DB3\u9996': '\u3064\u307E\u5148',
        }
        self.GetAnkle_EN = {
            'ankle': 'toe',
            '\u8DB3\u9996': 'toe',
        }

        self.Tip_JP = '\u5148'
        self.Tip_EN = ' tip'

        # Shape Name
        self.ShapeTwist1 = "b2pmxe_shape_twist1"
        self.ShapeTwist2 = "b2pmxe_shape_twist2"
        self.ShapeAuto = "b2pmxe_shape_auto"
        self.ShapeMaster = "b2pmxe_shape_master"
        self.ShapeEyes = "b2pmxe_shape_eyes"

    def SetStartTime(self):
        self.StartTime = time.time()

    def SetVertCount(self, vert_count):
        self.VertCount = vert_count

    def PrintTime(self, filepath, type):
        take_time = time.time() - self.StartTime
        text_type = {
            'import': "Importing",
            'export': "Exporting",
        }

        print(
            "Finished %s: %r in %.3f sec. %d verts." % (
                text_type.get(type, ""),
                bpy.path.basename(filepath),
                take_time,
                self.VertCount
            ))

        bpy.ops.wm.memory_statistics()
