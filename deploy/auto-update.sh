#!/bin/sh
# Pull the latest master and put it live.
#
# Run it from a systemd timer (see deploy/README.md). It is safe to run often:
# when origin/master hasn't moved it does nothing.
#
# nginx serves web/html straight from the checkout (a read-only bind mount),
# so updating the files is enough. The container is only recreated when
# web/docker-compose.yml itself changes.
set -eu

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
BRANCH="${BRANCH:-master}"

cd "$REPO_DIR"

git fetch --quiet origin "$BRANCH"
old="$(git rev-parse HEAD)"
new="$(git rev-parse "origin/$BRANCH")"

if [ "$old" = "$new" ]; then
    exit 0
fi

echo "Updating $old -> $new"

# The server never edits tracked files, so a hard reset is the simplest way to
# match master exactly. Untracked files such as web/.env are left alone.
git reset --quiet --hard "$new"

# Keep the files readable by nginx whatever the server's umask is.
chmod 755 web/html
find web/html -type d -exec chmod 755 {} +
find web/html -type f -exec chmod 644 {} +

if ! git diff --quiet "$old" "$new" -- web/docker-compose.yml; then
    echo "docker-compose.yml changed, recreating the container"
    (cd web && docker compose up -d --remove-orphans)
fi

echo "Live at $(git log -1 --format='%h %s')"
