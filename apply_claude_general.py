import sys

content = '''"""
Callable OMR service module. Ported from the standalone research script
iome_omr.py (Adaptive Matrix-Crop OpenCV/PIL pipeline for the fixed
180-question, 5-panel BIOME answer sheet layout).
The original script was a CLI tool that read/wrote files on disk. This
module keeps the same geometry, scoring, and decision-routing logic but
exposes it as a single async-safe function that operates on in-memory
image bytes and returns a structured result - no disk I/O, no CLI.
Geometry and thresholds are unchanged from the original script; they are
still provisional (not adjudicated against certified ground truth) and
are called out as such in OMRResult.limitations.
"""
from __future__ import annotations
import asyncio
import hashlib
import io
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
import numpy as np
from PIL import Image
VERSION = "1.1.0-cde-self-calibrated"
W_REF, H_REF = 992.0, 1347.0
PANEL_LEFTS = [70, 237, 405, 578, 756]
PANEL_WIDTH = 165
OPTION_OFFSETS = [49, 83, 117, 151]
ROW_Y0, ROW_Y1 = 638, 1217
N_ROWS = 36
N_PANELS = 5
TOTAL_QUESTIONS = N_PANELS * N_ROWS
OPTION_LETTERS = "ABCD"
AnswerKey = Mapping[Union[int, str], str]
@dataclass
class QuestionResult:
    question_number: int
    panel: int
    row: int
    state: str
    reason: str
    selected_option: Optional[str]
    confidence: float
    scores: List[float]
    needs_review: bool
    crop_box: Tuple[int, int, int, int]
    correct_option: Optional[str] = None
    is_correct: Optional[bool] = None
@dataclass
class OMRResult:
    schema: str
    version: str
    sha256: str
    image_width: int
    image_height: int
    questions: List[QuestionResult]
    score: int
    max_score: int
    blank_count: int
    review_count: int
    ambiguous_questions: List[int] = field(default_factory=list)
    limitations: List[str] = field(default_factory=lambda: [
        "Template coordinates are fixed to the supplied BIOME answer-sheet layout",
    ])
def _build_template(w: int, h: int) -> List[Dict[str, Any]]:
    sx, sy = w / W_REF, h / H_REF
    panels = []
    for panel in range(N_PANELS):
        rows = []
        for r in range(N_ROWS):
            y = (ROW_Y0 + (ROW_Y1 - ROW_Y0) * r / (N_ROWS - 1)) * sy
            opts = []
            for o, off in enumerate(OPTION_OFFSETS, 1):
                x = (PANEL_LEFTS[panel] + off) * sx
                opts.append({"option": o, "x": x, "y": y})
            rows.append({"question": panel * N_ROWS + r + 1, "row": r + 1, "y": y, "options": opts})
        panels.append({
            "panel": panel + 1,
            "bbox": ((PANEL_LEFTS[panel]) * sx, ROW_Y0 * sy, (PANEL_LEFTS[panel] + PANEL_WIDTH) * sx, ROW_Y1 * sy),
            "rows": rows,
        })
    return panels
# ---------------------------------------------------------------------------
# Self-calibration.
#
# _build_template() above assumes the incoming scan is framed *exactly* like
# the 992x1347 reference image: same crop, same aspect, no skew. Real scans
# rarely are (trimmed margins, slight rotation, a different scanner DPI on
# height vs width), and that mismatch alone was pushing ~half of every sheet
# into the human-review queue. Rather than trust a single linear scale
# factor, we locate the actual grid on THIS scan using the marks the student
# already made: a filled bubble sits, by definition, exactly on the true
# grid. We isolate those marks, cluster them into 5 panel-columns x 4
# option-columns x 36 rows, and only fall back to the naive reference
# position for any individual row/column that didn't get enough evidence
# (e.g. a column nobody happened to mark).
# ---------------------------------------------------------------------------
def _reference_x(panel: int, option_idx: int, w: int) -> float:
    return (PANEL_LEFTS[panel] + OPTION_OFFSETS[option_idx]) * (w / W_REF)
def _reference_y(row: int, h: int) -> float:
    return (ROW_Y0 + (ROW_Y1 - ROW_Y0) * row / (N_ROWS - 1)) * (h / H_REF)
def _auto_header_cutoff(ys: np.ndarray, h: int, expected: float) -> float:
    """Find the natural gap between the student-info block (name/BID/mobile
    bubble grids -- these also produce filled circular blobs) and the answer
    grid, instead of trusting a fixed fraction of page height.
    We anchor the search around expected (the naive reference-scaled
    position of row 0) rather than scanning the whole upper half of the
    page: the identity grid itself often contains smaller internal gaps
    (e.g. between the name-letters block and the BID/mobile blocks), and on
    some scans one of those is larger than the true header/grid boundary.
    Searching close to the expected boundary avoids latching onto the
    wrong one, while still tolerating real per-scan vertical drift.
    """
    ys = np.sort(ys)
    for tol in (0.15, 0.25, 0.40):
        lo, hi = expected - tol * h, expected + tol * h
        window = ys[(ys >= lo) & (ys <= hi)]
        if len(window) < 2:
            continue
        diffs = np.diff(window)
        i = int(np.argmax(diffs))
        if diffs[i] >= 0.03 * h:
            return float((window[i] + window[i + 1]) / 2.0)
    return expected # no convincing gap anywhere reasonable; trust the reference
def _detect_filled_blobs(gray_u8: np.ndarray, radius: float) -> np.ndarray:
    """Isolate roughly-circular, fully-filled ink blobs of about bubble size.
    A morphological opening with a disk the size of a bubble erases thin
    strokes (printed digits, rule lines, the timing-track ladder) while
    leaving filled bubbles intact, since only they are solid over an area
    that large."""
    h, w = gray_u8.shape
    try:
        import cv2
    except ImportError:
        return np.empty((0, 2), dtype=np.float32)
    _, ink = cv2.threshold(gray_u8, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    k = max(3, int(round(radius * 0.8)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    opened = cv2.morphologyEx(ink, cv2.MORPH_OPEN, kernel)
    n, _, stats, centroids = cv2.connectedComponentsWithStats(opened, connectivity=8)
    min_area = (radius * 0.7) ** 2 * math.pi * 0.5
    max_area = (radius * 1.6) ** 2 * math.pi
    margin_x = 0.052 * w # exclude the left/right timing-track ladders
    raw, all_cy = [], []
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        if not (min_area <= area <= max_area) or ww == 0 or hh == 0:
            continue
        if not (0.6 <= ww / hh <= 1.6):
            continue
        if area / (ww * hh) < 0.55:
            continue
        cx, cy = centroids[i]
        if cx < margin_x or cx > w - margin_x:
            continue
        raw.append((cx, cy))
        all_cy.append(cy)
    if not raw:
        return np.empty((0, 2), dtype=np.float32)
    header_y = _auto_header_cutoff(np.asarray(all_cy), h, _reference_y(0, h))
    pts = [(cx, cy) for cx, cy in raw if cy >= header_y]
    return np.asarray(pts, dtype=np.float32)
def _kmeans_1d(cv2_mod, values: np.ndarray, k: int, init: np.ndarray):
    """1-D clustering seeded at the naive reference positions, so clusters
    stay anchored to the right panel/row/option even when evidence is
    sparse or unevenly distributed."""
    centers = init.astype(np.float64).copy()
    labels = np.zeros(len(values), dtype=np.int64)
    for _ in range(25):
        d = np.abs(values[:, None] - centers[None, :])
        labels = np.argmin(d, axis=1)
        new_centers = centers.copy()
        for i in range(k):
            sel = values[labels == i]
            if len(sel):
                new_centers[i] = sel.mean()
        if np.allclose(new_centers, centers):
            centers = new_centers
            break
        centers = new_centers
    return labels, centers
def _calibrate_grid(gray_u8: np.ndarray, radius: float):
    """Returns (x[panel][option], y[row], evidence) in gray_u8's own pixel
    coordinates. Cells without enough real evidence keep the naive
    reference-scaled position, so this always degrades gracefully."""
    h, w = gray_u8.shape
    calibrated_x = np.array([[_reference_x(p, o, w) for o in range(4)] for p in range(N_PANELS)])
    calibrated_y = np.array([_reference_y(r, h) for r in range(N_ROWS)])
    evidence = {"panels_calibrated": 0, "rows_calibrated": 0, "options_calibrated": 0, "points": 0}
    try:
        import cv2
    except ImportError:
        return calibrated_x, calibrated_y, evidence
    pts = _detect_filled_blobs(gray_u8, radius)
    evidence["points"] = len(pts)
    if len(pts) < N_PANELS * 3:
        return calibrated_x, calibrated_y, evidence # not enough evidence, stay with the naive template
    ref_panel_x = np.array([_reference_x(p, 1, w) for p in range(N_PANELS)])
    panel_labels, panel_centers = _kmeans_1d(cv2, pts[:, 0], N_PANELS, ref_panel_x)
    panel_order = np.argsort(panel_centers) # old cluster index -> panel index 0..4, left to right
    for panel_idx, old_panel in enumerate(panel_order):
        sel = pts[panel_labels == old_panel]
        if len(sel) < 8:
            continue
        ref_opts = np.array([_reference_x(panel_idx, o, w) for o in range(4)])
        opt_labels, opt_centers = _kmeans_1d(cv2, sel[:, 0], 4, ref_opts)
        opt_order = np.argsort(opt_centers)
        for new_o, old_o in enumerate(opt_order):
            if (opt_labels == old_o).sum() >= 2:
                calibrated_x[panel_idx, new_o] = opt_centers[old_o]
                evidence["options_calibrated"] += 1
        evidence["panels_calibrated"] += 1
    if len(pts) >= N_ROWS * 2:
        ref_row_y = np.array([_reference_y(r, h) for r in range(N_ROWS)])
        row_labels, row_centers = _kmeans_1d(cv2, pts[:, 1], N_ROWS, ref_row_y)
        row_order = np.argsort(row_centers)
        for new_r, old_r in enumerate(row_order):
            if (row_labels == old_r).sum() >= 2:
                calibrated_y[new_r] = row_centers[old_r]
                evidence["rows_calibrated"] += 1
    return calibrated_x, calibrated_y, evidence
def _build_calibrated_template(w: int, h: int, calibrated_x: np.ndarray, calibrated_y: np.ndarray) -> List[Dict[str, Any]]:
    panels = []
    for panel in range(N_PANELS):
        rows = []
        for r in range(N_ROWS):
            y = float(calibrated_y[r])
            opts = [{"option": o + 1, "x": float(calibrated_x[panel, o]), "y": y} for o in range(4)]
            rows.append({"question": panel * N_ROWS + r + 1, "row": r + 1, "y": y, "options": opts})
        panels.append({
            "panel": panel + 1,
            "bbox": (
                (PANEL_LEFTS[panel]) * (w / W_REF), ROW_Y0 * (h / H_REF),
                (PANEL_LEFTS[panel] + PANEL_WIDTH) * (w / W_REF), ROW_Y1 * (h / H_REF),
            ),
            "rows": rows,
        })
    return panels
def _gray_array(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("L"), dtype=np.float32) / 255.0
def _disk_score(a: np.ndarray, x: float, y: float, radius: float) -> Tuple[float, float, float]:
    h, w = a.shape
    r = max(3, int(round(radius)))
    cx, cy = int(round(x)), int(round(y))
    x0, x1, y0, y1 = max(0, cx - r), min(w, cx + r + 1), max(0, cy - r), min(h, cy + r + 1)
    crop = a[y0:y1, x0:x1]
    if crop.size == 0: return 0.0, 0.0, 0.0
    yy, xx = np.ogrid[: crop.shape[0], : crop.shape[1]]
    rr = np.sqrt((xx + x0 - x) ** 2 + (yy + y0 - y) ** 2)
    inner = crop[rr <= radius * 0.30]
    ann = crop[(rr >= radius * 0.42) & (rr <= radius * 0.55)]
    if inner.size == 0: return 0.0, 0.0, 0.0
    darkness = float(1.0 - np.mean(inner))
    ring = float(1.0 - np.mean(ann)) if ann.size else 0.0
    corrected = darkness - 0.35 * ring
    return darkness, ring, corrected
def _classify(scores: List[float]) -> Tuple[str, str, float, Optional[int]]:
    order = np.argsort(scores)[::-1]
    best, second = float(scores[order[0]]), float(scores[order[1]])
    if best < 0.18: return "blank", "all_options_below_provisional_floor", best, None
    if best - second < 0.035: return "ambiguous", "top_two_score_margin_too_small", best - second, None
    if sum(s >= max(0.18, best - 0.06) for s in scores) > 1: return "multiple", "multiple_options_above_relative_gate", best, None
    # We maintain our 0.40 patch here to safely route smudges/erasures to HITL
    if best < 0.40: return "review_low_resolution", "weak_candidate", best, None
    return "filled", "single_candidate_passed_provisional_gate", best - second, int(order[0])
def _row_crop_box(panel: Dict[str, Any], row: Dict[str, Any], w: int, h: int) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = panel["bbox"]
    pad_y = (ROW_Y1 - ROW_Y0) / (N_ROWS - 1) / 2.0 * (h / H_REF)
    top = max(0, int(row["y"] - pad_y))
    bottom = min(h, int(row["y"] + pad_y))
    return (int(x0), top, int(x1), bottom)
def _normalize_answer_key(exam_answer_key: Optional[AnswerKey]) -> Dict[int, str]:
    if not exam_answer_key: return {}
    normalized: Dict[int, str] = {}
    for k, v in exam_answer_key.items():
        try:
            normalized[int(k)] = str(v).strip().upper()
        except:
            continue
    return normalized
def _process_sync(image_bytes: bytes, exam_answer_key: Optional[AnswerKey]) -> OMRResult:
    sha256 = hashlib.sha256(image_bytes).hexdigest()
    im = Image.open(io.BytesIO(image_bytes))
    im.load()
    work_w = min(im.width, 1800)
    work_h = round(im.height * work_w / im.width)
    work = im.resize((work_w, work_h), Image.Resampling.LANCZOS)
    a = _gray_array(work)
    radius = work_w / 142.0
    # Calibrate once at working resolution (cheap, and cv2's Otsu/morphology
    # need uint8), then scale the calibrated centers up to native resolution
    # by the same uniform factor used to produce work from im.
    work_gray_u8 = np.asarray(work.convert("L"), dtype=np.uint8)
    calibrated_x, calibrated_y, calibration_evidence = _calibrate_grid(work_gray_u8, radius)
    native_scale = im.width / work_w
    native_x = calibrated_x * native_scale
    native_y = calibrated_y * native_scale
    work_template = _build_calibrated_template(work_w, work_h, calibrated_x, calibrated_y)
    native_template = _build_calibrated_template(im.width, im.height, native_x, native_y)
    key = _normalize_answer_key(exam_answer_key)
    questions: List[QuestionResult] = []
    score = 0
    max_score = 0
    blank_count = 0
    review_count = 0
    ambiguous_questions: List[int] = []
    for panel_idx, panel in enumerate(work_template):
        native_panel = native_template[panel_idx]
        for row_idx, row in enumerate(panel["rows"]):
            native_row = native_panel["rows"][row_idx]
            scores = [_disk_score(a, op["x"], op["y"], radius)[2] for op in row["options"]]
            state, reason, confidence, sel_idx = _classify(scores)
            selected_option = OPTION_LETTERS[sel_idx] if sel_idx is not None else None
            q_num = row["question"]
            needs_review = state in ("ambiguous", "multiple", "review_low_resolution", "blank")
            correct_option = key.get(q_num)
            is_correct: Optional[bool] = None
            if correct_option is not None and not needs_review:
                max_score += 1
                is_correct = selected_option == correct_option
                if is_correct: score += 1
            if state == "blank": blank_count += 1
            if needs_review:
                review_count += 1
                ambiguous_questions.append(q_num)
            questions.append(QuestionResult(
                question_number=q_num, panel=panel["panel"], row=row["row"],
                state=state, reason=reason, selected_option=selected_option,
                confidence=round(float(confidence), 6), scores=[round(float(s), 6) for s in scores],
                needs_review=needs_review, crop_box=_row_crop_box(native_panel, native_row, im.width, im.height),
                correct_option=correct_option, is_correct=is_correct,
            ))
    limitations = ["Template coordinates are fixed to the supplied BIOME answer-sheet layout"]
    if calibration_evidence["panels_calibrated"] < N_PANELS or calibration_evidence["rows_calibrated"] < N_ROWS:
        limitations.append(
            "Grid self-calibration was partial (evidence=%s); some rows/options fell back to the "
            "uncalibrated reference-scaled position" % calibration_evidence
        )
    return OMRResult(
        schema="cde-omr-result/v1", version=VERSION, sha256=sha256,
        image_width=im.width, image_height=im.height, questions=questions,
        score=score, max_score=max_score, blank_count=blank_count,
        review_count=review_count, ambiguous_questions=ambiguous_questions,
        limitations=limitations,
    )
async def process_omr_sheet(image_bytes: bytes, exam_answer_key: Optional[AnswerKey] = None) -> OMRResult:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_sync, image_bytes, exam_answer_key)
'''

with open(r"C:\Users\bit\Downloads\cde_app_ready_fixed\cde_app_ready\cde\omr_engine\engine.py", "w", encoding="utf-8") as f:
    f.write(content)
