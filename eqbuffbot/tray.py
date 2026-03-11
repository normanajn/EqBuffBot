"""System tray icon and menu for EQBuffBot."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from typing import Callable

logger = logging.getLogger(__name__)


def _create_icon_image():
    """Create a simple colored square icon if no icon file is present."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (64, 64), color=(30, 80, 180))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 8, 56, 56], outline=(255, 215, 0), width=4)
        draw.text((20, 22), "EQ", fill=(255, 215, 0))
        return img
    except Exception:
        return None


def run_tray(pause_event: threading.Event, quit_callback: Callable[[], None], reload_callback: Callable[[], None], log_path: str) -> None:
    """Run the system tray icon. Blocks until the user quits."""
    try:
        import pystray
        from pystray import MenuItem, Menu
    except ImportError:
        logger.warning("pystray not installed; running without tray icon.")
        import signal
        signal.signal(signal.SIGINT, lambda *_: quit_callback())
        signal.pause()
        return

    icon_image = _create_icon_image()
    if icon_image is None:
        logger.warning("Could not create tray icon image.")
        return

    def on_pause(icon, item):
        if pause_event.is_set():
            pause_event.clear()
            logger.info("Resumed.")
        else:
            pause_event.set()
            logger.info("Paused.")

    def on_open_log(icon, item):
        try:
            os.startfile(log_path)
        except Exception as e:
            logger.error("Could not open log: %s", e)

    def on_reload(icon, item):
        # Run in a thread so the tray stays responsive during reload
        threading.Thread(target=reload_callback, name="ConfigReload", daemon=True).start()

    def on_quit(icon, item):
        icon.stop()
        quit_callback()

    def pause_label(item):
        return "Resume" if pause_event.is_set() else "Pause"

    icon = pystray.Icon(
        "EQBuffBot",
        icon_image,
        "EQBuffBot",
        menu=Menu(
            MenuItem(pause_label, on_pause),
            MenuItem("Reload Config", on_reload),
            MenuItem("Open Log", on_open_log),
            MenuItem("Quit", on_quit),
        ),
    )

    logger.info("Tray icon running.")
    icon.run()
