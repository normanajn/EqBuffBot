"""Monitor an EverQuest log file and push new lines into a queue."""

from __future__ import annotations

import logging
import os
import queue
import threading
import time

logger = logging.getLogger(__name__)

# Seconds between polls when no file-system event is received
_POLL_INTERVAL = 0.25


class LogMonitor:
    """Tail an EQ log file and put each new line into *line_queue*."""

    def __init__(self, log_path: str, line_queue: "queue.Queue[str]"):
        self._path = log_path
        self._queue = line_queue
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="LogMonitor", daemon=True)

    def start(self) -> None:
        logger.info("LogMonitor starting, watching: %s", self._path)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        """Open the log file, seek to end, then tail new content."""
        fh = None
        last_inode = None
        last_size = None

        while not self._stop_event.is_set():
            # Open (or reopen) the file if needed
            try:
                stat = os.stat(self._path)
                current_inode = stat.st_ino
                current_size = stat.st_size
            except FileNotFoundError:
                if fh:
                    fh.close()
                    fh = None
                logger.warning("Log file not found, waiting: %s", self._path)
                time.sleep(1.0)
                continue

            # Detect log rotation: inode changed or file shrank
            rotated = (
                fh is not None and (
                    current_inode != last_inode or current_size < last_size
                )
            )

            if fh is None or rotated:
                if fh:
                    logger.info("Log rotation detected, reopening.")
                    fh.close()
                try:
                    fh = open(self._path, "r", encoding="utf-8", errors="replace")
                    # On first open, seek to end to skip historical lines.
                    # On rotation, start from the beginning of the new file.
                    if last_inode is None:
                        fh.seek(0, 2)  # seek to end
                    last_inode = current_inode
                    last_size = current_size
                    logger.info("Opened log file at position %d", fh.tell())
                except OSError as e:
                    logger.error("Cannot open log file: %s", e)
                    time.sleep(1.0)
                    continue

            # Read all available new lines
            while True:
                line = fh.readline()
                if not line:
                    break
                line = line.rstrip("\r\n")
                if line:
                    self._queue.put(line)

            last_size = current_size
            time.sleep(_POLL_INTERVAL)

        if fh:
            fh.close()
        logger.info("LogMonitor stopped.")
