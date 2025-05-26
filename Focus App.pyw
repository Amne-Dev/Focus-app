# A simple focus timer with media info and volume bar
# Requires: pycaw, customtkinter, keyboard, winrt (optional)
# This script is designed to run on Windows and requires admin privileges
# It will relaunch itself with admin rights if not already elevated.
# It also supports a full-screen focus mode with a timer and media info display.
#Feel free to modify and use it as you like!
#Made by AmDev(@Amne-Dev). 


import ctypes
from ctypes import POINTER, cast
import sys
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import keyboard

# === Elevation Check & Relaunch as Admin ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit()



# === Try to import WinRT media-control API ===
WINRT_AVAILABLE = False
try:
    import asyncio
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager
    )
    WINRT_AVAILABLE = True
except ImportError:
    WINRT_AVAILABLE = False

async def _fetch_media_async():
    mgr = await MediaManager.request_async()
    # Use the correct method name:
    sessions = mgr.get_sessions()
    session  = mgr.get_current_session()
    if session:
        props = await session.try_get_media_properties_async()
        artist = props.artist or ""
        title  = props.title  or ""
        return f"{artist} – {title}".strip(" – ")
    return ""

def get_current_media():
    if not WINRT_AVAILABLE:
        return ""
    try:
        return asyncio.run(_fetch_media_async())
    except:
        return ""

def get_system_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        # GetMasterVolumeLevelScalar returns volume as a float between 0.0 and 1.0
        return volume.GetMasterVolumeLevelScalar()
    except:
        return 0

# === Full-screen focus mode ===
def launch_focus_screen(minutes: int):
    focus = tk.Tk()
    focus.attributes('-fullscreen', True)
    focus.configure(bg='black')
    focus.overrideredirect(True)
    focus.config(cursor="none")

    big_font   = ("Poppins", 80, "bold")
    small_font = ("Poppins", 30)

    timer_label = tk.Label(focus, text="", font=big_font, fg="white", bg="black")
    timer_label.pack(expand=True)

    media_label = tk.Label(focus, text="", font=small_font, fg="white", bg="black")
    media_label.pack(side="bottom", pady=40)

    # Volume bar setup
    bar_width = 20
    bar_height = 300
    bar_x = 0.97  # near right edge
    radius = 10

    volume_canvas = tk.Canvas(focus, width=bar_width + 10, height=bar_height, bg="black", highlightthickness=0)
    volume_canvas.place(relx=bar_x, rely=0.5, anchor='e')

    def draw_rounded_rect(x1, y1, x2, y2, r, **kwargs):
        # Draw a rounded rectangle on canvas
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
        ]
        return volume_canvas.create_polygon(points, smooth=True, **kwargs)

    def draw_volume_bar():
        vol = get_system_volume()
        fill_height = int(bar_height * vol)

        volume_canvas.delete("all")

        # Draw gray rounded border as background
        draw_rounded_rect(5, 0, 5 + bar_width, bar_height, radius, fill="#555555", outline="white", width=1)

        # Draw white filled rectangle inside, no rounding needed
        if fill_height > 0:
            y1 = bar_height - fill_height
            volume_canvas.create_rectangle(5, y1, 5 + bar_width, bar_height, fill="white", width=0)

    # Set up key hook: suppress all keys except Ctrl+O+P to exit
    pressed = set()
    def on_event(e):
        name = e.name

        # ---- KEY UP: clear state and return (we don't need to suppress ups) ----
        if e.event_type == 'up':
            if name in ('ctrl', 'ctrl_l', 'ctrl_r'):
                pressed.discard('ctrl')
            elif name in ('o', 'p'):
                pressed.discard(name)
            return  # let key-ups through

        # ---- KEY DOWN: track only ctrl / o / p, block everything else ----
        # Track ctrl
        if name in ('ctrl', 'ctrl_l', 'ctrl_r'):
            pressed.add('ctrl')
        # Track O
        elif name == 'o':
            pressed.add('o')
        # Track P
        elif name == 'p':
            pressed.add('p')
        # Any other key: we just return (it stays suppressed by the hook)
        else:
            return

        # If we now have ctrl+o+p, exit
        if {'ctrl', 'o', 'p'}.issubset(pressed):
            keyboard.unhook_all()
            focus.destroy()

    # Suppress everything by default, let our handler decide which to ignore
    keyboard.hook(on_event, suppress=True)

    end_time = time.time() + minutes * 60

    def update_ui():
        remaining = int(end_time - time.time())
        if remaining >= 0:
            mins, secs = divmod(remaining, 60)
            timer_label.config(text=f"{mins:02d}:{secs:02d}")
            media_label.config(text=get_current_media())
            draw_volume_bar()
            focus.after(50, update_ui)
        else:
            keyboard.unhook_all()
            focus.destroy()

    focus.after(0, update_ui)
    focus.mainloop()
    
# === Launcher GUI ===
def launch_main_gui():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Focus Timer")
    app.geometry("400x360")
    app.resizable(False, False)

    # Timer input
    ctk.CTkLabel(app, text="Enter minutes:", font=("Poppins", 18))\
        .pack(pady=(30,5))
    entry = ctk.CTkEntry(app, placeholder_text="e.g. 25", font=("Poppins", 18), width=200)
    entry.pack(pady=(0,10))

    # Presets (30/60/90)
    frame = ctk.CTkFrame(app, fg_color="transparent")
    frame.pack(pady=(0,20))
    def set_preset(m):
        entry.delete(0, tk.END)
        entry.insert(0, str(m))
    for val in (30,60,90):
        ctk.CTkButton(frame, text=f"{val} min", width=80,
                      command=lambda v=val: set_preset(v))\
            .pack(side="left", padx=10)

    # Error label
    error = ctk.CTkLabel(app, text="", text_color="red", font=("Poppins", 14))
    error.pack()

    # Warn if media-info unavailable
    if not WINRT_AVAILABLE:
        messagebox.showwarning(
            "Media Info Disabled",
            "Local media detection is unavailable on this setup.\n"
            "You`ll still get the timer, but no “Now Playing” text."
        )

    # Start button
    def on_start():
        try:
            m = int(entry.get())
            if m <= 0: raise ValueError
            app.destroy()
            launch_focus_screen(m)
        except:
            error.configure(text="Please enter a valid number > 0")

    ctk.CTkButton(app, text="Start Timer", command=on_start, font=("Poppins", 18))\
        .pack(pady=(0,20))

    app.mainloop()

if __name__ == "__main__":
    launch_main_gui()
