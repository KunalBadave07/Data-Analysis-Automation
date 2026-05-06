# Phase 2: Frontend UI Framework Hardening

## 1) Architecture Explanation
Phase 2 introduces a reusable frontend framework layer on top of the Flask/Jinja app:

- `Base shell`: sticky responsive header, mobile navigation, global background effects.
- `UI component macros`: shared template primitives for page headers, status badges, step pipeline, action buttons, metric cards.
- `Design system CSS`: tokenized colors, spacing, cards, inputs, buttons, status states, progress/timeline patterns.
- `Interaction layer JS`: mobile menu toggling, reveal-on-scroll animation, animated progress bars.

This keeps UI logic consistent while backend/API contracts remain unchanged.

## 2) Folder Structure
```text
app/
  templates/
    base.html
    components/
      ui.html                  # new reusable Jinja macros
    auth/
      login.html
      register.html
    home.html
    operation_select.html
    upload.html
    processing.html
    results.html
    dashboard.html
    report.html
    history.html
  static/
    css/styles.css             # upgraded design system
    js/main.js                 # mobile nav + animation behaviors
tests/
  test_health.py
  test_pages.py                # new page render/redirect checks
docs/
  PHASE_01.md
  PHASE_02.md
```

## 3) Code Generation
Implemented in this phase:

- New Jinja macro library: `app/templates/components/ui.html`
  - `page_header(...)`
  - `status_badge(...)`
  - `action_button(...)`
  - `metric_card(...)`
  - `pipeline_steps(...)`
- Reworked `base.html`:
  - responsive shell layout
  - mobile menu with toggle button
  - accessible skip-link
  - layered background visuals
- Reworked all page templates to use shared components and consistent spacing.
- Upgraded CSS with reusable style tokens and component classes.
- Upgraded JS for progressive animation and menu interaction.
- Added `tests/test_pages.py` for UI route render validation.

## 4) Required Commands
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Run tests:
```powershell
python -m pytest -q
```

## 5) AWS Setup Instructions
No new AWS resources are required in Phase 2.

Carry-forward requirements:
1. Manasvi must provide Kunal IAM programmatic credentials.
2. Keep S3 bucket and DynamoDB tables available for upcoming integration phases.
3. Keep Step Functions placeholder ARN documented in `.env`.

## 6) Integration Instructions
1. Frontend components are now standardized via `components/ui.html`.
2. Future backend responses should continue to expose:
   - `job.status`
   - `job.result.metrics`
   - `job.result.insights`
   - `job.result.recommendations`
3. In Phase 5+, when real pipeline status becomes asynchronous:
   - wire status polling into processing page
   - map backend states to `status_badge` classes (`SUCCEEDED`, `FAILED`, running states)

## 7) Testing Instructions
Run:
```powershell
python -m pytest -q
```

Validation checklist:
1. Home, login, and register pages render successfully.
2. Protected routes redirect unauthenticated users to login.
3. Existing `/health` API test remains passing.
4. Mobile menu opens/closes correctly in narrow viewport.
5. Step indicators and progress bars render across operation/upload/results/dashboard/report pages.
