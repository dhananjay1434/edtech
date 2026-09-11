from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

@dataclass(frozen=True)
class Crop:
    id: str
    path: Path
    sha256: str
    question_number: int
    page_index: int
    box: tuple[int, int, int, int]
    mapping_verified: bool

def overlaps(a: tuple[int, int, int, int],
             b: tuple[int, int, int, int]) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])

def validate_crops(
    question_number: int,
    crops: list[Crop],
    page_dimensions: dict[int, tuple[int, int]],
    identity_boxes: dict[int, list[tuple[int, int, int, int]]],
) -> None:
    if len(crops) > 3 or len({c.id for c in crops}) != len(crops):
        raise ValueError("Invalid crop count or duplicate crop ID")
    for crop in crops:
        if not crop.id or crop.question_number != question_number:
            raise ValueError("Wrong crop identity or question")
        if not crop.mapping_verified:
            raise ValueError("Work mapping is not verified")
        if crop.page_index not in page_dimensions or crop.page_index not in identity_boxes:
            raise ValueError("Missing page or identity-region contract")
        width, height = page_dimensions[crop.page_index]
        x0, y0, x1, y1 = crop.box
        if any(type(v) is not int for v in crop.box):
            raise ValueError("Crop coordinates must be integer pixels")
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError("Crop outside aligned page")
        if (x1 - x0) * (y1 - y0) > 2_000_000:
            raise ValueError("Crop pixel limit exceeded")
        if any(overlaps(crop.box, box) for box in identity_boxes[crop.page_index]):
            raise ValueError("Crop overlaps a known identity region")
        data = crop.path.read_bytes()
        if len(data) > 8 * 1024 * 1024:
            raise ValueError("Crop byte limit exceeded")
        if hashlib.sha256(data).hexdigest() != crop.sha256:
            raise ValueError("Crop digest mismatch")
        with Image.open(crop.path) as image:
            if image.format != "PNG" or image.size != (x1 - x0, y1 - y0):
                raise ValueError("Crop encoding or dimensions mismatch")
            image.verify()

def validate_evidence_box(box: list[float]) -> None:
    if len(box) != 4:
        raise ValueError("Evidence box needs four coordinates")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
        raise ValueError("Evidence coordinates must be finite numbers")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError("Evidence box must be ordered and normalized")
