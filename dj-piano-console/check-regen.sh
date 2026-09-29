#!/usr/bin/env bash
#
# Regression guard for the DJ + piano console design package.
#
# Regenerates BOTH variants, BOTH concept renders and the French edition into a
# throwaway directory and compares every artefact against the copy sitting next to
# this script. Run it on a clean tree and that copy is the committed one. The tree
# is never written to.
#
#   drawing-*.svg  drawing-*-v2.svg      compared by sha256
#   dj-piano-console{,-v2}-spec.html     compared by sha256 after normalising the
#                                        date stamp, the one legitimate daily diff
#   dj-piano-console-v2-spec-fr.html     the French edition, rebuilt by fr/build_fr.py
#                                        from the English this run generated, and
#                                        compared like the English HTML
#   render-cg.png  render-cg-v2.png      compared by sha256 (render-cg.html seeds
#                                        its PRNG, so the renders are reproducible)
#
# The PDFs are deliberately NOT compared: Chrome stamps /CreationDate into every
# print, so two prints of one HTML never match. Rebuild them by hand per README.
#
# Run it from anywhere - cwd is never used to locate anything:
#     dj-piano-console/check-regen.sh
#     ./check-regen.sh
#     bash /any/abs/path/check-regen.sh
#
# Exit: 0 every artefact matches | 1 drift | 2 the guard could not run.

set -uo pipefail

# ---------------------------------------------------------------------------
# Locate the package directory from this script's own path, never from $PWD.
# The ad-hoc check this replaces built paths as "dj-piano-console/<file>"
# relative to the caller's cwd: run from inside dj-piano-console/ the prefix
# doubled, every path missed, nothing was compared and it reported success.
# Two things stop that recurring: every path below is anchored on $HERE, and
# the sanity checks refuse to "pass" a run that compared nothing.
# ---------------------------------------------------------------------------
src=${BASH_SOURCE[0]:-$0}
while [ -L "$src" ]; do                       # follow symlinks; readlink -f is not portable
    src_dir=$(cd -- "$(dirname -- "$src")" >/dev/null 2>&1 && pwd -P)
    src=$(readlink "$src")
    case "$src" in /*) ;; *) src="$src_dir/$src" ;; esac
done
HERE=$(cd -- "$(dirname -- "$src")" >/dev/null 2>&1 && pwd -P)
if [ -z "${HERE:-}" ] || [ ! -f "$HERE/generate.py" ] || [ ! -f "$HERE/render-cg.html" ]; then
    echo "check-regen: not the package directory: '${HERE:-unresolved}' has no generate.py/render-cg.html" >&2
    exit 2
fi

# Floor on how many artefacts a healthy run compares (4 v1 SVG + 5 v2 SVG +
# 3 HTML, the French one included, + 2 PNG). Adding a drawing only raises the real
# count; this is here so that a run which compares nothing can never be mistaken
# for a clean one.
MIN_ARTEFACTS=14

CHROME=${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}
if [ ! -x "$CHROME" ]; then
    for c in google-chrome google-chrome-stable chromium chromium-browser; do
        if command -v "$c" >/dev/null 2>&1; then CHROME=$(command -v "$c"); break; fi
    done
fi
if [ ! -x "$CHROME" ]; then
    echo "check-regen: no Chrome found for the concept renders; set CHROME=/path/to/chrome" >&2
    exit 2
fi

if command -v shasum >/dev/null 2>&1; then
    sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
elif command -v sha256sum >/dev/null 2>&1; then
    sha() { sha256sum "$1" | cut -d' ' -f1; }
else
    echo "check-regen: neither shasum nor sha256sum is available" >&2
    exit 2
fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/dj-console-regen.XXXXXX") || exit 2
KEEP=0
cleanup() { [ "$KEEP" -eq 1 ] || rm -rf "$WORK"; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Regenerate. generate.py writes next to itself, so copying it into $WORK is
# what keeps the working tree untouched.
# ---------------------------------------------------------------------------
cp "$HERE/generate.py" "$HERE/render-cg.html" "$WORK/" || exit 2

render() {  # $1 = url query, $2 = output basename
    "$CHROME" --headless=new --use-angle=swiftshader --enable-unsafe-swiftshader \
        --hide-scrollbars --window-size=1600,1200 --virtual-time-budget=20000 \
        --screenshot="$WORK/$2" "file://$WORK/render-cg.html$1" >/dev/null 2>&1
    if [ ! -s "$WORK/$2" ]; then
        echo "check-regen: Chrome produced no $2" >&2
        return 1
    fi
}
render ""     "render-cg.png"    || exit 2
render "?v=2" "render-cg-v2.png" || exit 2

( cd "$WORK" && python3 ./generate.py )            >/dev/null || { echo "check-regen: v1 generate failed" >&2; exit 2; }
( cd "$WORK" && VARIANT=2 python3 ./generate.py )  >/dev/null || { echo "check-regen: v2 generate failed" >&2; exit 2; }

# The French edition is rebuilt from the English this run just generated, so the
# guard also catches a French that has fallen behind the English: build_fr.py
# leaves any string it cannot translate in English and exits 1, and the comparison
# below shows the resulting drift. Its audit is kept for the report either way.
french_audit=0
python3 -B "$HERE/fr/build_fr.py" --src "$WORK/dj-piano-console-v2-spec.html" \
    --out "$WORK/dj-piano-console-v2-spec-fr.html" > "$WORK/fr-audit.txt" 2>&1 || french_audit=1

# ---------------------------------------------------------------------------
# The HTML carries a date.today() stamp in its sub-title and nothing else that
# legitimately moves. Rewrite it to a fixed token - and verify the rewrite fired,
# so a normaliser that quietly stops matching shows up as a guard error rather
# than as permanent drift or, worse, as a pass.
# ---------------------------------------------------------------------------
normalise_html() {  # $1 = source, $2 = destination (English or French sub-title)
    sed -E -e 's/(Design package for the carpenter\. [^,<]*), [0-9]{1,2} [A-Za-z]+ [0-9]{4}\./\1, DATE-STAMP./' \
           -e 's/(Dossier technique pour le menuisier\. [^,<]*), [0-9]{1,2} [^ ,.<]+ [0-9]{4}\./\1, DATE-STAMP./' \
           "$1" > "$2" || return 1
    grep -q 'DATE-STAMP' "$2"
}

artefacts() {  # $1 = directory -> sorted basenames of everything generate.py and fr/build_fr.py own
    ( cd "$1" 2>/dev/null && ls -1 drawing-*.svg dj-piano-console*-spec.html dj-piano-console*-spec-fr.html \
        render-cg.png render-cg-v2.png 2>/dev/null ) | sort -u
}

mkdir -p "$WORK/.norm"
names=$(printf '%s\n%s\n' "$(artefacts "$WORK")" "$(artefacts "$HERE")" | sed '/^$/d' | sort -u)
count=$(printf '%s\n' "$names" | sed '/^$/d' | wc -l | tr -d ' ')

if [ "$count" -lt "$MIN_ARTEFACTS" ]; then
    echo "check-regen: only $count artefact(s) to compare, expected at least $MIN_ARTEFACTS." >&2
    echo "             Regenerated: $(artefacts "$WORK" | tr '\n' ' ')" >&2
    echo "             Committed:   $(artefacts "$HERE" | tr '\n' ' ')" >&2
    exit 2
fi

echo "check-regen: comparing $count artefacts in $HERE"
echo

drift=0
for f in $names; do
    new="$WORK/$f"
    old="$HERE/$f"
    if [ ! -f "$new" ]; then
        printf 'DRIFT  %-28s committed, but this run did not generate it\n' "$f"
        drift=1; continue
    fi
    if [ ! -f "$old" ]; then
        printf 'DRIFT  %-28s generated, but nothing is committed under that name\n' "$f"
        drift=1; continue
    fi
    case "$f" in
        *-spec.html|*-spec-fr.html)
            if ! normalise_html "$new" "$WORK/.norm/new-$f" || ! normalise_html "$old" "$WORK/.norm/old-$f"; then
                printf 'ERROR  %-28s the date-stamp normaliser matched nothing; fix it before trusting this guard\n' "$f"
                drift=1; continue
            fi
            a=$(sha "$WORK/.norm/new-$f"); b=$(sha "$WORK/.norm/old-$f")
            note=" (date stamp normalised)"
            ;;
        *)
            a=$(sha "$new"); b=$(sha "$old")
            note=""
            ;;
    esac
    if [ "$a" = "$b" ]; then
        printf 'OK     %-28s %s%s\n' "$f" "${a:0:12}" "$note"
    else
        printf 'DRIFT  %-28s regenerated %s != committed %s%s\n' "$f" "${a:0:12}" "${b:0:12}" "$note"
        drift=1
    fi
done

if [ "$french_audit" -ne 0 ]; then
    printf 'DRIFT  %-28s the French build flagged these; translate them in fr/ (see README):\n' "fr/build_fr.py audit"
    sed 's/^/         /' "$WORK/fr-audit.txt"
    drift=1
fi

echo
if [ "$drift" -eq 0 ]; then
    echo "check-regen: clean - all $count artefacts match the package on disk."
    exit 0
fi
KEEP=1
echo "check-regen: DRIFT. Regenerate and commit, or fix the generator." >&2
echo "             The regenerated files were kept in $WORK for diffing." >&2
exit 1
