# EQBuffBot

An EverQuest buff bot that monitors your log file for direct tells and automatically responds by sending keystrokes to the EQ window.

## How It Works

1. Monitors your EverQuest log file for incoming tells
2. Matches the tell message against your configured triggers
3. Focuses the EQ window and sends the configured keystroke sequence

## Requirements

- Python 3.11+
- Windows 10/11
- EverQuest with logging enabled (`/log` in-game to toggle)

## Installation

```bash
pip install -r requirements.txt
```

## Running

Double-click `run.bat`, or from a terminal:

```bash
python -m eqbuffbot.main
```

To use a different config file:

```bash
python -m eqbuffbot.main --config mychar_config.yaml
python -m eqbuffbot.main -c mychar_config.yaml
```

## Configuration

Edit `config.yaml` before running. Key settings:

| Setting | Description |
|---|---|
| `character_name` | Your character's name |
| `log_file` | Full path to your EQ log file |
| `eq_window_title` | Part of the EverQuest window title |
| `global_cooldown` | Minimum seconds between any two trigger fires |

### Triggers

Each trigger watches for a substring in incoming tells and sends a sequence of actions to EQ.

```yaml
triggers:
  - name: "sow"
    match: "sow"              # case-insensitive substring match
    sender_whitelist: null    # null = anyone; or list specific names

    actions:
      - text: "{ENTER}/cast 8{ENTER}"
        delay_after: 1.5      # seconds to wait before next action
      - text: "{ENTER}/r You are fast now{ENTER}"
        delay_after: 0.0

  - name: "default"
    default: true             # fires when no other trigger matches
    actions:
      - text: "{ENTER}/r I don't recognize that command.{ENTER}"
        delay_after: 0.0
```

### Special Keys

Use curly-brace notation in `text` fields:

| Token | Key |
|---|---|
| `{ENTER}` | Enter |
| `{TAB}` | Tab |
| `{ESC}` | Escape |
| `{SPACE}` | Space |
| `{F1}`–`{F12}` | Function keys |
| `{UP}` `{DOWN}` `{LEFT}` `{RIGHT}` | Arrow keys |
| `{DELETE}` | Delete |
| `{BACK}` | Backspace |

### Sender Whitelist

Restrict a trigger to specific characters:

```yaml
sender_whitelist:
  - "Guildmate"
  - "Aleran"
```

Set to `null` to respond to tells from anyone.

### Default Trigger

Add `default: true` to a trigger (no `match` needed) to catch any tell that didn't match another trigger:

```yaml
- name: "default"
  default: true
  actions:
    - text: "{ENTER}/r Available commands: sow, haste, buffs{ENTER}"
      delay_after: 0.0
```

## System Tray

EQBuffBot runs in the system tray with the following options:

- **Pause / Resume** — temporarily stop responding to tells
- **Reload Config** — reload `config.yaml` without restarting
- **Open Log** — open the bot's log file (`eqbuffbot.log`)
- **Quit** — exit the bot

## Log File

The bot writes its own log to `eqbuffbot.log` in the project folder. Check this file if triggers aren't firing — it will show tells received, triggers matched, and any errors.

## EQ Log Format

EverQuest must have logging enabled. The bot looks for lines in this format:

```
[Sun Mar 08 12:34:56 2026] SenderName tells you, 'message'
```

Enable logging in-game with `/log on`. Log files are located at:

```
C:\Users\Public\Daybreak Game Company\Installed Games\EverQuest\Logs\
```
