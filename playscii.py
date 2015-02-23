import sys, os.path, time

# obnoxious PyOpenGL workaround for py2exe
import platform
if platform.system() == 'Windows':
    import os
    # set env variable so pysdl2 can find sdl2.dll
    os.environ['PYSDL2_DLL_PATH'] = '.'
    sys.path += ['.']

# app imports
import ctypes
import sdl2
import sdl2.ext
from sdl2 import video
from OpenGL import GL
from PIL import Image

# submodules - set here so cfg file can modify them all easily
from shader import ShaderLord
from camera import Camera
from charset import CharacterSet
from palette import Palette
from art import Art, ArtFromDisk, ArtFromEDSCII
from renderable import TileRenderable
from framebuffer import Framebuffer
from art import ART_DIR, ART_FILE_EXTENSION
from ui import UI
from cursor import Cursor
from grid import Grid
from input_handler import InputLord
# some classes are imported only so the cfg file can modify their defaults
from renderable_line import LineRenderable
from ui_swatch import CharacterSetSwatch
from ui_element import UIRenderable

CONFIG_FILENAME = 'playscii.cfg'
CONFIG_TEMPLATE_FILENAME = 'playscii.cfg.default'
LOG_FILENAME = 'console.log'
LOGO_FILENAME = 'ui/logo.png'
SCREENSHOT_SUBDIR = 'screenshots'

VERSION = '0.4.0'

class Application:
    
    window_width, window_height = 800, 600
    fullscreen = False
    # framerate: uncapped if -1
    framerate = 60
    base_title = 'Playscii'
    # force to run even if we can't get an OpenGL 2.1 context
    run_if_opengl_incompatible = False
    # starting document defaults
    starting_charset = 'c64_petscii'
    starting_palette = 'c64_original'
    new_art_width, new_art_height = 8, 8
    # arbitrary size cap, but something bigger = probably a bad idea
    max_art_width, max_art_height = 9999, 9999
    # use capslock as another ctrl key - SDL2 doesn't seem to respect OS setting
    capslock_is_ctrl = False
    bg_color = (0.1, 0.1, 0.1, 1)
    # if True, ignore camera loc saved in .psci files
    override_saved_camera = False
    # debug test stuff
    test_mutate_each_frame = False
    test_life_each_frame = False
    test_art = False
    auto_save = False
    
    def __init__(self, log_file, log_lines, art_filename):
        self.init_success = False
        # log fed in from __main__, might already have stuff in it
        self.log_file = log_file
        self.log_lines = log_lines
        self.elapsed_time = 0
        self.should_quit = False
        self.mouse_x, self.mouse_y = 0, 0
        self.inactive_layer_visibility = 1
        self.version = VERSION
        # last edit came from keyboard or mouse, used by cursor control logic
        self.keyboard_editing = False
        sdl2.ext.init()
        flags = sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE | sdl2.SDL_WINDOW_ALLOW_HIGHDPI
        if self.fullscreen:
            flags = flags | sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
        self.window = sdl2.SDL_CreateWindow(bytes(self.base_title, 'utf-8'), sdl2.SDL_WINDOWPOS_UNDEFINED, sdl2.SDL_WINDOWPOS_UNDEFINED, self.window_width, self.window_height, flags)
        # set ui None so other objects can check it None, eg load_art check
        # for its active art on later runs
        self.ui = None
        # force GL2.1 'core' before creating context
        video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MAJOR_VERSION, 2)
        video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MINOR_VERSION, 1)
        video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_PROFILE_MASK,
                                  video.SDL_GL_CONTEXT_PROFILE_CORE)
        self.context = sdl2.SDL_GL_CreateContext(self.window)
        # report OS, version, CPU
        self.log('OS: %s' % platform.platform())
        self.log('CPU: %s' % platform.processor())
        self.log('Python: %s' % ' '.join(sys.version.split('\n')))
        # report GL version, vendor, GLSL version etc
        # try single-argument GL2.0 version first
        gl_ver = GL.glGetString(GL.GL_VERSION)
        if not gl_ver:
            gl_ver = GL.glGetString(GL.GL_VERSION, ctypes.c_int(0))
        gl_ver = gl_ver.decode('utf-8')
        self.log('OpenGL detected: %s' % gl_ver)
        glsl_ver = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
        if not glsl_ver:
            glsl_ver = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION, ctypes.c_int(0))
        glsl_ver = glsl_ver.decode('utf-8')
        self.log('GLSL detected: %s' % glsl_ver)
        # verify that we got at least a 2.1 context
        majorv, minorv = ctypes.c_int(0), ctypes.c_int(0)
        video.SDL_GL_GetAttribute(video.SDL_GL_CONTEXT_MAJOR_VERSION, majorv)
        video.SDL_GL_GetAttribute(video.SDL_GL_CONTEXT_MINOR_VERSION, minorv)
        context_version = majorv.value + (minorv.value * 0.1)
        vao_support = bool(GL.glGenVertexArrays)
        self.log('Vertex Array Object support %sfound.' % ['NOT ', ''][vao_support])
        if not vao_support  or context_version < 2.1 or gl_ver.startswith('2.0'):
            self.log("Could not create a compatible OpenGL context, your hardware doesn't appear to meet Playscii's requirements!  Sorry ;_________;")
            if not self.run_if_opengl_incompatible:
                self.should_quit = True
                return
        # draw black screen while doing other init
        self.sdl_renderer = sdl2.SDL_CreateRenderer(self.window, -1, sdl2.SDL_RENDERER_ACCELERATED)
        self.blank_screen()
        self.set_icon()
        # SHADERLORD rules shader init/destroy, hot reload
        self.sl = ShaderLord(self)
        self.camera = Camera(self)
        self.art_loaded_for_edit, self.edit_renderables = [], []
        # "game mode" renderables
        self.art_loaded_for_game, self.game_renderables = [], []
        self.game_mode = False
        self.game_objects = []
        # lists of currently loaded character sets and palettes
        self.charsets, self.palettes = [], []
        self.load_art_for_edit(art_filename)
        self.fb = Framebuffer(self)
        # setting cursor None now makes for easier check in status bar drawing
        self.cursor, self.grid = None, None
        # initialize UI with first art loaded active
        self.ui = UI(self, self.art_loaded_for_edit[0])
        # set camera bounds based on art size
        self.camera.max_x = self.ui.active_art.width * self.ui.active_art.quad_width
        self.camera.min_y = -self.ui.active_art.height * self.ui.active_art.quad_height
        self.update_window_title()
        self.cursor = Cursor(self)
        self.grid = Grid(self, self.ui.active_art)
        self.ui.set_active_layer(0)
        self.frame_time, self.fps, self.last_tick_time = 0, 0, 0
        # INPUTLORD rules input handling and keybinds
        self.il = InputLord(self)
        self.init_success = True
        self.log('init done.')
        self.ui.message_line.post_line('Welcome to Playscii! Press SPACE to select characters and colors to paint.', 10)
    
    def set_icon(self):
        # TODO: this doesn't seem to work in Ubuntu, what am i missing?
        img = Image.open(LOGO_FILENAME).convert('RGBA')
        # does icon need to be a specific size?
        img = img.resize((32, 32), Image.ANTIALIAS)
        w, h = img.size
        depth, pitch = 32, w * 4
        #SDL_CreateRGBSurfaceFrom((pixels, width, height, depth, pitch, Rmask, Gmask, Bmask, Amask)
        #mask = (0x0f00, 0x00f0, 0x000f, 0xf000)
        mask = (0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
        icon_surf = sdl2.SDL_CreateRGBSurfaceFrom(img.tobytes(), w, h, depth, pitch, *mask)
        # SDL_SetWindowIcon(self.window, SDL_Surface* icon)
        sdl2.SDL_SetWindowIcon(self.window, icon_surf)
        sdl2.SDL_FreeSurface(icon_surf)
    
    def log(self, new_line):
        "write to log file, stdout, and in-app console log"
        self.log_file.write('%s\n' % new_line)
        self.log_lines.append(new_line)
        print(new_line)
        if self.ui:
            self.ui.message_line.post_line(new_line)
    
    def new_art(self, filename, width=None, height=None):
        width = width or self.new_art_width
        height = height or self.new_art_height
        filename = filename or 'new'
        if not filename.startswith(ART_DIR):
            filename = '%s%s' % (ART_DIR, filename)
        charset = self.load_charset(self.starting_charset)
        palette = self.load_palette(self.starting_palette)
        return Art(filename, self, charset, palette, width, height)
    
    def load_art(self, filename):
        """
        determine a viable filename and load it from disk;
        create new file if unsuccessful
        """
        orig_filename = filename
        filename = filename or 'new'
        # try adding art subdir
        if not os.path.exists(filename):
            filename = '%s%s' % (ART_DIR, filename)
        # if not found, try adding extension
        if not os.path.exists(filename):
            filename += '.%s' % ART_FILE_EXTENSION
        art = None
        # use given path + file name even if it doesn't exist; use as new file's name
        if not os.path.exists(filename):
            text = 'Creating new document %s' % filename
            if orig_filename:
                text = "Couldn't find file %s, %s" % (orig_filename, text)
            self.log(text)
            art = self.new_art(filename)
        else:
            for a in self.art_loaded_for_edit + self.art_loaded_for_game:
                # TODO: this check doesn't work on EDSCII imports b/c its name changes
                if a.filename == filename:
                    return a
            self.log('Loading file %s...' % filename)
            art = ArtFromDisk(filename, self)
            if not art or not art.valid:
                art = ArtFromEDSCII(filename, self)
            # if file failed to load, create a new file with that name
            # TODO: this may be foolish, ensure this never overwrites user data
            if not art or not art.valid:
                art = self.new_art(filename)
        # remember time loaded for UI list sorting
        art.time_loaded = time.time()
        return art
    
    def new_art_for_edit(self, filename, width, height):
        art = self.new_art(filename, width, height)
        self.art_loaded_for_edit.insert(0, art)
        renderable = TileRenderable(self, art)
        self.edit_renderables.insert(0, renderable)
        self.ui.set_active_art(art)
        art.set_unsaved_changes(True)
    
    def load_art_for_edit(self, filename):
        art = self.load_art(filename)
        if art in self.art_loaded_for_edit:
            self.ui.message_line.post_line('Art file %s already loaded' % filename)
            return
        self.art_loaded_for_edit.insert(0, art)
        renderable = TileRenderable(self, art)
        self.edit_renderables.insert(0, renderable)
        if self.ui:
            self.ui.set_active_art(art)
    
    def close_art(self, art):
        if not art in self.art_loaded_for_edit:
            return
        self.art_loaded_for_edit.remove(art)
        for r in art.renderables:
            self.edit_renderables.remove(r)
        if art is self.ui.active_art:
            self.ui.active_art = None
        self.log('Unloaded %s' % art.filename)
        if len(self.art_loaded_for_edit) > 0:
            self.ui.set_active_art(self.art_loaded_for_edit[0])
        self.update_window_title()
    
    def recover_edscii(self, filename, width_override):
        "recovers an incorrectly-saved EDSCII file using the given width"
        art = ArtFromEDSCII(filename, self, width_override)
        self.art_loaded_for_edit.insert(0, art)
        renderable = TileRenderable(self, art)
        self.edit_renderables.insert(0, renderable)
        if self.ui:
            self.ui.set_active_art(art)
    
    def load_charset(self, charset_to_load, log=True):
        "creates and returns a character set with the given name"
        # already loaded?
        for charset in self.charsets:
            if charset_to_load == charset.name:
                return charset
        new_charset = CharacterSet(self, charset_to_load, log)
        if new_charset.init_success:
            self.charsets.append(new_charset)
            return new_charset
        else:
            # if init failed (eg bad filename) return something safe
            return self.ui.active_art.charset
    
    def load_palette(self, palette_to_load, log=True):
        for palette in self.palettes:
            if palette.name == palette_to_load:
                return palette
        new_palette = Palette(self, palette_to_load, log)
        if new_palette.init_success:
            self.palettes.append(new_palette)
            return new_palette
        else:
            # if init failed (eg bad filename) return something safe
            return self.ui.active_art.palette
    
    def set_window_title(self, text=None):
        new_title = self.base_title
        if text:
            new_title += ' - %s' % text
        new_title = bytes(new_title, 'utf-8')
        sdl2.SDL_SetWindowTitle(self.window, new_title)
    
    def update_window_title(self):
        if not self.ui.active_art:
            self.set_window_title()
            return
        # display current active document's name and info
        filename = self.ui.active_art.filename
        if filename and os.path.exists(filename):
            full_filename = os.path.abspath(filename)
        else:
            full_filename = filename
        if self.ui.active_art.unsaved_changes:
            full_filename += '*'
        self.set_window_title(full_filename)
    
    def blank_screen(self):
        r = sdl2.SDL_Rect()
        r.x, r.y = 0,0
        r.w, r.h = self.window_width, self.window_height
        sdl2.SDL_SetRenderDrawColor(self.sdl_renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderFillRect(self.sdl_renderer, r)
        sdl2.SDL_GL_SwapWindow(self.window)
    
    def resize_window(self, new_width, new_height):
        GL.glViewport(0, 0, new_width, new_height)
        self.window_width, self.window_height = new_width, new_height
        # preserve FB state, eg CRT shader enabled
        crt = self.fb.crt
        # create a new framebuffer in its place
        # TODO: determine if it's better to do this or change existing fb
        self.fb = Framebuffer(self)
        self.fb.crt = crt
        # tell camera and UI that view aspect has changed
        self.camera.window_resized()
        self.ui.window_resized()
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = 0
        if self.fullscreen:
            flags = sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP
        sdl2.SDL_SetWindowFullscreen(self.window, flags)
        # for all intents and purposes, this is like resizing the window
        self.resize_window(self.window_width, self.window_height)
    
    def screenshot(self):
        "saves a date + time-stamped screenshot"
        # create screenshot subdir if it doesn't exist
        if not os.path.exists(SCREENSHOT_SUBDIR):
            os.mkdir(SCREENSHOT_SUBDIR)
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        output_filename = 'playscii_%s.png' % timestamp
        w, h = self.window_width, self.window_height
        pixels = GL.glReadPixels(0, 0, w, h, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                                 outputType=None)
        pixel_bytes = pixels.flatten().tobytes()
        img = Image.frombytes(mode='RGBA', size=(w, h), data=pixel_bytes)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save('%s/%s' % (SCREENSHOT_SUBDIR, output_filename))
        self.log('Saved screenshot %s' % output_filename)
    
    def export_image(self, art):
        output_filename = '%s.png' % os.path.splitext(art.filename)[0]
        # determine art's native size in pixels
        w = art.charset.char_width * art.width
        h = art.charset.char_height * art.height
        # TODO: if CRT is on, use that shader for output w/ a scale factor!
        scale = 2 if self.fb.crt and not self.fb.disable_crt else 1
        # create render target
        #export_fb = Framebuffer(self, w * scale, h * scale)
        #GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, export_fb.framebuffer)
        #GL.glClearColor(*self.bg_color)
        #GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        framebuffer = GL.glGenFramebuffers(1)
        render_buffer = GL.glGenRenderbuffers(1)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, render_buffer)
        GL.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_RGBA8, w, h)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, framebuffer)
        GL.glFramebufferRenderbuffer(GL.GL_DRAW_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0,
                                     GL.GL_RENDERBUFFER, render_buffer)
        GL.glViewport(0, 0, w, h)
        GL.glClearColor(0, 0, 0, 0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        # render to it
        art.renderables[0].render_for_export()
        #export_fb.render(self.elapsed_time)
        GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0)
        # read pixels from it
        pixels = GL.glReadPixels(0, 0, w, h, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                                 outputType=None)
        # cleanup / deinit of GL stuff
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glViewport(0, 0, self.window_width, self.window_height)
        GL.glDeleteFramebuffers(1, [framebuffer])
        GL.glDeleteRenderbuffers(1, [render_buffer])
        # GL pixel data as numpy array -> bytes for PIL image export
        pixel_bytes = pixels.flatten().tobytes()
        img = Image.frombytes(mode='RGBA', size=(w, h), data=pixel_bytes)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(output_filename)
        self.log('%s exported' % output_filename)
    
    def enter_game_mode(self):
        self.game_mode = True
    
    def exit_game_mode(self):
        self.game_mode = False
    
    def game_mode_test(self):
        "render quality/perf test for 'game mode'"
        # background w/ parallax layers
        from game_object import GameObject, WobblyThing, ParticleThing
        bg = GameObject(self, 'test_bg')
        bg.set_loc(0, 0, -3)
        self.player = GameObject(self, 'test_player')
        self.player.set_loc(1, -13)
        # spawn a bunch of enemies
        from random import randint
        for i in range(25):
            enemy = WobblyThing(self, 'owell')
            enemy.set_origin(randint(0, 30), randint(-30, 0), randint(-5, 5))
            enemy.start_animating()
        # particle thingy
        smoke1 = ParticleThing(self)
        smoke1.set_loc(25, -10)
        # set camera
        px = self.player.x + self.player.art.width / 2
        self.camera.set_loc(px, self.player.y, self.camera.z)
        self.camera.set_zoom(20)
    
    def main_loop(self):
        while not self.should_quit:
            tick_time = sdl2.timer.SDL_GetTicks()
            self.input()
            self.update()
            self.render()
            self.sl.check_hot_reload()
            elapsed_time = sdl2.timer.SDL_GetTicks()
            # determine frame work time, feed it into delay
            tick_time = elapsed_time - tick_time
            self.delta_time = elapsed_time - self.elapsed_time
            self.elapsed_time = elapsed_time
            # determine FPS
            # alpha: lower = smoother
            alpha = 0.2
            self.frame_time = alpha * self.delta_time + (1 - alpha) * self.frame_time
            self.fps = 1000 / self.frame_time
            # delay to maintain framerate, if uncapped
            if self.framerate != -1:
                delay = int(1000 / self.framerate)
                # subtract work time from delay to maintain framerate
                delay -= min(delay, tick_time)
                sdl2.timer.SDL_Delay(delay)
            self.last_tick_time = tick_time
        return 1
    
    def input(self):
        self.il.input()
    
    def update(self):
        for art in self.art_loaded_for_edit:
            art.update()
        for renderable in self.edit_renderables:
            renderable.update()
        if self.game_mode:
            for game_object in self.game_objects:
                game_object.update()
        self.camera.update()
        if self.test_mutate_each_frame:
            self.test_mutate_each_frame = False
            self.ui.active_art.run_script_every('mutate', 0.01)
        if self.test_life_each_frame:
            self.test_life_each_frame = False
            self.ui.active_art.run_script_every('conway', 0.05)
        if self.test_art:
            self.test_art = False
            # load some test data - simulates some user edits:
            # add layers, write text, duplicate that frame, do some animation
            self.ui.active_art.run_script('hello1')
        # test saving functionality
        if self.auto_save:
            art.save_to_file()
            self.auto_save = False
        if self.ui.active_art and not self.ui.popup.visible and not self.ui.console.visible and not self.game_mode and not self.ui.menu_bar in self.ui.hovered_elements and not self.ui.menu_bar.active_menu_name and not self.ui.active_dialog:
            self.cursor.update(self.elapsed_time)
        if self.ui.visible:
            self.ui.update()
        if not self.game_mode:
            self.grid.update()
            self.cursor.end_update()
    
    class RenderItem:
        "quickie class to debug render order"
        def __init__(self, game_object, layer, layer_z):
            self.game_object, self.layer, self.layer_z = game_object, layer, layer_z
        def __str__(self):
            return '%s layer %s z %s' % (self.game_object.art.filename, self.layer, self.layer_z)
    
    def game_render(self):
        # sort objects for drawing by each layer Z order
        draw_order = []
        for game_object in self.game_objects:
            for i,z in enumerate(game_object.art.layers_z):
                z += game_object.z
                item = self.RenderItem(game_object, i, z)
                draw_order.append(item)
        draw_order.sort(key=lambda item: item.layer_z, reverse=False)
        for item in draw_order:
            item.game_object.render(item.layer)
    
    def render(self):
        # draw main scene to framebuffer
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fb.framebuffer)
        GL.glClearColor(*self.bg_color)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        if self.game_mode:
            self.game_render()
        else:
            for r in self.edit_renderables:
                r.render()
            # draw selection grid, then selection, then cursor
            if self.grid.visible and self.ui.active_art:
                self.grid.render()
            self.ui.select_tool.render_selections()
            if self.ui.active_art and not self.ui.popup.visible and not self.ui.console.visible and not self.ui.menu_bar in self.ui.hovered_elements and not self.ui.menu_bar.active_menu_name and not self.ui.active_dialog:
                self.cursor.render()
        # draw framebuffer to screen
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        self.fb.render(self.elapsed_time)
        if self.ui.visible:
            self.ui.render()
        GL.glUseProgram(0)
        sdl2.SDL_GL_SwapWindow(self.window)
    
    def quit(self):
        self.log('Thank you for using Playscii!  <3')
        if self.init_success:
            for r in self.edit_renderables:
                r.destroy()
            self.fb.destroy()
            self.ui.destroy()
            for charset in self.charsets:
                charset.texture.destroy()
            for palette in self.palettes:
                palette.texture.destroy()
            self.sl.destroy()
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()
        self.log_file.close()


if __name__ == "__main__":
    file_to_load = None
    # start log file even before Application has initialized so we can write to it
    log_file = open(LOG_FILENAME, 'w')
    log_lines = []
    # startup message: application and version #
    line = '%s v%s' % (Application.base_title, VERSION)
    log_file.write('%s\n' % line)
    log_lines.append(line)
    print(line)
    # load in config - may change above values and submodule class defaults
    if os.path.exists(CONFIG_FILENAME):
        exec(open(CONFIG_FILENAME).read())
    # if cfg file doesn't exist, copy a new one from playscii.cfg.default
    else:
        # snip first "this is a template" line
        default_data = open(CONFIG_TEMPLATE_FILENAME).readlines()[1:]
        new_cfg = open(CONFIG_FILENAME, 'w')
        new_cfg.writelines(default_data)
        new_cfg.close()
        exec(''.join(default_data))
        line = 'Created new config file %s' % CONFIG_FILENAME
        log_file.write('%s\n' % line)
        log_lines.append(line)
        print(line)
    file_to_load = None
    if len(sys.argv) > 1:
        file_to_load = sys.argv[1]
    app = Application(log_file, log_lines, file_to_load)
    error = app.main_loop()
    app.quit()
    sys.exit(error)
