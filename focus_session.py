import time, threading
import pyautogui, keyboard, pygetwindow as gw
from system_utils import get_system_volume, get_current_media, send_media_command
from tkinter import Tk, Label, Canvas, Button, Toplevel
from PIL import ImageTk, Image
import os

# Helper to minimize all other windows (except current one)
def prepare_focus_environment():
    current = gw.getActiveWindow()
    for w in gw.getAllWindows():
        try:
            if w != current and w.visible:
                w.minimize()
        except:
            pass

class FocusSession:
    def __init__(self, cfg, restore_callback, mode='focus'):
        self.cfg = cfg
        self.restore = restore_callback
        duration = cfg.session_minutes
        self.session_minutes = duration
        self.end_time = time.time() + duration * 60
        self._running = False

    def start(self):
        prepare_focus_environment()
        self._running = True
        self._launch_fullscreen()

    def _launch_fullscreen(self):
        self.win = Tk()
        self.win.iconbitmap(default=os.path.join('assets', 'FocusLogo.ico'))
        self.win.attributes('-fullscreen', True)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.config(bg='black', cursor='none')

        self.lbl_title = Label(self.win, text='Focus Mode', font=(self.cfg.font, 40), fg='gray', bg='black')
        self.lbl_title.pack(pady=(40,0))

        self.lbl_timer = Label(self.win, font=(self.cfg.font,80,'bold'), fg='white', bg='black')
        self.lbl_timer.pack(expand=True)
        self.lbl_media = Label(self.win, font=(self.cfg.font,30), fg='white', bg='black')
        self.lbl_media.pack(side='bottom', pady=40)

        if self.cfg.show_volume_bar:
            self._init_volume_bar()
        if self.cfg.media_controls:
            self._init_media_controls()

        self._setup_input_hooks()
        self._mouse_thread = threading.Thread(target=self._mouse_tracker, daemon=True)
        self._mouse_thread.start()

        self._schedule_volume_update()
        self._update_ui()
        self.win.mainloop()

    def _init_volume_bar(self):
        self.canvas = Canvas(self.win, width=60, height=10, bg='black', highlightthickness=0)
        self.canvas.place(relx=0.99, rely=0.99, anchor='se')

    def _draw_volume(self):
        if not getattr(self, 'win', None) or not self.win.winfo_exists():
            return
        vol = get_system_volume()
        self.canvas.delete('all')
        self.canvas.create_oval(0,0,60,10, fill='#333333', width=0)
        self.canvas.create_rectangle(2,2,int(58*vol),8,fill='white',width=0)

    def _schedule_volume_update(self):
        if not self._running or not self.win.winfo_exists():
            return
        if self.cfg.show_volume_bar:
            self._draw_volume()
        self.win.after(200, self._schedule_volume_update)

    def _init_media_controls(self):
        def mkbtn(image_path, cmd):
            icon = Image.open(image_path).resize((24,24))
            img = ImageTk.PhotoImage(icon)
            btn = Button(self.win, image=img, command=lambda: send_media_command(cmd),
                         bg='black', bd=0, highlightthickness=0, activebackground='black')
            btn.image = img
            return btn

        self.prev_btn = mkbtn(os.path.join('assets','prev.png'),'prev')
        self.play_btn = mkbtn(os.path.join('assets','play.png'),'playpause')
        self.next_btn = mkbtn(os.path.join('assets','next.png'),'next')
        self.prev_btn.place(relx=0.01, rely=0.98, anchor='sw')
        self.play_btn.place(relx=0.05, rely=0.98, anchor='sw')
        self.next_btn.place(relx=0.09, rely=0.98, anchor='sw')

    def _setup_input_hooks(self):
        forbidden = {'tab','windows','shift'}
        def on_event(e):
            if e.event_type=='up':
                e.suppress=False
                return
            name = e.name.lower()
            if name=='esc':
                keyboard.unhook_all()
                self._running=False
                if getattr(self,'win',None) and self.win.winfo_exists():
                    self.win.destroy()
                self.restore()
                self._show_shame_popup()
                return
            if name in forbidden:
                e.suppress=True
            else:
                e.suppress=False
        keyboard.hook(on_event, suppress=False)

    def _mouse_tracker(self):
        delay = self.cfg.mouse_hide_delay
        prev = pyautogui.position(); last=time.time()
        while self._running:
            time.sleep(0.1)
            curr = pyautogui.position()
            if getattr(self,'win',None) and self.win.winfo_exists():
                if curr!=prev:
                    last=time.time(); self.win.config(cursor='arrow')
                elif time.time()-last>delay:
                    self.win.config(cursor='none')
            prev=curr

    def _update_ui(self):
        if not self._running:
            return
        rem = int(self.end_time-time.time())
        if rem>=0:
            m,s=divmod(rem,60)
            if self.win.winfo_exists():
                self.lbl_timer.config(text=f"{m:02d}:{s:02d}")
                self.lbl_media.config(text=get_current_media())
                self.win.after(100,self._update_ui)
        else:
            self._running=False
            keyboard.unhook_all()
            if self.win.winfo_exists(): self.win.destroy()
            self.restore()
            self._show_congrats_popup()
