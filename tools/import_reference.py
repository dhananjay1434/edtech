from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = (
    "https://customer-assets-4nw71qhi.emergentagent.net/"
    "job_daab7c77-d9c1-4db4-b0b0-73550965f901/artifacts/"
    "43u04b5g_cognitive_diagnostic_engine_blueprint.md"
)
SOURCE = ROOT / "reference/source.md"
LOCK = ROOT / "reference/source.lock.json"
MANIFEST = ROOT / "reference/copied-blocks.json"
MAX_SOURCE_BYTES = 4 * 1024 * 1024

TARGETS = {
    0: [
        ("5.1", "python", "cde/omr.py"),
        ("5.2", "json", "templates/a4-demo-v1.json"),
    ],
    2: [
        ("8.2", "text", "prompts/diagnose-v1.txt"),
        ("8.4", "json", "schemas/diagnostic-v1.json"),
        ("8.5", "python", "cde/diagnostics_reference.py"),
    ],
    3: [
        ("10.3", "python", "cde/embeddings_reference.py"),
        ("10.7", "python", "cde/report_reference.py"),
    ],
    4: [("11.3", "python", "cde/email_reference.py")],
}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def frozen_source() -> bytes:
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists():
        if LOCK.exists():
            raise SystemExit("Frozen source missing; restore it, do not replace it")
        with urlopen(URL, timeout=60) as response:
            data = response.read(MAX_SOURCE_BYTES + 1)
        if len(data) > MAX_SOURCE_BYTES:
            raise SystemExit("Source exceeds the importer limit")
        if b"# Cognitive Diagnostic Engine" not in data[:4096]:
            raise SystemExit("Unexpected source content")
        SOURCE.write_bytes(data)
    data = SOURCE.read_bytes()
    if len(data) > MAX_SOURCE_BYTES:
        raise SystemExit("Source exceeds the importer limit")
    current = digest(data)
    if LOCK.exists():
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        if lock["sha256"] != current:
            raise SystemExit("Frozen source hash mismatch")
    else:
        LOCK.write_text(
            json.dumps({"url": URL, "sha256": current}, indent=2) + "\n",
            encoding="utf-8",
        )
    return data

def blocks(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    result = []
    section = None
    opened = None
    language = None
    collected = []
    block_section = None
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if opened is not None:
            closing = re.fullmatch(
                re.escape(opened[0]) + "{" + str(len(opened)) + ",}" + r"\s*",
                stripped,
            )
            if closing:
                result.append({
                    "section": block_section,
                    "language": language,
                    "data": "".join(collected).encode("utf-8"),
                })
                opened = None
                collected = []
            else:
                collected.append(line)
            continue
        heading = re.match(r"^#{1,6}\s+(\d+(?:\.\d+)*)(?:\s|$)", stripped)
        if heading:
            section = heading.group(1)
        opening = re.fullmatch(r"(`{3,}|~{3,})([^\r\n]*)", stripped)
        if opening:
            opened = opening.group(1)
            info = opening.group(2).strip().split()
            language = info[0] if info else ""
            block_section = section
            collected = []
    if opened is not None:
        raise SystemExit("Unclosed source fence")
    return result

def import_phase(phase: int) -> None:
    data = frozen_source()
    candidates = blocks(data)
    manifest = (
        json.loads(MANIFEST.read_text(encoding="utf-8"))
        if MANIFEST.exists() else {}
    )
    for section, language, relative in TARGETS[phase]:
        matches = [b for b in candidates
                   if b["section"] == section and b["language"] == language]
        if len(matches) != 1:
            raise SystemExit(
                f"Expected one {language} block in section {section}; "
                f"found {len(matches)}. Stop; do not select a substitute."
            )
        content = matches[0]["data"]
        target = ROOT / relative
        if target.exists() and target.read_bytes() != content:
            raise SystemExit(f"Protected destination differs: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest[relative] = {
            "section": section,
            "language": language,
            "sha256": digest(content),
            "source_sha256": digest(data),
        }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"phase": phase, "source_sha256": digest(data),
                      "files": [x[2] for x in TARGETS[phase]]}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=sorted(TARGETS), required=True)
    import_phase(parser.parse_args().phase)
