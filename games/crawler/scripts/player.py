
from game_object import GameObject
from game_util_objects import Player

from games.crawler.scripts.crawler import DIR_NORTH, DIR_SOUTH, DIR_EAST, DIR_WEST, LEFT_TURN_DIRS, RIGHT_TURN_DIRS, DIR_NAMES, OPPOSITE_DIRS


class CrawlPlayer(Player):
    should_save = False # we are spawned by maze
    generate_art = True
    art_width, art_height = 1, 1
    art_charset, art_palette = 'jpetscii', 'c64_pepto'
    art_off_pct_x, art_off_pct_y = 0, 0
    # bespoke grid-based movement method
    physics_move = False
    handle_key_events = True
    
    view_range_tiles = 8
    fg_color = 8 # yellow
    dir_chars = { DIR_NORTH: 147,
                  DIR_SOUTH: 163,
                  DIR_EAST: 181,
                  DIR_WEST: 180
    }
    
    def pre_first_update(self):
        Player.pre_first_update(self)
        # top-down facing
        self.direction = DIR_NORTH
        self.maze.update_tile_visibilities()
        self.art.set_tile_at(0, 0, 0, 0, self.dir_chars[self.direction], self.fg_color)
    
    def handle_key_down(self, key, shift_pressed, alt_pressed, ctrl_pressed):
        # turning?
        if key == 'left':
            self.direction = LEFT_TURN_DIRS[self.direction]
        elif key == 'right':
            self.direction = RIGHT_TURN_DIRS[self.direction]
        # moving?
        elif key == 'up' or key == 'down':
            x, y = self.maze.get_tile_at_point(self.x, self.y)
            if key == 'up':
                new_x = x + self.direction[0]
                new_y = y + self.direction[1]
            else:
                new_x = x - self.direction[0]
                new_y = y - self.direction[1]
            # is move valid?
            if self.maze.is_tile_solid(new_x, new_y):
                # TEMP negative feedback
                dir_name = DIR_NAMES[self.direction] if key == 'up' else DIR_NAMES[OPPOSITE_DIRS[self.direction]]
                self.app.log("can't go %s!" % dir_name)
            else:
                self.x, self.y = self.maze.x + new_x, self.maze.y - new_y
        # update art to show facing
        self.art.set_char_index_at(0, 0, 0, 0, self.dir_chars[self.direction])
        # update maze tiles
        self.maze.update_tile_visibilities()
