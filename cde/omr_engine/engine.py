"""
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
VERSION = "1.3.0-cde-self-calibrated"
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
    blank_count: int
    review_count: int
    ambiguous_questions: List[int] = field(default_factory=list)
    limitations: List[str] = field(default_factory=lambda: [
        "Template coordinates are fixed to the supplied BIOME answer-sheet layout",
    ])
    layout_rejections: List[str] = field(default_factory=list)
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
    """Find the gap that marks the boundary nearest `expected`.

    The tolerance window can include the student-info block, which may
    contain a gap even larger than the true header/footer gap. Picking the
    single largest gap in the window (np.argmax) can therefore latch onto
    that block instead of the real boundary, even when that gap also passes
    a "convincing" size check. Across the labeled fixtures, every genuine
    boundary lands within ~0.04*h of the calibrated `expected` position;
    the student-info-block gap that caused the page-1 regression sits at
    ~0.21*h away. MAX_OFFSET_FRAC caps candidates to the genuine range with
    a safety margin, so a convincing-but-distant gap is rejected in favor
    of falling back to `expected`.
    """
    MAX_OFFSET_FRAC = 0.08
    ys = np.sort(ys)
    for tol in (0.15, 0.25, 0.40):
        lo, hi = expected - tol * h, expected + tol * h
        window = ys[(ys >= lo) & (ys <= hi)]
        if len(window) < 6:
            continue
        diffs = np.diff(window)
        median_gap = float(np.median(diffs))
        is_convincing = (diffs >= 0.03 * h) & (
            (median_gap <= 0) | (diffs >= 2.5 * median_gap)
        )
        candidates = np.nonzero(is_convincing)[0]
        if candidates.size == 0:
            continue
        midpoints = (window[candidates] + window[candidates + 1]) / 2.0
        within_range = np.abs(midpoints - expected) <= MAX_OFFSET_FRAC * h
        candidates, midpoints = candidates[within_range], midpoints[within_range]
        if candidates.size == 0:
            continue
        best = candidates[np.argmin(np.abs(midpoints - expected))]
        return float((window[best] + window[best + 1]) / 2.0)
    return expected
def _detect_filled_blobs(gray_u8: np.ndarray, radius: float) -> np.ndarray:
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
    margin_x = 0.052 * w
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
    all_cy_arr = np.asarray(all_cy)
    header_y = _auto_header_cutoff(all_cy_arr, h, _reference_y(0, h))
    footer_y = _auto_header_cutoff(all_cy_arr, h, _reference_y(N_ROWS - 1, h))
    if footer_y <= header_y:
        footer_y = float(h)
    pts = [(cx, cy) for cx, cy in raw if header_y <= cy <= footer_y]
    return np.asarray(pts, dtype=np.float32)
def _kmeans_1d(cv2_mod, values: np.ndarray, k: int, init: np.ndarray):
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
def _fit_evenly_spaced_rows(row_ys: np.ndarray, h: int):
    ys = np.sort(row_ys)
    if len(ys) < 4:
        return None, 0
    b0 = (_reference_y(N_ROWS - 1, h) - _reference_y(0, h)) / (N_ROWS - 1)
    y_min = float(ys[0])
    best = None
    for leading_blanks in (0, 1, 2, 3):
        a, b = y_min - leading_blanks * b0, b0
        for _ in range(25):
            row_idx = np.clip(np.round((ys - a) / b), 0, N_ROWS - 1).astype(int)
            A = np.stack([np.ones_like(row_idx, dtype=np.float64), row_idx.astype(np.float64)], axis=1)
            sol, *_ = np.linalg.lstsq(A, ys, rcond=None)
            new_a, new_b = float(sol[0]), float(sol[1])
            if abs(new_a - a) < 1e-3 and abs(new_b - b) < 1e-5:
                a, b = new_a, new_b
                break
            a, b = new_a, new_b
        if b <= 0 or not (0.5 * b0 <= b <= 1.5 * b0):
            continue
        row_idx = np.clip(np.round((ys - a) / b), 0, N_ROWS - 1).astype(int)
        residual = float(np.sum((ys - (a + b * row_idx)) ** 2))
        # Add a small penalty to break shift-invariance ties (prefer the fit closest to the reference)
        penalty = 0.05 * abs(a - _reference_y(0, h))
        score = residual + penalty
        if best is None or score < best[0] - 1e-6:
            best = (score, residual, a, b, row_idx)
    if best is None:
        return None, 0
    _, _, a, b, row_idx = best
    fitted = a + b * np.arange(N_ROWS)
    counts = np.bincount(row_idx, minlength=N_ROWS)
    sums = np.bincount(row_idx, weights=ys, minlength=N_ROWS)
    has_evidence = counts >= 1
    fitted[has_evidence] = sums[has_evidence] / counts[has_evidence]
    return fitted, int(has_evidence.sum())
def _fit_evenly_spaced_options(col_xs: np.ndarray, w: int):
    xs = np.sort(col_xs)
    if len(xs) < 2:
        return None, 0
    b0 = (OPTION_OFFSETS[-1] - OPTION_OFFSETS[0]) / (len(OPTION_OFFSETS) - 1) * (w / W_REF)
    x_min = float(xs[0])
    best = None
    for leading_blanks in (0, 1, 2, 3):
        a, b = x_min - leading_blanks * b0, b0
        for _ in range(25):
            opt_idx = np.clip(np.round((xs - a) / b), 0, 3).astype(int)
            A = np.stack([np.ones_like(opt_idx, dtype=np.float64), opt_idx.astype(np.float64)], axis=1)
            sol, *_ = np.linalg.lstsq(A, xs, rcond=None)
            new_a, new_b = float(sol[0]), float(sol[1])
            if abs(new_a - a) < 1e-3 and abs(new_b - b) < 1e-5:
                a, b = new_a, new_b
                break
            a, b = new_a, new_b
        if b <= 0 or not (0.5 * b0 <= b <= 1.5 * b0):
            continue
        opt_idx = np.clip(np.round((xs - a) / b), 0, 3).astype(int)
        residual = float(np.sum((xs - (a + b * opt_idx)) ** 2))
        if best is None or residual < best[0] - 1e-6:
            best = (residual, a, b, opt_idx)
    if best is None:
        return None, 0
    _, a, b, opt_idx = best
    fitted = a + b * np.arange(4)
    counts = np.bincount(opt_idx, minlength=4)
    sums = np.bincount(opt_idx, weights=xs, minlength=4)
    has_evidence = counts >= 1
    fitted[has_evidence] = sums[has_evidence] / counts[has_evidence]
    return fitted, int(has_evidence.sum())
def _fit_skewed_options(sel: np.ndarray, fitted_y, row_centers_ref: np.ndarray, w: int):
    baseline, n_opts_fit = _fit_evenly_spaced_options(sel[:, 0], w)
    if baseline is None:
        return None, 0
    if fitted_y is not None:
        row_centers = fitted_y
    else:
        row_centers = row_centers_ref
    xs, ys = sel[:, 0], sel[:, 1]
    opt_idx = np.argmin(np.abs(xs[:, None] - baseline[None, :]), axis=1)
    row_idx = np.argmin(np.abs(ys[:, None] - row_centers[None, :]), axis=1)
    row_center = (N_ROWS - 1) / 2.0
    b0 = (OPTION_OFFSETS[-1] - OPTION_OFFSETS[0]) / (len(OPTION_OFFSETS) - 1) * (w / W_REF)
    c_max = (1.2 * b0) / row_center
    c = 0.0
    fitted_grid = np.tile(baseline, (N_ROWS, 1)).astype(np.float64)
    for _ in range(3):
        residual = xs - baseline[opt_idx]
        dr = (row_idx - row_center).astype(np.float64)
        denom = float(np.sum(dr * dr))
        if denom > 1e-6:
            c_new = float(np.sum(dr * residual) / denom)
            c = float(np.clip(c_new, -c_max, c_max))
        fitted_grid = baseline[None, :] + c * (np.arange(N_ROWS)[:, None] - row_center)
        predicted = baseline[None, :] + c * (row_idx[:, None] - row_center)
        opt_idx = np.argmin(np.abs(xs[:, None] - predicted), axis=1)
    return fitted_grid, n_opts_fit
def _calibrate_grid(gray_u8: np.ndarray, radius: float):
    h, w = gray_u8.shape
    base_x = np.array([[_reference_x(p, o, w) for o in range(4)] for p in range(N_PANELS)])
    calibrated_x = np.repeat(base_x[:, None, :], N_ROWS, axis=1)
    calibrated_y = np.array([[_reference_y(r, h) for r in range(N_ROWS)] for _ in range(N_PANELS)])
    ref_row_y = np.array([_reference_y(r, h) for r in range(N_ROWS)])
    evidence = {"panels_calibrated": 0, "rows_calibrated": 0, "options_calibrated": 0, "points": 0}
    try:
        import cv2
    except ImportError:
        return calibrated_x, calibrated_y, evidence
    pts = _detect_filled_blobs(gray_u8, radius)
    evidence["points"] = len(pts)
    if len(pts) < N_PANELS * 3:
        return calibrated_x, calibrated_y, evidence
    ref_panel_x = np.array([_reference_x(p, 1, w) for p in range(N_PANELS)])
    panel_labels, panel_centers = _kmeans_1d(cv2, pts[:, 0], N_PANELS, ref_panel_x)
    panel_order = np.argsort(panel_centers)
    rows_calibrated_total = 0
    for panel_idx, old_panel in enumerate(panel_order):
        sel = pts[panel_labels == old_panel]
        if len(sel) < 8:
            continue
        fitted_y = None
        if len(sel) >= N_ROWS // 3:
            fitted_y, n_rows_fit = _fit_evenly_spaced_rows(sel[:, 1], h)
            if fitted_y is not None:
                calibrated_y[panel_idx] = fitted_y
                rows_calibrated_total += n_rows_fit
        fitted_x_grid, n_opts_fit = _fit_skewed_options(sel, fitted_y, ref_row_y, w)
        if fitted_x_grid is not None:
            calibrated_x[panel_idx] = fitted_x_grid
            evidence["options_calibrated"] += n_opts_fit
        evidence["panels_calibrated"] += 1
    evidence["rows_calibrated"] = rows_calibrated_total // max(1, evidence["panels_calibrated"] or 1)
    return calibrated_x, calibrated_y, evidence
def _build_calibrated_template(w: int, h: int, calibrated_x: np.ndarray, calibrated_y: np.ndarray) -> List[Dict[str, Any]]:
    panels = []
    for panel in range(N_PANELS):
        rows = []
        for r in range(N_ROWS):
            y = float(calibrated_y[panel, r])
            opts = [{"option": o + 1, "x": float(calibrated_x[panel, r, o]), "y": y} for o in range(4)]
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
def validate_layout(image_width: int, image_height: int,
                    calibration_evidence: Dict[str, Any]) -> List[str]:
    """Check the scan really is the answer sheet this engine understands.

    Returns reasons to REJECT. Empty list = acceptable. Non-empty = DO NOT
    GRADE; send to a human.
    """
    reasons: List[str] = []
    if image_height <= 0 or image_width <= 0:
        return ["invalid_image_dimensions"]

    ratio = image_width / image_height
    if not (0.60 <= ratio <= 0.85):            # portrait A4-like
        reasons.append(f"unexpected_aspect_ratio:{ratio:.3f}")
    if calibration_evidence.get("panels_calibrated", 0) < N_PANELS:
        reasons.append("insufficient_panel_evidence")
    if calibration_evidence.get("rows_calibrated", 0) < 30:
        reasons.append("insufficient_row_evidence")
    if calibration_evidence.get("points", 0) < 100:
        reasons.append("too_few_detected_marks")
    return reasons
def _process_sync(image_bytes: bytes, exam_answer_key: Optional[AnswerKey]) -> OMRResult:
    sha256 = hashlib.sha256(image_bytes).hexdigest()
    im = Image.open(io.BytesIO(image_bytes))
    im.load()
    work_w = min(im.width, 1800)
    work_h = round(im.height * work_w / im.width)
    work = im.resize((work_w, work_h), Image.Resampling.LANCZOS)
    a = _gray_array(work)
    radius = work_w / 142.0
    work_gray_u8 = np.asarray(work.convert("L"), dtype=np.uint8)
    calibrated_x, calibrated_y, calibration_evidence = _calibrate_grid(work_gray_u8, radius)
    layout_rejections = validate_layout(im.width, im.height, calibration_evidence)
    native_scale = im.width / work_w
    native_x = calibrated_x * native_scale
    native_y = calibrated_y * native_scale
    work_template = _build_calibrated_template(work_w, work_h, calibrated_x, calibrated_y)
    native_template = _build_calibrated_template(im.width, im.height, native_x, native_y)
    key = _normalize_answer_key(exam_answer_key)
    questions: List[QuestionResult] = []
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
                is_correct = selected_option == correct_option
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
        blank_count=blank_count,
        review_count=review_count, ambiguous_questions=ambiguous_questions,
        limitations=limitations, layout_rejections=layout_rejections,
    )
async def process_omr_sheet(image_bytes: bytes, exam_answer_key: Optional[AnswerKey] = None) -> OMRResult:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _process_sync, image_bytes, exam_answer_key)
