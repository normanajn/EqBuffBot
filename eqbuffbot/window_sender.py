"""Find the EverQuest window and send keystroke sequences to it via pydirectinput."""

from __future__ import annotations

import logging
import queue
import re
import threading
import time

import pyautogui      # used only for the mouse click to focus
import pydirectinput  # scan-code based SendInput — works with DirectInput games

# Remove the built-in per-keystroke pause (default is 0.1s each)
pydirectinput.PAUSE = 0.0
pyautogui.PAUSE = 0.0

logger = logging.getLogger(__name__)

_KEY_INTERVAL = 0.02
5  # seconds to wait between keystrokes
FOCUS_DELAY = 1.0   # seconds to wait after SetForegroundWindow
CLICK_DELAY = 0.25  # seconds to wait after the focus click

# Map {TOKEN} names to pydirectinput key names (same names as pyautogui)
_TOKEN_TO_KEY: dict[str, str] = {
    "ENTER":  "enter", "RETURN": "enter",
    "TAB":    "tab",
    "ESC":    "esc",   "ESCAPE": "esc",
    "SPACE":  "space",
    "BACK":   "backspace",
    "DELETE": "delete", "DEL":   "delete",
    "UP":     "up",    "DOWN":  "down",
    "LEFT":   "left",  "RIGHT": "right",
    "F1":  "f1",  "F2":  "f2",  "F3":  "f3",  "F4":  "f4",
    "F5":  "f5",  "F6":  "f6",  "F7":  "f7",  "F8":  "f8",
    "F9":  "f9",  "F10": "f10", "F11": "f11", "F12": "f12",
}

# Tokeniser: splits "hello {ENTER} world" into ["hello ", "{ENTER}", " world"]
_TOKEN_RE = re.compile(r"(\{[^}]+\})")

# Maps a character to the (pydirectinput key name, needs_shift) needed to produce it.
# Only entries that differ from a plain lowercase press are listed; everything else
# is sent as-is (lowercase letters, digits, already-lowercase symbols).
_CHAR_MAP: dict[str, tuple[str, bool]] = {
    # Uppercase letters
    **{ch: (ch.lower(), True) for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
    # Shifted number-row symbols (US layout)
    "!": ("1", True),  "@": ("2", True),  "#": ("3", True),
    "$": ("4", True),  "%": ("5", True),  "^": ("6", True),
    "&": ("7", True),  "*": ("8", True),  "(": ("9", True),
    ")": ("0", True),
    # Shifted punctuation (US layout)
    "_": ("-",     True),  "+": ("=",         True),
    "{": ("[",     True),  "}": ("]",         True),
    "|": ("\\",    True),  ":": (";",         True),
    '"': ("'",     True),  "<": (",",         True),
    ">": (".",     True),  "?": ("/",         True),
    "~": ("`",     True),
    # Space
    " ": ("space", False),
}


def _type_char(ch: str) -> None:
    """Press a single character using pydirectinput, holding Shift when needed."""
    key, shift = _CHAR_MAP.get(ch, (ch, False))
    if shift:
        pydirectinput.keyDown("shift")
    pydirectinput.press(key)
    if shift:
        pydirectinput.keyUp("shift")
    time.sleep(_KEY_INTERVAL)


def _send_string(text: str) -> None:
    """Send *text* to the foreground window using pydirectinput (scan codes)."""
    for part in _TOKEN_RE.split(text):
        if not part:
            continue
        if part.startswith("{") and part.endswith("}"):
            key_name = part[1:-1].upper()
            key = _TOKEN_TO_KEY.get(key_name)
            if key:
                pydirectinput.press(key)
                time.sleep(_KEY_INTERVAL)
            else:
                logger.warning("Unknown special key: %s", part)
        else:
            for ch in part:
                _type_char(ch)


def _find_and_focus_eq(title_fragment: str) -> bool:
    """Bring the EQ window to the foreground. Returns True on success."""
    try:
        import win32gui
        import win32con

        results: list[int] = []

        def _cb(hwnd: int, _):
            if title_fragment.lower() in win32gui.GetWindowText(hwnd).lower():
                results.append(hwnd)

        win32gui.EnumWindows(_cb, None)
        if not results:
            logger.warning("EQ window not found (title contains '%s').", title_fragment)
            return False

        hwnd = results[0]
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(FOCUS_DELAY)

        # Click the center of the window to ensure input focus
        #left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        #center_x = (left + right) // 2
        #center_y = (top + bottom) // 2
        #pyautogui.click(center_x, center_y)
        #time.sleep(CLICK_DELAY)

        return True
    except Exception as e:
        logger.error("Failed to focus EQ window: %s", e)
        return False


class WindowSender:
    """Consume action lists from *action_queue* and send them to the EQ window."""

    def __init__(self, config, action_queue: "queue.Queue[list]"):
        self._config = config
        self._action_queue = action_queue
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="WindowSender", daemon=True)

    def start(self) -> None:
        logger.info("WindowSender starting.")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def update_config(self, new_config) -> None:
        self._config = new_config

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                actions = self._action_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not _find_and_focus_eq(self._config.eq_window_title):
                logger.warning("Skipping actions — could not focus EQ window.")
                continue

            for action in actions:
                if self._stop_event.is_set():
                    break
                logger.debug("Sending: %r", action.text)
                try:
                    _send_string(action.text)
                except Exception as e:
                    logger.error("Error sending %r: %s", action.text, e)
                if action.delay_after > 0:
                    time.sleep(action.delay_after)

        logger.info("WindowSender stopped.")
