"""Match incoming tells against configured triggers and dispatch actions."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import TYPE_CHECKING

from .config import AppConfig, TriggerConfig
from .tell_parser import TellEvent, parse_line

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TriggerEngine:
    """Read lines from *line_queue*, parse tells, fire matching triggers."""

    def __init__(
        self,
        config: AppConfig,
        line_queue: "queue.Queue[str]",
        action_queue: "queue.Queue[list]",
        pause_event: threading.Event,
    ):
        self._config = config
        self._line_queue = line_queue
        self._action_queue = action_queue
        self._pause_event = pause_event
        self._last_fire_time: float = 0.0
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="TriggerEngine", daemon=True)

    def start(self) -> None:
        logger.info("TriggerEngine starting.")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def update_config(self, new_config: AppConfig) -> None:
        self._config = new_config

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                line = self._line_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if self._pause_event.is_set():
                continue

            tell = parse_line(line, self._config.character_name)
            if tell is None:
                continue

            logger.debug("Tell received from %s: %s", tell.sender, tell.message)

            # Global cooldown check
            now = time.monotonic()
            if now - self._last_fire_time < self._config.global_cooldown:
                logger.debug("Global cooldown active, skipping tell.")
                continue

            matched = False
            for trigger in self._config.triggers:
                if trigger.default:
                    continue  # handled below if nothing else matches
                if self._matches(tell, trigger):
                    logger.info(
                        "Trigger '%s' matched tell from %s: %s",
                        trigger.name, tell.sender, tell.message,
                    )
                    self._action_queue.put(trigger.actions)
                    self._last_fire_time = time.monotonic()
                    matched = True
                    break

            if not matched:
                default = next((t for t in self._config.triggers if t.default), None)
                if default:
                    logger.info("Default trigger fired for tell from %s: %s", tell.sender, tell.message)
                    self._action_queue.put(default.actions)
                    self._last_fire_time = time.monotonic()

        logger.info("TriggerEngine stopped.")

    def _matches(self, tell: TellEvent, trigger: TriggerConfig) -> bool:
        # Case-insensitive substring match on message
        if trigger.match.lower() not in tell.message.lower():
            return False

        # Sender whitelist check
        if trigger.sender_whitelist is not None:
            if tell.sender not in trigger.sender_whitelist:
                return False

        return True
