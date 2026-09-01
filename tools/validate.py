#!/usr/bin/env python3
"""Validate the marketplace catalog against the PolyDice app rules.

Checks index.json and every game file it references. Mirrors the Swift
validator in the app (GameDefinitionValidator): anything that passes here
must import cleanly in the app. Stdlib only; exit code 1 on any failure.
"""

import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCHEMA = 1
DICE_TYPES = {"d3", "d4", "d6", "d8", "d10", "d12", "d20"}
RESERVED_IDS = {"generic", "mansions-of-madness", "heroquest"}  # app built-ins

MAX_RAW_FILE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_FACES = 12
MAX_WEIGHT = 1000
MAX_SYMBOL_NAME_LEN = 64

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# SF Symbol names: lowercase letters, digits, dots, and a few separators.
SF_SYMBOL_RE = re.compile(r"^[a-z0-9][a-z0-9.]{0,63}$")

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def check_game(path: Path, expected_id: str | None = None) -> None:
    tag = path.name
    raw = path.read_bytes()
    if len(raw) > MAX_RAW_FILE_BYTES:
        err(f"{tag}: file is {len(raw)} bytes; limit is {MAX_RAW_FILE_BYTES}")
        return
    try:
        game = json.loads(raw)
    except json.JSONDecodeError as e:
        err(f"{tag}: not valid JSON ({e})")
        return
    if not isinstance(game, dict):
        err(f"{tag}: top level must be a JSON object")
        return

    def req(key, ty, label=None):
        label = label or key
        if key not in game:
            err(f"{tag}: missing required field '{key}'")
            return None
        v = game[key]
        if not isinstance(v, ty) or isinstance(v, bool) and ty is int:
            err(f"{tag}: field '{label}' has the wrong type (expected {ty.__name__})")
            return None
        return v

    # Identity ------------------------------------------------------------
    gid = req("id", str)
    if gid is not None:
        if not ID_RE.match(gid):
            err(f"{tag}: id '{gid}' must match {ID_RE.pattern}")
        if gid in RESERVED_IDS:
            err(f"{tag}: id '{gid}' is reserved by the app")
        if expected_id is not None and gid != expected_id:
            err(f"{tag}: index says id '{expected_id}' but the file has id '{gid}'")

    for key in ("name", "shortName"):
        v = req(key, str)
        if v is not None and not v.strip():
            err(f"{tag}: '{key}' must not be empty")

    version = req("version", int)
    if version is not None and version < 1:
        err(f"{tag}: version must be >= 1 (found {version})")

    if "isGeneric" not in game:
        err(f"{tag}: missing required field 'isGeneric'")
    elif game["isGeneric"] is not False:
        err(f"{tag}: marketplace games must have isGeneric = false")

    # Dice type / count ----------------------------------------------------
    dt = game.get("diceType")
    if dt is not None and dt not in DICE_TYPES:
        err(f"{tag}: diceType '{dt}' not in {sorted(DICE_TYPES)}")

    dc = req("diceCount", int)
    if dc is not None and not (1 <= dc <= 9):
        err(f"{tag}: diceCount must be 1..9 (found {dc})")

    # Shape ------------------------------------------------------------------
    shape = game.get("dieShape")
    if shape is not None:
        if not isinstance(shape, dict):
            err(f"{tag}: dieShape must be an object")
        else:
            if shape.get("type") not in ("polygon", "roundedPolygon"):
                err(f"{tag}: dieShape.type '{shape.get('type')}' must be 'polygon' or 'roundedPolygon'")
            sides = shape.get("sides")
            if not isinstance(sides, int) or not (3 <= sides <= 12):
                err(f"{tag}: dieShape.sides must be 3..12 (found {sides})")
            cr = shape.get("cornerRadius")
            if cr is not None and (not isinstance(cr, (int, float)) or not (0 <= cr <= 40)):
                err(f"{tag}: dieShape.cornerRadius must be 0..40 (found {cr})")

    # Colors -----------------------------------------------------------------
    for field in ("dieColor", "accentColor"):
        c = game.get(field)
        if c is None:
            continue
        if not isinstance(c, dict):
            err(f"{tag}: {field} must be an object")
            continue
        for ch in ("r", "g", "b"):
            v = c.get(ch)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0 <= v <= 1):
                err(f"{tag}: {field}.{ch} must be 0..1 (found {v})")

    # Faces ------------------------------------------------------------------
    faces = game.get("faces")
    if not isinstance(faces, list) or not faces:
        err(f"{tag}: 'faces' must be a non-empty array")
        return
    if len(faces) > MAX_FACES:
        err(f"{tag}: {len(faces)} faces; limit is {MAX_FACES}")

    seen_ids = set()
    for i, face in enumerate(faces):
        ft = f"{tag}: faces[{i}]"
        if not isinstance(face, dict):
            err(f"{ft}: must be an object")
            continue
        fid = face.get("id")
        if not isinstance(fid, str) or not fid.strip():
            err(f"{ft}: missing or empty 'id'")
        elif fid in seen_ids:
            err(f"{ft}: duplicate face id '{fid}'")
        else:
            seen_ids.add(fid)
        if not str(face.get("name", "")).strip():
            err(f"{ft}: 'name' must not be empty")
        w = face.get("weight")
        if not isinstance(w, int) or isinstance(w, bool) or not (1 <= w <= MAX_WEIGHT):
            err(f"{ft}: weight must be 1..{MAX_WEIGHT} (found {w})")

        sym = face.get("symbol")
        if not isinstance(sym, dict):
            err(f"{ft}: 'symbol' must be an object")
            continue
        sname = sym.get("name")
        if not isinstance(sname, str) or not sname.strip():
            err(f"{ft}: symbol 'name' must not be empty")
            continue
        if len(sname) > MAX_SYMBOL_NAME_LEN or "/" in sname or "\\" in sname or ".." in sname:
            err(f"{ft}: unsafe symbol name '{sname}'")
            continue
        stype = sym.get("type")
        if stype == "sfSymbol" and not SF_SYMBOL_RE.match(sname):
            # The app additionally checks UIImage(systemName:) at runtime;
            # this catches structurally impossible names server-side.
            err(f"{ft}: '{sname}' does not look like a valid SF Symbol name")
        if stype == "builtin" and sname != "blank":
            err(f"{ft}: builtin symbols only support 'blank' (found '{sname}')")
        if stype not in ("image", "sfSymbol", "builtin"):
            err(f"{ft}: symbol type '{stype}' must be image, sfSymbol or builtin")

    # Embedded images ------------------------------------------------------
    images = game.get("images") or {}
    if not isinstance(images, dict):
        err(f"{tag}: 'images' must be an object")
        images = {}
    decoded = 0
    for name, b64 in images.items():
        it = f"{tag}: images['{name}']"
        if not SAFE_NAME_RE.match(str(name)):
            err(f"{it}: key must match {SAFE_NAME_RE.pattern}")
            continue
        try:
            data = base64.b64decode(b64, validate=True)
        except Exception:
            err(f"{it}: not valid base64")
            continue
        if not (data[:4] == b"\x89PNG" or data[:2] == b"\xff\xd8"):
            err(f"{it}: not a PNG or JPEG")
            continue
        decoded += len(data)
    if decoded > MAX_IMAGE_BYTES:
        err(f"{tag}: embedded images total {decoded} bytes; limit is {MAX_IMAGE_BYTES}")


def check_index() -> list[dict]:
    index_path = ROOT / "index.json"
    try:
        index = json.loads(index_path.read_text())
    except FileNotFoundError:
        err("index.json is missing")
        return []
    except json.JSONDecodeError as e:
        err(f"index.json: not valid JSON ({e})")
        return []

    if index.get("schema") != SCHEMA:
        err(f"index.json: schema must be {SCHEMA} (found {index.get('schema')})")

    games = index.get("games")
    if not isinstance(games, list):
        err("index.json: 'games' must be an array")
        return []

    seen = set()
    # Entries must be sorted by id for stable diffs (checked once, below).
    ids = [g.get("id", "") for g in games if isinstance(g, dict)]
    for i, entry in enumerate(games):
        et = f"index.json: games[{i}]"
        if not isinstance(entry, dict):
            err(f"{et}: must be an object")
            continue
        for key, ty in (("id", str), ("name", str), ("description", str),
                        ("version", int), ("file", str)):
            v = entry.get(key)
            if not isinstance(v, ty) or (ty is str and not v.strip()):
                err(f"{et}: '{key}' must be a non-empty {ty.__name__}")
        eid = entry.get("id")
        if isinstance(eid, str):
            if not ID_RE.match(eid):
                err(f"{et}: id '{eid}' must match {ID_RE.pattern}")
            if eid in seen:
                err(f"{et}: duplicate id '{eid}'")
            seen.add(eid)
        f = entry.get("file")
        if isinstance(f, str):
            if f.startswith("/") or ".." in f or not f.startswith("games/"):
                err(f"{et}: file must be a repo-relative path under games/ (found '{f}')")
            elif not (ROOT / f).is_file():
                err(f"{et}: file '{f}' does not exist")
    if ids != sorted(ids):
        err("index.json: 'games' must be sorted by id")
    return [g for g in games if isinstance(g, dict)]


def check_examples() -> None:
    for path in sorted((ROOT / "examples").glob("*.polydicegame")):
        check_game(path)


def main() -> int:
    entries = check_index()
    for entry in entries:
        f = entry.get("file")
        if isinstance(f, str) and f and not f.startswith("/") and ".." not in f:
            p = ROOT / f
            if p.is_file():
                check_game(p, expected_id=entry.get("id"))
    check_examples()

    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: index and all game files are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())