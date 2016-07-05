"""
Class to wrap the registry entries for HLMV model registry keys
"""

import _winreg
from math import sin, cos, radians, pi
from re import match
from traceback import print_exc

class HLMVModelRegistryKey(object):
    def __init__(self, weapon_key, rotation=None, translation=None):
        """
        Creates a new HLMV model object.
        If set, rotation and translation are assumed to be the model's
        starting values. If not set, they are pulled from the registry.
        rotation offset and vertical offset can be specified to adjust
        how the model rotates around its center.
        """
        
        try:
            self.itemkey = _winreg.OpenKey(
                _winreg.HKEY_CURRENT_USER,
                'Software\\Valve\\hlmv\\' + weapon_key,
                0,
                _winreg.KEY_ALL_ACCESS
                )
        except WindowsError:
            print 'HLMV Weapon key "%s" doesn\'t exist.' % weapon_key
            print_exc()
            raise

        # Initial model setup: Enable normals, set bgcolor to white
        _winreg.SetValueEx(self.itemkey, 'enablenormalmapping', 0, _winreg.REG_DWORD, 1)
        _winreg.SetValueEx(self.itemkey, 'bgColor', 0, _winreg.REG_SZ, '(1.000000 1.000000 1.000000 1.000000)')

        # Matches 3 floats
        regex = r'\((-?\d+\.\d{6}) (-?\d+\.\d{6}) (-?\d+\.\d{6})\)'
        if rotation:
            self.x_ang = rotation[0]
            self.y_ang = rotation[1]
            self.z_ang = rotation[2]
        else:
            values = match(regex, _winreg.QueryValueEx(self.itemkey, 'Rot')[0])
            self.x_ang = float(values.group(1))
            self.y_ang = float(values.group(2))
            self.z_ang = float(values.group(3))
        if self.y_ang < 0:
            self.y_ang += 360 # HLMV goes 0 to 360 not -180 to 180
        if translation:
            self.x_pos = translation[0]
            self.y_pos = translation[1]
            self.z_pos = translation[2]
        else:
            values = match(regex, _winreg.QueryValueEx(self.itemkey, 'Trans')[0])
            self.x_pos = float(values.group(1))
            self.y_pos = float(values.group(2))
            self.z_pos = float(values.group(3))
            print (self.x_pos, self.y_pos, self.z_pos)

        self.rot_offset = 0
        self.vert_offset = 0

    def rotate(self, x, y):
        """
        Rotate the model to coordinates x, y from its initial rotation.
        X rotation is around the vertical axis, aka yaw
        Y rotation is around the horizontal axis, aka pitch
        """
        new_rotation = (
            self.x_ang + x,
            self.y_ang + y,
            self.z_ang
        )

        print self.y_pos
        print sin(y)*self.rot_offset
        
        new_translation = (
            self.x_pos + cos(y)*self.rot_offset + sin(x)*sin(y)*self.vert_offset,
            self.y_pos + sin(y)*self.rot_offset + sin(x)*sin(y)*self.vert_offset,
            self.z_pos - sin(x)*self.rot_offset
        )
        # Python's math module only uses radians
        x = radians(x)
        y = radians(y)
        
        print new_translation

        # Modify the angle from its initial value
        _winreg.SetValueEx(self.itemkey, # Model key
                           'Rot', # Field name
                           0, # Ignored
                           _winreg.REG_SZ, # Type (Null-terminated string)
                           '(%0.6f %0.6f %0.6f)' % new_rotation)
        _winreg.SetValueEx(self.itemkey, # Model key
                           'Trans', # Field name
                           0, # Ignored
                           _winreg.REG_SZ, # Type (Null-terminated string)
                           '(%0.6f %0.6f %0.6f)' % new_translation) # Value
