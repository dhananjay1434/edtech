from __future__ import annotations

import math
from typing import Iterable

MODEL = "text-embedding-004"
DIMENSIONS = 768
CLASSES = {
    "Calculation Slip", "Procedural Flaw",
    "Reading Comprehension Error", "Conceptual Deficit",
}

class InsufficientBank(RuntimeError):
    pass

def cosine_distance(a: list[float], b: list[float]) -> float:
    if len(a) != DIMENSIONS or len(b) != DIMENSIONS:
        raise ValueError("Embedding dimension mismatch")
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in a + b):
        raise ValueError("Embedding contains a non-finite or invalid value")
    an = math.sqrt(sum(x * x for x in a))
    bn = math.sqrt(sum(x * x for x in b))
    if an == 0 or bn == 0:
        raise ValueError("Zero-norm embedding")
    similarity = sum(x * y for x, y in zip(a, b)) / (an * bn)
    return 1.0 - max(-1.0, min(1.0, similarity))

def eligible(candidate: dict, original: dict, error_class: str,
             excluded_families: set[str]) -> bool:
    if error_class not in CLASSES:
        raise ValueError("Unsupported error class")
    if not candidate["approved"] or not candidate["active"]:
        return False
    if candidate["family_id"] in excluded_families:
        return False
    if candidate.get("embedding_model") != MODEL or candidate.get("embedding") is None:
        return False
    for field in ("subject", "topic_code", "language"):
        if candidate[field] != original[field]:
            return False
    difficulty = original["difficulty"]
    if error_class == "Calculation Slip":
        return (candidate["target_skill"] == "accuracy"
                and candidate["difficulty"] == difficulty)
    if error_class == "Procedural Flaw":
        procedure = original.get("procedure_code")
        return (procedure is not None
                and candidate["target_skill"] == "procedure"
                and candidate.get("procedure_code") == procedure
                and candidate["difficulty"] <= difficulty)
    if error_class == "Reading Comprehension Error":
        return (candidate["target_skill"] == "reading"
                and candidate["phrasing_variant"] != original["phrasing_variant"]
                and candidate["difficulty"] <= difficulty)
    return (candidate["target_skill"] == "foundation"
            and candidate["concept_code"] == original["concept_code"]
            and candidate["difficulty"] <= max(1, difficulty - 1))

def select_questions(
    original: dict,
    error_class: str,
    query_vector: list[float],
    candidates: Iterable[dict],
    excluded_families: set[str],
    limit: int = 2,
) -> list[tuple[dict, float]]:
    if type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError("Per-gap selection limit must be one or two")
    # Validate query even when the eligible bank is empty.
    cosine_distance(query_vector, query_vector)
    if error_class == "Procedural Flaw" and not original.get("procedure_code"):
        raise InsufficientBank("MISSING_PROCEDURE_CODE")
    excluded = set(excluded_families)
    excluded.add(original["family_id"])
    best_per_family = {}
    for candidate in candidates:
        if not eligible(candidate, original, error_class, excluded):
            continue
        distance = cosine_distance(query_vector, candidate["embedding"])
        ordering = (distance, candidate["family_id"], candidate["_id"])
        previous = best_per_family.get(candidate["family_id"])
        if previous is None or ordering < previous[0]:
            best_per_family[candidate["family_id"]] = (ordering, candidate)
    ranked = sorted(best_per_family.values(), key=lambda entry: entry[0])
    return [(candidate, ordering[0]) for ordering, candidate in ranked[:limit]]
