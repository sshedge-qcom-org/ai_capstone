#!/bin/sh
set -eu
umask 077
python -m alembic upgrade head
exec "$@"
