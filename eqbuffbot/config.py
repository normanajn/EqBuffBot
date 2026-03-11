"""Configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml


class ConfigError(Exception):
    pass


@dataclass
class TriggerAction:
    text: str
    delay_after: float = 0.0


@dataclass
class TriggerConfig:
    name: str
    match: str
    actions: list[TriggerAction]
    sender_whitelist: Optional[list[str]] = None
    default: bool = False


@dataclass
class AppConfig:
    character_name: str
    log_file: str
    eq_window_title: str
    global_cooldown: float
    triggers: list[TriggerConfig]


def load_config(path: str) -> AppConfig:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config YAML: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must be a YAML mapping.")

    def require(key: str):
        if key not in data or data[key] is None:
            raise ConfigError(f"Missing required config key: '{key}'")
        return data[key]

    character_name = str(require("character_name"))
    log_file = str(require("log_file"))
    eq_window_title = str(require("eq_window_title"))
    global_cooldown = float(data.get("global_cooldown", 5.0))

    raw_triggers = data.get("triggers", [])
    if not isinstance(raw_triggers, list):
        raise ConfigError("'triggers' must be a list.")

    triggers: list[TriggerConfig] = []
    for i, t in enumerate(raw_triggers):
        if not isinstance(t, dict):
            raise ConfigError(f"Trigger #{i} must be a mapping.")

        t_name = str(t.get("name", f"trigger_{i}"))
        t_default = bool(t.get("default", False))
        t_match = t.get("match", "")
        if not t_match and not t_default:
            raise ConfigError(f"Trigger '{t_name}' missing required key 'match'.")

        t_whitelist = t.get("sender_whitelist")
        if t_whitelist is not None:
            if not isinstance(t_whitelist, list):
                raise ConfigError(f"Trigger '{t_name}' sender_whitelist must be a list or null.")
            t_whitelist = [str(s) for s in t_whitelist]

        raw_actions = t.get("actions", [])
        if not isinstance(raw_actions, list) or len(raw_actions) == 0:
            raise ConfigError(f"Trigger '{t_name}' must have at least one action.")

        actions: list[TriggerAction] = []
        for j, a in enumerate(raw_actions):
            if not isinstance(a, dict):
                raise ConfigError(f"Trigger '{t_name}' action #{j} must be a mapping.")
            a_text = a.get("text")
            if a_text is None:
                raise ConfigError(f"Trigger '{t_name}' action #{j} missing 'text'.")
            a_delay = float(a.get("delay_after", 0.0))
            actions.append(TriggerAction(text=str(a_text), delay_after=a_delay))

        triggers.append(TriggerConfig(
            name=t_name,
            match=str(t_match),
            actions=actions,
            sender_whitelist=t_whitelist,
            default=t_default,
        ))

    return AppConfig(
        character_name=character_name,
        log_file=log_file,
        eq_window_title=eq_window_title,
        global_cooldown=global_cooldown,
        triggers=triggers,
    )
