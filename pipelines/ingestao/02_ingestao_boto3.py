# Databricks notebook source
# MAGIC %md
# MAGIC # Ingestão do Data Lake Bancário (S3 boto3 / Geração Determinística) — Meridian Bank S.A.

# COMMAND ----------

import os, pathlib, sys

VARIAVEIS = ["S3_ENDPOINT", "AWS_DEFAULT_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

for nome in VARIAVEIS:
    if os.environ.get(nome):
        continue
    dbutils.widgets.text(nome, "")
    os.environ[nome] = dbutils.widgets.get(nome)

S3_BUCKET = "DataLakeVertice"
RAW = "/Volumes/lakehouse_meridian/bronze/raw"

if os.environ.get("AWS_ACCESS_KEY_ID") in ("", "SEM_CHAVE", None):
    print("Modo autônomo (sem chaves S3): verificando/provisionando dataset bancário no volume raw...")
    destino = pathlib.Path(RAW)
    if not (destino / "operacoes_bancarias" / "carteira_credito_pdd.csv").exists():
        pasta_atual = pathlib.Path(os.getcwd())
        raiz = pasta_atual.parents[1] if pasta_atual.name == "ingestao" else pasta_atual
        sys.path.insert(0, str(raiz / "data_generator"))
        import gerar_dataset
        contagens = gerar_dataset.gerar(destino, seed=42)
        print("Dataset bancário gerado com sucesso:", contagens)
    else:
        print("Arquivos brutos já presentes em:", RAW)
else:
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        config=Config(s3={"addressing_style": "path"}),
    )
    objetos = []
    for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=S3_BUCKET):
        objetos += pagina.get("Contents", [])
    arquivos = [o["Key"] for o in objetos if not o["Key"].endswith("/") and o["Size"] > 0
                and not o["Key"].endswith(".emptyFolderPlaceholder")]
    for key in arquivos:
        dest_file = f"{RAW}/{key}"
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        conteudo = s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()
        with open(dest_file, "wb") as f:
            f.write(conteudo)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.projetos AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/pmo/projetos.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.status_semanal AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/pmo/status_semanal.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.colaboradores AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/rh/colaboradores.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.apontamentos AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/timesheet/apontamentos.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.custos AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/financeiro/custos.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.entregas_fornecedor AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/compras/entregas_fornecedor.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.carteira_credito_pdd AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/operacoes_bancarias/carteira_credito_pdd.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.monitoramento_fraude_pix AS
# MAGIC SELECT * EXCEPT (_rescued_data)
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/operacoes_bancarias/monitoramento_fraude_pix.csv',
# MAGIC                 format => 'csv', header => true, inferColumnTypes => false);

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.excel_tarefas AS
# MAGIC SELECT `ID`               AS id,
# MAGIC        `Fase`             AS fase,
# MAGIC        `Tarefa`           AS tarefa,
# MAGIC        `Responsável`      AS responsavel,
# MAGIC        `Início previsto`  AS inicio_previsto,
# MAGIC        `Término previsto` AS termino_previsto,
# MAGIC        `Início real`      AS inicio_real,
# MAGIC        `Término real`     AS termino_real,
# MAGIC        `% Concluído`      AS pct_concluido,
# MAGIC        `Horas previstas`  AS horas_previstas,
# MAGIC        url_decode(_metadata.file_name) AS arquivo
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/excel/',
# MAGIC                 format => 'excel', headerRows => 1, inferColumnTypes => false);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.clickup_tarefas AS
# MAGIC SELECT list.id   AS list_id,
# MAGIC        list.name AS list_name,
# MAGIC        t.*,
# MAGIC        url_decode(_metadata.file_name) AS arquivo
# MAGIC FROM (
# MAGIC     SELECT list, explode(tasks) AS t, _metadata
# MAGIC     FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/clickup/',
# MAGIC                     format => 'json', multiLine => true)
# MAGIC );
# MAGIC
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.msproject_tarefas AS
# MAGIC SELECT * EXCEPT (_rescued_data),
# MAGIC        url_decode(_metadata.file_name) AS arquivo
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/msproject/',
# MAGIC                 format => 'xml', rowTag => 'Task');
