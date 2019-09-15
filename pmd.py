#!/bin/python
# -*- coding utf_8 -*-

#
# pmd.py : 20111203 v 5.0
#
import bpy
import mathutils
from struct import *

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


def StringRemoveNull(string):  # PMD String
    for pos, w in enumerate(string):
        if w == 0:  # "\x00":
            return string[:pos]
    return string


def DecodeSjis(string):
    return string.decode('shift_jis', 'ignore')


def EncodeSjis(string):
    return string.encode('shift_jis', 'ignore')


def PaddingString(str, length):
    return str + b"\x00" + b"\xFD" * length


def ReadStringSjis(f, length):
    return DecodeSjis(StringRemoveNull(ReadStruct(f, str(length) + "s")))


def WriteStringSjis(f, data, length):
    WriteStruct(f, str(length) + "s", PaddingString(EncodeSjis(data), length))


class Model(object):

    def __init__(self):
        self.Header = ""
        self.Vertices = []
        self.Polys = []
        self.Materials = []
        self.Bones = []
        self.IKs = []
        self.DispNames = []
        self.BoneIndexs = []
        self.Skins = []
        self.SkinIndexs = []
        self.ToonName = []
        self.Rigids = []
        self.Joints = []

        self.UseEnglish = 1

    def Load(self, f):
        # Header
        Echo("Load PMD File...")
        self.Header = PMDHeader()
        self.Header.Load(f)

        if self.Header.Magic != b'Pmd':
            f.close()
            return None

        # Vertex
        count = ReadStruct(f, "L")
        Echo("Vertex...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDVertex()
            temp.Load(f)
            self.Vertices.append(temp)

        # Pory
        count = ReadStruct(f, "L")
        Echo("Pory...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDPoly()
            temp.Load(f)
            self.Polys.append(temp)

        # Material
        count = ReadStruct(f, "L")
        Echo("Material...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDMaterial()
            temp.Load(f)
            self.Materials.append(temp)

        # Bone
        count = ReadStruct(f, "H")
        Echo("Bone...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDBone()
            temp.Load(f)
            self.Bones.append(temp)

        # IK
        count = ReadStruct(f, "H")
        Echo("IK...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDIK()
            temp.Load(f)
            self.IKs.append(temp)

        # Skin
        count = ReadStruct(f, "H")
        Echo("Skin...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDSkin()
            temp.Load(f)
            self.Skins.append(temp)

        # SkinIndex
        count = ReadStruct(f, "B")
        Echo("SkinIndex...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDSkinIndex()
            temp.Load(f)
            self.SkinIndexs.append(temp)

        # DispName
        count = ReadStruct(f, "B")
        Echo("DispName...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDDispName()
            temp.Load(f)
            self.DispNames.append(temp)

        # BoneIndex
        count = ReadStruct(f, "L")
        Echo("BoneIndex...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDBoneIndex()
            temp.Load(f)
            self.BoneIndexs.append(temp)

        # English
        self.UseEnglish = ReadStruct(f, "B")

        if(self.UseEnglish != 0):
            Echo("English... from:%d" % f.tell())

            # E_Header
            self.Header.Load_E(f)

            bone_count = len(self.Bones)
            face_count = len(self.SkinIndexs)
            disp_count = len(self.DispNames)

            Echo("E_Bone from:%d" % f.tell())
            for i in range(bone_count):
                self.Bones[i].Load_E(f)

            Echo("E_SkinIndex from:%d" % f.tell())
            for i in range(face_count):
                self.SkinIndexs[i].Load_E(f)

            Echo("E_Dispname from:%d" % f.tell())
            for i in range(disp_count):
                self.DispNames[i].Load_E(f)

        # Toons
        Echo("Toons...%d from:%d" % (10, f.tell()))
        for i in range(10):
            temp = ReadStringSjis(f, 100)
            self.ToonName.append(temp)

        # Rigid
        count = ReadStruct(f, "L")
        Echo("Rigid...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDRigid()
            temp.Load(f)
            self.Rigids.append(temp)

        # Joint
        count = ReadStruct(f, "L")
        Echo("Joint...%d from:%d" % (count, f.tell() - 4))
        for i in range(count):
            temp = PMDJoint()
            temp.Load(f)
            self.Joints.append(temp)

        Echo("done...")

    def Save(self, f):
        # Header
        Echo("Save PMD File...")
        self.Header.Save(f)

        # Vertex
        count = len(self.Vertices)
        Echo("Vertex... %d" % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.Vertices[i].Save(f)

        # Poly
        count = len(self.Polys)
        Echo("Poly... %d " % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.Polys[i].Save(f)

        # Material
        count = len(self.Materials)
        Echo("Material... %d " % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.Materials[i].Save(f)

        # Bone
        count = len(self.Bones)
        Echo("Bone... %d " % count)
        WriteStruct(f, "H", count)
        for i in range(count):
            self.Bones[i].Save(f)

        # IK
        count = len(self.IKs)
        Echo("IK... %d " % count)
        WriteStruct(f, "H", count)
        for i in range(count):
            self.IKs[i].Save(f)

        # Skin
        count = len(self.Skins)
        Echo("Skin... %d " % count)
        WriteStruct(f, "H", count)
        for i in range(count):
            self.Skins[i].Save(f)

        # SkinIndex
        count = len(self.SkinIndexs)
        Echo("SkinIndex... %d " % count)
        WriteStruct(f, "B", count)
        for i in range(count):
            self.SkinIndexs[i].Save(f)

        # DispName
        count = len(self.DispNames)
        Echo("DispName... %d " % count)
        WriteStruct(f, "B", count)
        for i in range(count):
            self.DispNames[i].Save(f)

        # BoneIndex
        count = len(self.BoneIndexs)
        Echo("BoneIndex... %d " % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.BoneIndexs[i].Save(f)

        # English
        Echo("English... %d " % count)

        # engFlag
        f.write(pack("B", 1))

        # E_Header
        self.Header.Save_E(f)

        # E_Bone
        for data in self.Bones:
            data.Save_E(f)

        # E_SkinIndex
        for data in self.SkinIndexs:
            data.Save_E(f)

        # E_DispNames
        for data in self.DispNames:
            data.Save_E(f)

        # ToonName
        count = 10
        Echo("ToonName... %d " % count)
        for i in range(count):
            WriteStringSjis(f, self.ToonName[i], 100)

        # Rigid
        count = len(self.Rigids)
        Echo("Rigid... %d " % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.Rigids[i].Save(f)

        # Joint
        count = len(self.Joints)
        Echo("Rigid... %d " % count)
        WriteStruct(f, "L", count)
        for i in range(count):
            self.Joints[i].Save(f)

        Echo("done...")


class PMDHeader(object):

    def __init__(self):
        self.Magic = "Pmd"
        self.Version = 1.0
        self.Name = ""
        self.Comment = ""
        self.Name_E = ""
        self.Comment_E = ""

    def Load(self, f):
        self.Magic = ReadStruct(f, "3s")
        self.Version = ReadStruct(f, "f")
        self.Name = ReadStringSjis(f, 20)
        self.Comment = ReadStringSjis(f, 256)

    def Load_E(self, f):
        self.Name_E = ReadStringSjis(f, 20)
        self.Comment_E = ReadStringSjis(f, 256)

    def Save(self, f):
        WriteStruct(f, "3s", self.Magic)
        WriteStruct(f, "f", self.Version)
        WriteStringSjis(f, self.Name, 20)
        WriteStringSjis(f, self.Comment, 256)

    def Save_E(self, f):
        WriteStringSjis(f, self.Name_E, 20)
        WriteStringSjis(f, self.Comment_E, 256)


class PMDVertex(object):
    # l_vert = [ ( x,y,z,nx,ny,nz,u,v) ]
    # l_weight = [ ( bone1,bone2,weight,flag ) ]

    def __init__(self):
        self.Pos = mathutils.Vector((0, 0, 0))
        self.No = mathutils.Vector((0, 0, 0))
        self.Uv = mathutils.Vector((0, 0))
        self.Bone = [0, 0]
        self.Weight = 100
        self.Flag = 0

    def Load(self, f):
        self.Pos = mathutils.Vector(ReadStruct(f, "3f"))
        self.No = mathutils.Vector(ReadStruct(f, "3f"))
        self.Uv = mathutils.Vector(ReadStruct(f, "2f"))
        self.Bone = ReadStruct(f, "2H")
        self.Weight = ReadStruct(f, "B")
        self.Flag = ReadStruct(f, "B")

    def Save(self, f):
        WriteStruct(f, "3f", self.Pos.to_tuple())
        WriteStruct(f, "3f", self.No.to_tuple())
        WriteStruct(f, "2f", self.Uv.to_tuple())
        WriteStruct(f, "2H", self.Bone)
        WriteStruct(f, "B", self.Weight)
        WriteStruct(f, "B", self.Flag)


class PMDPoly(object):
    # l_poly = [ vertex number ]

    def __init__(self):
        self.Index = 0

    def Load(self, f):
        self.Index = ReadStruct(f, "H")

    def Save(self, f):
        WriteStruct(f, "H", self.Index)


class PMDMaterial(object):
    # ( r,g,b,a, shininess, specular(r,g,b), ambient(r,g,b) , toon, toon_edge , edges, file ) ]

    def __init__(self):
        self.Deffuse = mathutils.Vector((0, 0, 0))
        self.Alpha = 1.0
        self.Shiness = 1.0
        self.Specler = mathutils.Vector((0, 0, 0))
        self.Ambient = mathutils.Vector((0, 0, 0))
        self.Toon = 1
        self.Edge = 1
        self.VertCount = 0
        self.Texture = ""
        self.Sphere = ""

    def Load(self, f):
        self.Deffuse = mathutils.Vector(ReadStruct(f, "4f"))
        # self.Alpha   = ReadStruct(f,"f")
        self.Shiness = ReadStruct(f, "f")
        self.Specler = mathutils.Vector(ReadStruct(f, "3f"))
        self.Ambient = mathutils.Vector(ReadStruct(f, "3f"))
        self.Toon = ReadStruct(f, "B")
        self.Edge = ReadStruct(f, "B")
        self.VertCount = ReadStruct(f, "i")

        texture = ReadStringSjis(f, 20)
        textures = texture.split("*")
        self.Texture = ""
        self.Sphere = ""

        for tex in textures:
            if tex.lower().find(".sph") > 0 or tex.lower().find(".spa") > 0:
                self.Sphere = tex
            else:
                self.Texture = tex

    def Save(self, f):
        WriteStruct(f, "4f", self.Deffuse.to_tuple())
        # WriteStruct(f,"f",self.Alpha)
        WriteStruct(f, "f", self.Shiness)
        WriteStruct(f, "3f", self.Specler.to_tuple())
        WriteStruct(f, "3f", self.Ambient.to_tuple())
        WriteStruct(f, "B", self.Toon)
        WriteStruct(f, "B", self.Edge)
        WriteStruct(f, "L", self.VertCount)

        temp = ""
        if(len(self.Texture) == 0):
            temp = self.Sphere

        elif (len(self.Sphere) == 0):
            temp = self.Texture

        else:
            temp = self.Texture + "*" + self.Sphere

        WriteStringSjis(f, temp, 20)


class PMDBone(object):
    # ( name, parent , to , kind , knum, x,y,z )

    def __init__(self):
        self.Name = ""
        self.Parent = -1
        self.To = -1
        self.Kind = 0
        self.KindNo = -1
        self.Pos = mathutils.Vector((0, 0, 0))
        self.Name_E = ""

    def Load(self, f):
        self.Name = ReadStringSjis(f, 20)
        self.Parent = ReadStruct(f, "H")
        self.To = ReadStruct(f, "H")
        self.Kind = ReadStruct(f, "B")
        self.KindNo = ReadStruct(f, "H")
        self.Pos = mathutils.Vector(ReadStruct(f, "3f"))

    def Load_E(self, f):
        self.Name_E = ReadStringSjis(f, 20)

    def Save(self, f):
        WriteStringSjis(f, self.Name, 20)
        WriteStruct(f, "H", self.Parent)
        WriteStruct(f, "H", self.To)
        WriteStruct(f, "B", self.Kind)
        WriteStruct(f, "H", self.KindNo)
        WriteStruct(f, "3f", self.Pos.to_tuple())

    def Save_E(self, f):
        WriteStringSjis(f, self.Name_E, 20)


class PMDIK(object):
    # ( target,end,p1,p2,[node])

    def __init__(self):
        self.Target = 0
        self.End = 0
        self.P1 = 10
        self.P2 = 0.8
        self.Node = []

    def Load(self, f):
        self.Target = ReadStruct(f, "H")
        self.End = ReadStruct(f, "H")
        link_count = ReadStruct(f, "B")
        self.P1 = ReadStruct(f, "H")
        self.P2 = ReadStruct(f, "f")

        self.Node = []
        for i in range(link_count):
            node = ReadStruct(f, "H")
            self.Node.append(node)

    def Save(self, f):
        WriteStruct(f, "H", self.Target)
        WriteStruct(f, "H", self.End)
        WriteStruct(f, "B", len(self.Node))
        WriteStruct(f, "H", self.P1)
        WriteStruct(f, "f", self.P2)

        for data in self.Node:
            WriteStruct(f, "H", data)


class PMDSkin(object):
    # ( name,type,[vertex])

    def __init__(self):
        self.Name = ""
        self.Type = 0
        self.Verts = []
        self.Name_E = ""

    def Load(self, f):
        self.Name = ReadStringSjis(f, 20)
        vert_count = ReadStruct(f, "L")
        self.Type = ReadStruct(f, "B")

        self.Verts = []
        for j in range(vert_count):
            temp = PMDSkinVert()
            temp.Load(f)
            self.Verts.append(temp)

    def Load_E(self, f):
        self.Name_E = ReadStringSjis(f, 20)

    def Save(self, f):
        WriteStringSjis(f, self.Name, 20)
        WriteStruct(f, "L", len(self.Verts))
        WriteStruct(f, "B", self.Type)

        for data in self.Verts:
            data.Save(f)

    def Save_E(self, f):
        WriteStringSjis(f, self.Name_E, 20)


class PMDSkinVert(object):
    # (index,x,y,z)

    def __init__(self):
        self.Index = 0
        self.Pos = mathutils.Vector((0, 0, 0))

    def Load(self, f):
        self.Index = ReadStruct(f, "L")
        self.Pos = mathutils.Vector(ReadStruct(f, "3f"))

    def Save(self, f):
        WriteStruct(f, "L", self.Index)
        WriteStruct(f, "3f", self.Pos.to_tuple())


class PMDSkinIndex(object):
    # (skingroup)

    def __init__(self):
        self.Index = 0
        self.Name_E = ""

    def Load(self, f):
        self.Index = ReadStruct(f, "H")

    def Load_E(self, f):
        self.Name_E = ReadStringSjis(f, 20)

    def Save(self, f):
        WriteStruct(f, "H", self.Index)

    def Save_E(self, f):
        WriteStringSjis(f, self.Name_E, 20)


class PMDDispName(object):
    # (dispname)
    # (skingroup)

    def __init__(self):
        self.Name = ""
        self.Name_E = ""

    def Load(self, f):
        self.Name = ReadStringSjis(f, 50)

    def Load_E(self, f):
        self.Name_E = ReadStringSjis(f, 50)

    def Save(self, f):
        WriteStringSjis(f, self.Name, 50)

    def Save_E(self, f):
        WriteStringSjis(f, self.Name_E, 50)


class PMDBoneIndex(object):
    # ( bone , type )

    def __init__(self):
        self.Bone = 0
        self.Group = 0

    def Load(self, f):
        self.Bone = ReadStruct(f, "H")
        self.Group = ReadStruct(f, "B")

    def Save(self, f):
        WriteStruct(f, "H", self.Bone)
        WriteStruct(f, "B", self.Group)


class PMDRigid(object):
    # (name,bone,group,noCollision,boundType,(size),(pos),(rot),mass,pos_loss,rot_loss,opposition,friction,physicaltype))

    def __init__(self):
        self.Name = ""
        self.Bone = -1
        self.Group = 1
        self.NoCollision = 0
        self.BoundType = 0
        self.Size = [0, 0, 0]
        self.Pos = mathutils.Vector((0, 0, 0))
        self.Rot = mathutils.Vector((0, 0, 0))
        self.Mass = 1.0
        self.PosLoss = 0.0
        self.RotLoss = 0.0
        self.OpPos = 0.0
        self.Friction = 0.0
        self.PhysicalType = 0

    def Load(self, f):
        self.Name = ReadStringSjis(f, 20)
        self.Bone = ReadStruct(f, "H")
        self.Group = ReadStruct(f, "B")
        self.NoCollision = ReadStruct(f, "H")
        self.BoundType = ReadStruct(f, "B")
        self.Size = ReadStruct(f, "3f")
        self.Pos = mathutils.Vector(ReadStruct(f, "3f"))
        self.Rot = mathutils.Vector(ReadStruct(f, "3f"))
        self.Mass = ReadStruct(f, "f")
        self.PosLoss = ReadStruct(f, "f")
        self.RotLoss = ReadStruct(f, "f")
        self.OpPos = ReadStruct(f, "f")
        self.Friction = ReadStruct(f, "f")
        self.PhysicalType = ReadStruct(f, "B")

    def Save(self, f):
        WriteStringSjis(f, self.Name, 20)
        WriteStruct(f, "H", self.Bone)
        WriteStruct(f, "B", self.Group)
        WriteStruct(f, "H", self.NoCollision)
        WriteStruct(f, "B", self.BoundType)
        WriteStruct(f, "3f", (self.Size[0], self.Size[1], self.Size[2]))
        WriteStruct(f, "3f", self.Pos.to_tuple())
        WriteStruct(f, "3f", self.Rot.to_tuple())
        WriteStruct(f, "f", self.Mass)
        WriteStruct(f, "f", self.PosLoss)
        WriteStruct(f, "f", self.RotLoss)
        WriteStruct(f, "f", self.OpPos)
        WriteStruct(f, "f", self.Friction)
        WriteStruct(f, "B", self.PhysicalType)


class PMDJoint(object):
    # (name,parent,child,(pos),(rot),(pos_lower_rimit),(pos_upper_rimit),(rot_lower_rimit),(rot_upper_rimit),(pos_spring),(rot_spring)))

    def __init__(self):
        self.Name = ""
        self.Parent = 0
        self.Child = 0
        self.Pos = mathutils.Vector((0, 0, 0))
        self.Rot = mathutils.Vector((0, 0, 0))
        self.PosLowerLimit = mathutils.Vector((0, 0, 0))
        self.PosUpperLimit = mathutils.Vector((0, 0, 0))
        self.RotLowerLimit = mathutils.Vector((0, 0, 0))
        self.RotUpperLimit = mathutils.Vector((0, 0, 0))
        self.PosSpring = mathutils.Vector((0, 0, 0))
        self.RotSpring = mathutils.Vector((0, 0, 0))

    def Load(self, f):
        self.Name = ReadStringSjis(f, 20)
        self.Parent = ReadStruct(f, "L")
        self.Child = ReadStruct(f, "L")
        self.Pos = mathutils.Vector(ReadStruct(f, "3f"))
        self.Rot = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosLowerLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosUpperLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotLowerLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotUpperLimit = mathutils.Vector(ReadStruct(f, "3f"))
        self.PosSpring = mathutils.Vector(ReadStruct(f, "3f"))
        self.RotSpring = mathutils.Vector(ReadStruct(f, "3f"))

    def Save(self, f):
        WriteStringSjis(f, self.Name, 20)
        WriteStruct(f, "L", self.Parent)
        WriteStruct(f, "L", self.Child)
        WriteStruct(f, "3f", self.Pos.to_tuple())
        WriteStruct(f, "3f", self.Rot.to_tuple())
        WriteStruct(f, "3f", self.PosLowerLimit.to_tuple())
        WriteStruct(f, "3f", self.PosUpperLimit.to_tuple())
        WriteStruct(f, "3f", self.RotLowerLimit.to_tuple())
        WriteStruct(f, "3f", self.RotUpperLimit.to_tuple())
        WriteStruct(f, "3f", self.PosSpring.to_tuple())
        WriteStruct(f, "3f", self.RotSpring.to_tuple())


#
# main
#
if __name__ == '__main__':

    filename1 = "test.pmd"
    filename2 = "temp2.pmd"
    with open(filename1, "rb") as f:
        d_pmd = Model()
        d_pmd.Load(f)

    with open(filename2, "wb") as g:
        d_pmd.Save(g)

    print("done.")
