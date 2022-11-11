# Config

Sandpiper can be configured with a JSON file at `sandpiper/config.json`.
[sandpiper/config_example.json](../sandpiper/config_example.json) contains
default values and can be used as a template. Field types suffixed by `?` are
optional.

## Config Fields

### (root)

Fields in the root JSON object.

| Key         | Type     | Value                                                                                     |
|-------------|----------|-------------------------------------------------------------------------------------------|
| `bot_token` | `string` | Your [Discord bot's](https://discord.com/developers/docs/topics/oauth2#bots) access token |

### bot

Fields which describe the bot itself. See also
the [discord.py bot documentation](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot)
for more info on how these fields are used.

| Key              | Type      | Value                                          |
|------------------|-----------|------------------------------------------------|
| `command_prefix` | `string?` | What users type to run a command               |
| `description`    | `string?` | Description of the bot (used in help messages) |

### bot.modules.bios

Fields which describe how the Bios module runs. This module handles users
getting/setting/deleting personal info within Sandpiper which may be used
by other modules.

| Key                            | Type    | Value                                                                                                                                                                                                                                  |
|--------------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `allow_public_setting`         | `bool?` | Whether commands like `name set` are allowed outside DMs. This is `false` by default to force users to DM Sandpiper for their privacy, but it may be easier to troubleshoot with them if they're allowed to enter commands in servers. |

### bot.modules.birthdays

Fields which describe how the Birthdays module runs. This module handles sending
messages to servers when it's a user's birthday.

A message template is randomly selected, formatted, and sent for each birthday.
If the user allows their age to be visible, the template will be picked from
`message_templates_with_age`, otherwise from `message_templates_no_age`.

See [Birthday message template formatting](#birthday-message-template-formatting) for more details
on how to format the message template fields.

| Key                            | Type         | Value                                                                                                             |
|--------------------------------|--------------|-------------------------------------------------------------------------------------------------------------------|
| `past_birthdays_day_range`     | `int?`       | How many days behind to show past birthdays in the `birthdays upcoming` command (between 0 and 365, inclusive)    |
| `upcoming_birthdays_day_range` | `int?`       | How many days ahead to show upcoming birthdays in the `birthdays upcoming` command (between 0 and 365, inclusive) |
| `message_templates_no_age`     | `list[str]?` | A list of birthday message templates ***without*** the user's age announced                                       |
| `message_templates_with_age`   | `list[str]?` | A list of birthday message templates ***with*** the user's age announced                                          |

### logging

Fields which describe how logging is performed. Sandpiper uses rotating logging
to write log files which rotate in specified intervals. See also the
[TimedRotatingFileHandler documentation](https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler)
for more info on how these fields are used.

| Key                       | Type       | Value                                                                                                                                         |
|---------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `sandpiper_logging_level` | `string?`  | Sandpiper's most verbose logging level. Must be one of ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').                                     |
| `discord_logging_level`   | `string?`  | discord.py's most verbose logging level. Must be one of ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').                                    |
| `output_file`             | `string?`  | Absolute or relative (to sandpiper module) filepath to output logs to (including filename)                                                    |
| `when`                    | `integer?` | Type of time interval for rotating log files. Must be one of ('S', 'M', 'H', 'D', 'midnight')                                                 |
| `interval`                | `integer?` | Number of specified time intervals that must elapse before rotating to a new log file                                                         |
| `backup_count`            | `integer?` | Number of backup log files to retain (deletes oldest after limit is reached)                                                                  |
| `format`                  | `string?`  | Format string used when writing log messages ([format string reference](https://docs.python.org/3/library/logging.html#logrecord-attributes)) |

## Birthday message template formatting

Several formatting fields are allowed within birthday message templates. If the
birthday-haver has stored personal info in Sandpiper and set it to public, she
will use it to personalize the message.

- `name`
- `age`
- `age_suffixed` (20th, 21st, 22nd, etc.)
- `ping` (a Discord user ping, like "@Sandpiper")
- `they`
- `them`
- `their`
- `theirs`
- `themself`
- `theyre`
- `are`

All fields except age and ping may also be written with either the first or all
letters capitalized to format the fields the same way.

Examples:

- `"{ping}! It's your birthday!"`
    - @Sandpiper! It's your birthday!
- `"IT'S {NAME}'S {AGE_SUFFIXED} BIRTHDAY!"`
    - IT'S SANDPIPER'S 1ST BIRTHDAY!
- `"Hey! It's {name}'s birthday! {They} {are} {age} years old today!"`
    - Hey! It's Sandpiper's birthday! She is 1 years old today!
