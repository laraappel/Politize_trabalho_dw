#!/bin/sh
set -e
flask --app wsgi migrate
if [ "${IMPORTAR_DADOS_DEMO:-1}" = "1" ] && [ -f "${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}" ]; then
  if [ "$(python -c 'import json, sys; p = sys.argv[1];
try:
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    print("1" if isinstance(data, dict) and isinstance(data.get("politicos"), list) else "0")
except Exception:
    print("0")' "${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}")" = "1" ]; then
    flask --app wsgi importar-dados --arquivo "${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}"
  else
    echo "Arquivo de demonstração inválido; ignorando importação automática: ${DEMO_DATA_FILE:-/database/seeds/demonstracao.json}"
  fi
fi
exec flask run --host=0.0.0.0 --port=5000
