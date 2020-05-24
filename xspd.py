"""\
XSPD Block Decoder
"""

import struct
import os
import io

#import numpy as np
from model import Vertex, Normal, Face, Model
from anims import NewSubframe, OldSubframe, Frame, Animation

def find_offset(fn:str):
    """\
Finds the offset for the XSPD block. At the moment this just searches
the file for the XSPD header, but in future this will use the offsets
of the other blocks to seek to the correct location.
"""
    BS = 4194304
    with open(fn, "rb") as wad:
        count = 0
        b = wad.read(BS)
        while len(b) > 0:
            if b"XSPD" in b:
                return b.find(b"XSPD") + BS*count
            count += 1

class XSPD(object):
    def __init__(self, fn:str, offset:int):
        """\
Object representing the XSPD block of a WAD file. The object
requires a path to a WAD file and an offset to the XSPD block.
The raw bytes will be stored in the object and can be
processed further to extract data.
"""
        # initialise the object
        self.filename = fn
        self.offset = offset
        self.next_offset = 0
        self.data = io.BytesIO() # use it like a file
        self._models_end = None

        # read the wad file
        with open(fn, "rb") as wad:
            wad.seek(offset)

            # verify the header
            header = wad.read(4)
            assert header == b"XSPD"

            # read the offset of the next block
            self.next_offset = struct.unpack("<I", wad.read(4))[0] + wad.tell()

            # read the block
            to_read = self.next_offset-offset
            wad.seek(offset)
            self.data.write(wad.read(to_read))

    def read_models(self, n=None, verbose=False):
        """\
Reads the models from the block.
If n is an integer, will read the model with index n only.
The end of the models section will be stored for faster
access to animations in future."""
        # jump to models
        self.data.seek(0x810)
        num_models = struct.unpack("<I", self.data.read(4))[0]
        if verbose:
            print(num_models, "models")

        models = []
        for m in range(num_models):
            if verbose:
                print("\n== Model {i} ==".format(i=m+1))
            # skip unknown data
            self.data.read(0x48)

            vertex_count = struct.unpack("<I", self.data.read(4))[0]
            if verbose:
                print("Vertices:", vertex_count)
            assert int(self.data.read(8).hex(), 16) == 0

            face_count = struct.unpack("<I", self.data.read(4))[0]
            if verbose:
                print("Faces:", face_count)
            assert int(self.data.read(4).hex(), 16) == 0

            ed1,ed2,ed3 = struct.unpack("<3H", self.data.read(2*3))
            if verbose:
                print("Extended:", ed1, ed2, ed3)

            # skip some null data
            # for Harry Potter 1, this is 0x6
            # Harry Potter 2 is unknown
            assert int(self.data.read(0x6).hex(), 16) == 0

            # prepare for reading vertices
            self.current_group = 0
            vertices = []
            if verbose:
                print("\nReading vertices...")
            for v in range(vertex_count):
                vertices.append(self._read_vertex())
            groups = self.current_group

            # read vertex normals
            # normals use same structure as vertices, so reuse the function
            self.current_group = 0
            normals = []
            if verbose:
                print("Reading vertex normals...")
            for v in range(vertex_count):
                normals.append(self._read_normal())

            # read faces
            self.current_group = 0
            faces = []
            if verbose:
                print("Reading faces...")
            for f in range(face_count):
                faces.append(self._read_face())

            # skip extended data
            # in HP1, extended data size is 0x20
            self.data.read(0x20 * (ed1+ed2+ed3))

            if n is None or n == m:
                model = Model(vertices, normals, faces, groups)
                models.append(model)
            if verbose:
                print("Done!")

        # store the end of models (beginning of anims)
        self._models_end = self.data.tell()
        
        if n is not None:
            return models[0]
        return models

    def _read_vertex(self):
        x, y, z = struct.unpack("<3h", self.data.read(2*3))
        vertex = Vertex(x, y, z, self.current_group)

        # scale the models
##        vertex.r /= 4096
        
        grp_index = struct.unpack("<H", self.data.read(2))[0]
        if grp_index == 1:
            self.current_group += 1

        return vertex

    def _read_normal(self):
        x, y, z = struct.unpack("<3h", self.data.read(2*3))
        norm = Normal(x, y, z, self.current_group)

        # normalise the normal
        # from inspecting the models in Blender, the
        # normals seem to point the wrong way, so we
        # invert them, too
##        norm.r /= 4096
        norm.r *= -1

        grp_index = struct.unpack("<H", self.data.read(2))[0]
        if grp_index == 0:
            self.current_group += 1

        return norm

    def _read_face(self):
        n = self._read_normal()

        # get face-specific data
        verts = struct.unpack("<4H", self.data.read(2*4))
        texture = struct.unpack("<H", self.data.read(2))[0]

        # skip unknown data
        self.data.read(2)

        # construct face dict
        return Face(verts, n, n.group, texture)

    def read_anims(self, verbose=False):
        """\
Read animations from the file. Since there is no easy way
to jump to the animations, the models must all be read
first. Once the models have been read once it will be
possible to jump to the animations.
"""
        if self._models_end is None:
            self.read_models()

        self.data.seek(self._models_end)
        num_anims = struct.unpack("<I", self.data.read(4))[0]
        if verbose:
            print(num_anims, "animations")

        anims = []
        for a in range(num_anims):
            if verbose:
                print("\n== Anim {i} ==".format(i=a+1))
            # unknown counter, used later
            uc = struct.unpack("<I", self.data.read(4))[0]

            assert int(self.data.read(4).hex(), 16) == 0

            # number of frames, including interpolated frames
            num_frames = struct.unpack("<I", self.data.read(4))[0]
            if verbose:
                print("Length:", num_frames, "frames")

            # another unknown value
            uk = struct.unpack("<I", self.data.read(4))[0]

            assert int(self.data.read(8).hex(), 16) == 0

            # number of vertex groups
            # can be used to associate an animation with a model
            groups = struct.unpack("<I", self.data.read(4))[0]
            if verbose:
                print("Vertex Groups:", groups)

            assert int(self.data.read(4).hex(), 16) == 0

            # number of stored frames
            # if zero, uses old animation format
            stored_frames = struct.unpack("<I", self.data.read(4))[0]
            if stored_frames == 0:
                new = False
                if verbose:
                    print("Old anim format")
            else:
                new = True
                if verbose:
                    print("New anim format,", stored_frames, "stored frames")

            assert int(self.data.read(0xC).hex(), 16) == 0

            # skip some unknown data
            self.data.read(4*uc)
            if uk == 0:
                self.data.read(8*num_frames)
            self.data.read(4*num_frames + 4*stored_frames)

            # read actual frames
            frames = []
            if new:
                for f in range(stored_frames):
                    frames.append(self._read_new_frame(groups))
            else:
                for f in range(num_frames):
                    frames.append(self._read_old_frame(groups, f))

            anims.append(Animation(frames, groups))
            if verbose:
                print("Done!")

        return anims

    def _read_new_frame(self, num_groups):
        subframes = []
        for sf in range(num_groups):
            subframes.append(self._read_new_subframe(sf))
        return Frame(subframes[0].index, subframes)

    def _read_new_subframe(self, group):
        # read the quaternion
        w, x, y, z = struct.unpack("<4h", self.data.read(2*4))
##        w /= 4096
##        x /= 4096
##        y /= 4096
##        z /= 4096
        #print([w,x,y,z])

        # read the translation vector
        tx, ty, tz = struct.unpack("<3h", self.data.read(2*3))
##        tx /= 4096
##        ty /= 4096
##        tz /= 4096

        # frame index
        index = struct.unpack("<H", self.data.read(2))[0]

        # pack into NewSubframe
        return NewSubframe(group, [w,x,y,z], [tx,ty,tz], index)

    def _read_old_frame(self, num_groups, index):
        subframes = []
        for sf in range(num_groups):
            subframes.append(self._read_old_subframe(sf))
        return Frame(index, subframes)

    def _read_old_subframe(self, group):
        # read the matrix
        M11, M12, M13 = struct.unpack("<3h", self.data.read(2*3))
        M21, M22, M23 = struct.unpack("<3h", self.data.read(2*3))
        M31, M32, M33 = struct.unpack("<3h", self.data.read(2*3))
        matrix = [[M11/32767, M12/32767, M13/32767],
                  [M21/32767, M22/32767, M23/32767],
                  [M31/32767, M32/32767, M33/32767]]
        
        # read the translation vector
        tx, ty, tz = struct.unpack("<3h", self.data.read(2*3))
        tx /= 4096
        ty /= 4096
        tz /= 4096

        # pack into OldSubframe
        return OldSubframe(group, [w,x,y,z], [tx,ty,tz])

