# Cortana Stock Redistribution — Web

A single-page web app that runs the Cortana stock redistribution algorithm entirely in the browser. Upload the weekly stock CSV, get the redistribution sheet plus per-shop shipment CSVs, and see the results table on the page.

No server, no data leaves the browser — Python runs client-side via [Pyodide](https://pyodide.org/).

## Files

- `index.html` — UI (drop zone, summary, downloads, results table)
- `app.js` — bootstraps Pyodide, wires the UI, triggers downloads, renders the table
- `redistribute.py` — the redistribution algorithm (adapted from the Claude Code skill to work on strings instead of files)

## Local test

Serve the folder with any static server, then open `http://localhost:8000/`:

```bash
cd cortana-stock-web
python3 -m http.server 8000
```

Opening `index.html` directly with `file://` will not work — Pyodide needs `fetch()` for `redistribute.py`, which requires an HTTP origin.

## Deploy to GitHub Pages

1. Commit and push this folder to your GitHub repo (e.g. `papaleoluca/personal`).
2. In the repo on GitHub: **Settings → Pages**.
3. Under **Source**, pick the branch (e.g. `main`) and the folder (`/` root, or `/docs` if you move the files there).
4. Save. Your app will be live at `https://<username>.github.io/<repo>/cortana-stock-web/` after a minute.

If you'd rather have the app at the root of the site, move the three files to the repo root or into a `docs/` folder and adjust GitHub Pages settings accordingly.

## Notes

- Pyodide is loaded from `cdn.jsdelivr.net` at version `v0.26.4`. If a browser blocks it, or you want to pin a newer version, edit the `<script src="…">` tag in `index.html`.
- Output CSVs use `;` delimiter, UTF-8 with BOM, and CRLF line endings — matching the input format.
- The redistribution logic is a copy of the Claude Code skill at `~/.claude/skills/cortana-stock/scripts/redistribute.py`. If you change the rules in one place, sync the other.
