import customtkinter as ctk
from focus_session import FocusSession
from PIL import Image
import os

def launch_main_gui(cfg):
    ctk.set_appearance_mode('Dark'); ctk.set_default_color_theme('blue')
    app = ctk.CTk(); app.title('Focus Timer'); app.geometry('400x520'); app.resizable(False,False)

    icon_path = os.path.join('assets', 'FocusLogo.ico')
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)

    ctk.CTkLabel(app, text='Enter minutes:', font=(cfg.font,18)).pack(pady=(30,5))
    entry = ctk.CTkEntry(app, placeholder_text=str(cfg.session_minutes), font=(cfg.font,18), width=200)
    entry.pack(pady=(0,10)); entry.insert(0, str(cfg.session_minutes))

    frame = ctk.CTkFrame(app, fg_color='transparent'); frame.pack(pady=20)
    for v in (25,30,60): ctk.CTkButton(frame, text=f'{v} min', width=80,
        command=lambda m=v: entry.delete(0,'end') or entry.insert(0,str(m)) ).pack(side='left',padx=10)

    pomodoro_toggle = ctk.CTkCheckBox(app, text='Enable Pomodoro Mode', variable=ctk.IntVar(value=int(cfg.pomodoro_mode)), font=(cfg.font, 14))
    pomodoro_toggle.pack(pady=(10,0))

    def open_settings():
        win = ctk.CTkToplevel(app); win.title('Settings'); win.geometry('300x300')
        win.iconbitmap('assets/FocusLogo.ico')
        win.attributes('-topmost', True)
        win.focus_force()
        win.grab_set()

        def toggle(option):
            setattr(cfg, option, not getattr(cfg, option))
            cfg.save()

        ctk.CTkLabel(win, text='Shortcut (comma-separated):', font=(cfg.font, 12)).pack()
        shortcut_entry = ctk.CTkEntry(win, width=200)
        shortcut_entry.insert(0, ','.join(cfg.unlock_combo))
        shortcut_entry.pack(pady=5)

        ctk.CTkButton(win, text='Set Shortcut', command=lambda: setattr(cfg, 'unlock_combo', [s.strip() for s in shortcut_entry.get().split(',')]) or cfg.save()).pack()

        ctk.CTkCheckBox(win, text='Show Volume Bar', variable=ctk.IntVar(value=cfg.show_volume_bar), command=lambda: toggle('show_volume_bar')).pack(pady=10)
        ctk.CTkCheckBox(win, text='Media Controls', variable=ctk.IntVar(value=cfg.media_controls), command=lambda: toggle('media_controls')).pack(pady=10)

        font_entry = ctk.CTkEntry(win, placeholder_text='Font', width=150)
        font_entry.insert(0, cfg.font); font_entry.pack(pady=10)
        ctk.CTkButton(win, text='Set Font', command=lambda: setattr(cfg, 'font', font_entry.get()) or cfg.save()).pack()

    err = ctk.CTkLabel(app, text='', text_color='red', font=(cfg.font,14)); err.pack()

    ctk.CTkButton(app, text='⚙', command=open_settings, font=(cfg.font, 14), width=30, height=30, fg_color='transparent').place(relx=0.97, rely=0.03, anchor='ne')

    def start():
        try:
            m=int(entry.get());
            if m<=0: raise ValueError
            cfg.session_minutes=m
            cfg.pomodoro_mode = bool(pomodoro_toggle.get())
            cfg.save()
            app.destroy();
            FocusSession(cfg, lambda: launch_main_gui(cfg)).start()
        except:
            err.configure(text='Please enter a valid number > 0')

    ctk.CTkButton(app, text='Start Timer', command=start, font=(cfg.font,18)).pack(pady=20)
    app.mainloop()