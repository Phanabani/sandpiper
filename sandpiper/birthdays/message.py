__all__ = ["age_with_suffix", "format_birthday_message"]

from typing import Optional

from sandpiper.user_data import Pronouns, common_pronouns


base_ordinal_suffix = 'th'
ordinal_suffixes = {
    1: 'st',
    2: 'nd',
    3: 'rd'
}


def capitalize_first(string: str) -> str:
    if not string:
        return ''
    return string[0].upper() + string[1:]


def get_ordinal_suffix(number: int) -> str:
    return ordinal_suffixes.get(number % 10, base_ordinal_suffix)


def age_with_suffix(age: int) -> str:
    return f'{age}{get_ordinal_suffix(age)}'


def format_birthday_message(
        msg: str,
        user_id: int,
        name: str,
        pronouns: Pronouns = common_pronouns['they'],
        age: Optional[int] = None
):
    p = pronouns

    # Generate normal (not explicitly lower), capitalized, and upper versions
    # of these args
    generate_cases = {
        'name': name,
        'they': p.subjective,
        'them': p.objective,
        'their': p.determiner,
        'theirs': p.possessive,
        'themself': p.reflexive,
        'are': p.to_be_conjugation,
        'theyre': p.subjective_to_be_contraction,
        'age_suffixed': age_with_suffix(age) if age is not None else None,
    }
    args_generated_cases = {}
    for k, v in generate_cases.items():
        args_generated_cases[k] = v
        args_generated_cases[capitalize_first(k)] = capitalize_first(v)
        args_generated_cases[k.upper()] = v.upper()

    return msg.format(
        **args_generated_cases,
        ping=f"<@{user_id}>",
        age=age,
    )
