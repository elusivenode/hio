#!/bin/sh
# HIO review-branch scope check (operating model §6.2).
# Usage: hio/tools/check_review_branch.sh <assigned_head_sha> <review_branch>
#
# Run the copy of this script from the STAGING branch, never the copy on the review branch.
# Passing establishes a content-scope constraint only. It does not authenticate the reviewer
# or approve anything.
#
# Fails (exit 1) if:
#   - the review branch does not start exactly at the assigned head;
#   - the range contains merge commits;
#   - any changed path is outside hio/reviews/;
#   - any change is not an added or modified regular, non-executable .md file
#     (no symlinks, submodules, executables, deletions, renames or other file types);
#   - an existing file under hio/reviews/records/ is modified (submitted records are immutable).
set -eu
[ $# -eq 2 ] || { echo "usage: $0 <assigned_head_sha> <review_branch>" >&2; exit 2; }
head=$(git rev-parse --verify "$1^{commit}")
branch=$(git rev-parse --verify "$2^{commit}")
fail=0
err() { echo "FAIL: $*" >&2; fail=1; }

[ "$(git merge-base "$head" "$branch")" = "$head" ] || err "branch does not descend from the assigned head $head"
[ -z "$(git rev-list --merges "$head..$branch")" ] || err "merge commits in $head..$2"

# --raw lines: ":<oldmode> <newmode> <oldsha> <newsha> <status>\t<path>"
scan() {
  git diff --raw --no-renames "$head" "$branch" | while IFS="$(printf '\t')" read -r meta path; do
    newmode=$(echo "$meta" | awk '{print $2}')
    status=$(echo "$meta" | awk '{print $5}')
    case "$path" in hio/reviews/*) ;; *) echo "path outside hio/reviews/: $path" ;; esac
    case "$status" in
      A|M)
        [ "$newmode" = "100644" ] || echo "mode $newmode (only regular non-executable files): $path"
        case "$path" in *.md) ;; *) echo "not a .md file: $path" ;; esac
        case "$status:$path" in M:hio/reviews/records/*) echo "submitted record modified: $path" ;; esac
        ;;
      *) echo "status $status not allowed (only add or modify): $path" ;;
    esac
  done
}
problems=$(scan)
if [ -n "$problems" ]; then
  echo "$problems" | sed 's/^/FAIL: /' >&2
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS: $2 changes only permitted review records relative to $head"
  git diff --name-status --no-renames "$head" "$branch"
fi
exit "$fail"
