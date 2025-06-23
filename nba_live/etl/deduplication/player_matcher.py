"""Player deduplication utility.

This module provides fuzzy matching across multiple data sources to
identify identical players that may appear under slightly different
names, nicknames, or spelling variations.

Example:
    matcher = PlayerMatcher()
    result = matcher.match_players(record_a, record_b)
    if result.match:
        # treat as same player
"""

from dataclasses import dataclass
from typing import Dict, Any, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    PlayerDict = Dict[str, Any]

try:
    from rapidfuzz import fuzz  # type: ignore
except ImportError:  # pragma: no cover
    fuzz = None  # will warn at runtime


@dataclass
class MatchResult:
    confidence: float
    match: bool
    reasoning: str


class PlayerMatcher:  # noqa: D101
    NICKNAME_MAP = {
        "Magic": "Earvin",
        "Dr. J": "Julius",
        "Pistol Pete": "Pete",
        "The Big O": "Oscar",
    }

    def __init__(self) -> None:
        if fuzz is None:
            warnings.warn(
                "rapidfuzz not installed; using naive name compare.",
                RuntimeWarning,
                stacklevel=2,
            )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def match_players(
        self, player1: "PlayerDict", player2: "PlayerDict"
    ) -> MatchResult:  # noqa: D401
        """Return likelihood that two player records refer to same person."""
        name_score = self._calculate_name_similarity(player1, player2)
        context_score = self._validate_context(player1, player2)
        stats_score = self._compare_stat_signatures(player1, player2)

        final_score = (
            (name_score * 0.4) + (context_score * 0.4) + (stats_score * 0.2)
        )
        
        reason = (
            f"name={name_score:.2f}, ctx={context_score:.2f}, "
            f"stat={stats_score:.2f}"
        )
        return MatchResult(
            confidence=final_score,
            match=final_score > 0.85,
            reasoning=reason,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _calculate_name_similarity(
        self, p1: "PlayerDict", p2: "PlayerDict"
    ) -> float:
        first_name_1 = p1.get("first_name", "")
        first_name_2 = p2.get("first_name", "")
        
        first1 = self.NICKNAME_MAP.get(first_name_1, first_name_1)
        first2 = self.NICKNAME_MAP.get(first_name_2, first_name_2)
        
        full1 = f"{first1} {p1.get('last_name', '')}".strip()
        full2 = f"{first2} {p2.get('last_name', '')}".strip()

        if fuzz:
            return fuzz.token_sort_ratio(full1, full2) / 100.0
        return 1.0 if full1.lower() == full2.lower() else 0.0

    def _validate_context(self, p1: "PlayerDict", p2: "PlayerDict") -> float:
        birth1 = p1.get("birth_year")
        birth2 = p2.get("birth_year")
        if birth1 and birth2 and abs(birth1 - birth2) > 5:
            return 0.0

        s1 = self._parse_season_to_year(p1.get("first_season"))
        e1 = self._parse_season_to_year(p1.get("last_season"))
        s2 = self._parse_season_to_year(p2.get("first_season"))
        e2 = self._parse_season_to_year(p2.get("last_season"))

        p1_has_range = s1 is not None and e1 is not None
        p2_has_range = s2 is not None and e2 is not None

        if p1_has_range and p2_has_range:
            # We've confirmed s1, e1, s2, e2 are not None
            assert s1 is not None and e1 is not None
            assert s2 is not None and e2 is not None
            years1 = set(range(s1, e1 + 1))
            years2 = set(range(s2, e2 + 1))
            if not years1 or not years2:
                return 0.5  # Treat empty sets as neutral
            overlap = len(years1 & years2) / len(years1 | years2)
            return overlap

        if p1_has_range or p2_has_range:
            return 0.0  # Mismatch: one has data, the other doesn't

        return 0.5  # Neutral: neither has data

    def _compare_stat_signatures(
        self, p1: "PlayerDict", p2: "PlayerDict"
    ) -> float:
        seasons1_dict = p1.get("seasons", {})
        seasons2_dict = p2.get("seasons", {})

        if not isinstance(seasons1_dict, dict) or not isinstance(
            seasons2_dict, dict
        ):
            return 0.5  # Neutral if data is malformed

        seasons1 = set(seasons1_dict.keys())
        seasons2 = set(seasons2_dict.keys())
        seasons_common = seasons1 & seasons2
        if not seasons_common:
            return 0.5
        diffs = []
        for season in seasons_common:
            s1 = seasons1_dict[season]
            s2 = seasons2_dict[season]
            if all(k in s1 and k in s2 for k in ("ppg",)):
                delta = abs(s1["ppg"] - s2["ppg"]) / max(s1["ppg"], 1)
                diffs.append(delta)
        return 1.0 - (sum(diffs) / len(diffs)) if diffs else 0.5

    def _parse_season_to_year(self, season: Any) -> int | None:
        """Extract the starting year from a season string (e.g., '1996-97')."""
        if not season or not isinstance(season, str):
            return None
        try:
            return int(season.split("-")[0])
        except (ValueError, IndexError):
            return None 