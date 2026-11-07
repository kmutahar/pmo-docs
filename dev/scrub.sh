#!/usr/bin/env bash
# Privacy gate: fails if staged or untracked files hold private data.
# Run from the repo root before every commit: dev/scrub.sh
# Names to block (project, people, roster slugs, sub-project ids) go one per line in
# the untracked .scrub-names file (case-insensitive, regex allowed, no blank lines).
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
skip=(':!dev/scrub.sh' ':!LICENSE' ':!skills/pmo-docs/LICENSE' ':!skills/pmo-docs/scripts/_vendor') # vendored upstream code

# Scans what a commit would publish: the index (staged copies, not the files on disk)
# plus untracked files that are about to be added. Gitignored files (tmp/) are skipped.
scan() {
  git grep --cached -nI "$@" -- . "${skip[@]}"
  git ls-files -oz --exclude-standard -- . "${skip[@]}" | xargs -0r grep -nI "$@" --
} 2>/dev/null

generic='/home/[a-z]|\.bashrc|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|\+[0-9][0-9 ]{8,}'
hits=$(scan -E -e "$generic")
[ -n "$hits" ] && { echo "== machine paths / emails / phones =="; echo "$hits"; fail=1; }

if [ -s .scrub-names ]; then
  # an invalid pattern makes git grep fail, and scan hides its errors: that would read as "clean"
  grep -qiEf .scrub-names /dev/null 2>/dev/null
  [ $? -eq 2 ] && { echo "error: .scrub-names holds an invalid regex, so names can't be checked" >&2; exit 1; }
  hits=$(scan -iE -f .scrub-names)
  [ -n "$hits" ] && { echo "== blocked names =="; echo "$hits"; fail=1; }
  # commit messages become CHANGELOG entries (git-cliff), so they must be clean too
  hits=$(git log --format='%h %s%n%b' | grep -iEf .scrub-names)
  [ -n "$hits" ] && { echo "== blocked names in commit messages =="; echo "$hits"; fail=1; }
elif [ -n "${CI:-}" ]; then
  echo "note: CI run, names are checked only on the maintainer's machine" >&2
else
  # a fresh clone without the names list must not pass silently
  echo "error: no .scrub-names file, so project and people names can't be checked" >&2
  fail=1
fi

[ "$fail" -eq 0 ] && echo "scrub clean"
exit "$fail"
