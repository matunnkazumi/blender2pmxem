#!/bin/python
# -*- coding utf_8 -*-

#
# pmx.py : 20140104 v 1.1
#
import mathutils
from struct import calcsize
from struct import unpack
from struct import pack

DEBUG = False


def Echo(data):
    if DEBUG:
        print(data)


def ReadStruct(f, format):  # Read Struct
    try:
        length = calcsize(format)
        dat = f.read(length)
        p = unpack(format, dat)
        if len(p) < 2:
            q = p[0]
            if format == "B" and q == 255:
                return -1
            if format == "H" and q == 65535:
                return -1
            return q
        else:
            return p
    except:
        return 0


def WriteStruct(f, format, data):  # Write Struct
    if isinstance(data, tuple):
        f.write(pack(format, *data))
    else:
        if format == "B" and data == -1:
            f.write(pack(format, 255))
        elif format == "H" and data == -1:
            f.write(pack(format, 65535))
        else:
            f.write(pack(format, data))


def ReadString(f, mode):  # Read String
    length = ReadStruct(f, "i")
    if length == 0:
        return ""
    data = ReadStruct(f, str(length) + "s")
    if mode.Encode == 0:
        return data.decode("utf-16", 'ignore')
    if mode.Encode == 1:
        return data.decode("utf-8", 'ignore')
    return data.decode('shift_jis', 'ignore')


def WriteString(f, mode, data):  # Write String
    if mode.Encode == 0:
        temp = data.encode("utf-16", 'ignore')[2:]
    elif mode.Encode == 1:
        temp = data.encode("utf-8", 'ignore')
    length = len(temp)
    WriteStruct(f, "i", length)
    if length != 0:
        WriteStruct(f, str(length) + "s", temp)


# def StringRemoveNull(string):
#    for pos , w in enumerate(string):
# if w == 0:#"\x00":
#            return string[:pos]
#    return string
#
# def DecodeSjis(string):
#    return string.decode('shift_jis','ignore')
#
# def EncodeSjis(string):
#    return string.encode('shift_jis','ignore')


class ModelStatus(object):

    def __init__(self):
        #  Magic                   | [0:PMD 1:PMX]
        self.Magic = 0

        #  Version                 | float[PMD:fixed 1.0 PMX:2.0/2.1]
        self.Version = 1.0

        #  Index byte Size
        #  [0] - Encode            | [0:UTF16 1:UTF8 255:shift_jis
        #  [1] - AppendUVCount	   | [0:4]
        #  [2] - VertexIndexSize   | ["B","H","i"]
        #  [3] - TextureIndexSize  | ["b","h","i"]
        #  [4] - MaterialIndexSize | ["b","h","i"]
        #  [5] - BoneIndexSize     | ["b","h","i"]
        #  [6] - MorphIndexSize    | ["b","h","i"]
        #  [7] - RigidIndexSize    | ["b","h","i"]
        self.Encode = 0
        self.AppendUVCount = 0
        self.VertexIndexSize = "B"
        self.TextureIndexSize = "b"
        self.MaterialIndexSize = "b"
        self.BoneIndexSize = "b"
        self.MorphIndexSize = "b"
        self.RigidIndexSize = "b"

        self.HasError = 0
        self.ErrorMessage = ""

    def Load(self, f):
        hdr_string = ReadStruct(f, "3s")
        if hdr_string[0:3] == b"Pmd":
            self.Version = ReadStruct(f, "f")
            if self.Version != 1.0:
                self.HasError = 1
                self.ErrorMessage = "PMD Version Error"
                return
            # PMD Status
            self.Magic = 0
            self.Encode = 255
            return

        elif hdr_string[0:3] == b"PMX":
            temp = ReadStruct(f, "s")
            self.Version = ReadStruct(f, "f")
            if self.Version == 2.0:
                pass
            elif self.Version == 2.1:
                pass
                # self.HasError = 1
                # self.ErrorMessage = "PMX 2.1 Not Supported"
                # break
            else:
                self.HasError = 1
                self.ErrorMessage = "PMX Version Error"
                return
            # PMX Status
            pmx_param_size = ReadStruct(f, "B")  # Fixed 8
            pmx_params = ReadStruct(f, "8B")
            self.Magic = 1
            self.Encode = pmx_params[0]
            self.AppendUVCount = pmx_params[1]
            self.VertexIndexSize = paramGetSize(pmx_params[2], 1)
            self.TextureIndexSize = paramGetSize(pmx_params[3], 0)
            self.MaterialIndexSize = paramGetSize(pmx_params[4], 0)
            self.BoneIndexSize = paramGetSize(pmx_params[5], 0)
            self.MorphIndexSize = paramGetSize(pmx_params[6], 0)
            self.RigidIndexSize = paramGetSize(pmx_params[7], 0)
        else:
            return

    def Save(self, f):
        self.HasError = 0
        self.ErrorMessagew = ""

        if self.Magic == 0:  # PMD
            self.Version = 1.0
            self.Encode = 255

            WriteStruct(f, "3s", b"Pmd")
            WriteStruct(f, "f", self.Version)
            return

        elif self.Magic == 1:  # PMX
            WriteStruct(f, "4s", b"PMX ")
            WriteStruct(f, "f", self.Version)
            # PMX Status
            WriteStruct(f, "B", 8)  # Parem size Fixed 8
            WriteStruct(f, "B", self.Encode)
            WriteStruct(f, "B", self.AppendUVCount)
            WriteStruct(f, "B", paramSetSize(self.VertexIndexSize))
            WriteStruct(f, "B", paramSetSize(self.TextureIndexSize))
            WriteStruct(f, "B", paramSetSize(self.MaterialIndexSize))
            WriteStruct(f, "B", paramSetSize(self.BoneIndexSize))
            WriteStruct(f, "B", paramSetSize(self.MorphIndexSize))
            WriteStruct(f, "B", paramSetSize(self.RigidIndexSize))
        else:
            return


def paramGetSize(data, is_vert):
    if data == 1:
        if is_vert == 1:
            return "B"
        else:
            return "b"
    elif data == 2:
        if is_vert == 1:
            return "H"
        else:
            return "h"
    elif data == 4:
        return "i"
    else:
        return "i"


def paramSetSize(data):
    if data == "B" or data == "b":
        return 1
    elif data == "H" or data == "h":
        return 2
    elif data == "i":
        return 4
    else:
        return 4


def paramSize(data, is_vert):
    length = len(data)
    if is_vert == 1:
        if length < 256:
            return "B"
        elif length < 65536:
            return "H"
        else:
            return "i"
    else:
        if length < 128:
            return "b"
        elif length < 32768:
            return "h"
        else:
            return "i"


class Model(object):
    # Status
    #    Status = ModelStatus()
    #
    # Name
    #    Name = ""
    #    Name_E = ""
    # Comment
    #    Comment = ""
    #    Comment_E = ""
    #
    # Model Data
    #    Vertices = []
    #    Faces = []
    #    Textures =[]
    #    Materials = []
    #    Bones =[]
    #    Morphs = []
    # Display
    #    DisplayFrames = []
    # Physics
    #    Rigids = []
    #    Joints = []
    #    SoftBodies = []

    def __init__(self):
        # Status
        self.Status = ModelStatus()

        # Name
        self.Name = ""
        self.Name_E = ""

        # Comment
        self.Comment = ""
        self.Comment_E = ""

        # Model Data
        self.Vertices = []
        self.Faces = []
        self.Textures = []
        self.Materials = []
        self.Bones = []
        self.Morphs = []

        # Display
        self.DisplayFrames = []

        # Physics
        self.Rigids = []
        self.Joints = []
        self.SoftBodies = []

    def Load(self, f):
        self.Status.Load(f)

        if self.Status.Magic == 0:  # PMD
            return

        elif self.Status.Magic == 1:  # PMX
            Echo("Loading Pmx ")

            # Name
            self.Name = ReadString(f, self.Status)
            self.Name_E = ReadString(f, self.Status)

            # Comment
            self.Comment = ReadString(f, self.Status)
            self.Comment_E = ReadString(f, self.Status)

            self.Comment = self.Comment.replace("\r", "")
            self.Comment_E = self.Comment_E.replace("\r", "")

            # Model Data
            # Vertex
            Echo("Vertex...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMVertex()
                temp.Load(f, self.Status)
                self.Vertices.append(temp)

            # Face
            Echo("Face...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = ReadStruct(f, self.Status.VertexIndexSize)
                self.Faces.append(temp)

            # Texture
            Echo("Texture...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMTexture()
                temp.Load(f, self.Status)
                self.Textures.append(temp)

            # Material
            Echo("Material...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMMaterial()
                temp.Load(f, self.Status)
                self.Materials.append(temp)

            # Bone
            Echo("Bone...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMBone()
                temp.Load(f, self.Status)
                self.Bones.append(temp)

            # Morph
            Echo("Morph...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMMorph()
                temp.Load(f, self.Status)
                self.Morphs.append(temp)

            # Display
            # DisplayFrame
            Echo("Displayframe...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMDisplayFrame()
                temp.Load(f, self.Status)
                self.DisplayFrames.append(temp)

            # Physics
            # Rigid
            Echo("Rigid...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMRigid()
                temp.Load(f, self.Status)
                self.Rigids.append(temp)

            # Joint
            Echo("Joint...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMJoint()
                temp.Load(f, self.Status)
                self.Joints.append(temp)

            # SoftBody
            Echo("SoftBody...")
            count = ReadStruct(f, "i")
            for i in range(count):
                temp = PMSoftBody()
                temp.Load(f, self.Status)
                self.SoftBodies.append(temp)
        else:
            pass

        Echo("done.")

    def Save(self, f):
        self.Status.VertexIndexSize = paramSize(self.Vertices, 1)
        self.Status.TextureIndexSize = paramSize(self.Textures, 0)
        self.Status.MaterialIndexSize = paramSize(self.Materials, 0)
        self.Status.BoneIndexSize = paramSize(self.Bones, 0)
        self.Status.MorphIndexSize = paramSize(self.Morphs, 0)
        self.Status.RigidIndexSize = paramSize(self.Rigids, 0)

        self.Status.Save(f)

        if self.Status.Magic == 0:  # PMD
            Echo("Saving Pmd ")
            pass

        elif self.Status.Magic == 1:  # PMX
            Echo("Saving Pmx ")

            # Name
            WriteString(f, self.Status, self.Name)
            WriteString(f, self.Status, self.Name_E)

            # Comment
            WriteString(f, self.Status, self.Comment)
            WriteString(f, self.Status, self.Comment_E)

            # Model Data
            # Vertex
            Echo("Vertex...")
            count = len(self.Vertices)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Vertices[i].Save(f, self.Status)

            # Face
            Echo("Face...")
            count = len(self.Faces)
            WriteStruct(f, "i", count)
            for i in range(count):
                WriteStruct(f, self.Status.VertexIndexSize, self.Faces[i])

            # Texture
            Echo("Texture...")
            count = len(self.Textures)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Textures[i].Save(f, self.Status)

            # Material
            Echo("Material...")
            count = len(self.Materials)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Materials[i].Save(f, self.Status)

            # Bone
            Echo("Bone...")
            count = len(self.Bones)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Bones[i].Save(f, self.Status)

            # Morph
            Echo("Morph...")
            count = len(self.Morphs)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Morphs[i].Save(f, self.Status)

            # Display
            # DisplayFrame
            Echo("Displayframe...")
            count = len(self.DisplayFrames)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.DisplayFrames[i].Save(f, self.Status)

            # Physics
            # Rigid
            Echo("Rigid...")
            count = len(self.Rigids)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Rigids[i].Save(f, self.Status)

            # Joint
            Echo("Joint...")
            count = len(self.Joints)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.Joints[i].Save(f, self.Status)

            # SoftBody
            Echo("SoftBody...")
            count = len(self.SoftBodies)
            WriteStruct(f, "i", count)
            for i in range(count):
                self.SoftBodies[i].Save(f, self.Status)
        else:
            pass

        Echo("done.")


class PMVertex(object):

    def __init__(self):
        self.Position = mathutils.Vector((0, 0, 0))
        self.Normal = mathutils.Vector((0, 0, 0))
        self.UV = mathutils.Vector((0, 0))

        # WeightType |[0:BDEF1 1:BDEF2 2:BDEF4 3:SDEF]
        self.Type = 0

        self.AppendUV = []

        # Weidht
        self.Bones = []
        self.Weights = []

        # Edge
        self.EdgeSize = 1.0

    def Load(self, f, mode):
        self.Position = mathutils.Vector(ReadStruct(f, "3f"))
        self.Normal = mathutils.Vector(ReadStruct(f, "3f"))
        self.UV = mathutils.Vector(ReadStruct(f, "2f"))

        self.AppendUV = [mathutils.Vector((0, 0, 0, 0))] * mode.AppendUVCount
        for tempUV in self.AppendUV:
            tempUV = ReadStruct(f, "4f")

        self.Type = ReadStruct(f, "b")

        if self.Type == 0:  # 0:BDEF1
            self.Bones = [0]
            self.Weights = []
            self.Bones[0] = ReadStruct(f, mode.BoneIndexSize)

        elif self.Type == 1:  # 1:BDEF2
            self.Bones = [0, 0]
            self.Weights = [1.0]
            self.Bones[0] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[1] = ReadStruct(f, mode.BoneIndexSize)
            self.Weights[0] = ReadStruct(f, "f")

        elif self.Type == 2:  # 2:BDEF4
            self.Bones = [0, 0, 0, 0]
            self.Weights = [0.0, 0.0, 0.0, 0.0]
            self.Bones[0] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[1] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[2] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[3] = ReadStruct(f, mode.BoneIndexSize)
            self.Weights[0] = ReadStruct(f, "f")
            self.Weights[1] = ReadStruct(f, "f")
            self.Weights[2] = ReadStruct(f, "f")
            self.Weights[3] = ReadStruct(f, "f")

        elif self.Type == 3:  # 3:SDEF
            self.Bones = [0, 0]
            self.Weights = [0.0, 0.0, 0.0, 0.0]
            self.Bones[0] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[1] = ReadStruct(f, mode.BoneIndexSize)
            self.Weights[0] = ReadStruct(f, "f")
            self.Weights[1] = mathutils.Vector(ReadStruct(f, "3f"))
            self.Weights[2] = mathutils.Vector(ReadStruct(f, "3f"))
            self.Weights[3] = mathutils.Vector(ReadStruct(f, "3f"))

        elif self.Type == 4:  # 4:QDEF
            self.Bones = [0, 0, 0, 0]
            self.Weights = [0.0, 0.0, 0.0, 0.0]
            self.Bones[0] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[1] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[2] = ReadStruct(f, mode.BoneIndexSize)
            self.Bones[3] = ReadStruct(f, mode.BoneIndexSize)
            self.Weights[0] = ReadStruct(f, "f")
            self.Weights[1] = ReadStruct(f, "f")
            self.Weights[2] = ReadStruct(f, "f")
            self.Weights[3] = ReadStruct(f, "f")

        self.EdgeSize = ReadStruct(f, "f")

    def Save(self, f, mode):
        WriteStruct(f, "3f", self.Position.to_tuple())
        WriteStruct(f, "3f", self.Normal.to_tuple())
        WriteStruct(f, "2f", self.UV.to_tuple())

        for index in range(mode.AppendUVCount):
            WriteStruct(f, "4f", self.AppendUV[index])

        WriteStruct(f, "b", self.Type)

        if self.Type == 0:  # 0:BDEF1
            WriteStruct(f, mode.BoneIndexSize, self.Bones[0])

        elif self.Type == 1:  # 1:BDEF2
            WriteStruct(f, mode.BoneIndexSize, self.Bones[0])
            WriteStruct(f, mode.BoneIndexSize, self.Bones[1])
            WriteStruct(f, "f", self.Weights[0])

        elif self.Type == 2:  # 2:BDEF4
            WriteStruct(f, mode.BoneIndexSize, self.Bones[0])
            WriteStruct(f, mode.BoneIndexSize, self.Bones[1])
            WriteStruct(f, mode.BoneIndexSize, self.Bones[2])
            WriteStruct(f, mode.BoneIndexSize, self.Bones[3])
            WriteStruct(f, "f", self.Weights[0])
            WriteStruct(f, "f", self.Weights[1])
            WriteStruct(f, "f", self.Weights[2])
            WriteStruct(f, "f", self.Weights[3])

        elif self.Type == 3:  # 3:SDEF
            WriteStruct(f, mode.BoneIndexSize, self.Bones[0])
            WriteStruct(f, mode.BoneIndexSize, self.Bones[1])
            WriteStruct(f, "f", self.Weights[0])
            WriteStruct(f, "3f", self.Weights[1].to_tuple())
            WriteStruct(f, "3f", self.Weights[2].to_tuple())
            WriteStruct(f, "3f", self.Weights[3].to_tuple())

        WriteStruct(f, "f", self.EdgeSize)


class PMTexture(object):

    def __init__(self):
        self.Path = ""

    def Load(self, f, mode):
        self.Path = ReadString(f, mode)
        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Path)
        return


class PMMaterial(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""
        self.Deffuse = mathutils.Vector((0, 0, 0, 1))
        self.Specular = mathutils.Vector((0, 0, 0))
        self.Power = 0.5
        self.Ambient = mathutils.Vector((0, 0, 0))

        # Flags
        self.Both = 0
        self.GroundShadow = 1
        self.DropShadow = 1
        self.OnShadow = 1
        self.OnEdge = 1
        self.VertexColor = 0
        self.DrawPoint = 0
        self.DrawLine = 0

        # Edge
        self.EdgeColor = mathutils.Vector((0, 0, 0, 1))
        self.EdgeSize = 1.0

        # Texture
        self.TextureIndex = -1
        self.SphereIndex = -1

        # Sphere
        self.SphereType = 0  # [0:None 1:Multi 2:Add 3:SubTexture]

        # Toon
        self.UseSystemToon = 1
        self.ToonIndex = 0

        # Comment
        self.Comment = ""

        # FaceLength
        self.FaceLength = 0

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)
        self.Deffuse = mathutils.Vector(ReadStruct(f, "4f"))
        self.Specular = mathutils.Vector(ReadStruct(f, "3f"))
        self.Power = ReadStruct(f, "f")
        self.Ambient = mathutils.Vector(ReadStruct(f, "3f"))

        # Flags
        Flag = ReadStruct(f, "B")

        self.Both = 1 if Flag & 0x01 != 0 else 0
        self.GroundShadow = 1 if Flag & 0x02 != 0 else 0
        self.DropShadow = 1 if Flag & 0x04 != 0 else 0
        self.OnShadow = 1 if Flag & 0x08 != 0 else 0
        self.OnEdge = 1 if Flag & 0x10 != 0 else 0
        self.VertexColor = 1 if Flag & 0x20 != 0 else 0
        self.DrawPoint = 1 if Flag & 0x40 != 0 else 0
        self.DrawLine = 1 if Flag & 0x80 != 0 else 0

        # Edge
        self.EdgeColor = mathutils.Vector(ReadStruct(f, "4f"))
        self.EdgeSize = ReadStruct(f, "f")

        # Texture
        self.TextureIndex = ReadStruct(f, mode.TextureIndexSize)
        self.SphereIndex = ReadStruct(f, mode.TextureIndexSize)

        # Sphere
        self.SphereType = ReadStruct(f, "B")  # [0:None 1:Multi 2:Add 3:SubTexture]

        # Toon
        self.UseSystemToon = ReadStruct(f, "B")
        if self.UseSystemToon == 0:
            self.ToonIndex = ReadStruct(f, "B")
        else:
            self.ToonIndex = ReadStruct(f, mode.TextureIndexSize)

        # Comment
        self.Comment = ReadString(f, mode)

        # FaceLength
        self.FaceLength = ReadStruct(f, "i")

        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)
        WriteStruct(f, "4f", self.Deffuse.to_tuple())
        WriteStruct(f, "3f", self.Specular.to_tuple())
        WriteStruct(f, "f", self.Power)
        WriteStruct(f, "3f", self.Ambient.to_tuple())

        # Flags
        Flag = self.Both * 0x01
        Flag += self.GroundShadow * 0x02
        Flag += self.DropShadow * 0x04
        Flag += self.OnShadow * 0x08
        Flag += self.OnEdge * 0x10
        Flag += self.VertexColor * 0x20
        Flag += self.DrawPoint * 0x40
        Flag += self.DrawLine * 0x80
        WriteStruct(f, "B", Flag)

        # Edge
        WriteStruct(f, "4f", self.EdgeColor.to_tuple())
        WriteStruct(f, "f", self.EdgeSize)

        # Texture
        WriteStruct(f, mode.TextureIndexSize, self.TextureIndex)
        WriteStruct(f, mode.TextureIndexSize, self.SphereIndex)

        # Sphere
        WriteStruct(f, "B", self.SphereType)  # [0:None 1:Multi 2:Add 3:SubTexture]

        # Toon
        WriteStruct(f, "B", self.UseSystemToon)
        if self.UseSystemToon == 0:
            WriteStruct(f, "B", self.ToonIndex)
        else:
            WriteStruct(f, mode.TextureIndexSize, self.ToonIndex)

        # Comment
        WriteString(f, mode, self.Comment)

        # FaceLength
        WriteStruct(f, "i", self.FaceLength)

        return


class PMIK(object):

    def __init__(self):
        self.TargetIndex = 0
        self.Loops = 1  # Max:255
        self.Limit = 3.1415
        self.Member = []

    def Load(self, f, mode):
        self.TargetIndex = ReadStruct(f, mode.BoneIndexSize)
        self.Loops = ReadStruct(f, "i")
        self.Limit = ReadStruct(f, "f")
        count = ReadStruct(f, "i")
        self.Member = [0] * count
        for i in range(count):
            self.Member[i] = PMIKLink()
            self.Member[i].Load(f, mode)
        return

    def Save(self, f, mode):
        WriteStruct(f, mode.BoneIndexSize, self.TargetIndex)
        WriteStruct(f, "i", self.Loops)
        WriteStruct(f, "f", self.Limit)
        count = len(self.Member)
        WriteStruct(f, "i", count)
        for i in range(count):
            self.Member[i].Save(f, mode)
        return


class PMIKLink(object):

    def __init__(self):
        self.Index = 0
        self.UseLimit = 0
        self.UpperLimit = mathutils.Vector((0, 0, 0))
        self.LowerLimit = mathutils.Vector((0, 0, 0))

    def Load(self, f, mode):
        self.Index = ReadStruct(f, mode.BoneIndexSize)
        self.UseLimit = ReadStruct(f, "B")
        if self.UseLimit == 1:
            self.LowerLimit = mathutils.Vector(ReadStruct(f, "3f"))
            self.UpperLimit = mathutils.Vector(ReadStruct(f, "3f"))

    def Save(self, f, mode):
        WriteStruct(f, mode.BoneIndexSize, self.Index)
        WriteStruct(f, "B", self.UseLimit)
        if self.UseLimit == 1:
            WriteStruct(f, "3f", self.LowerLimit.to_tuple())
            WriteStruct(f, "3f", self.UpperLimit.to_tuple())


class PMBone(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

        self.Position = mathutils.Vector((0, 0, 0))
        self.Parent = -1
        self.Level = 0

        # Flags
        self.ToConnectType = 1  # [0:Offset 1:Bone]
        self.Rotatable = 1
        self.Movable = 1
        self.Visible = 1
        self.Operational = 1
        self.UseIK = 0
        self.AdditionalLocal = 0
        self.AdditionalRotation = 0
        self.AdditionalMovement = 0
        self.UseFixedAxis = 0
        self.UseLocalAxis = 0
        self.AfterPhysical = 0
        self.ExternalBone = 0

        # Arm
        self.TailPosition = mathutils.Vector((0, 0, 1))
        self.ChildIndex = -1

        self.AdditionalBoneIndex = -1
        self.AdditionalPower = 1.0

        self.FixedAxis = mathutils.Vector((0, 0, 0))

        self.LocalAxisX = mathutils.Vector((0, 0, 0))
        # self.LocalAxisY = mathutils.Vector((0,0,0))
        self.LocalAxisZ = mathutils.Vector((0, 0, 0))

        self.ExternalBoneIndex = -1

        self.IK = PMIK()

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)

        self.Position = mathutils.Vector(ReadStruct(f, "3f"))
        self.Parent = ReadStruct(f, mode.BoneIndexSize)
        self.Level = ReadStruct(f, "i")

        # Flags
        Flag = ReadStruct(f, "H")
        self.ToConnectType = 1 if Flag & 0x0001 != 0 else 0  # [0:Offset 1:Bone]

        self.Rotatable = 1 if Flag & 0x0002 != 0 else 0
        self.Movable = 1 if Flag & 0x0004 != 0 else 0
        self.Visible = 1 if Flag & 0x0008 != 0 else 0
        self.Operational = 1 if Flag & 0x0010 != 0 else 0

        self.UseIK = 1 if Flag & 0x0020 != 0 else 0

        self.AdditionalLocal = 1 if Flag & 0x0080 != 0 else 0
        self.AdditionalRotation = 1 if Flag & 0x0100 != 0 else 0
        self.AdditionalMovement = 1 if Flag & 0x0200 != 0 else 0

        self.UseFixedAxis = 1 if Flag & 0x0400 != 0 else 0
        self.UseLocalAxis = 1 if Flag & 0x0800 != 0 else 0

        self.AfterPhysical = 1 if Flag & 0x1000 != 0 else 0
        self.ExternalBone = 1 if Flag & 0x2000 != 0 else 0

        # Arm
        if self.ToConnectType == 0:
            self.TailPosition = mathutils.Vector(ReadStruct(f, "3f"))
        else:
            self.ChildIndex = ReadStruct(f, mode.BoneIndexSize)

        # Additional Rotate or Move
        if self.AdditionalRotation == 1 or self.AdditionalMovement == 1:
            self.AdditionalBoneIndex = ReadStruct(f, mode.BoneIndexSize)
            self.AdditionalPower = ReadStruct(f, "f")

        # Fixed Rotate & Move
        if self.UseFixedAxis == 1:
            self.FixedAxis = mathutils.Vector(ReadStruct(f, "3f"))

        if self.UseLocalAxis == 1:
            self.LocalAxisX = mathutils.Vector(ReadStruct(f, "3f"))
            # self.LocalAxisY = mathutils.Vector(ReadStruct(f,"3f"))
            self.LocalAxisZ = mathutils.Vector(ReadStruct(f, "3f"))

        # External Model Bone Control
        if self.ExternalBone == 1:
            self.ExternalBoneIndex = ReadStruct(f, "i")

        # Use IK
        if self.UseIK == 1:
            self.IK = PMIK()
            self.IK.Load(f, mode)

        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)

        WriteStruct(f, "3f", self.Position.to_tuple())
        WriteStruct(f, mode.BoneIndexSize, self.Parent)
        WriteStruct(f, "i", self.Level)

        # Flags
        Flag = self.ToConnectType * 0x0001

        Flag += self.Rotatable * 0x0002
        Flag += self.Movable * 0x0004
        Flag += self.Visible * 0x0008
        Flag += self.Operational * 0x0010

        Flag += self.UseIK * 0x0020

        Flag += self.AdditionalLocal * 0x0080
        Flag += self.AdditionalRotation * 0x0100
        Flag += self.AdditionalMovement * 0x0200

        Flag += self.UseFixedAxis * 0x0400
        Flag += self.UseLocalAxis * 0x0800

        Flag += self.AfterPhysical * 0x1000
        Flag += self.ExternalBone * 0x2000
        WriteStruct(f, "H", Flag)

        # Arm
        if self.ToConnectType == 0:
            WriteStruct(f, "3f", self.TailPosition.to_tuple())
        else:
            WriteStruct(f, mode.BoneIndexSize, self.ChildIndex)

        if self.AdditionalRotation == 1 or self.AdditionalMovement == 1:
            WriteStruct(f, mode.BoneIndexSize, self.AdditionalBoneIndex)
            WriteStruct(f, "f", self.AdditionalPower)

        if self.UseFixedAxis == 1:
            WriteStruct(f, "3f", self.FixedAxis.to_tuple())

        if self.UseLocalAxis == 1:
            WriteStruct(f, "3f", self.LocalAxisX.to_tuple())
            # WriteStruct(f,"3f",self.LocalAxisY.to_tuple())
            WriteStruct(f, "3f", self.LocalAxisZ.to_tuple())

        if self.ExternalBone == 1:
            WriteStruct(f, "i", self.ExternalBoneIndex)

        if self.UseIK == 1:
            self.IK.Save(f, mode)

        return


class PMMorph(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""
        self.Panel = 1  # [1:Eyebrows 2:Mouth 3:Eye 4:Other 0:System]
        self.Type = 1  # [0:Group 1:Vertex 2:Bone 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4 8:Material 9:Flip 10:Impulse]
        self.Offsets = []

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)
        self.Panel = ReadStruct(f, "B")
        self.Type = ReadStruct(f, "B")
        count = ReadStruct(f, "i")
        self.Offsets = [0] * count
        for i in range(count):
            self.Offsets[i] = PMMorphOffset()
            self.Offsets[i].Load(f, mode, self.Type)
        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)
        WriteStruct(f, "B", self.Panel)
        WriteStruct(f, "B", self.Type)
        count = len(self.Offsets)
        WriteStruct(f, "i", count)
        for i in range(count):
            self.Offsets[i].Save(f, mode, self.Type)
        return


class PMMorphOffset(object):

    def __init__(self):
        self.Index = -1
        self.Move = mathutils.Vector((0, 0, 0))
        self.UV = mathutils.Vector((0, 0, 0, 0))
        self.Rotate = mathutils.Vector((0, 0, 0, 0))
        self.Material = PMMaterial()
        self.Power = 0.0
        self.IsLocal = 0
        self.Torque = mathutils.Vector((0, 0, 0))

        # Material
        self.MatEffectType = 0  # [0:Multiplication 1:Add]
        self.MatDiffuse = mathutils.Vector((0, 0, 0, 0))
        self.MatSpeculer = mathutils.Vector((0, 0, 0))
        self.MatPower = 0.5
        self.MatAmbient = mathutils.Vector((0, 0, 0))
        self.MatEdgeColor = mathutils.Vector((0, 0, 0, 0))
        self.MatEdgeSize = 1.0
        self.MatTexture = mathutils.Vector((0, 0, 0, 0))
        self.MatSphere = mathutils.Vector((0, 0, 0, 0))
        self.MatToon = mathutils.Vector((0, 0, 0, 0))

    def Load(self, f, mode, type):
        # [0:Group 1:Vertex 2:Bone 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4 8:Material]
        if type in (0, 9):  # 0:Group 9:Flip
            self.Index = ReadStruct(f, mode.MorphIndexSize)
            self.Power = ReadStruct(f, "f")

        elif type == 1:     # 1:Vertex
            self.Index = ReadStruct(f, mode.VertexIndexSize)
            self.Move = mathutils.Vector(ReadStruct(f, "3f"))

        elif type == 2:     # 2:Bone
            self.Index = ReadStruct(f, mode.BoneIndexSize)
            self.Move = mathutils.Vector(ReadStruct(f, "3f"))
            self.Rotate = mathutils.Vector(ReadStruct(f, "4f"))

        elif type in (3, 4, 5, 6, 7):  # 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4
            self.Index = ReadStruct(f, mode.VertexIndexSize)
            self.UV = mathutils.Vector(ReadStruct(f, "4f"))

        elif type == 8:     # 8:Material
            self.Index = ReadStruct(f, mode.MaterialIndexSize)
            self.MatEffectType = ReadStruct(f, "B")
            self.MatDiffuse = mathutils.Vector(ReadStruct(f, "4f"))
            self.MatSpeculer = mathutils.Vector(ReadStruct(f, "3f"))
            self.MatPower = ReadStruct(f, "f")
            self.MatAmbient = mathutils.Vector(ReadStruct(f, "3f"))
            self.MatEdgeColor = mathutils.Vector(ReadStruct(f, "4f"))
            self.MatEdgeSize = ReadStruct(f, "f")
            self.MatTexture = mathutils.Vector(ReadStruct(f, "4f"))
            self.MatSphere = mathutils.Vector(ReadStruct(f, "4f"))
            self.MatToon = mathutils.Vector(ReadStruct(f, "4f"))

        elif type == 10:     # 10:Impalse
            self.Index = ReadStruct(f, mode.RigidIndexSize)
            self.IsLocal = ReadStruct(f, "B")
            self.Move = mathutils.Vector(ReadStruct(f, "3f"))
            self.Torque = mathutils.Vector(ReadStruct(f, "3f"))

        return

    def Save(self, f, mode, type):
        # [0:Group 1:Vertex 2:Bone 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4 8:Material]
        if type in (0, 9):   # 0:Group 9:Flip
            WriteStruct(f, mode.MorphIndexSize, self.Index)
            WriteStruct(f, "f", self.Power)

        elif type == 1:     # 1:Vertex
            WriteStruct(f, mode.VertexIndexSize, self.Index)
            WriteStruct(f, "3f", self.Move.to_tuple())

        elif type == 2:     # 2:Bone
            WriteStruct(f, mode.BoneIndexSize, self.Index)
            WriteStruct(f, "3f", self.Move.to_tuple())
            WriteStruct(f, "4f", self.Rotate.to_tuple())

        elif type in (3, 4, 5, 6, 7):  # 3:UV 4:ExUV1 5:ExUV2 6:ExUV3 7:ExUV4
            WriteStruct(f, mode.VertexIndexSize, self.Index)
            WriteStruct(f, "4f", self.UV.to_tuple())

        elif type == 8:     # 8:Material
            WriteStruct(f, mode.MaterialIndexSize, self.Index)
            WriteStruct(f, "B", self.MatEffectType)
            WriteStruct(f, "4f", self.MatDiffuse.to_tuple())
            WriteStruct(f, "3f", self.MatSpeculer.to_tuple())
            WriteStruct(f, "f", self.MatPower)
            WriteStruct(f, "3f", self.MatAmbient.to_tuple())
            WriteStruct(f, "4f", self.MatEdgeColor.to_tuple())
            WriteStruct(f, "f", self.MatEdgeSize)
            WriteStruct(f, "4f", self.MatTexture.to_tuple())
            WriteStruct(f, "4f", self.MatSphere.to_tuple())
            WriteStruct(f, "4f", self.MatToon.to_tuple())

        elif type == 10:     # 10:Impalse
            WriteStruct(f, mode.RigidIndexSize, self.Index)
            WriteStruct(f, "B", self.IsLocal)
            WriteStruct(f, "3f", self.Move.to_tuple())
            WriteStruct(f, "3f", self.Torque.to_tuple())
        return


class PMDisplayFrame(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

        self.Type = 0  # [0:Normal 1:Special]

        self.Members = []

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)

        self.Type = ReadStruct(f, "B")

        count = ReadStruct(f, "i")
        self.Members = [0] * count
        for i in range(count):
            self.Members[i] = [0, 0]
            self.Members[i][0] = ReadStruct(f, "B")  # [0:Bone 1:Morph ]
            if self.Members[i][0] == 0:
                self.Members[i][1] = ReadStruct(f, mode.BoneIndexSize)
            else:
                self.Members[i][1] = ReadStruct(f, mode.MorphIndexSize)
        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)

        WriteStruct(f, "B", self.Type)

        count = len(self.Members)
        WriteStruct(f, "i", count)
        for i in range(count):
            WriteStruct(f, "B", self.Members[i][0])
            if self.Members[i][0] == 0:
                WriteStruct(f, mode.BoneIndexSize, self.Members[i][1])
            else:
                WriteStruct(f, mode.MorphIndexSize, self.Members[i][1])
        return


class PMRigid(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

        self.Bone = -1

        self.Group = 0
        self.NoCollision = 0

        self.BoundType = 0  # [0:Sphere 1:Box 2:Capsule]
        self.Size = mathutils.Vector((0, 0, 0))
        self.Position = mathutils.Vector((0, 0, 0))
        self.Rotate = mathutils.Vector((0, 0, 0))
        self.Mass = 0.0
        self.PosLoss = 0.0
        self.RotLoss = 0.0
        self.OpPos = 0.0
        self.Friction = 0.0
        self.PhysicalType = 0  # [0:Static 1:Dynamic 2:Dynamic2 ]
        return

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)

        self.Bone = ReadStruct(f, mode.BoneIndexSize)
        self.Group = ReadStruct(f, "B")
        self.NoCollision = ReadStruct(f, "H")
        self.BoundType = ReadStruct(f, "B")
        self.Size = mathutils.Vector(ReadStruct(f, "3f"))
        self.Position = mathutils.Vector(ReadStruct(f, "3f"))
        self.Rotate = mathutils.Vector(ReadStruct(f, "3f"))
        self.Mass = ReadStruct(f, "f")
        self.PosLoss = ReadStruct(f, "f")
        self.RotLoss = ReadStruct(f, "f")
        self.OpPos = ReadStruct(f, "f")
        self.Friction = ReadStruct(f, "f")
        self.PhysicalType = ReadStruct(f, "B")

        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)

        WriteStruct(f, mode.BoneIndexSize, self.Bone)
        WriteStruct(f, "B", self.Group)
        WriteStruct(f, "H", self.NoCollision)
        WriteStruct(f, "B", self.BoundType)
        WriteStruct(f, "3f", self.Size.to_tuple())
        WriteStruct(f, "3f", self.Position.to_tuple())
        WriteStruct(f, "3f", self.Rotate.to_tuple())
        WriteStruct(f, "f", self.Mass)
        WriteStruct(f, "f", self.PosLoss)
        WriteStruct(f, "f", self.RotLoss)
        WriteStruct(f, "f", self.OpPos)
        WriteStruct(f, "f", self.Friction)
        WriteStruct(f, "B", self.PhysicalType)

        return


class PMJoint(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

        self.Type = 0  # [0:Spring6DOF 1:6DOF 2:P2P 3:ConeTwist 4:Slider  5:Hinge]

        self.Parent = 0
        self.Child = 0
        self.Position = mathutils.Vector((0, 0, 0))
        self.Rotate = mathutils.Vector((0, 0, 0))
        self.PosLowerLimit = mathutils.Vector((0, 0, 0))
        self.PosUpperLimit = mathutils.Vector((0, 0, 0))
        self.RotLowerLimit = mathutils.Vector((0, 0, 0))
        self.RotUpperLimit = mathutils.Vector((0, 0, 0))
        self.PosSpring = mathutils.Vector((0, 0, 0))
        self.RotSpring = mathutils.Vector((0, 0, 0))

        return

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)

        self.Type = ReadStruct(f, "B")  # [0:Spring6DOF] Fixed

        self.Parent = ReadStruct(f, mode.RigidIndexSize)
        self.Child = ReadStruct(f, mode.RigidIndexSize)
        self.Position = mathutils.Vector(ReadStruct(f, "3f"))
        self.Rotate = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosLowerLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosUpperLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotLowerLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotUpperLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosSpring = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotSpring = mathutils.Vector(ReadStruct(f, "3f"))

        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)

        WriteStruct(f, "B", self.Type)

        WriteStruct(f, mode.RigidIndexSize, self.Parent)
        WriteStruct(f, mode.RigidIndexSize, self.Child)
        WriteStruct(f, "3f", self.Position.to_tuple())
        WriteStruct(f, "3f", self.Rotate.to_tuple())
        WriteStruct(f, "3f", self.PosLowerLimit.to_tuple())
        WriteStruct(f, "3f", self.PosUpperLimit.to_tuple())
        WriteStruct(f, "3f", self.RotLowerLimit.to_tuple())
        WriteStruct(f, "3f", self.RotUpperLimit.to_tuple())
        WriteStruct(f, "3f", self.PosSpring.to_tuple())
        WriteStruct(f, "3f", self.RotSpring.to_tuple())

        return


class PMSoftBody(object):

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

        self.Type = 0  # [0:TriMesh 1:Rope]

        self.Material = 0

        self.Group = 0
        self.NoCollision = 0

        self.B_Link = 0
        self.MakeCluster = 0
        self.LinkCrossing = 0

        self.B_Link_Length = 0
        self.ClusterSize = 0

        self.Mass = 0.0
        self.Mergine = 0.0

        self.AeroModel = 0  # [0:V_Point 1:V_TwoSided 2:V_OneSided 3:F_TwoSided 4:F_OneSided]

        self.Configs = [0.0] * 12
        self.ClusterSettings = [0.0] * 6
        self.IterationSettings = [0] * 4
        self.MaterialSettings = [0.0] * 3

        self.Anchors = []

        self.Pins = []

        return

    def Load(self, f, mode):
        self.Name = ReadString(f, mode)
        self.Name_E = ReadString(f, mode)

        self.Type = ReadStruct(f, "B")

        self.Material = ReadStruct(f, mode.MaterialIndexSize)

        self.Group = ReadStruct(f, "B")
        self.NoCollision = ReadStruct(f, "H")

        Flag = ReadStruct(f, "B")
        self.B_Link = 1 if Flag & 0x01 != 0 else 0
        self.MakeCluster = 1 if Flag & 0x02 != 0 else 0
        self.LinkCrossing = 1 if Flag & 0x04 != 0 else 0

        self.B_Link_Length = ReadStruct(f, "i")
        self.ClusterSize = ReadStruct(f, "i")

        self.Mass = ReadStruct(f, "f")
        self.Mergine = ReadStruct(f, "f")

        self.AeroModel = ReadStruct(f, "i")

        self.Configs = ReadStruct(f, "12f")
        self.ClusterSettings = ReadStruct(f, "6f")
        self.IterationSettings = ReadStruct(f, "4i")
        self.MaterialSettings = ReadStruct(f, "3f")

        count = ReadStruct(f, "i")
        self.Anchors = [0] * count
        for i in range(count):
            self.Anchors[i] = [0, 0, 0]
            self.Anchors[i][0] = ReadStruct(f, mode.RegidIndexSize)
            self.Anchors[i][1] = ReadStruct(f, mode.VertexIndexSize)
            self.Anchors[i][2] = ReadStruct(f, "B")  # [0:OFF 1:ON ]

        count = ReadStruct(f, "i")
        self.Pins = [0] * count
        for i in range(count):
            self.Pins[i] = ReadStruct(f, mode.VertexIndexSize)
        return

    def Save(self, f, mode):
        WriteString(f, mode, self.Name)
        WriteString(f, mode, self.Name_E)

        WriteStruct(f, "B", self.Type)
        WriteStruct(f, mode.MaterialIndexSize, self.Material)

        WriteStruct(f, "B", self.Group)
        WriteStruct(f, "H", self.NoCollision)

        Flag = 0
        Flag += self.B_Link * 0x01
        Flag += self.MakeCluster * 0x02
        Flag += self.LinkCrossing * 0x04
        WriteStruct(f, "B", Flag)

        WriteStruct(f, "i", self.B_Link_Length)
        WriteStruct(f, "i", self.ClusterSize)

        WriteStruct(f, "f", self.Mass)
        WriteStruct(f, "f", self.Mergine)

        WriteStruct(f, "i", self.AeroModel)

        WriteStruct(f, "12f", self.Configs)
        WriteStruct(f, "6f", self.ClusterSettings)
        WriteStruct(f, "4i", self.IterationSettings)
        WriteStruct(f, "3f", self.MaterialSettings)

        count = len(self.Anchors)
        WriteStruct(f, "i", count)
        for i in range(count):
            WriteStruct(f, mode.RegidIndexSize, self.Anchors[i][0])
            WriteStruct(f, mode.VertexIndexSize, self.Anchors[i][1])
            WriteStruct(f, "B", self.Anchors[i][2])

        self.Pins = []
        count = len(self.Pins)
        WriteStruct(f, "i", count)
        for i in range(count):
            WriteStruct(f, mode.VertexIndexSize, self.Pins[i])

        return


#
# main
#
if __name__ == '__main__':

    filename1 = "pass1"
    filename2 = "pass2"
    with open(filename1, "rb") as f:
        d_pmd = Model()
        d_pmd.Load(f)

    with open(filename2, "wb") as g:
        d_pmd.Save(g)
