"""EQBuffBot entry point."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import queue
import sys
import threading

# ---------------------------------------------------------------------------
# Resolve paths relative to the repo root (one level up from this package)
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

_DEFAULT_CONFIG = os.path.join(_ROOT, "config.yaml")
BOT_LOG_PATH = os.path.join(_ROOT, "eqbuffbot.log")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="eqbuffbot",
        description="EverQuest buff bot — monitors the log and sends keystrokes.",
    )
    parser.add_argument(
        "-c", "--config",
        default=_DEFAULT_CONFIG,
        metavar="FILE",
        help=f"Path to config YAML file (default: {_DEFAULT_CONFIG})",
    )
    return parser.parse_args()


def _setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(threadName)s] %(levelname)s %(name)s: %(message)s")

    # Rotating file handler (5 MB × 3 backups)
    fh = logging.handlers.RotatingFileHandler(
        BOT_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler (INFO and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)


def main() -> None:
    args = _parse_args()
    CONFIG_PATH = os.path.abspath(args.config)

    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("EQBuffBot starting up.")
    logger.info("Using config: %s", CONFIG_PATH)

    # Import here so logging is configured first
    from .config import load_config, ConfigError
    from .log_monitor import LogMonitor
    from .trigger_engine import TriggerEngine
    from .window_sender import WindowSender
    from .tray import run_tray

    # Load configuration
    try:
        config = load_config(CONFIG_PATH)
    except ConfigError as e:
        logger.critical("Configuration error: %s", e)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(e), "EQBuffBot Config Error", 0x10)
        except Exception:
            pass
        sys.exit(1)

    logger.info(
        "Loaded config: character=%s, triggers=%d",
        config.character_name, len(config.triggers),
    )

    # Shared queues
    line_queue: queue.Queue[str] = queue.Queue()
    action_queue: queue.Queue[list] = queue.Queue()

    # Pause event: set = paused, clear = running
    pause_event = threading.Event()

    # Components
    monitor = LogMonitor(config.log_file, line_queue)
    engine = TriggerEngine(config, line_queue, action_queue, pause_event)
    sender = WindowSender(config, action_queue)

    # Start background threads
    monitor.start()
    engine.start()
    sender.start()

    def _quit():
        logger.info("Shutting down...")
        monitor.stop()
        engine.stop()
        sender.stop()

    def _reload():
        nonlocal monitor, config
        logger.info("Reloading configuration...")
        try:
            new_config = load_config(CONFIG_PATH)
        except ConfigError as e:
            logger.error("Config reload failed: %s", e)
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, str(e), "EQBuffBot Reload Error", 0x10)
            except Exception:
                pass
            return

        old_log = config.log_file
        config = new_config
        engine.update_config(new_config)
        sender.update_config(new_config)

        # Restart monitor only if the log file path changed
        if new_config.log_file != old_log:
            logger.info("Log path changed, restarting monitor.")
            monitor.stop()
            monitor = LogMonitor(new_config.log_file, line_queue)
            monitor.start()

        logger.info(
            "Config reloaded: character=%s, triggers=%d",
            new_config.character_name, len(new_config.triggers),
        )

    # Run tray (blocks main thread until user quits)
    try:
        run_tray(pause_event, _quit, _reload, BOT_LOG_PATH)
    except KeyboardInterrupt:
        _quit()

    logger.info("EQBuffBot exited.")


if __name__ == "__main__":
    main()
