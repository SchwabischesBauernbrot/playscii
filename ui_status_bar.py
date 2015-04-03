import os.path, time
from math import ceil

from ui_element import UIElement, UIArt, UIRenderable
from renderable_line import UIRenderableX
from art import uv_names

class StatusBarUI(UIElement):
    
    snap_bottom = True
    snap_left = True
    dim_color = 12
    char_label = 'ch:'
    fg_label = 'fg:'
    bg_label = 'bg:'
    xform_label = 'xform:'
    swatch_width = 3
    char_label_x = 1
    char_swatch_x = char_label_x + len(char_label)
    fg_label_x = char_swatch_x + swatch_width + 1
    fg_swatch_x = fg_label_x + len(fg_label)
    bg_label_x = fg_swatch_x + swatch_width + 1
    bg_swatch_x = bg_label_x + len(bg_label)
    xform_label_x = bg_swatch_x + swatch_width + 1
    xform_selected_width = len('Rotate 180')
    xform_selected_x = xform_label_x + len(xform_label)
    tool_label = 'tool:'
    tool_label_x = xform_selected_x + xform_selected_width + 2
    tool_selection_x = tool_label_x + len(tool_label)
    # total width of left-justified items
    left_items_width = tool_selection_x + 7
    tile_label = 'tile:'
    layer_label = 'layer:'
    frame_label = 'frame:'
    right_items_width = len(tile_label) + len(layer_label) + len(frame_label) + (len('X/Y') + 2) * 2 + len('XX/YY') + 2 + 10
    
    def __init__(self, ui):
        art = ui.active_art
        # create 3 custom Arts w/ source charset and palette, renderables for each
        art_name = '%s_%s' % (int(time.time()), self.__class__.__name__)
        self.char_art = UIArt(art_name, ui.app, art.charset, art.palette, self.swatch_width, 1)
        self.char_renderable = UIRenderable(ui.app, self.char_art)
        self.fg_art = UIArt(art_name, ui.app, art.charset, art.palette, self.swatch_width, 1)
        self.fg_renderable = UIRenderable(ui.app, self.fg_art)
        self.bg_art = UIArt(art_name, ui.app, art.charset, art.palette, self.swatch_width, 1)
        self.bg_renderable = UIRenderable(ui.app, self.bg_art)
        # "dimmed out" box
        self.dim_art = UIArt(art_name, ui.app, ui.charset, ui.palette, self.swatch_width + len(self.char_label), 1)
        self.dim_renderable = UIRenderable(ui.app, self.dim_art)
        self.dim_renderable.alpha = 0.75
        # set some properties in bulk
        self.renderables = []
        for r in [self.char_renderable, self.fg_renderable, self.bg_renderable, self.dim_renderable]:
            r.ui = ui
            r.grain_strength = 0
            # add to list of renderables to manage eg destroyed on quit
            self.renderables.append(r)
        # red X for transparent colors
        self.x_renderable = UIRenderableX(ui.app, self.char_art)
        # give it a special reference to this element
        self.x_renderable.status_bar = self
        self.renderables.append(self.x_renderable)
        UIElement.__init__(self, ui)
    
    def reset_art(self):
        UIElement.reset_art(self)
        self.tile_width = ceil(self.ui.width_tiles * self.ui.scale)
        # must resize here, as window width will vary
        self.art.resize(self.tile_width, self.tile_height)
        # write chars/colors to the art
        self.rewrite_art()
        self.x_renderable.scale_x = self.char_art.width
        self.x_renderable.scale_y = -self.char_art.height
        # dim box
        self.dim_art.clear_frame_layer(0, 0, self.ui.colors.white)
        self.dim_art.update()
        # rebuild geo, elements may be new dimensions
        self.dim_art.geo_changed = True
        self.char_art.geo_changed = True
        self.fg_art.geo_changed = True
        self.bg_art.geo_changed = True
    
    def rewrite_art(self):
        bg = self.ui.colors.white
        self.art.clear_frame_layer(0, 0, bg)
        # if user is making window reeeeally skinny, bail
        if self.tile_width < self.left_items_width:
            return
        self.write_left_elements()
        # only draw right side info if the window is wide enough
        if self.art.width > self.left_items_width + self.right_items_width:
            self.write_right_elements()
    
    def set_active_charset(self, new_charset):
        self.char_art.charset = self.fg_art.charset = self.bg_art.charset = new_charset
        self.reset_art()
    
    def set_active_palette(self, new_palette):
        self.char_art.palette = self.fg_art.palette = self.bg_art.palette = new_palette
        self.reset_art()
    
    def update(self):
        # set color swatches
        for i in range(self.swatch_width):
            self.char_art.set_color_at(0, 0, i, 0, self.ui.selected_bg_color, False)
            self.fg_art.set_color_at(0, 0, i, 0, self.ui.selected_fg_color, False)
            self.bg_art.set_color_at(0, 0, i, 0, self.ui.selected_bg_color, False)
        # set char w/ correct FG color
        self.char_art.set_char_index_at(0, 0, 1, 0, self.ui.selected_char)
        self.char_art.set_color_at(0, 0, 1, 0, self.ui.selected_fg_color, True)
        # position elements
        self.position_swatch(self.char_renderable, self.char_swatch_x)
        self.position_swatch(self.fg_renderable, self.fg_swatch_x)
        self.position_swatch(self.bg_renderable, self.bg_swatch_x)
        for art in [self.char_art, self.fg_art, self.bg_art]:
            art.update()
        self.rewrite_art()
    
    def position_swatch(self, renderable, x_offset):
        renderable.x = (self.char_art.quad_width * x_offset) - 1
        renderable.y = self.char_art.quad_height - 1
    
    def reset_loc(self):
        UIElement.reset_loc(self)
    
    def write_left_elements(self):
        """
        fills in left-justified parts of status bar, eg labels for selected
        character/color/tool sections
        """
        # draw labels first
        color = self.ui.palette.darkest_index
        self.art.write_string(0, 0, self.char_label_x, 0, self.char_label, color)
        self.art.write_string(0, 0, self.fg_label_x, 0, self.fg_label, color)
        self.art.write_string(0, 0, self.bg_label_x, 0, self.bg_label, color)
        self.art.write_string(0, 0, self.xform_label_x, 0, self.xform_label, color)
        self.art.write_string(0, 0, self.tool_label_x, 0, self.tool_label, color)
        # draw selections (tool, xform)
        color = self.ui.colors.white
        bg = self.ui.colors.black
        xform_selection = uv_names[self.ui.selected_xform]
        self.art.write_string(0, 0, self.xform_selected_x, 0, xform_selection, color, bg)
        # get name of tool from UI
        tool_selection = ' %s ' % self.ui.selected_tool.button_caption
        self.art.write_string(0, 0, self.tool_selection_x, 0, tool_selection, color, bg)
    
    def write_right_elements(self):
        """
        fills in right-justified parts of status bar, eg current
        frame/layer/tile and filename
        """
        dark = self.ui.colors.black
        light = self.ui.colors.white
        padding = 2
        x = self.tile_width - 1
        art = self.ui.active_art
        # filename
        filename = ' [nothing] '
        if art:
            filename = ' %s ' % os.path.basename(art.filename)
        # use "right justify" final arg of write_string
        self.art.write_string(0, 0, x, 0, filename, light, dark, True)
        x += -padding - len(filename)
        # tile
        tile = 'X/Y'
        color = light
        if self.ui.app.cursor and art:
            tile_x, tile_y = self.ui.app.cursor.get_tile()
            tile_y = int(tile_y)
            # user-facing coordinates are always base 1
            tile_x += 1
            tile_y += 1
            if tile_x <= 0 or tile_x > art.width:
                color = self.dim_color
            if tile_y <= 0 or tile_y > art.height:
                color = self.dim_color
            tile_x = str(tile_x).rjust(3)
            tile_y = str(tile_y).rjust(3)
            tile = '%s,%s' % (tile_x, tile_y)
        self.art.write_string(0, 0, x, 0, tile, color, dark, True)
        x -= len(tile)
        self.art.write_string(0, 0, x, 0, self.tile_label, dark, light, True)
        x += -padding - len(self.tile_label)
        # layer
        layers = art.layers if art else 0
        layer = '%s/%s' % (art.active_layer + 1, layers) if art else 'n/a'
        self.art.write_string(0, 0, x, 0, layer, light, dark, True)
        x -= len(layer)
        self.art.write_string(0, 0, x, 0, self.layer_label, dark, light, True)
        x += -padding - len(self.layer_label)
        # frame
        frames = art.frames if art else 0
        frame = '%s/%s' % (art.active_frame + 1, frames) if art else 'n/a'
        self.art.write_string(0, 0, x, 0, frame, light, dark, True)
        x -= len(frame)
        self.art.write_string(0, 0, x, 0, self.frame_label, dark, light, True)
    
    def render(self):
        UIElement.render(self)
        # draw wireframe red X /behind/ char if BG transparent
        if self.ui.selected_bg_color == 0:
            self.x_renderable.x = self.char_renderable.x
            self.x_renderable.y = self.char_renderable.y
            self.x_renderable.render()
        self.char_renderable.render()
        self.fg_renderable.render()
        self.bg_renderable.render()
        # draw red X for transparent FG or BG
        if self.ui.selected_fg_color == 0:
            self.x_renderable.x = self.fg_renderable.x
            self.x_renderable.y = self.fg_renderable.y
            self.x_renderable.render()
        if self.ui.selected_bg_color == 0:
            self.x_renderable.x = self.bg_renderable.x
            self.x_renderable.y = self.bg_renderable.y
            self.x_renderable.render()
        # dim out items if brush is set to not affect them
        self.dim_renderable.y = self.char_renderable.y
        if not self.ui.selected_tool.affects_char:
            self.dim_renderable.x = self.char_renderable.x - self.art.quad_width * len(self.char_label)
            self.dim_renderable.render()
        if not self.ui.selected_tool.affects_fg_color:
            self.dim_renderable.x = self.fg_renderable.x - self.art.quad_width * len(self.fg_label)
            self.dim_renderable.render()
        if not self.ui.selected_tool.affects_bg_color:
            self.dim_renderable.x = self.bg_renderable.x - self.art.quad_width * len(self.bg_label)
            self.dim_renderable.render()
        if not self.ui.selected_tool.affects_xform:
            # render dim renderable thrice to cover label and item
            self.dim_renderable.x = self.xform_label_x * self.art.quad_width - 1
            self.dim_renderable.render()
            self.dim_renderable.x = self.xform_selected_x * self.art.quad_width - 1
            self.dim_renderable.render()
            self.dim_renderable.x = (self.xform_selected_x + 6) * self.art.quad_width - 1
            self.dim_renderable.render()
