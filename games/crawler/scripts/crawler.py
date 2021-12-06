 
from game_object import GameObject

# initial work: 2019-02-17 and 18
# FP view research: 2021-11-22

"""
wall art breakdown:
what are the maze tiles ahead of the viewer?
left / center / right, at different distances (1 tile away, 2 tiles away, etc)
the further away the tiles, the wider a swath of them we need to composite

each "tile" -> a vertical slice for each grid square that shows either a wall or an empty space

art.composite_to(src_frame, src_layer, src_x, src_y, width, height,
             dest_art, dest_frame, dest_layer, dest_x, dest_y)
(art.composite_from)

very useful:
https://weblogs.asp.net/bleroy/dungeon-master
"just draw the entire left/right perspective wall and clip out portions of it where there's a passage" method = good

face-on wall tilers: "distance 0", "distance 1", etc

naming:
"left 1 (1 tile immediately to our left) distance 3 (3 tiles away from POV)", "front distance 2 (2 tiles from POV)", etc

"""

DIR_NORTH = (0, -1)
DIR_SOUTH = (0, 1)
DIR_EAST = (1, 0)
DIR_WEST = (-1, 0)
LEFT_TURN_DIRS = { DIR_NORTH: DIR_WEST, DIR_WEST: DIR_SOUTH,
                   DIR_SOUTH: DIR_EAST, DIR_EAST: DIR_NORTH }
RIGHT_TURN_DIRS = { DIR_NORTH: DIR_EAST, DIR_EAST: DIR_SOUTH,
                    DIR_SOUTH: DIR_WEST, DIR_WEST: DIR_NORTH }
DIR_NAMES = { DIR_NORTH: 'north', DIR_SOUTH: 'south',
              DIR_EAST: 'east', DIR_WEST: 'west' }
OPPOSITE_DIRS = { DIR_NORTH: DIR_SOUTH, DIR_SOUTH: DIR_NORTH,
                  DIR_EAST: DIR_WEST, DIR_WEST: DIR_EAST }


class CompositeTester(GameObject):
    # slightly confusing terms here, our "source" will be loaded at runtime
    art_src = 'comptest_dest'
    use_art_instance = True
    
    def pre_first_update(self):
        # load composite source art
        comp_src_art = self.app.load_art('comptest_src', False)
        self.art.composite_from(comp_src_art, 0, 0, 0, 0,
                                comp_src_art.width, comp_src_art.height,
                                0, 0, 3, 2)
