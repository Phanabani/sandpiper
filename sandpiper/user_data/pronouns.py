from __future__ import annotations
from dataclasses import astuple, dataclass
import re

__all__ = ["Pronouns", "common_pronouns"]

_slashed_group_pattern = re.compile(r"[a-zA-Z]+(?: *[/\\] *[a-zA-Z]+)*")


@dataclass
class Pronouns:

    subjective: str = "they"
    objective: str = None
    determiner: str = None
    possessive: str = None
    reflexive: str = None

    def __post_init__(self):
        if self.objective is None:
            if self.subjective == "they":
                self.objective = "them"
            else:
                self.objective = self.subjective

        if self.determiner is None:
            if self.subjective == "they":
                self.determiner = "their"
            else:
                self.determiner = f"{self.subjective}s"

        if self.possessive is None:
            if self.subjective == "they":
                self.possessive = "theirs"
            else:
                self.possessive = f"{self.subjective}s"

        if self.reflexive is None:
            if self.subjective == "they":
                self.reflexive = "themself"
            else:
                self.reflexive = f"{self.subjective}self"

    def __contains__(self, pronoun: str):
        return (
            pronoun == self.subjective
            or pronoun == self.objective
            or pronoun == self.determiner
            or pronoun == self.possessive
            or pronoun == self.reflexive
        )

    def __str__(self):
        return "/".join(self.to_tuple())

    @property
    def to_be_conjugation(self):
        # Conjugation following Elverson (ey/em) pronouns can be either is or are
        if self.subjective == "they":
            return "are"
        return "is"

    @property
    def subjective_to_be_contraction(self):
        if self.subjective == "they":
            return "they're"
        return f"{self.subjective}'s"

    def to_tuple(self):
        return astuple(self)

    @classmethod
    def parse(cls, string: str) -> list[Pronouns]:
        """
        Parse a pronoun descriptor string. Tries to be fairly lenient to
        accommodate a wide variety of how people share their pronouns.
        For example:
            He
            She/her
            They/he
            Xe/xem/xyr/xyrs/xemself
        """
        if string == "":
            return [Pronouns()]

        out = []
        tuples = []
        for slashed_group in _slashed_group_pattern.finditer(string):
            # Iterate through groups of slashed pronouns ("she/her they/them")
            first = True
            split = iter(re.split(r" *[\\/] *", slashed_group.group()))
            for pronoun in map(lambda x: x.lower(), split):
                pronoun = pronoun
                # Infer set of pronouns from this one
                pronouns = _infer_pronouns(pronoun)

                if pronouns is None:
                    # Unique pronouns
                    if first:
                        # Assume the rest of the pronouns listed in this group
                        # are ordered cases (subjective, objective, ...)
                        pronouns = Pronouns(pronoun, *split)
                    else:
                        # This isn't the first pronoun, so we're just going to
                        # assume they've listed a bunch of their subjective
                        # pronouns (like she/he/they)
                        pronouns = Pronouns(pronoun)

                pronouns_tuple = pronouns.to_tuple()
                if pronouns_tuple not in tuples:
                    out.append(pronouns)
                    tuples.append(pronouns_tuple)

                first = False

        return out


common_pronouns = {
    "they": Pronouns("they", "them", "their", "theirs", "themself"),
    "she": Pronouns("she", "her", "her", "hers", "herself"),
    "he": Pronouns("he", "him", "his", "his", "himself"),
    "it": Pronouns("it", "it", "its", "its", "itself"),
    "one": Pronouns("one", "one", "one's", "one's", "oneself"),
    "thon": Pronouns("thon", "thon", "thons", "thon's", "thonself"),
    "ae": Pronouns("ae", "aer", "aer", "aers", "aerself"),
    "co": Pronouns("co", "co", "cos", "co's", "coself"),
    "ve": Pronouns("ve", "ver", "vis", "vers", "verself"),
    "vi": Pronouns("vi", "vir", "vis", "virs", "virself"),
    "xe": Pronouns("xe", "xem", "xyr", "xyrs", "xemself"),
    "per": Pronouns("per", "per", "per", "pers", "perself"),  # person
    "ey": Pronouns("ey", "em", "eir", "eirs", "emself"),  # Elverson
    "hu": Pronouns("hu", "hum", "hus", "hus", "huself"),  # humanist
    # Conflicts with e below, so it's disambiguated
    "e_spivak": Pronouns("e", "em", "eir", "eirs", "emself"),  # Spivak
    "ze": Pronouns("ze", "zir", "zir", "zirs", "zirself"),
    "fae": Pronouns("fae", "faer", "faer", "faers", "faerself"),
    "e": Pronouns("e", "em", "es", "ems", "emself"),
}


def _infer_pronouns(pronoun: str):
    """
    Return the first pronoun class (defined above) in which this pronoun first
    appears, or None if it is not found.
    """
    for pronouns in common_pronouns.values():
        if pronoun in pronouns:
            return pronouns
    return None
