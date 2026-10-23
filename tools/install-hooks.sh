#!/bin/sh
# Install a local pre-commit hook that runs the public-repository safeguards before every
# commit (OD-0019, OD-0020 item 4). CI runs the same checks; the hook catches problems before
# they reach a public remote, where a pushed secret must be treated as leaked.
set -eu
root=$(git rev-parse --show-toplevel)
hook="$root/.git/hooks/pre-commit"
cat > "$hook" <<'HOOK'
#!/bin/sh
exec uv run --no-project --python 3.13 --with pyyaml==6.0.2 python tools/check_repo.py public imports valid_time
HOOK
chmod +x "$hook"
echo "installed $hook"
