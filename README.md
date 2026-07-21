# Risk Manager

A desktop co-pilot for a discretionary trader. It enforces pre-defined risk rules in real time, tracks trading discipline across a session, and produces an end-of-session report. **It never places trades and has no order-execution capability of any kind.**

Version 1 uses manual data entry ("Simulate Data"). Version 3  adds optional OCR capture from a mirrored phone screen as an alternate data source — both feed the exact same evaluation pipeline.

---

## Requirements

- Python 3.10+
- Windows, macOS, or Linux (CustomTkinter is cross-platform; packaging instructions below assume Windows, adjust paths for other OSes)
- Tesseract OCR binary — **only required if using Milestone 3 (OCR) features.** See [OCR setup](#ocr-setup-milestone-3-only).

---

## Setup

```bash
git clone <repo-url>
cd risk_manager
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

On first run, the app creates `database/trader_rules.db` and seeds default settings automatically — no manual DB setup required.

---

## Run from source

```bash
python src/main.py
```

---

## Run tests

```bash
pytest -v
```

Run a single suite:
```bash
pytest tests/test_risk_engine.py -v
```

`test_risk_engine.py` is the highest-priority suite in the project — it covers `evaluate_risk()` and the Discipline Score calculation, which drive every risk signal the trader sees. All tests here must pass before merging any change that touches `risk_engine.py`.

---

## Build executable

Packaging uses PyInstaller and produces a standalone executable that does not require Python installed on the target machine.

```bash
pip install pyinstaller
pyinstaller --windowed --onefile src/main.py
```

Output is written to `dist/`. The build reads/writes `trader_rules.db` and `logs/` from a persistent user-data directory (not the source tree — this matters because PyInstaller's bundled runtime path is not the same as the source directory). See the Technical Documentation for the exact path resolution logic.

**Before considering a build "done," test the executable on a machine without the dev `venv` active** — packaging issues (missing DLLs, broken relative paths) don't show up when testing from source.

### OCR setup (Milestone 3 only)

Tesseract is a system binary, not a Python package, and is **not** bundled automatically by PyInstaller.

1. Install Tesseract separately:
   - Windows: [UB-Mannheim Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `apt install tesseract-ocr`
2. If it's not on your system `PATH`, set the path explicitly before running:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```
3. Install the OCR-only Python dependencies (commented out in `requirements.txt` by default):
   ```bash
   pip install pytesseract opencv-python mss pygetwindow
   ```

---

## Project structure

```
risk_manager/
├── src/
│   ├── main.py              # entry point
│   ├── models/               # risk_engine, data_manager, session
│   ├── views/                 # dashboard, settings dialog, report view
│   ├── controllers/          # app_controller — the only layer that touches both UI and model
│   └── ocr/                   # milestone 3 only, fully isolated
├── tests/
├── database/                  # trader_rules.db (gitignored)
├── logs/                      # rotating app logs (gitignored)
└── requirements.txt
```

See `docs/technical_documentation.md` for architecture details and `docs/user_manual.md` for end-user instructions.

---

## Logging

Logs write to `logs/app.log` (rotating, 5MB × 3 backups). Check here first when diagnosing a bug — the app never relies on console output.

---

## Contributing / git workflow

- `main` is always deployable.
- One feature branch per task, named after the plan section it implements (e.g. `feature/discipline-score`).
- No commit to `main` without `pytest` passing locally.
