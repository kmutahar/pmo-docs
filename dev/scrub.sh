#!/usr/bin/env bash
# Privacy gate: fails if staged or untracked files hold private data.
# Usage:
#   dev/scrub.sh [--] [PATH...]    check staged+untracked files, or working-tree PATHs (as git commit -- PATHs sees them)
#   dev/scrub.sh --message FILE    check a commit message (FILE may be - for stdin)
#   dev/scrub.sh -h | --help       show this help
# Names to block (project, people, roster slugs, sub-project ids) go one per line in
# the untracked .scrub-names file (case-insensitive, regex allowed, no blank lines).
# The pre-commit hook sees git's temporary index; pass -- PATH... for a matching manual check.
set -u

msg_mode=0
msg_file=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      awk 'NR > 1 { if (/^#/) { sub(/^# ?/, ""); print } else exit }' "$0"
      exit 0
      ;;
    --message)
      [ $# -ge 2 ] || { echo "error: --message requires a file path or -" >&2; exit 2; }
      msg_mode=1
      msg_file="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [ "$msg_mode" -eq 1 ]; then
  [ $# -eq 0 ] || { echo "error: --message does not take path arguments" >&2; exit 2; }
  if [ "$msg_file" = "-" ]; then
    msg_text=$(cat)
  elif [ -r "$msg_file" ]; then
    msg_text=$(cat "$msg_file")
  else
    echo "error: cannot read message file: $msg_file" >&2
    exit 2
  fi
fi

paths=()
if [ $# -gt 0 ]; then
  prefix=$(git rev-parse --show-prefix 2>/dev/null || true)
  for p in "$@"; do
    case "$p" in
      /*|:*) paths+=("$p") ;;
      *) paths+=("${prefix}${p}") ;;
    esac
  done
fi

cd "$(dirname "$0")/.." || exit 2
fail=0
skip=(':!dev/scrub.sh' ':!LICENSE' ':!skills/pmo-docs/LICENSE' ':!skills/pmo-docs/scripts/_vendor') # vendored upstream code
generic='/home/[A-Za-z]|/Users/[A-Za-z]|/root/|/var/home/|/Volumes/|[A-Za-z]:\\Users\\|\.bashrc|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|\+[0-9][0-9 ().-]{8,}|(^|[^0-9A-Za-z])00[0-9]{8,}|\([0-9]{3}\)[ .-]?[0-9]{3}[ .-][0-9]{4}|(^|[^0-9A-Za-z-])0[0-9]{2,3}[ .-][0-9]{3,4}[ .-][0-9]{3,4}([^0-9]|$)'

if [ "$msg_mode" -eq 1 ]; then
  hits=$(printf '%s\n' "$msg_text" | grep -nE -e "$generic")
  [ -n "$hits" ] && { echo "commit-msg: the message contains a machine path, email or phone number" >&2; echo "$hits" >&2; fail=1; }
  if [ -s .scrub-names ]; then
    grep -qiEf .scrub-names /dev/null 2>/dev/null
    [ $? -eq 2 ] && { echo "commit-msg: .scrub-names holds an invalid regex" >&2; exit 1; }
    hits=$(printf '%s\n' "$msg_text" | grep -iEf .scrub-names)
    [ -n "$hits" ] && { echo "commit-msg: the message contains a blocked name (see .scrub-names)" >&2; fail=1; }
  elif [ -z "${CI:-}" ]; then
    echo "commit-msg: no .scrub-names file, so names can't be checked" >&2; fail=1
  fi
  exit "$fail"
fi

# Scans what a commit would publish: the index (staged copies, not the files on disk)
# plus untracked files that are about to be added, or the given working-tree paths
# (what `git commit -- <paths>` commits). Gitignored files (tmp/) are skipped.
scan() {
  if [ "${#paths[@]}" -gt 0 ]; then
    git grep -na --untracked "$@" -- "${paths[@]}" "${skip[@]}"
  else
    git grep --cached -na "$@" -- . "${skip[@]}"
    git ls-files -oz --exclude-standard -- . "${skip[@]}" | xargs -0r grep -na "$@" --
  fi | tr -d '\000'
} 2>/dev/null

history_text() {
  git log --all --format='%h %s%n%b' 2>/dev/null
  git tag -n99 2>/dev/null
}

hits=$(scan -E -e "$generic")
[ -n "$hits" ] && { echo "== machine paths / emails / phones =="; echo "$hits"; fail=1; }
hits=$(history_text | grep -vxF 'Signed-off-by: dependabot[bot] <support@github.com>' | grep -E -e "$generic")
[ -n "$hits" ] && { echo "== machine paths / emails / phones in history or tags =="; echo "$hits"; fail=1; }

if [ -s .scrub-names ]; then
  # an invalid pattern makes git grep fail, and scan hides its errors: that would read as "clean"
  grep -qiEf .scrub-names /dev/null 2>/dev/null
  [ $? -eq 2 ] && { echo "error: .scrub-names holds an invalid regex, so names can't be checked" >&2; exit 1; }
  hits=$(scan -iE -f .scrub-names)
  [ -n "$hits" ] && { echo "== blocked names =="; echo "$hits"; fail=1; }
  # quotepath=off keeps non-ASCII names unquoted; a directory argument lists the files inside it
  if [ "${#paths[@]}" -gt 0 ]; then
    hits=$(git -c core.quotepath=off ls-files --cached --others --exclude-standard -- "${paths[@]}" "${skip[@]}" | grep -iEf .scrub-names)
  else
    hits=$(git -c core.quotepath=off ls-files --cached --others --exclude-standard -- . "${skip[@]}" | grep -iEf .scrub-names)
  fi
  [ -n "$hits" ] && { echo "== blocked names in file paths =="; echo "$hits"; fail=1; }
  # commit messages become CHANGELOG entries (git-cliff), so they must be clean too
  hits=$(history_text | grep -iEf .scrub-names)
  [ -n "$hits" ] && { echo "== blocked names in commit messages or tags =="; echo "$hits"; fail=1; }
elif [ -n "${CI:-}" ]; then
  echo "note: CI run, names are checked only on the maintainer's machine" >&2
else
  # a fresh clone without the names list must not pass silently
  echo "error: no .scrub-names file, so project and people names can't be checked" >&2
  fail=1
fi

[ "$fail" -eq 0 ] && echo "scrub clean"
exit "$fail"
