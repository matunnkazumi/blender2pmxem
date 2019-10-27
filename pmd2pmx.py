#!/bin/python
# -*- coding utf_8 -*-

#
# pmx.py : 20111204 v 1.0
#
import mathutils
import os

DEBUG = False

J_Knee = "\u3072\u3056"

sys_toons = {"toon01.bmp": 0, "toon02.bmp": 1, "toon03.bmp": 2, "toon04.bmp": 3, "toon05.bmp": 4,
             "toon06.bmp": 5, "toon07.bmp": 6, "toon08.bmp": 7, "toon09.bmp": 8, "toon10.bmp": 9}


def Echo(data):
    if DEBUG:
        print(data)


def Convert(d_pmd):

    from blender2pmxe import pmx
    from blender2pmxe import pmd

    d_pmx = pmx.Model()

    Echo("Convert Pmx ")

    # Name
    d_pmx.Name = d_pmd.Header.Name
    d_pmx.Name_E = d_pmd.Header.Name_E

    # Comment
    d_pmx.Comment = d_pmd.Header.Comment
    d_pmx.Comment_E = d_pmd.Header.Comment_E

    # Model Data
    # Vertex
    Echo("Vertex...")
    for data in d_pmd.Vertices:
        self = pmx.PMVertex()
        self.Position = data.Pos
        self.Normal = data.No
        self.UV = data.Uv

        # WeightType |[0:BDEF1 1:BDEF2 2:BDEF4 3:SDEF]
        self.Type = 1
        self.AppendUV = []

        # Weidht
        a = data.Bone[0]
        b = data.Bone[1]

        if a == b or data.Weight == 100:
            self.Type = 0
            self.Bones = [a]
            self.Weights = []

        elif data.Weight == 0:
            self.Type = 0
            self.Bones = [b]
            self.Weights = []

        else:
            self.Bones = data.Bone
            self.Weights = [data.Weight / 100.0]

        # Edge
        self.EdgeSize = 1.0 if data.Flag == 1 else 0.0
        d_pmx.Vertices.append(self)

    # Face
    Echo("Face...")
    for data in d_pmd.Polys:
        d_pmx.Faces.append(data.Index)

    # Texture
    Echo("Texture...")
    tex_dic = {}
    d_pmx.Textures = []

    # Material
    Echo("Material...")
    for i, data in enumerate(d_pmd.Materials):
        self = pmx.PMMaterial()
        self.Name = "mat%02d" % i
        self.Name_E = self.Name
        self.Deffuse = data.Deffuse
        self.Specular = data.Specler
        self.Power = data.Shiness
        self.Ambient = data.Ambient

        # Flags
        self.Both = 1 if data.Deffuse.w < 1.0 else 0
        self.GroundShadow = data.Edge
        self.DropShadow = 0 if int(data.Deffuse.w * 100) == 98 else 1
        self.OnShadow = 1
        self.OnEdge = data.Edge

        # Edge
        self.EdgeColor = mathutils.Vector((0, 0, 0, 1))
        self.EdgeSize = 1.0

        # Texture
        self.TextureIndex = -1
        self.SphereIndex = -1
        self.SphereType = 0  # [0:None 1:Multi 2:Add 3:SubTexture]

        if data.Texture != "":
            if data.Texture not in tex_dic.keys():
                newid = len(tex_dic)
                tex_dic[data.Texture] = newid
                new_tex = pmx.PMTexture()
                new_tex.Path = data.Texture
                d_pmx.Textures.append(new_tex)

            self.TextureIndex = tex_dic[data.Texture]

        if data.Sphere != "":
            if data.Sphere not in tex_dic.keys():
                newid = len(tex_dic)
                tex_dic[data.Sphere] = newid
                new_tex = pmx.PMTexture()
                new_tex.Path = data.Sphere
                d_pmx.Textures.append(new_tex)

            self.SphereIndex = tex_dic[data.Sphere]
            root, ext = os.path.splitext(data.Sphere)

            if ext == ".sph":
                self.SphereType = 1

            elif ext == ".spa":
                self.SphereType = 2

        # Toon
        self.UseSystemToon = 1
        self.ToonIndex = 0

        if data.Toon < 0:
            self.UseSystemToon = 0
            self.ToonIndex = -1

        else:
            toon_name = d_pmd.ToonName[data.Toon]
            if toon_name in sys_toons.keys():
                self.ToonIndex = sys_toons[toon_name]

            elif toon_name != "":
                self.UseSystemToon = 0
                if toon_name not in tex_dic.keys():
                    newid = len(tex_dic)
                    tex_dic[toon_name] = newid
                    new_tex = pmx.PMTexture()
                    new_tex.Path = toon_name
                    d_pmx.Textures.append(new_tex)

                self.ToonIndex = tex_dic[toon_name]

        # Comment
        self.Comment = ""

        # FaceLength
        self.FaceLength = data.VertCount

        d_pmx.Materials.append(self)

    # Bone
    Echo("Bone...")
    for data in d_pmd.Bones:
        self = pmx.PMBone()
        self.Name = data.Name
        self.Name_E = data.Name_E

        self.Position = data.Pos
        self.Parent = data.Parent
        self.Level = 0

        self.ToConnectType = 1  # [@:Offset 1:Bone]
        self.ChildIndex = data.To

        if data.Kind == 0:
            self.Movable = 0

        elif data.Kind == 1:
            pass

        elif data.Kind == 2:
            self.UseIK = 1

        elif data.Kind == 3:
            self.Rotatable = 0
            self.Movable = 0

        elif data.Kind == 4:
            self.Movable = 0

        elif data.Kind == 5:
            self.AdditionalRotation = 1
            self.AdditionalBoneIndex = data.KindNo
            self.AdditionalPower = 1.0

        elif data.Kind == 6:
            self.Rotatable = 0
            self.Movable = 0
            self.Visible = 0

        elif data.Kind == 7:
            self.Rotatable = 0
            self.Movable = 0
            self.Visible = 0

        elif data.Kind == 8:
            self.Movable = 0
            self.UseFixedAxis = 1
            self.FixedAxis = d_pmd.Bones[data.To].Pos - data.Pos

        elif data.Kind == 9:
            self.Movable = 0
            self.Visible = 0
            self.AdditionalRotation = 1
            self.AdditionalBoneIndex = data.To
            self.ChildIndex = d_pmd.Bones[data.To].To
            self.AdditionalPower = data.KindNo / 100.0

        d_pmx.Bones.append(self)

    # IK
    for data in d_pmd.IKs:
        self = pmx.PMIK()
        self.TargetIndex = data.End
        self.Loops = data.P1
        self.Limit = data.P2 * 4
        self.Member = []

        for node in data.Node:
            self1 = pmx.PMIKLink()
            self1.Index = node
            if d_pmd.Bones[node].Name.find(J_Knee) > 0:
                self1.UseLimit = 1
                self1.UpperLimit = mathutils.Vector((0, 0, 0))
                self1.LowerLimit = mathutils.Vector((-180, 0, 0))

            self.Member.append(self1)

        d_pmx.Bones[data.Target].UseIK = 1
        d_pmx.Bones[data.Target].IK = self

    # Morph
    Echo("Morph...")
    basis = pmd.PMDSkin()
    for data in d_pmd.Skins:
        if data.Type == 0:
            basis = data
            break

    for data in d_pmd.Skins:
        if data.Type == 0:
            continue

        self = pmx.PMMorph()
        self.Name = data.Name
        self.Name_E = data.Name_E
        self.Type = 1  # Vertex Morph
        self.Panel = data.Type
        self.Offsets = []

        for v in data.Verts:
            self1 = pmx.PMMorphOffset()
            self1.Index = basis.Verts[v.Index].Index
            # self1.Index = v.Index
            self1.Move = v.Pos
            self.Offsets.append(self1)

        d_pmx.Morphs.append(self)

    # Display
    # DisplayFrame
    Echo("Displayframe...")
    pmx_label0 = pmx.PMDisplayFrame()
    pmx_label0.Name = "Root"
    pmx_label0.Name_E = "Root"
    pmx_label0.Type = 1
    pmx_label0.Members = [[0, 0]]

    d_pmx.DisplayFrames.append(pmx_label0)

    pmx_label1 = pmx.PMDisplayFrame()
    pmx_label1.Name = "\u8868\u60C5"
    pmx_label1.Name_E = "Exp"
    pmx_label1.Type = 1
    pmx_label1.Members = []

    for index, data in enumerate(d_pmd.SkinIndexs):
        pmx_label1.Members.append([1, data.Index - 1])
        d_pmx.Morphs[index].Name_E = data.Name_E

    d_pmx.DisplayFrames.append(pmx_label1)

    for data in d_pmd.DispNames:
        self = pmx.PMDisplayFrame()
        self.Name = data.Name
        self.Name_E = data.Name_E
        self.Type = 0  # [0:Normal 1:Special]
        self.Members = []

        d_pmx.DisplayFrames.append(self)

    for data in d_pmd.BoneIndexs:
        d_pmx.DisplayFrames[data.Group + 1].Members.append([0, data.Bone])

    # Physics
    # Rigid
    Echo("Regid...")
    for data in d_pmd.Rigids:
        self = pmx.PMRigid()
        self.Name = data.Name
        self.Name_E = data.Name
        self.Bone = data.Bone
        self.Group = data.Group
        self.NoCollision = data.NoCollision
        self.BoundType = data.BoundType  # [0:Sphere 1:Box 2:Capsule]
        self.Size = mathutils.Vector(data.Size)

        if data.Bone < 0:
            self.Position = data.Pos

        else:
            self.Position = data.Pos + d_pmd.Bones[data.Bone].Pos

        self.Rotate = data.Rot
        self.Mass = data.Mass
        self.PosLoss = data.PosLoss
        self.RotLoss = data.RotLoss
        self.OpPos = data.OpPos
        self.Friction = data.Friction
        self.PhysicalType = data.PhysicalType

        d_pmx.Rigids.append(self)

    # Joint
    Echo("Joint...")
    for data in d_pmd.Joints:
        self = pmx.PMJoint()
        self.Name = data.Name
        self.Name_E = data.Name
        self.Type = 0  # [0:Spring6DOF] Fixed
        self.Parent = data.Parent
        self.Child = data.Child
        self.Position = data.Pos
        self.Rotate = data.Rot
        self.PosLowerLimit = data.PosLowerLimit
        self.PosUpperLimit = data.PosUpperLimit
        self.RotLowerLimit = data.RotLowerLimit
        self.RotUpperLimit = data.RotUpperLimit
        self.PosSpring = data.PosSpring
        self.RotSpring = data.RotSpring

        d_pmx.Joints.append(self)

    return d_pmx
