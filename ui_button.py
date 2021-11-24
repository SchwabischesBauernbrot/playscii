
from ui_colors import UIColors

TEXT_LEFT = 0
TEXT_CENTER = 1
TEXT_RIGHT = 2

BUTTON_STATES = ['normal', 'hovered', 'clicked', 'dimmed']

class UIButton:
    
    "clickable button that does something in a UIElement"
    
    # x/y/width/height given in tile scale
    x, y = 0, 0
    width, height = 1, 1
    caption = 'TEST'
    caption_justify = TEXT_LEFT
    # paint caption from string, or not
    should_draw_caption = True
    caption_y = 0
    callback = None
    normal_fg_color = UIColors.black
    normal_bg_color = UIColors.lightgrey
    hovered_fg_color = UIColors.black
    hovered_bg_color = UIColors.white
    clicked_fg_color = UIColors.white
    clicked_bg_color = UIColors.black
    dimmed_fg_color = UIColors.black
    dimmed_bg_color = UIColors.medgrey
    # dimmed is a special, alternative-to-normal state
    dimmed = False
    can_hover = True
    can_click = True
    visible = True
    # if true, this button is invisible and used for special trickery
    never_draw = False
    # weird (gross?) thing: other code can stash an argument to callback here
    cb_arg = None
    # if True, pass in mouse button #
    pass_mouse_button = False
    # if true, clear all characters before painting a new caption
    clear_before_caption_draw = False
    # if true, display a tooltip when hovered, and dismiss it when unhovered.
    # contents set from get_tooltip_text and positioned by get_tooltip_location.
    tooltip_on_hover = False
    
    def __init__(self, element, starting_state=None):
        self.element = element
        self.state = starting_state or 'normal'
    
    def log_event(self, event_type):
        "common code for button event logging"
        if self.element.ui.logg:
            self.element.ui.app.log("UIButton: %s's %s %s" % (self.element.__class__.__name__, self.__class__.__name__, event_type))
    
    def set_state(self, new_state):
        if not new_state in BUTTON_STATES:
            self.element.ui.app.log('Unrecognized state for button %s: %s' % (self.__class__.__name__, new_state))
            return
        self.dimmed = new_state == 'dimmed'
        self.state = new_state
        self.set_state_colors()
    
    def get_state_colors(self, state):
        fg = getattr(self, '%s_fg_color' % state)
        bg = getattr(self, '%s_bg_color' % state)
        return fg, bg
    
    def set_state_colors(self):
        if self.never_draw:
            return
        # set colors for entire button area based on current state
        if self.dimmed and self.state == 'normal':
            self.state = 'dimmed'
        # just bail if we're trying to draw something out of bounds
        if self.x + self.width > self.element.art.width:
            return
        elif self.y + self.height > self.element.art.height:
            return
        fg, bg = self.get_state_colors(self.state)
        for y in range(self.height):
            for x in range(self.width):
                self.element.art.set_tile_at(0, 0, self.x + x, self.y + y, None, fg, bg)
    
    def update_tooltip(self):
        tt = self.element.ui.tooltip
        tt.reset_art()
        tt.set_text(self.get_tooltip_text())
        tt.tile_x, tt.tile_y = self.get_tooltip_location()
        tt.reset_loc()
    
    def hover(self):
        self.log_event('hovered')
        self.set_state('hovered')
        if self.tooltip_on_hover:
            self.element.ui.tooltip.visible = True
            self.update_tooltip()
    
    def unhover(self):
        self.log_event('unhovered')
        if self.dimmed:
            self.set_state('dimmed')
        else:
            self.set_state('normal')
        if self.tooltip_on_hover:
            # if two buttons are adjacent, we might be unhovering this one
            # right after hovering the other in the same frame. if so,
            # don't dismiss the tooltip
            another_tooltip = False
            for b in self.element.hovered_buttons:
                if b is self:
                    continue
                if b.tooltip_on_hover:
                    another_tooltip = True
            if not another_tooltip:
                self.element.ui.tooltip.visible = False
    
    def click(self):
        self.log_event('clicked')
        self.set_state('clicked')
    
    def unclick(self):
        self.log_event('unclicked')
        if self in self.element.hovered_buttons:
            self.hover()
        else:
            self.unhover()
    
    def get_tooltip_text(self):
        "override in a subclass to define this button's tooltip text"
        return 'ERROR'
    
    def get_tooltip_location(self):
        "override in a subclass to define this button's tooltip screen location"
        return 10, 10
    
    def draw_caption(self):
        y = self.y + self.caption_y
        text = self.caption
        # trim if too long
        text = text[:self.width]
        if self.caption_justify == TEXT_CENTER:
            text = text.center(self.width)
        elif self.caption_justify == TEXT_RIGHT:
            text = text.rjust(self.width)
        # just bail if we're trying to draw something out of bounds
        if self.x + len(text) > self.element.art.width:
            return
        if self.clear_before_caption_draw:
            for ty in range(self.height):
                for tx in range(self.width):
                    self.element.art.set_char_index_at(0, 0, self.x+tx, y+ty, 0)
        # leave FG color None; should already have been set
        self.element.art.write_string(0, 0, self.x, y, text, None)
    
    def draw(self):
        if self.never_draw:
            return
        self.set_state_colors()
        if self.should_draw_caption:
            self.draw_caption()
