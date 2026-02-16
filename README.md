# eDelphi MVP (Real-time / 2-round compatible)

This is a minimal, invite-only Django app to run a Delphi-style survey with:
- 5-point Likert items (Strongly disagree → Strongly agree)
- Either/Or items
- Anonymous comments + optional suggested revisions
- "Real-time" group feedback shown only after a participant's first submission in a round (configurable)
- Responses can be revised while a round is open
- Group summary stats (n, mean, top-box agreement, bottom-box disagreement, consensus @ 0.75) updated in real time

## Quick start (local)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/

## Setup steps (admin)
1) Create a Study
2) Create Round 1 and Round 2 (optional)
   - For Round 1: set `status=OPEN`, `show_feedback_immediately=False`
   - For Round 2: set `status=DRAFT` initially; set `show_feedback_immediately=True` if you want immediate feedback display
3) Import items (CSV)
4) Sync latest item versions into a round
5) Import panelists (CSV)
6) Mint invitation links and send them by email

### CSV formats
**items.csv** columns:
- stable_code, domain_tag, stem_text, response_type, option_a, option_b, order_index, version

response_type is one of: `LIKERT_5` or `EITHER_OR`

**panelists.csv** columns:
- email, display_name, affiliation

## Management commands
Import items:
```bash
python manage.py import_items --study_id 1 --csv items.csv
```

Import panelists:
```bash
python manage.py import_panelists --study_id 1 --csv panelists.csv
```

Attach items to a round (latest versions):
```bash
python manage.py sync_round_items --round_id 1 --overwrite
```

Mint invite links (prints links):
```bash
python manage.py mint_invites --study_id 1 --base_url http://127.0.0.1:8000 --dry_run
```

Compute feedback for all items in a round (optional; feedback is also updated on each save):
```bash
python manage.py compute_feedback --round_id 1 --overwrite
```

## Notes
- This MVP uses Django sessions for panelist authentication via magic links.
- Email sending is not wired; mint_invites prints links for you to email (mail merge).
- For production: move to PostgreSQL, set a strong SECRET_KEY, and enforce HTTPS.
