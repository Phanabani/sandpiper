__all__ = ["Bot"]

from phanas_pydantic_helpers import Factory
from pydantic import BaseModel, Field, conint

from sandpiper.config.models._field_types import SnowflakeField

message_templates_no_age = [
    "Hey!! It's {name}'s birthday! Happy birthday {ping}!",
    #
    "{name}! It's your birthday!! Hope it's a great one {ping}!",
    #
    "omg! did yall know it's {name}'s birthday?? happy birthday {ping}! :D",
    #
    "I am pleased to announce... IT'S {NAME}'s BIRTHDAY!! Happy birthday {ping}!!",
]

message_templates_with_age = [
    "Hey!! It's {name}'s birthday! {They} turned {age} today. Happy birthday {ping}!",
    #
    "{name}! It's your birthday!! I can't believe you're already {age} ;u; "
    "Hope it's a great one {ping}!",
    #
    "omg! did yall know it's {name}'s birthday?? {Theyre} {age} now! happy birthday "
    "{ping}! :D",
    #
    "I am pleased to announce... IT'S {NAME}'S BIRTHDAY!! {They} just turned {age}! "
    "Happy birthday {ping}!!",
]


class Bot(BaseModel):
    description: str = (
        "A bot that makes it easier to communicate with friends around the world.\n"
        "Visit my GitHub page for more info about commands and features: "
        "https://github.com/phanabani/sandpiper#commands-and-features"
    )

    class _Commands(BaseModel):
        guilds: list[SnowflakeField] = Factory(
            list,
            description=(
                "Guilds to immediately push new commands to (helpful for debugging)"
            ),
        )

    commands: _Commands = Factory(_Commands)

    class _Components(BaseModel):
        class _Bios(BaseModel):
            allow_public_setting: bool = False

        bios: _Bios = Factory(_Bios)

        class _Birthdays(BaseModel):
            past_birthdays_day_range: conint(ge=0, le=365) = 7
            upcoming_birthdays_day_range: conint(ge=0, le=365) = 14
            message_templates_no_age: list[str] = message_templates_no_age
            message_templates_with_age: list[str] = message_templates_with_age

        birthdays: _Birthdays = Factory(_Birthdays)

    components: _Components = Field(_Components, alias="modules")
