import json
import os

DEFAULTS = {
    'unlock_combo': ['ctrl', 'o', 'p'],
    'pomodoro_mode': False,
    'session_minutes': 25,
    'break_minutes': 5,
    'show_volume_bar': True,
    'media_controls': True,
    'mouse_hide_delay': 2.0,
    'font': 'Poppins'
}

class Settings:
    FILE = os.path.join(os.path.expanduser('~'), '.focus_timer_cfg.json')

    def __init__(self, **kwargs):
        for k,v in DEFAULTS.items(): setattr(self, k, kwargs.get(k, v))

    @classmethod
    def load(cls):
        try:
            with open(cls.FILE, 'r') as f: data = json.load(f)
        except FileNotFoundError:
            data = DEFAULTS.copy()
            with open(cls.FILE, 'w') as f: json.dump(data, f, indent=4)
        return cls(**data)

    def save(self):
        data = {k: getattr(self, k) for k in DEFAULTS}
        with open(self.FILE, 'w') as f:
            json.dump(data, f, indent=4)