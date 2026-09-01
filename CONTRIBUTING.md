# Contributing a Game

Thanks for adding a game to the PolyDice marketplace! The whole process is one pull request.

## Before you start

- Read [docs/JSON_REFERENCE.md](docs/JSON_REFERENCE.md) — it documents every field and every rule the app enforces.
- Try PolyDice's **Settings → Import game file** with your `.polydicegame` first: if it imports without errors, it will pass validation here too. The app is the source of truth.

## Content rules

1. **Original or licensed art only.** You must own the artwork or have permission to distribute it. No scans, photos or rip-offs of commercial dice (Zombicide, HeroQuest, etc.).
2. **No trademarks in game names.** Use a descriptive name ("Fate / Fudge Dice"), not a product name someone else owns.
3. **English metadata.** `name`, `shortName` and `description` in index.json, and `name` fields in the game file, should be in English.
4. **Keep files small.** Raw file ≤ 15 MB, embedded images decoded ≤ 10 MB in total. Prefer SF Symbols or simple PNGs.

## Step-by-step

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/PolyDice-Marketplace
cd PolyDice-Marketplace
```

### 2. Create your game file

Add `games/<your-game-id>.polydicegame`. The file name must match the game's `id`. Minimal template (also in [`examples/minimal-sfSymbols.polydicegame`](examples/minimal-sfSymbols.polydicegame)):

```json
{
  "id": "your-game-id",
  "name": "Your Game Name",
  "shortName": "Short",
  "author": "your-github-username",
  "version": 1,
  "isGeneric": false,
  "diceType": "d6",
  "dieShape": { "type": "roundedPolygon", "sides": 6, "rotation": 0, "cornerRadius": 16 },
  "dieColor": { "r": 0.13, "g": 0.13, "b": 0.20 },
  "accentColor": { "r": 1.0, "g": 1.0, "b": 1.0 },
  "faces": [
    { "id": "plus", "name": "Plus", "weight": 1, "symbol": { "type": "sfSymbol", "name": "plus" } },
    { "id": "minus", "name": "Minus", "weight": 1, "symbol": { "type": "sfSymbol", "name": "minus" } }
  ],
  "diceCount": 2
}
```

For custom face art, see the embedded-image workflow in [docs/JSON_REFERENCE.md](docs/JSON_REFERENCE.md) (the `images` map) — `games/geometric-runes.polydicegame` is a full example.

### 3. Add your entry to index.json

Insert it in the `games` array, **sorted by `id`** (CI enforces the order):

```json
{
  "id": "your-game-id",
  "name": "Your Game Name",
  "shortName": "Short",
  "author": "your-github-username",
  "description": "One or two sentences shown in the app.",
  "version": 1,
  "file": "games/your-game-id.polydicegame"
}
```

### 4. Validate locally

No dependencies needed — Python 3 standard library only:

```bash
python3 tools/validate.py
```

You should see `OK: index and all game files are valid`. If it prints problems, fix them (the messages name the exact field).

### 5. Open the pull request

```bash
git checkout -b add-your-game-id
git add games/your-game-id.polydicegame index.json
git commit -m "Add your-game-id"
git push -u origin add-your-game-id
```

Then open the PR against `main`. CI runs the same validator; once it's green the game goes live — the app fetches `index.json` from this repo's `main` branch, so merged games appear in the app immediately (no app update needed).

## Updating or removing a game

- **Update:** edit the game file, bump its `version`, and bump the `version` in the index entry. Re-importing in the app replaces the previous install.
- **Removal:** open an issue; only the repo owner removes entries (the app's installed copy is untouched either way).

## Questions?

Open an issue, or check [docs/JSON_REFERENCE.md](docs/JSON_REFERENCE.md) first — it covers every rule.