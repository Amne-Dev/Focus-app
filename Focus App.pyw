
import ctypes
import sys

# === Elevation Check ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    params = " ".join([f'\"{arg}\"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import os
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import keyboard

# === Spotify Config ===
SPOTIFY_CLIENT_ID = 'your_client_id'
SPOTIFY_CLIENT_SECRET = 'your_client_secret'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'
sp = None
spotify_user = None

def try_spotify_login():
    global sp, spotify_user, login_in_progress
    try:
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope='user-read-playback-state user-read-currently-playing user-modify-playback-state',
            open_browser=True
        )
        token_info = auth_manager.get_cached_token()
        if not token_info:
            auth_manager.get_access_token(as_dict=False)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        spotify_user = sp.current_user().get("display_name") or sp.current_user().get("id")
    except Exception as e:
        print("Spotify login failed:", e)
    finally:
        login_in_progress = False
def get_current_song():
    if sp:
        try:
            playback = sp.current_playback()
            if playback and playback['is_playing']:
                item = playback['item']
                return f"{item['name']} - {item['artists'][0]['name']}"
        except:
            pass
    return ""

# === Focus screen with suppression ===
def launch_focus_screen(minutes: int):
    focus = tk.Tk()
    focus.attributes('-fullscreen', True)
    focus.configure(bg='black')
    focus.overrideredirect(True)
    # Hide mouse cursor
    focus.config(cursor="none")

    big_font = ("Poppins", 80, "bold")
    small_font = ("Poppins", 30)

    timer_label = tk.Label(focus, text="", font=big_font, fg="white", bg="black")
    timer_label.pack(expand=True)

    song_label = tk.Label(focus, text="", font=small_font, fg="white", bg="black")
    song_label.pack(side="bottom", pady=40)

    # Set up keyboard hook to suppress all keys except Ctrl+O+P
    pressed = set()
    def on_event(e):
        if e.event_type != 'down':
            return
        name = e.name
        # Track pressed keys for unlock
        if name in ('ctrl', 'ctrl_l', 'ctrl_r'):
            pressed.add('ctrl')
        elif name == 'o':
            pressed.add('o')
        elif name == 'p':
            pressed.add('p')
        # Check unlock combo
        if {'ctrl', 'o', 'p'}.issubset(pressed):
            keyboard.unhook_all()
            focus.destroy()
            return
        # Otherwise suppress
        e.suppress = True

    keyboard.hook(on_event)

    def countdown():
        total = minutes * 60
        while total >= 0:
            mins, secs = divmod(total, 60)
            timer_label.config(text=f"{mins:02d}:{secs:02d}")
            song_label.config(text=get_current_song())
            time.sleep(1)
            total -= 1
        keyboard.unhook_all()
        focus.destroy()

    threading.Thread(target=countdown, daemon=True).start()
    focus.mainloop()
# === Tooltip class ===
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow:
            return
        x = self.widget.winfo_pointerx() + 10
        y = self.widget.winfo_pointery() + 10
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.text, bg="#111", fg="white",
                       relief="solid", borderwidth=1, font=("Poppins", 9))
        lbl.pack()
        self.tipwindow = tw

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def logout_user():
    if messagebox.askyesno("Logout", "Log out from Spotify?"):
        try:
            os.remove(".cache")
        except:
            pass
        webbrowser.open("https://accounts.spotify.com/en/logout")
        os.execl(sys.executable, sys.executable, *sys.argv)

# === Main GUI ===
def launch_main_gui():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Focus Timer")
    app.geometry("400x360")
    app.resizable(False, False)

    user_label = ctk.CTkLabel(app, text="", font=("Poppins", 16), cursor="hand2")
    user_label.pack(pady=(20, 5))

    def update_user_label():
        if spotify_user:
            user_label.configure(text=f"Logged in as {spotify_user}")
            ToolTip(user_label, "Log out")
            user_label.bind("<Button-1>", lambda e: logout_user())
        else:
            user_label.configure(text="Log in to Spotify")
            user_label.bind("<Button-1>", lambda e: (try_spotify_login() and app.destroy() or update_user_label()))

    update_user_label()

    entry_label = ctk.CTkLabel(app, text="Enter minutes:", font=("Poppins", 18))
    entry_label.pack(pady=(10, 5))
    entry = ctk.CTkEntry(app, placeholder_text="e.g. 25", font=("Poppins", 18), width=200)
    entry.pack(pady=(0, 10))

    presets_frame = ctk.CTkFrame(app, fg_color="transparent")
    presets_frame.pack(pady=(0, 20))
    def set_preset(m):
        entry.delete(0, tk.END)
        entry.insert(0, str(m))
    for val in (30, 60, 90):
        btn = ctk.CTkButton(presets_frame, text=f"{val} min", width=80, command=lambda v=val: set_preset(v))
        btn.pack(side="left", padx=10)

    error_label = ctk.CTkLabel(app, text="", text_color="red", font=("Poppins", 14))
    error_label.pack()

    def start():
        try:
            m = int(entry.get())
            if m <= 0:
                raise ValueError
            app.destroy()
            launch_focus_screen(m)
        except:
            error_label.configure(text="Please enter a valid number > 0")

    start_button = ctk.CTkButton(app, text="Start Timer", command=start, font=("Poppins", 18))
    start_button.pack(pady=(0, 20))

    app.mainloop()

if __name__ == "__main__":
    launch_main_gui()
