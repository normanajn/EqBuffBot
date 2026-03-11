# EQBuffBot

* Do you belong to a large guild and want to provide your class's buffs to others?
* Are you constantly needing all your characters to have the buffs they need to perform at thier best?  
* Are you playing a class that is constantly being asked for buffs?
* Do you need a way to organize your buffing life?

Welcome to EQBuffBot!  

EQBuffBot is a simple system for managing the complex ecosystem of spells and buffs that Everquest provides.  The program is designed to monitor what is going on with your character and take actions based on tells and other cues that the game provides.

This can make it easy to:
1. Respond to constant tells for "SoW me!", "Haste please" etc....
2. Customize the buffs you give different characters (i.e. Raifin really like Speed of Shissar not Visions of Grandure)
3. Setup buffing stations in your guild hall to speed raid buffing
4. Refresh short duration buffs more accurately

## How It Works

So how does this work?  In a nut shell it reads and reacts.  The program reads your logfiles and then sends commands to your interface.

Specificially it:
1. Monitors your EverQuest log file for incoming tells or other events that can be pattern matched
2. Matches the messages/events against your configured triggers
3. Focuses the EQ window
4. Sends the configured commands/keystrokes sequences to EQ

For example:
```
Tehom is an enchanter.  

Tehom recieves a tell for "haste please".  The tell message shows up in his logfile and is parsed (<blank> tells you haste please).  This matches an event rule that 1. issues an /rtar (target last player to send a tell) 2. /cast 8 (or /cast Visions of Grandure)

Tehom's sanity is preserved during raids
```


## Requirements

EQBuffBot is designed to run under Windows 10/11.  It does NOT need the windows subsystem for Linux.  Just a normal power shell to start the application (or via the start script).  However there are a few dependancies that need to be present:

- Windows 10/11. (earlier versions may work but aren't tested)
- EverQuest with logging enabled (`/log` in-game to toggle)
- Python 3.11+
- Python viritual environments
- Python packages described in the requirements

## Installation

If you are running the program for the first time you will need to install the package dependancies.

If you use virtual environments then you will want to create a virtual environment and then populate it.  Otherwise you can just skip to the `pip install` part and install the dependancies globally.
```
python -m venv venv.  # Creates a virtual environment tree called venv in the current directory
source venv/bin/activate. # Activate the virtual environment
pip install -r requirements.txt
```

Or without virtual environments:
```bash
pip install -r requirements.txt
```

## Running

When you start the program it will go to your status bar and be available from there.  It can be stopped and reconfigured when running from the status area.

To start it,  Double-click `run.bat`, or from a terminal:

```bash
python -m eqbuffbot.main
```

To use a different config from the default file you can pass it along as a commandline option:

```bash
python -m eqbuffbot.main --config mychar_config.yaml
python -m eqbuffbot.main -c mychar_config.yaml
```

## Configuration

All parameters and triggers are controled through a configuration file.  The file is split into two main sections, general config and event triggers.

Start by editing the provided `config.yaml` example before running and customize it to your character and setup.

Key settings you will want to change are:

| Setting | Description |
|---|---|
| `character_name` | Your character's name |
| `log_file` | Full path to your EQ log file |
| `eq_window_title` | Part of the EverQuest window title |
| `global_cooldown` | Minimum seconds between any two trigger fires |

### Triggers

Triggers are essentially a pattern that is matched and then actions that are taken.  You can have any number of triggers defined with each following the same general pattern.

In this initial version each trigger watches for a substring in incoming tells ONLY (i.e. it must be a direct tell to you and must have the given substring in it) and when it is detect then executes the  sends a sequence of actions as direct input to EQ.

Example of a Spirt of the Wolf trigger:

```yaml
triggers:
  - name: "Movement Speed"
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

If a command sequence needs a special key you can input it using the curly-brace notation in the `text` fields.  This is supported for the following keys:

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

Do you love/hate certain people?  Do you hate Furor?  I do.  So if you want to restrict things only respond to certain people you can create a whitelist with the different names of people to respond to.

The syntax to restrict a trigger to specific characters is:

```yaml
sender_whitelist:
  - "Guildmate"
  - "Apostate"
  - "Gster"
  - "Etasi"
```

If the whitelist is set to `null` it responds to tells from anyone.

### Default Trigger

What about when people send a tell that doesn't match?  Well there are a couple of options.  If you do not have a default trigger defined then nothing happens.  This is great if you are raiding and get random tells for buffs mixed in with normal tells that you want to respond to normally.

IF you have a default defined then if nothing else matches, it will fire off.  This is good if you are leaving a toon up in a guild hall and want it to respond with a list of options.  HOWEVER, it will respond to ALL tells that don't match with this. (so be cautioned since this will basically make it so that people can't chat with you normally)

To setup a default just add `default: true` to a trigger (no `match` needed) to catch any tell that didn't match another trigger:

```yaml
- name: "default"
  default: true
  actions:
    - text: "{ENTER}/r Available commands: sow, haste, buffs, hawt cyborz{ENTER}"
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

## Enjoy and Cyborz on!

Enjoy all your buffs.  And for those who are interested you can probably tell that you can setup all sorts of fun triggers to respond to silly things.  Get a lot of "A/S/L"?  You know what to do....