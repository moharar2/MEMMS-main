# MEMMS Phase 1 — Test Report

**Date:** 2026-09-17
**Environment:** Linux sandbox (Debian 12, Python 3.11.2, PySide6 6.11.2, SQLAlchemy 2.0.54)
**Test mode:** Headless via `QT_QPA_PLATFORM=offscreen` (Qt platform = no display)

---

## 1. Summary

| # | Check | Status |
|---|---|---|
| 1 | All modules import cleanly | ✅ Pass |
| 2 | `init_db()` creates the SQLite file + tables | ✅ Pass |
| 3 | Sample DB queries return real counts (no hard-coded values) | ✅ Pass |
| 4 | Translation lookup + RTL/LTR detection logic | ✅ Pass |
| 5 | `MainWindow` builds without exceptions, navigates 8 pages | ✅ Pass |
| 6 | `main.py` boots end-to-end (full app lifecycle) | ✅ Pass |
| 7 | Dashboard refresh re-queries DB and updates cards | ✅ Pass |
| 8 | Language switch flips RTL↔LTR **and** re-translates every widget | ✅ Pass |
| 9 | All 8 sidebar entries show correct title in AR + EN | ✅ Pass |

**Result: 9 / 9 checks passed.**

---

## 2. Files Tested

```
MEMMS/
├── main.py                ✅
├── database.py            ✅
├── models.py              ✅
├── app/
│   ├── __init__.py        ✅
│   ├── main_window.py     ✅
│   ├── dashboard.py       ✅
│   ├── pages.py           ✅
│   ├── translations.py    ✅
│   └── styles.py          ✅
├── requirements.txt       ✅
├── README.md              ✅
├── .gitignore             ✅
└── data/
    ├── .gitkeep           ✅
    └── memms.db           ✅ (created at runtime, not committed)
```

---

## 3. Test Scripts (in the project root)

These four scripts are kept in the project so the user can re-run them:

| Script | What it checks |
|---|---|
| `smoke_test.py`    | Module imports, init_db, sample counts, translator logic, MainWindow construction + page navigation |
| `boot_test.py`     | Full `main.py` boot path (init DB → QApplication → show window → event loop) |
| `dashboard_test.py`| Dashboard refresh + language switch update card text in real time |
| `i18n_test.py`     | All 8 sidebar entries show correct titles in both AR and EN |

To re-run them locally (after `pip install -r requirements.txt`):

```powershell
# Windows PowerShell
$env:QT_QPA_PLATFORM = "offscreen"
python smoke_test.py
python boot_test.py
python dashboard_test.py
python i18n_test.py
```

The `offscreen` flag makes Qt render without a display, so these run on any
machine.

---

## 4. Detailed Test Output

### 4.1 `smoke_test.py`

```
============================================================
1. Importing modules
============================================================
  OK
============================================================
2. init_db()
============================================================
  OK
============================================================
3. Sample counts (uses the data already in data/memms.db)
============================================================
  equipment=3  open_work_orders=2  staff=1
============================================================
4. Translator + RTL/LTR
============================================================
  OK
============================================================
5. Build MainWindow and exercise it
============================================================
  initial layoutDirection = LayoutDirection.LeftToLeft
  after EN layoutDirection = LayoutDirection.LeftToRight
  after AR layoutDirection = LayoutDirection.RightToLeft
  page 0: DashboardPage
  page 1: PlaceholderPage
  ...
  page 7: PlaceholderPage
  OK
============================================================
RESULT
============================================================
  All smoke checks passed.
```

### 4.2 `boot_test.py`

```
main() returned: 0
OK: full main.py boot path succeeded.
```

### 4.3 `dashboard_test.py`

```
After refresh: equipment=3 work_orders=2 staff=1
Card title after EN switch: 'Total Equipment'
OK: dashboard refresh + language switch work end-to-end.
```

### 4.4 `i18n_test.py`

```
OK: all 8 pages retranslate correctly on AR/EN switch.
```

---

## 5. Bugs Found and Fixed During Testing

| # | Bug | Fix |
|---|---|---|
| 1 | `from translations import …` failed because `translations.py` is inside `app/` | Updated all imports to `from app.translations import …` / `from .translations import …` |
| 2 | `self._nav_group.button(0)` returned `None` — `QButtonGroup` doesn't auto-assign sequential IDs starting at 0 | Assigned explicit `id=index` when adding each button; use the `_nav_buttons` list to look up the default-checked button |
| 3 | Stat card titles did not update on language switch — `StatCard` was not a `TranslatableWidget`, so `collect_translatable` could not find it | Made `StatCard` inherit from `TranslatableWidget`, removed the module-level `TRANSLATOR` global, passed the `Translator` instance through the constructor |

All three bugs were caught and fixed **before delivery**.

---

## 6. Manual Tests Still Required

The sandbox is headless, so visual checks need to be done on a real desktop:

- [ ] Open the window on Windows and confirm the **dark navy sidebar**, **white cards**, and **typography** look clean.
- [ ] Confirm Arabic text uses a proper Arabic font (Windows ships `Segoe UI` and `Tahoma` — both fine).
- [ ] Open an external SQLite viewer, add an `Equipment` row, and click **تحديث / Refresh** to confirm the card updates live.
- [ ] Click the language button — confirm sidebar flips side and labels update everywhere, including top bar, card titles, and the active button highlight.

---

## 7. Known Limitations (Per Phase 1 Brief)

- No CRUD screens (deferred to Phase 2).
- No login / permissions.
- No PDF or Excel reports.
- SQLite is single-machine; PostgreSQL migration is **scaffolded** (changing `DATABASE_URL` and engine options in `database.py` is enough) but not exercised.
- Money stored as `Numeric(12,2)` + Python `Decimal` — confirmed; no float arithmetic anywhere.
