
from game_object import GameObject
from vector import get_tiles_along_integer_line

from art import TileIter

from random import randint  # DEBUG

from games.crawler.scripts.crawler import DIR_NORTH, DIR_SOUTH, DIR_EAST, DIR_WEST, LEFT_TURN_DIRS, RIGHT_TURN_DIRS, DIR_NAMES, OPPOSITE_DIRS


class CrawlTopDownView(GameObject):
    art_src = 'maze2'
    art_off_pct_x, art_off_pct_y = 0, 0
    # we will be modifying this view at runtime so don't write on the source art
    use_art_instance = True
    # first character we find with this index will be where we spawn player
    playerstart_char_index = 147
    # undiscovered = player has never seen this tile
    undiscovered_color_index = 1 # black
    # discovered = player has seen this tile but isn't currently looking at it
    discovered_color_index = 12 # dark grey
    
    def pre_first_update(self):
        # scan art for spot to spawn player
        player_x, player_y = -1, -1
        for frame, layer, x, y in TileIter(self.art):
            if self.art.get_char_index_at(frame, layer, x, y) == self.playerstart_char_index:
                player_x, player_y = self.x + x, self.y - y
                # clear the tile at this spot in our art
                self.art.set_char_index_at(frame, layer, x, y, 0)
                break
        self.world.player = self.world.spawn_object_of_class('CrawlPlayer', player_x, player_y)
        # give player a ref to us
        self.world.player.maze = self
        # make a copy of original layer to color for visibility, hide original
        self.art.duplicate_layer(0)
        self.art.layers_visibility[0] = False
        for frame, layer, x, y in TileIter(self.art):
            if layer == 0:
                continue
            # set all tiles undiscovered
            self.art.set_color_at(0, layer, x, y, self.undiscovered_color_index)
        self.art.mark_all_frames_changed() # DEBUG - this fixes the difference in result when use_art_instance=True! why?
        # keep a list of tiles player can see
        self.player_visible_tiles = []
    
    def is_tile_solid(self, x, y):
        return self.art.get_char_index_at(0, 0, x, y) != 0
    
    # world to tile: self.get_tile_at_point(world_x, world_y)
    # tile to world: self.get_tile_loc(tile_x, tile_y)
    
    def get_visible_tiles(self, x, y, dir_x, dir_y, tile_range, see_thru_walls=False):
        "return tiles visible from given point facing given direction"
        # NOTE: all the calculations here are done in this object's art's tile
        # coordinates, not world space. so -Y is up/north, -X is left/west.
        tiles = []
        # find back left corner of frustum and direction to scan along
        if (dir_x, dir_y) == DIR_NORTH:
            scan_start_x, scan_start_y = x - tile_range, y - tile_range
            scan_dir_x, scan_dir_y = 1, 0
        elif (dir_x, dir_y) == DIR_SOUTH:
            scan_start_x, scan_start_y = x + tile_range, y + tile_range
            scan_dir_x, scan_dir_y = -1, 0
        elif (dir_x, dir_y) == DIR_EAST:
            scan_start_x, scan_start_y = x + tile_range, y - tile_range
            scan_dir_x, scan_dir_y = 0, 1
        elif (dir_x, dir_y) == DIR_WEST:
            scan_start_x, scan_start_y = x - tile_range, y + tile_range
            scan_dir_x, scan_dir_y = 0, -1
        # scan back of frustum tile by tile left to right,
        # checking each tile hit
        scan_distance = 0
        scan_length = tile_range * 2 + 1 # TODO make sure this is correct
        while scan_distance < scan_length:
            scan_x = scan_start_x + (scan_dir_x * scan_distance)
            scan_y = scan_start_y + (scan_dir_y * scan_distance)
            hit_tiles = get_tiles_along_integer_line(x, y, scan_x, scan_y)
            for tile in hit_tiles:
                tile_x, tile_y = tile[0], tile[1]
                # skip out-of-bounds tiles
                if 0 > tile_x or tile_x >= self.art.width or \
                   0 > tile_y or tile_y >= self.art.height:
                    continue
                # whether this tile is solid or not, we have seen it
                if not tile in tiles:
                    tiles.append((tile_x, tile_y))
                if not see_thru_walls and self.is_tile_solid(*tile):
                    break
            scan_distance += 1
        return tiles
    
    def update_tile_visibilities(self):
        """
        update our art's tile visuals based on what tiles can be, can't be,
        or have been seen.
        """
        previously_visible_tiles = self.player_visible_tiles[:]
        p = self.world.player
        px, py = self.get_tile_at_point(p.x, p.y)
        self.player_visible_tiles = self.get_visible_tiles(px, py,
                                                           *p.direction,
                                                           p.view_range_tiles,
                                                           see_thru_walls=False)
        #print(self.player_visible_tiles)
        # color currently visible tiles
        for tile in self.player_visible_tiles:
            #print(tile)
            if 0 > tile[0] or tile[0] >= self.art.width or \
               0 > tile[1] or tile[1] >= self.art.height:
                continue
            if self.is_tile_solid(*tile):
                orig_color = self.art.get_fg_color_index_at(0, 0, *tile)
                self.art.set_color_at(0, 1, *tile, orig_color)
            else:
                #self.art.set_color_at(0, 1, *tile, randint(2, 14)) # DEBUG
                pass
        # color "previously seen" tiles
        for tile in previously_visible_tiles:
            if not tile in self.player_visible_tiles and \
               self.is_tile_solid(*tile):
                self.art.set_color_at(0, 1, *tile, self.discovered_color_index)
