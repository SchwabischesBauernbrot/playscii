import math
import numpy as np

class Vec3:
    
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z
    
    def __str__(self):
        return 'Vec3 %.4f, %.4f, %.4f' % (self.x, self.y, self.z)
    
    def __sub__(self, b):
        return Vec3(self.x - b.x, self.y - b.y, self.z - b.z)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def normalize(self):
        "returns a unit length version of this vector"
        n = Vec3()
        l = self.length()
        if l != 0:
            ilength = 1.0 / l
            n.x = self.x * ilength
            n.y = self.y * ilength
            n.z = self.z * ilength
        return n
    
    def cross(self, b):
        x = self.y * b.z - self.z * b.y
        y = self.z * b.x - self.x * b.z
        z = self.x * b.y - self.y * b.x
        return Vec3(x, y, z)
    
    def dot(self, b):
        return self.x * b.x + self.y * b.y + self.z * b.z
    
    def inverse(self):
        return Vec3(-self.x, -self.y, -self.z)
    
    def copy(self):
        return Vec3(self.x, self.y, self.z)


def transform_vec4(x, y, z, w, m):
    "transforms given 4d vector by given matrix"
    m = m.getA()
    out_x = x * m[0][0] + y * m[1][0] + z * m[2][0] + w * m[3][0]
    out_y = x * m[0][1] + y * m[1][1] + z * m[2][1] + w * m[3][1]
    out_z = x * m[0][2] + y * m[1][2] + z * m[2][2] + w * m[3][2]
    out_w = x * m[0][3] + y * m[1][3] + z * m[2][3] + w * m[3][3]
    return out_x, out_y, out_z, out_w

def unproject(screen_x, screen_y, screen_z, screen_width, screen_height,
              screen_projection_matrix, screen_view_matrix):
    """
    returns 4d vector unprojected using given screen dimensions and
    projection + view matrices
    """
    x = 2 * screen_x / screen_width - 1
    y = -(2 * screen_y / screen_height + 1)
    z = screen_z
    w = 1.0
    inv_proj = screen_projection_matrix.getI()
    inv_view = screen_view_matrix.getI()
    x, y, z, w = transform_vec4(x, y, z, w, inv_proj)
    x, y, z, w = transform_vec4(x, y, z, w, inv_view)
    if w != 0:
        x /= w
        y /= w
        z /= w
    return x, y, z, w

def screen_to_ray(x, y, width, height, projection_matrix, view_matrix):
    "returns a 3d ray (start + normal) for given point in 2d screen space"
    unproject_args = [x, y, 0, width, height, projection_matrix, view_matrix]
    near_x, near_y, near_z, near_w = unproject(*unproject_args)
    unproject_args[2] = -1
    far_x, far_y, far_z, far_w = unproject(*unproject_args)
    dir_x, dir_y, dir_z = far_x - near_x, far_y - near_y, far_z - near_z
    dir_length = math.sqrt(dir_x ** 2 + dir_y ** 2 + dir_z ** 2)
    if dir_length != 0:
        dir_inv_length = 1 / dir_length
        dir_x *= dir_inv_length
        dir_y *= dir_inv_length
        dir_z *= dir_inv_length
    else:
        dir_x = dir_y = dir_z = 0
    return near_x, near_y, near_z, dir_x, dir_y, dir_z

def line_plane_intersection(plane_x, plane_y, plane_z, plane_d,
                            start_x, start_y, start_z, end_x, end_y, end_z):
    """
    returns point of intersection for given plane (3d normal + distance from origin)
    and given line (start and end 3d vector)
    """
    # http://paulbourke.net/geometry/pointlineplane/
    u = (plane_x * start_x) + (plane_y * start_y) + (plane_z * start_z) + plane_d
    u /= plane_x * (start_x - end_x) + plane_y * (start_y - end_y) + plane_z * (start_z - end_z)
    if u <= 0 or u > 1:
        return False, False, False
    x = u * start_x + (1 - u) * end_x
    y = u * start_y + (1 - u) * end_y
    z = u * start_z + (1 - u) * end_z
    return x, y, z

def screen_to_world_NEW(app, screen_x, screen_y):
    """
    returns 3D (float) world space coordinates for given 2D (int)
    screen space coordinates.
    """
    screen_width, screen_height = app.window_width, app.window_height
    proj = np.matrix(app.camera.projection_matrix)
    view = np.matrix(app.camera.view_matrix)
    args = (screen_x, screen_y, screen_width, screen_height, proj, view)
    start_x, start_y, start_z, ray_x, ray_y, ray_z = screen_to_ray(*args)
    # turn ray into line segment
    ray_dist = 100
    end_x = start_x + ray_x * ray_dist
    end_y = start_y + ray_y * ray_dist
    end_z = start_z + ray_z * ray_dist
    # determine "plane distance from origin"
    if app.ui.active_art and not app.game_mode:
        d = app.ui.active_art.layers_z[app.ui.active_art.active_layer]
    else:
        d = 0
    print('ray start: %.4f, %.4f, %.4f\nray end: %.4f, %.4f, %.4f' % (start_x, start_y, start_z, end_x, end_y, end_z))
    x, y, z = line_plane_intersection(0, 0, 1, d, start_x, start_y, start_z,
                                      end_x, end_y, end_z)
    if not x: return 0, 0, 0
    return x, y, z

def screen_to_world_OLD(app, screen_x, screen_y):
    """
    returns 3D (float) world space coordinates for given 2D (int)
    screen space coordinates.
    """
    # "normalized device coordinates"
    ndc_x = (2 * screen_x) / app.window_width - 1
    ndc_y = (-2 * screen_y) / app.window_height + 1
    # reverse camera projection
    pjm = np.matrix(app.camera.projection_matrix)
    vm = np.matrix(app.camera.view_matrix)
    vp_inverse = (pjm * vm).getI()
    if app.ui.active_art and not app.game_mode:
        z = app.ui.active_art.layers_z[app.ui.active_art.active_layer]
    else:
        z = 0
    point = vp_inverse.dot(np.array([ndc_x, ndc_y, z, 0]))
    point = point.getA()
    cz = app.camera.z - z
    # apply camera offsets
    x = point[0][0] * cz + app.camera.x
    y = point[0][1] * cz + app.camera.y
    # TODO: below doesn't properly account for distance between current
    # layer and camera - close but still inaccurate as cursor gets further
    # from world origin
    #y += self.app.camera.look_y.y
    y += app.camera.y_tilt
    return x, y, z
