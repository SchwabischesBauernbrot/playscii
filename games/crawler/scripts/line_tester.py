
import vector

from game_object import GameObject
from renderable_line import DebugLineRenderable


# stuff for troubleshooting "get tiles intersecting line" etc


class DebugMarker(GameObject):
    art_width, art_height = 1, 1
    art_off_pct_x, art_off_pct_y = 0.0, 0.0
    generate_art = True
    should_save = False
    alpha = 0.5
    def pre_first_update(self):
        # red X with yellow background
        self.art.set_tile_at(0, 0, 0, 0, 24, 3, 8)
        self.z = 0.1


class LineTester(GameObject):
    art_width, art_height = 40, 40
    art_off_pct_x, art_off_pct_y = 0.0, 0.0
    generate_art = True
    
    def pre_first_update(self):
        self.mark_a = self.world.spawn_object_of_class('DebugMarker', -3, 33)
        self.mark_b = self.world.spawn_object_of_class('DebugMarker', -10, 40)
        self.z = -0.01
        self.world.grid.visible = True
        self.line = DebugLineRenderable(self.app, self.art)
        self.line.z = 0.0
        self.line.line_width = 3
    
    def update(self):
        GameObject.update(self)
        # debug line
        self.line.set_lines([(self.mark_a.x, self.mark_a.y, 0.0),
                             (self.mark_b.x, self.mark_b.y, 0.0)])
        # paint tiles under line
        self.art.clear_frame_layer(0, 0, 7)
        line_func = vector.get_tiles_along_line
        line_func = vector.get_tiles_along_integer_line
        tiles = line_func(self.mark_a.x, self.mark_a.y,
                          self.mark_b.x, self.mark_b.y)
        for tile in tiles:
            x, y = self.get_tile_at_point(tile[0], tile[1])
            char, fg = 1, 6
            self.art.set_tile_at(0, 0, x, y, char, fg)
    
    def render(self, layer, z_override=None):
        GameObject.render(self, layer, z_override)
        # TODO not sure why this is necessary, pre_first_update should run before first render(), right? blech
        if hasattr(self, 'line') and self.line:
            self.line.render()
