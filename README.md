# UGP Juniors — athlete portal (experiment)

Static site. One folder per athlete (`seve/`), each with a `data.json` record and a generated `index.html`.

- `src/portal.html` — the page template (same as the Claude artifact that is the editable record)
- `<athlete>/data.json` — that athlete's published record (schedule, results, log, team, profile, plans, school)
- `tools/build.py` — regenerates every athlete page and the landing page: `python3 tools/build.py`

Edits are made in the record (the Claude artifact); the record is exported to `data.json` and the site is rebuilt and pushed. Daily check-offs on the site stay in the viewer's browser.
