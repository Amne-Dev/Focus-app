# main.py
import subprocess
import os
from settings import Settings
from ui import launch_main_gui

if __name__ == "__main__":
    cfg = Settings.load()
    from system_utils import ensure_admin
    ensure_admin()
    launch_main_gui(cfg)


