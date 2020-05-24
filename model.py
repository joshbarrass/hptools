import numpy as np

class Vec3(object):
    def __init__(self, x, y, z):
        self.r = np.array([x,y,z], dtype=np.float64)

class Vertex(Vec3):
    def __init__(self, x, y, z, group):
        super().__init__(x, y, z)
        self.group = group

class Normal(Vec3):
    def __init__(self, x, y, z, group):
        super().__init__(x, y, z)
        self.group = group
        
class Face(object):
    def __init__(self, vert_indices, normal, group, texture):
        self.verts = vert_indices
        self.norm = normal
        self.group = group
        self.texture = texture
    
        
class Model(object):
    def __init__(self, vertices, normals, faces, groups=0):
        """\
Stores the data for a model and provides functions for exporting it
"""
        self.verts = vertices
        self.norms = normals
        self.faces = faces
        self.groups = groups

    def __repr__(self):
        out = "{package}.Model({v} vertices, {n} normals, {f} faces)"
        return out.format(package=__name__,
                          v=len(self.verts),
                          n=len(self.norms),
                          f=len(self.faces))

    def save_obj(self, fn:str):
        """\
Save the model as a Wavefront .obj file
"""
        # construct lines
        vertex_lines = [
            "v {x} {y} {z}\n".format(x=v.r[0],
                                   y=v.r[1],
                                   z=v.r[2])
            for v in self.verts]
        normal_lines = [
            "vn {x} {y} {z}\n".format(x=n.r[0],
                                    y=n.r[1],
                                    z=n.r[2])
            for n in self.norms]
        # face lines require more logic
        face_lines = []
        for f in self.faces:
            if f.group == 0: # quad
                face_lines.append(
                    "f {v1}//{v1} {v2}//{v2} {v4}//{v4} {v3}//{v3}\n".format(
                        v1=f.verts[0]+1,
                        v2=f.verts[1]+1,
                        v3=f.verts[2]+1,
                        v4=f.verts[3]+1))
            else: # tri
                face_lines.append(
                    "f {v1}//{v1} {v2}//{v2} {v3}//{v3}\n".format(
                        v1=f.verts[0]+1,
                        v2=f.verts[1]+1,
                        v3=f.verts[2]+1))

        # write the lines to file
        with open(fn, "w", encoding="ascii") as obj:
            obj.write("# vertices\n")
            obj.writelines(vertex_lines)
            obj.write("\n# vertex normals\n")
            obj.writelines(normal_lines)
            obj.write("\n# faces\n")
            obj.writelines(face_lines)
