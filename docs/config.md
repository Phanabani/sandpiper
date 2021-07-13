# Config

Sandpiper can be configured with a JSON file at `sandpiper/config.json`.
[sandpiper/config_example.json](../sandpiper/config_example.json) contains
default values and can be used as a template. `bot_token` is the only required
field.

## Config Fields

### (root)

Fields in the root JSON object.

Key | Value
--- | -----
`bot_token` *(string)* | Your [Discord bot's](https://discord.com/developers/docs/topics/oauth2#bots) access token

### bot

Fields which describe the bot itself. See also
the [discord.py bot documentation](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot)
for more info on how these fields are used.

Key | Value
--- | -----
`command_prefix` *(string)* | What users type to run a command
`description` *(string)* | Description of the bot (used in help messages)

### bot.modules.bios

Fields which describe how the Bios submodule runs.

Key | Value
--- | -----
`allow_public_setting` *(bool)* | Whether commands like `name set` are allowed outside DMs. This is `false` by default to force users to DM Sandpiper for their privacy, but it may be easier to troubleshoot with them if they're allowed to enter commands in servers.

### logging

Fields which describe how logging is performed. Sandpiper
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
