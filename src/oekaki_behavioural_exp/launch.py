import pygame as pg
from pygame_constants import DEBUG_MODE
import experiment
import i18n
import experiment_data
import pygame_textinput
import ui

DIALOG_MARGIN = (480, 60)


def get_enum(txt, index):
    if index == 0:
        return int(txt)
    if index == 1:
        if txt == "solo":
            return experiment_data.Condition.SOLO
        else:
            return experiment_data.Condition.SOCIAL
    elif index == 2:
        if txt == "a" or txt == "A":
            return experiment_data.TaskPattern.PATTERN_A
        elif txt == "b" or txt == "B":
            return experiment_data.TaskPattern.PATTERN_B
        elif txt == "c" or txt == "C":
            return experiment_data.TaskPattern.PATTERN_C
        elif txt == "d" or txt == "D":
            return experiment_data.TaskPattern.PATTERN_D
    elif index == 3:
        if txt == "A" or txt == "a":
            return experiment_data.ColorPattern.PATTERN_P
        elif txt == "B" or txt == "b":
            return experiment_data.ColorPattern.PATTERN_Q
        else:
            return experiment_data.ColorPattern.NONE


def validation(txt, index):
    if index == 0:
        return txt.isdecimal()
    elif index == 1:
        return txt in ["solo", "social"]
    elif index == 2:
        return txt in ["A", "B", "C", "D", "a", "b", "c", "d"]
    elif index == 3:
        return txt == "" or txt in ["A", "B", "a", "b"]


def text_show(screen, txi, txt, pos):
    default_color = (50, 50, 50)
    if len(txt) > 15:
        txts = txt.split('\n')
        i = 0
        for t in txts:
            screen.blit(txi.font_object.render(t, True, (100, 100, 100) if i > 0 else default_color),
                        (pos[0], pos[1] + (txi.font_size + 10) * i))
            i += 1
    else:
        screen.blit(txi.font_object.render(txt, True, default_color), pos)


if __name__ == '__main__':
    _main = experiment.Main()
    # pygame_textinput falls back to the default DejaVu Sans whenever its
    # internal match_font fails. Pre-resolve the actual file path from the
    # comma-separated candidate list in config.yaml so we can hand a real
    # path to TextInput.
    import app_config as _config
    _font_path = _config.resolve_font_path(_config.display.font)
    textinput = pygame_textinput.TextInput(
        font_family=_font_path or 'bizudgothicbizudpgothicboldtruetype',
        text_color=ui.UIColor.get_color(ui.UIColor.UI_ACCENT))
    # DEBUG
    if DEBUG_MODE == True:
        screen = pg.display.set_mode((1920, 1000))
    else:
        screen = pg.display.set_mode((0, 0), flags=pg.FULLSCREEN)
    clock = _main.clock
    prompt = {"message": [i18n.t("launch_id_input"),
                          i18n.t("launch_condition_select"),
                          i18n.t("launch_pattern_select"),
                          i18n.t("launch_color_pattern_select")], "input": []}
    prompt_index = 0
    while True:
        screen.fill(ui.UIColor.get_color(ui.UIColor.WHITE))

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                exit()

        # Feed it with events every frame
        flag = textinput.update(events)
        # Blit its surface onto the screen
        text_show(screen, textinput, prompt["message"][prompt_index], (10 + DIALOG_MARGIN[0], 30 + DIALOG_MARGIN[1]))
        screen.blit(textinput.get_surface(), (10 + DIALOG_MARGIN[0], 130 + DIALOG_MARGIN[1]))
        if flag:
            t = textinput.get_text()
            res = validation(t, prompt_index)
            if prompt_index == 2:
                if prompt["input"][1] == experiment_data.Condition.SOLO:
                    res = res and t in ["A", "B", "a", "b"]
                else:
                    res = res and t in ["C", "D", "c", "d"]

            if res:
                prompt["input"].append(get_enum(t, prompt_index))

                prompt_index += 1
                textinput.clear_text()
                if prompt_index == 2:
                    if get_enum(t, 1) == experiment_data.Condition.SOLO:
                        prompt["message"][2] = i18n.t("launch_pattern_select_solo")
                    else:
                        prompt["message"][2] = i18n.t("launch_pattern_select_social")
                elif prompt_index > 2:
                    break
            else:
                textinput.clear_text()

        pg.display.update()
        clock.tick(30)
    if DEBUG_MODE == True:
        pg.display.set_mode((1920, 1000))
    else:
        pg.display.set_mode((0, 0), flags=pg.FULLSCREEN)
    _main.launch(prompt["input"][0], prompt["input"][1], prompt["input"][2])
    pg.quit()
