#!/bin/sh
set -e
flask --app wsgi migrate
if [ "${IMPORTAR_DADOS_DEMO:-1}" = "1" ] && [ -f "${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}" ]; then
  flask --app wsgi importar-dados --arquivo "${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}"
fi
exec flask run --host=0.0.0.0 --port=5000
