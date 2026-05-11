"""Application-wide **invariant constants** and pygame custom event types.

Experiment-tunable parameters (``DELAY_FRAMES``, ``CIRCLE_RADIUS``,
``MARGIN`` etc.) are no longer kept here; reference them directly via
``app_config.experiment.*`` / ``app_config.corrector.*``.

What stays in this module is only **constants that must travel with
the code**: pygame event type ids, color definitions, and a few small
helpers.
"""
import pygame

VERSION = "0.9.6"
DEBUG_MODE = False
RECORD_OTHERSELF_MODE = False
RECORD_OTHERSELF_NUM = 0

# --- Colors -------------------------------------------------------------
CDEF_CROSS_BLACK = (16, 16, 16)
CDEF_LIGHT_GRAY = (189, 195, 199)
CDEF_DARK_GRAY = (68, 70, 71)
CDEF_CROSS_WHITE = (236, 240, 241)  # (255, 255, 255)
CDEF_CROSS_COLPAT1_ENHANCED = (250, 240, 0)
CDEF_CROSS_COLPAT1_DELAYED = (0, 6, 255)
CDEF_CROSS_COLPAT2_A = (236, 240, 241)
CDEF_CROSS_COLPAT2_B = (224, 34, 69)
CDEF_CROSS_COLPAT3_A = (232, 225, 67)
CDEF_CROSS_COLPAT3_B = (47, 81, 181)
CDEF_UI_ACCENT = (41, 128, 185)
CDEF_UI_ACCENT2 = (26, 83, 120)

# --- Hardware-side fullscreen offset ------------------------------------
# Top-left position of the (window_size x window_size) drawing area on the
# actual display. Mutable list (not a tuple) so init_screen_layout() can
# update it in place after pygame initializes the display – any module that
# did ``from pygame_constants import *`` keeps a reference to the SAME list
# object and therefore sees the new values transparently.
#
# Default values are sized for a 1920x1080 display with a 960x960 drawing
# area. They are overwritten by init_screen_layout() at startup.
FULLSCREEN_MARGIN = [480, 60]


def init_screen_layout(screen_size, window_size):
    """Recenter ``FULLSCREEN_MARGIN`` based on the real display resolution.

    Parameters
    ----------
    screen_size : tuple[int, int]
        Actual display size in px, e.g. ``screen.get_size()``.
    window_size : int
        Side length of the square drawing area, normally
        ``app_config.experiment.window_size``.

    Notes
    -----
    Trajectory CSV output is unaffected. Coordinates are stored in
    field-local space after two offsets are subtracted –
    ``screen -> window-local`` (this ``FULLSCREEN_MARGIN``) and
    ``window-local -> field-local`` (the experiment-field margin) – so
    moving the drawing area to the center of an arbitrarily-sized display
    only changes where it is *drawn*, not what is *recorded*.
    """
    sw, sh = screen_size
    FULLSCREEN_MARGIN[0] = max(0, (sw - window_size) // 2)
    FULLSCREEN_MARGIN[1] = max(0, (sh - window_size) // 2)


def inc_rec_os_num():
    global RECORD_OTHERSELF_NUM
    RECORD_OTHERSELF_NUM += 1


def get_rec_os_num():
    global RECORD_OTHERSELF_NUM
    return RECORD_OTHERSELF_NUM


# --- pygame custom event ids (allocated once at import time) -----------
NEXT_SCENE_EVENT = pygame.event.custom_type()
QUIT_EVENT = pygame.event.custom_type()
TIMER_FIN_EVENT = pygame.event.custom_type()
UIBTN_CLICKED_EVENT = pygame.event.custom_type()


LEFT_CLICK = 1
RIGHT_CLICK = 3

CONFIG_DIR = "Config/"


class CommonFunction:
    def __init__(self):
        self.time = 0

    def set_time_object(self, pg_time):
        self.time = pg_time

    def set_timer(self, ms, isOnce=True):
        self.time.set_timer(TIMER_FIN_EVENT, ms, isOnce)
