# Sandpiper

[![release](https://img.shields.io/github/v/release/phanabani/sandpiper)](https://github.com/phanabani/sandpiper/releases)
[![license](https://img.shields.io/github/license/phanabani/sandpiper)](LICENSE)
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
    - [Birthday notifications](#birthday-notifications)
- [Developers](#developers)
- [Planned features](#planned-features)
- [Inspiration](#inspiration)
- [License](#license)

## Install

### Prerequisites

- [Poetry](https://python-poetry.org/docs/#installation) – dependency manager
- (Optional) pyenv – Python version manager
    - [pyenv](https://github.com/pyenv/pyenv) (Linux, Mac)
    - [pyenv-win](https://github.com/pyenv-win/pyenv-win) (Windows)
- (Optional) [PM2](https://pm2.keymetrics.io/docs/usage/quick-start) – process manager

### Install Sandpiper

To get started, clone the repo.

```shell
git clone https://github.com/phanabani/sandpiper.git
cd sandpiper
```

Install the dependencies with Poetry. Sandpiper requires Python 3.10.

```shell
# If you're using pyenv, run the following to init a Poetry environment using
# the correct Python version
poetry env use $(pyenv which python)

# Install dependencies
poetry install --no-root --no-dev
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

See [config](#config) for more info.

### Running Sandpiper

#### Basic

In the top level directory, simply run Sandpiper as a Python module with Poetry.

```shell script
poetry run python -m sandpiper
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

Sandpiper can be configured with a JSON file at `sandpiper/config.json`.
[sandpiper/config_example.json](sandpiper/config_example.json) contains
default values and can be used as a template. `bot_token` is the only required
field.

See [Config](docs/config.md) for detailed information about setting up the
config file.

## Commands and features

In servers, commands must be prefixed with the configured command prefix
(default=`"!piper "`). When DMing Sandpiper, you do not need to prefix commands.

### Unit conversion

Convert measurements written in regular messages! Just surround a measurement
in curly brackets -- like this: `{5 ft}` -- and Sandpiper will convert it for
you. You can put multiple measurements in a message as long as each is put in
its own brackets.

Many measurements are converted by default without needing to specify an output
unit. Read [Default unit mappings](docs/default_unit_mappings.md) to see all
currently supported default conversions.

You can explicitly specify an output unit like this: `{2 tonnes > lbs}`.
This opens up to you nearly any unit conversion you may need.

Lastly, you can do math in conversions, too! `{2.3 ft + 5 in}`

#### Examples

> guys it's **{30f}** outside today, I'm so cold...

> I've been working out a lot lately and I've already lost **{2 kg}**!!

> I think Jason is like **{6' 2"}** tall

> Lou lives about **{15km}** from me and TJ's staying at a hotel **{1.5km}**
> away, so he and I are gonna meet up and drive over to Lou.

> I weigh about 9.3 stone. For you americans, that's **{9.3 stone > lbs}**

> my two favorite songs are **{5min+27s}** and **{4min+34s}**. that's a total
> time of **{5min+27s + 4min+34s > s}** seconds

> hey sandpiper what's **{30 * 7}**?

### Time conversion

Just like [unit conversion](#unit-conversion), you can also convert times
between timezones! Surround a time in curly brackets `{5:30pm}` and Sandpiper
will convert it to the different timezones of users in your server.

Times can be formatted in 12- or 24-hour time and use colon separators (HH:MM).
12-hour times can optionally include AM or PM to specify what half of the day
you mean. If you don't specify, AM will be assumed.

You can use the keywords `now`, `midnight`, and `noon` instead of a numeric time.
 
You can put multiple times in a message as long as each is put in its own brackets.

You can explicitly specify input and output timezones very similarly to
how units are specified in unit conversion:

| Timezone specification  | How to write                     | What it does                                                             |
|-------------------------|----------------------------------|--------------------------------------------------------------------------|
| Input timezone          | `{5:45 PM London}`               | Converts 5:45 PM in London time to all timezones of users in your server |
| Output timezone         | `{5:45 PM > Los Angeles}`        | Converts 5:45 PM from your timezone to Los Angeles time                  |
| Input & output timezone | `{5:45 PM Amsterdam > Helsinki}` | Converts 5:45 PM in Amsterdam time to Helsinki time                      |

To use this feature without having to specify input/output timezones every time,
you and your friends need to set your timezones with the `timezone set` command
(see the [bio commands section](#setting-your-info) for more info).

#### Examples

> do you guys wanna play at **{9pm}**?

> I wish I could, but I'm busy from **{14}** to **{17:45}**

> yeah I've gotta wake up at **{5}** for work tomorrow, so it's an early bedtime
> for me

> ugh I have a 2 hr meeting at **{noon}** tomorrow

> my flight took off at **{7pm new york}** and landed at **{8 AM london}**

> what time is it in dubai right now? **{now > dubai}**

> the game's releasing at **{1 PM > new york}** for americans and
> **{1500 > london}** for europeans

> hey alex, jaakko's getting on at **{8 pm helsinki > amsterdam}**

### Bios

Store some info about yourself to help your friends get to know you more easily!
Unless [specified otherwise in the config file](docs/config.md#botmodulesbios),
most of these commands can only be used in DMs with Sandpiper for your privacy.

#### General commands

| Command      | Description                                              |
|--------------|----------------------------------------------------------|
| `bio show`   | Display all your stored info and their privacy settings. |
| `bio delete` | Delete all your stored info.                             |

#### Setting your info

Setting a field doesn't automatically make it public. See the [privacy section](#manage-the-privacy-of-your-info)
for more info about managing your privacy.

| Command                       | Description                                                                                                                                                                                                                                                                                       | Example                   |
|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| `name set <new_name>`         | Set your preferred name (max 64 characters).                                                                                                                                                                                                                                                      | `name set Phana`          |
| `pronouns set <new_pronouns>` | Set your pronouns (max 64 characters).                                                                                                                                                                                                                                                            | `pronouns set She/Her`    |
| `birthday set <new_birthday>` | Set your birthday in one of the following formats: `1997-08-27`, `8 August 1997`, `Aug 8 1997`, `August 8`, `8 Aug`. You may omit your birth year with the month-name format (age will not be calculated).                                                                                        | `birthday set 1997-08-27` |
| `timezone set <new_timezone>` | Set your timezone. Don't worry about formatting. Typing the name of the nearest major city should be good enough, but you can also try your state/country if that doesn't work. If you're confused, use this website to find your full timezone name: http://kevalbhatt.github.io/timezone-picker | `timezone set new york`   |

#### Displaying your info

| Command         | Description                                                     | Example         |
|-----------------|-----------------------------------------------------------------|-----------------|
| `name show`     | Display your preferred name.                                    | `name show`     |
| `pronouns show` | Display your pronouns.                                          | `pronouns show` |
| `birthday show` | Display your birthday.                                          | `birthday show` |
| `age show`      | Display your age (calculated automatically from your birthday). | `age show`      |
| `timezone show` | Display your timezone.                                          | `timezone show` |

#### Deleting your info

| Command           | Description                 | Example           |
|-------------------|-----------------------------|-------------------|
| `name delete`     | Delete your preferred name. | `name delete`     |
| `pronouns delete` | Delete your pronouns.       | `pronouns delete` |
| `birthday delete` | Delete your birthday.       | `birthday delete` |
| `timezone delete` | Delete your timezone.       | `timezone delete` |

#### Manage the privacy of your info

You can set the privacy for each field in your bio to either `public` or
`private`. Everything is private by default. If you set a field as public,
anyone may be able to see it as long as they are in the same server as you and
Sandpiper.

| Command                          | Description                               | Example                    |
|----------------------------------|-------------------------------------------|----------------------------|
| `privacy all <new_privacy>`      | Set the privacy of all your info at once. | `privacy all public`       |
| `privacy name <new_privacy>`     | Set the privacy of your preferred name.   | `privacy name public`      |
| `privacy pronouns <new_privacy>` | Set the privacy of your pronouns.         | `privacy pronouns public`  |
| `privacy birthday <new_privacy>` | Set the privacy of your birthday.         | `privacy birthday private` |
| `privacy age <new_privacy>`      | Set the privacy of your age.              | `privacy age private`      |
| `privacy timezone <new_privacy>` | Set the privacy of your timezone.         | `privacy timezone public`  |

#### Search for users by one of their names

If you're new to a server, you might hear someone's name floating around but not
know who they are. Sandpiper lets you search for users by either their
preferred name (configured with the `name set` command), their Discord username,
or their nickname in a server you are both in.

You can run this command in a server or in Sandpiper DMs.

| Command        | Description                                         | Example       |
|----------------|-----------------------------------------------------|---------------|
| `whois <name>` | Search for a user by one of their names on Discord. | `whois jason` |

### Birthday notifications

Sandpiper can announce your birthday to your friends!

To enable this feature, set some of your info with the [bios](#bios) commands:

- Birthday
- \[Optional] Timezone
- \[Optional] Name
- \[Optional] Pronouns

You also need to set these fields to public with the [privacy commands](#manage-the-privacy-of-your-info)
for them to be used (otherwise, they are private by default, and Sandpiper will
not use them to keep your personal info private).

Here is how your personal info will be used to create your birthday announcement
message:

- Birthday
  - (Public) Your birthday will be announced on every server you and Sandpiper are in together
  - (Private) Your birthday will not be announced
- Timezone
  - (Public) Your birthday will be announced at midnight in your timezone
  - (Private) Your birthday will be announced at midnight UTC (coordinated universal time)
- Name
  - (Public) Your preferred name will be used in the message
  - (Private) Your Discord username will be used in the message
- Pronouns
  - (Public) Your pronouns will be used in the message
  - (Private) They/them will be used in the message
- Age
  - (Public and birth year set) Your new age will be displayed in the message
  - (Private or birth year not set) Your new age will not be displayed in the message

#### Commands

| Command              | Description                       | Example              |
|----------------------|-----------------------------------|----------------------|
| `birthdays upcoming` | Show upcoming and past birthdays. | `birthdays upcoming` |


## Developers

### Installation

Follow the installation steps in [install](#install) and use Poetry to 
install the development dependencies:

```bash
poetry install --no-root
```

### Testing

#### Run unit tests

```bash
poetry run python -m pytest --pyargs sandpiper
# or run tests with profiling (--profile-svg to generate svg image):
poetry run python -m pytest --pyargs --profile sandpiper
```

#### Run tests with code coverage

```bash
poetry run coverage run -m pytest --pyargs sandpiper
poetry run coverage html
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
- [X] Birthday notifications

## Inspiration

These Discord bots inspired the development of Sandpiper:

- [Friend-Time by Kevin Novak](https://github.com/KevinNovak/Friend-Time) - inspiration for time and unit conversion features
- [Birthday Bot by NoiTheCat](https://github.com/NoiTheCat/BirthdayBot) - inspiration for upcoming birthday feature

## License

[MIT © Phanabani.](LICENSE)
