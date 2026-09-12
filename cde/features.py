"""Student-facing feature catalog and entitlement semantics (DB-free).

Every gated student feature is declared here once. `status` says what enabling
it actually shows: "available" means a real implementation reads the student's
own data; "preview" means only a clearly-labelled fictional sample exists and
the enabled route returns an honest insufficient-evidence state.

Gated routes answer 404, never 403 — a disabled feature is invisible, not
forbidden, so nothing reveals what exists behind a gate.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

ENTITLEMENTS_DOC_ID = "institute"

# Student-facing copy must describe the work, never the student, and must never
# read as a sales pitch. Word boundaries keep taxonomy keys like careless_slip
# (underscore is a word character) from tripping the guard.
DENYLIST = re.compile(
    r"\b(careless|unmotivated|lazy|weak student|poor grasp|anxious|stressed|"
    r"struggling emotionally|panic|streaks?|badges?|points|trophy|trophies|"
    r"days[ _]?active|upgrade|premium|prices?|pricing|leaderboard|percentiles?)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Feature:
    key: str
    title: str
    description: str
    tier: Literal[2, 3]
    status: Literal["available", "preview"]


CATALOG: tuple = (
    Feature("cognitive.diagnosis", "Rough-work diagnosis",
            "Attach a photo of your rough work and see, for each question you did not get "
            "right, what the working shows — with a confidence level and whether a teacher "
            "has reviewed it.", 2, "available"),
    Feature("cognitive.growth", "Growth against your own previous best",
            "Each new result compared with your own earlier best, by subject. Never a "
            "comparison with other students.", 2, "available"),
    Feature("cognitive.heatmap", "Subject map",
            "A grid of your published exams by subject, showing how many questions were "
            "correct, not correct yet, or left blank in each.", 2, "available"),
    Feature("cognitive.patterns", "Working patterns",
            "Shows where your working most often stops or slips across exams, with a "
            "confidence level and whether a teacher has reviewed it.", 2, "preview"),
    Feature("cognitive.calibration", "Confidence mirror",
            "Rate how sure you are before you submit, then see how that matched what was "
            "correct. A mirror, not a grade.", 2, "preview"),
    Feature("cognitive.exam_history", "Exam history and time per question",
            "Every published exam in one place, with time spent per question when your "
            "institute records it.", 2, "preview"),
    Feature("learning.spaced_review", "Spaced review",
            "Short review cards built from the questions you got wrong, scheduled so the "
            "concept comes back just before you would forget it.", 3, "preview"),
    Feature("learning.planner", "Study plan",
            "A weekly plan that re-plans when a day is missed instead of piling up, and "
            "lightens the load before an exam.", 3, "preview"),
    Feature("learning.micro_wins", "Small wins",
            "Specific things you did that were hard — noted once, for you only, then gone "
            "when you acknowledge them.", 3, "preview"),
    Feature("learning.trajectory", "Trajectory insight",
            "What students whose working looked like yours went on to recover, with the "
            "evidence and the confidence behind it.", 3, "preview"),
)

FEATURE_KEYS: frozenset = frozenset(f.key for f in CATALOG)
_BY_KEY: Dict[str, Feature] = {f.key: f for f in CATALOG}


def get_feature(key: str) -> Feature:
    return _BY_KEY[key]


def effective_enabled(doc: Optional[dict]) -> Dict[str, bool]:
    """Every catalog key, defaulting to False; stored keys not in the catalog are ignored."""
    stored = (doc or {}).get("enabled") or {}
    return {k: bool(stored.get(k, False)) for k in FEATURE_KEYS}


def validate_toggles(payload: dict) -> Dict[str, bool]:
    unknown = sorted(k for k in payload if k not in FEATURE_KEYS)
    if unknown:
        raise ValueError(f"Unknown feature keys: {', '.join(unknown)}")
    bad = sorted(k for k, v in payload.items() if not isinstance(v, bool))
    if bad:
        raise ValueError(f"Feature toggles must be true or false: {', '.join(bad)}")
    return dict(payload)


def catalog_view(enabled: Dict[str, bool]) -> List[dict]:
    return [{"key": f.key, "title": f.title, "description": f.description,
             "tier": f.tier, "status": f.status, "enabled": bool(enabled.get(f.key, False))}
            for f in CATALOG]
