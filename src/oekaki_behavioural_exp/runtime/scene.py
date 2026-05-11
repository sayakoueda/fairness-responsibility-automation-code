import os
from collections import deque

import pygame
import pygame as pg

import app_config
import corrector
import i18n
import experiment_data
import rmse
import ui
from experiment_data import *

# Short alias to keep references to app_config.experiment concise.
_exp = app_config.experiment


class SceneStatus(enum.Enum):
    CONTINUE = 0
    SUCCESS = 1
    ENDED = 2
    FAILED = -1
    FATAL = -10000


class Timeline:
    def __init__(self, ui):
        self.tl = list()
        self.tl.append(DummyScene())
        self._index = 0
        self.ui = ui
        self.config = None

    def update(self, _events, time):
        res = self.cursor().update(_events, time)
        if res == SceneStatus.SUCCESS:
            self.cursor().on_exit()
            return res
        elif res == SceneStatus.CONTINUE:
            return res

    def cursor(self):
        return self.tl[self._index]

    def set_config(self, _cfg):
        # Legacy plumbing. The body uses the module-level `config`;
        # the parameter is renamed to `_cfg` so it does not shadow the
        # imported module.
        self.config = _cfg

    def define_taskpattern_ab(self, expdata: OData):
        # === PATTERN A/B (solo)
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.DARK_GRAY)
        s.ui = self.ui
        self.tl.append(s)
        # --- rest 10s
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
        s.ui = self.ui
        self.tl.append(s)
        for index, trial in enumerate(expdata.response["other_or_self"]):  # iterate once per trial


            # --- trace ?s
            # TODO - [x] dispatch on avatar pattern here
            if expdata.response["o_or_e_or_d"][index] == "e":
                # --- rest 2s
                c = ui.RestUIColorMode.CROSS_WHITE
                s = SceneRest(SceneChangeCondition.TIME, c)
                s.change_duration(_exp.before_task_time)
                s.ui = self.ui
                self.tl.append(s)

                s = SceneTrace(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.ENHANCED
                s.exp_data = expdata
                rec_no = -1
            elif expdata.response["o_or_e_or_d"][index] == "d":
                s = SceneTrace(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.DELAYED
                s.exp_data = expdata
                rec_no = -1
            else:
                s = SceneObserve(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.RECORDED
                s.exp_data = expdata
                rec_no = int(expdata.response["o_or_e_or_d"][index]) - 1
                record_path = experiment_data.get_record_data_path(rec_no)
                s.load_records(record_path)

            s.change_duration(expdata.response["durations"][index])
            s.ui = self.ui
            self.tl.append(s)

            avatar = s.avatar

            # --- enquete 1
            s = SceneSliderSoloTimeEvaluation(SceneChangeCondition.LEFT_CLICK)
            s.ui = self.ui
            s.avatar = avatar
            s.trial_no = index
            s.exp_data = expdata
            self.tl.append(s)

            # --- enquete 2
            s = SceneSliderSoloSelfEvaluation(SceneChangeCondition.LEFT_CLICK)
            s.ui = self.ui
            s.avatar = avatar
            s.trial_no = index
            s.exp_data = expdata
            self.tl.append(s)

            # --- Save Response Data
            s = SaveResponse()
            s.change_duration(0)
            s.exp_data = expdata
            self.tl.append(s)

            # --- rest 10s
            s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
            s.ui = self.ui
            self.tl.append(s)

    def define_taskpattern_solo(self, expdata: OData):
        # === PATTERN A/B (solo)
        p = expdata.pattern
        s = SceneKyouji(SceneChangeCondition.LEFT_CLICK, app_config.task.kyouji_imgpaths)
        s.slide_no = 0 if p == expdata.pattern.PATTERN_A else 1
        s.ui = self.ui
        self.tl.append(s)
        # --- rest click
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
        s.ui = self.ui
        self.tl.append(s)
        for index, trial in enumerate(expdata.response["other_or_self"]):  # iterate once per trial
            # --- rest 2s
            # Pick the color for the rest screen
            _avt = expdata.response["other_or_self"][index]
            if p == expdata.pattern.PATTERN_A:
                if _avt == "self":
                    c=ui.RestUIColorMode.CROSS_RED
                elif _avt=="other":
                    c = ui.RestUIColorMode.CROSS_WHITE
                else:
                    raise ValueError
            elif p == expdata.pattern.PATTERN_B:
                if _avt == "self":
                    c = ui.RestUIColorMode.CROSS_WHITE
                elif _avt == "other":
                    c = ui.RestUIColorMode.CROSS_RED
                else:
                    raise ValueError
            s = SceneRest(SceneChangeCondition.TIME, c)
            s.change_duration(_exp.before_task_time)
            s.ui = self.ui
            self.tl.append(s)

            # --- trace ?s
            e_d_o = expdata.response["o_or_e_or_d"][index]
            # Dispatch on avatar pattern
            if expdata.response["other_or_self"][index] == "self":
                if expdata.response["o_or_e_or_d"][index] == "e":
                    s = SceneTrace(SceneChangeCondition.TIME, self.config)
                    s.avatar = experiment_data.AvatarPattern.ENHANCED
                    s.exp_data = expdata
                    rec_no = -1
                elif expdata.response["o_or_e_or_d"][index] == "d":
                    s = SceneTrace(SceneChangeCondition.TIME, self.config)
                    s.avatar = experiment_data.AvatarPattern.DELAYED
                    s.exp_data = expdata
                    rec_no = -1
            elif expdata.response["other_or_self"][index] == "other":
                # For other-observation we load the pre-corrected variant
                # of the recorded data (E -> *_enhanced.csv, D -> *_delayed.csv)
                # so playback never re-applies the corrector at runtime.
                s = SceneObserve(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.RECORDED
                s.exp_data = expdata
                rec_no = int(expdata.response["data_id"][index]) - 1
                record_path = experiment_data.get_record_data_path(rec_no, mode=e_d_o)
                s.load_records(record_path)
            else:
                raise ValueError

            s.change_duration(expdata.response["durations"][index])
            s.ui = self.ui
            self.tl.append(s)

            avatar = s.avatar

            # --- enquete 1
            s = SceneSliderSoloTimeEvaluation(SceneChangeCondition.LEFT_CLICK)
            s.ui = self.ui
            s.avatar = avatar
            s.trial_no = index
            s.exp_data = expdata
            self.tl.append(s)

            # --- enquete 2
            s = SceneSliderSoloSelfEvaluation(SceneChangeCondition.LEFT_CLICK)
            s.ui = self.ui
            s.avatar = avatar
            s.trial_no = index
            s.exp_data = expdata
            self.tl.append(s)

            # --- enquete 3 // add Oct 10
            s = SceneSliderSoloResponsibilityEvaluation(SceneChangeCondition.LEFT_CLICK)
            s.ui = self.ui
            s.avatar = avatar
            s.trial_no = index
            s.exp_data = expdata
            self.tl.append(s)

            # --- Save Response Data
            s = SaveResponse()
            s.change_duration(0)
            s.exp_data = expdata
            self.tl.append(s)

            # --- rest 10s
            s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
            s.ui = self.ui
            self.tl.append(s)
    def define_taskpattern_social(self, expdata: OData):
        # === PATTERN C/D (social)
        p = expdata.pattern
        s = SceneKyouji(SceneChangeCondition.LEFT_CLICK, app_config.task.kyouji_imgpaths)
        s.slide_no = 2 if p == expdata.pattern.PATTERN_C else 3
        s.ui = self.ui
        self.tl.append(s)

        # --- rest 10s
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
        s.ui = self.ui
        self.tl.append(s)

        for index, trial in enumerate(expdata.response["other_or_self"]):  # iterate once per trial
            # Pick the color for the rest screen
            _sub = expdata.response["other_or_self"][index]
            if _sub == "self":
                _avt = expdata.response["o_or_e_or_d"][index]
            elif _sub == "other":
                if index >= len(expdata.response["o_or_e_or_d"]):
                    raise ValueError
                _avt = expdata.response["o_or_e_or_d"][index+1]
            else:
                raise ValueError
            if p == TaskPattern.PATTERN_C:
                if _avt == "e":
                    color_mode = ui.RestUIColorMode.CROSS_YELLOW
                elif _avt == "d":
                    color_mode = ui.RestUIColorMode.CROSS_BLUE
            elif  p == TaskPattern.PATTERN_D:
                if _avt == "e":
                    color_mode = ui.RestUIColorMode.CROSS_BLUE
                elif _avt == "d":
                    color_mode = ui.RestUIColorMode.CROSS_YELLOW

            s = SceneRest(SceneChangeCondition.TIME, color_mode)
            s.change_duration(_exp.before_task_time)
            s.ui = self.ui
            self.tl.append(s)
            # 2022-08-03: had an issue where the other's data id
            # was a numeric value, breaking the schema.
            # --> resolved by adjusting the config file format.

            # # --- rest 2s
            # # this would re-fetch the number every iteration; needs lookahead!!

            # --- trace ?s
            # TODO - [x] dispatch on avatar pattern here
            #_sub
            e_d_o = expdata.response["o_or_e_or_d"][index]
            if _sub == "self":
                if e_d_o == "e":
                    s = SceneTrace(SceneChangeCondition.TIME, self.config)
                    s.avatar = experiment_data.AvatarPattern.ENHANCED
                    s.exp_data = expdata
                    rec_no = -1
                    s.change_duration(expdata.response["durations"][index])
                    s.ui = self.ui
                    self.tl.append(s)
                    self.define_after_dep_e_d(expdata, s.avatar, index)
                elif e_d_o == "d":
                    s = SceneTrace(SceneChangeCondition.TIME, self.config)
                    s.avatar = experiment_data.AvatarPattern.DELAYED
                    s.exp_data = expdata
                    rec_no = -1
                    s.change_duration(expdata.response["durations"][index])
                    s.ui = self.ui
                    self.tl.append(s)
                    self.define_after_dep_e_d(expdata, s.avatar, index)
                else:
                    pass
            elif _sub == "other":
                s = SceneObserve(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.RECORDED
                s.exp_data = expdata
                rec_no = int(expdata.response["data_id"][index]) - 1
                record_path = experiment_data.get_record_data_path(rec_no, mode=e_d_o)
                s.load_records(record_path)
                s.change_duration(expdata.response["durations"][index])
                s.ui = self.ui
                self.tl.append(s)
                # --- rest 1s
                s = SceneRest(SceneChangeCondition.TIME, color_mode)
                _duration = 1 #second
                s.change_duration(_duration)
                s.ui = self.ui
                self.tl.append(s)



            # --- trace ?s
    def define_taskpattern_cd(self, expdata: OData):
        # === PATTERN C/D (social)
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.DARK_GRAY)
        s.ui = self.ui
        self.tl.append(s)
        # --- rest 10s
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
        s.ui = self.ui
        self.tl.append(s)
        for index, trial in enumerate(expdata.response["other_or_self"]):  # iterate once per trial
            e_d_o = expdata.response["o_or_e_or_d"][index]
            if e_d_o.isdecimal():
                edo_rest_color_mode = expdata.response["o_or_e_or_d"][index + 1]
            else:
                edo_rest_color_mode = e_d_o
            # --- rest 2s

            s = SceneRest(SceneChangeCondition.TIME,
                          ui.RestUIColorMode.get_palette(expdata.pattern, edo_rest_color_mode))
            # this would re-fetch the number every iteration; needs lookahead!!
            s.change_duration(_exp.before_task_time)
            s.ui = self.ui
            self.tl.append(s)

            # --- trace ?s
            # TODO - [x] dispatch on avatar pattern here
            if e_d_o == "e":
                s = SceneTrace(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.ENHANCED
                s.exp_data = expdata
                rec_no = -1
                s.change_duration(expdata.response["durations"][index])
                s.ui = self.ui
                self.tl.append(s)
                self.define_after_dep_e_d(expdata, s.avatar, index)
            elif e_d_o == "d":
                s = SceneTrace(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.DELAYED
                s.exp_data = expdata
                rec_no = -1
                s.change_duration(expdata.response["durations"][index])
                s.ui = self.ui
                self.tl.append(s)
                self.define_after_dep_e_d(expdata, s.avatar, index)
            else:
                s = SceneObserve(SceneChangeCondition.TIME, self.config)
                s.avatar = experiment_data.AvatarPattern.RECORDED
                s.exp_data = expdata
                rec_no = int(expdata.response["o_or_e_or_d"][index]) - 1
                record_path = experiment_data.get_record_data_path(rec_no)
                s.load_records(record_path)
                s.change_duration(expdata.response["durations"][index])
                s.ui = self.ui
                self.tl.append(s)
                # --- rest 2s
                s = SceneRest(SceneChangeCondition.TIME,
                              ui.RestUIColorMode.get_palette(expdata.pattern, edo_rest_color_mode))
                s.change_duration(_exp.before_task_time)
                s.ui = self.ui
                self.tl.append(s)

    def define_after_dep_e_d(self, expdata, avatar, index):
        # --- enquete 1
        s = SceneSliderDependentTimeEvaluation(SceneChangeCondition.LEFT_CLICK)
        s.ui = self.ui
        s.avatar = avatar
        s.trial_no = index
        s.exp_data = expdata
        self.tl.append(s)

        # --- enquete 2
        s = SceneSliderDependentSelfEvaluation(SceneChangeCondition.LEFT_CLICK)
        s.ui = self.ui
        s.avatar = avatar
        s.trial_no = index
        s.exp_data = expdata
        self.tl.append(s)

        # --- enquete 3
        s = SceneSliderDependentResponsibilityEvaluation(SceneChangeCondition.LEFT_CLICK)
        s.ui = self.ui
        s.avatar = avatar
        s.trial_no = index
        s.exp_data = expdata
        self.tl.append(s)

        # --- Save Response Data
        s = SaveResponse()
        s.change_duration(0)
        s.exp_data = expdata
        self.tl.append(s)

        # --- rest click
        s = SceneRest(SceneChangeCondition.LEFT_CLICK, ui.RestUIColorMode.CROSS_BLACK)
        s.ui = self.ui
        self.tl.append(s)

    def load_timeline(self, expdata: OData):
        cond = expdata.condition
        if cond == Condition.SOLO:
            self.define_taskpattern_solo(expdata)
        elif cond == Condition.SOCIAL:
            self.define_taskpattern_social(expdata)
        pattern = expdata.pattern
        self.itr_index()
        # on_start needs to be supplied by the caller.
        return SceneStatus.SUCCESS

    def itr_index(self, plus=1):
        self._index += plus
        print(self._index)

    def next_scene(self):
        try:
            self.itr_index()
            if self._index >= len(self.tl):
                raise IndexError
        except:
            return SceneStatus.ENDED
        else:
            return SceneStatus.SUCCESS


class Scene:
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        self.scene_change_condition = _scene_change_condition
        self.time = 5000  # ms
        self.scene_start_time = 0  # elapsed since on_start

    def change_duration(self, sec):
        self.time = sec * 1000

    def on_start(self, tick):
        self.scene_start_time = tick

    def on_exit(self):
        pass
    # Scene transition condition is managed by the main loop.


class DummyScene(Scene):
    def __init__(self):
        super().__init__(SceneChangeCondition.DUMMY)

    def update(self, dummy_tick=0, dummy_2=0, dummy_3=0):
        return SceneStatus.SUCCESS


class SaveResponse(Scene):
    def __init__(self):
        super().__init__(SceneChangeCondition.TIME)
        self.exp_data: experiment_data.OData = None

    def update(self, dummy_tick=None, dummy_event=None, dummy_3=0):
        if self.exp_data == None:
            raise ValueError
        fdir = "Records/" + str(self.exp_data.patient_id) + "/"
        os.makedirs(fdir, exist_ok=True)
        self.exp_data.export_csv(fdir + self.exp_data.gen_filename(True))
        print("Save: Success")
        return SceneStatus.SUCCESS


# Build SceneKyouji

class SceneKyouji(Scene, ui.KyoujiUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition,img_paths):
        Scene.__init__(self, _scene_change_condition)
        ui.KyoujiUI.__init__(self,img_paths)
        self.slide_no = 0
        self.slide_max= len(self.imgs)

    def on_start(self, tick):
        Scene.on_start(self, tick)
        self.Show(self.slide_no)

    def update(self, events,dummy):
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for event in events:
                # Mouse-pointer movement handler
                # 1 - left click
                # 2 - middle click
                # 3 - right click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        return SceneStatus.SUCCESS

            return SceneStatus.CONTINUE
        return SceneStatus.CONTINUE

class SceneRest(Scene, ui.RestUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition,colormode=ui.RestUIColorMode.CROSS_WHITE):
        Scene.__init__(self, _scene_change_condition)
        ui.RestUI.__init__(self)
        self.colormode = colormode

    def on_start(self, tick):
        Scene.on_start(self, tick)
        self.ApplyView(self.colormode)

    def update(self, events, timer):
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for event in events:
                # Mouse-pointer movement handler
                # 1 - left click
                # 2 - middle click
                # 3 - right click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        return SceneStatus.SUCCESS
            return SceneStatus.CONTINUE
        tick = timer.get_ticks()
        if tick >= self.scene_start_time + self.time:
            if self.scene_change_condition == SceneChangeCondition.TIME:
                return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


class SceneTrace(Scene, ui.TracerUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition, _config):
        Scene.__init__(self, _scene_change_condition)
        ui.TracerUI.__init__(self)
        self.set_config(_config)
        self.paint_state = 0
        self.prev_frame_pos = (0.0, 0.0)
        self.prev_raw_frame_pos: tuple[float, float] | None = None
        # TODO: figure out what to do here
        self.avatar = None
        self.delay_q2 = deque()
        # append() adds at the tail,
        # popleft() takes from the head
        # taskdata
        self.exp_data = None  # placeholder
        self.traj = Trajectory()
    def on_start(self, tick):
        Scene.on_start(self, tick)
        ui.TracerUI.awake(self)
        if self.avatar == AvatarPattern.DELAYED:
            ui.TracerUI.switch_mode(self, "delay")
        elif self.avatar == AvatarPattern.RECORDED:
            ui.TracerUI.switch_mode(self, "observe")
        else:
            ui.TracerUI.switch_mode(self, "enhanced")
        self.delay_q2.clear()
        for i in range(_exp.delay_frames):
            self.delay_q2.append(False)
        if pg.mouse.get_pressed()[0]:
            self.paint_state = 1

    def update(self, events, timer):
        tick = timer.get_ticks()
        x, y = 0, 0
        isRecordedFlg = False
        for event in events:
            # Mouse-pointer movement handler
            # 1 - left click
            # 2 - middle click
            # 3 - right click
            # 4 - scroll up
            # 5 - scroll down
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    ui.TracerUI.update(self, False, (-1, -1))
                    self.paint_state = 1
            if event.type == pygame.MOUSEBUTTONUP:
                print(event.button, type(event.button))
                if event.button == 1:
                    self.paint_state = 0
                    ui.TracerUI.update(self, False, (-1, -1))
                    ui.TracerUI.traj_clear(self)

            if self.paint_state > 0 and event.type == pygame.MOUSEMOTION:
                # Refresh the view
                (raw_x, raw_y) = event.pos
                (raw_x, raw_y) = (raw_x - FULLSCREEN_MARGIN[0], raw_y - FULLSCREEN_MARGIN[1])
                x, y = ui.TracerUI.update(self, True, (raw_x, raw_y))
                # Check whether the start point was crossed
                old_judge = self.delay_q2.popleft()
                self.delay_q2.append(
                    corrector.Corrector.check_point_on_start_point("Circle", (raw_x - _exp.margin, raw_y - _exp.margin),
                                                                   self.brush_size,
                                                                   pg.time.get_ticks()))
                _rx, _ry = raw_x - _exp.margin, raw_y - _exp.margin
                if old_judge:
                    self.traj.add_trial(x - _exp.margin, y - _exp.margin, self.paint_state,
                                        raw_x=_rx, raw_y=_ry)
                    isRecordedFlg = True
                    self.traj.sync_set()
                    ui.TracerUI.refresh(self)
                else:
                    self.traj.add_trial(x - _exp.margin, y - _exp.margin, self.paint_state,
                                        raw_x=_rx, raw_y=_ry)
                    isRecordedFlg = True
                self.prev_frame_pos = x - _exp.margin, y - _exp.margin
                self.prev_raw_frame_pos = (_rx, _ry)
        if isRecordedFlg == False:
            if self.paint_state > 0:
                _prev_rx, _prev_ry = self.prev_raw_frame_pos if self.prev_raw_frame_pos else (None, None)
                self.traj.add_trial(self.prev_frame_pos[0], self.prev_frame_pos[1], self.paint_state,
                                    raw_x=_prev_rx, raw_y=_prev_ry)
            else:
                self.traj.add_trial(x - _exp.margin, y - _exp.margin, self.paint_state)

        if tick >= self.scene_start_time + self.time:
            if self.scene_change_condition == SceneChangeCondition.TIME:
                self.traj.sync_set()
                # End-of-trial handling
                if RECORD_OTHERSELF_MODE:
                    with open(experiment_data.get_record_data_path(get_rec_os_num()), 'w', newline="") as fp:
                        self.traj.create_csv(fp)
                    inc_rec_os_num()
                else:
                    fdir = "Records/" + str(self.exp_data.patient_id) + "/"
                    os.makedirs(fdir, exist_ok=True)
                    _t_filename = self.exp_data.gen_filename(False)
                    print("CSVFILENAME: ", fdir + _t_filename)
                    # Pull this trial's e/d type (Config CSV `data` column) so we
                    # know whether to fill delayed_x/y or enhanced_x/y in the output.
                    _modes = self.exp_data.response.get("o_or_e_or_d") or []
                    _idx = max(0, self.exp_data.current_lines)
                    _trial_mode = _modes[_idx] if _idx < len(_modes) else None
                    with open(fdir + _t_filename, 'w', newline="") as fp:
                        self.traj.create_csv(fp, mode=_trial_mode)
                    # Also drop a sibling *_rmse.csv computed in-process,
                    # mirroring the bundled web tool (scripts/csv_processor_cp).
                    _rmse_filename = _t_filename[:-4] + "_rmse.csv"
                    with open(fdir + _rmse_filename, 'w', newline="") as fp:
                        rmse.write_rmse_csv_from_trajectory(fp, self.traj)
                return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


# --------

class SceneObserve(Scene, ui.TracerUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition, _config):
        Scene.__init__(self, _scene_change_condition)
        ui.TracerUI.__init__(self)
        self.set_config(_config)
        self.traj = Trajectory()
        self.frame_count = 0
        self.trial_count = 0

    def load_records(self, path):
        self.traj.load_csv(path)

    def on_start(self, tick):
        Scene.on_start(self, tick)
        ui.TracerUI.awake(self, True)  # 2nd argument is for make circle color gray.

    def update(self, events, timer):
        tick = timer.get_ticks()
        x, y, mouse_state, isEndOfTrial, isEndOfTrials = self.traj.get_pos(self.trial_count, self.frame_count)
        if mouse_state > 0:
            # Recorded data is already pre-corrected on disk; render as-is.
            ui.TracerUI.update(self, True, (x + _exp.margin, y + _exp.margin))
        else:
            ui.TracerUI.update(self, False, (-1, -1))
        self.frame_count += 1
        if isEndOfTrial:
            self.trial_count += 1
            self.frame_count = 0
            if isEndOfTrials:
                self.trial_count = 0
                ui.TracerUI.refresh(self)
                return SceneStatus.SUCCESS

        if tick >= self.scene_start_time + self.time:
            if self.scene_change_condition == SceneChangeCondition.TIME:
                self.trial_count = 0
                ui.TracerUI.refresh(self)
                return SceneStatus.SUCCESS
        # Mouse-pointer movement handler
        # 1 - left click
        # 2 - middle click
        # 3 - right click
        # 4 - scroll up
        # 5 - scroll down
        return SceneStatus.CONTINUE


# --------
class SceneSliderSoloTimeEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

        # self.

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_time")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": i18n.t("scene_q_time_range")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "  　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        t: str = i18n.t("format_seconds").format(int(ui.SliderUI.get_slider_val(self) * 20))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.TIME
                                               , ui.SliderUI.get_slider_val(self) * 20)
                    return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


class SceneSliderSoloSelfEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_skill")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": i18n.t("scene_q_skill_range")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "  　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        tick = timer.get_ticks()
        t: str = i18n.t("format_points").format(int(ui.SliderUI.get_slider_val(self) * 100))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.SELF
                                               , ui.SliderUI.get_slider_val(self) * 100)
                    return SceneStatus.SUCCESS

        return SceneStatus.CONTINUE

# SceneSliderSoloResponsibilityEvaluation
# Oct 10 added
class SceneSliderSoloResponsibilityEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_responsibility_solo")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": "(0～100％)"},
                       {"center_x": 280,
                        "center_y": 480 + 36,
                        "size": 24,
                        "text": i18n.t("scene_responsibility_low")},
                       {"center_x": 680,
                        "center_y": 480 + 36,
                        "size": 24,
                        "text": i18n.t("scene_responsibility_high")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "    　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        tick = timer.get_ticks()
        t: str = "{:>3d}％".format(int(ui.SliderUI.get_slider_val(self) * 100))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.RESPONSIBILITY
                                               , ui.SliderUI.get_slider_val(self) * 100)
                    return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE



# -------------------------------------------------

class SceneSliderDependentTimeEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_time")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": i18n.t("scene_q_time_range")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "    　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        tick = timer.get_ticks()
        t: str = i18n.t("format_seconds").format(int(ui.SliderUI.get_slider_val(self) * 20))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.TIME
                                               , ui.SliderUI.get_slider_val(self) * 20)
                    return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


class SceneSliderDependentSelfEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text":  i18n.t("scene_q_skill")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": i18n.t("scene_q_skill_range")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "    　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        tick = timer.get_ticks()
        t: str = i18n.t("format_points").format(int(ui.SliderUI.get_slider_val(self) * 100))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.SELF
                                               , ui.SliderUI.get_slider_val(self) * 100)
                    return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


# -------------------------------------------------

class SceneSliderDependentResponsibilityEvaluation(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)
        self.exp_data: OData = None

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_responsibility_social")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": "(0～100％)"},
                       {"center_x": 280,
                        "center_y": 480 + 36,
                        "size": 24,
                        "text": i18n.t("scene_responsibility_low")},
                       {"center_x": 680,
                        "center_y": 480 + 36,
                        "size": 24,
                        "text": i18n.t("scene_responsibility_high")}
                       ]
        upd_txts = [
            {"center_x": 480,
             "center_y": 440,
             "size": 36,
             "text": "    　",
             "fg": ui.UIColor.get_color(ui.UIColor.UI_ACCENT)}
        ]
        self.awake_view(text_labels, upd_txts)

    def update(self, events, timer):
        tick = timer.get_ticks()
        t: str = "{:>3d}％".format(int(ui.SliderUI.get_slider_val(self) * 100))
        ui.SliderUI.update(self, t)
        if self.scene_change_condition == SceneChangeCondition.LEFT_CLICK:
            for e in events:
                if e.type == UIBTN_CLICKED_EVENT:
                    # Save handling
                    self.exp_data.add_response(EnquetePattern.RESPONSIBILITY
                                               , ui.SliderUI.get_slider_val(self) * 100)
                    return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE


# -------------------------------------------------


class TestSceneSlider(Scene, ui.SliderUI):
    def __init__(self, _scene_change_condition: SceneChangeCondition):
        Scene.__init__(self, _scene_change_condition)
        ui.SliderUI.__init__(self)

    def on_start(self, tick):
        Scene.on_start(self, tick)
        # , y=, width=, height=
        self.awake_control({"x": 480 - 200,
                            "y": 480 - 25,
                            "width": 400,
                            "height": 50})
        text_labels = [{"center_x": 480,
                        "center_y": 240,
                        "size": 48,
                        "text": i18n.t("scene_q_time")},
                       {"center_x": 480,
                        "center_y": 360,
                        "size": 36,
                        "text": i18n.t("scene_q_time_range")}
                       ]
        self.awake_view(text_labels)

    def update(self, events, timer):
        tick = timer.get_ticks()
        ui.SliderUI.update(self)
        if tick >= self.scene_start_time + self.time:
            if self.scene_change_condition == SceneChangeCondition.TIME:
                return SceneStatus.SUCCESS
        return SceneStatus.CONTINUE
