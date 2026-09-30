"""Win32 helpers for typing into the *user's* window, not Rei's own.

Typing used to go to whatever had keyboard focus, which is Rei itself right
after the user talks or clicks in it. We instead pick the window the user was
using before Rei (next in z-order), or the app launched earlier in the same
request, bring it to the foreground, and type with SendInput + Unicode.
"""
import ctypes
import os
import time
from ctypes import wintypes
from typing import Any

user32: Any = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None
dwmapi: Any = ctypes.WinDLL("dwmapi") if os.name == "nt" else None
kernel32: Any = None

if user32 is not None:
    # Declare handle types: the ctypes default (C int) truncates 64-bit HWNDs
    HWND = wintypes.HWND
    user32.GetTopWindow.argtypes = [HWND]
    user32.GetTopWindow.restype = HWND
    user32.GetWindow.argtypes = [HWND, wintypes.UINT]
    user32.GetWindow.restype = HWND
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = HWND
    user32.IsWindowVisible.argtypes = [HWND]
    user32.IsIconic.argtypes = [HWND]
    user32.GetWindowLongW.argtypes = [HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.GetWindowTextW.argtypes = [HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.SetForegroundWindow.argtypes = [HWND]
    user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.BringWindowToTop.argtypes = [HWND]
    user32.SetFocus.argtypes = [HWND]
    user32.SetFocus.restype = HWND
    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [HWND]
    user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.SendMessageTimeoutW.argtypes = [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                                           wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
    user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t
    dwmapi.DwmGetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long

GW_HWNDNEXT = 2
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
DWMWA_CLOAKED = 14
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_RETURN = 0x0D
VK_MENU = 0x12

# Set by apps.open so a following type_text in the same request targets that app.
# We remember which windows already existed; the launched app is the first NEW
# window (Store apps such as Win11 Notepad run under a different PID than the
# process we started, so matching PIDs isn't enough).
_last_launch: dict[str, object] = {}


def note_launch(pid: int) -> None:
    _last_launch.clear()
    _last_launch.update(pid=pid, at=time.monotonic(), before=set(_candidate_windows()))


def recent_launch_pid(max_age_s: float = 15.0) -> int | None:
    at = _last_launch.get("at")
    if isinstance(at, float) and time.monotonic() - at <= max_age_s:
        pid = _last_launch.get("pid")
        return pid if isinstance(pid, int) else None
    return None


def _pid_of(hwnd: int) -> int:
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return int(pid.value)


def _title(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def is_candidate(hwnd: int, own_pid: int) -> bool:
    """A normal, visible, top-level app window that isn't Rei."""
    if not hwnd or not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
        return False
    if _pid_of(hwnd) == own_pid:
        return False
    if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
        return False
    if not _title(hwnd):
        return False
    cloaked = wintypes.DWORD()
    status = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    if status == 0 and cloaked.value:
        return False  # hidden UWP / other-desktop windows
    return True


def _candidate_windows() -> list[int]:
    """Candidate app windows, topmost (most recently used) first."""
    own_pid = os.getpid()
    out: list[int] = []
    hwnd = user32.GetTopWindow(None)
    while hwnd:
        if is_candidate(hwnd, own_pid):
            out.append(int(hwnd))
        hwnd = user32.GetWindow(hwnd, GW_HWNDNEXT)
    return out


def target_window(prefer_pid: int | None = None, wait_s: float = 5.0) -> int | None:
    """Window to type into: the app launched just before (first new window,
    waiting up to wait_s for it to appear), else the most recently used
    non-Rei window."""
    before = _last_launch.get("before") if prefer_pid is not None else None
    if isinstance(before, set):
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            windows = _candidate_windows()
            new = [h for h in windows if h not in before or _pid_of(h) == prefer_pid]
            if new:
                return new[0]
            time.sleep(0.1)
    windows = _candidate_windows()
    return windows[0] if windows else None


def focus(hwnd: int) -> bool:
    """Bring hwnd to the foreground without sending any keystrokes.

    Windows only lets the foreground thread change the foreground window, so we
    briefly attach our input queue to it (AttachThreadInput). The common "tap
    ALT" trick is avoided on purpose: ALT opens the target app's menu bar,
    which then swallows the first characters we type.
    """
    if user32.GetForegroundWindow() == hwnd:
        return True
    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    me = kernel32.GetCurrentThreadId()
    attached = bool(fg_thread and fg_thread != me and user32.AttachThreadInput(me, fg_thread, True))
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(me, fg_thread, False)
    for _ in range(40):
        if user32.GetForegroundWindow() == hwnd:
            time.sleep(0.15)  # let the app route keyboard focus to its text box
            return True
        time.sleep(0.05)
    return False


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("_pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


def _key(vk: int = 0, scan: int = 0, flags: int = 0) -> INPUT:
    return INPUT(type=INPUT_KEYBOARD, u=_INPUTUNION(ki=KEYBDINPUT(vk, scan, flags, 0, 0)))


def build_inputs(text: str) -> list[INPUT]:
    """Key events for text: Unicode scan codes (any language, emoji via
    surrogate pairs), newlines as Enter."""
    events: list[INPUT] = []
    for ch in text.replace("\r\n", "\n"):
        if ch == "\n":
            events += [_key(vk=VK_RETURN), _key(vk=VK_RETURN, flags=KEYEVENTF_KEYUP)]
            continue
        encoded = ch.encode("utf-16-le")
        for i in range(0, len(encoded), 2):
            unit = int.from_bytes(encoded[i:i + 2], "little")
            events += [_key(scan=unit, flags=KEYEVENTF_UNICODE),
                       _key(scan=unit, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP)]
    return events


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
VK_CONTROL = 0x11
VK_V = 0x56


def wait_responsive(hwnd: int, timeout_ms: int = 3000) -> bool:
    """Block until the window's UI thread processes messages (i.e. the app has
    finished starting up and won't mangle input)."""
    result = ctypes.c_size_t()
    # WM_NULL with SMTO_ABORTIFHUNG
    ok = user32.SendMessageTimeoutW(hwnd, 0x0000, 0, 0, 0x0002, timeout_ms, ctypes.byref(result))
    return bool(ok)


def _get_clipboard_text() -> str | None:
    if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
        return None
    handle = user32.GetClipboardData(CF_UNICODETEXT)
    if not handle:
        return None
    ptr = kernel32.GlobalLock(handle)
    try:
        return ctypes.wstring_at(ptr) if ptr else None
    finally:
        kernel32.GlobalUnlock(handle)


def _set_clipboard_text(text: str) -> None:
    data = ctypes.create_unicode_buffer(text)
    size = ctypes.sizeof(data)
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    if not handle:
        raise OSError("GlobalAlloc failed")
    ptr = kernel32.GlobalLock(handle)
    ctypes.memmove(ptr, data, size)
    kernel32.GlobalUnlock(handle)
    user32.EmptyClipboard()
    if not user32.SetClipboardData(CF_UNICODETEXT, handle):
        kernel32.GlobalFree(handle)
        raise OSError("SetClipboardData failed")


def _open_clipboard(retries: int = 10) -> bool:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.03)  # another app may hold it briefly
    return False


def paste_text(text: str) -> None:
    """Insert text into the focused app via the clipboard + Ctrl+V.

    The app receives the whole string atomically, so any Unicode arrives intact
    no matter how busy the app is. The user's previous clipboard text is put
    back afterwards.
    """
    if not _open_clipboard():
        raise OSError("clipboard busy")
    try:
        previous = _get_clipboard_text()
        _set_clipboard_text(text.replace("\r\n", "\n").replace("\n", "\r\n"))
    finally:
        user32.CloseClipboard()

    keys = [_key(vk=VK_CONTROL), _key(vk=VK_V), _key(vk=VK_V, flags=KEYEVENTF_KEYUP),
            _key(vk=VK_CONTROL, flags=KEYEVENTF_KEYUP)]
    arr = (INPUT * len(keys))(*keys)
    if user32.SendInput(len(keys), arr, ctypes.sizeof(INPUT)) != len(keys):
        raise OSError(f"SendInput blocked ({ctypes.get_last_error()})")

    # Give the app time to read the clipboard before restoring it
    time.sleep(0.4)
    if previous is not None and _open_clipboard():
        try:
            _set_clipboard_text(previous)
        finally:
            user32.CloseClipboard()


def insert_text(text: str) -> None:
    """Paste when possible; fall back to paced keystrokes."""
    try:
        paste_text(text)
    except OSError:
        send_text(text, delay_s=0.02)


def send_text(text: str, delay_s: float = 0.01) -> None:
    """Send one key (down+up) at a time. Batching many Unicode key events in a
    single SendInput makes some apps (Win11 Notepad) drop and repeat characters;
    ~10ms per key is reliable and still fast (~100 chars/s)."""
    events = build_inputs(text)
    for i in range(0, len(events), 2):
        pair = events[i:i + 2]
        arr = (INPUT * len(pair))(*pair)
        sent = user32.SendInput(len(pair), arr, ctypes.sizeof(INPUT))
        if sent != len(pair):
            raise OSError(f"SendInput blocked ({ctypes.get_last_error()})")
        time.sleep(delay_s)
