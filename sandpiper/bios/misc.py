from dataclasses import dataclass
from typing import List, Optional, Tuple

from fuzzywuzzy import fuzz, process as fuzzy_process
import pytz

__all__ = ['TimezoneMatches', 'fuzzy_match_timezone']


@dataclass
class TimezoneMatches:
    matches: List[Tuple[str, int]] = None
    best_match: Optional[pytz.BaseTzInfo] = False
    has_multiple_best_matches: bool = False


def fuzzy_match_timezone(tz_str: str, best_match_threshold=75,
                         lower_score_cutoff=50, limit=5) -> TimezoneMatches:
    """
    Fuzzily match a timezone based on given timezone name.

    :param tz_str: timezone name to fuzzily match in pytz's list of timezones
    :param best_match_threshold: Score from 0-100 that the highest scoring
        match must be greater than to qualify as the best match
    :param lower_score_cutoff: Lower score limit from 0-100 to qualify matches
        for storage in ``TimezoneMatches.matches``
    :param limit: Maximum number of matches to store in
        ``TimezoneMatches.matches``
    """

    # ratio (aka token_sort_ratio) provides the best output.
    # partial_ratio finds substrings, which isn't really what users will be
    # searching by, and the _set_ratio methods are totally unusable.
    matches: List[Tuple[str, int]] = fuzzy_process.extractBests(
        tz_str, pytz.all_timezones, scorer=fuzz.ratio,
        score_cutoff=lower_score_cutoff, limit=limit)
    tz_matches = TimezoneMatches(matches)

    if matches and matches[0][1] >= best_match_threshold:
        # Best match
        tz_matches.best_match = pytz.timezone(matches[0][0])
        if len(matches) > 1 and matches[1][1] == matches[0][1]:
            # There are multiple best matches
            # I think given our inputs and scoring algorithm, this shouldn't
            # ever happen, but I'm leaving it just in case
            tz_matches.has_multiple_best_matches = True
    return tz_matches
