# MEMMS — Phase 1 Implementation Plan

## 1. Architectural Summary

**Pattern**: Lightweight MVC-ish layering, beginner-friendly.

```
┌─────────────────────────────────────────────┐
│  main.py            → app entry point       │
├─────────────────────────────────────────────┤
│  app/               → all UI lives here     │
│   ├─ main_window.py → QMainWindow + sidebar │
│   ├─ dashboard.py   → stats cards page      │
│   ├─ pages.py       → placeholder pages     │
│   ├─ translations.py→ AR/EN strings + RTL   │
│   └─ styles.py      → QSS stylesheet        │
├─────────────────────────────────────────────┤
│  database.py        → engine + SessionLocal │
│  models.py          → SQLAlchemy 2.x models │
├─────────────────────────────────────────────┤
│  data/memms.db      → SQLite file (gitignored) │
└─────────────────────────────────────────────┘
```

**Why an `app/` package even though the prompt shows flat?**  
The prompt allows a "minor technical adjustment if justified." Two reasons:
1. UI code grows fast in Phase 2 (CRUD forms, dialogs). Mixing it with `main.py`/`database.py` makes that file unreadable for a beginner.
2. Keeping root to "boot + data + models" matches what most PySide6 tutorials show — easier to read.

## 2. Key Decisions

| Decision | Choice | Why |
|---|---|---|
| Translation | Python dict in `app/translations.py` | No `lupdate` toolchain; instant AR/EN switch; readable for beginners |
| RTL/LTR | `QApplication.setLayoutDirection()` on language change | Standard Qt approach; flips sidebar + content in one call |
| DB sessions | `SessionLocal()` as context manager | Guaranteed close, beginner-safe |
| Money | `Numeric(12,2)` → Python `Decimal` | Spec requires; avoids float drift |
| Auto table creation | `Base.metadata.create_all(engine)` on first run | Spec requires; no Alembic for Phase 1 |
| Stat refresh | `dashboard.refresh_stats()` on language switch + manual button | Card labels retranslate too |
| Placeholder pages | Reusable `PlaceholderPage(title_key, body_key)` widget | One implementation, 7 sections |

## 3. Out of Scope (Phase 1)

Per the prompt's explicit limits:
- CRUD on Equipment/WorkOrders/etc.
- Login / permissions
- Network multi-user (SQLite is single-machine)
- PDF/Excel reports
- Preventive Maintenance scheduling logic

## 4. Files to Create

| File | Purpose |
|---|---|
| `main.py` | Boot QApplication, set translation, show MainWindow |
| `database.py` | Engine + SessionLocal + `get_session()` context manager |
| `models.py` | 7 SQLAlchemy 2.x models with relationships |
| `app/main_window.py` | QMainWindow, sidebar nav, QStackedWidget |
| `app/dashboard.py` | 3 stat cards reading live DB counts |
| `app/pages.py` | `PlaceholderPage` for 7 non-Dashboard sections |
| `app/translations.py` | AR/EN strings, `Translator` class, RTL flag |
| `app/styles.py` | QSS for dark sidebar + light content + cards |
| `requirements.txt` | PySide6, SQLAlchemy |
| `README.md` | Setup + run + test instructions |
| `.gitignore` | `data/`, `__pycache__`, `.venv` |
| `data/.gitkeep` | Keep folder in git, db ignored |

## 5. Verification Plan

In sandbox (headless where possible):
1. `python -c "import database, models, app.main_window, app.dashboard, app.pages"` — all modules import clean.
2. Run a script that creates DB, inserts one Equipment row + one WorkOrder + one Staff, queries counts.
3. Launch the app under `QT_QPA_PLATFORM=offscreen` for a few seconds — verify no crash.
4. Language switch test: call translator, check `layoutDirection` flips.

Manual (user runs in Windows + VS Code):
- Window opens, sidebar visible, dashboard cards show real numbers.
- Click AR/EN toggle → labels + layout direction change.
- Click each sidebar entry → correct page loads.
- Status bar / window title updates.

## 6. Risks & Mitigations

- **PySide6 install on Windows may pull large wheels** → Document the exact pip command; mention `--upgrade pip` first.
- **Arabic fonts on default Windows** → Recommend `Segoe UI` (built-in) + Tahoma fallback. Both ship with Windows.
- **SQLite file locked if app crashes** → Always use context-managed sessions; document this in README.
- **Beginner might edit translations wrong** → Group strings by section, comment each.

## 7. Next Step

If you sign off on this plan, I'll:
1. Create all files in `/workspace/MEMMS/`
2. Install PySide6 + SQLAlchemy in sandbox
3. Run the verification tests
4. Hand back a tested, runnable Phase 1 + clear test report

Estimated time: ~15–20 min of build + test, then delivery.
