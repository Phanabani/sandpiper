# Sandpiper

[![release](https://img.shields.io/github/v/release/hawkpath/sandpiper)](https://github.com/Hawkpath/sandpiper/releases)
[![license](https://img.shields.io/github/license/hawkpath/sandpiper)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

Sandpiper is a Discord bot that makes it easier to communicate with friends
around the world.

Her current features include:
- Unit conversion between imperial and metric quantities
- Time conversion between the timezones of users in your server
- Miniature user bios
    - Set your preferred name, pronouns, birthday, and timezone
    - Manage the privacy of each of these fields (private by default, but they 
    may be set to public visibility)
- Search for users by their preferred name, Discord username, or server nicknames

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Config](#config)
- [Commands and features](#commands-and-features)
    - [Unit conversion](#unit-conversion)
    - [Time conversion](#time-conversion)
    - [Bios](#bios)
- [Developers](#developers)
- [Planned features](#planned-features)
- [Inspiration](#inspiration)
- [License](#license)

## Install

To get started, clone the repo.

```shell script
git clone https://github.com/hawkpath/sandpiper.git
cd sandpiper
```

With Python 3.8+, create a virtual environment and install dependencies.

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

### Running Sandpiper

#### Basic

In the top level directory, simply run Sandpiper as a Python module.

```shell script
python -m sandpiper
```

#### With PM2

[PM2](https://pm2.keymetrics.io/docs/usage/quick-start/) is a daemon process
manager. Ensure you've followed the virtual environment setup described above,
then simply run the following command in Sandpiper's root directory:

```shell script
pm2 start
```

This starts the process as a daemon using info from [ecosystem.config.js](ecosystem.config.js).

### Inviting Sandpiper to your Discord server

Sandpiper requires the following permissions to run normally:

- View Channels
- Send Messages
- Embed links

These correspond to the permission integer `19456`.

Sandpiper also requires the [server members privileged intent](https://discord.com/developers/docs/topics/gateway#privileged-intents)
to allow for Discord username/server nickname lookup in the `whois` command.
You can enable it on the bot page of your application (https:\/\/discord.com/developers/applications/<client_id>/bot).

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
`format` *(string)* | Format string used when writing log messages ([format string reference](https://docs.python.org/3/library/logging.html#logrecord-attributes))

## Commands and features

In servers, commands must be prefixed with the configured command prefix
(default=`"!piper "`). When DMing Sandpiper, you do not need to prefix commands.

### Unit conversion

Convert measurements written in regular messages! Just surround a measurement
in {curly brackets} and Sandpiper will convert it for you. You can put
multiple measurements in a message as long as each is put in its own brackets.

#### Examples

> guys it's **{30f}** outside today, I'm so cold...

> I've been working out a lot lately and I've already lost **{2 kg}**!!

> I think Jason is like **{6' 2"}** tall

> Lou lives about **{15km}** from me and TJ's staying at a hotel **{1.5km}**
> away, so he and I are gonna meet up and drive over to Lou.

#### Supported units:

Metric | Imperial
------ | --------
Kilometer `km` | Mile `mi`
Meter `m` | Foot `ft or '`
Centimeter `cm` | Inch `in or "`
Kilogram `kg` | Pound `lbs`
Celsius `C or degC or °C` | Fahrenheit `F or degF or °F`

### Time conversion

Just like [unit conversion](#unit-conversion), you can also convert times
between timezones! Surround a time in {curly brackets} and Sandpiper will
convert it to the different timezones of users in your server.

Times can be formatted in 12- or 24-hour time and use colon separators (HH:MM).
12-hour times can optionally include AM or PM to specify what half of the day
you mean. If you don't specify, AM will be assumed.
 
You can put multiple times in a message as long as each is put in its own brackets.

To use this feature, you and your friends need to set your timezones with the
`timezone set` command (see the [bio commands section](#setting-your-info)
for more info).

#### Examples

> do you guys wanna play at {9pm}?

> I wish I could, but I'm busy from {14} to {17:45}

> yeah I've gotta wake up at {5} for work tomorrow, so it's an early bedtime
> for me

### Bios

Store some info about yourself to help your friends get to know you more easily!
Most of these commands can only be used in DMs with Sandpiper for your privacy.

#### General commands

Command | Description
------- | -----------
`bio show` | Display all your stored info and their privacy settings.
`bio delete` | Delete all your stored info.

#### Setting your info

Setting a field doesn't automatically make it public. See the [privacy section](#manage-the-privacy-of-your-info)
for more info about managing your privacy.

Command | Description | Example
------- | ----------- | -------
`name set <new_name>` | Set your preferred name (max 64 characters). | `name set Hawk`
`pronouns set <new_pronouns>` | Set your pronouns (max 64 characters). | `pronouns set She/Her`
`birthday set <new_birthday>` | Set your birthday in one of the following formats: `1997-08-27`, `8 August 1997`, `Aug 8 1997`, `August 8`, `8 Aug`. You may omit your birth year with the month-name format (age will not be calculated). | `birthday set 1997-08-27`
`timezone set <new_timezone>` | Set your timezone. Don't worry about formatting. Typing the name of the nearest major city should be good enough, but you can also try your state/country if that doesn't work. If you're confused, use this website to find your full timezone name: http://kevalbhatt.github.io/timezone-picker | `timezone set new york`

#### Displaying your info

Command | Description | Example
------- | ----------- | -------
`name show` | Display your preferred name. | `name show`
`pronouns show` | Display your pronouns. | `pronouns show`
`birthday show` | Display your birthday. | `birthday show`
`age show` | Display your age (calculated automatically from your birthday). | `age show`
`timezone show` | Display your timezone. | `timezone show`

#### Deleting your info

Command | Description | Example
------- | ----------- | -------
`name delete` | Delete your preferred name. | `name delete`
`pronouns delete` | Delete your pronouns. | `pronouns delete`
`birthday delete` | Delete your birthday. | `birthday delete`
`timezone delete` | Delete your timezone. | `timezone delete`

#### Manage the privacy of your info

You can set the privacy for each field in your bio to either `public` or
`private`. Everything is private by default. If you set a field as public,
anyone may be able to see it as long as they are in the same server as you and
Sandpiper.

Command | Description | Example
------- | ----------- | -------
`privacy all <new_privacy>` | Set the privacy of all your info at once. | `privacy all public`
`privacy name <new_privacy>` | Set the privacy of your preferred name. | `privacy name public`
`privacy pronouns <new_privacy>` | Set the privacy of your pronouns. | `privacy pronouns public`
`privacy birthday <new_privacy>` | Set the privacy of your birthday. | `privacy birthday private`
`privacy age <new_privacy>` | Set the privacy of your age. | `privacy age private`
`privacy timezone <new_privacy>` | Set the privacy of your timezone. | `privacy timezone public`

#### Search for users by one of their names

If you're new to a server, you might hear someone's name floating around but not
know who they are. Sandpiper lets you search for users by either their
preferred name (configured with the `name set` command), their Discord username,
or their nickname in a server you are both in.

You can run this command in a server or in Sandpiper DMs.

Command | Description | Example
------- | ----------- | -------
`whois <name>` | Search for a user by one of their names on Discord. | `whois jason`

## Developers

### Installation

Follow the installation steps in [install](#install) and install the
development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

### Testing

#### Run unit tests

```bash
python -m sandpiper.tests
```

#### Run tests with code coverage

```bash
coverage run -m sandpiper.tests
coverage html
```

Open `htmlcov/index.html` to view the coverage report.

## Planned features

- [X] Unit conversion
- [X] User bios
  - [X] Preferred name
  - [X] Pronouns
  - [X] Birthday
  - [X] Timezone
- [X] Time conversion
- [ ] Birthday notifications

## Inspiration

These Discord bots inspired the development of Sandpiper:

- [Friend-Time by Kevin Novak](https://github.com/KevinNovak/Friend-Time) - inspiration for time and unit conversion features
- [Birthday Bot by NoiTheCat](https://github.com/NoiTheCat/BirthdayBot) - inspiration for upcoming birthday feature

## License

[MIT © Hawkpath.](LICENSE)
