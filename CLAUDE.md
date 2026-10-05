# Personal Projects

Personal repo for games and other projects.

## GitHub

- **Repo:** https://github.com/papaleoluca/personal
- **Remote:** `origin` via HTTPS
- **Push:** `git push origin main`
- **Auth:** Uses HTTPS (no SSH key configured). GitHub CLI (`gh`) is available for authentication if needed.

## Workout plan pages (private)

The repo is public and GitHub Pages serves the whole tree, so pages under `workout-plan/` are
committed only in StaticCrypt-encrypted form. Each plan folder keeps its plaintext in `source/`,
which `workout-plan/.gitignore` excludes. Never commit the plaintext HTML.

- Run StaticCrypt (encrypt, `--share` and `--decrypt` alike) from inside `workout-plan/` so the salt in
  `.staticrypt.json` is reused. A new salt breaks the saved magic link and every remembered device.
  The output keeps the input's file name:
  `STATICRYPT_PASSWORD=... npx --yes staticrypt@3.5.4 "<plan>/source/<page>.html" -d "<plan>"`
- Magic link (a separate run, `--share` only prints): `npx --yes staticrypt@3.5.4 --share "<page URL>" --share-remember`
- The password is not stored anywhere in the repo. Ask Luca for it.
- Before committing, grep the output for a heading from the page to confirm no plaintext.
