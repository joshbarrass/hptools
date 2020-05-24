"""\
Animation and frame objects
"""

import numpy as np
from scipy.spatial.transform import Rotation as Rot

from model import Vertex, Normal, Model

class Animation(object):
    def __init__(self, frames, groups):
        self.groups = groups
        self.frames = frames

class Frame(object):
    def __init__(self, index, subframes):
        self.index = index
        self.subframes = subframes
        self.groups = len(subframes)

    def apply_to_model(self, model):
        """\
Produces a new model with the rotation and translation
applied to the correct vertex groups.
"""
        verts = model.verts
        norms = model.norms

        # transform all verts and norms
        newverts = []
        newnorms = []
        for i in range(len(verts)):
            group = verts[i].group
            sf = self.subframes[group]
            rot_matrix = sf.rot.as_dcm()
            v_rotated = verts[i].r.dot(rot_matrix)
            v_rotated += sf.trans
            newvert = Vertex(v_rotated[0],
                             v_rotated[1],
                             v_rotated[2],
                             group)
            
            n_rotated = norms[i].r.dot(rot_matrix)
            newnorm = Normal(n_rotated[0],
                             n_rotated[1],
                             n_rotated[2],
                             group)
            newverts.append(newvert)
            newnorms.append(newvert)
        return Model(newverts, newnorms, model.faces[:], model.groups)

class Subframe(object):
    def __init__(self, group, rot, trans):
        self.group = group # redundant but good to store
        self.rot = rot
        self.trans = np.array(trans, dtype=np.float64)

class NewSubframe(Subframe):
    def __init__(self, group, quat, trans, index):
        """\
Represents a subframe for a new style animation.
Takes the rotation quaternion and translation vector
in tuple or list format and converts them to rot
objects.
"""
        # rearrange the quaternion to [x,y,z,w]
        w, x, y, z = quat
        quat_fixed = np.array([x, y, z, w])
        # construct a scipy rotation object
        rot = Rot.from_quat(quat_fixed)
        super().__init__(group, rot, trans)
        self.index = index

class OldSubframe(Subframe):
    def __init__(self, group, matrix, trans):
        """\
Represents a subframe for an old style animation.
Takes the rotation matrix and translation vector
in tuple or list format and converts them to rot
objects.
"""
        # construct a scipy rotation object
        rot = Rot.from_matrix(quat)
        super().__init__(group, rot, trans)
