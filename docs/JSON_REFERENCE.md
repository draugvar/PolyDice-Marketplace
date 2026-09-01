# PolyDice Game JSON Reference

A `.polydicegame` file is a JSON object describing one game: its dice, faces and artwork. The app (source of truth: `GameDefinitionValidator` in the PolyDice repo) enforces every rule below at import time — a file that violates any of them is rejected with an error naming the field.

## Top-level fields

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `id` | string | yes | `^[a-z0-9][a-z0-9-]{0,63}$` — 1–64 lowercase letters, digits or dashes, starting with a letter or digit. Must not be `generic` or any app built-in id (`mansions-of-madness`, `heroquest`). |
| `name` | string | yes | Non-empty. Displayed on the game pill and in Settings. |
| `shortName` | string | yes | Non-empty. Shown in compact contexts. |
| `author` | string | no | Your GitHub username or credit line. |
| `version` | int | yes | ≥ 1. Bump when you update the game. |
| `isGeneric` | bool | yes | Must be `false` for marketplace games. |
| `diceType` | string | no | One of `d3`, `d4`, `d6`, `d8`, `d10`, `d12`, `d20`. |
| `dieShape` | object | no | See below. |
| `dieColor` | object | no | `{ "r", "g", "b" }`, each 0–1. |
| `accentColor` | object | no | Same format as `dieColor`. |
| `faces` | array | yes (non-generic) | 1–12 faces. See below. |
| `images` | object | no | Map of embedded base64 images. See below. |
| `diceCount` | int | yes | 1–9. Default number of dice when the game is selected. |
| `minDiceCount` | int | no | **Ignored by the current app** (kept for compatibility). |

Unknown fields are ignored — forward compatibility is free, but don't rely on them.

## `dieShape`

```json
{ "type": "roundedPolygon", "sides": 6, "rotation": 0, "cornerRadius": 16 }
```

| Field | Rules |
|-------|-------|
| `type` | `"polygon"` or `"roundedPolygon"` |
| `sides` | 3–12 |
| `rotation` | degrees, any value |
| `cornerRadius` | 0–40, only used by `roundedPolygon` |

## `faces[]`

```json
{ "id": "plus", "name": "Plus", "weight": 1, "symbol": { "type": "sfSymbol", "name": "plus" } }
```

| Field | Rules |
|-------|-------|
| `id` | Unique within the file, non-empty. |
| `name` | Non-empty. |
| `weight` | 1–1000. Relative probability of the face; equal weights = fair die. |
| `symbol` | See below. |

## `symbol`

| Field | Rules |
|-------|-------|
| `type` | `"image"`, `"sfSymbol"` or `"builtin"` |
| `name` | ≤ 64 chars, no `/`, `\` or `..` |
| `rotation` | optional, degrees |
| `opacity` | optional, 0–1 |

Symbol resolution by type:

- **`sfSymbol`** — an [SF Symbols](https://developer.apple.com/sf-symbols/) name (e.g. `"plus"`, `"skull"`). The app verifies the symbol exists at import time. This is the cheapest and crispest option — prefer it when a suitable symbol exists.
- **`image`** — a face image, resolved in this order: the `images` map in this file, then a file on disk, then the app's asset catalog. Use the embedded `images` map for self-contained games (below).
- **`builtin`** — only `"blank"` is available (an empty face).

## Embedded images (`images`)

```json
{
  "images": {
    "circle": "iVBORw0KGgo...",
    "cross": "iVBORw0KGgo..."
  }
}
```

- Keys: 1–64 chars of `A–Z a–z 0–9 _ -`.
- Values: base64-encoded **PNG or JPEG** data (the app checks magic bytes).
- Budget: the decoded images must total ≤ 10 MB, and the whole file ≤ 15 MB raw.
- On import, the app extracts them to its own storage and looks them up by face symbol `name` — so symbol names must match image keys exactly.
- Workflow: export your art as PNG (128×128 or 256×256 is plenty — faces render small), then `base64 -i face.png | pbcopy` on macOS (or `base64 -w0 face.png` on Linux) and paste it as the value.

`games/geometric-runes.polydicegame` is a complete example; `tools/generate_image_seed.py` regenerates it and shows the workflow in code.

## Rules summary (as enforced at import)

1. File ≤ 15 MB, must parse as JSON.
2. `id` matches `^[a-z0-9][a-z0-9-]{0,63}$` and is not reserved (`generic` + app built-ins).
3. `name`, `shortName` non-empty; `version` ≥ 1.
4. Non-generic games: 1–12 `faces`; face `id`s unique; face `name`s non-empty.
5. `weight` 1–1000 per face.
6. Symbol `name` ≤ 64 chars, no `/`, `\`, `..`.
7. `sfSymbol` names must exist in the current SF Symbols set; `builtin` must be `"blank"`.
8. `diceType` ∈ {d3, d4, d6, d8, d10, d12, d20}.
9. `diceCount` 1–9.
10. `dieShape.type` ∈ {polygon, roundedPolygon}, `sides` 3–12, `cornerRadius` 0–40.
11. `dieColor`/`accentColor` components 0–1.
12. `images` keys safe; values valid base64 with PNG/JPEG magic bytes; decoded total ≤ 10 MB.

Re-importing the same `id` (from file or marketplace) **replaces** the previous install and cleans up its extracted images.

## index.json entry format

```json
{
  "id": "your-game-id",
  "name": "Your Game Name",
  "shortName": "Short",
  "author": "your-github-username",
  "description": "One or two sentences shown in the app's marketplace list.",
  "version": 1,
  "file": "games/your-game-id.polydicegame"
}
```

- `schema` at the top level is `1` (bump = breaking change coordinated with the app).
- `games` must be sorted by `id` (CI enforces it).
- `file` must be a repo-relative path under `games/` that exists.
- The entry `id` must equal the game file's `id`.