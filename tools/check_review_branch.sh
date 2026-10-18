#!/bin/sh
# HIO review-branch scope check (operating model §6.2).
# Usage: hio/tools/check_review_branch.sh <assigned_head_sha> <review_branch>
#
# Run the copy of this script from the STAGING branch, never the copy on the review branch.
# Passing establishes a content-scope constraint only. It does not authenticate the reviewer
# or approve anything.
#
# Fails (exit 1) if:
#   - the review branch does not descend from the assigned head;
#   - the range is empty, or contains merge commits;
#   - ANY commit in the range (not only the final diff) changes a path outside hio/reviews/,
#     or changes anything other than an added or modified regular, non-executable .md file
#     (no symlinks, submodules, executables, deletions, renames or other types);
#   - any commit modifies a file under hio/reviews/records/ that existed before that commit
#     (submitted records are immutable);
#   - the branch adds no review or verification record
#     (hio/reviews/records/REVIEW-*.md or hio/reviews/records/VERIFY-*.md).
set -eu
[ $# -eq 2 ] || { echo "usage: $0 <assigned_head_sha> <review_branch>" >&2; exit 2; }
head=$(git rev-parse --verify "$1^{commit}")
branch=$(git rev-parse --verify "$2^{commit}")
fail=0
err() { echo "FAIL: $*" >&2; fail=1; }

[ "$(git merge-base "$head" "$branch")" = "$head" ] || err "branch does not descend from the assigned head $head"
commits=$(git rev-list --reverse "$head..$branch")
[ -n "$commits" ] || err "empty review branch: no commits after $head"
[ -z "$(git rev-list --merges "$head..$branch")" ] || err "merge commits in $head..$2"

# Check one commit against its parent.
# --raw lines: ":<oldmode> <newmode> <oldsha> <newsha> <status>\t<path>"
scan_commit() {
  c=$1
  git diff --raw --no-renames "$c^" "$c" | while IFS="$(printf '\t')" read -r meta path; do
    newmode=$(echo "$meta" | awk '{print $2}')
    status=$(echo "$meta" | awk '{print $5}')
    short=$(git rev-parse --short "$c")
    case "$path" in hio/reviews/*) ;; *) echo "$short: path outside hio/reviews/: $path" ;; esac
    case "$status" in
      A|M)
        [ "$newmode" = "100644" ] || echo "$short: mode $newmode (only regular non-executable files): $path"
        case "$path" in *.md) ;; *) echo "$short: not a .md file: $path" ;; esac
        case "$status:$path" in M:hio/reviews/records/*) echo "$short: submitted record modified: $path" ;; esac
        ;;
      *) echo "$short: status $status not allowed (only add or modify): $path" ;;
    esac
  done
}
problems=""
for c in $commits; do
  p=$(scan_commit "$c")
  [ -z "$p" ] || problems="$problems$p
"
done
if [ -n "$problems" ]; then
  printf '%s' "$problems" | sed 's/^/FAIL: /' >&2
  fail=1
fi

# The branch must add at least one review or verification record.
if [ -n "$commits" ] && ! git diff --name-only --diff-filter=A --no-renames "$head" "$branch" \
     | grep -Eq '^hio/reviews/records/(REVIEW|VERIFY)-[^/]*\.md$'; then
  err "no review or verification record added (hio/reviews/records/REVIEW-*.md or VERIFY-*.md)"
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS: $2 ($(echo "$commits" | wc -l | tr -d ' ') commit(s)) changes only permitted review records relative to $head"
  git diff --name-status --no-renames "$head" "$branch"
fi
exit "$fail"
