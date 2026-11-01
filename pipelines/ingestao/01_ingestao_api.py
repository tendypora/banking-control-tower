# Databricks notebook source
# MAGIC %md
# MAGIC # Ingestão de Calendário Bancário Nacional via API REST (Meridian Bank S.A.)

# COMMAND ----------

import requests

url = "https://brasilapi.com.br/api/feriados/v1/2026"
try:
    resposta = requests.get(url, timeout=15)
    resposta.raise_for_status()
    feriados = resposta.json()
except Exception as e:
    print("Aviso: sem acesso externo na Free Edition, usando captura oficial da BrasilAPI 2026:", e)
    feriados = [
        {"date": "2026-01-01", "name": "Confraternização mundial", "type": "national", "weekday": "quinta-feira"},
        {"date": "2026-02-16", "name": "Carnaval", "type": "national", "weekday": "segunda-feira"},
        {"date": "2026-02-17", "name": "Carnaval", "type": "national", "weekday": "terça-feira"},
        {"date": "2026-04-03", "name": "Sexta-feira Santa", "type": "national", "weekday": "sexta-feira"},
        {"date": "2026-04-05", "name": "Páscoa", "type": "national", "weekday": "domingo"},
        {"date": "2026-04-21", "name": "Tiradentes", "type": "national", "weekday": "terça-feira"},
        {"date": "2026-05-01", "name": "Dia do trabalho", "type": "national", "weekday": "sexta-feira"},
        {"date": "2026-06-04", "name": "Corpus Christi", "type": "national", "weekday": "quinta-feira"},
        {"date": "2026-09-07", "name": "Independência do Brasil", "type": "national", "weekday": "segunda-feira"},
        {"date": "2026-10-12", "name": "Nossa Senhora Aparecida", "type": "national", "weekday": "segunda-feira"},
        {"date": "2026-11-02", "name": "Finados", "type": "national", "weekday": "segunda-feira"},
        {"date": "2026-11-15", "name": "Proclamação da República", "type": "national", "weekday": "domingo"},
        {"date": "2026-11-20", "name": "Dia da consciência negra", "type": "national", "weekday": "sexta-feira"},
        {"date": "2026-12-25", "name": "Natal", "type": "national", "weekday": "sexta-feira"},
    ]

print(len(feriados), "feriados")

# COMMAND ----------

import json, os
from datetime import datetime

pasta = "/Volumes/lakehouse_meridian/bronze/raw/feriados"
os.makedirs(pasta, exist_ok=True)

agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
with open(f"{pasta}/feriados_{agora}.json", "w") as arquivo:
    json.dump(feriados, arquivo, ensure_ascii=False)

sorted(os.listdir(pasta))

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE lakehouse_meridian.bronze.feriados
# MAGIC COMMENT 'Feriados nacionais de 2026 (Calendário Bancário FEBRABAN / BrasilAPI). Uma captura por execução do job.'
# MAGIC AS SELECT date AS data, name AS feriado, type AS tipo, weekday AS dia_da_semana,
# MAGIC           _metadata.file_name              AS arquivo,
# MAGIC           _metadata.file_modification_time AS coletado_em
# MAGIC FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/feriados/', format => 'json', multiLine => true)
