-- Camada Bronze · Ingestão Multi-Formato via read_files() (Meridian Bank S.A.)
--
-- A camada bronze preserva o dado exatamente como recebido dos sistemas bancários de origem,
-- garantindo rastreabilidade e auditabilidade regulatória (BACEN).
--
-- Destaques técnicos:
--   · Excel (.xlsx)      20 planilhas de cronograma de squads ingeridas com format => 'excel'
--   · ClickUp (.json)    25 arquivos JSON hierárquicos desaninhados via explode()
--   · MS Project (.xml)  15 arquivos XML MSPDI lidos pelo nó <Task>
--   · Sistemas (.csv)    PMO Bancário, RH, Timesheet, Financeiro, Compras, Carteira de Crédito/PDD e Fraude Pix
--
-- Execução via CLI:
--   python3 scripts/run_sql.py sql/01_ingestao_bronze.sql --profile SEU-PERFIL

-- ---------- pmo bancário ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.projetos AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/pmo/projetos.csv',
                format => 'csv', header => true, inferColumnTypes => false);

CREATE OR REPLACE TABLE lakehouse_meridian.bronze.status_semanal AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/pmo/status_semanal.csv',
                format => 'csv', header => true, inferColumnTypes => false);

-- ---------- as três ferramentas de gestão de squads ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.excel_tarefas AS
SELECT `ID`               AS id,
       `Fase`             AS fase,
       `Tarefa`           AS tarefa,
       `Responsável`      AS responsavel,
       `Início previsto`  AS inicio_previsto,
       `Término previsto` AS termino_previsto,
       `Início real`      AS inicio_real,
       `Término real`     AS termino_real,
       `% Concluído`      AS pct_concluido,
       `Horas previstas`  AS horas_previstas,
       url_decode(_metadata.file_name) AS arquivo
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/excel/',
                format => 'excel', headerRows => 1, inferColumnTypes => false);

CREATE OR REPLACE TABLE lakehouse_meridian.bronze.clickup_tarefas AS
SELECT list.id   AS list_id,
       list.name AS list_name,
       t.*,
       url_decode(_metadata.file_name) AS arquivo
FROM (
    SELECT list, explode(tasks) AS t, _metadata
    FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/clickup/',
                    format => 'json', multiLine => true)
);

CREATE OR REPLACE TABLE lakehouse_meridian.bronze.msproject_tarefas AS
SELECT * EXCEPT (_rescued_data),
       url_decode(_metadata.file_name) AS arquivo
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/msproject/',
                format => 'xml', rowTag => 'Task');

-- ---------- rh e timesheet ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.colaboradores AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/rh/colaboradores.csv',
                format => 'csv', header => true, inferColumnTypes => false);

CREATE OR REPLACE TABLE lakehouse_meridian.bronze.apontamentos AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/timesheet/apontamentos.csv',
                format => 'csv', header => true, inferColumnTypes => false);

-- ---------- financeiro ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.custos AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/financeiro/custos.csv',
                format => 'csv', header => true, inferColumnTypes => false);

-- ---------- compras e fintechs parceiras ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.entregas_fornecedor AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/compras/entregas_fornecedor.csv',
                format => 'csv', header => true, inferColumnTypes => false);

-- ---------- operações bancárias (crédito/PDD e prevenção a fraudes Pix) ----------
CREATE OR REPLACE TABLE lakehouse_meridian.bronze.carteira_credito_pdd AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/operacoes_bancarias/carteira_credito_pdd.csv',
                format => 'csv', header => true, inferColumnTypes => false);

CREATE OR REPLACE TABLE lakehouse_meridian.bronze.monitoramento_fraude_pix AS
SELECT * EXCEPT (_rescued_data)
FROM read_files('/Volumes/lakehouse_meridian/bronze/raw/operacoes_bancarias/monitoramento_fraude_pix.csv',
                format => 'csv', header => true, inferColumnTypes => false);

-- ---------- conferência ----------
SELECT 'projetos' AS tabela, COUNT(*) AS linhas FROM lakehouse_meridian.bronze.projetos
UNION ALL SELECT 'status_semanal', COUNT(*) FROM lakehouse_meridian.bronze.status_semanal
UNION ALL SELECT 'excel_tarefas', COUNT(*) FROM lakehouse_meridian.bronze.excel_tarefas
UNION ALL SELECT 'clickup_tarefas', COUNT(*) FROM lakehouse_meridian.bronze.clickup_tarefas
UNION ALL SELECT 'msproject_tarefas', COUNT(*) FROM lakehouse_meridian.bronze.msproject_tarefas
UNION ALL SELECT 'colaboradores', COUNT(*) FROM lakehouse_meridian.bronze.colaboradores
UNION ALL SELECT 'apontamentos', COUNT(*) FROM lakehouse_meridian.bronze.apontamentos
UNION ALL SELECT 'custos', COUNT(*) FROM lakehouse_meridian.bronze.custos
UNION ALL SELECT 'entregas_fornecedor', COUNT(*) FROM lakehouse_meridian.bronze.entregas_fornecedor
UNION ALL SELECT 'carteira_credito_pdd', COUNT(*) FROM lakehouse_meridian.bronze.carteira_credito_pdd
UNION ALL SELECT 'monitoramento_fraude_pix', COUNT(*) FROM lakehouse_meridian.bronze.monitoramento_fraude_pix
ORDER BY linhas DESC;
