# Changelog

Hi! Here is Sandpiper's version history. Look at her journey! c:


## Table of contents

- [2.0.0 - Thread support](#200---thread-support)
- [1.6.0 - Birthday notifications](#160---birthday-notifications)
- [1.5.0 - Better conversions and test coverage](#150---better-conversions-and-test-coverage)
- [1.4.1](#141)
- [1.4.0 - Better help messages and various improvements](#140---better-help-messages-and-various-improvements)
- [1.3.0 - Async database and unit testing](#130---async-database-and-unit-testing)
- [1.2.2](#122)
- [1.2.1](#121)
- [1.2.0 - Time conversion](#120---time-conversion)
- [1.1.0 - User bios](#110---user-bios)
- [1.0.0 - Unit conversion](#100---unit-conversion)


## 2.0.0 - Thread support

### Feature

- Add support for Discord threads

### Change (internal)
- Upgrade to Python 3.10
- Use Poetry
- Reformat with black
- Migrate to discord.py v2
- Optimize imports in all files

### Fix (internal)

- Fix flaky unit tests for discord.py v2


## 1.6.0 - Birthday notifications

### Feature

- Add birthday notifications
- Add `birthdays upcoming` command


## 1.5.0 - Better conversions and test coverage

### Feature

- Add the ability to specify and input and/or output timezone for time conversions
- Add a ton of new default unit conversion mappings

### Change (internal)

- Massively upgrade the conversions test suite to test many more conversion scenarios and allow for more easily adding tests in the future


## 1.4.1

### Feature

- Add "noon", "now", and "midnight" keywords for time conversion

### Change

- Allow time strings to be written without a colon separating hour and minutes (1430 = 14:30)


## 1.4.0 - Better help messages and various improvements

Help messages are now more meaningful! One shouldn't need to come to the repo
anymore to figure out how to use a command. Various bugfixes and quality of
life changes are also included.

### Feature

- Improve help messages


## 1.3.0 - Async database and unit testing

Switched to an asynchronous API for the database and added unit tests to ensure
functionality remains stable after large changes like this.

### Feature (internal)

- Add unit tests

### Change (internal)

- Use an async database API


## 1.2.2

Fixed an issue where null timezones weren't handled.

### Fix

- Fix null timezones not being handled


## 1.2.1

Fixes an issue where duplicate timezones are printed in time conversion output
if multiple users share the timezone.

### Fix

- Fix duplicate timezones showing in timezone list


## 1.2.0 - Time conversion

Added time conversion. Users can now convert a time to all timezones of users
in a server.

### Feature

- Add time conversion


## 1.1.0 - User bios

Added user bios. Users can store some personal information in Sandpiper so that
others can get to know them better.

### Feature

- Add user bios commands


## 1.0.0 - Unit conversion

Sandpiper's debut! Currently featuring unit conversion between imperial and
metric measurements.

### Feature

- Add unit conversion
