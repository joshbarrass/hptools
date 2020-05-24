"""\
XSPD Block Decoder
"""

import struct
import os
import io

#import numpy as np
from model import Vertex, Normal, Face, Model

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
If n is an integer, will read the model with index n only"""
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
                model = Model(vertices, normals, faces)
                models.append(model)
            if verbose:
                print("Done!")
        if n is not None:
            return models[0]
        return models

    def _read_vertex(self):
        x, y, z = struct.unpack("<3h", self.data.read(2*3))
        vertex = Vertex(x, y, z, self.current_group)

        # scale the models
        vertex.r /= 4096
        
        grp_index = struct.unpack("<H", self.data.read(2))[0]
        if grp_index == 0:
            self.current_group += 1

        return vertex

    def _read_normal(self):
        x, y, z = struct.unpack("<3h", self.data.read(2*3))
        norm = Normal(x, y, z, self.current_group)

        # normalise the normal
        # from inspecting the models in Blender, the
        # normals seem to point the wrong way, so we
        # invert them, too
        norm.r /= -4096

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
