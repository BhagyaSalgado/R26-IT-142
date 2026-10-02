"""Works out what KIND of trailer this is, and which act a given moment is in.

Why this exists: a 30-second TV spot and a 2.5-minute theatrical trailer are
different formats with different rules. A TV spot has no room for a slow
introduction -- it hooks and goes straight to the climax. Judging a TV spot
against theatrical expectations would flag its compression as a fault when it
is actually correct for the format.

Note on honesty: the cut-off numbers below (35s, 90s) are hand-chosen, and the
act boundaries are the conventional film-industry three/five-act proportions.
These are the kind of thresholds the genre-norm work is progressively
replacing with measured values -- structure_segmentation.py already derives
the acts from each trailer's real energy curve instead of fixed percentages.
This module remains as the fallback when that fails.
"""
from typing import Literal

TrailerType = Literal["tv_spot", "teaser", "theatrical", "unknown"]

def detect_trailer_type(total_duration: float, num_scenes: int) -> TrailerType:
    """Classify the trailer format from its length and number of cuts.

    Length alone is not enough: a 40-second clip with 4 long shots behaves like
    a TV spot, while 40 seconds crammed with 20 cuts behaves like a teaser. The
    shot count disambiguates the borderline cases.
    """
    # Very short, or short with very few cuts -> a TV advert.
    if total_duration <= 35.0 or (num_scenes <= 6 and total_duration <= 45.0):
        return "tv_spot"
    # Under a minute and a half -> a teaser: hook and mood, little plot.
    elif total_duration <= 90.0 or (num_scenes <= 12 and total_duration <= 100.0):
        return "teaser"
    # Anything longer is a full theatrical trailer.
    elif total_duration > 90.0:
        return "theatrical"
    return "theatrical"

def get_act_phase(position_ratio: float, trailer_type: str = "theatrical") -> str:
    """Given how far through the trailer we are (0.0 = start, 1.0 = end),
    name which dramatic act that moment belongs to.

    Shorter formats collapse the middle acts, because there is no time for
    them -- a TV spot jumps almost straight from hook to climax.
    """
    if trailer_type == "tv_spot":
        if position_ratio < 0.20:
            return "opening_hook"
        elif position_ratio < 0.75:
            return "climax"
        return "resolution"

    if trailer_type == "teaser":
        if position_ratio < 0.20:
            return "opening_hook"
        elif position_ratio < 0.50:
            return "introduction"
        elif position_ratio < 0.85:
            return "climax"
        return "resolution"

    # Full theatrical 5-act trailer structure
    if position_ratio < 0.15:
        return "opening_hook"
    elif position_ratio < 0.35:
        return "introduction"
    elif position_ratio < 0.70:
        return "build_up"
    elif position_ratio < 0.90:
        return "climax"
    return "resolution"
