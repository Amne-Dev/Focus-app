import ctypes, sys
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import asyncio

def ensure_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            params = ' '.join(f'"{arg}"' for arg in sys.argv)
            ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
            sys.exit()
    except Exception:
        pass

def get_system_volume():
    try:
        dev = AudioUtilities.GetSpeakers().Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(dev, POINTER(IAudioEndpointVolume))
        return vol.GetMasterVolumeLevelScalar()
    except:
        return 0.0

try:
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaMgr
    WINRT = True
except ImportError:
    WINRT = False

async def _fetch_media():
    mgr = await MediaMgr.request_async()
    sess = mgr.get_current_session()
    if sess:
        props = await sess.try_get_media_properties_async()
        return f"{props.artist or ''} – {props.title or ''}".strip(' – ')
    return ''

def get_current_media():
    if not WINRT: return ''
    try: return asyncio.run(_fetch_media())
    except: return ''

def send_media_command(cmd: str):
    VK = {'playpause':0xB3,'next':0xB0,'prev':0xB1}.get(cmd)
    if VK:
        ctypes.windll.user32.keybd_event(VK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK, 0, 2, 0)