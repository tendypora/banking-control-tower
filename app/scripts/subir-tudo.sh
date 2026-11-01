#!/usr/bin/env bash
# Script de provisionamento e deploy completo da aplicação web e banco Lakebase.
# Provisiona a instância Postgres, aplica permissões (GRANTs) e publica o Databricks App.
#
# Pré-requisitos (prompts 1 e 2): o job vertice_farol rodou (gold + gold.score_estouro_30d)
# e o bundle vertice publicou o Genie "Farol · Diretoria".
#
#   1. Lakebase (projeto farol-torre), se ainda não existe
#   2. o id do Genie "Farol · Diretoria" vai para o databricks.yml (e o .env, se existir)
#   3. app: bundle deploy → GRANT para o service principal → apps deploy (o build falha sem GRANT)
#
# O bônus dos contratos (bonus/agente) não entra aqui: ele tem o próprio passo a passo.
#
# Uso:  bash scripts/subir-tudo.sh <perfil>
set -euo pipefail
PERFIL="${1:?informe o profile}"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GENIE="Farol · Diretoria"
t0=$(date +%s)
passo() { echo -e "\n[$(( $(date +%s) - t0 ))s] $*"; }

passo "1. Lakebase"
# list-projects (e não get-project): get-project também devolve projeto apagado ("soft delete")
if databricks postgres list-projects --profile "$PERFIL" -o json | grep -q '"projects/farol-torre"'; then
  echo "projeto farol-torre já existe"
else
  databricks postgres create-project farol-torre --profile "$PERFIL" >/dev/null && echo "projeto farol-torre criado"
fi

passo "2. Genie \"$GENIE\" (do bundle vertice)"
SID=$(databricks api get "/api/2.0/genie/spaces?page_size=100" --profile "$PERFIL" \
      | python3 -c "import json,sys; print(next((s['space_id'] for s in json.load(sys.stdin).get('spaces', []) if s['title'] == '$GENIE'), ''))")
if [[ -z "$SID" ]]; then
  echo "Genie \"$GENIE\" não existe. Rode antes o prompt 2 (bundle deploy do vertice)." >&2
  exit 1
fi
echo "id: $SID"
sed -i.bak -E "s/(genie_space_id: )[0-9a-f]{32}/\1$SID/" "$APP_DIR/databricks.yml" && rm -f "$APP_DIR/databricks.yml.bak"
sed -i.bak -E "s/(DATABRICKS_GENIE_SPACE_ID=)[0-9a-f]{32}/\1$SID/" "$APP_DIR/.env" 2>/dev/null && rm -f "$APP_DIR/.env.bak" || true

passo "3. App (o Free Edition aceita no máximo 3 apps: confira com databricks apps list)"
cd "$APP_DIR"
databricks bundle deploy --profile "$PERFIL" 2>&1 | tail -3      # cria o app e o service principal
bash scripts/conceder-acesso.sh "$PERFIL"                          # sem isso o build falha no typegen
databricks apps deploy --profile "$PERFIL" 2>&1 | tail -3
passo "pronto: $(databricks apps get farol-torre --profile "$PERFIL" -o json | python3 -c "import json,sys;print(json.load(sys.stdin)['url'])")"
echo "Abra a URL e clique em Authorize (uma vez). Confira: 17 de 41 em risco, PRJ-024 com 46%."
