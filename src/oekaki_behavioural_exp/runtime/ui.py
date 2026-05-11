import collections
from collections import deque

from scipy.interpolate import interp1d

import app_config
import corrector
import i18n
import experiment_data
from pygame_constants import *

# Short alias to keep references to app_config.experiment concise.
_exp = app_config.experiment


class PUI:
    __singleton = None

    def __new__(cls, *args, **kwargs):
        if cls.__singleton is None:
            cls.__singleton = super().__new__(cls)
        return cls.__singleton

    def __init__(self, jfont, fonts, screen):
        self.jfont = jfont
        self.fonts = fonts
        self.font = fonts[36]
        self.screen = screen

    def showtext(self, screen, pos, text, color, bgcolor):
        textimg = self.font.render(text, 1, color, bgcolor)
        self.screen.blit(textimg, pos)
        return pos[0] + textimg.get_width() + 5, pos[1]


class TextBox:
    def __init__(self, ui, surface, string, x=0, y=0, size=36, fg=None, bg=None):
        (self.__x, self.__y) = x, y
        (self.__w, self.__h) = size * len(string.strip()), size
        self.__fg: (int, int, int) = CDEF_CROSS_BLACK if not fg else fg
        self.__bg: (int, int, int) = CDEF_CROSS_WHITE if not bg else bg
        self.string: str = string
        self.__ui: PUI = ui
        self.__surface = surface
        self.__size = size

    def render(self, align: int = 0, delimiter='\n'):
        # Size calculation. align: 0=top-left at (x,y), 1=center, 2=left (not implemented), 3=right (not implemented).
        strings: list = self.string.split(delimiter)
        i: int = 0
        for chunk in strings:
            if chunk == '':
                continue
            _w, _h = self.__ui.fonts[self.__size].size(chunk)
            baked: pygame.Surface = self.__ui.fonts[self.__size].render(chunk, True, self.__fg, self.__bg)
            pos = baked.get_rect()
            if align == 0:
                pos.x, pos.y = self.__x, self.__y + _h * i
                # pos.w,pos.h = self.__w,self.__h
            elif align == 1:
                pos.centerx = self.__x  # self.__ui.screen.get_rect().centerx
                pos.centery = self.__y + _h * i  # self.__ui.screen.get_rect().centery + _h * i
            pos.h += _h * i
            i += 1
            fixed_pos = (pos[0] + FULLSCREEN_MARGIN[0], pos[1] + FULLSCREEN_MARGIN[1])
            self.__surface.blit(baked, pos)


class RestUIColorMode:
    # Local color id constants
    PLAIN = 0
    CROSS_BLACK = 1
    CROSS_WHITE = 2
    CROSS_COLPAT1 = 3
    CROSS_COLPAT2 = 4
    LIGHT_GRAY = 5
    DARK_GRAY = 6
    UI_ACCENT = 7
    UI_ACCENT2 =8
    CROSS_WHITE2 = 9 # CDEF_CROSS_COLPAT2_A dummy
    CROSS_RED = 10 #CDEF_CROSS_COLPAT2_B
    CROSS_YELLOW = 11 #CDEF_CROSS_COLPAT3_A
    CROSS_BLUE = 12 #CDEF_CROSS_COLPAT3_B


    @classmethod
    def get_color2 (self, mode):
        if mode == self.PLAIN:
            return
        elif mode == self.CROSS_BLACK:
            return CDEF_CROSS_BLACK
        elif mode == self.CROSS_WHITE:
            return CDEF_CROSS_WHITE
        elif mode == self.CROSS_RED:
            return CDEF_CROSS_COLPAT2_B
        elif mode == self.CROSS_YELLOW:
            return CDEF_CROSS_COLPAT3_A
        elif mode == self.CROSS_BLUE:
            return CDEF_CROSS_COLPAT3_B
        elif mode == self.LIGHT_GRAY:
            return CDEF_LIGHT_GRAY
        elif mode == self.DARK_GRAY:
            return CDEF_DARK_GRAY
        elif mode == self.UI_ACCENT:
            return CDEF_UI_ACCENT
        elif mode == self.UI_ACCENT2:
            return CDEF_UI_ACCENT2


    @classmethod
    def get_color(self, mode, is_enhanced=True):
        if mode == self.PLAIN:
            return
        elif mode == self.CROSS_BLACK:
            return CDEF_CROSS_BLACK
        elif mode == self.CROSS_WHITE:
            return CDEF_CROSS_WHITE
        elif mode == self.CROSS_COLPAT1:
            if is_enhanced:
                return CDEF_CROSS_COLPAT1_ENHANCED
            else:
                return CDEF_CROSS_COLPAT1_DELAYED
        elif mode == self.CROSS_COLPAT2:
            if is_enhanced:
                return CDEF_CROSS_COLPAT1_DELAYED
            else:
                return CDEF_CROSS_COLPAT1_ENHANCED
        elif mode == self.LIGHT_GRAY:
            return CDEF_LIGHT_GRAY
        elif mode == self.DARK_GRAY:
            return CDEF_DARK_GRAY
        elif mode == self.UI_ACCENT:
            return CDEF_UI_ACCENT
        elif mode == self.UI_ACCENT2:
            return CDEF_UI_ACCENT2
        elif mode == self.CROSS_COLPAT3:
            if is_enhanced:
                return CDEF_CROSS_COLPAT3_B
            else:
                return CDEF_CROSS_COLPAT3_A
        elif mode == self.CROSS_COLPAT4:
            if is_enhanced:
                return CDEF_CROSS_COLPAT3_A
            else:
                return CDEF_CROSS_COLPAT3_B
        elif mode == self.CROSS_COLPAT5:
            if is_enhanced:
                return CDEF_CROSS_COLPAT2_B
            else:
                return CDEF_CROSS_COLPAT2_A
        elif mode == self.CROSS_COLPAT6:
            if is_enhanced:
                return CDEF_CROSS_COLPAT2_A
            else:
                return CDEF_CROSS_COLPAT2_B
    # from https://yeun.github.io/open-color/ingredients.html#yellow



class UIColor():
    PLAIN = 0
    BLACK = 1
    WHITE = 2
    LIGHT_GRAY = 5
    DARK_GRAY = 6
    UI_ACCENT = 7
    UI_ACCENT2 = 8
    ref_ui_color = RestUIColorMode()

    @classmethod
    def get_color(self, n):
        if self.PLAIN > n or self.UI_ACCENT2 < n:
            raise IndexError
        return self.ref_ui_color.get_color(n)

class KyoujiUI:
    def __init__(self,img_paths):
        self.ui = None
        self.imgs = []
        for pth in img_paths:
            self.imgs.append(pygame.image.load(pth))

    def set_ui(self, ui):
        self.ui = ui

    def slide_length(self):
        return len(self.imgs)

    def Show(self, slide_no):
        if slide_no >= self.slide_length():
            return
        img = self.imgs[slide_no]
        dw, dh = pygame.display.get_surface().get_size()
        iw,ih = img.get_size()
        ul_x = dw//2-iw//2
        ul_y = dh//2-ih//2
        self.ui.screen.blit(img, (ul_x, ul_y))
        pygame.display.flip()

class RestUI:
    def __init__(self):
        self.ui = None
        self.click_text_show = False

    def set_ui(self, ui):
        self.ui = ui

    def ApplyView(self, mode):
        self.ui.screen.fill((127, 127, 127))
        if mode == RestUIColorMode.PLAIN:
            return
        # Draw the click prompt or fixation cross
        if mode == RestUIColorMode.CROSS_BLACK:
            w,h= pygame.display.get_surface().get_size()
            tb_struct={"center_x": w//2,
                         "center_y": h//2,
                         "size": 72,
                         "text": i18n.t("ui_click_prompt"),
                         "fg": RestUIColorMode.get_color2(mode),
                         "bg": (127, 127, 127)}
            tb = component_label(self.ui,self.ui.screen, tb_struct)
            tb.render()
        else:
            color = RestUIColorMode.get_color2(mode)
            crossmark_longside_length = 150
            crossmark_shortside_length = 10
            rect1 = pygame.rect.Rect((self.ui.screen.get_width() // 2 - crossmark_longside_length // 2,
                                      self.ui.screen.get_height() // 2 - crossmark_shortside_length // 2),
                                     (crossmark_longside_length, crossmark_shortside_length))
            self.ui.screen.fill(color, rect1)
            rect2 = pygame.rect.Rect((self.ui.screen.get_width() // 2 - crossmark_shortside_length // 2,
                                      self.ui.screen.get_height() // 2 - crossmark_longside_length // 2),
                                     (crossmark_shortside_length, crossmark_longside_length))
            self.ui.screen.fill(color, rect2)
        pygame.display.flip()


# Slider UI
class SliderUI:
    def __init__(self):
        self.ui = None
        # NOTE: this class assumes one slider per screen.
        self.slider = None
        self.slider_value = 0.0
        self.update_texts = None
        self.surface_draw = pygame.Surface((960, 960))
        self.buttons = []

    def set_ui(self, ui):
        self.ui = ui

    def awake_control(self, struct_set):
        self.slider = component_slider(self.ui, self.surface_draw, struct_set["x"], struct_set["y"],
                                       struct_set["width"],
                                       struct_set["height"])
        btn_data = {"center_x": 800, "center_y": 780, "width": 160, "height": 60, "text": i18n.t("ui_next")}
        self.buttons.append(component_button(self.ui, self.surface_draw, btn_data))

    def awake_view(self, text_labels, text_updatevalue=None):
        self.ui.screen.fill((127, 127, 127))
        self.surface_draw.fill(UIColor.get_color(UIColor.WHITE))
        # Render the static text labels here.
        for d in text_labels:
            tbox = component_label(self.ui, self.surface_draw, d)
            tbox.render()
        # Draw the slider last.
        self.update_texts = text_updatevalue
        self.slider.draw()
        for b in self.buttons:
            b.draw()
        self.ui.screen.blit(self.slider.surface, FULLSCREEN_MARGIN)
        pygame.display.flip()

    def update_text(self, *args):
        if self.update_texts == None or args == None:
            return
        if len(self.update_texts) != len(args):
            return
        for index, d in enumerate(self.update_texts):
            tbox = component_label(self.ui, self.surface_draw, d)
            tbox.update_text(args[index])
            tbox.render()
        # Draw the slider last.
        self.slider.draw()
        self.ui.screen.blit(self.slider.surface, FULLSCREEN_MARGIN)
        pygame.display.flip()

    def get_slider_val(self):
        return self.slider_value

    def update(self, *args):
        # Control
        self.update_text(*args)
        # View
        self.slider_value = self.slider.update()
        for b in self.buttons:
                b.update()

    def on_exit(self):
        return self.slider_value


# Horizontal-bar slider drawable component
class component_slider:
    def __init__(self, ui, surface, x=480 - 50, y=480 - 25, width=100, height=50):
        # Internal property: how far the slider has been moved (0..1).
        self.pointer_position = 0.5  # ratio (0..1)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.ui = ui
        self.surface = surface
        self.is_grabbing = False
        self.padding = 20  # padding for the click hit-test region

    def draw(self):
        # Must be redrawn every time the slider moves.
        # TODO: draw tick marks.
        # Prepare the drawing field.
        # (messy)
        padding = 20
        field = pygame.Rect(self.x - padding, self.y, self.width + padding * 2, self.height)
        self.surface.fill(UIColor.get_color(UIColor.WHITE), field)
        bar_horz_height = 8
        bar_horz = pygame.Rect(self.x, self.y + (self.height - bar_horz_height) // 2, self.width,
                               bar_horz_height)  # 8px-tall slider bar (slidable region)
        pygame.draw.rect(self.surface, UIColor.get_color(UIColor.DARK_GRAY), bar_horz, 0, border_radius=4)
        pointer_x = round(self.x + self.width * self.pointer_position)
        bar_horz_after = pygame.Rect(pointer_x, self.y + (self.height - bar_horz_height) // 2,
                                     self.width - round(self.width * (self.pointer_position)),
                                     bar_horz_height)  # 8px-tall slider bar (slidable region)
        pygame.draw.rect(self.surface, UIColor.get_color(UIColor.LIGHT_GRAY), bar_horz_after, 0, border_radius=4)
        pygame.draw.circle(self.surface, UIColor.get_color(UIColor.LIGHT_GRAY),
                           (pointer_x, self.y + (self.height) // 2),
                           16)
        pygame.draw.circle(self.surface, UIColor.get_color(UIColor.WHITE), (pointer_x, self.y + (self.height) // 2),
                           14)

    def update(self):
        pos = pygame.mouse.get_pos()
        pos = (pos[0] - FULLSCREEN_MARGIN[0], pos[1] - FULLSCREEN_MARGIN[1])
        if self.is_grabbing == True:
            if pygame.mouse.get_pressed()[0] == False:
                self.is_grabbing = False
            else:
                self.pointer_position = self.get_pointer_position(pos[0])

        if pygame.mouse.get_pressed()[0] == True:
            if pos[0] > self.x - self.padding and pos[0] < self.x + self.width + self.padding and \
                    pos[1] > self.y - self.padding and pos[1] < self.y + self.height + self.padding:
                if self.is_grabbing == False:
                    if self.is_cursor_on_slidercontrol(pos):
                        self.is_grabbing = True
                    else:
                        self.pointer_position = self.get_pointer_position(pos[0])
                        self.is_grabbing = True
        if self.pointer_position > 1.0:
            self.pointer_position = 1.0
        if self.pointer_position < 0.0:
            self.pointer_position = 0.0
        self.draw()
        return self.pointer_position

    def get_pointer_position(self, x):
        return (x - self.x) / self.width

    def is_cursor_on_slidercontrol(self, pos):
        cx = round(self.x + self.width * self.pointer_position)
        cy = self.y + (self.height) // 2
        x, y = pos
        radius = 16 + 4  # slightly enlarge the hit-test radius
        return (cx - x) ** 2 + (cy - y) ** 2 < radius ** 2  #


class component_button:
    BTN_STATES = {"PUSHED_DOWN": 2,
                      "STANDBY": 0,
                      "HOVERED": 1,
                      "DISABLED": 3,
                  "PUSHED_UP":4}
    def __init__(self, ui: PUI, surface, struct):
        """
        {   "center_x": 480,
            "center_y": 360,
            "size": 48,
            "text": "(0-20s)"
        }
        """
        self.ui = ui
        self.surface = surface
        self.txt = struct["text"]
        self.width = int(struct["width"])
        self.height = int(struct["height"])
        self.cx = int(struct["center_x"])
        self.cy = int(struct["center_y"])
        self.x = self.cx - self.width // 2  # left
        self.y = self.cy - self.height // 2  # top
        self.status = 0
    def draw(self):
        # Must be redrawn every time the slider moves.
        # TODO: draw tick marks.
        # Prepare the drawing field.
        # (messy)
        padding = 20
        l = (self.cx - self.width // 2)
        t = (self.cy - self.height // 2)
        rct = (l, t, self.width, self.height)
        fg_color = None
        bg_color = None
        bdr_radius = 15

        if self.status == self.BTN_STATES["PUSHED_DOWN"]:
            # pushed down
            pygame.draw.rect(self.surface, UIColor.get_color(UIColor.UI_ACCENT2), rct, border_radius=bdr_radius)
            fg_color = UIColor.get_color(UIColor.WHITE)
            bg_color = UIColor.get_color(UIColor.UI_ACCENT2)
        elif self.status ==self.BTN_STATES["STANDBY"]:
            # Default
            pygame.draw.rect(self.surface, UIColor.get_color(UIColor.WHITE), rct, border_radius=bdr_radius)
            pygame.draw.rect(self.surface, UIColor.get_color(UIColor.UI_ACCENT), rct, width=3, border_radius=bdr_radius)
            fg_color = UIColor.get_color(UIColor.UI_ACCENT)
            bg_color = UIColor.get_color(UIColor.WHITE)
        elif self.status == self.BTN_STATES["HOVERED"]:
            # mouse over
            pygame.draw.rect(self.surface, UIColor.get_color(UIColor.UI_ACCENT), rct, border_radius=bdr_radius)
            fg_color = UIColor.get_color(UIColor.WHITE)
            bg_color = UIColor.get_color(UIColor.UI_ACCENT)
        elif self.status == self.BTN_STATES["DISABLED"]:
            # prohibited
            pygame.draw.rect(self.surface, UIColor.get_color(UIColor.DARK_GRAY), rct, border_radius=bdr_radius)

        btn_label_text = {"center_x": self.cx,
                          "center_y": self.cy,
                          "size": 24,
                          "text": self.txt,
                          "fg": fg_color,
                          "bg": bg_color}

        tbox = component_label(self.ui, self.surface, btn_label_text)
        tbox.render()

    def update(self):
        pos = pygame.mouse.get_pos()
        pos = (pos[0] - FULLSCREEN_MARGIN[0], pos[1] - FULLSCREEN_MARGIN[1])
        in_region = pos[0] > self.x and pos[0] < self.x + self.width and pos[1] > self.y and pos[
            1] < self.y + self.height
        if self.status == 2 and pygame.mouse.get_pressed()[0] == False:
            # ibento sousin
            _tmp_event = pygame.event.Event(UIBTN_CLICKED_EVENT)
            pygame.event.post(_tmp_event)
            print("event posted {0}".format(_tmp_event))
        if in_region and self.status != self.BTN_STATES["DISABLED"]:
            if pygame.mouse.get_pressed()[0] == True:
                self.status = self.BTN_STATES["PUSHED_DOWN"]
            else:
                self.status = self.BTN_STATES["HOVERED"]
        else:
            self.status = 0
        self.draw()


class component_label:
    def __init__(self, ui: PUI, surface, struct):
        """
        {   "center_x": 480,
            "center_y": 360,
            "size": 48,
            "text": "(0-20s)"}
        :param ui:
        :param struct:
        """
        self.ui = ui
        self.surface = surface
        if "fg" in struct:
            if "bg" in struct:
                self.tb = TextBox(self.ui, self.surface, struct["text"], struct["center_x"], struct["center_y"],
                                  struct["size"], struct["fg"], struct["bg"])
            else:
                self.tb = TextBox(self.ui, self.surface, struct["text"], struct["center_x"], struct["center_y"],
                                  struct["size"], struct["fg"])
        else:
            self.tb = TextBox(self.ui, self.surface, struct["text"], struct["center_x"], struct["center_y"],
                              struct["size"])

    def update_text(self, ctext):
        self.tb.string = ctext

    def render(self):
        self.tb.render(1)  # 1: center


class TracerUI:
    colorPalette = UIColor()  # treat as const

    class struct_delay:
        def __init__(self, x=-1, y=-1, is_paint_allowed=False):
            self.x = x,
            self.y = y
            self.is_paint_allowed = is_paint_allowed

        def __getitem__(self, key):
            if key == 0:
                return self.x
            elif key == 1:
                return self.y
            elif key == 2:
                return self.is_paint_allowed
            else:
                raise IndexError

    def __init__(self):
        self.ui = None
        self.paint_canvas = pygame.Surface((960, 960), pygame.SRCALPHA, 32)
        self.brush_size = 0  # filled in later
        self.trajectory_x = None
        self.trajectory_y = None
        self.config = None
        self.is_enhanced = False
        self.is_diminished = False
        self.is_delayed = False
        self.is_observe = False
        self.delay_q = deque(self.struct_delay(-1.0, -1.0, False) for i in range(_exp.delay_frames))
        # append() adds at the tail,
        # popleft() takes from the head
        self.__internal_trajectory = collections.deque([], 10)

    def set_config(self, _cfg):
        # _cfg accepts the legacy plumbing argument; the body actually uses
        # the module-level `config`. Using `config` as the parameter name would
        self.config = _cfg
        self.brush_size = int(app_config.task.brush_size)

    def set_ui(self, ui):
        self.ui = ui

    def awake(self, isObserve=False):
        self.is_observe = isObserve
        if self.ui is None:
            raise AttributeError
        self.ui.screen.fill((127, 127, 127))
        bg_board = pygame.Surface((960, 960))
        bg_board.fill(self.colorPalette.get_color(self.colorPalette.WHITE))
        self.ui.screen.blit(bg_board, FULLSCREEN_MARGIN)
        if self.is_observe == True:
            circle_color = RestUIColorMode.get_color(RestUIColorMode.LIGHT_GRAY)
        else:
            circle_color = RestUIColorMode.get_color(RestUIColorMode.CROSS_BLACK)
        pygame.draw.circle(self.paint_canvas, circle_color, (255 + _exp.margin, 255 + _exp.margin), _exp.circle_radius)
        pygame.draw.circle(self.paint_canvas, RestUIColorMode.get_color(RestUIColorMode.CROSS_WHITE),
                           (255 + _exp.margin, 255 + _exp.margin), _exp.circle_radius - _exp.circle_width)
        self.ui.screen.blit(self.paint_canvas, FULLSCREEN_MARGIN)

    def  switch_mode(self, s):
        if s == "delay":
            self.is_delayed = True
            self.is_enhanced = False
            self.is_observe = False
            self.is_diminished = False
        elif s == "enhanced":
            self.is_delayed = False
            self.is_enhanced = True
            self.is_observe = False
            self.is_diminished = False
        elif s == "observe":
            self.is_observe = True
            self.is_delayed = False
            self.is_enhanced = False
            self.is_diminished = False
        elif s == "diminished":
            self.is_delayed = False
            self.is_enhanced = False
            self.is_observe = False
            self.is_diminished = True

    def traj_clear(self):
        self.__internal_trajectory.clear()

    def update(self, is_paint_allowed, position,observe_enhanced=False,observe_delayed=False):
        if self.is_delayed:
            struct = self.delay_q.popleft()
            raw_x, raw_y, _is_paint_allowed = struct
            _tx, _ty = position
            self.delay_q.append((_tx, _ty, is_paint_allowed))
            if _is_paint_allowed == False:
                return -1, -1
        else:
            if is_paint_allowed == False:
                return -1, -1
            raw_x, raw_y = position
        x, y = corrector.Corrector.get_correct((raw_x - _exp.margin, raw_y - _exp.margin))
        ang = corrector.Corrector.get_angle((x, y))
        ang = corrector.Corrector.norm_angle2(ang)
        dist = corrector.Corrector.get_distance((raw_x - _exp.margin, raw_y - _exp.margin), (x, y))
        x += _exp.margin  # placeholder code
        y += _exp.margin  # placeholder code
        if self.is_delayed or (observe_delayed and not _exp.aug_observer_data_option_01):
            x, y = corrector.Corrector.get_dw_point((raw_x, raw_y), (x, y),
                                                    corrector.Corrector.correction_factor_adversarial)
        elif self.is_enhanced or observe_enhanced:
            x, y = corrector.Corrector.get_dw_point((raw_x, raw_y), (x, y),
                                                    corrector.Corrector.correction_factor_enhanced)
        elif self.is_observe or (observe_delayed and _exp.aug_observer_data_option_01):
            x, y = corrector.Corrector.get_dw_point((raw_x, raw_y), (x, y), 0)
        # Front
        self.__internal_trajectory.append([x, y])
        while len(self.__internal_trajectory) < 10:
            self.__internal_trajectory.append([x, y])

        interp = interp1d(list(range(10)), self.__internal_trajectory, kind='cubic', axis=0)
        pygame.draw.circle(self.paint_canvas, (232, 65, 24), (x, y), self.brush_size)
        int_n = 20
        for i in range(int_n):
            pygame.draw.circle(self.paint_canvas, (232, 65, 24), interp(i / float(int_n) + 8.0), self.brush_size)
        self.ui.screen.blit(self.paint_canvas, FULLSCREEN_MARGIN)
        return x, y

    def refresh(self):
        # ----
        # Display
        return
        self.ui.screen.fill(self.colorPalette.get_color(self.colorPalette.WHITE))
        self.paint_canvas.fill(self.colorPalette.get_color(self.colorPalette.WHITE))
        if self.is_observe == True:
            circle_color = RestUIColorMode.get_color(RestUIColorMode.LIGHT_GRAY)
        else:
            circle_color = RestUIColorMode.get_color(RestUIColorMode.CROSS_BLACK)
        pygame.draw.circle(self.paint_canvas, circle_color, (255 + _exp.margin, 255 + _exp.margin), _exp.circle_radius)
        pygame.draw.circle(self.paint_canvas, RestUIColorMode.get_color(RestUIColorMode.CROSS_WHITE),
                           (255 + _exp.margin, 255 + _exp.margin), _exp.circle_radius - _exp.circle_width)
        self.ui.screen.blit(self.paint_canvas, FULLSCREEN_MARGIN)
        self.delay_q.clear()
        for i in range(_exp.delay_frames):
            self.delay_q.append((-1, -1, False))
        self.traj_clear()
