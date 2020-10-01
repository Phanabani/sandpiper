# Sandpiper

[![release](https://img.shields.io/github/v/release/hawkpath/sandpiper)](https://github.com/Hawkpath/sandpiper/releases)
[![license](https://img.shields.io/github/license/hawkpath/sandpiper)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Sandpiper is a Discord bot that makes it easier to communicate with friends
around the world.

Her current features include:
- Unit conversion between imperial and metric quantities

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Config](#config)
- [Commands and features](#commands-and-features)
- [Planned features](#planned-features)
- [License](#license)

## Install

To get started, clone the repo.

```shell script
git clone https://github.com/hawkpath/sandpiper.git
cd sandpiper
```

Create a virtual environment and install dependencies.

```shell script
python -m venv venv

# Linux / OSX:
source venv/bin/activate

# Windows:
call venv\Scripts\activate.bat

python -m pip install -r requirements.txt
```

## Usage

### Set up configuration

Create a json file `sandpiper/config.json` (or copy [sandpiper/config_example.json](sandpiper/config_example.json)).
The only value you need to set is the `bot_token`.

```json
{
    "bot_token": "<YOUR_BOT_TOKEN>"
}
```

See [config](#config) for more configuration options.

### Running the bot

#### Basic

In the top level directory, simply run sandpiper as a Python module.

```shell script
python -m sandpiper
```

#### With PM2

[PM2](https://pm2.keymetrics.io/docs/usage/quick-start/) is a daemon process
manager. Ensure you've followed the virtual environment setup described above,
then simply run:

```shell script
pm2 start
```

This starts the process as a daemon using info from [ecosystem.config.js](ecosystem.config.js).

## Config

Sandpiper can be configured with a JSON file at `./sandpiper/config.json`.
[sandpiper/config_example.json](sandpiper/config_example.json) contains
default values and can be used as a template. `bot_token` is the only required
field.

### Config Fields

#### Root

Fields in the root JSON object.

Key | Value
--- | -----
`bot_token` *(string)* | Your [Discord bot's](https://discord.com/developers/docs/topics/oauth2#bots) access token

#### Bot

Fields in `(root).bot` which describe the bot itself. See also
the [discord.py bot documentation](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot)
for more info on how these fields are used.

Key | Value
--- | -----
`command_prefix` *(string)* | What users type to run a command
`description` *(string)* | Description of the bot (used in help messages)

#### Logging

Fields in `(root).logging` which describe how logging is performed. Sandpiper
uses rotating logging to write log files which rotate in specified intervals.
See also the
[TimedRotatingFileHandler documentation](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
for more info on how these fields are used.

Key | Value
--- | -----
`sandpiper_logging_level` *(string)* | Sandpiper's most verbose logging level. Must be one of ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
`discord_logging_level` *(string)* | discord.py's most verbose logging level. Must be one of ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
`output_file` *(string)* | Absolute or relative (to sandpiper module) filepath to output logs to (including filename)
`when` *(string)* | Type of time interval for rotating log files. Must be one of ('S', 'M', 'H', 'D', 'midnight')
`interval` *(integer)* | Number of specified time intervals that must elapse before rotating to a new log file
`backup_count` *(integer)* | Number of backup log files to retain (deletes oldest after limit is reached)
`format` *(string)* | Format string used when writing log messages ([format string reference](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot))

## Commands and features

### Unit conversion

Convert measurements written in regular messages! Just surround a measurement
in {curly brackets} and Sandpiper will convert it for you. You can put
multiple measurements in a message (just be sure that each is put in its own
brackets).

Here are some examples:

> guys it's **{30f}** outside today, I'm so cold...

> I've been working out a lot lately and I've already lost **{2 kg}**!!

> I think Jason is like **{6' 2"}**

> Lou lives about **{15km}** from me and TJ's staying at a hotel **{1.5km}**
> away, so he and I are gonna meet up and drive over to Lou.

Currently supported units:

Metric | Imperial
------ | --------
Kilometer `km` | Mile `mi`
Meter `m` | Foot `ft or '`
Centimeter `cm` | Inch `in or "`
Kilogram `kg` | Pound `lbs`
Celsius `C or degC or °C` | Fahrenheit `F or degF or °F`

## Planned features

- [X] Unit conversion
- [ ] User bios
  - [ ] Preferred name
  - [ ] Pronouns
  - [ ] Birthday
  - [ ] Timezone
- [ ] Time conversion
- [ ] Birthday notifications

## License

[MIT © Hawkpath.](LICENSE)
