-- silver.carteira_credito_pdd & silver.monitoramento_fraude_pix
-- Tipagem, padronização e contratos de qualidade (EXPECT) para as bases de
-- Risco de Crédito (Resolução CMN 4.966 / IFRS 9) e Prevenção a Fraudes Pix / MED BACEN.

CREATE OR REFRESH MATERIALIZED VIEW carteira_credito_pdd (
  CONSTRAINT saldo_positivo EXPECT (saldo_carteira_milhoes > 0) ON VIOLATION FAIL UPDATE,
  CONSTRAINT over90_valido EXPECT (inadimplencia_over90_pct BETWEEN 0 AND 100) ON VIOLATION FAIL UPDATE,
  CONSTRAINT estagio_conhecido EXPECT (estagio_cmn_4966 LIKE 'Stage %') ON VIOLATION FAIL UPDATE
)
COMMENT 'Evolução mensal das carteiras de crédito do Meridian Bank S.A.: saldo ativo, inadimplência Over 90 (%), classificação nos estágios 1, 2 e 3 da Resolução CMN 4.966 (IFRS 9) e provisão PDD constituída.'
AS SELECT
  competencia,
  to_date(concat(competencia, '-01'), 'yyyy-MM-dd')          AS data_competencia,
  projeto_id,
  modalidade_credito,
  superintendencia,
  segmento,
  CAST(saldo_carteira_milhoes AS DECIMAL(18,2))              AS saldo_carteira_milhoes,
  CAST(inadimplencia_over90_pct AS DECIMAL(10,2))            AS inadimplencia_over90_pct,
  estagio_cmn_4966,
  CAST(provisao_pdd_milhoes AS DECIMAL(18,2))                AS provisao_pdd_milhoes,
  CAST(indice_cobertura_pdd_pct AS DECIMAL(10,1))            AS indice_cobertura_pdd_pct
FROM lakehouse_meridian.bronze.carteira_credito_pdd;

CREATE OR REFRESH MATERIALIZED VIEW monitoramento_fraude_pix (
  CONSTRAINT volume_positivo EXPECT (volume_transacoes_mil > 0) ON VIOLATION FAIL UPDATE,
  CONSTRAINT sla_valido EXPECT (disponibilidade_sla_pct BETWEEN 0 AND 100) ON VIOLATION FAIL UPDATE
)
COMMENT 'Telemetria semanal de transações bancárias (Pix/SPI, Cartões e Open Finance), bloqueios antifraude, perda líquida por fraude, acionamentos de MED BACEN e SLA de latência p99.'
AS SELECT
  CAST(semana AS DATE)                                       AS semana,
  projeto_id,
  canal_bancario,
  superintendencia,
  CAST(volume_transacoes_mil AS DECIMAL(18,1))               AS volume_transacoes_mil,
  CAST(valor_transacionado_milhoes AS DECIMAL(18,2))         AS valor_transacionado_milhoes,
  CAST(tentativas_fraude_detectadas AS INT)                  AS tentativas_fraude_detectadas,
  CAST(fraude_bloqueada_mil AS DECIMAL(18,2))                AS fraude_bloqueada_mil,
  CAST(perda_liquida_fraude_mil AS DECIMAL(18,2))            AS perda_liquida_fraude_mil,
  CAST(acionamentos_med_bacen AS INT)                        AS acionamentos_med_bacen,
  CAST(latencia_p99_ms AS DECIMAL(10,1))                     AS latencia_p99_ms,
  CAST(disponibilidade_sla_pct AS DECIMAL(10,2))             AS disponibilidade_sla_pct
FROM lakehouse_meridian.bronze.monitoramento_fraude_pix;
