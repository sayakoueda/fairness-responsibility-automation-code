import math

import app_config

# Short aliases to keep references in this file concise.
_exp = app_config.experiment
_cor = app_config.corrector


class Corrector:
    threshold = _cor.threshold  # must be squared

    correction_factor_enhanced = _cor.correction_factor_enhanced
    correction_factor_adversarial = _cor.correction_factor_adversarial

    @staticmethod
    def get_correct(cursor: (int, int)):
        cp = Corrector.get_nearest_point_on_circle(cursor)
        return cp

    @staticmethod
    def get_nearest_point_on_triangle(cursor: (int, int)):
        ls = []
        # 1st line
        a = -290.988000
        b = -168.000000
        c = 93057.768000
        ls.append(Corrector.get_nearest_point_on_line(cursor, a, b, c))
        # 2nd line
        a = 0.000000
        b = -336.000000
        c = 134901.648000
        ls.append(Corrector.get_nearest_point_on_line(cursor, a, b, c))
        # 3rd line
        a = 290.988000
        b = -168.000000
        c = -55928.088000
        ls.append(Corrector.get_nearest_point_on_line(cursor, a, b, c))
        return min(ls)

    @staticmethod
    def get_angle(cursor: (int, int)):
        center_pos = (_exp.field_size // 2, _exp.field_size // 2)
        rd = math.atan2(cursor[1] - center_pos[1], cursor[0] - center_pos[0])
        return rd

    @staticmethod
    def norm_angle(rd):
        # -pi<=x<=pi --> 0<=x<2pi
        dg = (math.degrees(rd) + 360) % 360.0
        return math.radians(dg)

    @staticmethod
    def norm_angle2(rd):
        # -pi<=x<=pi --> 0<=x<2pi
        dg = (math.degrees(rd) + 360) % 360.0
        return dg

    @staticmethod
    def get_nearest_point_on_circle(cursor: (int, int)):
        center_pos = (_exp.field_size // 2, _exp.field_size // 2)
        rd = Corrector.get_angle(cursor)
        correct_pos = (
            center_pos[0] + _exp.circle_radius * math.cos(rd),
            center_pos[1] + _exp.circle_radius * math.sin(rd),
        )
        return correct_pos

    @staticmethod
    def get_distance(cur, ans):
        center_pos = (_exp.field_size // 2, _exp.field_size // 2)
        cur_distance = math.dist(cur, center_pos)
        ans_distance = math.dist(ans, center_pos)
        return (cur_distance - ans_distance) / _exp.circle_radius

    @staticmethod
    def get_nearest_point_on_line(p, a, b, c):
        t = (a ** 2 + b ** 2)
        t1 = b * p[0] - a * p[1]
        d2 = (a * p[0] + b * p[1] + c) ** 2 / t
        return d2, ((b * t1 - a * c) / t, (-a * t1 - b * c) / t)

    @staticmethod
    def get_dw_point(raw, correct, ratio):
        diff = correct[0] - raw[0], correct[1] - raw[1]
        if ratio == 0:
            return raw[0], raw[1]
        if abs(max(*diff)) > _exp.circle_threshold + 20:
            return raw[0], raw[1]
        elif abs(max(*diff)) > _exp.circle_threshold:
            diff_diff = abs(max(*diff)) - _exp.circle_threshold
            return raw[0] + (ratio * (diff_diff / 20.0) * diff[0]), raw[1] + (ratio * (diff_diff / 20.0) * diff[1])
        else:
            return raw[0] + ratio * diff[0], raw[1] + ratio * diff[1]

    prev_clock = 0

    @classmethod
    def on_exit_check_point_on_start_point(cls, clock):
        cls.prev_clock = clock
        return

    @classmethod
    def check_point_on_start_point(cls, type_name, cursor, brush_size, clock):
        if type_name == "Circle":
            ul = (math.degrees(Corrector.get_angle((cursor[0] - brush_size, cursor[1] - brush_size))))
            lr = (math.degrees(Corrector.get_angle((cursor[0] + brush_size, cursor[1] + brush_size))))
            if ul * lr < 0:
                return False
            if ul < 90.0 < lr or lr < 90 < ul:
                if (clock - cls.prev_clock) < 200:
                    return False
                Corrector.on_exit_check_point_on_start_point(clock)
                return True
            else:
                return False
        else:
            raise ValueError("unimplemented name")
