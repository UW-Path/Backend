#!/bin/sh
set -eu

echo "Starting backend"

if [ -n "${UWPATH_ENVIRONMENT:-}" ]; then
    echo "Configuring Oracle wallet"
    mkdir -p /code/Wallet_uwpathparallel
    printf '%s' "$WALLET_CWALLET_SSO" | base64 --decode > /code/Wallet_uwpathparallel/cwallet.sso
    printf '%s' "$WALLET_EWALLET_PEM" > /code/Wallet_uwpathparallel/ewallet.pem
    printf '%s' "$WALLET_TNSNAMES_ORA" > /code/Wallet_uwpathparallel/tnsnames.ora
    printf '%s' "$WALLET_SQLNET_ORA" > /code/Wallet_uwpathparallel/sqlnet.ora
    python manage.py migrate
    exec gunicorn uwpath_backend.wsgi --bind "0.0.0.0:${PORT:-8000}"
fi

python manage.py migrate
exec python manage.py runserver "0.0.0.0:${PORT:-8000}"
