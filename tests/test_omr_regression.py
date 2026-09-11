import asyncio, glob, io, os, re
import pytest
from PIL import Image
from cde.omr_engine import process_omr_sheet

PAGES_DIR = os.environ.get("CDE_TEST_PAGES", "tests/fixtures/pages")
MAX_FLAGGED = 15


def _pages():
    files = glob.glob(os.path.join(PAGES_DIR, "page_*.png"))
    return sorted(files, key=lambda p: int(re.search(r"page_(\d+)", p).group(1)))


pages_available = pytest.mark.skipif(
    not _pages(), reason=f"No labeled pages in {PAGES_DIR}; set CDE_TEST_PAGES")


@pages_available
def test_no_page_flags_excessively():
    """Page 1 must not regress AND page 4 must stay fixed — both at once."""
    bad = []
    for path in _pages():
        with open(path, "rb") as f:
            r = asyncio.run(process_omr_sheet(f.read()))
        if r.review_count > MAX_FLAGGED:
            bad.append(f"{os.path.basename(path)}={r.review_count}")
    assert not bad, "Too many flagged: " + ", ".join(bad)


def test_omr_result_has_no_score():
    from cde.omr_engine import OMRResult
    f = OMRResult.__dataclass_fields__
    assert "score" not in f and "max_score" not in f
    assert "layout_rejections" in f


def test_wrong_shaped_image_is_rejected():
    img = Image.new("RGB", (1600, 400), "white")     # landscape, blank
    buf = io.BytesIO(); img.save(buf, format="PNG")
    r = asyncio.run(process_omr_sheet(buf.getvalue()))
    assert r.layout_rejections, "A blank landscape image was accepted for grading"


@pages_available
def test_real_sheets_are_accepted():
    """The guard must not be over-strict."""
    for path in _pages():
        with open(path, "rb") as f:
            r = asyncio.run(process_omr_sheet(f.read()))
        assert not r.layout_rejections, f"{os.path.basename(path)}: {r.layout_rejections}"


def test_app_still_imports():
    import cde.api  # noqa: F401
