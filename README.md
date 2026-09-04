# PolyDice Marketplace

The community game catalog for [PolyDice](https://github.com/draugvar/PolyDice), a minimalist iOS dice roller for board games.

PolyDice users can open **Settings → Browse marketplace** inside the app and install any game listed here with one tap. Every download goes through the app's import validation, so a game that passes this repo's checks installs cleanly.

## Games

| Game | Author | Description |
|------|--------|-------------|
| [Dungeon Combat Die](games/dungeon-combat-die.polydicegame) | draugvar | Six-sided combat die for dungeon crawls: three skulls, two shields and one critical bolt. |
| [Elemental Dice](games/elemental-dice.polydicegame) | draugvar | Six elemental faces — fire, water, air, earth, storm and frost. |
| [Fate / Fudge Dice](games/fate-dice.polydicegame) | draugvar | Four Fudge/Fate dice with plus, blank and minus faces, built from SF Symbols. |
| [Geometric Runes](games/geometric-runes.polydicegame) | draugvar | Six original geometric rune glyphs embedded as base64 images; shows the embedded-image workflow. |
| [Playtest Dice](games/playtest-dice.polydicegame) | draugvar | Weighted resolution die for designers: 50% failure, 33% success, 17% critical. |

## How it works

- [`index.json`](index.json) is the catalog the app fetches: `{"schema": 1, "games": [...]}`.
- Each entry points to a `.polydicegame` file (JSON) under [`games/`](games/).
- Anyone can add a game via pull request — see [CONTRIBUTING.md](CONTRIBUTING.md) for the step-by-step guide and [docs/JSON_REFERENCE.md](docs/JSON_REFERENCE.md) for the full file format.
- [`tools/validate.py`](tools/validate.py) checks every file against the same rules the app enforces, and CI runs it on every push and pull request.

## Quickstart for contributors

```bash
git clone https://github.com/draugvar/PolyDice-Marketplace
cd PolyDice-Marketplace
# add your game to games/, then add your entry to index.json
python3 tools/validate.py
```

If that prints `OK`, open a pull request.

## License

The repo tooling and documentation are MIT-licensed (see [LICENSE](LICENSE)). Game files and their artwork are licensed **CC BY 4.0** by their authors (the `author` field is the attribution); third-party embedded assets keep their own license — credits in [ATTRIBUTION.md](ATTRIBUTION.md). Details in [CONTRIBUTING.md](CONTRIBUTING.md).