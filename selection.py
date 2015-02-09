import numpy as np

from renderable_line import LineRenderable

class SelectionRenderable(LineRenderable):
    
    color = (0.8, 0.8, 0.8, 1)
    line_width = 2
    x, y, z = 0, 0, 0
    # verts include Z for different layers - set 2 for a cool glitch :]
    vert_items = 3
    
    def build_geo(self):
        # init empty arrays; geo is rebuilt every time selection changes
        self.vert_array = np.array([], dtype=np.float32)
        self.elem_array = np.array([], dtype=np.uint32)
        self.color_array = np.array([], dtype=np.float32)
    
    def get_adjacent_tile(self, tiles, frame, layer, x, y, dir_x, dir_y):
        "returns True or False based on tile dict lookup relative to given tile"
        return tiles.get((frame, layer, x + dir_x, y + dir_y), False)
    
    def rebuild_geo(self, tiles):
        # array source lists of verts, elements, colors
        v, e, c = [], [], []
        index = 0
        for tile in tiles:
            frame, layer, x, y = tile[0], tile[1], tile[2], tile[3]
            # use rules to detect if a tile is above, below,
            # to left or right of this one, draw lines accordingly
            above = self.get_adjacent_tile(tiles, frame, layer, x, y, 0, -1)
            below = self.get_adjacent_tile(tiles, frame, layer, x, y, 0, 1)
            left = self.get_adjacent_tile(tiles, frame, layer, x, y, -1, 0)
            right = self.get_adjacent_tile(tiles, frame, layer, x, y, 1, 0)
            if not above and not below and not left and not right:
                continue
            z = self.app.ui.active_art.layers_z[layer]
            top_left =     (  x,   -y, z)
            top_right =    (x+1,   -y, z)
            bottom_right = (x+1, -y-1, z)
            bottom_left =  (  x, -y-1, z)
            def add_line(vert_a, vert_b, verts, elems, colors, element_index):
                verts += [vert_a, vert_b]
                elems += [element_index, element_index+1]
                colors += self.color * 2
            # verts = corners
            if not above:
                # top edge
                add_line(top_left, top_right, v, e, c, index)
                index += 2
            if not below:
                # bottom edge
                add_line(bottom_left, bottom_right, v, e, c, index)
                index += 2
            if not left:
                # left edge
                add_line(top_left, bottom_left, v, e, c, index)
                index += 2
            if not right:
                # right edge
                add_line(top_right, bottom_right, v, e, c, index)
                index += 2
        self.vert_array = np.array(v, dtype=np.float32)
        self.elem_array = np.array(e, dtype=np.uint32)
        self.color_array = np.array(c, dtype=np.float32)
    
    def reset_loc(self):
        pass
    
    def get_projection_matrix(self):
        return self.app.camera.projection_matrix
    
    def get_view_matrix(self):
        return self.app.camera.view_matrix
    
    def render(self, elapsed_time):
        LineRenderable.render(self, elapsed_time)
        #print('hi')
