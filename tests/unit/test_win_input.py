import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Win32 input helpers")

from rei.capabilities.builtin import _win_input as win  # noqa: E402


def _units(events: list[win.INPUT]) -> list[tuple[int, int, int]]:
    return [(e.u.ki.wVk, e.u.ki.wScan, e.u.ki.dwFlags) for e in events]


def test_unicode_text_becomes_scan_code_key_pairs() -> None:
    events = _units(win.build_inputs("hé"))
    assert events == [
        (0, ord("h"), win.KEYEVENTF_UNICODE), (0, ord("h"), win.KEYEVENTF_UNICODE | win.KEYEVENTF_KEYUP),
        (0, ord("é"), win.KEYEVENTF_UNICODE), (0, ord("é"), win.KEYEVENTF_UNICODE | win.KEYEVENTF_KEYUP),
    ]


def test_newline_is_enter_and_emoji_uses_surrogates() -> None:
    events = _units(win.build_inputs("a\n😀"))
    assert events[2] == (win.VK_RETURN, 0, 0)
    assert events[3] == (win.VK_RETURN, 0, win.KEYEVENTF_KEYUP)
    assert len(events) == 2 + 2 + 4           # emoji = two UTF-16 units, down+up each


def test_recent_launch_expires() -> None:
    win.note_launch(1234)
    assert win.recent_launch_pid() == 1234
    assert win.recent_launch_pid(max_age_s=-1) is None


def test_target_window_never_returns_rei_itself() -> None:
    import os
    hwnd = win.target_window()
    if hwnd is not None:
        assert win._pid_of(hwnd) != os.getpid()
