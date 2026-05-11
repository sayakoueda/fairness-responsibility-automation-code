import argparse

import pygame
import pygame as pg
from pygame.locals import *

import app_config
import experiment_data
import pygame_constants
import scene
import ui
from pygame_constants import *


class Main:
    def __init__(self):
        # app_config has already loaded config.yaml at import time, so
        # app_config.system / .display / ... can be accessed directly.
        self.__framerate = int(app_config.system.fps)
        pg.init()
        pg.font.init()
        if DEBUG_MODE == True:
            self.screen = pg.display.set_mode((1280, 1000))
        else:
            self.screen = pg.display.set_mode((0, 0), flags=pygame.FULLSCREEN)
        # Recenter the drawing area against the actual display resolution.
        # Updates FULLSCREEN_MARGIN in place; consumers in scene.py / ui.py
        # see the new values via the shared list reference. CSV output is
        # unaffected (see pygame_constants.init_screen_layout docstring).
        pygame_constants.init_screen_layout(
            self.screen.get_size(),
            app_config.experiment.window_size,
        )
        self.clock = pg.time.Clock()
        _font = app_config.display.font
        self.__jfont = pg.font.SysFont(_font, 36)
        self.font = {sz: pygame.font.SysFont(_font, sz)
                     for sz in (72, 48, 36, 32, 24, 18)}
        self.__ui = ui.PUI(self.__jfont, self.font, self.screen)
        self.__exitFlag = False
        self.experiment_data = experiment_data.OData()
        self.timeline = None

    def launch(self, id, cd, ptn):
        print(id, cd, ptn, type(id), type(cd), type(ptn))
        self.experiment_data.set_initial_data(id, cd, ptn)
        self.timeline = scene.Timeline(self.__ui)
        self.timeline.load_timeline(self.experiment_data)
        self.timeline.cursor().on_start(pg.time.get_ticks())
        self._MainLoop()

    def gen_event_watch(self, event):
        if event.type == QUIT:
            self.__exitFlag = True

    def _MainLoop(self):
        events = []
        while not self.__exitFlag:
            events.clear()
            for event in pg.event.get():
                if event.type == QUIT or event.type == QUIT_EVENT:
                    self.__exitFlag = True
                    continue
                if event.type == NEXT_SCENE_EVENT:
                    self.scenes.Next()
                    continue
                events.append(event)  # Forward unhandled events to update().
            rs = self.timeline.update(events, pg.time)
            if rs == scene.SceneStatus.SUCCESS:
                srs = self.timeline.next_scene()
                if srs == scene.SceneStatus.ENDED:
                    self.__exitFlag = True
                else:
                    self.timeline.cursor().on_start(pg.time.get_ticks())
            pg.display.update()
            self.clock.tick_busy_loop(self.__framerate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Drawing-task behavioral experiment, ver.' + str(VERSION))
    parser.add_argument("--id", help="Participant id (digits only)", type=int, default=10001)
    parser.add_argument("--condition", help="Experimental condition: solo / social",
                        choices=["solo", "social"], default="solo")
    parser.add_argument("--pattern", help="Task pattern A/B/C/D", choices=["A", "B", "C", "D", "a", "b", "c", "d"])
    args = parser.parse_args()
    if args.condition == "solo":
        cd = experiment_data.Condition.SOLO
        if args.pattern == "a" and args.pattern == "A":
            ptn = experiment_data.TaskPattern.PATTERN_A
        elif args.pattern == "b" and args.pattern == "B":
            ptn = experiment_data.TaskPattern.PATTERN_B
        else:
            raise ValueError
    else:
        cd = experiment_data.Condition.SOCIAL
        if args.pattern == "c" and args.pattern == "C":
            ptn = experiment_data.TaskPattern.PATTERN_C
        elif args.pattern == "d" and args.pattern == "D":
            ptn = experiment_data.TaskPattern.PATTERN_D
        else:
            raise ValueError
    main = Main()
    main.launch(args.id, cd, ptn)
    pg.quit()
