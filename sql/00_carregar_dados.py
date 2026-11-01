# Databricks notebook source
# MAGIC %md
# MAGIC # Setup e Geração do Dataset Corporativo — Meridian Bank S.A.
# MAGIC
# MAGIC Este notebook inicializa a infraestrutura de dados da **Torre de Controle de Projetos (PMO Lakehouse)** no Databricks:
# MAGIC
# MAGIC 1. Cria o catálogo `lakehouse_meridian`, os schemas da arquitetura Medalhão (`bronze`, `silver`, `gold`) e o volume `bronze.raw`.
# MAGIC 2. Executa o simulador determinístico (`data_generator/gerar_dataset.py`) gravando diretamente no Volume:
# MAGIC    - 20 planilhas Excel (`.xlsx`), 25 exports de API do ClickUp (`.json`) e 15 cronogramas do MS Project (`.xml`)
# MAGIC    - Arquivos operacionais (`.csv`) de PMO, RH, Timesheet, Financeiro e Compras
# MAGIC    - Contratos de fornecedores e políticas de engenharia em `.pdf`
# MAGIC 3. Executa a suíte de validação (`data_generator/validar_padroes.py`) para atestar a integridade dos dados gerados.

# COMMAND ----------

dbutils.widgets.text("catalogo", "lakehouse_meridian")
CATALOGO = dbutils.widgets.get("catalogo")

import os, pathlib, sys

PASTA_ATUAL = pathlib.Path(os.getcwd())
RAIZ = PASTA_ATUAL.parent if PASTA_ATUAL.name == "sql" else PASTA_ATUAL
print("Diretório raiz do projeto:", RAIZ)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Provisionamento do Unity Catalog
# MAGIC Executa o script `00_setup_catalogo.sql`.

# COMMAND ----------

sql = (RAIZ / "sql" / "00_setup_catalogo.sql").read_text(encoding="utf-8").replace("lakehouse_meridian", CATALOGO)
comandos = [c.strip() for c in sql.split(";")
            if any(l.strip() and not l.strip().startswith("--") for l in c.splitlines())]
for c in comandos:
    spark.sql(c)
    print("ok:", next(l for l in c.splitlines() if l.strip() and not l.strip().startswith("--"))[:80])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Geração dos Arquivos Brutos no Volume (`bronze.raw`)

# COMMAND ----------

sys.path.insert(0, str(RAIZ / "data_generator"))
import gerar_dataset

destino = pathlib.Path(f"/Volumes/{CATALOGO}/bronze/raw")
for pasta in gerar_dataset.PASTAS_GERADAS:
    if (destino / pasta).exists():
        import shutil
        shutil.rmtree(destino / pasta)
contagens = gerar_dataset.gerar(destino, seed=42)
for k, v in contagens.items():
    print(f"{k:<20} {v:>9,}".replace(",", "."))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Validação de Integridade e Regras de Negócio
# MAGIC Consolida as três ferramentas em Python, recalcula SPI e CPI e valida os 5 padrões operacionais do portfólio.

# COMMAND ----------

import subprocess
r = subprocess.run([sys.executable, str(RAIZ / "data_generator" / "validar_padroes.py"), "--dados", str(destino)],
                   capture_output=True, text=True)
print(r.stdout[-3000:])
assert r.returncode == 0, r.stderr or "Falha na validação dos padrões do dataset"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Concluído
# MAGIC Execute em seguida o script **`sql/01_ingestao_bronze.sql`** no SQL Editor para materializar as 9 tabelas Delta da camada `bronze`.
