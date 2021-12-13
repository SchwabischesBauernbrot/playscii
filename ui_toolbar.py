
from ui_element import UIElement
from ui_button import UIButton

from cursor import Cursor

from renderable_sprite import UISpriteRenderable
from renderable_line import ToolSelectionBoxRenderable


class ToolBar(UIElement):
    
    tile_width, tile_height = 4, 1
    snap_left = True
    
    def __init__(self, ui):
        self.ui = ui
        self.icon_renderables = []
        self.create_toolbar_buttons()
        UIElement.__init__(self, ui)
        self.selection_box = ToolSelectionBoxRenderable(ui.app, self.art)
    
    def reset_art(self):
        # by default, a 1D vertical bar
        self.tile_width = ToolBarButton.width
        # dynamically set height based on # of buttons
        self.tile_height = ToolBarButton.height * len(self.buttons)
        self.art.resize(self.tile_width, self.tile_height)
        UIElement.reset_art(self)
    
    def reset_loc(self):
        UIElement.reset_loc(self)
        # by default, a vertical bar centered along left edge of the screen
        height = self.art.quad_height * len(self.buttons) * self.buttons[0].height
        self.y = height / 2
        # (x is set by snap_left property in UIElement.reset_loc)
        self.renderable.x, self.renderable.y = self.x, self.y
        # scale and position button icons only now that we're positioned
        self.reset_button_icons()
    
    def create_toolbar_buttons(self):
        # (override in subclass)
        pass
    
    def update_selection_box(self):
        # (override in subclass)
        pass
    
    def update(self):
        UIElement.update(self)
        self.update_selection_box()
    
    def render(self):
        UIElement.render(self)
        for r in self.icon_renderables:
            r.render()
        self.selection_box.render()


class ToolBarButton(UIButton):
    width, height = 4, 2
    caption = ''


class ArtToolBar(ToolBar):
    
    def create_toolbar_buttons(self):
        for i,tool in enumerate(self.ui.tools):
            button = ToolBarButton(self)
            # button.caption = tool.button_caption # DEBUG
            button.x = 0
            button.y = i * button.height
            # alternate colors
            button.normal_bg_color = self.ui.colors.lightgrey if i % 2 == 0 else self.ui.colors.medgrey
            # callback: tell ui to set this tool as selected
            button.callback = self.ui.set_selected_tool
            button.cb_arg = tool
            self.buttons.append(button)
            # create button icon
            sprite = UISpriteRenderable(self.ui.app, self.ui.asset_dir + tool.icon_filename)
            self.icon_renderables.append(sprite)
    
    def reset_button_icons(self):
        scale_factor = Cursor.icon_scale_factor
        aspect = self.ui.app.window_height / self.ui.app.window_width
        button_height = self.art.quad_height * ToolBarButton.height
        for i,icon in enumerate(self.icon_renderables):
            # scale: same screen size as cursor icon
            scale_x = icon.texture.width / self.ui.app.window_width
            scale_x *= aspect * scale_factor * self.ui.scale
            icon.scale_x = scale_x
            scale_y = icon.texture.height / self.ui.app.window_height
            scale_y *= aspect * scale_factor * self.ui.scale
            icon.scale_y = scale_y
            # position
            # remember that in renderable space, (0, 0) = center of screen
            icon.x = self.x
            icon.x += (icon.scale_x / 4) * aspect # pad a little
            icon.y = self.y
            icon.y -= button_height * i
            icon.y -= icon.scale_y
            icon.y -= (icon.scale_y / 8) * aspect
    
    def update_selection_box(self):
        # scale and position box around currently selected tool
        self.selection_box.scale_x = ToolBarButton.width
        self.selection_box.scale_y = ToolBarButton.height
        self.selection_box.x = self.x
        self.selection_box.y = self.y
        sel_index = self.ui.tools.index(self.ui.selected_tool)
        self.selection_box.y -= sel_index * self.art.quad_height * ToolBarButton.height
